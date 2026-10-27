"""Lectura y validación del fichero de configuración tareas.toml."""

import tomllib
from pathlib import Path
from typing import Any

TIPOS_CONOCIDOS = ("asignaturas", "limpiar", "convertir")
NOMBRE_ESPERADO = "tareas.toml"


class ErrorConfig(Exception):
    """La configuración no es válida."""


def ruta_de_configuracion(solicitada: str | None = None) -> Path:
    """Devuelve la ruta del tareas.toml: la pedida, la del proyecto o la de usuario."""
    if solicitada:
        return Path(solicitada).expanduser()
    local = Path.cwd() / NOMBRE_ESPERADO
    if local.exists():
        return local
    return Path.home() / ".config" / "tareas" / NOMBRE_ESPERADO


def leer_configuracion(ruta: Path) -> dict[str, Any]:
    """Carga el TOML y devuelve el diccionario con las acciones validadas."""
    if not ruta.exists():
        raise ErrorConfig(f"no existe el fichero de configuración: {ruta}")
    try:
        with ruta.open("rb") as fichero:
            datos = tomllib.load(fichero)
    except tomllib.TOMLDecodeError as error:
        raise ErrorConfig(f"el TOML no se puede leer: {error}") from error
    except OSError as error:
        raise ErrorConfig(f"no se puede leer {ruta}: {error}") from error

    acciones = datos.get("acciones")
    if not isinstance(acciones, dict) or not acciones:
        raise ErrorConfig("falta la sección [acciones] o está vacía")

    for nombre, accion in acciones.items():
        _validar_accion(nombre, accion)

    return {"acciones": acciones}


def _validar_accion(nombre: str, accion: Any) -> None:
    """Comprueba que una acción tiene las claves obligatorias y valores sanos."""
    if not nombre.replace("-", "").isalnum() or nombre != nombre.lower():
        raise ErrorConfig(
            f"el nombre de acción '{nombre}' debe ir en minúsculas, sin espacios ni acentos"
        )
    if not isinstance(accion, dict):
        raise ErrorConfig(f"la acción '{nombre}' debe ser una tabla con claves")
    for clave in ("descripcion", "tipo", "origen"):
        if clave not in accion:
            raise ErrorConfig(f"la acción '{nombre}' no tiene la clave '{clave}'")
    if accion["tipo"] not in TIPOS_CONOCIDOS:
        raise ErrorConfig(
            f"la acción '{nombre}' tiene un tipo desconocido: '{accion['tipo']}' "
            f"(válidos: {', '.join(TIPOS_CONOCIDOS)})"
        )
    if not str(accion["origen"]).strip():
        raise ErrorConfig(f"la acción '{nombre}' tiene un origen vacío")
    if accion["tipo"] == "asignaturas":
        _validar_carpetas(nombre, accion)
    if accion["tipo"] == "limpiar":
        if "dias" not in accion:
            raise ErrorConfig(f"la acción '{nombre}' no tiene la clave 'dias'")
        if not isinstance(accion["dias"], int) or accion["dias"] <= 0:
            raise ErrorConfig(f"la acción '{nombre}' tiene un 'dias' que no es un entero positivo")


def _validar_carpetas(nombre: str, accion: dict[str, Any]) -> None:
    """Comprueba que las carpetas de asignatura son un dict de listas de palabras."""
    carpetas = accion.get("carpetas")
    if not isinstance(carpetas, dict) or not carpetas:
        raise ErrorConfig(f"la acción '{nombre}' no tiene la tabla [acciones.{nombre}.carpetas]")
    for carpeta, palabras in carpetas.items():
        if not isinstance(palabras, list) or not palabras:
            raise ErrorConfig(
                f"la carpeta '{carpeta}' de '{nombre}' debe ser una lista de palabras clave"
            )
        if not all(isinstance(palabra, str) and palabra.strip() for palabra in palabras):
            raise ErrorConfig(
                f"la carpeta '{carpeta}' de '{nombre}' tiene palabras que no son texto"
            )
