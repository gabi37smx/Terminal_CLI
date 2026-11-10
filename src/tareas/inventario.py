"""dam inventario: qué hay en una carpeta antes de organizarla.

Solo LEE nombres, tamaños, fechas y atributos: no abre el contenido de ningún fichero (salvo
.git/config para saber si un repo tiene remoto) y no mueve ni borra nada.

Saca: tamaño por subcarpeta (en el disco y solo en la nube), repos git, ficheros por tipo,
instaladores, basura, carpetas que se pueden regenerar (node_modules, .venv...), programas y
ficheros grandes.
"""

from __future__ import annotations

import os
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .errores import TareasError

LIMITE_GRANDE = 100 * 1024 * 1024  # 100 MB
SUELTOS = "(ficheros sueltos)"  # los que están directamente en la carpeta revisada

# Los mismos nombres que tendrán las carpetas de ~/Datos/por-tipo
TIPOS: dict[str, set[str]] = {
    "documentos": {".pdf", ".doc", ".docx", ".odt", ".txt", ".md", ".rtf", ".xls", ".xlsx", ".ods",
                   ".csv", ".ppt", ".pptx", ".odp", ".epub"},
    "imagenes": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".heic", ".ico", ".tif", ".tiff"},
    "video": {".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv"},
    "audio": {".mp3", ".wav", ".ogg", ".flac", ".m4a"},
    "comprimidos": {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz"},
    "instaladores": {".exe", ".msi", ".msix", ".iso", ".dmg", ".pkg", ".deb", ".rpm", ".appimage"},
    "codigo": {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h", ".cs", ".html", ".htm",
               ".css", ".sql", ".json", ".xml", ".sh", ".ps1", ".php", ".kt", ".ipynb", ".yml", ".yaml"},
    "maquinas-virtuales": {".vdi", ".vmdk", ".vhd", ".vhdx", ".ova", ".ovf", ".qcow2"},
    "redes": {".pkt", ".pka"},  # prácticas de Packet Tracer
}

