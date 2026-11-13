"""dam doctor: revisa que un proyecto esté sano antes de subirlo o entregarlo.

Comprobaciones básicas (si falla alguna, sale con 1): git, .gitignore, .env ignorado y sin subir,
.env.example con las mismas variables, README y sin secretos a la vista. Recomendadas (solo avisan):
tests, dependencias declaradas, CI y ficheros grandes.

Del .env solo se leen los NOMBRES de las variables: los valores nunca salen de aquí.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from . import escanear
from .errores import TareasError

LIMITE_GRANDE = 50 * 1024 * 1024  # GitHub avisa a partir de 50 MB y rechaza más de 100 MB
LINEAS_MINIMAS_README = 5
NOMBRES_README = {"readme.md", "readme", "readme.txt", "readme.rst"}
FICHEROS_DEPENDENCIAS = {"pyproject.toml", "requirements.txt", "package.json"}
CARPETAS_TEST = {"tests", "test", "__tests__"}
PATRON_TEST = re.compile(r"^(test_.+\.py|.+_test\.py|.+\.(test|spec)\.(js|ts|jsx|tsx|mjs))$", re.I)
_VARIABLE = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=")


@dataclass
class Comprobacion:
    nombre: str
    estado: str  # "ok", "falta", "aviso" o "no aplica"
    detalle: str
    basica: bool = True


@dataclass
class Informe:
    carpeta: Path
    repos_dentro: list[str] = field(default_factory=list)  # si la carpeta es «la de fuera»
    comprobaciones: list[Comprobacion] = field(default_factory=list)

    @property
    def aplicables(self) -> list[Comprobacion]:
        return [c for c in self.comprobaciones if c.estado != "no aplica"]

    @property
    def correctas(self) -> int:
        return sum(1 for c in self.comprobaciones if c.estado == "ok")

    @property
    def fallan_basicas(self) -> list[str]:
        return [c.nombre for c in self.comprobaciones if c.basica and c.estado == "falta"]


def nombres_de_variables(ruta: Path) -> set[str]:
    """Los nombres de un fichero tipo .env (API_KEY=..., export PUERTO=...). Los valores se descartan."""
    nombres = set()
    for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        m = _VARIABLE.match(linea)
        if m:
            nombres.add(m.group(1))
    return nombres


def _lista(nombres) -> str:
    return ", ".join(sorted(nombres))


# ---------- básicas ----------
def repos_dentro(raiz: Path) -> list[str]:
    """Subcarpetas (un nivel) que son repositorios: «PROJECTE TERMINAL CLI» tiene dentro Terminal_CLI/."""
    try:
        return sorted(p.name for p in raiz.iterdir() if p.is_dir() and (p / ".git").exists())
    except OSError:
        return []


def es_carpeta_personal(raiz: Path) -> bool:
    """¿Es tu carpeta personal (~) y no un repositorio? Ahí no hay un proyecto que revisar.

    13-nov, en clase: «dam doctor» en una terminal nueva (que empieza en ~) revisó todo: certificados de
    librerías en .cache como «secretos», .nvm/package.json como «dependencias»... y tardó.
    """
    try:
        return raiz.resolve() == Path.home().resolve() and not escanear.es_repo(raiz)
    except OSError:
        return False


def proyectos_visibles(raiz: Path) -> list[str]:
    """Los repos de dentro, sin las carpetas ocultas (.nvm, .cache...): esos no son proyectos tuyos."""
    return [r for r in repos_dentro(raiz) if not r.startswith(".")]


def _git(raiz: Path, con_git: bool, subrepos: list[str]) -> Comprobacion:
    if con_git:
        return Comprobacion("Repositorio git", "ok", "Tiene historial de cambios.")
    if subrepos:
        return Comprobacion("Repositorio git", "falta",
                            f"Esta carpeta no lo es, pero dentro hay: {_lista(r + '/' for r in subrepos)}.")
    return Comprobacion("Repositorio git", "falta", "No es un repositorio: git init (y súbelo a GitHub).")


def _gitignore(raiz: Path) -> Comprobacion:
    if (raiz / ".gitignore").is_file():
        return Comprobacion(".gitignore", "ok", "Existe.")
    return Comprobacion(".gitignore", "falta", "Créalo con .env, .venv/, node_modules/ y __pycache__/.")


def _env_ignorado(raiz: Path, con_git: bool) -> Comprobacion:
    nombre = ".env en .gitignore"
    if con_git:
        # --no-index: dice si las reglas lo ignoran, aunque .env no exista o ya esté subido
        ignorado = escanear.ejecutar_git(raiz, "check-ignore", "-q", "--no-index", ".env").returncode == 0
    else:
        gitignore = raiz / ".gitignore"
        reglas = gitignore.read_text(encoding="utf-8", errors="replace").splitlines() if gitignore.is_file() else []
        ignorado = any(r.strip() in {".env", "/.env", ".env*", "*.env"} for r in reglas)
    if ignorado:
        return Comprobacion(nombre, "ok", "git no subirá tus claves.")
    return Comprobacion(nombre, "falta", "Añade una línea «.env» a .gitignore.")


def _env_sin_subir(raiz: Path, con_git: bool) -> Comprobacion:
    nombre = "Ningún .env subido a git"
    if not con_git:
        return Comprobacion(nombre, "no aplica", "No es un repositorio git.")
    salida = escanear.ejecutar_git(raiz, "ls-files", "-z").stdout
    subidos = [r for r in salida.split("\0") if r and escanear.es_env(Path(r).name)]
    if not subidos:
        return Comprobacion(nombre, "ok", "Ninguno.")
    return Comprobacion(nombre, "falta", f"Subido: {_lista(subidos)}. git rm --cached FICHERO y cambia esas claves.")


def _env_example(raiz: Path) -> Comprobacion:
    nombre = ".env.example al día"
    env, ejemplo = raiz / ".env", raiz / ".env.example"
    if not env.is_file() and not ejemplo.is_file():
        return Comprobacion(nombre, "no aplica", "El proyecto no usa .env.")
    if not ejemplo.is_file():
        return Comprobacion(nombre, "falta", "Crea .env.example con los mismos nombres y los valores vacíos.")
    if not env.is_file():
        return Comprobacion(nombre, "ok", "Hay plantilla (aquí no hay .env para comparar).")
    en_env, en_ejemplo = nombres_de_variables(env), nombres_de_variables(ejemplo)
    if faltan := en_env - en_ejemplo:
        return Comprobacion(nombre, "falta", f"Faltan en .env.example: {_lista(faltan)}.")
    if sobran := en_ejemplo - en_env:
        return Comprobacion(nombre, "aviso", f"Están en .env.example pero no en tu .env: {_lista(sobran)}.")
    cuantas = "la misma variable" if len(en_env) == 1 else f"las mismas {len(en_env)} variables"
    return Comprobacion(nombre, "ok", f"Tiene {cuantas} que tu .env.")


def _readme(raiz: Path) -> Comprobacion:
    encontrados = [p for p in raiz.iterdir() if p.is_file() and p.name.lower() in NOMBRES_README]
    if not encontrados:
        return Comprobacion("README", "falta", "Crea README.md: qué es, cómo se instala y cómo se usa.")
    texto = encontrados[0].read_text(encoding="utf-8", errors="replace")
    lineas = sum(1 for linea in texto.splitlines() if linea.strip())
    if lineas < LINEAS_MINIMAS_README:
        texto_lineas = "1 línea" if lineas == 1 else f"{lineas} líneas"
        return Comprobacion("README", "aviso", f"Muy corto ({texto_lineas}): explica qué es y cómo se usa.")
    return Comprobacion("README", "ok", f"{encontrados[0].name}, {lineas} líneas.")


def _secretos(raiz: Path, ficheros: list[Path]) -> Comprobacion:
    # .env es el sitio correcto para las claves: que esté ignorado lo revisan las comprobaciones de arriba
    sin_env = [f for f in ficheros if not escanear.es_env(f.name)]
    hallazgos, revisados, _ = escanear.escanear_arbol(raiz, solo_alta=True, ficheros=sin_env)
    if not hallazgos:
        return Comprobacion("Sin secretos a la vista", "ok", f"Ninguno seguro en {revisados} ficheros.")
    donde = _lista({h.donde for h in hallazgos})
    return Comprobacion("Sin secretos a la vista", "falta",
                        f"{len(hallazgos)} en {donde}. Míralos con dam scan-secrets.")


# ---------- recomendadas ----------
def _tests(rels: list[Path]) -> Comprobacion:
    de_test = [r for r in rels if PATRON_TEST.match(r.name) or CARPETAS_TEST & set(r.parts[:-1])]
    if de_test:
        return Comprobacion("Tests", "ok", f"{len(de_test)} ficheros de test.", basica=False)
    return Comprobacion("Tests", "aviso", "No encuentro tests (tests/test_*.py, *.test.js...).", basica=False)


def _dependencias(rels: list[Path]) -> Comprobacion:
    declaradas = sorted({r.as_posix() for r in rels if r.name in FICHEROS_DEPENDENCIAS and len(r.parts) <= 2})
    if declaradas:
        return Comprobacion("Dependencias declaradas", "ok", _lista(declaradas), basica=False)
    if any(r.suffix.lower() == ".html" for r in rels):
        return Comprobacion("Dependencias declaradas", "no aplica", "Web estática.", basica=False)
    return Comprobacion("Dependencias declaradas", "aviso",
                        "Sin pyproject.toml, requirements.txt ni package.json: nadie sabrá qué instalar.", basica=False)


def _ci(rels: list[Path]) -> Comprobacion:
    flujos = [r for r in rels if r.parts[:2] == (".github", "workflows") and r.suffix.lower() in {".yml", ".yaml"}]
    if flujos:
        return Comprobacion("CI (GitHub Actions)", "ok", _lista(r.name for r in flujos), basica=False)
    return Comprobacion("CI (GitHub Actions)", "aviso",
                        "Añade .github/workflows/ para pasar los tests en cada push.", basica=False)


def _grandes(raiz: Path, rels: list[Path]) -> Comprobacion:
    grandes = []
    for rel in rels:
        try:
            if (raiz / rel).stat().st_size > LIMITE_GRANDE:
                grandes.append(rel.as_posix())
        except OSError:
            continue
    if grandes:
        return Comprobacion("Ficheros grandes", "aviso",
                            f"Más de 50 MB: {_lista(grandes)}. Mejor fuera de git.", basica=False)
    return Comprobacion("Ficheros grandes", "ok", "Ninguno de más de 50 MB.", basica=False)


def revisar(carpeta: Path) -> Informe:
    """Hace todas las comprobaciones. Solo lee: no cambia nada del proyecto."""
    raiz = carpeta.expanduser().resolve()
    if not raiz.is_dir():
        raise TareasError(f"«{raiz}» no existe o no es una carpeta.")
    con_git = escanear.es_repo(raiz)
    ficheros = escanear.ficheros_del_proyecto(raiz)  # lo que se subiría (respeta .gitignore)
    rels = [f.relative_to(raiz) for f in ficheros]
    subrepos = [] if con_git else repos_dentro(raiz)
    return Informe(raiz, subrepos, [
        _git(raiz, con_git, subrepos),
        _gitignore(raiz),
        _env_ignorado(raiz, con_git),
        _env_sin_subir(raiz, con_git),
        _env_example(raiz),
        _readme(raiz),
        _secretos(raiz, ficheros),
        _tests(rels),
        _dependencias(rels),
        _ci(rels),
        _grandes(raiz, rels),
    ])
