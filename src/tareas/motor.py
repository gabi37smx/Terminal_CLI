"""Motor: elige los ficheros que cumplen el filtro y se los pasa a la acción."""

from __future__ import annotations

import re
import time
from pathlib import Path

from .acciones import Accion, Resultado
from .errores import TareasError


class Motor:
    def __init__(self, acciones: list[dict]):
        self.acciones = {a["nombre"]: Accion.desde_config(a) for a in acciones}

    @staticmethod
    def seleccionar(carpeta: Path, filtro: dict) -> list[Path]:
        """Ficheros (no subcarpetas) de `carpeta` que cumplen TODAS las condiciones del filtro."""
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
        if not origen.is_dir():
            raise TareasError(f"La carpeta {origen} no existe")
        return accion, self.seleccionar(origen, accion.config.get("filtro", {}))

    def ejecutar(self, nombre: str, carpeta: Path | None, simular: bool) -> list[Resultado]:
        accion, ficheros = self.preparar(nombre, carpeta)
        return accion.ejecutar(ficheros, simular)
