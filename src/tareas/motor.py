"""Motor: elige los ficheros que cumplen el filtro y se los pasa a la acción."""

from __future__ import annotations

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
            raise TareasError(
                f"No hay ninguna acción «{nombre}». Mira la lista con: dam acciones"
            )
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
        else:
            raise TareasError(f"{origen} no existe (ni como carpeta ni como fichero)")
        if accion.necesita_ia:
            accion.proveedor = self.proveedor
        return accion, ficheros

    def ejecutar(self, nombre: str, carpeta: Path | None, simular: bool) -> list[Resultado]:
        accion, ficheros = self.preparar(nombre, carpeta)
        return accion.ejecutar(ficheros, simular)
