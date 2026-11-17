"""Lo que dice --simular es lo que pasa de verdad.

En el vídeo de la Sesión 2, la simulación decía que todo iba bien y, de verdad, los vídeos no se
movían (un comentario del agente mentía). Para que eso no me pase:

- Cada tipo de acción sin IA se ejecuta sobre DOS copias idénticas de la misma carpeta: en una con
  --simular y en la otra de verdad.
- Los ficheros elegidos, sus destinos y los saltados tienen que ser los mismos en las dos.
- Después de la ejecución real, cada fichero tiene que estar donde dijo la simulación (y el
  original, ya no estar si la acción mueve, o seguir ahí si copia).

Las acciones con IA no entran: con --simular no se pregunta al modelo, así que la simulación no
puede saber el nombre o la carpeta que elegirá (eso lo prueba test_ia.py).
"""

import os
import time
from pathlib import Path

import pytest
from PIL import Image

from tareas.motor import Motor

HACE_40_DIAS = time.time() - 40 * 24 * 3600


def preparar(base: Path) -> Path:
    """Una carpeta de Descargas con casos feos: tildes, espacios, mayúsculas, un temporal viejo
    y destinos que ya existen (para que salgan « (1)» y saltados)."""
    origen = base / "Descargas"
    origen.mkdir(parents=True)
    for nombre in ("factura.pdf", "linux tema 1.pdf", "apuntes sql.txt", "notas clase.docx", "reciente.tmp"):
        (origen / nombre).write_text(f"contenido de {nombre}", encoding="utf-8")
    (origen / "viejo.tmp").write_text("x", encoding="utf-8")
    os.utime(origen / "viejo.tmp", (HACE_40_DIAS, HACE_40_DIAS))
    Image.new("RGB", (8, 8), (200, 10, 10)).save(origen / "FOTO1.JPG", "JPEG")
    Image.new("RGBA", (8, 8), (10, 200, 10, 128)).save(origen / "cumpleaños 2.png", "PNG")
    # Destinos que ya existen
    (base / "PDF").mkdir()
    (base / "PDF" / "factura.pdf").write_text("la que ya tenía", encoding="utf-8")
    (base / "webp").mkdir()
    (base / "webp" / "FOTO1.webp").write_bytes(b"ya convertida")
    return origen


# (tipo, campos de la acción según la carpeta base, ¿mueve el original?)
CASOS = [
    ("mover", lambda b: {"destino": str(b / "PDF"), "filtro": {"extensiones": [".pdf"]}}, True),
    ("copiar", lambda b: {"destino": str(b / "copias"), "filtro": {"extensiones": [".jpg", ".png"]}}, False),
    ("renombrar", lambda b: {"plantilla": "foto_{n:03}{ext}", "filtro": {"extensiones": [".jpg", ".png"]}}, True),
    ("borrar", lambda b: {"filtro": {"extensiones": [".tmp"], "mas_antiguo_que_dias": 30}}, True),
    ("convertir", lambda b: {"destino": str(b / "webp"), "filtro": {"extensiones": [".jpg", ".png"]}}, False),
    ("ordenar", lambda b: {"carpetas": {"sistemas": ["linux"], "bases-datos": ["sql"]},
                           "por_tipo": str(b / "POR-TIPO")}, True),
]


def relativo(ruta: Path | None, base: Path) -> str | None:
    return None if ruta is None else ruta.relative_to(base).as_posix()


def resumen(resultados, base: Path) -> list[tuple]:
    """Lo que importa de cada resultado, sin la carpeta base y con «simulado» contado como «hecho»."""
    return [(relativo(r.origen, base), relativo(r.destino, base), "hecho" if r.estado == "simulado" else r.estado)
            for r in resultados]


def arbol(carpeta: Path) -> set:
    return {(p.relative_to(carpeta).as_posix(), p.stat().st_size) for p in carpeta.rglob("*")}


@pytest.mark.parametrize("tipo, campos, mueve", CASOS, ids=[c[0] for c in CASOS])
def test_lo_que_simula_es_lo_que_hace(tmp_path, tipo, campos, mueve):
    base_sim, base_real = tmp_path / "simulado", tmp_path / "real"
    origen_sim, origen_real = preparar(base_sim), preparar(base_real)

    def accion(base: Path) -> Motor:
        return Motor([{"nombre": "a", "descripcion": "d", "tipo": tipo, **campos(base)}])

    antes = arbol(base_sim)
    simulado = accion(base_sim).ejecutar("a", origen_sim, simular=True)
    real = accion(base_real).ejecutar("a", origen_real, simular=False)

    assert simulado, "la prueba no vale si la acción no elige ningún fichero"
    assert arbol(base_sim) == antes                                  # simular no ha tocado nada
    assert all(r.estado in ("simulado", "saltado") for r in simulado)
    assert all(r.estado in ("hecho", "saltado") for r in real)       # ningún error de verdad
    assert resumen(simulado, base_sim) == resumen(real, base_real)   # mismos ficheros, destinos y saltados

    # Y de verdad, cada fichero está donde dijo la simulación
    for r in real:
        if r.estado != "hecho":
            continue
        if r.destino is not None:
            assert r.destino.is_file(), f"la simulación dijo {r.destino.name} y no está"
        assert r.origen.exists() != mueve, f"{r.origen.name}: {'debía irse' if mueve else 'debía quedarse'}"
