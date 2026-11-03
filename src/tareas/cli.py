"""Interfaz de línea de órdenes de dam: aquí solo hay órdenes, opciones y salida por pantalla."""

import functools
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Optional

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from tareas import __version__, config, escanear, hook, sincronizar, web
from tareas.errores import ConfigError, TareasError
from tareas.motor import Motor
from typer import rich_utils


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

app = typer.Typer(
    help="dam: automatiza tareas con ficheros y mantiene tu almacén de apuntes sincronizado.",
    no_args_is_help=False,
    add_completion=False,
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


def tamano_legible(n: int) -> str:
    """Convierte bytes en texto: 532 B, 1.2 KB, 3.4 MB..."""
    if n < 1024:
        return f"{n} B"
    tamano = float(n)
    unidad = "B"
    for unidad in ("KB", "MB", "GB", "TB"):
        tamano /= 1024
        if tamano < 1024:
            break
    return f"{tamano:.1f} {unidad}"


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
        ("dam help", "El manual completo (lo mismo que dam --help)"),
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
    ("Tu web (portfolio): enlaces y cabeceras", ["test-links", "check-headers"]),
    ("Otros", ["version", "help"]),
]


def _resumen(cmd: Any) -> str:
    """Primer párrafo de la ayuda de un comando, en una línea."""
    return " ".join(((cmd.help or "").strip().split("\n\n") or [""])[0].split())


def _nombre_arg(a: Any) -> str:
    """Cómo se escribe un argumento en la ayuda: su metavar si lo tiene (COMANDO), si no su nombre."""
    return a.metavar or a.name.upper()


def _pintar_comando(nombre: str, cmd: Any) -> None:
    args = [p for p in cmd.params if p.param_type_name == "argument"]
    opts = [p for p in cmd.params if p.param_type_name == "option"]
    uso = " ".join(
        [nombre]
        + [_nombre_arg(a) if a.required else f"[{_nombre_arg(a)}]" for a in args]
        + (["[OPCIONES]"] if opts else [])
    )
    consola.print(f"\n  [bold cyan]dam {escape(uso)}[/bold cyan]")
    consola.print(f"      {escape(_resumen(cmd))}")
    for a in args:
        consola.print(f"      [green]{escape(_nombre_arg(a)):<22}[/green] {escape(a.help or '')}")
    for o in opts:
        nombres = ", ".join(o.opts) + ("" if o.is_flag else f" {o.metavar or o.name.upper()}")
        consola.print(f"      [green]{escape(nombres):<22}[/green] {escape(o.help or '')}")
    for ejemplo, explicacion in EJEMPLOS.get(nombre, []):
        if 6 + len(ejemplo) + len(explicacion) + 6 <= consola.width:
            consola.print(f"      [dim]$[/dim] {escape(ejemplo)}  [dim]# {escape(explicacion)}[/dim]")
        else:
            consola.print(f"      [dim]$[/dim] {escape(ejemplo)}")
            consola.print(f"          [dim]# {escape(explicacion)}[/dim]")


def mostrar_ayuda() -> None:
    """Ayuda general: todos los comandos con sus argumentos, opciones y ejemplos."""
    grupo = typer.main.get_command(app)
    comandos = grupo.commands
    consola.print(
        "[bold]dam[/bold] — automatiza tareas con ficheros y mantiene tu almacén "
        "de apuntes sincronizado."
    )
    consola.print("\n[bold]Uso:[/bold]  dam [OPCIONES] COMANDO [ARGUMENTOS]")
    consola.print("       dam COMANDO --help     (ayuda detallada de un comando)")

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

    consola.print("\n[bold underline]Opciones globales[/bold underline] (van ANTES del comando)")
    for o in [p for p in grupo.params if p.param_type_name == "option"]:
        nombres = ", ".join(o.opts) + ("" if o.is_flag else f" {o.metavar or o.name.upper()}")
        consola.print(f"  [green]{escape(nombres):<22}[/green] {escape(o.help or '')}")

    consola.print("\n[bold underline]Dónde busca cada cosa[/bold underline]")
    consola.print("  acciones.json   --config RUTA  >  ./acciones.json  >  ~/.config/dam/acciones.json")
    consola.print("  Almacén         --almacen RUTA  >  variable DAM_ALMACEN  >  «almacen» de acciones.json")
    consola.print("                  (Windows: setx DAM_ALMACEN \"%USERPROFILE%\\DAM-almacen\")")

    consola.print("\n[bold underline]Códigos de salida[/bold underline]")
    consola.print("  0 todo bien · 1 falló al ejecutar (o sync parado: hay cambios en los dos lados)")
    consola.print("  2 uso incorrecto del comando · 3 acciones.json inválido")

    consola.print("\n[bold underline]Reglas de seguridad[/bold underline]")
    consola.print("  Prueba siempre primero con --simular. dam nunca sobrescribe (añade « (1)»), no sube")
    consola.print("  .env ni claves, ni ficheros de más de 95 MB, y ante la duda no toca nada.")


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
        typer.Argument(metavar="COMANDO", help="Comando del que quieres la ayuda (sin él, el manual completo)."),
    ] = None,
) -> None:
    """Muestra la ayuda: sin nada, el manual completo; con un COMANDO, la de ese comando."""
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
    """Valida acciones.json. Sale con 3 si no es válido.

    Comprueba el fichero entero ANTES de tocar ningún fichero tuyo: JSON bien escrito, campos obligatorios, tipos de acción, filtros, expresiones regulares y plantillas.

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
    nombre: Annotated[str, typer.Argument(metavar="NOMBRE", help="Nombre de la acción (ver: dam acciones)")],
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
    asignatura: Annotated[Optional[str], typer.Argument(metavar="ASIGNATURA", help="Solo mira esa asignatura (carpeta dentro de asignaturas/).")] = None,
    almacen: OpcionAlmacen = None,
) -> None:
    """El guardián: qué has cambiado aquí y qué hay nuevo en GitHub. No modifica nada.

    Lista los archivos modificados, nuevos y borrados en local, los commits sin subir y los archivos que hay por descargar.

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
    asignatura: Annotated[Optional[str], typer.Argument(metavar="ASIGNATURA", help="Solo esa asignatura (carpeta dentro de asignaturas/). Sin ella, todo el almacén.")] = None,
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
    tabla = Table(title=f"Posibles secretos en {alcance}")
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
    consola.print(f"[red]✘ {len(hallazgos)} hallazgo(s).[/red] Quítalos, y si ya se subieron, cámbialos en el servicio.")
    raise typer.Exit(1)


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
