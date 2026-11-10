"""Interfaz de línea de órdenes de dam: aquí solo hay órdenes, opciones y salida por pantalla."""

import functools
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Optional

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from tareas import __version__, config, escanear, hook, sincronizar, web
from tareas import doctor as doctor_mod  # «doctor», «entregar» y «pendientes» ya son nombres de comandos
from tareas import duplicados as duplicados_mod
from tareas import entregar as entregar_mod
from tareas import inventario as inventario_mod
from tareas import pendientes as pendientes_mod
from tareas import readme as readme_mod
from tareas.errores import ConfigError, TareasError
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
            raise typer.Exit(e.codigo_salida) from None

    return envoltorio


def confirmar(pregunta: str) -> None:
    """Pregunta s/n (acepta s, sí, si, y, yes). Cualquier otra cosa cancela: nunca actúa por defecto."""
    respuesta = typer.prompt(f"{pregunta} [s/N]", default="n", show_default=False)
    if respuesta.strip().lower() not in {"s", "si", "sí", "y", "yes"}:
        raise typer.Abort()


# ---------- ayuda ----------
# Ejemplos por comando: salen en `dam` (ayuda general) y al final de `dam COMANDO --help`.
# Hay un test que obliga a que cada comando nuevo tenga los suyos.
EJEMPLOS: dict[str, list[tuple[str, str]]] = {
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
    ],
    "ejecutar": [
        ("dam ejecutar ordenar --simular", "Enseña cómo ordenaría, sin tocar nada"),
        ("dam ejecutar ordenar", "Lo hace de verdad: enseña la tabla y pregunta s/N"),
        ("dam ejecutar limpiar-temporales ~/pruebas-tareas", "Usa otra carpeta en vez del origen de la acción"),
        ("dam ejecutar convertir-webp --si", "Sin preguntar (solo si estás seguro)"),
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

GRUPOS = [
    ("Ficheros: ordenar, limpiar y convertir", ["listar", "validar", "acciones", "ejecutar"]),
    ("Almacén de apuntes (git): clase, casa y USB", ["status", "sync"]),
    ("Seguridad: claves expuestas", ["scan-secrets", "instalar-hook"]),
    ("Tus proyectos: revisar y entregar", ["doctor", "pendientes", "entregar"]),
    ("Tus datos: organizar el PC", ["inventario", "duplicados", "readme"]),
    ("Tu web (portfolio): enlaces y cabeceras", ["test-links", "check-headers"]),
    ("Otros", ["version", "help"]),
]


def _resumen(cmd: Any) -> str:
    """Primer párrafo de la ayuda de un comando, en una línea."""
    return " ".join(((cmd.help or "").strip().split("\n\n") or [""])[0].split())


def _pintar_comando(nombre: str, cmd: Any) -> None:
    """Una sola línea: el comando y su descripción corta."""
    consola.print(f"  [bold cyan]{escape('dam ' + nombre):<18}[/bold cyan] {escape(_resumen(cmd))}")


def mostrar_ayuda() -> None:
    """Ayuda general corta: cada comando con una descripción de una línea."""
    comandos = typer.main.get_command(app).commands
    consola.print(
        "[bold]dam[/bold] — automatiza tareas con ficheros y mantiene tu almacén "
        "de apuntes sincronizado."
    )
    consola.print("\n[bold]Uso:[/bold]  dam COMANDO [ARGUMENTOS] [OPCIONES]")

    mostrados: set[str] = set()
    for titulo, nombres in GRUPOS:
        consola.print(f"\n[bold underline]{titulo}[/bold underline]")
        for nombre in nombres:
            if nombre in comandos:
                _pintar_comando(nombre, comandos[nombre])
                mostrados.add(nombre)
    resto = [n for n in comandos if n not in mostrados]  # comandos nuevos que falten en GRUPOS
    if resto:
        consola.print("\n[bold underline]Más comandos[/bold underline]")
        for nombre in resto:
            _pintar_comando(nombre, comandos[nombre])

    consola.print("\nUsar otro acciones.json:  [bold]dam --config RUTA COMANDO[/bold]")
    consola.print("Activa el TAB:            [bold]dam --install-completion[/bold] (mejor con instalar.sh / instalar.ps1)"
                  " · ver el script: [bold]dam --show-completion[/bold]")


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
    consola.print(f"dam {__version__}")


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

    Tipos disponibles: mover, copiar, renombrar, borrar, ordenar (por asignatura) y convertir (a WebP).
    """
    lista = config.cargar(config.buscar(ctx.obj))
    tabla = Table(title="Acciones disponibles")
    tabla.add_column("Nombre", style="bold")
    tabla.add_column("Tipo")
    tabla.add_column("Descripción")
    for a in lista:
        tabla.add_row(escape(a["nombre"]), a["tipo"], escape(a["descripcion"]))
    consola.print(tabla)


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


def pintar_tabla(nombre: str, resultados, simular: bool) -> None:
    titulo = f"{nombre} (SIMULACIÓN: no se ha tocado nada)" if simular else nombre
    tabla = Table(title=titulo)
    tabla.add_column("Fichero", overflow="fold")
    tabla.add_column("Destino", overflow="fold")
    tabla.add_column("Estado")
    for r in resultados:
        destino = escape(str(r.destino)) if r.destino else "—"
        color = COLORES.get(r.estado, "white")
        estado = r.estado + (f" ({escape(r.nota)})" if r.nota else "")
        tabla.add_row(escape(r.origen.name), destino, f"[{color}]{estado}[/{color}]")
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
    carpeta: Annotated[Optional[Path], typer.Argument(metavar="CARPETA", help="Carpeta sobre la que actuar (por defecto, el origen de la acción).")] = None,
    simular: Annotated[bool, typer.Option("--simular", help="Enseña qué haría sin tocar nada.")] = False,
    si: Annotated[bool, typer.Option("--si", help="No pregunta antes de actuar (solo si estás seguro).")] = False,
) -> None:
    """Ejecuta una acción de acciones.json sobre una carpeta.

    Sin CARPETA usa el «origen» de la acción. Empieza SIEMPRE con --simular: enseña una tabla fichero → destino sin tocar nada.

    Sin --simular, las acciones que borran (o que tienen «confirmar») enseñan primero la tabla y preguntan s/N; --si se salta la pregunta.

    Nunca sobrescribe: si el destino ya existe, añade « (1)». Sale con 1 si algún fichero falla.
    """
    motor = Motor(config.cargar(config.buscar(ctx.obj)))
    accion, ficheros = motor.preparar(nombre, carpeta)
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
    if any(r.estado == "error" for r in resultados):
        raise typer.Exit(1)


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
    """Sincroniza el almacén con GitHub de forma segura (no pisa nada ante la duda).

    Hace primero un fetch y decide según lo que encuentre:

    • Nada nuevo en ningún lado: «Todo está actualizado».

    • Solo cambios en GitHub: los descarga (pull).

    • Solo cambios tuyos: add, commit con el mensaje «\\[asignatura]: texto» y push.

    • Cambios en los DOS lados: se para, enseña el diff y sale con 1. Con --integrar guarda lo tuyo y hace pull --rebase; si hay conflicto real lo deshace sin perder nada.

    Con ASIGNATURA solo se suben los cambios de asignaturas/ASIGNATURA. Para todo el almacén con tu mensaje usa -m (en PowerShell el texto vacío "" desaparece, no lo uses).

    Se niega a subir .env, claves (.pem, .key...) y ficheros de más de 95 MB.
    """
    informe = _abrir_almacen(ctx, almacen).sincronizar(asignatura, mensaje_opcion or mensaje, integrar, simular)
    for linea in informe.mensajes:
        color = "yellow" if informe.estado == "pendiente" else "green"
        consola.print(f"[{color}]{escape(linea)}[/{color}]")
    if informe.detalle:
        consola.print(f"\n{escape(informe.detalle)}")
    if informe.estado == "pendiente":
        raise typer.Exit(1)


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
