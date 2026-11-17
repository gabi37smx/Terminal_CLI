"""instalar-hook: revisa claves en cada «git commit» sin acordarte (hook pre-commit de git).

El hook ejecuta «mochila scan-secrets --staged». Con --revisor, además pasa lo que va en el commit
por el agente revisor de OpenCode (scripts/revisar.sh) si el commit lleva código: si dice
«VEREDICTO: CAMBIAR», el commit se cancela; si no se puede revisar (sin red, sin opencode...), avisa
y deja seguir. Lleva una marca para reconocer que es de mochila: nunca pisa un hook ajeno (salvo
--forzar) ni borra uno que no sea suyo.
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
elif ! mochila scan-secrets --staged; then
  echo "" >&2
  echo "✘ Commit cancelado: hay claves a la vista. Quítalas (y cámbialas si ya se subieron)." >&2
  echo "  Si es un falso aviso: añade mochila:ignore en esa línea, o usa git commit --no-verify." >&2
  exit 1
fi
"""

MARCA_REVISOR = "# mochila-hook: revisor"
# Qué cuenta como código: lo que cambia cómo funciona la herramienta o el agente (no la documentación)
CODIGO = r"\.(py|sh|ps1|cmd|json|jsonc|toml|ya?ml)$|^\.opencode/"
SCRIPT_REVISOR = f"""
{MARCA_REVISOR} (el agente revisor de OpenCode mira cada commit que lleve código)
if [ -n "$MOCHILA_SIN_REVISOR" ]; then
  echo "mochila: MOCHILA_SIN_REVISOR está puesto: esta vez no paso el revisor." >&2
  exit 0
fi
if [ ! -f scripts/revisar.sh ]; then
  exit 0
fi
if ! git diff --cached --name-only | grep -Eq '{CODIGO}'; then
  exit 0
fi
bash scripts/revisar.sh
estado=$?
if [ "$estado" -eq 1 ]; then
  echo "" >&2
  echo "✘ Commit cancelado: el revisor pide cambios. Lee lo que dice: lo que sea cierto, arréglalo y vuelve a hacer git add." >&2
  echo "  Si el revisor se equivoca, salta solo el revisor esta vez con MOCHILA_SIN_REVISOR=1 (mira el README)" >&2
  echo "  y apunta en docs/prompts.md en qué se equivocó." >&2
  exit 1
elif [ "$estado" -ne 0 ]; then
  echo "(aviso) No se ha podido pasar el revisor: el commit sigue. Revísalo luego con: bash scripts/revisar.sh" >&2
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


def instalar(repo: Path, forzar: bool = False, revisor: bool = False) -> str:
    destino = _ruta_del_hook(repo)
    if destino.exists() and not _es_nuestro(destino) and not forzar:
        raise TareasError(
            f"Ya hay un hook pre-commit que no es de mochila ({destino}). No lo piso: "
            "usa --forzar si quieres reemplazarlo."
        )
    raiz = Path(_git(repo, "rev-parse", "--show-toplevel").stdout.strip() or repo)
    if revisor and not (raiz / "scripts" / "revisar.sh").is_file():
        raise TareasError(
            f"«{repo}» no tiene scripts/revisar.sh: el revisor solo se puede poner en un proyecto que lo tenga."
        )
    destino.parent.mkdir(parents=True, exist_ok=True)
    texto = SCRIPT + (SCRIPT_REVISOR if revisor else "")
    destino.write_text(texto, encoding="utf-8", newline="\n")  # LF: el hook lo ejecuta sh, también en Windows
    destino.chmod(destino.stat().st_mode | 0o111)
    mensaje = f"Hook instalado: {destino}\nA partir de ahora cada git commit ejecuta mochila scan-secrets --staged."
    if revisor:
        mensaje += ("\nY si el commit lleva código, el agente revisor lo mira antes (bash scripts/revisar.sh): "
                    "si pide cambios, el commit se cancela.")
    return mensaje


def quitar(repo: Path) -> str:
    destino = _ruta_del_hook(repo)
    if not destino.exists():
        return "No hay ningún hook pre-commit: nada que quitar."
    if not _es_nuestro(destino):
        raise TareasError(f"El hook pre-commit de «{repo}» no es de mochila: no lo toco.")
    destino.unlink()
    return "Hook quitado."
