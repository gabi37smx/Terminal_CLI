"""Almacén de apuntes en git: status y sync seguros entre el PC de clase, el de casa y el USB.

Todo se hace con `git` mediante subprocess con lista de argumentos (sin shell=True), así
funciona igual en Linux, Windows y macOS. La regla de oro: ante la duda, NO tocar nada.
"""

from __future__ import annotations

import os
import socket
import subprocess
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .errores import GitError, TareasError

MAX_MB = 95  # GitHub rechaza ficheros de más de 100 MB
CARPETAS_PRIVADAS = ("documentacio",)  # nunca se suben al almacén


def _normalizar_nombre(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.lower()


def _es_privada(ruta: str) -> bool:
    return any(_normalizar_nombre(parte) in CARPETAS_PRIVADAS for parte in Path(ruta).parts)


@dataclass
class Cambio:
    estado: str  # "nuevo", "modificado" o "borrado"
    ruta: str


@dataclass
class Situacion:
    pathspec: str
    rama: str
    remota: str
    locales: list[Cambio]
    adelantados: int  # commits locales sin subir
    atrasados: int  # commits en GitHub que no tienes
    remotos: list[Cambio]
    sin_conexion: str = ""  # si no se pudo hacer fetch, el motivo

    @property
    def hay_local(self) -> bool:
        return bool(self.locales) or self.adelantados > 0

    @property
    def hay_remoto(self) -> bool:
        return self.atrasados > 0


@dataclass
class InformeSync:
    estado: str  # "actualizado", "descargado", "subido", "integrado" o "pendiente"
    mensajes: list[str] = field(default_factory=list)
    detalle: str = ""
    simulado: bool = False


def traducir_error(texto: str) -> str:
    """Convierte la salida de error de git en un mensaje humano en español."""
    t = texto.lower()
    ultima = next((l for l in reversed(texto.strip().splitlines()) if l.strip()), "error de git")
    if any(x in t for x in ("authentication failed", "terminal prompts disabled",
                            "returned error: 403", "returned error: 401",
                            "permission denied (publickey)", "could not read username")):
        return ("GitHub no te reconoce: inicia sesión (Git Credential Manager, token o "
                "`gh auth login`). No se ha tocado ningún fichero.")
    if any(x in t for x in ("could not resolve host", "unable to access", "failed to connect",
                            "network is unreachable", "connection timed out",
                            "could not read from remote", "connection refused")):
        return "Sin conexión con GitHub: comprueba internet. No se ha tocado ningún fichero."
    if "dubious ownership" in t:
        return ("Git desconfía de esta carpeta (pasa en USB exFAT/FAT32). Solución: "
                "git config --global --add safe.directory RUTA_DEL_ALMACEN")
    if "please tell me who you are" in t or "unable to auto-detect email" in t:
        return ('Git no sabe quién eres: git config --global user.name "Tu Nombre" y '
                'git config --global user.email "tu@correo"')
    if any(x in t for x in ("non-fast-forward", "fetch first", "[rejected]", "failed to push")):
        return ("La rama está desactualizada: hay cambios en GitHub que no tienes. "
                "Usa `dam sync --integrar` o descárgalos primero.")
    if "conflict" in t:
        return "Hay un conflicto de fusión real: hay que resolverlo a mano (git status te dice dónde)."
    if "not a git repository" in t:
        return "Esa carpeta no es un repositorio git. ¿Es la carpeta correcta del almacén?"
    return ultima


def _estado_de_diff(letra: str) -> str:
    return {"A": "nuevo", "D": "borrado"}.get(letra[:1], "modificado")


class Almacen:
    def __init__(self, ruta: Path, carpeta_asignaturas: str = "asignaturas"):
        self.ruta = ruta.expanduser()
        self.carpeta_asignaturas = carpeta_asignaturas

    # ---------- git de bajo nivel ----------
    def _git(self, *args: str, comprobar: bool = True) -> subprocess.CompletedProcess:
        orden = ["git", "-c", "core.quotepath=off", "-C", str(self.ruta), *args]
        entorno = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C", "LANGUAGE": "C"}
        try:
            p = subprocess.run(
                orden, capture_output=True, text=True, encoding="utf-8", errors="replace",
                stdin=subprocess.DEVNULL, env=entorno,
            )
        except FileNotFoundError:
            raise GitError("No encuentro git. Instálalo: winget install --id Git.Git -e") from None
        if comprobar and p.returncode != 0:
            raise GitError(traducir_error(p.stderr + p.stdout))
        return p

    # ---------- comprobaciones ----------
    def comprobar(self) -> None:
        if not self.ruta.is_dir():
            raise GitError(
                f"El almacén «{self.ruta}» no existe en este equipo. "
                f'Clónalo con: git clone URL_DE_TU_REPO "{self.ruta}"'
            )
        p = self._git("rev-parse", "--is-inside-work-tree", comprobar=False)
        if p.returncode != 0 or p.stdout.strip() != "true":
            raise GitError(traducir_error(p.stderr) if p.stderr.strip()
                           else f"«{self.ruta}» no es un repositorio git")
        up = self._git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}", comprobar=False)
        if up.returncode != 0:
            raise GitError("La rama actual no tiene remoto. Ejecuta una vez en el almacén: "
                           "git push -u origin main")

    def alcance(self, asignatura: str | None) -> str:
        """Pathspec de git (siempre con «/», es sintaxis de git, no una ruta del sistema)."""
        if not asignatura:
            return "."
        base = self.ruta / self.carpeta_asignaturas
        if Path(asignatura).name != asignatura or asignatura in (".", ".."):
            raise TareasError(f"«{asignatura}» no es un nombre de asignatura válido")
        if not (base / asignatura).is_dir():
            disponibles = sorted(p.name for p in base.iterdir() if p.is_dir()) if base.is_dir() else []
            raise TareasError(
                f"No existe la asignatura «{asignatura}» en {base}. "
                f"Hay: {', '.join(disponibles) or 'ninguna'}"
            )
        return f"{self.carpeta_asignaturas}/{asignatura}"

    # ---------- lectura del estado ----------
    def _locales(self, pathspec: str) -> list[Cambio]:
        p = self._git("status", "--porcelain=v1", "-z", "--untracked-files=all", "--", pathspec)
        partes = p.stdout.split("\0")
        cambios, i = [], 0
        while i < len(partes):
            entrada = partes[i]
            i += 1
            if len(entrada) < 4:
                continue
            xy, ruta = entrada[:2], entrada[3:]
            if xy[0] in "RC":
                i += 1  # en renombrados, la siguiente entrada es el nombre antiguo
            if _es_privada(ruta):
                continue
            estado = "nuevo" if xy == "??" else "borrado" if "D" in xy else "modificado"
            cambios.append(Cambio(estado, ruta))
        return cambios

    def _contar(self, rango: str) -> int:
        return int(self._git("rev-list", "--count", rango).stdout.strip() or 0)

    def _remotos(self) -> list[Cambio]:
        p = self._git("diff", "--name-status", "HEAD...@{u}")
        cambios = []
        for linea in p.stdout.splitlines():
            trozos = linea.split("\t")
            if len(trozos) >= 2 and not _es_privada(trozos[-1]):
                cambios.append(Cambio(_estado_de_diff(trozos[0]), trozos[-1]))
        return cambios

    def analizar(self, asignatura: str | None = None, tolerante: bool = False) -> Situacion:
        self.comprobar()
        pathspec = self.alcance(asignatura)
        sin_conexion = ""
        try:
            self._git("fetch", "--prune")
        except GitError as e:
            if not tolerante:
                raise
            sin_conexion = str(e)
        rama = self._git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        remota = self._git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").stdout.strip()
        return Situacion(
            pathspec=pathspec, rama=rama, remota=remota,
            locales=self._locales(pathspec),
            adelantados=self._contar("@{u}..HEAD"),
            atrasados=self._contar("HEAD..@{u}"),
            remotos=self._remotos(),
            sin_conexion=sin_conexion,
        )

    # ---------- sincronizar ----------
    def _revisar_peligrosos(self, cambios: list[Cambio]) -> None:
        problemas = []
        for c in cambios:
            ruta = self.ruta / c.ruta
            nombre = ruta.name.lower()
            if nombre.startswith(".env") and not nombre.endswith(".example"):
                problemas.append(f"{c.ruta} (parece un fichero de secretos)")
            elif c.estado != "borrado" and ruta.is_file() and ruta.stat().st_size > MAX_MB * 1024 * 1024:
                problemas.append(f"{c.ruta} (pesa más de {MAX_MB} MB y GitHub lo rechazaría)")
        if problemas:
            raise TareasError(
                "No subo esto, revísalo (añádelo a .gitignore o sácalo del almacén):\n  - "
                + "\n  - ".join(problemas)
            )

    def _privadas_en_indice(self) -> list[str]:
        p = self._git("diff", "--cached", "--name-only", "-z")
        return [r for r in p.stdout.split("\0") if r and _es_privada(r)]

    def _guardar(self, s: Situacion, mensaje: str) -> None:
        """git add (solo del alcance) + commit, desindexando siempre las carpetas privadas."""
        if not s.locales:
            return
        self._revisar_peligrosos(s.locales)
        self._git("add", "-A", "--", s.pathspec)
        privadas = self._privadas_en_indice()
        if privadas:
            self._git("reset", "-q", "--", *privadas)
        p = self._git("commit", "-m", mensaje, comprobar=False)
        if p.returncode != 0 and "nothing to commit" not in (p.stdout + p.stderr).lower():
            raise GitError(traducir_error(p.stderr + p.stdout))

    def _stat(self, s: Situacion) -> str:
        local = self._git("diff", "--stat", "HEAD", "--", s.pathspec, comprobar=False).stdout.strip()
        remoto = self._git("diff", "--stat", "HEAD...@{u}", comprobar=False).stdout.strip()
        return (f"Tus cambios locales (ficheros ya rastreados):\n{local or '  (ninguno)'}\n\n"
                f"Cambios en GitHub:\n{remoto or '  (ninguno)'}")

    def sincronizar(self, asignatura: str | None, mensaje: str | None,
                    integrar: bool = False, simular: bool = False) -> InformeSync:
        s = self.analizar(asignatura, tolerante=False)
        etiqueta = f"[{asignatura}]" if asignatura else "[sync]"
        texto = mensaje or f"actualiza desde {socket.gethostname()} ({datetime.now():%Y-%m-%d %H:%M})"
        commit = f"{etiqueta}: {texto}"
        nota = ["(simulación: no he tocado nada)"] if simular else []

        if not s.hay_local and not s.hay_remoto:
            return InformeSync("actualizado", ["Todo está actualizado."], simulado=simular)

        if s.hay_remoto and not s.hay_local:
            if simular:
                return InformeSync("descargado", [f"Descargaría {s.atrasados} commit(s) de GitHub."] + nota, simulado=True)
            self._git("pull", "--ff-only")
            return InformeSync("descargado", [f"Archivos descargados desde clase/casa ({s.atrasados} commit(s))."])

        if s.hay_local and not s.hay_remoto:
            if simular:
                return InformeSync("subido", [f"Subiría {len(s.locales)} cambio(s) con el mensaje «{commit}»."] + nota, simulado=True)
            self._guardar(s, commit)
            self._git("push")
            return InformeSync("subido", [f"Subido a GitHub: «{commit}»."])

        # Hay AMBOS: cambios locales y cambios en GitHub
        if not integrar:
            return InformeSync(
                "pendiente",
                ["No hago nada automático: tienes cambios sin subir Y hay cambios nuevos en GitHub.",
                 "Si quieres que los una (guarda lo tuyo y hace pull --rebase; si hay conflicto lo deshace): "
                 "dam sync --integrar"],
                detalle=self._stat(s), simulado=simular,
            )
        if simular:
            return InformeSync("integrado", ["Guardaría lo tuyo, haría pull --rebase y subiría."] + nota, simulado=True)
        self._guardar(s, commit)
        p = self._git("pull", "--rebase", "--autostash", comprobar=False)
        if p.returncode != 0:
            salida = p.stdout + p.stderr
            self._git("rebase", "--abort", comprobar=False)
            if "conflict" in salida.lower():
                raise GitError(
                    "Conflicto real al unir tus cambios con los de GitHub. He deshecho la unión: "
                    "tus cambios siguen en tu último commit local y no se ha perdido nada. "
                    "Resuélvelo a mano (git pull --rebase) o guarda una copia antes de seguir."
                )
            raise GitError(traducir_error(salida))
        self._git("push")
        return InformeSync("integrado", ["Cambios unidos con los de GitHub y subidos."])
