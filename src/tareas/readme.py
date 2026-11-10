"""dam readme: el README.md de cada carpeta, con una tabla de lo que hay dentro.

Cada README tiene dos partes:
- Arriba, lo que escribes tú (qué guarda la carpeta). dam no lo toca nunca.
- El apartado «## Qué hay dentro»: una tabla con cada subcarpeta (tamaño y la primera frase de
  su propio README) y cada archivo (tamaño y tipo). Ese apartado lo rellena dam.

Un README que no tiene ese apartado (el de un repo, uno escrito a mano...) no se toca. No entra en
repos git ni en proyectos de código: sus README son del proyecto. Solo lee nombres y tamaños,
y los README.md de las subcarpetas.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .errores import TareasError
from .inventario import (PROGRAMAS, REGENERABLES, SISTEMA, _es_enlace, tamano_carpeta,
                         tamano_legible, tipo_de)

SECCION = "## Qué hay dentro"
PIE = "_Esta tabla la rellena `dam readme`"  # así empieza la última línea del apartado
PENDIENTE = "_Escribe aquí qué guarda esta carpeta. `dam readme` no toca este texto._"
MAX_ARCHIVOS = 15
MAX_DESCRIPCION = 110
# Un proyecto de código: su README es del proyecto y sus carpetas no se recorren
MARCAS_PROYECTO = {"pyproject.toml", "package.json", "requirements.txt", "setup.py", "pom.xml",
                   "build.gradle", "cargo.toml", "go.mod", "composer.json", "__init__.py",
                   ".venv", "venv", "node_modules"}
NO_SE_LISTAN = {"readme.md", "desktop.ini", "thumbs.db", ".ds_store"}
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
TIPOS = {"documentos": "documento", "imagenes": "imagen", "video": "vídeo", "audio": "audio",
         "comprimidos": "comprimido", "instaladores": "instalador", "codigo": "código",
         "maquinas-virtuales": "máquina virtual", "redes": "Packet Tracer", "programas": "programa"}


@dataclass
class Cambio:
    carpeta: Path
    que: str  # «crear», «actualizar», «igual» o «propio» (tiene README sin el apartado: no se toca)
    texto: str | None = None  # el README nuevo (None si no hay que escribir nada)


def fecha_corta(dia: date) -> str:
    return f"{dia.day}-{MESES[dia.month - 1]}-{dia.year}"


def _buscar_readme(carpeta: Path) -> Path | None:
    try:
        return next((h for h in carpeta.iterdir() if h.name.lower() == "readme.md" and h.is_file()), None)
    except OSError:
        return None


def _leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8", errors="replace")


def es_repo(carpeta: Path) -> bool:
    return (carpeta / ".git").exists()


def es_proyecto(carpeta: Path) -> bool:
    try:
        return any(h.name.lower() in MARCAS_PROYECTO for h in carpeta.iterdir())
    except OSError:
        return False


def _se_recorre(carpeta: Path) -> bool:
    nombre = carpeta.name
    return not (nombre.startswith(".") or nombre in SISTEMA or nombre in REGENERABLES
                or nombre in PROGRAMAS or _es_enlace(carpeta))


def descripcion(texto: str) -> str:
    """La primera frase (párrafo) que hay debajo del título, en una línea y sin pasarse de largo."""
    parrafo: list[str] = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not parrafo and (not linea or linea.startswith(("#", "![", "[![", "<", "---", "|")) or linea == PENDIENTE):
            if linea.startswith("## "):
                break  # sin descripción: el primer apartado ya empieza
            continue
        if not linea or linea.startswith(("#", "|", "- ", "* ")):
            break
        parrafo.append(linea)
    frase = " ".join(parrafo).replace("**", "")
    if len(frase) > MAX_DESCRIPCION:
        frase = frase[:MAX_DESCRIPCION].rsplit(" ", 1)[0].rstrip(",.;:(") + "…"
    return frase


def _celda(texto: str) -> str:
    return texto.replace("|", "\\|")


def _bytes(archivo: Path) -> int:
    try:
        return archivo.stat().st_size
    except OSError:
        return 0


def _tamano(disco: int, nube: int) -> str:
    return tamano_legible(disco) + (f" (+{tamano_legible(nube)} en la nube)" if nube else "")


def tabla(carpeta: Path) -> list[str]:
    """Las filas del apartado «Qué hay dentro»: primero las subcarpetas y luego los archivos."""
    carpetas, archivos = [], []
    for hijo in sorted(carpeta.iterdir(), key=lambda h: h.name.casefold()):
        if hijo.name.lower() in NO_SE_LISTAN or hijo.name.startswith((".", "~$")) or _es_enlace(hijo):
            continue
        (carpetas if hijo.is_dir() else archivos).append(hijo)
    if not carpetas and not archivos:
        return ["_Vacía de momento._"]

    filas = ["| Nombre | Tamaño | Qué es |", "|---|---:|---|"]
    for c in carpetas:
        medida = tamano_carpeta(c, ignorar=frozenset({"readme.md"}))  # escribir README no cambia la tabla del padre
        readme = _buscar_readme(c)
        que = descripcion(_leer(readme)) if readme else ""
        if es_repo(c):
            que = f"**Repo git.** {que}".strip()
        que = que or f"{medida.ficheros} archivo{'s' * (medida.ficheros != 1)}"
        filas.append(f"| 📁 **{_celda(c.name)}** | {_tamano(medida.disco, medida.nube)} | {_celda(que)} |")
    for a in archivos[:MAX_ARCHIVOS]:
        extension = a.suffix.lower()
        tipo = TIPOS.get(tipo_de(a.name), "otro")
        filas.append(f"| 📄 {_celda(a.name)} | {tamano_legible(_bytes(a))} | "
                     f"{tipo}{f' ({extension})' if extension else ''} |")
    if len(archivos) > MAX_ARCHIVOS:
        resto = archivos[MAX_ARCHIVOS:]
        filas.append(f"| … | {tamano_legible(sum(map(_bytes, resto)))} | y {len(resto)} archivos más |")
    return filas


def apartado(carpeta: Path, hoy: date) -> list[str]:
    return [SECCION, "", *tabla(carpeta), "",
            f"{PIE} ({fecha_corta(hoy)}): no escribas dentro de este apartado, se rehace cada vez._"]


def _sin_pie(texto: str) -> str:
    return "\n".join(l for l in texto.splitlines() if not l.startswith(PIE)).strip()


def nuevo_texto(carpeta: Path, actual: str | None, hoy: date) -> str | None:
    """El README con el apartado al día. None si tiene README pero sin el apartado (no es nuestro)."""
    if actual is None:
        lineas = [f"# {carpeta.name}", "", PENDIENTE, "", *apartado(carpeta, hoy)]
        return "\n".join(lineas) + "\n"
    lineas = actual.splitlines()
    inicio = next((i for i, l in enumerate(lineas) if l.strip() == SECCION), None)
    if inicio is None:
        return None
    # el apartado acaba en el siguiente título (## o #): lo que haya debajo también es tuyo
    fin = next((i for i in range(inicio + 1, len(lineas)) if re.match(r"#{1,2} ", lineas[i])), len(lineas))
    despues = ["", *lineas[fin:]] if fin < len(lineas) else []
    return "\n".join([*lineas[:inicio], *apartado(carpeta, hoy), *despues]) + "\n"


def planear(carpeta: Path, niveles: int = 3, hoy: date | None = None) -> list[Cambio]:
    """Qué README crearía o pondría al día, de la carpeta y de sus subcarpetas hasta «niveles»."""
    raiz = carpeta.expanduser().resolve()
    if not raiz.is_dir():
        raise TareasError(f"«{raiz}» no existe o no es una carpeta.")
    if es_repo(raiz):
        raise TareasError(f"«{raiz}» es un repo git: su README es del repo y dam readme no lo toca.")
    hoy = hoy or date.today()
    cambios: list[Cambio] = []

    def visitar(c: Path, nivel: int) -> None:
        proyecto = es_proyecto(c)
        readme = _buscar_readme(c)
        actual = _leer(readme) if readme else None
        if actual is not None or not proyecto:  # en un proyecto sin README no se crea uno
            texto = nuevo_texto(c, actual, hoy)
            if texto is None:
                cambios.append(Cambio(c, "propio"))
            elif actual is None:
                cambios.append(Cambio(c, "crear", texto))
            elif _sin_pie(texto) == _sin_pie(actual):
                cambios.append(Cambio(c, "igual"))
            else:
                cambios.append(Cambio(c, "actualizar", texto))
        if proyecto or nivel >= niveles:
            return
        try:
            hijos = sorted((h for h in c.iterdir() if h.is_dir()), key=lambda h: h.name.casefold())
        except OSError:
            return
        for hijo in hijos:
            if _se_recorre(hijo) and not es_repo(hijo):
                visitar(hijo, nivel + 1)

    visitar(raiz, 0)
    return cambios


def aplicar(cambios: list[Cambio]) -> list[tuple[Cambio, str]]:
    """Escribe los README. Devuelve los que fallaron, con el motivo."""
    errores = []
    for cambio in cambios:
        if cambio.texto is None:
            continue
        destino = _buscar_readme(cambio.carpeta) or cambio.carpeta / "README.md"
        try:
            destino.write_text(cambio.texto, encoding="utf-8", newline="\n")
        except OSError as e:
            errores.append((cambio, e.strerror or str(e)))
    return errores
