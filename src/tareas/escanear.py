"""scan-secrets: busca claves, tokens y contraseñas expuestas antes de subirlas a GitHub.

Reglas de oro: NUNCA se guarda ni se imprime un secreto entero (solo una muestra enmascarada)
y un secreto que ya llegó a GitHub hay que cambiarlo (revocarlo), no basta con borrarlo.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errores import GitError, TareasError

MAX_BYTES = 1_000_000  # los ficheros más grandes no se revisan (suelen ser binarios o datos)
CARPETAS_IGNORADAS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache",
                      "dist", "build", ".mypy_cache", ".ruff_cache"}
EXTENSIONES_CLAVE = {".pem", ".key", ".p12", ".pfx", ".ppk"}
MARCADORES = ("example", "ejemplo", "your", "tu_", "tu-", "changeme", "xxxx", "****", "${",
              "{env:", "dummy", "placeholder", "<", ">", "...", "environ", "getenv", "process.env")

# Documentos e imágenes: no se leen como texto (un PDF «parece» texto y da falsos avisos)
EXTENSIONES_BINARIAS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp", ".zip", ".gz",
                        ".7z", ".rar", ".docx", ".xlsx", ".pptx", ".odt", ".doc", ".xls", ".ppt", ".exe",
                        ".dll", ".ova", ".vdi", ".vmdk", ".iso", ".mp3", ".mp4", ".mov", ".woff", ".woff2"}
FIRMAS_BINARIAS = (b"%PDF-", b"PK\x03\x04", b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"\x1f\x8b",
                   b"Rar!", b"7z\xbc\xaf", b"MZ", b"\xd0\xcf\x11\xe0")
# Contraseñas que son claramente de plantilla (README, .env de ejemplo...)
CLAVES_DE_PLANTILLA = {"password", "passwd", "pass", "pwd", "contraseña", "contrasena", "clave", "secret",
                       "tu_password", "tu_clave", "tu_contraseña", "tupassword", "changeme", "123456",
                       "usuario", "user", "admin", "test", "root"}

GENERICO = re.compile(
    r"(?i)\b[\w\-]*(?:api[_\-]?key|secret|token|passw(?:or)?d|pwd|_key)[\w\-]*[\"']?\s*[:=]\s*[\"']?"
    r"([^\s\"'#,;]{10,})"
)
PATRONES: list[tuple[str, re.Pattern[str], str]] = [
    ("URL con usuario y contraseña (MongoDB u otra)",
     re.compile(r"[a-z][a-z0-9+.\-]*://[^\s:/@'\"]+:[^\s@/'\"]{3,}@[^\s'\"]+", re.I), "alta"),
    ("Token de GitHub", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{50,})\b"), "alta"),
    ("Clave de Google o Gemini (AIza...)", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"), "alta"),
    ("Clave de Resend (re_...)", re.compile(r"\bre_[A-Za-z0-9]{20,}\b"), "alta"),
    ("Clave de AWS (AKIA...)", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "alta"),
    ("Token de Slack", re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"), "alta"),
    ("Clave tipo OpenAI o Anthropic (sk-...)", re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_\-]{20,}\b"), "alta"),
    ("Token JWT (p. ej. clave de Supabase)",
     re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"), "alta"),
    ("Clave privada", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY(?: BLOCK)?-----"), "alta"),
    ("Asignación sospechosa (clave, token o contraseña)", GENERICO, "posible"),
]


@dataclass
class Hallazgo:
    donde: str  # fichero, o «commit:fichero» en el historial
    linea: int | None
    tipo: str
    muestra: str  # SIEMPRE enmascarada
    confianza: str  # "alta" o "posible"


def mascara(valor: str, tipo: str = "") -> str:
    if tipo == "Clave privada" or len(valor) <= 8:
        return "(oculto)"
    return f"{valor[:4]}… ({len(valor)} caracteres)"


def _es_marcador(texto: str) -> bool:
    bajo = texto.lower()
    return any(m in bajo for m in MARCADORES)


_URL_CRED = re.compile(r"://([^\s:/@'\"]+):([^\s@/'\"]+)@([^\s/'\"]+)")


def _url_es_plantilla(texto: str) -> bool:
    """mongodb://usuario:password@cluster... o postgres://postgres:password@db.xxx... son de ejemplo."""
    m = _URL_CRED.search(texto)
    if not m:
        return False
    usuario, clave, host = (g.lower() for g in m.groups())
    return clave in CLAVES_DE_PLANTILLA or re.fullmatch(r"x+", clave) is not None or ".xxx" in host or host.startswith("xxx")


