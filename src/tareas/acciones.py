"""Acciones: una clase base y una subclase por tipo. El motor no sabe nada de tipos concretos."""

from __future__ import annotations

import os
import re
import shutil
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .errores import AccionNoValida


@dataclass
class Resultado:
    origen: Path
    destino: Path | None
    estado: str  # "hecho", "simulado", "saltado" o "error"
    nota: str = ""


def _clave(ruta: Path) -> str:
    """Windows no distingue mayúsculas: FOTO.JPG y foto.jpg son el mismo fichero."""
    return os.path.normcase(str(ruta))


def destino_libre(destino: Path, reservados: set[str] | None = None) -> Path:
    """Nunca sobrescribe: si existe (o ya lo ha reservado otro fichero de esta pasada,
    importante en simulación), prueba 'nombre (1).ext', 'nombre (2).ext'..."""
    if reservados is None:
        reservados = set()
    libre, n = destino, 1
    while libre.exists() or _clave(libre) in reservados:
        libre = destino.with_name(f"{destino.stem} ({n}){destino.suffix}")
        n += 1
    reservados.add(_clave(libre))
    return libre


class Accion(ABC):
    tipo = ""
    destructiva = False
    _registro: dict[str, type[Accion]] = {}

    def __init__(self, config: dict):
        self.nombre = config["nombre"]
        self.descripcion = config["descripcion"]
        self.config = config
        self._reservados: set[str] = set()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls.tipo:
            Accion._registro[cls.tipo] = cls  # cada subclase se apunta sola

    @staticmethod
    def desde_config(config: dict) -> Accion:
        """Fábrica: del diccionario del JSON a la clase que toca."""
        clase = Accion._registro.get(config["tipo"])
        if clase is None:
            raise AccionNoValida(config["nombre"], "tipo", "no hay ninguna clase para ese tipo")
        return clase(config)

    def ejecutar(self, ficheros: list[Path], simular: bool) -> list[Resultado]:
        self._reservados = set()
        resultados = []
        for n, fichero in enumerate(ficheros, start=1):
            try:
                resultados.append(self.aplicar(fichero, n, simular))
            except OSError as e:  # permiso denegado, fichero en uso (Windows)...
                resultados.append(Resultado(fichero, None, "error", e.strerror or str(e)))
        return resultados

    @abstractmethod
    def aplicar(self, fichero: Path, n: int, simular: bool) -> Resultado: ...

    def _carpeta_destino(self, fichero: Path) -> Path:
        destino = self.config.get("destino")
        return Path(destino).expanduser() if destino else fichero.parent


class Mover(Accion):
    tipo = "mover"

    def aplicar(self, fichero, n, simular):
        carpeta = self._carpeta_destino(fichero)
        destino = destino_libre(carpeta / fichero.name, self._reservados)
        if not simular:
            carpeta.mkdir(parents=True, exist_ok=True)
            shutil.move(fichero, destino)
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Copiar(Accion):
    tipo = "copiar"

    def aplicar(self, fichero, n, simular):
        carpeta = self._carpeta_destino(fichero)
        destino = destino_libre(carpeta / fichero.name, self._reservados)
        if not simular:
            carpeta.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fichero, destino)
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Renombrar(Accion):
    tipo = "renombrar"

    def aplicar(self, fichero, n, simular):
        fecha = datetime.fromtimestamp(fichero.stat().st_mtime)
        nuevo = self.config["plantilla"].format(
            fecha=fecha, n=n, ext=fichero.suffix.lower(), nombre=fichero.stem
        )
        if nuevo == fichero.name:
            return Resultado(fichero, None, "saltado", "ya tiene ese nombre")
        destino = destino_libre(fichero.with_name(nuevo), self._reservados)
        if not simular:
            fichero.rename(destino)
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Borrar(Accion):
    tipo = "borrar"
    destructiva = True

    def aplicar(self, fichero, n, simular):
        if not simular:
            fichero.unlink()
        return Resultado(fichero, None, "simulado" if simular else "hecho")


