"""CLI de tareas: version, listar y comandos de configuración."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from tareas import __version__
from tareas.config import ErrorConfig, leer_configuracion, ruta_de_configuracion

app = typer.Typer(
    name="gabriel",
    help="CLI de Gabriel: automatiza tareas repetitivas con ficheros desde la terminal.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Muestra la versión de la herramienta."""
    console.print(f"gabriel [bold]{__version__}[/bold]")


@app.command()
def listar(
    carpeta: Optional[str] = typer.Argument(
        None, help="Carpeta a listar (por defecto, la actual)."
    ),
) -> None:
    """Lista los ficheros de una carpeta con tamaño y fecha de modificación."""
    ruta = Path(carpeta) if carpeta else Path.cwd()

    if not ruta.exists():
        console.print(f"[red]Error:[/red] la ruta no existe: {ruta}")
        raise typer.Exit(code=2)
    if not ruta.is_dir():
        console.print(f"[red]Error:[/red] no es una carpeta: {ruta}")
        raise typer.Exit(code=2)

    tabla = Table(title=f"Contenido de {ruta}")
    tabla.add_column("Nombre", style="cyan")
    tabla.add_column("Tipo")
    tabla.add_column("Tamaño", justify="right")
    tabla.add_column("Modificado")

    try:
        entradas = sorted(ruta.iterdir(), key=lambda p: (p.is_dir(), p.name.lower()))
        for entrada in entradas:
            if entrada.is_dir():
                tipo, tamano = "carpeta", "-"
            else:
                tipo, tamano = "fichero", _tamaño_legible(entrada.stat().st_size)
            modificado = _fecha_modificacion(entrada)
            tabla.add_row(entrada.name, tipo, tamano, modificado)
    except PermissionError:
        console.print(f"[red]Error:[/red] sin permisos para leer: {ruta}")
        raise typer.Exit(code=1)
    except OSError as error:
        console.print(f"[red]Error:[/red] no se pudo leer {ruta}: {error}")
        raise typer.Exit(code=1)

    if tabla.row_count == 0:
        console.print(f"La carpeta está vacía: {ruta}")
        return
    console.print(tabla)


@app.command()
def validar(
    config: Optional[str] = typer.Option(
        None, "--config", help="Ruta del tareas.toml (por defecto, se busca automáticamente)."
    ),
) -> None:
    """Valida el fichero de configuración. Salida 3 si no es válida."""
    ruta = ruta_de_configuracion(config)
    try:
        datos = leer_configuracion(ruta)
    except ErrorConfig as error:
        console.print(f"[red]Configuración inválida:[/red] {error}")
        raise typer.Exit(code=3)
    acciones = ", ".join(datos["acciones"])
    console.print(f"[green]Configuración válida:[/green] {ruta}")
    console.print(f"Acciones encontradas: {acciones}")


@app.command()
def acciones(
    config: Optional[str] = typer.Option(
        None, "--config", help="Ruta del tareas.toml (por defecto, se busca automáticamente)."
    ),
) -> None:
    """Lista las acciones definidas en la configuración."""
    ruta = ruta_de_configuracion(config)
    try:
        datos = leer_configuracion(ruta)
    except ErrorConfig as error:
        console.print(f"[red]Configuración inválida:[/red] {error}")
        raise typer.Exit(code=3)

    tabla = Table(title=f"Acciones de {ruta}")
    tabla.add_column("Nombre", style="cyan")
    tabla.add_column("Descripción")
    tabla.add_column("Tipo")
    tabla.add_column("Origen")
    for nombre, accion in datos["acciones"].items():
        tabla.add_row(
            nombre,
            str(accion["descripcion"]),
            str(accion["tipo"]),
            str(accion["origen"]),
        )
    console.print(tabla)


@app.command()
def ejecutar(
    nombre: str = typer.Argument(..., help="Nombre de la acción a ejecutar."),
    simular: bool = typer.Option(
        False, "--simular", help="Muestra lo que haría sin tocar ningún fichero."
    ),
    config: Optional[str] = typer.Option(
        None, "--config", help="Ruta del tareas.toml (por defecto, se busca automáticamente)."
    ),
) -> None:
    """Ejecuta una acción de la configuración. Sin --simular pide confirmación."""
    ruta = ruta_de_configuracion(config)
    try:
        datos = leer_configuracion(ruta)
    except ErrorConfig as error:
        console.print(f"[red]Configuración inválida:[/red] {error}")
        raise typer.Exit(code=3)

    if nombre not in datos["acciones"]:
        console.print(
            f"[red]Error:[/red] no existe la acción '{nombre}'. "
            f"Disponible: {', '.join(datos['acciones'])}"
        )
        raise typer.Exit(code=2)

    accion = datos["acciones"][nombre]
    origen = Path(str(accion["origen"])).expanduser()
    if not origen.exists():
        console.print(f"[red]Error:[/red] la carpeta de origen no existe: {origen}")
        raise typer.Exit(code=2)
    if not origen.is_dir():
        console.print(f"[red]Error:[/red] el origen no es una carpeta: {origen}")
        raise typer.Exit(code=2)

    console.print(f"[bold]{accion['descripcion']}[/bold]  (origen: {origen})")
    if accion["tipo"] == "asignaturas":
        _ejecutar_asignaturas(origen, accion, simular)
    elif accion["tipo"] == "limpiar":
        _ejecutar_limpiar(origen, accion, simular)
    else:
        _ejecutar_convertir(origen, simular)