def _parece_secreto(valor: str) -> bool:
    """Para la regla genérica: con letras y números, y sin pinta de código (llamadas, rutas...)."""
    return (any(c.isdigit() for c in valor) and any(c.isalpha() for c in valor)
            and "(" not in valor and not valor.startswith(("os.", "self.", "env.")))


def analizar_linea(texto: str) -> list[tuple[str, str, str]]:
    """Devuelve [(tipo, valor_crudo, confianza)]. El valor crudo no debe salir de este módulo."""
    if "dam:ignore" in texto:
        return []
    encontrados = []
    for tipo, patron, confianza in PATRONES:
        for m in patron.finditer(texto):
            valor = m.group(1) if patron is GENERICO else m.group(0)
            if _es_marcador(m.group(0)):
                continue
            if tipo.startswith("URL con usuario") and _url_es_plantilla(m.group(0)):
                continue
            if patron is GENERICO and not _parece_secreto(valor):
                continue
            encontrados.append((tipo, valor, confianza))
    if any(c == "alta" for _, _, c in encontrados):  # si ya hay uno seguro, el «posible» sobra
        encontrados = [e for e in encontrados if e[2] == "alta"]
    return encontrados


def _hallazgos_de_texto(donde: str, contenido: str, filtro_alta: bool) -> list[Hallazgo]:
    resultado = []
    for n, linea in enumerate(contenido.splitlines(), start=1):
        for tipo, valor, confianza in analizar_linea(linea):
            if filtro_alta and confianza != "alta":
                continue
            resultado.append(Hallazgo(donde, n, tipo, mascara(valor, tipo), confianza))
    return resultado


# ---------- git ----------
def ejecutar_git(raiz: Path, *args: str) -> subprocess.CompletedProcess:
    entorno = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}
    try:
        return subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, encoding="utf-8",
                              errors="replace", stdin=subprocess.DEVNULL, env=entorno)
    except FileNotFoundError:
        raise GitError("No encuentro git. Instálalo: winget install --id Git.Git -e") from None


def es_repo(raiz: Path) -> bool:
    return ejecutar_git(raiz, "rev-parse", "--is-inside-work-tree").stdout.strip() == "true"


