"""dam duplicados: ficheros repetidos (mismo contenido) y carpetas que son copia de otra.

Solo LEE: no mueve ni borra nada. Para saber si dos ficheros son iguales compara su contenido
(huella SHA-256), no el nombre. Para ir rápido, primero agrupa por tamaño y solo calcula la
huella de los que coinciden; y antes de leer un fichero entero, compara su principio.

No lee los ficheros de OneDrive «solo en la nube» (leerlos los descargaría) y se salta lo mismo
que dam inventario: enlaces, carpetas del sistema, .git, carpetas regenerables y de programas.
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .errores import TareasError
from .inventario import REGENERABLES, SISTEMA, _es_enlace, _tabla, es_programa, esta_en_la_nube, tamano_legible

BLOQUE = 1024 * 1024  # se lee de 1 MB en 1 MB
PRINCIPIO = 64 * 1024  # para descartar rápido: los primeros 64 KB


@dataclass
class Grupo:
    """Ficheros con el mismo contenido. «sobra» es lo que se liberaría dejando solo una copia."""
    tamano: int
    rutas: list[str]  # relativas a la carpeta revisada, con /

    @property
    def sobra(self) -> int:
        return self.tamano * (len(self.rutas) - 1)


@dataclass
class CarpetaCopia:
    """Una carpeta en la que TODOS los ficheros tienen otra copia fuera de ella."""
    ruta: str
    ficheros: int
    tamano: int
    original: str | None  # dónde está la otra copia, si está entera en un sitio con la misma estructura


@dataclass
class Informe:
    carpeta: Path
    ficheros: int = 0  # revisados (sin contar los vacíos ni los de la nube)
    tamano: int = 0
    grupos: list[Grupo] = field(default_factory=list)
    carpetas_copia: list[CarpetaCopia] = field(default_factory=list)
    repos: list[str] = field(default_factory=list)
    en_nube: int = 0  # ficheros «solo en la nube»: no se leen
    sin_acceso: list[str] = field(default_factory=list)

    @property
    def sobra(self) -> int:
        return sum(g.sobra for g in self.grupos)

    def repo_de(self, ruta: str) -> str | None:
        """El repo en el que está una ruta (el más profundo), o None."""
        dentro = [r for r in self.repos if r == "." or ruta == r or ruta.startswith(r + "/")]
        return max(dentro, key=len) if dentro else None


def huella(ruta: Path, hasta: int | None = None) -> str:
    """SHA-256 del contenido (o de los primeros «hasta» bytes)."""
    calculo = hashlib.sha256()
    leidos = 0
    with ruta.open("rb") as fichero:
        while hasta is None or leidos < hasta:
            trozo = fichero.read(BLOQUE if hasta is None else min(BLOQUE, hasta - leidos))
            if not trozo:
                break
            calculo.update(trozo)
            leidos += len(trozo)
    return calculo.hexdigest()


def _ancestros(ruta: str) -> list[str]:
    """«a/b/c.pdf» -> ["a/b", "a"] (sin la raíz)."""
    partes = ruta.split("/")[:-1]
    return ["/".join(partes[:i]) for i in range(len(partes), 0, -1)]


def _recorrer(raiz: Path, informe: Informe) -> dict[int, list[tuple[str, Path]]]:
    """Ficheros por tamaño. Apunta los repos y lo que no se puede leer."""
    por_tamano: dict[int, list[tuple[str, Path]]] = defaultdict(list)
    vistos: set[tuple[int, int]] = set()  # enlaces duros: el mismo fichero con dos nombres no es una copia
    dentro_de_repo: dict[Path, bool] = {}

    def rel(ruta: Path) -> str:
        return ruta.relative_to(raiz).as_posix() or "."

    def sin_permiso(error: OSError) -> None:
        informe.sin_acceso.append(rel(Path(error.filename)) if error.filename else str(error))

    for actual, carpetas, ficheros in raiz.walk(on_error=sin_permiso):
        en_repo = dentro_de_repo.get(actual.parent, False) if actual != raiz else False
        if (actual / ".git").exists():
            informe.repos.append(rel(actual))
            en_repo = True
        dentro_de_repo[actual] = en_repo
        carpetas[:] = [c for c in carpetas
                       if not (_es_enlace(actual / c) or c in SISTEMA or c == ".git"
                               or c in REGENERABLES or es_programa(c, en_repo))]
        for nombre in ficheros:
            ruta = actual / nombre
            try:
                datos = ruta.stat(follow_symlinks=False)
            except OSError:
                informe.sin_acceso.append(rel(ruta))
                continue
            if esta_en_la_nube(datos):
                informe.en_nube += 1
                continue
            if datos.st_size == 0:
                continue  # los vacíos son todos «iguales»: no dicen nada
            if datos.st_ino and (datos.st_dev, datos.st_ino) in vistos:
                continue
            vistos.add((datos.st_dev, datos.st_ino))
            informe.ficheros += 1
            informe.tamano += datos.st_size
            por_tamano[datos.st_size].append((rel(ruta), ruta))
    return por_tamano


def _agrupar(candidatos: list[tuple[str, Path]], informe: Informe, hasta: int | None) -> list[list[tuple[str, Path]]]:
    """Separa los candidatos por su huella; devuelve solo los grupos de 2 o más."""
    por_huella: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    for relativa, ruta in candidatos:
        try:
            por_huella[huella(ruta, hasta)].append((relativa, ruta))
        except OSError:
            informe.sin_acceso.append(relativa)
    return [g for g in por_huella.values() if len(g) > 1]


def _carpetas_copia(informe: Informe, cuantos_en: Counter) -> list[CarpetaCopia]:
    """Carpetas en las que cada fichero tiene otra copia FUERA de la carpeta (solo las de más arriba)."""
    con_copia_fuera: Counter = Counter()
    bytes_fuera: Counter = Counter()
    raices: dict[str, Counter] = defaultdict(Counter)  # carpeta -> posibles «originales»
    for grupo in informe.grupos:
        debajo: Counter = Counter(a for r in grupo.rutas for a in _ancestros(r))
        for ruta in grupo.rutas:
            for carpeta in _ancestros(ruta):
                if debajo[carpeta] == len(grupo.rutas):
                    continue  # todas las copias están dentro de esta carpeta
                con_copia_fuera[carpeta] += 1
                bytes_fuera[carpeta] += grupo.tamano
                resto = ruta[len(carpeta) + 1:]
                igual = resto.casefold()  # en Windows, «Fotos» y «FOTOS» son la misma carpeta
                fuera = [o for o in grupo.rutas if not o.startswith(carpeta + "/")]
                # ¿hay otra copia con la misma estructura? (…/ORIGINAL/resto)
                misma = next((o for o in fuera if o.casefold().endswith("/" + igual) or o.casefold() == igual), None)
                raices[carpeta][(misma[: -len(resto)].rstrip("/") or ".") if misma else None] += 1

    def tiene_un_repo(carpeta: str) -> bool:
        """Su .git no se compara: borrarla entera perdería el historial."""
        return any(r == carpeta or r.startswith(carpeta + "/") for r in informe.repos)

    completas = {c for c, n in con_copia_fuera.items() if n >= 2 and n == cuantos_en[c] and not tiene_un_repo(c)}
    resultado = []
    for carpeta in completas:
        if any(a in completas for a in _ancestros(carpeta + "/x")[1:]):
            continue  # ya sale su carpeta de arriba
        original, veces = raices[carpeta].most_common(1)[0]
        resultado.append(CarpetaCopia(carpeta, cuantos_en[carpeta], bytes_fuera[carpeta],
                                      original if original is not None and veces == cuantos_en[carpeta] else None))

    # Primero las de fuera de los repos (se borran sin commit); dentro de cada bloque, las más grandes
    resultado.sort(key=lambda c: (informe.repo_de(c.ruta) is not None, -c.tamano, c.ruta))
    # Si A es copia de B y B de A, sale solo una (la primera: la de fuera del repo, si la hay).
    # También cuenta como pareja si B sale un nivel más arriba (B = «asignaturas» y el original era «asignaturas/1 PROJECTE»).
    def misma_pareja(ruta: str, original: str) -> bool:
        return ruta == original or original.startswith(ruta + "/") or ruta.startswith(original + "/")

    originales: list[str] = []
    sin_parejas = []
    for copia in resultado:
        if not any(misma_pareja(copia.ruta, o) for o in originales):
            sin_parejas.append(copia)
            if copia.original:
                originales.append(copia.original)
    return sin_parejas


def revisar(carpeta: Path) -> Informe:
    """Busca ficheros repetidos en la carpeta y las subcarpetas que son copia completa de otra."""
    raiz = carpeta.expanduser().resolve()
    if not raiz.is_dir():
        raise TareasError(f"«{raiz}» no existe o no es una carpeta.")
    informe = Informe(raiz)
    por_tamano = _recorrer(raiz, informe)

    cuantos_en: Counter = Counter()  # carpeta -> ficheros revisados que tiene dentro (a cualquier nivel)
    for lista in por_tamano.values():
        for relativa, _ in lista:
            cuantos_en.update(_ancestros(relativa))

    for tamano, candidatos in por_tamano.items():
        if len(candidatos) < 2:
            continue
        grupos = [candidatos]
        if tamano > PRINCIPIO:  # primero el principio; solo si coincide, el fichero entero
            grupos = _agrupar(candidatos, informe, PRINCIPIO)
        for posibles in grupos:
            for iguales in _agrupar(posibles, informe, None):
                informe.grupos.append(Grupo(tamano, sorted(r for r, _ in iguales)))

    informe.grupos.sort(key=lambda g: (g.sobra, g.rutas[0]), reverse=True)
    informe.carpetas_copia = _carpetas_copia(informe, cuantos_en)
    return informe


# ---------- informe en Markdown (--guardar) ----------
def a_markdown(informe: Informe, top: int = 15) -> str:
    """El informe en Markdown. Las carpetas copia salen todas; los grupos, los «top» más grandes."""
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    lineas = [
        f"# Duplicados de `{informe.carpeta}`", "",
        f"Generado con `dam duplicados` el {fecha}. Se ha comparado el contenido (SHA-256): no se ha tocado nada.", "",
        f"- **{informe.ficheros}** ficheros revisados ({tamano_legible(informe.tamano)})",
        f"- **{len(informe.grupos)}** grupos de ficheros repetidos · dejando una copia de cada, "
        f"se liberarían **{tamano_legible(informe.sobra)}**",
        f"- Ficheros «solo en la nube» que no se han leído: {informe.en_nube}", "",
        f"## Carpetas que son copia de otra ({len(informe.carpetas_copia)})", "",
        "Todos sus ficheros tienen otra copia fuera de la carpeta. Son las primeras candidatas a borrar, "
        "pero antes comprueba qué copia quieres guardar.", "",
    ]
    if informe.carpetas_copia:
        filas = [[f"`{c.ruta}`", str(c.ficheros), tamano_legible(c.tamano),
                  f"`{c.original}`" if c.original else "repartida en varios sitios",
                  "sí" if informe.repo_de(c.ruta) else ""] for c in informe.carpetas_copia]
        lineas += _tabla(["Carpeta", "Ficheros", "Tamaño", "La otra copia está en", "En un repo"], filas)
    else:
        lineas.append("Ninguna.")
    lineas += ["", f"## Ficheros repetidos ({len(informe.grupos)} grupos)", "",
               "«(repo)» = esa copia está en un repo git: si la quitas, hazlo con un commit.", ""]
    for grupo in informe.grupos[:top]:
        lineas.append(f"- **{tamano_legible(grupo.tamano)} × {len(grupo.rutas)}** (sobran {tamano_legible(grupo.sobra)})")
        lineas += [f"  - `{r}`" + (" (repo)" if informe.repo_de(r) else "") for r in grupo.rutas]
    if len(informe.grupos) > top:
        lineas.append(f"\n…y {len(informe.grupos) - top} grupos más (usa `--top {len(informe.grupos)}` para verlos todos).")
    if informe.sin_acceso:
        lineas += ["", f"## Sin permiso de lectura ({len(informe.sin_acceso)})", ""]
        lineas += [f"- `{s}`" for s in informe.sin_acceso[:top]]
    return "\n".join(lineas) + "\n"
