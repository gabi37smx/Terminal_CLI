"""dam entregar: empaqueta un proyecto en un .zip limpio para entregarlo.

Fuera quedan los secretos (.env, claves privadas), lo que no hace falta (.venv, node_modules,
.git, __pycache__...) y, si es un repositorio, todo lo que ignora .gitignore. Antes de crear
el zip se pasa scan-secrets sobre lo que va dentro: si hay un secreto seguro, no se crea.
"""

from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from . import escanear
from .acciones import destino_libre
from .errores import TareasError

# Ficheros que crea el sistema operativo y no aportan nada a la entrega
BASURA = {"thumbs.db", "desktop.ini", ".ds_store"}


@dataclass
class Plan:
    """Qué se va a meter en el zip y qué se queda fuera. Preparar un plan no toca nada."""

    carpeta: Path
    zip: Path
    con_git: bool  # si es un repositorio, se respeta su .gitignore
    incluidos: list[str] = field(default_factory=list)  # rutas relativas, con «/»
    excluidos: dict[str, list[str]] = field(default_factory=dict)  # motivo -> rutas
    hallazgos: list[escanear.Hallazgo] = field(default_factory=list)
    tamano: int = 0  # suma de los ficheros, sin comprimir

    @property
    def bloqueado(self) -> bool:
        """Un secreto seguro dentro del zip: no se entrega."""
        return any(h.confianza == "alta" for h in self.hallazgos)


def _motivo_para_excluir(rel: Path) -> tuple[str, str] | None:
    """Devuelve (motivo, lo que se enseña) si el fichero NO debe ir en el zip, o None si va."""
    for i, parte in enumerate(rel.parts[:-1]):
        if parte in escanear.CARPETAS_IGNORADAS:
            # Se enseña la carpeta, no sus miles de ficheros (node_modules/, .venv/...)
            return "carpetas que se regeneran", Path(*rel.parts[: i + 1]).as_posix() + "/"
    if escanear.es_env(rel.name):
        return "secretos", rel.as_posix()
    if escanear.es_clave_privada(rel):
        return "claves privadas", rel.as_posix()
    if rel.name.lower() in BASURA:
        return "basura del sistema", rel.as_posix()
    return None


def _lo_que_se_queda_fuera_en_disco(carpeta: Path) -> dict[str, list[str]]:
    """Recorre el disco (no la lista de git) para enseñar siempre lo importante que no entra:
    .venv/, node_modules/... (sin entrar en ellas: pueden ser enormes), los .env y las claves,
    aunque ya los ignore .gitignore. Así se ve que .env se queda fuera."""
    fuera: dict[str, list[str]] = {"carpetas que se regeneran": [], "secretos": [], "claves privadas": []}
    for actual, subcarpetas, nombres in os.walk(carpeta):
        rel_actual = Path(actual).relative_to(carpeta)
        for nombre in subcarpetas:
            if nombre in escanear.CARPETAS_IGNORADAS:
                fuera["carpetas que se regeneran"].append((rel_actual / nombre).as_posix() + "/")
        subcarpetas[:] = [d for d in subcarpetas if d not in escanear.CARPETAS_IGNORADAS]
        for nombre in nombres:
            if escanear.es_env(nombre):
                fuera["secretos"].append((rel_actual / nombre).as_posix())
            elif escanear.es_clave_privada(Path(nombre)):
                fuera["claves privadas"].append((rel_actual / nombre).as_posix())
    return {motivo: sorted(rutas) for motivo, rutas in fuera.items() if rutas}


def _nombre_zip(carpeta: Path, nombre: str | None, hoy: date) -> str:
    if nombre is None:
        return f"{carpeta.name}_{hoy.isoformat()}.zip"
    if not nombre.strip() or Path(nombre).name != nombre:
        raise TareasError(f"«{nombre}» no vale como nombre: escribe solo el nombre, sin carpetas (usa --destino).")
    return nombre if nombre.lower().endswith(".zip") else nombre + ".zip"


def preparar(carpeta: Path, destino: Path | None = None, nombre: str | None = None,
             hoy: date | None = None) -> Plan:
    """Decide qué entra en el zip y pasa scan-secrets sobre ello. No escribe nada en disco."""
    carpeta = carpeta.expanduser().resolve()
    if not carpeta.is_dir():
        raise TareasError(f"«{carpeta}» no existe o no es una carpeta.")
    # Por defecto el zip va al lado de la carpeta, no dentro (si no, la próxima entrega lo incluiría)
    destino = (destino.expanduser().resolve() if destino else carpeta.parent)
    if not destino.is_dir():
        raise TareasError(f"La carpeta de destino «{destino}» no existe.")

    zip_final = destino_libre(destino / _nombre_zip(carpeta, nombre, hoy or date.today()))
    plan = Plan(carpeta, zip_final, escanear.es_repo(carpeta))
    plan.excluidos = _lo_que_se_queda_fuera_en_disco(carpeta)

    dentro: list[Path] = []
    for ruta in escanear.ficheros_del_proyecto(carpeta):
        rel = ruta.relative_to(carpeta)
        motivo = _motivo_para_excluir(rel)
        if motivo:
            motivo_texto, mostrar = motivo
            lista = plan.excluidos.setdefault(motivo_texto, [])
            if mostrar not in lista:
                lista.append(mostrar)
            continue
        try:
            plan.tamano += ruta.stat().st_size
        except OSError:
            continue  # enlace roto o sin permisos: no se puede meter
        dentro.append(ruta)
        plan.incluidos.append(rel.as_posix())

    plan.hallazgos, _, _ = escanear.escanear_arbol(carpeta, ficheros=dentro)
    return plan


def crear_zip(plan: Plan) -> Path:
    """Escribe el zip. Dentro, todo va en una carpeta con el nombre del proyecto."""
    assert not plan.bloqueado, "no se crea un zip con secretos dentro"
    if not plan.incluidos:
        raise TareasError("No hay ningún fichero que entregar.")
    try:
        # «x»: si el fichero ya existe, falla en vez de pisarlo
        with zipfile.ZipFile(plan.zip, "x", compression=zipfile.ZIP_DEFLATED, strict_timestamps=False) as z:
            for rel in plan.incluidos:
                z.write(plan.carpeta / rel, f"{plan.carpeta.name}/{rel}")
    except FileExistsError:
        raise TareasError(f"«{plan.zip}» ya existe: no lo piso. Vuelve a lanzar la orden.") from None
    except OSError as e:
        plan.zip.unlink(missing_ok=True)  # no dejar un zip a medias
        raise TareasError(f"No he podido crear «{plan.zip}»: {e}") from None
    return plan.zip