def ficheros_del_proyecto(raiz: Path) -> list[Path]:
    """Lo que se subiría: ficheros rastreados + nuevos NO ignorados. Fuera de git, todo salvo carpetas típicas."""
    if es_repo(raiz):
        p = ejecutar_git(raiz, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
        rutas = [raiz / r for r in p.stdout.split("\0") if r]
        return sorted(r for r in rutas if r.is_file())
    encontrados = []
    for carpeta, subcarpetas, nombres in os.walk(raiz):
        subcarpetas[:] = [d for d in subcarpetas if d not in CARPETAS_IGNORADAS]
        encontrados += [Path(carpeta) / n for n in nombres]
    return sorted(encontrados)


def es_env(nombre: str) -> bool:
    n = nombre.lower()
    return (n.startswith(".env") or n.endswith(".env") or ".env." in n) and not n.endswith(".example")


def es_clave_privada(ruta: Path) -> bool:
    """.pem, .key, id_rsa... (la parte pública, id_rsa.pub, sí se puede compartir)."""
    return ruta.suffix.lower() in EXTENSIONES_CLAVE or (
        ruta.name.lower().startswith(("id_rsa", "id_ed25519", "id_ecdsa")) and ruta.suffix.lower() != ".pub"
    )


def escanear_arbol(raiz: Path, solo_alta: bool = False,
                   ficheros: list[Path] | None = None) -> tuple[list[Hallazgo], int, int]:
    """Devuelve (hallazgos, ficheros_revisados, ficheros_omitidos).

    Sin «ficheros» revisa lo que se subiría a git; con ella, solo esa lista (la usa dam entregar).
    """
    hallazgos, revisados, omitidos = [], 0, 0
    for ruta in ficheros if ficheros is not None else ficheros_del_proyecto(raiz):
        rel = ruta.relative_to(raiz).as_posix()
        if es_env(ruta.name):
            hallazgos.append(Hallazgo(rel, None, "Fichero .env que NO está en .gitignore", "(fichero)", "alta"))
        if es_clave_privada(ruta):
            hallazgos.append(Hallazgo(rel, None, "Fichero de clave privada", "(fichero)", "alta"))
            continue
        try:
            if ruta.stat().st_size > MAX_BYTES:
                omitidos += 1
                continue
            datos = ruta.read_bytes()
        except OSError:
            omitidos += 1
            continue
        if ruta.suffix.lower() in EXTENSIONES_BINARIAS or datos.startswith(FIRMAS_BINARIAS) or b"\0" in datos[:8000]:
            omitidos += 1
            continue
        revisados += 1
        hallazgos += _hallazgos_de_texto(rel, datos.decode("utf-8", errors="replace"), solo_alta)
    return hallazgos, revisados, omitidos


_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def _escanear_diff(raiz: Path, args: list[str], con_commit: bool, solo_alta: bool) -> list[Hallazgo]:
    if not es_repo(raiz):
        raise TareasError(f"«{raiz}» no es un repositorio git: no hay historial ni zona de preparación.")
    proceso = subprocess.Popen(
        ["git", "-C", str(raiz), *args], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"},
    )
    visto: set[tuple[str, str, str]] = set()
    hallazgos: list[Hallazgo] = []
    commit, fichero, linea, cabecera = "", "", 0, False
    assert proceso.stdout is not None
    for texto in proceso.stdout:
        texto = texto.rstrip("\n")
        if texto.startswith("@@commit "):
            commit = texto[9:16]
        elif texto.startswith("diff --git"):
            cabecera = True
        elif cabecera and texto.startswith("+++ "):
            fichero = texto[6:] if texto.startswith("+++ b/") else ""
            if Path(fichero).suffix.lower() in EXTENSIONES_BINARIAS:
                fichero = ""  # documentos e imágenes: no se leen como texto
        elif m := _HUNK.match(texto):
            cabecera, linea = False, int(m.group(1))
        elif not cabecera and texto.startswith("+") and fichero:
            for tipo, valor, confianza in analizar_linea(texto[1:]):
                if solo_alta and confianza != "alta":
                    continue
                donde = f"{commit}:{fichero}" if con_commit else fichero
                clave = (donde, tipo, valor)
                if clave not in visto:
                    visto.add(clave)
                    hallazgos.append(Hallazgo(donde, linea, tipo, mascara(valor, tipo), confianza))
            linea += 1
    proceso.wait()
    if proceso.returncode not in (0, None):
        raise GitError("git no pudo leer el historial (¿todavía no hay ningún commit?)")
    return hallazgos


def escanear_staged(raiz: Path, solo_alta: bool = False) -> list[Hallazgo]:
    return _escanear_diff(raiz, ["diff", "--cached", "-U0", "--no-color", "--no-ext-diff"], False, solo_alta)


def escanear_historial(raiz: Path, solo_alta: bool = False) -> list[Hallazgo]:
    return _escanear_diff(raiz, ["log", "--all", "-p", "-U0", "--no-color", "--no-ext-diff",
                                 "--format=@@commit %H"], True, solo_alta)
