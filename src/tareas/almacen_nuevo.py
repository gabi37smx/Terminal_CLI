"""mochila crear-almacen: tu almacén de apuntes en GitHub, aunque no sepas git (ADR-0005).

El almacén es un repo privado TUYO, con una carpeta por asignatura. Se llama como tu ciclo
(DAM-almacen, ASIR-almacen...). Si aún no lo tienes, mochila abre GitHub con el nombre y «privado» ya
puestos: solo pulsas «Create repository». mochila nunca ve tu contraseña ni tu token: de eso se
encarga git.

Aquí solo está la lógica, sin preguntas por pantalla (esas están en cli.py), para poder probarla.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from urllib.parse import urlencode

from . import ciclos
from .errores import GitError

GITHUB = "https://github.com"  # las pruebas lo cambian por una carpeta con repos de mentira
_USUARIO = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})$")  # las reglas de GitHub
# Rutas que puso mochila (o el acciones.json del repo): esas se pueden cambiar al cambiar de ciclo
_RUTA_DE_CICLO = re.compile(r"^~/(?:" + "|".join([*ciclos.CICLOS, "apuntes"]) + r")-almacen$", re.IGNORECASE)
MENSAJE_PRIMERA_SUBIDA = "Carpetas de mis asignaturas (mochila crear-almacen)"


def nombre(ciclo: str | None) -> str:
    """'asir' -> 'ASIR-almacen'. Sin ciclo o con «otro»: 'APUNTES-almacen'."""
    if not ciclo or ciclo == ciclos.OTRO:
        return "APUNTES-almacen"
    return f"{ciclos.CICLOS[ciclo].nombre}-almacen" if ciclo in ciclos.CICLOS else f"{ciclo.upper()}-almacen"


def ruta_para(ruta_actual: str, ciclo: str) -> str:
    """La ruta del almacén en acciones.json tras elegir ciclo.

    Si es una de las que pone mochila (~/DAM-almacen, ~/SMX-almacen...), pasa a la de tu ciclo.
    Si la escribiste tú (D:/apuntes, ~/Documentos/mis-apuntes...), no se toca.
    """
    return f"~/{nombre(ciclo)}" if _RUTA_DE_CICLO.match(ruta_actual.strip()) else ruta_actual


def limpiar_usuario(texto: str) -> str:
    """'  https://github.com/Ana-22/ ' -> 'Ana-22'. Lanza ValueError si no puede ser un usuario de GitHub."""
    t = texto.strip().rstrip("/")
    t = re.sub(r"^(?:https?://)?(?:www\.)?github\.com/", "", t, flags=re.IGNORECASE).lstrip("@")
    if not _USUARIO.match(t):
        raise ValueError(f"«{texto.strip()}» no es un usuario de GitHub: es lo que va detrás de github.com/ "
                         "(letras, números y guiones)")
    return t


def url_repo(usuario: str, repo: str) -> str:
    return f"{GITHUB}/{usuario}/{repo}.git"


def url_crear(repo: str) -> str:
    """La página de GitHub para crear un repo, con el nombre y «privado» ya puestos."""
    return "https://github.com/new?" + urlencode({
        "name": repo,
        "visibility": "private",
        "description": "Mis apuntes, ordenados por asignatura (mochila sync)",
    })


def abrir_navegador(url: str) -> bool:
    """Abre la página si hay escritorio. En un Linux sin escritorio no lo intenta: abriría un
    navegador de texto dentro de la terminal. La URL se enseña siempre, por si acaso."""
    if sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False
    try:
        return webbrowser.open(url)
    except webbrowser.Error:
        return False


def _git_no_esta() -> GitError:
    return GitError("No encuentro git. Instálalo: winget install --id Git.Git -e (o sudo apt install git)")


def clonar(url: str, destino: Path) -> bool:
    """git clone con la terminal a la vista: si el repo es privado, git pide ahí el usuario y el token
    (en Windows abre el navegador). Devuelve si ha ido bien."""
    if shutil.which("git") is None:
        raise _git_no_esta()
    destino.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run(["git", "clone", url, str(destino)]).returncode == 0


def _git(ruta: Path, *args: str, a_la_vista: bool = False) -> subprocess.CompletedProcess:
    orden = ["git", "-c", "core.quotepath=off", "-C", str(ruta), *args]  # tildes tal cual, no «\303\241»
    try:
        if a_la_vista:  # push: si git necesita el token, lo pide en la terminal (y en tu idioma)
            return subprocess.run(orden)
        # En inglés, como en sincronizar.py: los errores se reconocen por su texto («who you are»...)
        return subprocess.run(orden, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              stdin=subprocess.DEVNULL, env={**os.environ, "LC_ALL": "C", "LANGUAGE": "C"})
    except FileNotFoundError:
        raise _git_no_esta() from None


def _commit(ruta: Path, *args: str) -> None:
    """git commit; si falla, un GitError que se entienda (sobre todo si git no sabe quién eres)."""
    p = _git(ruta, "commit", *args)
    if p.returncode != 0:
        if "user.name" in p.stderr + p.stdout or "who you are" in p.stderr + p.stdout:
            raise GitError("git no sabe tu nombre ni tu correo. Ponlos una vez con:\n"
                           '  git config --global user.name "Tu Nombre"\n'
                           '  git config --global user.email "tu@correo.es"\n'
                           "y repite: mochila crear-almacen")
        raise GitError(f"No he podido guardar las carpetas: {(p.stderr or p.stdout).strip()}")


def esta_vacio(ruta: Path) -> bool:
    """¿Es un repo recién creado, sin ningún commit?"""
    return _git(ruta, "rev-parse", "--verify", "--quiet", "HEAD").returncode != 0


def hay_cambios(ruta: Path) -> bool:
    """¿Hay algo en el almacén que aún no está en ningún commit (p. ej., lo que ordenaste sin GitHub)?"""
    return bool(_git(ruta, "status", "--porcelain").stdout.strip())


def solo_en_este_equipo(ruta: Path) -> bool:
    """¿Es un almacén sin ningún remoto? Lo crea así crear_local, pero también vale un «git init» hecho a
    mano: en los dos casos, mochila sync no tiene adónde subir y crear-almacen ofrece conectarlo."""
    p = _git(ruta, "remote")
    return p.returncode == 0 and not p.stdout.strip()


def crear_local(ruta: Path) -> None:
    """Un almacén solo en este equipo, para quien aún no tiene GitHub: un repo git vacío en la rama main.

    Issue #53: sin GitHub no había almacén, y sin almacén no se podía ni ordenar. Se sube después con
    mochila crear-almacen (conectar).
    """
    if shutil.which("git") is None:
        raise _git_no_esta()
    ruta.mkdir(parents=True, exist_ok=True)
    p = _git(ruta, "init")
    if p.returncode != 0:
        raise GitError(f"No he podido crear el almacén en {ruta}: {(p.stderr or p.stdout).strip()}")
    _git(ruta, "symbolic-ref", "HEAD", "refs/heads/main")  # GitHub usa main; el git de clase quizá master


def guardar_carpetas(ruta: Path) -> None:
    """En un almacén vacío: el primer commit, con las carpetas de las asignaturas (sin subir nada)."""
    _git(ruta, "symbolic-ref", "HEAD", "refs/heads/main")  # sin commits, symbolic-ref basta para llamarla main
    _git(ruta, "add", "-A")
    _commit(ruta, "-m", MENSAJE_PRIMERA_SUBIDA)


def primera_subida(ruta: Path) -> None:
    """En un almacén vacío: commit con las carpetas y push a main, que queda como rama remota
    (sin eso, mochila sync no sabe adónde subir)."""
    guardar_carpetas(ruta)
    if _git(ruta, "push", "-u", "origin", "main", a_la_vista=True).returncode != 0:
        raise GitError("Las carpetas están guardadas en tu equipo, pero no he podido subirlas a GitHub. "
                       f'Cuando tengas red, entra en el almacén y súbelas una vez con: git -C "{ruta}" push -u origin main')


def conectar(ruta: Path, url: str, repo: str) -> None:
    """Sube a GitHub un almacén que estaba solo en este equipo y deja ese repo como su remoto.

    El repo de GitHub tiene que estar VACÍO (sin README): si no, GitHub no acepta lo que subes.
    """
    if esta_vacio(ruta):  # sin asignaturas (ciclo «otro») no hay nada que subir: un commit vacío
        _commit(ruta, "--allow-empty", "-m", MENSAJE_PRIMERA_SUBIDA)
    # Con commits, «branch -M» sí la renombra (un «git init» a mano la llama master); symbolic-ref no
    p = _git(ruta, "branch", "-M", "main")
    if p.returncode != 0:
        raise GitError(f"No he podido llamar main a tu rama: {(p.stderr or p.stdout).strip()}")
    hay_origin = _git(ruta, "remote", "get-url", "origin").returncode == 0
    p = _git(ruta, "remote", "set-url" if hay_origin else "add", "origin", url)
    if p.returncode != 0:
        raise GitError(f"No he podido apuntar tu almacén a {repo}: {(p.stderr or p.stdout).strip()}")
    if _git(ruta, "push", "-u", "origin", "main", a_la_vista=True).returncode != 0:
        if not hay_origin:  # como estaba: así, al repetir crear-almacen, vuelve a ofrecer subirlo
            _git(ruta, "remote", "remove", "origin")
        raise GitError(
            f"No he podido subir tu almacén a {repo}. Si pone «Repository not found»: revisa el usuario y que "
            f"ya hayas creado {repo}. Si pone «rejected» o «fetch first»: el repo de GitHub no está vacío (lo "
            "creaste con README); bórralo y créalo otra vez sin marcar nada. Tus apuntes siguen en tu equipo. "
            "Para repetirlo: mochila crear-almacen"
        )
