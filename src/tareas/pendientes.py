"""dam pendientes: qué está verificado y qué no en la documentación de un proyecto.

Lee dos cosas de los .md:
  1. Las etiquetas sueltas: [Verificado], [Hipótesis] y [Pendiente] (con lo que lleven detrás:
     «[Verificado, entrevista 4, 29/10/2026]»). Un [Verificado] sin fecha se marca aparte.
  2. El registro de pendientes (pendientes.md): una tabla con las columnas #, Dato, Responsable y Estado.

Solo lee: no cambia ningún fichero.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from . import escanear
from .errores import TareasError

TIPOS = ("Verificado", "Hipótesis", "Pendiente")
CARPETAS_HISTORICO = {"historico", "histórico"}  # documentos viejos: sus etiquetas ya no cuentan
NOMBRE_REGISTRO = "pendientes.md"
ESTADOS_ABIERTOS = ("Pendiente", "En curso")
LARGO_TEXTO = 110

# [Verificado], [Verificado 29/10/2026], [Hipótesis], [Pendiente de decidir]... pero no un enlace [Pendiente](x.md)
ETIQUETA = re.compile(r"\[(Verificad[oa]s?|Hip[oó]tesis|Pendientes?)\b([^\]]*)\](?!\()", re.IGNORECASE)
FECHA = re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b")
# Líneas de leyenda: «- **[Verificado]** — comprobado en una fuente...» y «Etiquetas: [Verificado]..., [Pendiente]»
LEYENDA = re.compile(r"^\s*[-*]\s*\**\[[^\]]+\]\**\s*[—–:-]")
LEYENDA_TITULO = re.compile(r"^\W*Etiquetas\b[^:\[]{0,25}:", re.IGNORECASE)
ESTADO = re.compile(r"^\W*(pendiente|en curso|verificad[oa]|descartad[oa])", re.IGNORECASE)


@dataclass
class Etiqueta:
    fichero: str
    linea: int
    tipo: str  # "Verificado", "Hipótesis" o "Pendiente"
    texto: str  # la línea, limpia y recortada
    con_fecha: bool


@dataclass
class FilaRegistro:
    fichero: str
    numero: str
    dato: str
    responsable: str
    estado: str  # "Pendiente", "En curso", "Verificado", "Descartado" o "sin estado"

    @property
    def abierta(self) -> bool:
        return self.estado in ESTADOS_ABIERTOS


@dataclass
class Informe:
    carpeta: Path
    ficheros: list[str] = field(default_factory=list)  # los .md revisados
    etiquetas: list[Etiqueta] = field(default_factory=list)
    registro: list[FilaRegistro] = field(default_factory=list)

    def cuenta(self, fichero: str | None = None) -> dict[str, int]:
        """Etiquetas por tipo (de un fichero o de todos), y los verificados sin fecha aparte."""
        elegidas = [e for e in self.etiquetas if fichero is None or e.fichero == fichero]
        cuenta = {t: sum(1 for e in elegidas if e.tipo == t) for t in TIPOS}
        cuenta["sin fecha"] = sum(1 for e in elegidas if e.tipo == "Verificado" and not e.con_fecha)
        return cuenta


def sin_acentos(texto: str) -> str:
    """«Hipótesis» -> «hipotesis»: para comparar sin depender de acentos ni mayúsculas."""
    normal = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in normal if unicodedata.category(c) != "Mn")


def _tipo(palabra: str) -> str:
    p = sin_acentos(palabra)
    return "Verificado" if p.startswith("verificad") else "Hipótesis" if p.startswith("hipotesis") else "Pendiente"


def _limpiar(linea: str) -> str:
    """Quita el formato de Markdown para enseñar la línea en una tabla."""
    texto = linea.replace("**", "").replace("`", "").strip().lstrip("-*> ").strip()
    if texto.startswith("|"):
        texto = " · ".join(c.strip() for c in texto.strip("|").split("|") if c.strip())
    texto = " ".join(texto.split())
    return texto if len(texto) <= LARGO_TEXTO else texto[: LARGO_TEXTO - 1] + "…"


def etiquetas_de_texto(fichero: str, contenido: str) -> list[Etiqueta]:
    resultado = []
    for n, linea in enumerate(contenido.splitlines(), start=1):
        if "dam:ignore" in linea or LEYENDA.match(linea) or LEYENDA_TITULO.match(linea):
            continue
        encontradas = list(ETIQUETA.finditer(linea))
        if {_tipo(m.group(1)) for m in encontradas} == set(TIPOS):
            continue  # «Etiquetas: [Verificado]..., [Hipótesis], [Pendiente]»: es la leyenda
        for m in encontradas:
            tipo = _tipo(m.group(1))
            con_fecha = bool(FECHA.search(linea))  # en la etiqueta o en la misma línea (la fuente)
            resultado.append(Etiqueta(fichero, n, tipo, _limpiar(linea), con_fecha))
    return resultado


def _celdas(linea: str) -> list[str]:
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def _estado(texto: str) -> str:
    m = ESTADO.match(texto.replace("*", ""))
    if not m:
        return "sin estado"
    palabra = sin_acentos(m.group(1))
    return {"pendiente": "Pendiente", "en curso": "En curso"}.get(palabra, palabra[:-1].capitalize() + "o")


def filas_de_registro(fichero: str, contenido: str) -> list[FilaRegistro]:
    """Filas de las tablas que tengan las columnas # (o Nº), Dato, Responsable y Estado."""
    filas: list[FilaRegistro] = []
    columnas: dict[str, int] | None = None
    for linea in contenido.splitlines():
        if not linea.strip().startswith("|"):
            columnas = None  # fuera de una tabla
            continue
        celdas = _celdas(linea)
        if columnas is None:
            nombres = [sin_acentos(c.replace("*", "")) for c in celdas]
            buscadas = {"numero": ("#", "nº", "n"), "dato": ("dato", "que", "tarea"),
                        "responsable": ("responsable", "quien"), "estado": ("estado",)}
            encontradas = {clave: next((i for i, n in enumerate(nombres) if n in opciones), None)
                           for clave, opciones in buscadas.items()}
            columnas = {k: v for k, v in encontradas.items() if v is not None}
            if not {"dato", "estado"} <= columnas.keys():
                columnas = {}  # una tabla que no es un registro: se ignora entera
            continue
        if not columnas or set(linea.replace("|", "").strip()) <= set("-: "):
            continue  # tabla ignorada, o la línea |---|---| de debajo de la cabecera
        filas.append(FilaRegistro(
            fichero,
            _celda(celdas, columnas, "numero"),
            _limpiar(_celda(celdas, columnas, "dato")),
            _limpiar(_celda(celdas, columnas, "responsable")) or "—",
            _estado(_celda(celdas, columnas, "estado")),
        ))
    return filas


