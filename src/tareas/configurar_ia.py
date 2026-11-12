"""dam configurar-ia: elige con qué modelo trabajan las acciones con IA.

Aquí solo está la lógica, sin preguntas por pantalla (esas están en cli.py), para poder probarla:
- `modelos_gratis` pregunta a OpenCode qué modelos gratis hay hoy y los ordena (los recomendados, primero).
- `nota` dice qué hace cada uno con lo que le mandas.
- `ruta_opencode_global` / `modelo_global` / `poner_modelo_global` cambian el modelo por defecto de
  OpenCode en tu configuración global (~/.config/opencode/opencode.json), con copia del fichero anterior.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from .errores import ConfigError
from .ia import RECOMENDADOS

ESQUEMA = "https://opencode.ai/config.json"

# Lo que dice opencode.ai/docs/zen (12-nov-2026) de cada modelo gratis. Los que no estén aquí: mirar allí.
NOTAS = {
    "deepseek-v4.1-flash-free": "no guarda lo que le mandas ni entrena con ello",
    "glm-5.3-flash-free": "no guarda lo que le mandas ni entrena con ello",
    "minimax-m3.1-flash-free": "no guarda lo que le mandas ni entrena con ello",
    "longcat-2.5-free": "no guarda lo que le mandas ni entrena con ello (servidores en China)",
    "beam-free": "no entrena con ello, pero lo guarda 30 días",
    "big-pickle": "puede usar lo que le mandas para mejorar el modelo",
    "iceman-free": "guarda lo que le mandas y lo usa para mejorar el modelo",
    "flint-40b-free": "puede usarlo para mejorar el modelo y lo guarda 30 días",
    "mimo-v2.6-flash-free": "puede usar lo que le mandas para mejorar el modelo",
    "inkling-2-small-free": "guarda lo que le mandas y puede entrenar con ello (no está en la UE)",
    "nemotron-3-ultra-free": "solo de prueba: no le mandes datos personales",
    "nemotron-3.5-lightning-free": "solo de prueba: no le mandes datos personales",
    "nemotron-3.5-super-vl-free": "solo de prueba: no le mandes datos personales",
}


def nota(modelo: str) -> str:
    """Qué hace ese modelo con lo que le mandas (o dónde mirarlo)."""
    return NOTAS.get(modelo.split("/", 1)[-1], "mira sus condiciones en opencode.ai/docs/zen")


def ordenar(modelos: list[str]) -> list[str]:
    """Los recomendados primero (en su orden) y después el resto por orden alfabético, sin repetir."""
    unicos = sorted(set(modelos))
    primero = [m for m in RECOMENDADOS if m in unicos]
    return primero + [m for m in unicos if m not in primero]


def modelos_gratis(ejecutable: str, segundos: int = 60) -> list[str]:
    """Los modelos gratis de OpenCode hoy («opencode models opencode», los que acaban en -free)."""
    try:
        r = subprocess.run([ejecutable, "models", "opencode"], capture_output=True, timeout=segundos,
                           stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise ConfigError(f"OpenCode no ha dado la lista de modelos en {segundos} s (¿tienes internet?)") from None
    except OSError as e:
        raise ConfigError(f"No he podido lanzar opencode ({e.strerror or e})") from None
    lineas = r.stdout.decode("utf-8", "replace").split()
    return ordenar([l for l in lineas if l.startswith("opencode/") and l.endswith("-free")])


def version(ejecutable: str) -> str:
    """La versión de opencode («1.18.35») o «?» si no la dice."""
    try:
        r = subprocess.run([ejecutable, "--version"], capture_output=True, timeout=30, stdin=subprocess.DEVNULL)
    except (subprocess.TimeoutExpired, OSError):
        return "?"
    return r.stdout.decode("utf-8", "replace").strip() or "?"


def _base_config() -> Path:
    """Donde OpenCode busca su configuración: $XDG_CONFIG_HOME o ~/.config (las pruebas la cambian)."""
    base = os.environ.get("XDG_CONFIG_HOME", "").strip()
    return Path(base) if base else Path.home() / ".config"


def ruta_opencode_global() -> Path:
    """La configuración global de OpenCode (también en Windows): ~/.config/opencode/opencode.json.

    Si no existe pero está opencode.jsonc (OpenCode lo crea solo la primera vez, con solo «$schema»),
    es esa. Si no hay ninguna, opencode.json.
    """
    carpeta = _base_config() / "opencode"
    jsonc = carpeta / "opencode.jsonc"
    return jsonc if jsonc.exists() and not (carpeta / "opencode.json").exists() else carpeta / "opencode.json"


def _leer(ruta: Path) -> dict:
    """Lee la configuración global. Si tiene comentarios o está rota, no la toco."""
    if not ruta.exists():
        return {}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise ConfigError(f"No entiendo {ruta} (¿tiene comentarios?): no la toco, cámbiala a mano") from None
    if not isinstance(datos, dict):
        raise ConfigError(f"{ruta} no es un objeto JSON: no la toco")
    return datos


def modelo_global(ruta: Path) -> str | None:
    """El modelo que usa OpenCode por defecto ahora (o None si no hay ninguno o no se puede leer)."""
    try:
        modelo = _leer(ruta).get("model")
    except ConfigError:
        return None
    return modelo if isinstance(modelo, str) and modelo else None


def poner_modelo_global(ruta: Path, modelo: str) -> Path | None:
    """Pone «model» y «small_model» de OpenCode en ese modelo. Lo demás de tu fichero no se toca.

    small_model también, porque OpenCode lo usa para los títulos de las sesiones y, si es el del
    centro, en casa falla. Si ya había fichero, lo copia antes (devuelve la copia).
    """
    datos = _leer(ruta)
    copia = None
    if ruta.exists():
        copia = ruta.with_name(f"{ruta.name}.antes-{datetime.now():%Y%m%d-%H%M%S}")
        copia.write_bytes(ruta.read_bytes())
    datos.setdefault("$schema", ESQUEMA)
    datos["model"] = modelo
    datos["small_model"] = modelo
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return copia
