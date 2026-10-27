"""Carga y validación de acciones.json: aquí se comprueba TODO antes de tocar un solo fichero."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from .errores import AccionNoValida, ConfigError

NOMBRE_FICHERO = "acciones.json"
TIPOS = {"mover", "copiar", "renombrar", "borrar", "ordenar", "convertir"}
OBLIGATORIOS = ("nombre", "descripcion", "tipo")
POR_TIPO = {
    "mover": "destino",
    "copiar": "destino",
    "renombrar": "plantilla",
    "ordenar": "carpetas",
}
FILTROS = {"extensiones", "patron", "mas_antiguo_que_dias", "mayor_que_mb"}
NOMBRE_VALIDO = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PROHIBIDOS_EN_NOMBRES = '<>:"/\\|?*'  # Windows no admite estos caracteres en nombres


def sitios_de_busqueda() -> list[Path]:
    """Dónde se busca acciones.json si no se pasa --config."""
    return [Path.cwd() / NOMBRE_FICHERO, Path.home() / ".config" / "dam" / NOMBRE_FICHERO]


def buscar(ruta: Path | None) -> Path:
    """Devuelve la ruta del fichero de configuración o lanza ConfigError."""
    if ruta is not None:
        ruta = ruta.expanduser()
        if not ruta.is_file():
            raise ConfigError(f"No encuentro {ruta}")
        return ruta
    sitios = sitios_de_busqueda()
    for candidato in sitios:
        if candidato.is_file():
            return candidato
    raise ConfigError(
        f"No encuentro {NOMBRE_FICHERO}. Busqué en: {', '.join(str(s) for s in sitios)}. "
        "Créalo o usa --config RUTA"
    )


def _leer_json(ruta: Path) -> dict:
    try:
        # utf-8-sig tolera el BOM que PowerShell 5 añade al guardar en UTF-8
        datos = json.loads(ruta.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise ConfigError(
            f"{ruta.name} no es JSON válido: línea {e.lineno}, columna {e.colno} ({e.msg})"
        ) from None
    except UnicodeDecodeError:
        raise ConfigError(f"{ruta.name} no está guardado en UTF-8") from None
    except OSError as e:
        raise ConfigError(f"No puedo leer {ruta}: {e.strerror}") from None
    if not isinstance(datos, dict):
        raise ConfigError(f"{ruta.name}: la raíz debe ser un objeto con «version» y «acciones»")
    return datos


def _texto(valor: object) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


def _validar_filtro(nombre: str, filtro: object) -> None:
    if not isinstance(filtro, dict):
        raise AccionNoValida(nombre, "filtro", "debe ser un objeto { ... }")
    for clave in filtro:
        if clave not in FILTROS:
            raise AccionNoValida(
                nombre, f"filtro.{clave}", f"no existe; usa uno de: {', '.join(sorted(FILTROS))}"
            )
    exts = filtro.get("extensiones")
    if "extensiones" in filtro and not (
        isinstance(exts, list)
        and exts
        and all(isinstance(e, str) and e.startswith(".") for e in exts)
    ):
        raise AccionNoValida(
            nombre, "filtro.extensiones", 'debe ser una lista de textos con punto, como [".pdf"]'
        )
    if "patron" in filtro:
        try:
            re.compile(filtro["patron"])
        except (re.error, TypeError) as e:
            raise AccionNoValida(nombre, "filtro.patron", f"expresión regular rota: {e}") from None
    for clave in ("mas_antiguo_que_dias", "mayor_que_mb"):
        if clave in filtro:
            v = filtro[clave]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
                raise AccionNoValida(nombre, f"filtro.{clave}", "debe ser un número mayor que 0")


def _validar_plantilla(nombre: str, plantilla: str) -> None:
    try:
        ejemplo = plantilla.format(
            fecha=datetime(2026, 1, 2), n=1, ext=".jpg", nombre="IMG_1"
        )
    except (KeyError, IndexError, ValueError, AttributeError, TypeError) as e:
        raise AccionNoValida(
            nombre,
            "plantilla",
            f"no es válida ({type(e).__name__}: {e}); huecos permitidos: "
            "{fecha:%Y-%m-%d}, {n:03}, {ext}, {nombre}",
        ) from None
    if any(c in ejemplo for c in PROHIBIDOS_EN_NOMBRES):
        raise AccionNoValida(
            nombre, "plantilla", f"genera nombres con caracteres prohibidos ({PROHIBIDOS_EN_NOMBRES})"
        )


def _validar_ordenar(nombre: str, accion: dict) -> None:
    carpetas = accion["carpetas"]
    if not isinstance(carpetas, dict) or not carpetas:
        raise AccionNoValida(
            nombre, "carpetas", 'debe ser un objeto {"asignatura": ["palabra", ...]}'
        )
    for carpeta, claves in carpetas.items():
        if not _texto(carpeta) or any(c in carpeta for c in PROHIBIDOS_EN_NOMBRES):
            raise AccionNoValida(nombre, f"carpetas.{carpeta}", "nombre de carpeta no válido")
        if not (isinstance(claves, list) and claves and all(_texto(c) for c in claves)):
            raise AccionNoValida(
                nombre, f"carpetas.{carpeta}", "debe ser una lista de palabras clave (textos)"
            )
    por_ext = accion.get("por_extension", {})
    if not isinstance(por_ext, dict):
        raise AccionNoValida(nombre, "por_extension", 'debe ser un objeto {".sql": "carpeta"}')
    for ext, carpeta in por_ext.items():
        if not ext.startswith("."):
            raise AccionNoValida(nombre, f"por_extension.{ext}", "la extensión debe empezar por punto")
        if carpeta not in carpetas:
            raise AccionNoValida(
                nombre, f"por_extension.{ext}", f"«{carpeta}» no está en «carpetas»"
            )


def _validar_accion(a: object, i: int, vistos: set[str]) -> None:
    if not isinstance(a, dict):
        raise AccionNoValida(f"nº {i}", "(acción)", "debe ser un objeto { ... }")
    nombre = a["nombre"] if _texto(a.get("nombre")) else f"nº {i}"
    for campo in OBLIGATORIOS:
        if not _texto(a.get(campo)):
            raise AccionNoValida(nombre, campo, "es obligatorio (un texto)")
    if not NOMBRE_VALIDO.match(nombre):
        raise AccionNoValida(
            nombre, "nombre", "usa minúsculas, números y guiones, sin espacios (ej.: ordenar-apuntes)"
        )
    if nombre in vistos:
        raise AccionNoValida(nombre, "nombre", "está repetido")
    vistos.add(nombre)

    tipo = a["tipo"]
    if tipo not in TIPOS:
        raise AccionNoValida(
            nombre, "tipo", f"«{tipo}» no existe; usa uno de: {', '.join(sorted(TIPOS))}"
        )
    extra = POR_TIPO.get(tipo)
    if extra and not a.get(extra):
        raise AccionNoValida(nombre, extra, f"es obligatorio en acciones de tipo {tipo}")
    if "origen" in a and not _texto(a["origen"]):
        raise AccionNoValida(nombre, "origen", "debe ser un texto (una ruta)")
    if "destino" in a and not _texto(a["destino"]):
        raise AccionNoValida(nombre, "destino", "debe ser un texto (una ruta)")
    if "confirmar" in a and not isinstance(a["confirmar"], bool):
        raise AccionNoValida(nombre, "confirmar", "debe ser true o false")
    if "filtro" in a:
        _validar_filtro(nombre, a["filtro"])
    if tipo == "borrar" and not a.get("filtro"):
        raise AccionNoValida(
            nombre, "filtro", "es obligatorio en acciones de tipo borrar (sin filtro borraría todo)"
        )
    if tipo == "renombrar":
        _validar_plantilla(nombre, a["plantilla"])
    if tipo == "ordenar":
        _validar_ordenar(nombre, a)
    if tipo == "convertir" and "calidad" in a:
        c = a["calidad"]
        if isinstance(c, bool) or not isinstance(c, int) or not 1 <= c <= 100:
            raise AccionNoValida(nombre, "calidad", "debe ser un entero entre 1 y 100")


def _validar_almacen(almacen: object) -> None:
    if almacen is None:
        return
    if not isinstance(almacen, dict) or not _texto(almacen.get("ruta")):
        raise ConfigError("«almacen» debe ser un objeto con «ruta»: {\"ruta\": \"~/DAM-almacen\"}")
    if "asignaturas" in almacen and not _texto(almacen["asignaturas"]):
        raise ConfigError("«almacen.asignaturas» debe ser el nombre de una carpeta (texto)")


def leer(ruta: Path) -> dict:
    """Lee y valida TODO el fichero. Devuelve el diccionario completo."""
    datos = _leer_json(ruta)
    if datos.get("version") != 1:
        raise ConfigError(
            f"{ruta.name}: falta «version»: 1 (o es una versión que no conozco: {datos.get('version')!r})"
        )
    acciones = datos.get("acciones")
    if not isinstance(acciones, list) or not acciones:
        raise ConfigError("Falta la lista «acciones» o está vacía")
    vistos: set[str] = set()
    for i, accion in enumerate(acciones, start=1):
        _validar_accion(accion, i, vistos)
    _validar_almacen(datos.get("almacen"))
    return datos


def cargar(ruta: Path) -> list[dict]:
    """Lista de acciones ya validadas."""
    return leer(ruta)["acciones"]


def almacen(ruta: Path) -> dict | None:
    """Solo la sección «almacen» (para status/sync no hace falta que las acciones estén perfectas)."""
    datos = _leer_json(ruta)
    _validar_almacen(datos.get("almacen"))
    return datos.get("almacen")