def _celda(celdas: list[str], columnas: dict[str, int], clave: str) -> str:
    i = columnas.get(clave)
    return celdas[i] if i is not None and i < len(celdas) else ""


def revisar(carpeta: Path) -> Informe:
    raiz = carpeta.expanduser().resolve()
    if not raiz.is_dir():
        raise TareasError(f"«{raiz}» no existe o no es una carpeta.")
    informe = Informe(raiz)
    for ruta in escanear.ficheros_del_proyecto(raiz):  # respeta .gitignore y salta .venv, node_modules...
        rel = ruta.relative_to(raiz)
        if ruta.suffix.lower() != ".md" or CARPETAS_HISTORICO & {sin_acentos(p) for p in rel.parts[:-1]}:
            continue
        try:
            contenido = ruta.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        nombre = rel.as_posix()
        informe.ficheros.append(nombre)
        informe.etiquetas += etiquetas_de_texto(nombre, contenido)
        if ruta.name.lower() == NOMBRE_REGISTRO:
            informe.registro += filas_de_registro(nombre, contenido)
    return informe


NOMBRE_PROPIO = re.compile(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñü]+\b")


def personas(responsable: str) -> list[str]:
    """«Gabi y Javi» -> [Gabi, Javi]; «Sergio; lo aprueba el equipo» -> [Sergio]. Sin nombres: [«sin responsable»]."""
    nombres = list(dict.fromkeys(NOMBRE_PROPIO.findall(responsable)))
    return nombres or ["sin responsable"]


def reparto(filas: list[FilaRegistro]) -> dict[str, int]:
    """Cuántas filas tiene cada persona (una fila de «Gabi y Javi» cuenta para los dos), de más a menos."""
    cuenta: dict[str, int] = {}
    for fila in filas:
        for persona in personas(fila.responsable):
            cuenta[persona] = cuenta.get(persona, 0) + 1
    return dict(sorted(cuenta.items(), key=lambda par: (-par[1], par[0])))


def es_de(fila: FilaRegistro, quien: str) -> bool:
    """¿Le toca a «quien»? Compara nombres enteros (Mar no es «Marta»). Lo de «Todos» le toca a todo el mundo."""
    nombres = {sin_acentos(p) for p in personas(fila.responsable)}
    return sin_acentos(quien.strip()) in nombres or "todos" in nombres
