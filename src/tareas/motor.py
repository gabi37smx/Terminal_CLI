"""Motor: elige los ficheros que cumplen el filtro y se los pasa a la acción."""

from __future__ import annotations

import difflib
import re
import time
from pathlib import Path

from .acciones import Accion, Resultado
from .errores import TareasError
from .ia import ProveedorIA


def describir_filtro(filtro: dict) -> str:
    """{"extensiones": [".jpg", ".png"]} -> 'solo .jpg, .png'. Para explicar por qué no entra un fichero."""
    partes = []
    if filtro.get("extensiones"):
        partes.append("solo " + ", ".join(filtro["extensiones"]))
    if "patron" in filtro:
        partes.append(f"nombre que encaje con {filtro['patron']}")
    if "mas_antiguo_que_dias" in filtro:
        partes.append(f"de más de {filtro['mas_antiguo_que_dias']} días")
    if "mayor_que_mb" in filtro:
        partes.append(f"de más de {filtro['mayor_que_mb']} MB")
    return "; ".join(partes) or "sin filtro"


def sugerir(nombre: str, opciones: list[str]) -> str | None:
    """La opción que seguramente querías: «clasificar» -> «clasificar-asignatura». Si no está claro, None."""
    empiezan = [o for o in opciones if o.startswith(nombre)]
    if len(empiezan) == 1:
        return empiezan[0]
    parecidas = difflib.get_close_matches(nombre, opciones, n=1, cutoff=0.75)
    return parecidas[0] if parecidas else None


class Motor:
    def __init__(self, acciones: list[dict], proveedor: ProveedorIA | None = None):
        self.acciones = {a["nombre"]: Accion.desde_config(a) for a in acciones}
        self.proveedor = proveedor  # solo lo usan las acciones con IA; lo pone cli.py si hace falta

    @staticmethod
    def seleccionar(carpeta: Path, filtro: dict) -> list[Path]:
        """Ficheros (no subcarpetas) de `carpeta` que cumplen TODAS las condiciones del filtro."""
        assert carpeta.is_dir(), f"seleccionar espera una carpeta existente, no «{carpeta}»"
        exts = {e.lower() for e in filtro.get("extensiones", [])}
        patron = re.compile(filtro["patron"]) if "patron" in filtro else None
        dias = filtro.get("mas_antiguo_que_dias")
        mb = filtro.get("mayor_que_mb")
        ahora = time.time()
        elegidos = []
        for f in sorted(carpeta.iterdir(), key=lambda p: p.name.lower()):
            try:
                if not f.is_file():
                    continue
                if exts and f.suffix.lower() not in exts:
                    continue
                if patron and not patron.search(f.name):
                    continue
                datos = f.stat()
            except OSError:
                continue  # enlace roto o sin permisos
            if dias and ahora - datos.st_mtime < dias * 86400:
                continue
            if mb and datos.st_size < mb * 1024 * 1024:
                continue
            elegidos.append(f)
        return elegidos

    def preparar(self, nombre: str, carpeta: Path | None) -> tuple[Accion, list[Path]]:
        """Resuelve la acción y los ficheros SIN tocar nada (sirve para pedir confirmación)."""
        accion = self.acciones.get(nombre)
        if accion is None:
            parecida = sugerir(nombre, list(self.acciones))
            pista = f" ¿Querías decir «{parecida}»?" if parecida else ""
            raise TareasError(f"No hay ninguna acción «{nombre}».{pista} Mira la lista con: mochila acciones")
        origen = carpeta if carpeta is not None else accion.config.get("origen")
        if origen is None:
            raise TareasError("Indica una CARPETA o define «origen» en la acción")
        origen = Path(origen).expanduser()
        filtro = accion.config.get("filtro", {})
        if origen.is_file():  # un fichero suelto: solo ese, y solo si cumple el filtro (borrar no se salta nada)
            ficheros = [f for f in self.seleccionar(origen.parent, filtro) if f.name == origen.name]
            if not ficheros:
                raise TareasError(f"«{origen.name}» no cumple el filtro de «{nombre}» ({describir_filtro(filtro)}): "
                                  "no hago nada")
        elif origen.is_dir():
            ficheros = self.seleccionar(origen, filtro)
        elif carpeta is None:
            # «mochila ejecutar ordenar» sin carpeta: el origen de la acción es de ejemplo y aquí no está
            raise TareasError(
                f"Dime qué carpeta o fichero: mochila ejecutar {nombre} CARPETA (un punto, «.», es la carpeta "
                f"en la que estás). Sin ella uso la de la acción, {origen}, y no existe."
            )
        else:
            raise TareasError(f"{origen} no existe (ni como carpeta ni como fichero)")
        if accion.necesita_ia:
            accion.proveedor = self.proveedor
        return accion, ficheros

    def ejecutar(self, nombre: str, carpeta: Path | None, simular: bool) -> list[Resultado]:
        accion, ficheros = self.preparar(nombre, carpeta)
        return accion.ejecutar(ficheros, simular)