def _confirmar(mensaje: str) -> bool:
    """Pregunta al usuario y devuelve si quiere continuar."""
    try:
        return typer.confirm(mensaje)
    except typer.Abort:
        console.print("Cancelado por el usuario.")
        return False


def _hay_pdfs(origen: Path) -> bool:
    """Comprueba si hay algún PDF en la carpeta de origen."""
    return any(
        entrada.is_file() and entrada.suffix.lower() == ".pdf"
        for entrada in origen.iterdir()
    )


def _tiene_pypdf() -> bool:
    """Comprueba si la librería pypdf está instalada."""
    import importlib.util

    return importlib.util.find_spec("pypdf") is not None


def _ejecutar_asignaturas(origen: Path, accion: dict, simular: bool) -> None:
    """Ordena los ficheros de la carpeta por carpetas de asignatura."""
    from tareas.acciones import mover_ficheros, planificar_ordenar

    if _hay_pdfs(origen) and not _tiene_pypdf():
        console.print(
            "[yellow]Aviso:[/yellow] falta pypdf, los PDF se clasificarán "
            "solo por su nombre (uv add pypdf)."
        )

    mover, sin_destino = planificar_ordenar(origen, accion["carpetas"])
    if not mover:
        console.print("No hay ningún fichero que reconocer. Nada que hacer.")
        return

    total = sum(len(ficheros) for ficheros in mover.values())
    tabla = Table(title="Ficheros que se moverían" if simular else "Ficheros a mover")
    tabla.add_column("Destino", style="cyan")
    tabla.add_column("Ficheros")
    for carpeta, ficheros in mover.items():
        for fichero in ficheros:
            tabla.add_row(carpeta, fichero.name)
    console.print(tabla)
    if sin_destino:
        console.print(
            f"[yellow]{len(sin_destino)} sin asignatura[/yellow] "
            f"(se quedan donde están): {', '.join(f.name for f in sin_destino)}"
        )
    if simular:
        console.print(f"[dim]SIMULACIÓN: se moverían {total} ficheros. "
                      "Ningún fichero ha sido tocado.[/dim]")
        return
    if not _confirmar(f"¿Mover {total} ficheros a sus carpetas?"):
        return

    movidos = 0
    for carpeta, ficheros in mover.items():
        movidos += mover_ficheros(origen / carpeta, ficheros)
    console.print(f"[green]Hecho:[/green] movidos {movidos} ficheros a {len(mover)} carpetas.")


def _ejecutar_limpiar(origen: Path, accion: dict, simular: bool) -> None:
    """Borra ficheros temporales antiguos tras preguntar."""
    from tareas.acciones import borrar_ficheros, planificar_limpiar

    viejos = planificar_limpiar(origen, int(accion["dias"]))
    if not viejos:
        console.print(f"No hay ficheros temporales con más de {accion['dias']} días.")
        return

    for fichero in viejos:
        console.print(f"  [red]borraría[/red] {fichero.name}")
    if simular:
        console.print(
            f"[dim]SIMULACIÓN: se borrarían {len(viejos)} ficheros. "
            "Ningún fichero ha sido tocado.[/dim]"
        )
        return
    if not _confirmar(f"¿Borrar {len(viejos)} ficheros? (no se pueden recuperar)"):
        return
    borrados = borrar_ficheros(viejos)
    console.print(f"[green]Hecho:[/green] borrados {borrados} ficheros temporales.")


def _ejecutar_convertir(origen: Path, simular: bool) -> None:
    """Convierte imágenes a WebP tras preguntar."""
    from tareas.acciones import convertir_imagenes, planificar_convertir

    a_convertir, sin_convertir, error = planificar_convertir(origen)
    if error:
        console.print(f"[red]Error:[/red] {error}")
        raise typer.Exit(code=1)
    if not a_convertir:
        console.print("No hay imágenes JPEG/PNG nuevas por convertir.")
        return

    for fichero in a_convertir:
        console.print(f"  convertiría {fichero.name} → {fichero.with_suffix('.webp').name}")
    if sin_convertir:
        console.print(
            f"[yellow]{len(sin_convertir)} con .webp ya existente[/yellow] "
            f"(se ignoran): {', '.join(f.name for f in sin_convertir)}"
        )
    if simular:
        console.print(
            f"[dim]SIMULACIÓN: se convertirían {len(a_convertir)} imágenes. "
            "Ningún fichero ha sido tocado.[/dim]"
        )
        return
    if not _confirmar(f"¿Convertir {len(a_convertir)} imágenes a WebP?"):
        return
    convertidas, fallidas = convertir_imagenes(a_convertir)
    console.print(f"[green]Hecho:[/green] convertidas {len(convertidas)} imágenes.")
    if fallidas:
        console.print(
            f"[yellow]No se pudieron convertir:[/yellow] "
            f"{', '.join(f.name for f in fallidas)}"
        )


def _tamaño_legible(bytes_: int) -> str:
    """Convierte un tamaño en bytes a una cadena legible (ej. 1,5 MB)."""
    unidades = ["B", "KB", "MB", "GB", "TB"]
    tamaño = float(bytes_)
    for unidad in unidades:
        if tamaño < 1024 or unidad == unidades[-1]:
            if unidad == "B":
                return f"{int(tamaño)} {unidad}"
            return f"{tamaño:.1f} {unidad}"
        tamaño /= 1024
    return f"{bytes_} B"


def _fecha_modificacion(ruta: Path) -> str:
    """Devuelve la fecha de modificación como 'AAAA-MM-DD HH:MM'."""
    try:
        return datetime.fromtimestamp(ruta.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    except OSError:
        return "-"
