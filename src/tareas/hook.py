"""instalar-hook: revisa claves en cada «git commit» sin acordarte (hook pre-commit de git).

El hook solo ejecuta «mochila scan-secrets --staged». Lleva una marca para reconocer que es de mochila:
nunca pisa un hook ajeno (salvo --forzar) ni borra uno que no sea suyo.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .errores import GitError, TareasError

MARCA = "# mochila-hook: scan-secrets"
MARCA_ANTIGUA = "# dam-hook: scan-secrets"  # el de antes de llamarse mochila: también es nuestro
SCRIPT = f"""#!/bin/sh
{MARCA} (lo instala «mochila instalar-hook»; se quita con «mochila instalar-hook --quitar»)
if ! command -v mochila >/dev/null 2>&1; then
  echo "mochila: no encuentro el comando mochila; me salto la revisión de claves." >&2
  exit 0
fi
if ! mochila scan-secrets --staged; then
  echo "" >&2
  echo "✘ Commit cancelado: hay claves a la vista. Quítalas (y cámbialas si ya se subieron)." >&2
  echo "  Si es un falso aviso: añade mochila:ignore en esa línea, o usa git commit --no-verify." >&2
  exit 1
fi
"""


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    entorno = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "LC_ALL": "C"}
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, encoding="utf-8",
                              errors="replace", stdin=subprocess.DEVNULL, env=entorno)
    except FileNotFoundError:
        raise GitError("No encuentro git. Instálalo: winget install --id Git.Git -e") from None


def _ruta_del_hook(repo: Path) -> Path:
    """Dónde guarda git los hooks de este repositorio (respeta core.hooksPath y los worktrees)."""
    proceso = _git(repo, "rev-parse", "--git-path", "hooks")
    if proceso.returncode != 0 or not proceso.stdout.strip():
        raise TareasError(f"«{repo}» no es un repositorio git.")
    carpeta = Path(proceso.stdout.strip())
    return (carpeta if carpeta.is_absolute() else repo / carpeta) / "pre-commit"


def _es_nuestro(destino: Path) -> bool:
    texto = destino.read_text(encoding="utf-8", errors="replace")
    return MARCA in texto or MARCA_ANTIGUA in texto


def instalar(repo: Path, forzar: bool = False) -> str:
    destino = _ruta_del_hook(repo)
    if destino.exists() and not _es_nuestro(destino) and not forzar:
        raise TareasError(
            f"Ya hay un hook pre-commit que no es de mochila ({destino}). No lo piso: "
            "usa --forzar si quieres reemplazarlo."
        )
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(SCRIPT, encoding="utf-8", newline="\n")  # LF: el hook lo ejecuta sh, también en Windows
    destino.chmod(destino.stat().st_mode | 0o111)
    return f"Hook instalado: {destino}\nA partir de ahora cada git commit ejecuta mochila scan-secrets --staged."


def quitar(repo: Path) -> str:
    destino = _ruta_del_hook(repo)
    if not destino.exists():
        return "No hay ningún hook pre-commit: nada que quitar."
    if not _es_nuestro(destino):
        raise TareasError(f"El hook pre-commit de «{repo}» no es de mochila: no lo toco.")
    destino.unlink()
    return "Hook quitado."
