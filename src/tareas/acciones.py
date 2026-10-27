"""Lógica real de las acciones: ordenar por asignaturas, limpiar y convertir.

Todas las funciones solo trabajan dentro de la carpeta de origen que indique
la configuración, y las de conversión/eliminación devuelven un plan para que
la CLI pregunte antes de tocar nada.
"""

import re
import unicodedata
from datetime import datetime
from pathlib import Path

EXTENSION_TEMPORALES = {
    ".tmp",
    ".temp",
    ".bak",
    ".cache",
    ".part",
    ".swp",
    ".download",
    ".crdownload",
}
EXTENSION_IMAGENES = {".jpg", ".jpeg", ".png"}

EXTENSIONES_ASIGNATURA = {
    ".py": "programacion",
    ".sql": "bases-datos",
    ".db": "bases-datos",
    ".xml": "lenguaje-marcas",
    ".html": "lenguaje-marcas",
    ".htm": "lenguaje-marcas",
    ".sh": "sistemas",
}


def normalizar(texto: str) -> str:
    """Pasa el texto a minúsculas y sin acentos para poder comparar."""
    desacentuado = unicodedata.normalize("NFKD", texto)
    plano = desacentuado.encode("ascii", "ignore").decode("ascii").lower()
    return plano.replace("_", " ").replace("-", " ")


def _contiene(texto: str, palabras: list[str]) -> bool:
    """Busca las palabras como palabras completas en el texto normalizado."""
    texto_normalizado = normalizar(texto)
    for palabra in palabras:
        patron = rf"\b{re.escape(normalizar(palabra))}\b"
        if re.search(patron, texto_normalizado):
            return True
    return False


def texto_pdf(ruta: Path, paginas: int = 3) -> str:
    """Devuelve el texto de las N primeras y N últimas páginas de un PDF."""
    try:
        from pypdf import PdfReader

        lector = PdfReader(str(ruta))
        total = len(lector.pages)
        indices = list(range(min(paginas, total)))
        indices += list(range(max(paginas, total - paginas), total))
        trozos = []
        for indice in dict.fromkeys(indices):
            trozos.append(lector.pages[indice].extract_text() or "")
        return " ".join(trozos)
    except Exception:
        return ""


def clasificar(ruta: Path, carpetas: dict[str, list[str]]) -> str | None:
    """Devuelve el nombre de la carpeta de asignatura o None si no se reconoce.

    Orden: palabras clave en el nombre, extensión conocida, contenido del PDF.
    """
    for carpeta, palabras in carpetas.items():
        todas = palabras + [carpeta.replace("-", " ")]
        if _contiene(ruta.name, todas):
            return carpeta

    destino = EXTENSIONES_ASIGNATURA.get(ruta.suffix.lower())
    if destino in carpetas:
        return destino

    if ruta.suffix.lower() == ".pdf":
        contenido = texto_pdf(ruta)
        if contenido:
            for carpeta, palabras in carpetas.items():
                todas = palabras + [carpeta.replace("-", " ")]
                if _contiene(contenido, todas):
                    return carpeta
    return None


def planificar_ordenar(
    origen: Path, carpetas: dict[str, list[str]]
) -> tuple[dict[str, list[Path]], list[Path]]:
    """Reparte los ficheros de la carpeta entre carpetas de asignatura."""
    mover: dict[str, list[Path]] = {}
    sin_destino: list[Path] = []
    for entrada in sorted(origen.iterdir()):
        if entrada.is_dir():
            continue
        destino = clasificar(entrada, carpetas)
        if destino is None:
            sin_destino.append(entrada)
        else:
            mover.setdefault(destino, []).append(entrada)
    return mover, sin_destino


def mover_ficheros(destino: Path, ficheros: list[Path]) -> int:
    """Mueve ficheros a la carpeta de destino, creándola si no existe.

    Si ya hay un fichero con el mismo nombre, le pone un número al final
    para no sobrescribir nada. Devuelve el número de ficheros movidos.
    """
    destino.mkdir(parents=True, exist_ok=True)
    movidos = 0
    for fichero in ficheros:
        objetivo = destino / fichero.name
        contador = 1
        while objetivo.exists():
            objetivo = destino / f"{fichero.stem} ({contador}){fichero.suffix}"
            contador += 1
        fichero.rename(objetivo)
        movidos += 1
    return movidos


def planificar_limpiar(origen: Path, dias: int) -> list[Path]:
    """Devuelve los ficheros temporales de la carpeta con más de N días."""
    limite = datetime.now().timestamp() - dias * 86400
    viejos = []
    for entrada in sorted(origen.iterdir()):
        if not entrada.is_file():
            continue
        if entrada.suffix.lower() not in EXTENSION_TEMPORALES:
            continue
        if entrada.stat().st_mtime <= limite:
            viejos.append(entrada)
    return viejos


def borrar_ficheros(ficheros: list[Path]) -> int:
    """Borra los ficheros indicados. Devuelve el número de borrados."""
    borrados = 0
    for fichero in ficheros:
        fichero.unlink()
        borrados += 1
    return borrados


def planificar_convertir(origen: Path) -> tuple[list[Path], list[Path], str | None]:
    """Busca imágenes JPEG/PNG a convertir. Devuelve (a_convertir, no_convertir, error)."""
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        return [], [], "falta la librería Pillow: ejecuta 'uv add pillow'"

    a_convertir: list[Path] = []
    no_convertir: list[Path] = []
    for entrada in sorted(origen.iterdir()):
        if not entrada.is_file():
            continue
        if entrada.suffix.lower() not in EXTENSION_IMAGENES:
            continue
        if entrada.with_suffix(".webp").exists():
            no_convertir.append(entrada)
            continue
        a_convertir.append(entrada)
    return a_convertir, no_convertir, None


def convertir_imagenes(ficheros: list[Path]) -> tuple[list[Path], list[Path]]:
    """Convierte las imágenes a WebP. Devuelve (convertidas, fallidas)."""
    from PIL import Image

    convertidas: list[Path] = []
    fallidas: list[Path] = []
    for fichero in ficheros:
        salida = fichero.with_suffix(".webp")
        contador = 1
        while salida.exists():
            salida = fichero.with_name(f"{fichero.stem} ({contador}).webp")
            contador += 1
        try:
            with Image.open(fichero) as imagen:
                imagen.save(salida, "WEBP")
            convertidas.append(fichero)
        except OSError:
            fallidas.append(fichero)
    return convertidas, fallidas
