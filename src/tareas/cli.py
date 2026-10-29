"""Interfaz de línea de órdenes de dam: aquí solo hay órdenes, opciones y salida por pantalla."""

import functools
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from tareas import __version__, config, sincronizar
from tareas.errores import ConfigError, TareasError
from tareas.motor import Motor


def _forzar_utf8() -> None:
    """En Windows, si la salida se redirige, Python usa cp1252 y los símbolos (✔ →) fallan."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError, OSError):
            pass


_forzar_utf8()

app = typer.Typer(
    help="dam: automatiza tareas con ficheros y mantiene tu almacén de apuntes sincronizado.",
    no_args_is_help=False,
    add_completion=False,
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


EJEMPLOS = [
    "dam listar",
    'dam listar "C:\\Users\\HP\\Desktop\\DAM\\SISTEMES"',
    "dam validar",
    "dam acciones",
    "dam ejecutar ordenar --simular",
    "dam ejecutar ordenar",
    "dam ejecutar limpiar-temporales --simular",
    "dam ejecutar convertir-webp --simular",
    "dam status",
    "dam status programacion",
    "dam sync --simular",
    'dam sync programacion "tema 3"',
    "dam sync --integrar",
]


def mostrar_ayuda() -> None:
    """Ayuda estilo terminal: uso, comandos, opciones y ejemplos."""
    consola.print(
        "[bold]dam[/bold] — automatiza tareas con ficheros y mantiene tu almacén "
        "de apuntes sincronizado.\n"
    )
    consola.print("[bold]Uso:[/bold]")
    consola.print("  dam [OPCIONES] COMANDO [ARGUMENTOS]")
    consola.print("  dam COMANDO --help\n")
    consola.print("[bold]Comandos:[/bold]")
    for cmd in app.registered_commands:
        nombre = cmd.name or (cmd.callback.__name__.replace("_", "-") if cmd.callback else "?")
        resumen = ((cmd.callback.__doc__ or "").strip().splitlines() or [""])[0]
        consola.print(f"  [cyan]{nombre:<10}[/cyan] {escape(resumen)}")
    consola.print("\n[bold]Opciones:[/bold]")
    consola.print("  [cyan]-h, --help[/cyan]      Muestra esta ayuda y sale.")
    consola.print("  [cyan]--config RUTA[/cyan]   Usa otro acciones.json (./ o ~/.config/dam/).")
    consola.print("\n[bold]Ejemplos:[/bold]")
    for ejemplo in EJEMPLOS:
        consola.print(f"  {escape(ejemplo)}")
    consola.print("\nPara más ayuda de un comando: [cyan]dam COMANDO --help[/cyan]")


@app.callback(invoke_without_command=True)
def principal(
    ctx: typer.Context,
    config_ruta: Annotated[
        Optional[Path],
        typer.Option("--config", help="Ruta de acciones.json (por defecto: ./ o ~/.config/dam/)"),
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


def comando():
    """Registra un subcomando con su propia ayuda -h/--help."""
    return app.command(context_settings={"help_option_names": ["-h", "--help"]})


@comando()
def version() -> None:
    """Muestra la versión instalada."""
    consola.print(f"dam {__version__}")


@comando()
@controlar_errores
def listar(
    carpeta: Annotated[
        Path, typer.Argument(help="Carpeta que quieres ver (por defecto, la actual).")
    ] = Path("."),
) -> None:
    """Lista los ficheros de una carpeta en una tabla."""
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


@comando()
@controlar_errores
def validar(ctx: typer.Context) -> None:
    """Valida acciones.json. Sale con 3 si no es válido."""
    ruta = config.buscar(ctx.obj)
    acciones = config.cargar(ruta)
    consola.print(f"[green]✔ {len(acciones)} acciones válidas[/green] ({escape(str(ruta))})")


@comando()
@controlar_errores
def acciones(ctx: typer.Context) -> None:
    """Lista las acciones definidas en acciones.json."""
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


@comando()
@controlar_errores
def ejecutar(
    ctx: typer.Context,
    nombre: Annotated[str, typer.Argument(help="Nombre de la acción (ver: dam acciones)")],
    carpeta: Annotated[Optional[Path], typer.Argument(help="Carpeta sobre la que actuar")] = None,
    simular: Annotated[bool, typer.Option("--simular", help="Enseña qué haría sin tocar nada")] = False,
    si: Annotated[bool, typer.Option("--si", help="No pedir confirmación")] = False,
) -> None:
    """Ejecuta una acción. Pide confirmación si borra o si la acción lo exige (salvo --si)."""
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
    typer.Option("--almacen", help="Ruta del almacén (si no, DAM_ALMACEN o «almacen» de acciones.json)"),
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


@comando()
@controlar_errores
def status(
    ctx: typer.Context,
    asignatura: Annotated[Optional[str], typer.Argument(help="Limita el análisis a esa asignatura")] = None,
    almacen: OpcionAlmacen = None,
) -> None:
    """El guardián: qué has cambiado aquí y qué hay nuevo en GitHub. No modifica nada."""
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


@comando()
@controlar_errores
def sync(
    ctx: typer.Context,
    asignatura: Annotated[Optional[str], typer.Argument(help="Solo esta asignatura (carpeta de asignaturas/)")] = None,
    mensaje: Annotated[Optional[str], typer.Argument(help="Mensaje del commit")] = None,
    integrar: Annotated[bool, typer.Option("--integrar", help="Si hay cambios en ambos lados: guarda lo tuyo y hace pull --rebase")] = False,
    simular: Annotated[bool, typer.Option("--simular", help="Enseña qué haría sin tocar nada")] = False,
    almacen: OpcionAlmacen = None,
) -> None:
    """Sincroniza el almacén con GitHub de forma segura (no pisa nada ante la duda)."""
    informe = _abrir_almacen(ctx, almacen).sincronizar(asignatura, mensaje, integrar, simular)
    for linea in informe.mensajes:
        color = "yellow" if informe.estado == "pendiente" else "green"
        consola.print(f"[{color}]{escape(linea)}[/{color}]")
    if informe.detalle:
        consola.print(f"\n{escape(informe.detalle)}")
    if informe.estado == "pendiente":
        raise typer.Exit(1)
