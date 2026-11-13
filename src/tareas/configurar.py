"""dam configurar: pone TUS asignaturas en acciones.json (como adduser, que pregunta y configura).

Aquí solo está la lógica, sin preguntas por pantalla (esas están en cli.py), para poder probarla:
- `aplicar` cambia las acciones «ordenar» y «clasificar» de una plantilla por tus asignaturas.
- `guardar` valida el resultado entero y lo escribe, con copia del fichero anterior.
- `carpetas_que_faltan` / `crear_carpetas` preparan asignaturas/ en tu almacén.
- La ruta del almacén pasa a ser la de tu ciclo (~/ASIR-almacen...) si era una de las que pone dam.
"""

from __future__ import annotations

import copy
import json
import re
from datetime import datetime
from pathlib import Path

from . import ciclos, config, almacen_nuevo
from .errores import ConfigError

OTROS = "otros"  # categoría de «clasificar» para lo que no es de ninguna asignatura
_CURSO_EN_TEXTO = re.compile(r"\b(de?l? )?(?:[12]º de )?(?:SMX|DAM|DAW|ASIR)\b|\btu curso\b")


def perfil(datos: dict) -> dict | None:
    """Lo que guardó la última vez dam configurar: {"ciclo": "dam", "cursos": [1]} (o None)."""
    p = datos.get("perfil")
    return p if isinstance(p, dict) else None


def asignaturas_actuales(datos: dict) -> dict[str, list[str]]:
    """Las carpetas de la primera acción «ordenar» (tus asignaturas de ahora, con sus palabras clave)."""
    for accion in datos.get("acciones", []):
        if isinstance(accion, dict) and accion.get("tipo") == "ordenar" and isinstance(accion.get("carpetas"), dict):
            return {k: list(v) for k, v in accion["carpetas"].items()}
    return {}


def palabras_al_dia(asignaturas: dict[str, list[str]]) -> dict[str, list[str]]:
    """Las asignaturas de la última vez con las palabras clave del vocabulario de AHORA.

    Si ciclos.py ha aprendido palabras nuevas desde entonces, se añaden; las que pusiste tú se quedan.
    Las asignaturas tuyas (las que no están en el vocabulario) no cambian.
    """
    resultado = {}
    for nombre, palabras in asignaturas.items():
        vocabulario = list(ciclos.ASIGNATURAS[nombre].palabras) if nombre in ciclos.ASIGNATURAS else []
        resultado[nombre] = vocabulario + [p for p in palabras if p not in vocabulario]
    return resultado


def _cambiar_curso(texto: str, etiqueta: str) -> str:
    """'...por asignatura del DAM...' -> '...por asignatura de 1º de SMX...'."""
    return _CURSO_EN_TEXTO.sub(lambda m: (f"de {etiqueta}" if m.group(1) else etiqueta), texto)


def instrucciones(etiqueta: str, asignaturas: dict[str, list[str]]) -> str:
    """Lo que se le pide al modelo en «clasificar»: cada asignatura con su nombre y unas pistas."""
    partes = []
    for nombre, palabras in asignaturas.items():
        largo = ciclos.ASIGNATURAS[nombre].castellano if nombre in ciclos.ASIGNATURAS else ""
        pistas = ", ".join(palabras[:5])
        partes.append(f"«{nombre}» ({largo}: {pistas})" if largo else f"«{nombre}» ({pistas})")
    return (
        f"Son apuntes de {etiqueta}, en castellano o en valenciano. Las asignaturas son: "
        + "; ".join(partes)
        + f". Si no es de ninguna asignatura (un calendario, una factura...), responde «{OTROS}»."
    )


def aplicar(plantilla: dict, ciclo: str, cursos: list[int], asignaturas: dict[str, list[str]]) -> dict:
    """Copia de la plantilla con tus asignaturas. La plantilla no se toca.

    Si una acción ya tiene justo esas asignaturas, se queda como está (con lo que ya hubieras afinado).
    """
    if not asignaturas:
        raise ConfigError("Hace falta al menos una asignatura")
    datos = copy.deepcopy(plantilla)
    etiqueta = ciclos.etiqueta(ciclo, cursos)
    nombres = list(asignaturas)
    categorias = nombres + ([] if OTROS in asignaturas else [OTROS])
    for accion in datos.get("acciones", []):
        if not isinstance(accion, dict):
            continue
        if accion.get("tipo") == "ordenar" and accion.get("carpetas") != asignaturas:
            accion["carpetas"] = {k: list(v) for k, v in asignaturas.items()}
            extensiones = ciclos.por_extension(nombres)
            if extensiones:
                accion["por_extension"] = extensiones
            else:
                accion.pop("por_extension", None)
            accion["descripcion"] = _cambiar_curso(accion.get("descripcion", ""), etiqueta)
        elif accion.get("tipo") == "clasificar" and accion.get("categorias") != categorias:
            accion["categorias"] = categorias
            accion["instrucciones"] = instrucciones(etiqueta, asignaturas)
            accion["descripcion"] = _cambiar_curso(accion.get("descripcion", ""), etiqueta)
    almacen = datos.get("almacen")
    if isinstance(almacen, dict) and isinstance(almacen.get("ruta"), str):
        almacen["ruta"] = almacen_nuevo.ruta_para(almacen["ruta"], ciclo)  # ~/DAM-almacen -> ~/ASIR-almacen
    datos["perfil"] = {"ciclo": ciclo, "cursos": sorted(set(cursos))}
    return datos


def guardar(datos: dict, destino: Path) -> Path | None:
    """Valida TODO y lo escribe en UTF-8. Si ya había un fichero, lo copia antes (devuelve la copia)."""
    config.validar_datos(datos, destino.name)
    copia = None
    if destino.exists():
        copia = destino.with_name(f"{destino.name}.antes-{datetime.now():%Y%m%d-%H%M%S}")
        copia.write_bytes(destino.read_bytes())
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return copia


def carpetas_que_faltan(base: Path, asignaturas: list[str]) -> list[str]:
    """Las asignaturas que todavía no tienen carpeta en asignaturas/ del almacén."""
    return [a for a in asignaturas if not (base / a).is_dir()]


def crear_carpetas(base: Path, asignaturas: list[str]) -> None:
    """Crea asignaturas/NOMBRE con un .gitkeep (git no sube carpetas vacías: así dam sync las lleva a GitHub)."""
    for nombre in asignaturas:
        carpeta = base / nombre
        carpeta.mkdir(parents=True, exist_ok=True)
        (carpeta / ".gitkeep").touch()
