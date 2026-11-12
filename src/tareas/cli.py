"""Interfaz de línea de órdenes de dam: aquí solo hay órdenes, opciones y salida por pantalla."""

import functools
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Optional

import typer
from rich import box
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from tareas import URL_EJEMPLO_ACCIONES, __version__, ciclos, config, escanear, hook, sincronizar, web
from tareas import configurar as configurar_mod  # «configurar» ya es el nombre del comando
from tareas import doctor as doctor_mod  # «doctor», «entregar» y «pendientes» ya son nombres de comandos
from tareas import duplicados as duplicados_mod
from tareas import entregar as entregar_mod
from tareas import inventario as inventario_mod
from tareas import pendientes as pendientes_mod
from tareas import readme as readme_mod
from tareas.errores import ConfigError, IANoDisponible, TareasError
from tareas.ia import ProveedorCentro
from tareas.inventario import tamano_legible
from tareas.motor import Motor
from typer import _completion_classes, _completion_shared, rich_utils


def _forzar_utf8() -> None:
    """En Windows, si la salida se redirige, Python usa cp1252 y los símbolos (✔ →) fallan."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


_forzar_utf8()

# Textos de la ayuda de cada comando (dam COMANDO --help) en español
rich_utils.ARGUMENTS_PANEL_TITLE = "Argumentos"
rich_utils.OPTIONS_PANEL_TITLE = "Opciones"
rich_utils.COMMANDS_PANEL_TITLE = "Comandos"
rich_utils.ERRORS_PANEL_TITLE = "Error de uso"
rich_utils.ABORTED_TEXT = "Cancelado."
rich_utils.DEFAULT_STRING = "[por defecto: {}]"
rich_utils.REQUIRED_LONG_STRING = "[obligatorio]"
rich_utils.RICH_HELP = "Prueba [blue]'{command_path} {help_option}'[/] para ver la ayuda."

# Los errores de uso («No such command...») los escribe Click, dentro de Typer, en inglés y sin
# traducción. No toco la librería: traduzco su mensaje justo antes de que Typer lo pinte.
# Lo que no esté en la lista sale tal cual (en inglés, pero sin perderse nada).
TRADUCCIONES_CLICK = [
    (r"No such command '([^']*)'\.", r"No existe el comando «\1»."),
    (r"Did you mean one of (.+?)\?", r"¿Querías decir uno de estos: \1?"),
    (r"Did you mean (.+?)\?", r"¿Querías decir \1?"),
    (r"No such option: (\S+)", r"No existe la opción \1"),
    (r"\(Possible options: ([^)]*)\)", r"(¿Querías decir \1?)"),
    (r"Missing argument", "Falta el argumento"),
    (r"Missing option", "Falta la opción"),
    (r"Missing parameter", "Falta el parámetro"),
    (r"Got unexpected extra argument\(s\) \(([^)]*)\)", r"Sobra: \1"),
    (r"Invalid value for (.+?): ", r"Valor no válido para \1: "),
    (r"Invalid value: ", "Valor no válido: "),
    (r"Option ('[^']*') requires an argument\.", r"La opción \1 necesita un valor."),
    (r"Option ('[^']*') requires (\d+) arguments\.", r"La opción \1 necesita \2 valores."),
    (r"Option ('[^']*') does not take a value\.", r"La opción \1 no lleva valor."),
    (r"('[^']*') is not a valid integer\.", r"\1 no es un número entero."),
    (r"('[^']*') is not a valid float\.", r"\1 no es un número."),
    (r"('[^']*') is not one of (.+)\.", r"\1 no es ninguno de estos: \2."),
]


def traducir_error_click(mensaje: str) -> str:
    """Pasa al español los mensajes de error de uso más comunes de Click."""
    for patron, cambio in TRADUCCIONES_CLICK:
        mensaje = re.sub(patron, cambio, mensaje)
    return mensaje


_pintar_error_click = rich_utils.rich_format_error


def _pintar_error_en_espanol(error) -> None:
    original = error.format_message
    error.format_message = lambda: traducir_error_click(original())
    _pintar_error_click(error)


rich_utils.rich_format_error = _pintar_error_en_espanol

_PARECE_RUTA = re.compile(r"^([A-Za-z]:[\\/]|\.{1,2}[\\/]|~[\\/]|\\\\)")


def _citar(argumento: str) -> str:
    return f'"{argumento}"' if " " in argumento else argumento


def ruta_con_comillas_metidas(argumentos: list[str]) -> Optional[str]:
    """Si una ruta trae una " dentro, devuelve la orden corregida (si no, None).

    En Windows, "C:\\carpeta\\" llega como C:\\carpeta" : la \\ final se «come» las comillas de cierre
    (y lo que venga detrás se pega a la ruta). El TAB de PowerShell 5.1 añade esa \\ final.
    """
    for i, argumento in enumerate(argumentos):
        if '"' in argumento and _PARECE_RUTA.match(argumento):
            ruta, _, resto = argumento.partition('"')
            ruta = ruta.rstrip("\\/") or ruta
            partes = [_citar(a) for a in argumentos[:i]] + [f'"{ruta}"']
            partes += resto.split() + [_citar(a) for a in argumentos[i + 1:]]
            return "dam " + " ".join(partes)
    return None


class Dam(typer.Typer):
    """El Typer de siempre, pero antes de nada revisa los argumentos tal y como llegan de la terminal."""

    def __call__(self, *args, **kwargs):
        corregida = ruta_con_comillas_metidas(sys.argv[1:])
        if corregida:
            consola_err.print("[red]✘ Una ruta lleva unas comillas metidas.[/red] En Windows, una \\ justo "
                              "antes de las comillas de cierre se las come (el TAB de PowerShell la añade).")
            consola_err.print(f"Quita la \\ del final y repite:  [bold]{escape(corregida)}[/bold]")
            raise SystemExit(2)  # 2 = uso incorrecto
        return super().__call__(*args, **kwargs)


app = Dam(
    help="dam: automatiza tareas con ficheros y mantiene tu almacén de apuntes sincronizado.",
    no_args_is_help=False,
    add_completion=True,  # --install-completion / --show-completion y el TAB (ver completar_*)
    rich_markup_mode="rich",
    context_settings={"help_option_names": []},
)
consola = Console(highlight=False)
consola_err = Console(stderr=True, highlight=False)

COLORES = {"hecho": "green", "simulado": "cyan", "saltado": "yellow", "error": "red"}


def controlar_errores(funcion):
    """Convierte cualquier TareasError en un mensaje en rojo y su código de salida (sin traza)."""

    @functools.wraps(funcion)
    def envoltorio(*args, **kwargs):
        try:
            return funcion(*args, **kwargs)
        except TareasError as e:
            consola_err.print(f"[red]✘ {escape(str(e))}[/red]")
            if isinstance(e, IANoDisponible):
                consola_err.print("Las acciones sin IA siguen funcionando: mira cuáles son con «dam acciones».")
            raise typer.Exit(e.codigo_salida) from None

    return envoltorio


def preguntar(pregunta: str) -> bool:
    """Pregunta s/n (acepta s, sí, si, y, yes). Cualquier otra cosa es «no»: nunca actúa por defecto."""
    respuesta = typer.prompt(f"{pregunta} [s/N]", default="n", show_default=False)
    return respuesta.strip().lower() in {"s", "si", "sí", "y", "yes"}


def confirmar(pregunta: str) -> None:
    """Como preguntar, pero si la respuesta no es «sí» cancela la orden."""
    if not preguntar(pregunta):
        raise typer.Abort()


# ---------- ayuda ----------
# Ejemplos por comando: salen en `dam` (ayuda general) y al final de `dam COMANDO --help`.
# Hay un test que obliga a que cada comando nuevo tenga los suyos.
EJEMPLOS: dict[str, list[tuple[str, str]]] = {
    "configurar": [
        ("dam configurar", "Te pregunta ciclo, curso y asignaturas, y deja acciones.json a tu medida"),
        ("dam configurar --ciclo asix --curso 2 --simular", "Enseña cómo quedaría para 2º de ASIR/ASIX, sin guardar"),
        ('dam configurar --ciclo smx --curso 1 --nueva "fol=fol,contrato" --si', "Sin preguntas, con una asignatura más"),
        ("dam configurar --plantilla acciones.json", "Parte del acciones.json del repo (lo hace el instalador)"),
    ],
    "scan-secrets": [
        ("dam scan-secrets", "Revisa la carpeta actual (solo lo que se subiría a git)"),
        ("dam scan-secrets --staged", "Revisa solo lo preparado con git add: úsalo antes de cada commit"),
        ("dam scan-secrets --historial", "Revisa TODO el historial de git (cero claves, exige la rúbrica)"),
        ("dam scan-secrets ~/DAM-almacen --alta", "Otra carpeta, solo hallazgos seguros"),
    ],
    "instalar-hook": [
        ("dam instalar-hook", "Revisa claves en cada git commit del repositorio actual"),
        ("dam instalar-hook ~/DAM-almacen", "En otro repositorio"),
        ("dam instalar-hook --quitar", "Lo desactiva"),
    ],
    "doctor": [
        ("dam doctor", "Revisa el proyecto de la carpeta actual"),
        ("dam doctor ~/Electrician", "Revisa otro proyecto (no cambia nada)"),
    ],
    "pendientes": [
        ("dam pendientes ~/Electrician", "Etiquetas por fichero, lo que está sin verificar y el registro de pendientes"),
        ("dam pendientes ~/Electrician --quien Gabi", "Solo lo que te toca a ti (y lo de «Todos»)"),
        ("dam pendientes . --resumen", "Solo los números, sin las listas"),
    ],
    "entregar": [
        ("dam entregar ~/Electrician --simular", "Enseña qué entraría en el zip y qué se queda fuera, sin crearlo"),
        ("dam entregar ~/Electrician", "Crea Electrician_AAAA-MM-DD.zip al lado de la carpeta"),
        ("dam entregar . --destino ~/Escritorio", "El zip de la carpeta actual, en otra carpeta"),
        ('dam entregar . --nombre "Vidal_Gabriel_practica3"', "Con el nombre que pida el profesor"),
    ],
    "inventario": [
        ("dam inventario ~/Desktop", "Qué hay en el Escritorio: tamaños, repos, tipos, instaladores y basura"),
        ("dam inventario ~ --guardar ~/inventario.md", "Todo tu usuario, con el informe completo en un .md"),
        ("dam inventario ~/Downloads --top 30", "Enseña 30 filas por lista en vez de 15"),
    ],
    "duplicados": [
        ("dam duplicados ~/Datos", "Ficheros repetidos y carpetas que son copia de otra (no borra nada)"),
        ("dam duplicados ~/Datos --guardar ~/duplicados.md", "Con el informe en un .md para repasarlo con calma"),
        ("dam duplicados ~/Downloads --top 50", "Enseña los 50 grupos más grandes en vez de 15"),
    ],
    "readme": [
        ("dam readme ~/Datos --simular", "Enseña qué README crearía o pondría al día, sin tocar nada"),
        ("dam readme ~/Datos", "Lo hace de verdad: enseña la lista y pregunta s/N"),
        ("dam readme ~/Datos/SMX --niveles 1", "Solo SMX y sus carpetas de primer nivel"),
    ],
    "test-links": [
        ("dam test-links ~/portfolio", "Revisa todos los .html de la carpeta (enlaces internos y externos)"),
        ("dam test-links index.html", "Una sola página"),
        ("dam test-links ~/portfolio --sin-externos", "Solo enlaces internos: no necesita internet"),
        ("dam test-links https://tu-web.com", "Una página ya publicada"),
    ],
    "check-headers": [
        ("dam check-headers https://tu-web.com", "Cabeceras de seguridad de tu web"),
        ("dam check-headers https://tu-api.onrender.com --timeout 60", "Render gratis tarda en despertar: dale más tiempo"),
    ],
    "version": [
        ("dam version", "Muestra la versión instalada"),
    ],
    "help": [
        ("dam help", "La lista de comandos (lo mismo que dam --help)"),
        ("dam help sync", "La ayuda detallada de un comando (lo mismo que dam sync --help)"),
    ],
    "listar": [
        ("dam listar", "Lista la carpeta actual"),
        ("dam listar ~/DAM-almacen", "Lista una carpeta (~ también vale en Windows)"),
        ('dam listar "C:\\Users\\HP\\Desktop\\DAM"', "Rutas con espacios, entre comillas"),
    ],
    "validar": [
        ("dam validar", "Comprueba el acciones.json que usa dam"),
        ("dam --config pruebas/roto.json validar", "Comprueba otro fichero (--config va ANTES del comando)"),
    ],
    "acciones": [
        ("dam acciones", "Tabla con el nombre, tipo y descripción de cada acción"),
        ("dam --config ~/prueba-smx/acciones.json acciones", "Las de otro acciones.json (--config va ANTES del comando)"),
        ("dam ejecutar convertir-webp ~/Descargas --simular", "Después, usa una por su nombre: primero simulando"),
        ("dam ejecutar convertir-webp ~/Descargas/portada.png", "Solo un fichero, no toda la carpeta"),
        ("dam ejecutar -h", "Todas las opciones de ejecutar"),
    ],
    "ejecutar": [
        ("dam ejecutar ordenar --simular", "Enseña cómo ordenaría, sin tocar nada"),
        ("dam ejecutar ordenar", "Lo hace de verdad: enseña la tabla y pregunta s/N"),
        ("dam ejecutar limpiar-temporales ~/pruebas-tareas", "Usa otra carpeta en vez del origen de la acción"),
        ("dam ejecutar convertir-webp ~/Descargas/portada.png", "Solo ese fichero, no toda la carpeta"),
        ("dam ejecutar convertir-webp --si", "Sin preguntar (solo si estás seguro)"),
    ],
    "comprobar-ia": [
        ("dam comprobar-ia", "¿Llego al servidor de IA del centro? Enseña servidor y modelo, nunca la clave"),
    ],
    "status": [
        ("dam status", "Qué has cambiado y qué hay nuevo en GitHub (no modifica nada)"),
        ("dam status programacion", "Mira solo la asignatura programacion"),
        ("dam status --almacen D:\\DAM-almacen", "Almacén en otra ruta (por ejemplo, el USB)"),
    ],
    "sync": [
        ("dam sync --simular", "Enseña qué haría, sin tocar nada"),
        ("dam sync", "Sube o baja según toque, con mensaje automático"),
        ('dam sync -m "lo que he hecho"', "Todo el almacén, con tu mensaje"),
        ('dam sync programacion -m "tema 3"', "Solo asignaturas/programacion"),
        ("dam sync --integrar", "Cambios en los dos lados: guarda lo tuyo, une y sube"),
    ],
}

# (tema, para qué, comandos): el tema y el «para qué» salen en la primera columna de la tabla de ayuda
GRUPOS = [
    ("Ficheros", "ordenar y limpiar", ["configurar", "listar", "validar", "acciones", "ejecutar"]),
    ("IA", "modelos del centro", ["comprobar-ia"]),
    ("Almacén (git)", "clase, casa y USB", ["status", "sync"]),
    ("Seguridad", "claves expuestas", ["scan-secrets", "instalar-hook"]),
    ("Tus proyectos", "revisar y entregar", ["doctor", "pendientes", "entregar"]),
    ("Tus datos", "organizar el PC", ["inventario", "duplicados", "readme"]),
    ("Tu web", "enlaces y cabeceras", ["test-links", "check-headers"]),
    ("Otros", "", ["version", "help"]),
]


def _resumen(cmd: Any) -> str:
    """Primer párrafo de la ayuda de un comando, en una línea."""
    return " ".join(((cmd.help or "").strip().split("\n\n") or [""])[0].split())


def mostrar_ayuda() -> None:
    """Ayuda general corta: una tabla con cada comando y una descripción de una línea."""
    comandos = typer.main.get_command(app).commands
    consola.print(
        "[bold]dam[/bold] — automatiza tareas con ficheros y mantiene tu almacén "
        "de apuntes sincronizado."
    )
    consola.print(
        "\n[bold]Uso:[/bold]  dam COMANDO [ARGUMENTOS] [OPCIONES]"
        "   [dim](o «tareas»: es el mismo programa con otro nombre)[/dim]\n"
    )

    agrupados = {n for _, _, nombres in GRUPOS for n in nombres}
    resto = [n for n in comandos if n not in agrupados]  # comandos nuevos que falten en GRUPOS
    grupos = GRUPOS + ([("Más", "", resto)] if resto else [])
    tabla = Table(box=box.ROUNDED, header_style="bold")
    tabla.add_column("Tema", no_wrap=True)
    tabla.add_column("Comando", style="bold cyan", no_wrap=True)
    tabla.add_column("Qué hace")
    for i, (tema, para, nombres) in enumerate(grupos):
        primera = [f"[bold magenta]{escape(tema)}[/bold magenta]", f"[dim]{escape(para)}[/dim]"]
        for j, nombre in enumerate(n for n in nombres if n in comandos):
            tabla.add_row(primera[j] if j < 2 else "", escape(f"dam {nombre}"), escape(_resumen(comandos[nombre])))
        if i < len(grupos) - 1:
            tabla.add_section()  # una raya entre temas
    consola.print(tabla)

    consola.print("\nUsar otro acciones.json:  [bold]dam --config RUTA COMANDO[/bold]")
    consola.print(
        "Activa el TAB:            [bold]instalar.sh[/bold] / [bold]instalar.ps1[/bold] si clonaste el repo; "
        "si no (Linux y macOS): [bold]dam --install-completion[/bold]"
    )
    consola.print("Ver el script del TAB:    [bold]dam --show-completion[/bold]")


@app.callback(invoke_without_command=True)
def principal(
    ctx: typer.Context,
    config_ruta: Annotated[
        Optional[Path],
        typer.Option(
            "--config",
            metavar="RUTA",
            help="Usa otro acciones.json (por defecto: ./acciones.json o ~/.config/dam/).",
        ),
    ] = None,
    ayuda: Annotated[
        bool,
        typer.Option("-h", "--help", help="Muestra esta ayuda y sale.", is_eager=True),
    ] = False,
):
    if ayuda or ctx.invoked_subcommand is None:
        mostrar_ayuda()
        raise typer.Exit()
    ctx.obj = config_ruta


def comando(funcion=None, *, nombre: Optional[str] = None):
    """Registra un subcomando con su ayuda -h/--help y sus ejemplos al final.

    Uso normal: @comando (el nombre sale de la función: scan_secrets -> scan-secrets).
    Si el nombre choca con Python (help ya existe), se da a mano: @comando(nombre="help").
    """

    def registrar(f):
        nombre_cmd = nombre or f.__name__.replace("_", "-")
        ejemplos = EJEMPLOS.get(nombre_cmd, [])
        epilog = None
        if ejemplos:
            lineas = [f"$ {escape(c)}  [dim]— {escape(e)}[/dim]" for c, e in ejemplos]
            epilog = "[bold]Ejemplos:[/bold]\n\n" + "\n\n".join(lineas)
        return app.command(
            nombre_cmd, epilog=epilog, context_settings={"help_option_names": ["-h", "--help"]}
        )(f)

    return registrar(funcion) if funcion is not None else registrar


@comando
def version() -> None:
    """Muestra la versión instalada."""
    # El mismo programa se instala como «dam» y como «tareas» (el nombre de la spec v0)
    nombre = "tareas" if Path(sys.argv[0]).stem.lower() == "tareas" else "dam"
    consola.print(f"{nombre} {__version__}")


@comando(nombre="help")
def ayuda(
    ctx: typer.Context,
    nombre: Annotated[
        Optional[str],
        typer.Argument(metavar="COMANDO", help="Comando del que quieres la ayuda (sin él, la lista de comandos)."),
    ] = None,
) -> None:
    """Esta lista, o las opciones y ejemplos de un comando: dam help COMANDO."""
    if nombre is None:
        mostrar_ayuda()
        return
    comandos = typer.main.get_command(app).commands
    if nombre not in comandos:
        consola.print(f"[red]No existe el comando «{escape(nombre)}».[/red] Mira la lista con: dam help")
        raise typer.Exit(2)  # 2 = uso incorrecto, como el resto de errores de uso
    # Pide a ese comando su propia ayuda, igual que si escribieras «dam NOMBRE --help»
    comandos[nombre].make_context(nombre, ["--help"], parent=ctx.parent)


@comando
@controlar_errores
def listar(
    carpeta: Annotated[
        Path, typer.Argument(metavar="CARPETA", help="Carpeta que quieres ver (por defecto, la actual).")
    ] = Path("."),
) -> None:
    """Lista los ficheros de una carpeta en una tabla.

    Muestra nombre, tipo (extensión o «carpeta»), tamaño y fecha de modificación. Primero van las carpetas y después los ficheros, por orden alfabético.

    Sin CARPETA usa la carpeta actual. Sale con 1 si la ruta no existe o no es una carpeta.
    """
    carpeta = carpeta.expanduser()
    if not carpeta.is_dir():
        raise TareasError(f"«{carpeta}» no existe o no es una carpeta.")
    elementos = sorted(carpeta.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    if not elementos:
        consola.print(f"La carpeta «{escape(str(carpeta))}» está vacía.")
        return
    tabla = Table(title=f"Contenido de {escape(str(carpeta.resolve()))}")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Tamaño", justify="right")
    tabla.add_column("Modificado")
    for ruta in elementos:
        try:
            datos = ruta.stat()
        except OSError:
            continue  # enlace roto o sin permisos
        es_carpeta = ruta.is_dir()
        tipo = "carpeta" if es_carpeta else (ruta.suffix.lower() or "(sin extensión)")
        tamano = "—" if es_carpeta else tamano_legible(datos.st_size)
        fecha = datetime.fromtimestamp(datos.st_mtime).strftime("%Y-%m-%d %H:%M")
        tabla.add_row(escape(ruta.name), tipo, tamano, fecha)
    consola.print(tabla)


@comando
@controlar_errores
def validar(ctx: typer.Context) -> None:
    """Comprueba que acciones.json está bien escrito.

    Sale con 3 si no es válido. Comprueba el fichero entero ANTES de tocar ningún fichero tuyo: JSON bien escrito, campos obligatorios, tipos de acción, filtros, expresiones regulares y plantillas.

    Si algo falla, el mensaje dice qué acción y qué campo.
    """
    ruta = config.buscar(ctx.obj)
    acciones = config.cargar(ruta)
    consola.print(f"[green]✔ {len(acciones)} acciones válidas[/green] ({escape(str(ruta))})")


@comando
@controlar_errores
def acciones(ctx: typer.Context) -> None:
    """Lista las acciones definidas en acciones.json.

    Muestra el nombre (el que escribes en «dam ejecutar NOMBRE»), el tipo y la descripción.

    Tipos sin IA: mover, copiar, renombrar, borrar, ordenar (por asignatura) y convertir (a WebP).

    Tipos con IA (columna IA): resumir, renombrar-ia y clasificar. Necesitan el servidor del centro (mira dam comprobar-ia); las demás funcionan sin red.
    """
    lista = config.cargar(config.buscar(ctx.obj))
    tabla = Table(title="Acciones disponibles")
    tabla.add_column("Nombre", style="bold")
    tabla.add_column("Tipo")
    tabla.add_column("IA", justify="center")
    tabla.add_column("Descripción")
    for a in lista:
        ia = "[magenta]sí[/magenta]" if a["tipo"] in config.TIPOS_IA else "—"
        tabla.add_row(escape(a["nombre"]), a["tipo"], ia, escape(a["descripcion"]))
    consola.print(tabla)
    consola.print("Para usar una: [bold]dam ejecutar NOMBRE CARPETA --simular[/bold] (o un solo fichero en vez de "
                  "la carpeta). Ejemplos: [bold]dam acciones -h[/bold]")


# ---------- Autocompletado con TAB ----------
# Al pulsar TAB la terminal ejecuta dam por debajo y enseña lo que devuelven estas funciones.
# Nunca deben fallar ni escribir nada: si algo va mal, simplemente no sugieren nada.

# Script de PowerShell: el de Typer, con dos arreglos. Con el original, un TAB en una ruta
# devolvía una línea vacía, PowerShell daba error y las variables _DAM_COMPLETE... se quedaban
# puestas: desde entonces, cada «dam» de esa ventana solo imprimía una línea en blanco.
#   1. Se salta las sugerencias vacías (PowerShell no acepta una sugerencia vacía).
#   2. try/finally: borra SIEMPRE las variables, aunque algo falle o pulses Ctrl+C.
# Sin sugerencias, PowerShell completa la ruta él solo, como siempre.
SCRIPT_TAB_POWERSHELL = """
Import-Module PSReadLine
Set-PSReadLineKeyHandler -Chord Tab -Function MenuComplete
$scriptblock = {
    param($wordToComplete, $commandAst, $cursorPosition)
    try {
        $Env:%(autocomplete_var)s = "complete_powershell"
        $Env:_TYPER_COMPLETE_ARGS = $commandAst.ToString()
        $Env:_TYPER_COMPLETE_WORD_TO_COMPLETE = $wordToComplete
        %(prog_name)s | ForEach-Object {
            $commandArray = $_ -Split ":::"
            $command = $commandArray[0]
            $helpString = $commandArray[1]
            if (-not [string]::IsNullOrWhiteSpace($command)) {
                if ([string]::IsNullOrWhiteSpace($helpString)) { $helpString = $command }
                [System.Management.Automation.CompletionResult]::new(
                    $command, $command, 'ParameterValue', $helpString)
            }
        }
    } finally {
        Remove-Item Env:%(autocomplete_var)s, Env:_TYPER_COMPLETE_ARGS, Env:_TYPER_COMPLETE_WORD_TO_COMPLETE -ErrorAction SilentlyContinue
    }
}
Register-ArgumentCompleter -Native -CommandName %(prog_name)s -ScriptBlock $scriptblock
"""
# Typer no deja cambiarlo por configuración: se sustituye su plantilla (la usan instalar.ps1,
# --install-completion y --show-completion). Si Typer cambia, lo detecta test_completado.py.
_completion_classes.PowerShellComplete.source_template = SCRIPT_TAB_POWERSHELL
for _terminal in ("powershell", "pwsh"):
    _completion_shared._completion_scripts[_terminal] = SCRIPT_TAB_POWERSHELL


def _config_al_completar(ctx: typer.Context) -> Optional[Path]:
    """El --config escrito en la línea (al completar no se ejecuta principal(), que es quien lo guarda).

    Al completar, Typer deja los valores como texto sin convertir: por eso el Path().
    """
    valor = ctx.find_root().params.get("config_ruta")
    return Path(valor) if valor else None


def completar_acciones(ctx: typer.Context, incomplete: str) -> list[tuple[str, str]]:
    """TAB en «dam ejecutar NOMBRE»: los nombres de acciones.json, con su descripción."""
    try:
        lista = config.cargar(config.buscar(_config_al_completar(ctx)))
    except (TareasError, OSError):
        return []
    return [(a["nombre"], a["descripcion"]) for a in lista if a["nombre"].startswith(incomplete)]


def completar_asignaturas(ctx: typer.Context, incomplete: str) -> list[str]:
    """TAB en «dam status/sync ASIGNATURA»: las carpetas que hay dentro de asignaturas/ del almacén."""
    ctx.obj = _config_al_completar(ctx)
    opcion = ctx.params.get("almacen")
    try:
        alm = _abrir_almacen(ctx, Path(opcion) if opcion else None)
        carpetas = [p for p in (alm.ruta / alm.carpeta_asignaturas).iterdir() if p.is_dir()]
    except (TareasError, OSError):
        return []
    return sorted(
        p.name
        for p in carpetas
        if p.name.startswith(incomplete)
        and not p.name.startswith(".")
        and p.name.lower() not in sincronizar.CARPETAS_PRIVADAS
    )


def con_virgulilla(ruta: Path) -> str:
    """C:\\Users\\HP\\pruebas-tareas\\x.pdf -> ~\\pruebas-tareas\\x.pdf: más corta y sin tu nombre de usuario."""
    casa = Path.home()
    try:
        return str(Path("~") / ruta.relative_to(casa))
    except ValueError:
        return str(ruta)


def pintar_tabla(nombre: str, resultados, simular: bool) -> None:
    titulo = f"{nombre} (SIMULACIÓN: no se ha tocado nada)" if simular else nombre
    tabla = Table(title=titulo)
    tabla.add_column("Fichero", overflow="fold")
    tabla.add_column("Destino", overflow="fold")
    tabla.add_column("Estado")
    con_detalle = any(r.nota for r in resultados)  # tokens, segundos, categoría, por qué se salta...
    if con_detalle:
        tabla.add_column("Detalle", overflow="fold")
    for r in resultados:
        destino = escape(con_virgulilla(r.destino)) if r.destino else "—"
        color = COLORES.get(r.estado, "white")
        fila = [escape(r.origen.name), destino, f"[{color}]{r.estado}[/{color}]"]
        if con_detalle:
            fila.append(escape(r.nota))
        tabla.add_row(*fila)
    consola.print(tabla)
    cuenta = {e: sum(1 for r in resultados if r.estado == e) for e in COLORES}
    consola.print(
        f"{len(resultados)} ficheros · {cuenta['hecho']} hechos · {cuenta['simulado']} simulados · "
        f"{cuenta['saltado']} saltados · {cuenta['error']} con error"
    )


@comando
@controlar_errores
def ejecutar(
    ctx: typer.Context,
    nombre: Annotated[str, typer.Argument(metavar="NOMBRE", help="Nombre de la acción (ver: dam acciones)", autocompletion=completar_acciones)],
    carpeta: Annotated[Optional[Path], typer.Argument(metavar="CARPETA|FICHERO", help="Carpeta sobre la que actuar, o un solo fichero (por defecto, el origen de la acción).")] = None,
    simular: Annotated[bool, typer.Option("--simular", help="Enseña qué haría sin tocar nada.")] = False,
    si: Annotated[bool, typer.Option("--si", help="No pregunta antes de actuar (solo si estás seguro).")] = False,
) -> None:
    """Ejecuta una acción de acciones.json sobre una carpeta (o un solo fichero).

    Sin CARPETA usa el «origen» de la acción. Con un FICHERO actúa solo sobre él, si cumple el filtro de la acción (si no, dice por qué y no hace nada). Empieza SIEMPRE con --simular: enseña una tabla fichero → destino sin tocar nada.

    Sin --simular, las acciones que borran (o que tienen «confirmar») enseñan primero la tabla y preguntan s/N; --si se salta la pregunta.

    Nunca sobrescribe: si el destino ya existe, añade « (1)». Sale con 1 si algún fichero falla.

    Una acción ordenar con «al_almacen»: true manda cada fichero a asignaturas/ASIGNATURA de tu almacén y, al acabar, pregunta si quieres hacer dam sync (con --si no lo hace: te lo recuerda).

    Con «por_tipo»: "~/Datos/POR-TIPO", lo que no es de ninguna asignatura va a POR-TIPO/DOCUMENTOS, IMAGENES, COMPRIMIDOS... Los ficheros del sistema, temporales y descargas a medias (desktop.ini, .crdownload, .part...) no se mueven nunca.
    """
    motor = Motor(config.cargar(config.buscar(ctx.obj)))
    previa = motor.acciones.get(nombre)
    if previa is not None and previa.necesita_ia and not simular:
        motor.proveedor = ProveedorCentro.desde_entorno()  # solo si hace falta: lo demás va sin red
    accion, ficheros = motor.preparar(nombre, carpeta)
    almacen = None
    if accion.config.get("al_almacen"):
        almacen = _abrir_almacen(ctx, None)
        asignaturas = almacen.ruta / almacen.carpeta_asignaturas
        if not asignaturas.is_dir():
            raise TareasError(f"No encuentro las asignaturas de tu almacén en «{asignaturas}». "
                              "Revisa la variable DAM_ALMACEN o «almacen» en acciones.json.")
        accion.config["destino"] = str(asignaturas)
    if not ficheros:
        consola.print("Ningún fichero cumple el filtro: no hay nada que hacer.")
        return
    if not simular and not si and (accion.destructiva or accion.config.get("confirmar")):
        previsto = accion.ejecutar(ficheros, True)  # vista previa: no toca nada
        pintar_tabla(nombre, previsto, True)
        n = sum(1 for r in previsto if r.estado == "simulado")
        if n == 0:
            consola.print("No hay nada que hacer.")
            return
        confirmar(f"¿{'BORRAR' if accion.destructiva else 'Aplicar la acción a'} {n} fichero(s)?")
    resultados = accion.ejecutar(ficheros, simular)
    pintar_tabla(nombre, resultados, simular)
    if simular:
        consola.print("Para hacerlo de verdad, repite la orden sin --simular.")
    # solo cuenta lo que ha entrado en el almacén (lo de «por_tipo» no se sube)
    hechos = sum(1 for r in resultados if r.estado == "hecho" and r.nota != "por tipo")
    if almacen is not None and hechos:
        if not (almacen.ruta / ".git").exists():  # p. ej. un almacén de prueba: los apuntes se quedan ahí
            consola.print(f"[yellow]Tu almacén ({escape(str(almacen.ruta))}) no es un repositorio git:[/yellow] "
                          "los apuntes ya están en él, pero dam sync no puede subirlos. Para eso, clónalo de GitHub.")
        elif si:
            consola.print("Para subir los apuntes a GitHub: [bold]dam sync[/bold]")
        elif preguntar(f"¿Hago ahora dam sync para subir {hechos} apunte(s) nuevo(s) a GitHub?"):
            _pintar_sync(almacen.sincronizar(None, f"ordenar: {hechos} apunte(s) nuevo(s)"))
        else:
            consola.print("Vale. Cuando quieras subirlos: [bold]dam sync[/bold]")
    if accion.corte_ia is not None:  # la IA se cayó a mitad: lo hecho, hecho; el resto, sin tocar
        raise accion.corte_ia
    if any(r.estado == "error" for r in resultados):
        raise typer.Exit(1)


@comando(nombre="comprobar-ia")
@controlar_errores
def comprobar_ia() -> None:
    """Comprueba la conexión con el servidor de IA (sin enseñar la clave).

    Lee CENTRO_IA_URL, CENTRO_IA_KEY, CENTRO_IA_CA y CENTRO_IA_MODELO de tu terminal o de un .env (mira .env.example) y hace una pregunta mínima al modelo (5 tokens como mucho).

    Sale con 4 si no hay clave, no hay red, falta el certificado o el servidor no responde.
    """
    proveedor = ProveedorCentro.desde_entorno()
    consola.print(f"Servidor: {escape(proveedor.url)}  ·  modelo: {escape(proveedor.modelo)}  ·  clave: definida")
    r = proveedor.completar("Responde solo con la palabra: ok", "¿Me oyes?", max_tokens=5)
    consola.print(f"[green]✔ El modelo responde «{escape(r.texto)}» en {r.segundos:.1f} s[/green] ({r.resumen()})")


# ---------- configurar: tu ciclo y tus asignaturas ----------
def _leer_si_vale(ruta: Path) -> dict:
    """El acciones.json que ya tienes (para proponer lo de la última vez); si está roto, como si no hubiera."""
    try:
        return config.leer_json(ruta) if ruta.is_file() else {}
    except ConfigError:
        return {}


def _elegir_plantilla(plantilla: Optional[Path], destino: Path) -> Path:
    """De dónde salen las acciones: --plantilla, el fichero que ya tienes o el acciones.json de esta carpeta."""
    if plantilla is not None:
        plantilla = plantilla.expanduser()
        if not plantilla.is_file():
            raise ConfigError(f"No encuentro la plantilla {plantilla}")
        return plantilla
    for candidato in (destino, Path.cwd() / config.NOMBRE_FICHERO):
        if candidato.is_file():
            return candidato
    raise ConfigError(
        f"No tengo acciones de partida. Descarga el ejemplo ({URL_EJEMPLO_ACCIONES}) "
        "y repite con --plantilla RUTA, o lanza dam configurar desde la carpeta del repositorio."
    )


def _pedir_ciclo(defecto: Optional[str]) -> str:
    opciones = [*ciclos.CICLOS, ciclos.OTRO]
    consola.print("\n[bold]¿Qué estudias?[/bold]")
    for i, clave in enumerate(opciones, start=1):
        if clave == ciclos.OTRO:
            texto = "Otro ciclo (escribes tú las asignaturas)"
        else:
            texto = f"{ciclos.CICLOS[clave].nombre} — {ciclos.CICLOS[clave].titulo}"
        consola.print(f"  {i}. {escape(texto)}")
    numero_defecto = str(opciones.index(defecto) + 1) if defecto in opciones else None
    while True:
        respuesta = typer.prompt("Número o nombre", default=numero_defecto).strip()
        if respuesta.isdigit() and 1 <= int(respuesta) <= len(opciones):
            return opciones[int(respuesta) - 1]
        try:
            return ciclos.ciclo_valido(respuesta)
        except ValueError as e:
            consola.print(f"[red]{escape(str(e))}[/red]")


def _pedir_cursos(defecto: list[int]) -> list[int]:
    texto_defecto = ",".join(str(c) for c in defecto)
    while True:
        respuesta = typer.prompt("¿Qué curso? 1, 2 o 1,2 (los dos)", default=texto_defecto)
        partes = [p.strip().rstrip("º") for p in respuesta.split(",") if p.strip()]
        if partes and all(p in ("1", "2") for p in partes):
            return sorted({int(p) for p in partes})
        consola.print("[red]Escribe 1, 2 o 1,2[/red]")


def _nueva_asignatura(texto: str) -> tuple[str, list[str]]:
    """'fol=fol,contrato' -> ('fol', ['fol', 'contrato']). Sin «=», la palabra clave es el propio nombre."""
    nombre, _, palabras = texto.partition("=")
    carpeta = ciclos.a_nombre_de_carpeta(nombre)
    if not carpeta:
        raise TareasError(f"«{texto}» no sirve como nombre de asignatura (usa letras y números)")
    if carpeta.replace("-", "").isdigit():  # «3»: casi seguro que es el número de una de la lista
        raise TareasError(f"«{nombre.strip()}» es un número: escribe el NOMBRE de la asignatura nueva "
                          "(las de la lista que no quitas ya se quedan)")
    lista = [p.strip().lower() for p in palabras.split(",") if p.strip()] or [nombre.strip().lower()]
    return carpeta, lista


def _tabla_asignaturas(asignaturas: dict[str, list[str]]) -> None:
    tabla = Table(box=box.SIMPLE_HEAD, header_style="bold")
    tabla.add_column("#", justify="right")
    tabla.add_column("Carpeta", style="cyan")
    tabla.add_column("Asignatura")
    tabla.add_column("Palabras clave")
    for i, (nombre, palabras) in enumerate(asignaturas.items(), start=1):
        largo = ciclos.ASIGNATURAS[nombre].castellano if nombre in ciclos.ASIGNATURAS else "(tuya)"
        resumen = ", ".join(palabras[:4]) + (f" y {len(palabras) - 4} más" if len(palabras) > 4 else "")
        tabla.add_row(str(i), escape(nombre), escape(largo), escape(resumen))
    consola.print(tabla)


def _editar_asignaturas(asignaturas: dict[str, list[str]]) -> dict[str, list[str]]:
    """Pregunta qué quitar (por número) y qué añadir (por nombre). Enter = nada."""
    nombres = list(asignaturas)
    quitar = typer.prompt("Números de las que QUITAS, separados por comas; las demás se quedan (Enter: ninguna)",
                          default="", show_default=False)
    for parte in (p.strip() for p in quitar.split(",") if p.strip()):
        if parte.isdigit() and 1 <= int(parte) <= len(nombres):
            asignaturas.pop(nombres[int(parte) - 1], None)
        else:
            consola.print(f"[yellow]«{escape(parte)}» no es ningún número de la lista: no lo tengo en cuenta[/yellow]")
    if asignaturas:
        consola.print(f"Te quedas con: {escape(', '.join(asignaturas))}")
    while True:  # si escribe un número en vez de un nombre, se le explica y se repite la pregunta
        nuevas = typer.prompt("Asignaturas NUEVAS que añades: escribe su nombre, separadas por comas (Enter: ninguna)",
                              default="", show_default=False)
        try:
            lista = [(n, _nueva_asignatura(n)[0]) for n in (x.strip() for x in nuevas.split(",")) if n]
            break
        except TareasError as e:
            consola.print(f"[yellow]{escape(str(e))}[/yellow]")
    for nombre, carpeta in lista:
        palabras = typer.prompt(f"  Palabras clave de «{carpeta}» (separadas por comas)", default=nombre.lower())
        asignaturas[carpeta] = _nueva_asignatura(f"{nombre}={palabras}")[1]
    return asignaturas


@comando
@controlar_errores
def configurar(
    ctx: typer.Context,
    ciclo: Annotated[Optional[str], typer.Option("--ciclo", metavar="CICLO", help="smx, dam, daw, asir (o asix) u otro. Sin ella, te lo pregunta.")] = None,
    curso: Annotated[Optional[list[int]], typer.Option("--curso", metavar="N", help="1 o 2. Repítela para los dos: --curso 1 --curso 2.")] = None,
    quitar: Annotated[Optional[list[str]], typer.Option("--quitar", metavar="CARPETA", help="Quita esa asignatura de la lista del ciclo (se puede repetir).")] = None,
    nueva: Annotated[Optional[list[str]], typer.Option("--nueva", metavar="NOMBRE=PALABRAS", help='Añade una asignatura: --nueva "fol=fol,contrato,nomina" (se puede repetir).')] = None,
    plantilla: Annotated[Optional[Path], typer.Option("--plantilla", metavar="RUTA", help="acciones.json del que salen las acciones (por defecto: el que ya tienes).")] = None,
    crear_carpetas: Annotated[bool, typer.Option("--crear-carpetas", help="Crea en el almacén las carpetas de asignatura que falten, sin preguntar.")] = False,
    si: Annotated[bool, typer.Option("--si", help="No pregunta nada: usa las opciones y lo que elegiste la última vez.")] = False,
    simular: Annotated[bool, typer.Option("--simular", help="Enseña cómo quedaría, sin guardar nada.")] = False,
) -> None:
    """Pregunta tu ciclo y curso y pone tus asignaturas en acciones.json.

    Como adduser en Linux: eliges ciclo (SMX, DAM, DAW, ASIR/ASIX u otro) y curso, y dam ya sabe qué asignaturas tienes. Puedes quitar y añadir las que quieras. Con eso rellena las carpetas y palabras clave de «ordenar» y las categorías de «clasificar».

    Guarda en ~/.config/dam/acciones.json (o en el de --config), con una copia del anterior. Si eliges las mismas asignaturas que ya tenías, esas acciones no cambian. Al acabar, ofrece crear las carpetas que falten en tu almacén.

    Lo lanza el instalador. Repítelo cuando cambies de curso: te propone lo de la última vez.
    """
    destino = (ctx.obj or config.sitios_de_busqueda()[-1]).expanduser()
    origen = _elegir_plantilla(plantilla, destino)
    base = config.leer_json(origen)
    actual = _leer_si_vale(destino)
    anterior = configurar_mod.perfil(actual) or configurar_mod.perfil(base) or {}
    consola.print(f"Acciones de partida: {escape(str(origen))}")

    # 1. Ciclo y curso
    if ciclo is not None:
        try:
            ciclo = ciclos.ciclo_valido(ciclo)
        except ValueError as e:
            raise typer.BadParameter(str(e), param_hint="--ciclo") from None
    elif si:
        if not anterior.get("ciclo"):
            raise typer.BadParameter("con --si hace falta --ciclo (no hay nada elegido de otra vez)", param_hint="--ciclo")
        ciclo = ciclos.ciclo_valido(anterior["ciclo"])
    else:
        ciclo = _pedir_ciclo(anterior.get("ciclo"))
    mismo_ciclo = anterior.get("ciclo") == ciclo
    if curso:
        if any(c not in (1, 2) for c in curso):
            raise typer.BadParameter("el curso es 1 o 2", param_hint="--curso")
        cursos = sorted(set(curso))
    elif ciclo == ciclos.OTRO:
        cursos = [1]
    elif si:
        cursos = anterior.get("cursos", [1]) if mismo_ciclo else [1]
    else:
        cursos = _pedir_cursos(anterior.get("cursos", [1]) if mismo_ciclo else [1])

    # 2. Asignaturas: las de la última vez si repites ciclo y curso; si no, las del ciclo
    if mismo_ciclo and anterior.get("cursos") == cursos and configurar_mod.asignaturas_actuales(actual):
        guardadas = configurar_mod.asignaturas_actuales(actual)
        asignaturas = configurar_mod.palabras_al_dia(guardadas)  # lo que haya aprendido ciclos.py desde entonces
        nuevas = sum(len(asignaturas[a]) - len(guardadas[a]) for a in asignaturas)
        consola.print(f"\nTus asignaturas de la última vez ({escape(ciclos.etiqueta(ciclo, cursos))})"
                      + (f", con {nuevas} palabras clave nuevas del vocabulario:" if nuevas else ":"))
    else:
        asignaturas = ciclos.asignaturas_de(ciclo, cursos)
        if asignaturas:
            consola.print(f"\nAsignaturas de {escape(ciclos.etiqueta(ciclo, cursos))}:")
    for nombre in quitar or []:
        if asignaturas.pop(nombre, None) is None:
            raise typer.BadParameter(f"«{nombre}» no está en la lista: {', '.join(asignaturas)}", param_hint="--quitar")
    for texto in nueva or []:
        carpeta, palabras = _nueva_asignatura(texto)
        asignaturas[carpeta] = palabras
    if asignaturas:
        _tabla_asignaturas(asignaturas)
    if not si and (not asignaturas or preguntar("¿Quieres quitar o añadir alguna?")):
        asignaturas = _editar_asignaturas(asignaturas)
        _tabla_asignaturas(asignaturas)
    if not asignaturas:
        raise ConfigError("Sin asignaturas no hay nada que configurar (añádelas con --nueva NOMBRE=PALABRAS)")

    # 3. Aplicar, validar y guardar
    datos = configurar_mod.aplicar(base, ciclo, cursos, asignaturas)
    config.validar_datos(datos, destino.name)
    if simular:
        consola.print(f"[cyan](simulado) Quedaría bien: {len(datos['acciones'])} acciones válidas. "
                      f"No he guardado nada en {escape(str(destino))}[/cyan]")
        return
    if not si:
        confirmar(f"¿Lo guardo en {destino}?")
    copia = configurar_mod.guardar(datos, destino)
    consola.print(f"[green]✔ Guardado en {escape(str(destino))}[/green]: {len(asignaturas)} asignaturas, "
                  f"{len(datos['acciones'])} acciones válidas")
    if copia:
        consola.print(f"  La versión anterior está en {escape(str(copia))}")
    if ctx.obj is None and (Path.cwd() / config.NOMBRE_FICHERO).is_file() and Path.cwd() / config.NOMBRE_FICHERO != destino:
        consola.print("[yellow]Ojo: en esta carpeta hay otro acciones.json y aquí dam usa ese. "
                      "Fuera de esta carpeta, dam usa el que acabo de guardar.[/yellow]")

    # 4. Carpetas en el almacén
    try:
        almacen = _abrir_almacen(ctx, None)
    except ConfigError:
        almacen = None
    base_asignaturas = almacen.ruta / almacen.carpeta_asignaturas if almacen else None
    if base_asignaturas is None or not almacen.ruta.is_dir():
        consola.print("Cuando tengas el almacén clonado, repite dam configurar para crear las carpetas de asignatura.")
        return
    faltan = configurar_mod.carpetas_que_faltan(base_asignaturas, list(asignaturas))
    if not faltan:
        consola.print(f"[green]✔ Tu almacén ya tiene todas las carpetas[/green] ({escape(str(base_asignaturas))})")
    elif crear_carpetas or (not si and preguntar(f"¿Creo en tu almacén las carpetas que faltan ({', '.join(faltan)})?")):
        configurar_mod.crear_carpetas(base_asignaturas, faltan)
        consola.print(f"[green]✔ Creadas {len(faltan)} carpetas en {escape(str(base_asignaturas))}[/green]. "
                      "Súbelas con: dam sync")
    else:
        consola.print(f"[yellow]Faltan en tu almacén: {escape(', '.join(faltan))}.[/yellow] "
                      "«ordenar» no mete ficheros en asignaturas sin carpeta (créalas con --crear-carpetas).")


# ---------- almacén de apuntes (git) ----------
OpcionAlmacen = Annotated[
    Optional[Path],
    typer.Option(
        "--almacen",
        metavar="RUTA",
        help="Carpeta del almacén. Si no la pones: variable DAM_ALMACEN o «almacen» de acciones.json.",
    ),
]


def _abrir_almacen(ctx: typer.Context, opcion: Optional[Path]) -> sincronizar.Almacen:
    ruta, carpeta = opcion, "asignaturas"
    if ruta is None and os.environ.get("DAM_ALMACEN"):
        ruta = Path(os.environ["DAM_ALMACEN"])
    if ruta is None:
        try:
            fichero = config.buscar(ctx.obj)
        except ConfigError:
            if ctx.obj is not None:  # el usuario pidió un --config concreto y no existe
                raise
            fichero = None
        datos = config.almacen(fichero) if fichero else None
        if datos:
            ruta, carpeta = Path(datos["ruta"]), datos.get("asignaturas", "asignaturas")
    if ruta is None:
        raise ConfigError(
            "No sé dónde está tu almacén. Añade «almacen»: {\"ruta\": \"~/DAM-almacen\"} a "
            "acciones.json, usa --almacen RUTA o define la variable DAM_ALMACEN."
        )
    return sincronizar.Almacen(ruta, carpeta)


def _lista(titulo: str, color: str, cambios: list[sincronizar.Cambio], limite: int = 15) -> None:
    if not cambios:
        return
    consola.print(f"\n[bold {color}]{titulo} ({len(cambios)})[/bold {color}]")
    for c in cambios[:limite]:
        consola.print(f"  [{color}]{c.estado:<10}[/{color}] {escape(c.ruta)}")
    if len(cambios) > limite:
        consola.print(f"  ... y {len(cambios) - limite} más")


@comando
@controlar_errores
def status(
    ctx: typer.Context,
    asignatura: Annotated[Optional[str], typer.Argument(metavar="ASIGNATURA", help="Solo mira esa asignatura (carpeta dentro de asignaturas/).", autocompletion=completar_asignaturas)] = None,
    almacen: OpcionAlmacen = None,
) -> None:
    """Muestra qué has cambiado y qué hay nuevo en GitHub.

    No modifica nada. Lista los archivos modificados, nuevos y borrados en local, los commits sin subir y los archivos que hay por descargar.

    Si tienes cambios sin subir Y hay cambios nuevos en GitHub, te avisa del peligro. Sin internet funciona igual, con lo último que sabe de GitHub.

    Con ASIGNATURA solo mira asignaturas/ASIGNATURA.
    """
    alm = _abrir_almacen(ctx, almacen)
    s = alm.analizar(asignatura, tolerante=True)
    alcance = f"asignatura «{asignatura}»" if asignatura else "todo el almacén"
    consola.print(f"[bold]Almacén:[/bold] {escape(str(alm.ruta))}  ({escape(s.rama)} ↔ {escape(s.remota)}) · {alcance}")
    if s.sin_conexion:
        consola.print(f"[yellow]⚠ {escape(s.sin_conexion)} Muestro lo último que sé de GitHub.[/yellow]")
    _lista("Archivos modificados (locales, no subidos)", "yellow", [c for c in s.locales if c.estado == "modificado"])
    _lista("Archivos nuevos (locales, sin rastrear)", "green", [c for c in s.locales if c.estado == "nuevo"])
    _lista("Archivos borrados en local", "red", [c for c in s.locales if c.estado == "borrado"])
    if s.adelantados:
        consola.print(f"\n[bold yellow]Commits sin subir: {s.adelantados}[/bold yellow]")
    _lista("Archivos por descargar (cambios en GitHub que no tienes)", "cyan", s.remotos)
    if not s.hay_local and not s.hay_remoto:
        consola.print("\n[green]✔ Todo está actualizado.[/green]")
    if s.hay_local and s.hay_remoto:
        consola.print(
            "\n[bold red]⚠️ Peligro: Tienes archivos sin subir y hay archivos nuevos en GitHub. "
            "Haz un commit o guarda una copia antes de sincronizar.[/bold red]"
        )


@comando
@controlar_errores
def sync(
    ctx: typer.Context,
    asignatura: Annotated[Optional[str], typer.Argument(metavar="ASIGNATURA", help="Solo esa asignatura (carpeta dentro de asignaturas/). Sin ella, todo el almacén.", autocompletion=completar_asignaturas)] = None,
    mensaje: Annotated[Optional[str], typer.Argument(metavar="MENSAJE", help="Mensaje del commit (con ASIGNATURA). Para el resto usa -m.")] = None,
    mensaje_opcion: Annotated[Optional[str], typer.Option("-m", "--mensaje", metavar="TEXTO", help="Mensaje del commit; sirve con o sin ASIGNATURA.")] = None,
    integrar: Annotated[bool, typer.Option("--integrar", help="Si hay cambios en los dos lados: guarda lo tuyo, hace pull --rebase y sube.")] = False,
    simular: Annotated[bool, typer.Option("--simular", help="Enseña qué haría sin tocar nada")] = False,
    almacen: OpcionAlmacen = None,
) -> None:
    """Sincroniza el almacén con GitHub sin pisar nada ante la duda.

    Hace primero un fetch y decide según lo que encuentre:

    • Nada nuevo en ningún lado: «Todo está actualizado».

    • Solo cambios en GitHub: los descarga (pull).

    • Solo cambios tuyos: add, commit con el mensaje «\\[asignatura]: texto» y push.

    • Cambios en los DOS lados: se para, enseña el diff y sale con 1. Con --integrar guarda lo tuyo y hace pull --rebase; si hay conflicto real lo deshace sin perder nada.

    Con ASIGNATURA solo se suben los cambios de asignaturas/ASIGNATURA. Para todo el almacén con tu mensaje usa -m (en PowerShell el texto vacío "" desaparece, no lo uses).

    Se niega a subir .env, claves (.pem, .key...) y ficheros de más de 95 MB.
    """
    informe = _abrir_almacen(ctx, almacen).sincronizar(asignatura, mensaje_opcion or mensaje, integrar, simular)
    _pintar_sync(informe)
    if informe.estado == "pendiente":
        raise typer.Exit(1)


def _pintar_sync(informe: sincronizar.InformeSync) -> None:
    """Lo que cuenta dam sync (también lo usa ordenar cuando sincroniza al acabar)."""
    for linea in informe.mensajes:
        color = "yellow" if informe.estado == "pendiente" else "green"
        consola.print(f"[{color}]{escape(linea)}[/{color}]")
    if informe.detalle:
        consola.print(f"\n{escape(informe.detalle)}")


# ---------- seguridad ----------
@comando
@controlar_errores
def scan_secrets(
    ruta: Annotated[Path, typer.Argument(metavar="RUTA", help="Carpeta a revisar (por defecto, la actual).")] = Path("."),
    staged: Annotated[bool, typer.Option("--staged", help="Solo lo preparado para el próximo commit (git add).")] = False,
    historial: Annotated[bool, typer.Option("--historial", help="Todo el historial de git, commit a commit.")] = False,
    alta: Annotated[bool, typer.Option("--alta", help="Solo hallazgos seguros (menos falsos avisos).")] = False,
) -> None:
    """Busca claves, tokens y contraseñas expuestas antes de hacer push.

    Revisa lo que se subiría a git (los ficheros ignorados no cuentan) y detecta MongoDB, GitHub, Gemini o Google, Resend, AWS, Slack, claves sk-, claves privadas, ficheros .env sin ignorar y asignaciones sospechosas como password = ...

    Nunca imprime un secreto entero: solo las primeras letras y la longitud. Sale con 0 si está limpio y con 1 si encuentra algo. Para saltarte un falso aviso añade dam:ignore en esa línea.

    Si una clave ya llegó a GitHub, bórrala Y cámbiala (revócala en el servicio): seguirá en el historial.
    """
    if staged and historial:
        raise typer.BadParameter("usa --staged o --historial, no los dos a la vez")
    ruta = ruta.expanduser()
    if not ruta.is_dir():
        raise TareasError(f"«{ruta}» no existe o no es una carpeta.")
    revisados = omitidos = None
    if staged:
        alcance, hallazgos = "lo preparado para commit", escanear.escanear_staged(ruta, alta)
    elif historial:
        alcance, hallazgos = "todo el historial de git", escanear.escanear_historial(ruta, alta)
    else:
        hallazgos, revisados, omitidos = escanear.escanear_arbol(ruta, alta)
        alcance = f"{revisados} ficheros ({omitidos} omitidos: binarios o muy grandes)"
    if not hallazgos:
        consola.print(f"[green]✔ Sin claves a la vista[/green] en {alcance}.")
        return
    pintar_hallazgos(hallazgos, f"Posibles secretos en {alcance}")
    consola.print(f"[red]✘ {len(hallazgos)} hallazgo(s).[/red] Quítalos, y si ya se subieron, cámbialos en el servicio.")
    raise typer.Exit(1)


def pintar_hallazgos(hallazgos: list[escanear.Hallazgo], titulo: str) -> None:
    """Tabla de scan-secrets (también la usa entregar). La muestra ya viene enmascarada."""
    tabla = Table(title=titulo)
    tabla.add_column("Dónde", overflow="fold")
    tabla.add_column("Línea", justify="right")
    tabla.add_column("Qué parece", overflow="fold")
    tabla.add_column("Muestra")
    tabla.add_column("Confianza")
    for h in hallazgos:
        color = "red" if h.confianza == "alta" else "yellow"
        tabla.add_row(escape(h.donde), str(h.linea or "—"), escape(h.tipo), escape(h.muestra),
                      f"[{color}]{h.confianza}[/{color}]")
    consola.print(tabla)


@comando
@controlar_errores
def instalar_hook(
    ruta: Annotated[Path, typer.Argument(metavar="REPO", help="Repositorio donde instalarlo (por defecto, el actual).")] = Path("."),
    quitar: Annotated[bool, typer.Option("--quitar", help="Desinstala el hook (solo si es de dam).")] = False,
    forzar: Annotated[bool, typer.Option("--forzar", help="Reemplaza un hook pre-commit que no sea de dam.")] = False,
) -> None:
    """Revisa claves en cada git commit, sin acordarte.

    Instala un hook pre-commit que ejecuta «dam scan-secrets --staged» justo antes de cada commit y lo cancela si encuentra algo. Se instala una vez por repositorio.

    No pisa un hook que no sea de dam (salvo --forzar). Si «dam» no está en el PATH, avisa pero no bloquea. Para saltarlo una vez: git commit --no-verify.
    """
    ruta = ruta.expanduser()
    mensaje = hook.quitar(ruta) if quitar else hook.instalar(ruta, forzar)
    consola.print(f"[green]✔ {escape(mensaje)}[/green]")


@comando
@controlar_errores
def doctor(
    carpeta: Annotated[Path, typer.Argument(metavar="CARPETA", help="Proyecto que quieres revisar (por defecto, la carpeta actual).")] = Path("."),
) -> None:
    """Revisa que un proyecto esté sano antes de subirlo o entregarlo.

    Básicas (si falla alguna, sale con 1): repositorio git, .gitignore, .env ignorado y sin subir, .env.example con las mismas variables que tu .env, README y sin secretos a la vista.

    Recomendadas (solo avisan): tests, dependencias declaradas (pyproject.toml, requirements.txt o package.json), CI con GitHub Actions y ficheros de más de 50 MB.

    No cambia nada. Del .env solo lee los NOMBRES de las variables, nunca los valores.
    """
    informe = doctor_mod.revisar(carpeta)
    tabla = Table(title=f"Revisión de {escape(str(informe.carpeta))}")
    tabla.add_column("Comprobación", overflow="fold")
    tabla.add_column("Estado", no_wrap=True)
    tabla.add_column("Detalle", overflow="fold")
    estados = {"ok": "[green]✔ ok[/green]", "falta": "[red]✘ falta[/red]",
               "aviso": "[yellow]⚠ aviso[/yellow]", "no aplica": "[dim]— no aplica[/dim]"}
    for c in informe.comprobaciones:
        nombre = c.nombre + ("" if c.basica else " (recomendada)")
        tabla.add_row(escape(nombre), estados[c.estado], escape(c.detalle))
    consola.print(tabla)
    consola.print(f"{informe.correctas} de {len(informe.aplicables)} comprobaciones bien.")
    for repo in informe.repos_dentro:
        consola.print(f'[yellow]⚠ Parece la carpeta de fuera. Revisa el proyecto:[/yellow]  '
                      f'dam doctor "{escape(str(informe.carpeta / repo))}"')
    if informe.fallan_basicas:
        consola.print(f"[red]✘ Falla lo básico: {escape(', '.join(informe.fallan_basicas))}[/red]")
        raise typer.Exit(1)
    consola.print("[green]✔ Lo básico está bien.[/green]")


COLORES_ETIQUETA = {"Verificado": "green", "Hipótesis": "magenta", "Pendiente": "yellow"}
COLORES_ESTADO = {"Pendiente": "yellow", "En curso": "cyan", "Verificado": "green", "Descartado": "dim",
                  "sin estado": "white"}


def _pintar_etiquetas(informe: pendientes_mod.Informe) -> None:
    """Tabla con las etiquetas de cada fichero y una fila de total."""
    tabla = Table(title="Etiquetas por fichero")
    tabla.add_column("Fichero", overflow="fold")
    for tipo in pendientes_mod.TIPOS:
        tabla.add_column(f"[{COLORES_ETIQUETA[tipo]}]{tipo}[/]", justify="right")
    tabla.add_column("Verificado sin fecha", justify="right")
    for fichero in dict.fromkeys(e.fichero for e in informe.etiquetas):  # en orden, sin repetir
        c = informe.cuenta(fichero)
        tabla.add_row(escape(fichero), *(str(c[t] or "") for t in pendientes_mod.TIPOS), str(c["sin fecha"] or ""))
    total = informe.cuenta()
    tabla.add_row("[bold]Total[/bold]", *(f"[bold]{total[t]}[/bold]" for t in pendientes_mod.TIPOS),
                  f"[bold]{total['sin fecha']}[/bold]")
    consola.print(tabla)


def _pintar_lista_etiquetas(titulo: str, etiquetas: list[pendientes_mod.Etiqueta]) -> None:
    if not etiquetas:
        return
    tabla = Table(title=f"{titulo} ({len(etiquetas)})")
    tabla.add_column("Dónde", overflow="fold", no_wrap=True)
    tabla.add_column("Tipo")
    tabla.add_column("Texto", overflow="fold")
    for e in etiquetas:
        color = COLORES_ETIQUETA[e.tipo]
        tabla.add_row(escape(f"{e.fichero}:{e.linea}"), f"[{color}]{e.tipo}[/{color}]", escape(e.texto))
    consola.print(tabla)


def _pintar_registro(filas: list[pendientes_mod.FilaRegistro], quien: Optional[str], resumen: bool) -> None:
    for fichero in dict.fromkeys(f.fichero for f in filas):
        del_fichero = [f for f in filas if f.fichero == fichero]
        estados = {}
        for f in del_fichero:
            estados[f.estado] = estados.get(f.estado, 0) + 1
        texto_estados = " · ".join(f"[{COLORES_ESTADO[e]}]{e} {n}[/]" for e, n in estados.items())
        consola.print(f"\n[bold]Registro {escape(fichero)}:[/bold] {len(del_fichero)} filas · {texto_estados}")

        abiertas = [f for f in del_fichero if f.abierta]
        if abiertas:
            reparto = " · ".join(f"{escape(p)} {n}" for p, n in pendientes_mod.reparto(abiertas).items())
            consola.print(f"Abiertas por persona (una fila compartida cuenta para cada uno): {reparto}")
        if quien:
            abiertas = [f for f in abiertas if pendientes_mod.es_de(f, quien)]
        if resumen or not abiertas:
            if quien and not abiertas:
                consola.print(f"[green]✔ A «{escape(quien)}» no le queda nada abierto.[/green]")
            continue
        titulo = f"Abiertas de {quien} (y de «Todos»)" if quien else "Abiertas (Pendiente o En curso)"
        tabla = Table(title=f"{escape(titulo)}: {len(abiertas)}")
        tabla.add_column("#", justify="right")
        tabla.add_column("Dato", overflow="fold")
        tabla.add_column("Responsable", overflow="fold")
        tabla.add_column("Estado", no_wrap=True)
        for f in abiertas:
            color = COLORES_ESTADO[f.estado]
            tabla.add_row(escape(f.numero), escape(f.dato), escape(f.responsable), f"[{color}]{f.estado}[/{color}]")
        consola.print(tabla)


@comando
@controlar_errores
def pendientes(
    carpeta: Annotated[Path, typer.Argument(metavar="CARPETA", help="Proyecto cuya documentación quieres revisar (por defecto, la carpeta actual).")] = Path("."),
    quien: Annotated[Optional[str], typer.Option("--quien", metavar="NOMBRE", help="Solo las filas del registro de esa persona (y las de «Todos»).")] = None,
    resumen: Annotated[bool, typer.Option("--resumen", help="Solo los números, sin las listas.")] = False,
) -> None:
    """Cuenta lo verificado y lo pendiente en la documentación de un proyecto.

    Busca en los .md las etiquetas \\[Verificado], \\[Hipótesis] y \\[Pendiente] (también con texto detrás: \\[Verificado, entrevista 4, 29/10/2026]) y las cuenta por fichero. Un \\[Verificado] sin fecha en su línea sale aparte: le falta la fuente.

    Si hay un pendientes.md con una tabla de columnas #, Dato, Responsable y Estado, resume el registro y lista lo abierto (Pendiente o En curso).

    No cuenta las líneas de leyenda, los enlaces \\[Pendiente](x.md), docs/historico/ ni las líneas con dam:ignore. No cambia nada.
    """
    informe = pendientes_mod.revisar(carpeta)
    consola.print(f"[bold]Documentación de[/bold] {escape(str(informe.carpeta))}: {len(informe.ficheros)} ficheros .md")
    if not informe.etiquetas and not informe.registro:
        consola.print("No hay etiquetas \\[Verificado], \\[Hipótesis] ni \\[Pendiente], ni registro de pendientes.")
        return
    if informe.etiquetas:
        _pintar_etiquetas(informe)
    if not resumen and not quien:  # con --quien, lo que importa es el registro
        sin_verificar = [e for e in informe.etiquetas if e.tipo != "Verificado"]
        sin_fecha = [e for e in informe.etiquetas if e.tipo == "Verificado" and not e.con_fecha]
        _pintar_lista_etiquetas("Sin verificar en los documentos", sin_verificar)
        _pintar_lista_etiquetas("Verificado, pero sin fecha en la línea", sin_fecha)
    if informe.registro:
        _pintar_registro(informe.registro, quien, resumen)
    elif quien:
        consola.print("[yellow]⚠ No hay registro (pendientes.md con columna Responsable): --quien no filtra nada.[/yellow]")


@comando
@controlar_errores
def entregar(
    carpeta: Annotated[Path, typer.Argument(metavar="CARPETA", help="Proyecto que quieres entregar (por defecto, la carpeta actual).")] = Path("."),
    destino: Annotated[Optional[Path], typer.Option("--destino", metavar="CARPETA", help="Dónde dejar el zip (por defecto, al lado del proyecto).")] = None,
    nombre: Annotated[Optional[str], typer.Option("--nombre", metavar="NOMBRE", help="Nombre del zip (por defecto, CARPETA_AAAA-MM-DD.zip).")] = None,
    simular: Annotated[bool, typer.Option("--simular", help="Enseña qué entraría en el zip sin crearlo.")] = False,
) -> None:
    """Empaqueta un proyecto en un .zip limpio, listo para entregar.

    Deja fuera .env, claves privadas, .git, .venv, node_modules, __pycache__ y la basura del sistema (Thumbs.db, .DS_Store). Si la carpeta es un repositorio git, tampoco entra lo que ignora .gitignore.

    Antes de crear el zip pasa scan-secrets sobre lo que va dentro: si encuentra un secreto seguro, NO lo crea y sale con 1. Los avisos «posibles» se enseñan, pero no bloquean.

    Nunca sobrescribe: si el zip ya existe, añade « (1)». Dentro del zip todo va en una carpeta con el nombre del proyecto.
    """
    plan = entregar_mod.preparar(carpeta, destino, nombre)
    origen = "respetando su .gitignore" if plan.con_git else "no es un repositorio git"
    consola.print(f"[bold]Proyecto:[/bold] {escape(str(plan.carpeta))} ({origen})")

    if simular:
        consola.print(f"\n[bold green]Entraría en el zip ({len(plan.incluidos)}):[/bold green]")
        for rel in plan.incluidos:
            consola.print(f"  {escape(rel)}")
    if plan.excluidos:
        consola.print("\n[bold yellow]Se queda fuera:[/bold yellow]")
        for motivo, rutas in plan.excluidos.items():
            muestra = ", ".join(rutas[:6]) + (f" y {len(rutas) - 6} más" if len(rutas) > 6 else "")
            consola.print(f"  [yellow]{escape(motivo)}:[/yellow] {escape(muestra)}")

    if plan.hallazgos:
        pintar_hallazgos(plan.hallazgos, "Posibles secretos dentro de la entrega")
    if plan.bloqueado:
        consola.print("[red]✘ Hay secretos dentro: no creo el zip.[/red] Sácalos a .env (y ponlo en .gitignore) "
                      "o, si es un falso aviso, añade dam:ignore en esa línea.")
        raise typer.Exit(1)
    if plan.hallazgos:
        consola.print("[yellow]⚠ Revisa los avisos de arriba antes de entregar.[/yellow]")

    resumen = f"{len(plan.incluidos)} ficheros · {tamano_legible(plan.tamano)} sin comprimir"
    if simular:
        consola.print(f"\n[cyan]SIMULACIÓN:[/cyan] {resumen} → {escape(str(plan.zip))}")
        consola.print("Para crearlo de verdad, repite la orden sin --simular.")
        return
    zip_creado = entregar_mod.crear_zip(plan)
    consola.print(f"\n[green]✔ Creado[/green] {escape(str(zip_creado))} "
                  f"({resumen} · {tamano_legible(zip_creado.stat().st_size)} el zip)")


# ---------- tus datos: organizar el PC ----------
def _pintar_ficheros(titulo: str, color: str, lista: list[inventario_mod.Fichero], top: int) -> None:
    """Una lista del inventario (instaladores, basura...) con su total; si está vacía, no sale."""
    if not lista:
        return
    titulo = f"[{color}]{titulo}[/{color}] ({len(lista)} · {inventario_mod.resumen_tamano(lista)})"
    con_nube = any(f.en_nube for f in lista)
    tabla = Table(title=titulo, title_justify="left")
    tabla.add_column("Ruta", overflow="fold")
    tabla.add_column("Tamaño", justify="right", no_wrap=True)
    if con_nube:
        tabla.add_column("Dónde", no_wrap=True)
    for f in lista[:top]:
        donde = ["[blue]nube[/blue]" if f.en_nube else "disco"] if con_nube else []
        tabla.add_row(escape(f.ruta), tamano_legible(f.tamano), *donde)
    if len(lista) > top:
        tabla.add_row(f"[dim]…y {len(lista) - top} más[/dim]", "", *([""] if con_nube else []))
    consola.print(tabla)


@comando
@controlar_errores
def inventario(
    carpeta: Annotated[Path, typer.Argument(metavar="CARPETA", help="Carpeta que quieres revisar (por defecto, la actual).")] = Path("."),
    guardar: Annotated[Optional[Path], typer.Option("--guardar", metavar="INFORME.md", help="Guarda el informe completo en un .md.")] = None,
    top: Annotated[int, typer.Option("--top", min=1, metavar="N", help="Filas por lista (por defecto, 15).")] = 15,
) -> None:
    """Hace inventario de una carpeta antes de organizarla. No cambia nada.

    Saca el tamaño de cada subcarpeta, los ficheros por tipo, los repos git (y si tienen remoto configurado), los instaladores, la basura (temporales, descargas a medias, Thumbs.db...), las carpetas que se pueden regenerar (node_modules, .venv...), las de programas (miniconda3, .vscode...) y los ficheros de más de 100 MB.

    Separa lo que ocupa el disco de lo que está «solo en la nube» (OneDrive): eso no gasta disco.

    Solo lee nombres y tamaños. No entra en AppData ni sigue enlaces (como «Mis documentos»), para no contar nada dos veces.
    """
    if guardar is not None:
        guardar = guardar.expanduser()
        if guardar.suffix.lower() != ".md":
            raise TareasError("El informe tiene que ser un .md (por ejemplo, --guardar ~/inventario.md).")
        if guardar.is_file() and not guardar.read_text(encoding="utf-8", errors="replace").startswith("# Inventario de"):
            raise TareasError(f"«{guardar}» ya existe y no es un inventario: no lo sobrescribo. Elige otro nombre.")

    with consola.status("Recorriendo la carpeta (en el disco entero puede tardar unos minutos)…"):
        informe = inventario_mod.revisar(carpeta)

    consola.print(f"[bold]Inventario de[/bold] {escape(str(informe.carpeta))}")
    con_nube = informe.tamano_nube > 0
    nube = f" · [blue]{tamano_legible(informe.tamano_nube)} solo en la nube[/blue]" if con_nube else ""
    consola.print(f"{informe.ficheros} ficheros en {informe.carpetas} carpetas · "
                  f"[bold]{tamano_legible(informe.tamano)} en el disco[/bold]{nube}\n")

    def columnas_tamano(tabla: Table) -> None:
        tabla.add_column("En el disco", justify="right", no_wrap=True)
        if con_nube:
            tabla.add_column("Solo en la nube", justify="right", no_wrap=True, style="blue")

    def tamanos(disco: int, en_nube: int) -> list[str]:
        return [tamano_legible(disco)] + ([tamano_legible(en_nube)] if con_nube else [])

    tabla = Table(title="Tamaño por carpeta", title_justify="left")
    tabla.add_column("Carpeta", overflow="fold")
    columnas_tamano(tabla)
    for nombre in informe.carpetas_ordenadas[:top]:
        tabla.add_row(escape(nombre), *tamanos(informe.por_carpeta[nombre], informe.por_carpeta_nube[nombre]))
    consola.print(tabla)

    tabla = Table(title="Por tipo", title_justify="left")
    tabla.add_column("Tipo")
    tabla.add_column("Ficheros", justify="right")
    columnas_tamano(tabla)
    for tipo in informe.tipos_ordenados:
        tabla.add_row(tipo, str(informe.cuantos_por_tipo[tipo]),
                      *tamanos(informe.tamano_por_tipo[tipo], informe.nube_por_tipo[tipo]))
    consola.print(tabla)

    if informe.repos:
        remoto = {True: "[green]sí[/green]", False: "[yellow]sin remoto configurado[/yellow]", None: "?"}
        tabla = Table(title=f"Repos git ({len(informe.repos)})", title_justify="left")
        tabla.add_column("Repo", overflow="fold")
        tabla.add_column("Tamaño", justify="right", no_wrap=True)
        tabla.add_column("Remoto", no_wrap=True)
        for r in informe.repos:
            tabla.add_row(escape(r.ruta), tamano_legible(r.tamano), remoto[r.con_remoto])
        consola.print(tabla)

    _pintar_ficheros("Instaladores", "magenta", informe.instaladores, top)
    _pintar_ficheros("Basura", "red", informe.basura, top)
    _pintar_ficheros("Carpetas regenerables (uv sync, npm install)", "yellow", informe.regenerables, top)
    _pintar_ficheros("Programas y configuración (no se organizan)", "dim", informe.programas, top)
    _pintar_ficheros("Ficheros de más de 100 MB", "cyan", informe.grandes, top)

    consola.print(f"\nRecuperable sin perder nada: basura {tamano_legible(inventario_mod.en_disco(informe.basura))} · "
                  f"regenerables {tamano_legible(inventario_mod.en_disco(informe.regenerables))}. "
                  f"Instaladores: {inventario_mod.resumen_tamano(informe.instaladores)}.")
    if informe.saltadas:
        consola.print(f"[dim]No recorridas (sistema o enlaces): {len(informe.saltadas)}.[/dim]")
    if informe.sin_acceso:
        consola.print(f"[yellow]⚠ Sin permiso de lectura: {len(informe.sin_acceso)} rutas (detalle en --guardar).[/yellow]")

    if guardar is not None:
        guardar.parent.mkdir(parents=True, exist_ok=True)
        guardar.write_text(inventario_mod.a_markdown(informe, top), encoding="utf-8")
        consola.print(f"[green]✔ Informe guardado en[/green] {escape(str(guardar))}")


@comando
@controlar_errores
def duplicados(
    carpeta: Annotated[Path, typer.Argument(metavar="CARPETA", help="Carpeta que quieres revisar (por defecto, la actual).")] = Path("."),
    guardar: Annotated[Optional[Path], typer.Option("--guardar", metavar="INFORME.md", help="Guarda el informe en un .md.")] = None,
    top: Annotated[int, typer.Option("--top", min=1, metavar="N", help="Grupos de ficheros que enseña (por defecto, 15).")] = 15,
) -> None:
    """Busca ficheros repetidos y carpetas que son copia de otra. No borra nada.

    Compara el contenido (no el nombre): dos ficheros son iguales si tienen la misma huella SHA-256.

    Primero enseña las carpetas en las que TODOS los ficheros tienen otra copia fuera (las primeras candidatas a borrar) y después los grupos de ficheros repetidos, de más a menos espacio. Marca las copias que están dentro de un repo git: esas se quitan con un commit.

    No lee los ficheros «solo en la nube» de OneDrive (se descargarían) y se salta lo mismo que dam inventario (AppData, enlaces, .git, .venv, node_modules...).
    """
    if guardar is not None:
        guardar = guardar.expanduser()
        if guardar.suffix.lower() != ".md":
            raise TareasError("El informe tiene que ser un .md (por ejemplo, --guardar ~/duplicados.md).")
        if guardar.is_file() and not guardar.read_text(encoding="utf-8", errors="replace").startswith("# Duplicados de"):
            raise TareasError(f"«{guardar}» ya existe y no es un informe de duplicados: no lo sobrescribo. Elige otro nombre.")

    with consola.status("Comparando ficheros (en carpetas grandes puede tardar unos minutos)…"):
        informe = duplicados_mod.revisar(carpeta)

    consola.print(f"[bold]Duplicados en[/bold] {escape(str(informe.carpeta))}")
    consola.print(f"{informe.ficheros} ficheros revisados ({tamano_legible(informe.tamano)}) · "
                  f"[bold]{len(informe.grupos)} grupos repetidos[/bold] · "
                  f"dejando una copia de cada, se liberarían [bold]{tamano_legible(informe.sobra)}[/bold]\n")
    if not informe.grupos:
        consola.print("[green]✔ No hay ficheros repetidos.[/green]")

    def marca(ruta: str) -> str:
        return escape(ruta) + (" [yellow](repo)[/yellow]" if informe.repo_de(ruta) else "")

    if informe.carpetas_copia:
        tabla = Table(title=f"[magenta]Carpetas que son copia de otra[/magenta] ({len(informe.carpetas_copia)})",
                      title_justify="left", caption_justify="left",
                      caption="Todos sus ficheros tienen otra copia fuera. Primero las de fuera de los repos; "
                              "si dos carpetas son copia una de otra, sale solo una.")
        tabla.add_column("Carpeta", overflow="fold")
        tabla.add_column("Ficheros", justify="right")
        tabla.add_column("Tamaño", justify="right", no_wrap=True)
        tabla.add_column("La otra copia está en", overflow="fold")
        for c in informe.carpetas_copia[:top]:
            original = marca(c.original) if c.original else "[dim]repartida en varios sitios[/dim]"
            tabla.add_row(marca(c.ruta), str(c.ficheros), tamano_legible(c.tamano), original)
        if len(informe.carpetas_copia) > top:
            tabla.add_row(f"[dim]…y {len(informe.carpetas_copia) - top} más (--top o --guardar para verlas)[/dim]", "", "", "")
        consola.print(tabla)

    if informe.grupos:
        tabla = Table(title=f"[cyan]Ficheros repetidos[/cyan] ({len(informe.grupos)} grupos)", title_justify="left",
                      show_lines=True)
        tabla.add_column("Copias", overflow="fold")
        tabla.add_column("Tamaño", justify="right", no_wrap=True)
        tabla.add_column("Sobra", justify="right", no_wrap=True)
        for grupo in informe.grupos[:top]:
            tabla.add_row("\n".join(marca(r) for r in grupo.rutas),
                          f"{tamano_legible(grupo.tamano)} × {len(grupo.rutas)}", tamano_legible(grupo.sobra))
        if len(informe.grupos) > top:
            tabla.add_row(f"[dim]…y {len(informe.grupos) - top} grupos más (--top o --guardar para verlos)[/dim]", "", "")
        consola.print(tabla)

    if informe.en_nube:
        consola.print(f"[dim]No leídos por estar solo en la nube (OneDrive): {informe.en_nube}.[/dim]")
    if informe.sin_acceso:
        consola.print(f"[yellow]⚠ Sin permiso de lectura: {len(informe.sin_acceso)} rutas (detalle en --guardar).[/yellow]")
    if informe.grupos:
        consola.print("\n[bold]dam duplicados no borra nada.[/bold] Antes de borrar, decide qué copia guardas; "
                      "si la que sobra está en un repo, quítala con un commit. Mejor a la Papelera que borrar del todo.")

    if guardar is not None:
        guardar.parent.mkdir(parents=True, exist_ok=True)
        guardar.write_text(duplicados_mod.a_markdown(informe, top), encoding="utf-8")
        consola.print(f"[green]✔ Informe guardado en[/green] {escape(str(guardar))}")


@comando
@controlar_errores
def readme(
    carpeta: Annotated[Path, typer.Argument(metavar="CARPETA", help="Carpeta de arriba (por defecto, la actual).")] = Path("."),
    niveles: Annotated[int, typer.Option("--niveles", min=0, metavar="N", help="Hasta qué profundidad baja (por defecto, 3).")] = 3,
    simular: Annotated[bool, typer.Option("--simular", help="Enseña qué haría sin tocar nada.")] = False,
    si: Annotated[bool, typer.Option("--si", help="No pregunta antes de escribir (solo si estás seguro).")] = False,
) -> None:
    """Pone en cada carpeta un README.md con una tabla de lo que hay dentro.

    El apartado «## Qué hay dentro» es una tabla: cada subcarpeta con su tamaño y la primera frase de su propio README, y cada archivo con su tamaño y su tipo.

    Lo que escribes tú encima de ese apartado no se toca nunca, ni un README que no tenga ese apartado (el de un repo, por ejemplo). No entra en repos git ni en proyectos de código.

    Enseña primero qué README crearía o pondría al día y pregunta s/N; --simular solo lo enseña y --si no pregunta.
    """
    with consola.status("Mirando las carpetas…"):
        cambios = readme_mod.planear(carpeta, niveles)
    raiz = carpeta.expanduser().resolve()
    cuenta = {q: sum(1 for c in cambios if c.que == q) for q in ("crear", "actualizar", "igual", "propio")}
    estilo = {"crear": "[green]crear[/green]", "actualizar": "[yellow]poner al día[/yellow]",
              "propio": "[dim]no se toca (README sin «Qué hay dentro»)[/dim]"}
    visibles = [c for c in cambios if c.que != "igual"]
    if visibles:
        titulo = "README (SIMULACIÓN: no se ha tocado nada)" if simular else "README"
        tabla = Table(title=titulo, title_justify="left")
        tabla.add_column("Carpeta", overflow="fold")
        tabla.add_column("Qué hará")
        for c in visibles:
            ruta = c.carpeta.relative_to(raiz).as_posix() if c.carpeta != raiz else f". ({raiz.name})"
            tabla.add_row(escape(ruta), estilo[c.que])
        consola.print(tabla)
    consola.print(f"{cuenta['crear']} nuevos · {cuenta['actualizar']} a poner al día · "
                  f"{cuenta['igual']} ya al día · {cuenta['propio']} que no se tocan")
    a_escribir = cuenta["crear"] + cuenta["actualizar"]
    if a_escribir == 0:
        consola.print("No hay nada que hacer.")
        return
    if simular:
        consola.print("Para hacerlo de verdad, repite la orden sin --simular.")
        return
    if not si:
        confirmar(f"¿Escribir {a_escribir} README?")
    errores = readme_mod.aplicar(cambios)
    for cambio, motivo in errores:
        consola.print(f"[red]✘ {escape(str(cambio.carpeta))}: {escape(motivo)}[/red]")
    consola.print(f"[green]✔ {a_escribir - len(errores)} README escritos.[/green]"
                  + (f" [red]{len(errores)} con error.[/red]" if errores else ""))
    if errores:
        raise typer.Exit(1)


# ---------- tu web (portfolio) ----------
@comando
@controlar_errores
def test_links(
    fuente: Annotated[str, typer.Argument(metavar="FUENTE", help="Carpeta con .html, un .html suelto o una URL (por defecto, la carpeta actual).")] = ".",
    sin_externos: Annotated[bool, typer.Option("--sin-externos", help="No comprueba enlaces a otras webs (no necesita internet).")] = False,
    timeout: Annotated[float, typer.Option("--timeout", metavar="SEGUNDOS", help="Tiempo máximo por enlace externo.")] = 8.0,
) -> None:
    """Busca enlaces rotos en tu web.

    Revisa enlaces, imágenes, hojas CSS y scripts. Los internos se comprueban en disco, con sus anclas #id y las mayúsculas (en Windows Foto.jpg y foto.jpg son lo mismo, en GitHub Pages no). Los externos se comprueban con una petición HTTP.

    Sale con 1 si hay enlaces rotos. Los avisos (webs como LinkedIn que no dejan comprobar a robots) no hacen fallar. mailto: y tel: se omiten.
    """
    informe = web.revisar_enlaces(fuente, externos=not sin_externos, timeout=timeout)
    if informe.problemas:
        tabla = Table(title="Enlaces con problemas")
        tabla.add_column("Dónde", overflow="fold", min_width=min(max(len(p.donde) for p in informe.problemas), 24))
        tabla.add_column("Línea", justify="right")
        tabla.add_column("Enlace", overflow="fold", min_width=min(max(len(p.enlace) for p in informe.problemas), 30))
        tabla.add_column("Problema", overflow="fold")
        for p in informe.problemas:
            color = "red" if p.gravedad == "roto" else "yellow"
            tabla.add_row(escape(p.donde), str(p.linea or "—"), escape(p.enlace), f"[{color}]{escape(p.motivo)}[/{color}]")
        consola.print(tabla)
    resumen = (f"{informe.paginas} página(s) · {informe.revisados} enlaces revisados · "
               f"{informe.rotos} rotos · {informe.avisos} avisos · {informe.omitidos} omitidos")
    if informe.rotos:
        consola.print(f"[red]✘ {resumen}[/red]")
        raise typer.Exit(1)
    consola.print(f"[green]✔ Sin enlaces rotos[/green] · {resumen}")


@comando
@controlar_errores
def check_headers(
    url: Annotated[str, typer.Argument(metavar="URL", help="Dirección de tu web o API (sin https:// se asume https).")],
    timeout: Annotated[float, typer.Option("--timeout", metavar="SEGUNDOS", help="Tiempo máximo de espera.")] = 10.0,
) -> None:
    """Revisa las cabeceras de seguridad de tu web o API.

    Mira Content-Security-Policy, Strict-Transport-Security, X-Frame-Options y X-Content-Type-Options (básicas: si falta alguna, sale con 1) y Referrer-Policy y Permissions-Policy (recomendadas).

    También avisa de cabeceras que revelan tecnología (Server, X-Powered-By), CORS abierto a todos y cookies sin Secure, HttpOnly o SameSite. Nunca imprime el valor de una cookie.
    """
    informe = web.revisar_cabeceras(url, timeout)
    tabla = Table(title=f"Cabeceras de {escape(informe.url)} (respuesta {informe.codigo})")
    tabla.add_column("Cabecera", overflow="fold")
    tabla.add_column("Estado")
    tabla.add_column("Valor", overflow="fold")
    tabla.add_column("Qué hacer", overflow="fold")
    estados = {"ok": "[green]✔ ok[/green]", "falta": "[red]✘ falta[/red]", "debil": "[yellow]⚠ débil[/yellow]"}
    for c in informe.comprobaciones:
        nombre = c.nombre + ("" if c.basica else " (recomendada)")
        valor = c.valor if len(c.valor) <= 40 else c.valor[:37] + "..."
        tabla.add_row(escape(nombre), estados[c.estado], escape(valor), escape(c.consejo))
    consola.print(tabla)
    for aviso in informe.avisos:
        consola.print(f"[yellow]⚠ {escape(aviso)}[/yellow]")
    consola.print(f"{informe.correctas} de {len(informe.comprobaciones)} cabeceras correctas.")
    if informe.faltan_basicas:
        consola.print(f"[red]✘ Faltan cabeceras básicas: {escape(', '.join(informe.faltan_basicas))}[/red]")
        raise typer.Exit(1)
    consola.print("[green]✔ Están las 4 cabeceras básicas.[/green]")