def _normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y solo palabras sueltas: 'Programación_Tema1.pdf' -> 'programacion tema1 pdf'."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(re.findall(r"[a-z0-9]+", sin_tildes.lower()))


def _texto_pdf(ruta: Path) -> str:
    """Texto de las 3 primeras y 3 últimas páginas (si no se puede leer, no ayuda y ya)."""
    try:
        from pypdf import PdfReader

        paginas = list(PdfReader(str(ruta)).pages)
        elegidas = paginas[:3] + paginas[-3:] if len(paginas) > 6 else paginas
        return " ".join((p.extract_text() or "") for p in elegidas)[:20000]
    except Exception:  # PDF roto, cifrado, etc.: simplemente no sirve para clasificar
        return ""


class Ordenar(Accion):
    """Reparte ficheros en carpetas por asignatura usando palabras clave (palabras COMPLETAS)."""

    tipo = "ordenar"

    def __init__(self, config: dict):
        super().__init__(config)
        self._claves = {
            asignatura: [k for k in (_normalizar(c) for c in [*claves, asignatura]) if k]
            for asignatura, claves in config["carpetas"].items()
        }

    def _sumar(self, puntos: dict[str, int], texto: str, peso: int) -> None:
        palabras = set(texto.split())
        relleno = f" {texto} "
        for asignatura, claves in self._claves.items():
            for clave in claves:
                if (f" {clave} " in relleno) if " " in clave else (clave in palabras):
                    puntos[asignatura] += peso

    def clasificar(self, fichero: Path) -> str | None:
        puntos = dict.fromkeys(self._claves, 0)
        self._sumar(puntos, _normalizar(fichero.stem), 2)  # el nombre pesa más
        por_ext = {k.lower(): v for k, v in self.config.get("por_extension", {}).items()}
        asignatura_ext = por_ext.get(fichero.suffix.lower())
        if asignatura_ext in puntos:
            puntos[asignatura_ext] += 1
        if not any(puntos.values()) and fichero.suffix.lower() == ".pdf":
            self._sumar(puntos, _normalizar(_texto_pdf(fichero)), 1)
        mejor = max(puntos.values())
        if mejor == 0:
            return None
        return next(a for a, p in puntos.items() if p == mejor)  # empate: gana la primera

    def aplicar(self, fichero, n, simular):
        asignatura = self.clasificar(fichero)
        if asignatura is None:
            return Resultado(fichero, None, "saltado", "no sé de qué asignatura es")
        carpeta = self._carpeta_destino(fichero) / asignatura
        destino = destino_libre(carpeta / fichero.name, self._reservados)
        if not simular:
            carpeta.mkdir(parents=True, exist_ok=True)
            shutil.move(fichero, destino)
        return Resultado(fichero, destino, "simulado" if simular else "hecho")


class Convertir(Accion):
    """JPEG/PNG -> WebP con Pillow. No toca el original ni repite si el .webp ya existe."""

    tipo = "convertir"

    def aplicar(self, fichero, n, simular):
        carpeta = self._carpeta_destino(fichero)
        destino = carpeta / f"{fichero.stem}.webp"
        if destino.exists() or _clave(destino) in self._reservados:
            return Resultado(fichero, destino, "saltado", "ya existe el .webp")
        self._reservados.add(_clave(destino))
        if simular:
            return Resultado(fichero, destino, "simulado")
        from PIL import Image, UnidentifiedImageError

        try:
            carpeta.mkdir(parents=True, exist_ok=True)
            with Image.open(fichero) as imagen:
                if imagen.mode not in ("RGB", "RGBA"):
                    transparente = imagen.mode in ("P", "LA", "PA") or "transparency" in imagen.info
                    imagen = imagen.convert("RGBA" if transparente else "RGB")
                imagen.save(destino, "WEBP", quality=int(self.config.get("calidad", 80)))
        except UnidentifiedImageError:
            self._reservados.discard(_clave(destino))
            return Resultado(fichero, None, "saltado", "no es una imagen válida")
        except OSError:
            destino.unlink(missing_ok=True)  # no dejar un .webp a medias
            raise
        return Resultado(fichero, destino, "hecho")