# Carpetas que se pueden volver a crear (uv sync, npm install...): ocupan, pero no hay que guardarlas
REGENERABLES = {"node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
# Carpetas de programas: se miden enteras, pero no se recorren (sus .exe y sus repos no son tuyos).
# Además, toda carpeta que empieza por «.» y no está dentro de un repo (.vscode, .local, .cursor...).
PROGRAMAS = {"miniconda3", "anaconda3", "Anaconda3", "Miniconda3"}
# Carpetas del sistema: ni se recorren ni se miden
SISTEMA = {"AppData", "$RECYCLE.BIN", "System Volume Information"}
# Basura: temporales (los mismos que limpiar-temporales), miniaturas y bloqueos de Office
TEMPORALES = {".tmp", ".temp", ".bak", ".cache", ".part", ".swp", ".download", ".crdownload"}
NOMBRES_BASURA = {"thumbs.db", ".ds_store"}

# Atributos de Windows de un fichero cuyos datos no están en el disco (OneDrive «solo en la nube»):
# OFFLINE (0x1000), RECALL_ON_OPEN (0x40000) y RECALL_ON_DATA_ACCESS (0x400000)
ATRIBUTOS_NUBE = 0x1000 | 0x40000 | 0x400000


@dataclass
class Fichero:
    ruta: str  # relativa a la carpeta revisada, con /
    tamano: int
    en_nube: bool = False


@dataclass
class Repo:
    ruta: str  # relativa; "." si la carpeta revisada ya es un repo
    tamano: int = 0
    con_remoto: bool | None = None  # None: no se sabe (.git es un fichero)


@dataclass
class Medida:
    disco: int = 0
    nube: int = 0
    ficheros: int = 0


@dataclass
class Informe:
    carpeta: Path
    ficheros: int = 0
    carpetas: int = 0
    tamano: int = 0  # en el disco
    tamano_nube: int = 0  # solo en la nube: no ocupa disco
    por_carpeta: Counter = field(default_factory=Counter)  # primer nivel -> bytes en el disco
    por_carpeta_nube: Counter = field(default_factory=Counter)
    cuantos_por_tipo: Counter = field(default_factory=Counter)
    tamano_por_tipo: Counter = field(default_factory=Counter)
    nube_por_tipo: Counter = field(default_factory=Counter)
    repos: list[Repo] = field(default_factory=list)
    instaladores: list[Fichero] = field(default_factory=list)
    basura: list[Fichero] = field(default_factory=list)
    regenerables: list[Fichero] = field(default_factory=list)  # carpetas enteras
    programas: list[Fichero] = field(default_factory=list)  # carpetas enteras
    grandes: list[Fichero] = field(default_factory=list)
    saltadas: list[str] = field(default_factory=list)  # sistema y enlaces: no se recorren
    sin_acceso: list[str] = field(default_factory=list)

    @property
    def carpetas_ordenadas(self) -> list[str]:
        """Primero lo que más disco ocupa; a igualdad, lo que más hay en la nube."""
        nombres = set(self.por_carpeta) | set(self.por_carpeta_nube)
        return sorted(nombres, key=lambda c: (self.por_carpeta[c], self.por_carpeta_nube[c]), reverse=True)

    @property
    def tipos_ordenados(self) -> list[str]:
        return sorted(self.cuantos_por_tipo,
                      key=lambda t: (self.tamano_por_tipo[t], self.nube_por_tipo[t]), reverse=True)


def en_disco(lista: list[Fichero]) -> int:
    return sum(f.tamano for f in lista if not f.en_nube)


def en_nube(lista: list[Fichero]) -> int:
    return sum(f.tamano for f in lista if f.en_nube)


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


def tipo_de(nombre: str, hay_dll_al_lado: bool = False) -> str:
    """El tipo de un fichero por su extensión. Un .exe al lado de .dll es un programa, no un instalador."""
    extension = Path(nombre).suffix.lower()
    if extension == ".exe" and hay_dll_al_lado:
        return "programas"
    for tipo, extensiones in TIPOS.items():
        if extension in extensiones:
            return tipo
    return "otros"


def es_basura(nombre: str) -> bool:
    return (nombre.lower() in NOMBRES_BASURA or nombre.startswith("~$")
            or Path(nombre).suffix.lower() in TEMPORALES)


def es_programa(nombre: str, dentro_de_repo: bool) -> bool:
    """miniconda3 y las carpetas ocultas (.vscode, .local...). Dentro de un repo, .github o .opencode son tuyas."""
    return nombre in PROGRAMAS or (nombre.startswith(".") and not dentro_de_repo)


def esta_en_la_nube(datos: os.stat_result) -> bool:
    """True si el fichero es un marcador de OneDrive: existe, pero sus datos siguen en la nube.

    Solo Windows tiene st_file_attributes; en Linux y macOS siempre es False.
    """
    return bool(getattr(datos, "st_file_attributes", 0) & ATRIBUTOS_NUBE)


def _es_enlace(ruta: Path) -> bool:
    """Enlaces y «junctions» de Windows (como «Mis documentos»): seguirlos contaría cosas dos veces."""
    try:
        return ruta.is_symlink() or ruta.is_junction()
    except OSError:
        return True


def tamano_carpeta(carpeta: Path, ignorar: frozenset[str] = frozenset()) -> Medida:
    """Lo que ocupa una carpeta entera (en el disco y en la nube), sin seguir enlaces.

    «ignorar»: nombres de fichero en minúsculas que no cuentan (dam readme no cuenta los README.md).
    """
    medida = Medida()
    for raiz, carpetas, ficheros in carpeta.walk(on_error=lambda e: None):
        carpetas[:] = [c for c in carpetas if not _es_enlace(raiz / c)]
        for nombre in ficheros:
            if nombre.lower() in ignorar:
                continue
            try:
                datos = (raiz / nombre).stat(follow_symlinks=False)
            except OSError:
                continue
            medida.ficheros += 1
            if esta_en_la_nube(datos):
                medida.nube += datos.st_size
            else:
                medida.disco += datos.st_size
    return medida


def tiene_remoto(repo: Path) -> bool | None:
    """Mira si .git/config tiene algún [remote "..."]. Sin lanzar git: es mucho más rápido."""
    config = repo / ".git" / "config"
    if not config.is_file():
        return None
    try:
        return '[remote "' in config.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def revisar(carpeta: Path) -> Informe:
    """Recorre la carpeta (sin entrar en enlaces ni en carpetas del sistema) y rellena el informe."""
    raiz = carpeta.expanduser().resolve()
    if not raiz.is_dir():
        raise TareasError(f"«{raiz}» no existe o no es una carpeta.")
    informe = Informe(raiz)
    repo_de: dict[Path, Repo | None] = {}  # cada carpeta -> el repo en el que está (o None)

    def rel(ruta: Path) -> str:
        return ruta.relative_to(raiz).as_posix() or "."

    def sumar(donde: Path, disco: int, nube: int, repo: Repo | None) -> None:
        partes = donde.relative_to(raiz).parts
        clave = partes[0] if partes else SUELTOS
        informe.tamano += disco
        informe.tamano_nube += nube
        informe.por_carpeta[clave] += disco
        informe.por_carpeta_nube[clave] += nube
        if repo:
            repo.tamano += disco + nube

    def sin_permiso(error: OSError) -> None:
        informe.sin_acceso.append(rel(Path(error.filename)) if error.filename else str(error))

    for actual, carpetas, ficheros in raiz.walk(on_error=sin_permiso):
        repo = repo_de.get(actual.parent) if actual != raiz else None
        if (actual / ".git").exists():
            repo = Repo(rel(actual), con_remoto=tiene_remoto(actual))
            informe.repos.append(repo)
        repo_de[actual] = repo

        quedan = []
        for nombre in carpetas:
            ruta = actual / nombre
            if _es_enlace(ruta) or nombre in SISTEMA:
                informe.saltadas.append(rel(ruta))
            elif nombre == ".git" or nombre in REGENERABLES or es_programa(nombre, repo is not None):
                medida = tamano_carpeta(ruta)  # se mide entera, pero no se lista por dentro
                informe.ficheros += medida.ficheros
                sumar(ruta, medida.disco, medida.nube, repo)
                if nombre in REGENERABLES:
                    informe.regenerables.append(Fichero(rel(ruta), medida.disco))
                elif nombre != ".git":
                    informe.programas.append(Fichero(rel(ruta), medida.disco))
            else:
                quedan.append(nombre)
        carpetas[:] = quedan
        informe.carpetas += len(quedan)

        hay_dll = any(n.lower().endswith(".dll") for n in ficheros)
        for nombre in ficheros:
            ruta = actual / nombre
            try:
                datos = ruta.stat(follow_symlinks=False)
            except OSError:
                informe.sin_acceso.append(rel(ruta))
                continue
            nube = esta_en_la_nube(datos)
            bytes_ = datos.st_size
            informe.ficheros += 1
            sumar(actual, 0 if nube else bytes_, bytes_ if nube else 0, repo)  # en la raíz: «sueltos»
            tipo = tipo_de(nombre, hay_dll)
            informe.cuantos_por_tipo[tipo] += 1
            (informe.nube_por_tipo if nube else informe.tamano_por_tipo)[tipo] += bytes_
            fichero = Fichero(rel(ruta), bytes_, nube)
            if tipo == "instaladores":
                informe.instaladores.append(fichero)
            if es_basura(nombre):
                informe.basura.append(fichero)
            if bytes_ >= LIMITE_GRANDE:
                informe.grandes.append(fichero)

    for lista in (informe.instaladores, informe.basura, informe.regenerables, informe.programas, informe.grandes):
        lista.sort(key=lambda f: f.tamano, reverse=True)
    informe.repos.sort(key=lambda r: r.ruta.lower())
    return informe


# ---------- informe en Markdown (--guardar) ----------
def _tabla(cabeceras: list[str], filas: list[list[str]]) -> list[str]:
    def limpia(texto: str) -> str:
        return texto.replace("|", "\\|")
    lineas = ["| " + " | ".join(cabeceras) + " |", "|" + "---|" * len(cabeceras)]
    lineas += ["| " + " | ".join(limpia(c) for c in fila) + " |" for fila in filas]
    return lineas


def resumen_tamano(lista: list[Fichero]) -> str:
    """«3.2 GB» o, si hay ficheros en la nube, «3.2 GB en el disco · 10.1 GB en la nube»."""
    nube = en_nube(lista)
    texto = tamano_legible(en_disco(lista))
    return f"{texto} en el disco · {tamano_legible(nube)} en la nube" if nube else texto


def _ficheros(titulo: str, explicacion: str, lista: list[Fichero], top: int) -> list[str]:
    lineas = [f"## {titulo} ({len(lista)} · {resumen_tamano(lista)})", "", explicacion, ""]
    if not lista:
        return lineas + ["Ninguno.", ""]
    filas = [[f"`{f.ruta}`", tamano_legible(f.tamano), "nube" if f.en_nube else "disco"] for f in lista[:top]]
    lineas += _tabla(["Ruta", "Tamaño", "Dónde"], filas)
    if len(lista) > top:
        lineas.append(f"\n…y {len(lista) - top} más.")
    return lineas + [""]


def a_markdown(informe: Informe, top: int = 15) -> str:
    """El informe completo en Markdown, para guardarlo y repasarlo con calma."""
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    lineas = [
        f"# Inventario de `{informe.carpeta}`", "",
        f"Generado con `dam inventario` el {fecha}. Solo se han leído nombres y tamaños: no se ha tocado nada.", "",
        f"- **{informe.ficheros}** ficheros en **{informe.carpetas}** carpetas · "
        f"**{tamano_legible(informe.tamano)}** en el disco · {tamano_legible(informe.tamano_nube)} solo en la nube",
        f"- Recuperable sin perder nada: basura {tamano_legible(en_disco(informe.basura))} · "
        f"carpetas regenerables {tamano_legible(en_disco(informe.regenerables))}",
        f"- Instaladores: {resumen_tamano(informe.instaladores)} (revisa si aún los necesitas)", "",
        "## Tamaño por carpeta", "",
    ]
    lineas += _tabla(["Carpeta", "En el disco", "Solo en la nube"],
                     [[f"`{c}`", tamano_legible(informe.por_carpeta[c]), tamano_legible(informe.por_carpeta_nube[c])]
                      for c in informe.carpetas_ordenadas])
    lineas += ["", "## Por tipo", ""]
    lineas += _tabla(["Tipo", "Ficheros", "En el disco", "Solo en la nube"],
                     [[t, str(informe.cuantos_por_tipo[t]), tamano_legible(informe.tamano_por_tipo[t]),
                       tamano_legible(informe.nube_por_tipo[t])] for t in informe.tipos_ordenados])
    lineas += ["", f"## Repos git ({len(informe.repos)})", "",
               "«Remoto» mira si el clon tiene un origin configurado, no si el repo existe en GitHub.", ""]
    remoto = {True: "sí", False: "**sin remoto configurado**", None: "?"}
    lineas += _tabla(["Repo", "Tamaño", "Remoto"],
                     [[f"`{r.ruta}`", tamano_legible(r.tamano), remoto[r.con_remoto]] for r in informe.repos])
    lineas.append("")
    lineas += _ficheros("Instaladores", "Si el programa ya está instalado, el instalador sobra.",
                        informe.instaladores, top)
    lineas += _ficheros("Basura", "Temporales, descargas a medias, miniaturas y bloqueos de Office.",
                        informe.basura, top)
    lineas += _ficheros("Carpetas regenerables", "Se vuelven a crear con `uv sync` o `npm install`.",
                        informe.regenerables, top)
    lineas += _ficheros("Programas y configuración", "Carpetas de programas (miniconda3, .vscode...): no se organizan.",
                        informe.programas, top)
    lineas += _ficheros("Ficheros grandes", f"De más de {tamano_legible(LIMITE_GRANDE)}.", informe.grandes, top)
    if informe.saltadas:
        lineas += ["## No recorridas", "", "Enlaces y carpetas del sistema (no se organizan):", ""]
        lineas += [f"- `{s}`" for s in informe.saltadas[:top]]
        lineas.append("")
    if informe.sin_acceso:
        lineas += [f"## Sin permiso de lectura ({len(informe.sin_acceso)})", ""]
        lineas += [f"- `{s}`" for s in informe.sin_acceso[:top]]
        lineas.append("")
    return "\n".join(lineas)
