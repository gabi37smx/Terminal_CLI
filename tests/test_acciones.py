import os
import time
from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from tareas.acciones import Accion, Ordenar, destino_libre
from tareas.cli import app
from tareas.errores import TareasError
from tareas.motor import Motor

import json
import pytest


def foto(ruta: Path, formato="PNG"):
    Image.new("RGB", (8, 8), (200, 10, 10)).save(ruta, formato)


def arbol(carpeta: Path) -> set:
    return {(str(p.relative_to(carpeta)), p.stat().st_size) for p in carpeta.rglob("*")}


def motor(tmp_path, **accion):
    base = {"nombre": "a", "descripcion": "d"}
    return Motor([{**base, **accion}])


def test_mover_no_sobrescribe_y_es_idempotente(tmp_path):
    orig, dest = tmp_path / "o", tmp_path / "d"
    orig.mkdir(); dest.mkdir()
    (orig / "f.pdf").write_text("nuevo")
    (dest / "f.pdf").write_text("viejo")
    m = motor(tmp_path, tipo="mover", destino=str(dest), filtro={"extensiones": [".pdf"]})
    r = m.ejecutar("a", orig, simular=False)
    assert r[0].estado == "hecho" and r[0].destino.name == "f (1).pdf"
    assert (dest / "f.pdf").read_text() == "viejo"
    assert m.ejecutar("a", orig, simular=False) == []  # la segunda vez no hay nada


def test_simular_no_toca_nada_ni_crea_carpetas(tmp_path):
    orig = tmp_path / "o"; orig.mkdir()
    (orig / "a.pdf").write_text("x")
    antes = arbol(tmp_path)
    m = motor(tmp_path, tipo="mover", destino=str(tmp_path / "NoExiste" / "sub"))
    r = m.ejecutar("a", orig, simular=True)
    assert r[0].estado == "simulado"
    assert arbol(tmp_path) == antes
    assert not (tmp_path / "NoExiste").exists()


def test_simulacion_detecta_colision_entre_ficheros_nuevos(tmp_path):
    orig = tmp_path / "o"; orig.mkdir()
    for n in ("a.jpg", "b.jpg"):
        (orig / n).write_text("x")
        os.utime(orig / n, (1_700_000_000, 1_700_000_000))
    m = motor(tmp_path, tipo="renombrar", plantilla="{fecha:%Y}{ext}")
    r = m.ejecutar("a", orig, simular=True)
    assert {x.destino.name for x in r} == {"2023.jpg", "2023 (1).jpg"}


def test_destino_libre_no_distingue_mayusculas_en_reservados(tmp_path):
    reservados = set()
    a = destino_libre(tmp_path / "foto.jpg", reservados)
    b = destino_libre(tmp_path / "foto.jpg", reservados)
    assert a != b


def test_extension_en_mayusculas_y_nombres_con_tildes(tmp_path):
    orig = tmp_path / "o"; orig.mkdir()
    (orig / "FOTO1.JPG").write_text("x")
    (orig / "cumpleaños 2.jpg").write_text("x")
    (orig / "[borrador].txt").write_text("x")
    m = motor(tmp_path, tipo="copiar", destino=str(tmp_path / "d"), filtro={"extensiones": [".jpg"]})
    r = m.ejecutar("a", orig, simular=False)
    assert sorted(x.origen.name for x in r) == ["FOTO1.JPG", "cumpleaños 2.jpg"]
    assert (tmp_path / "d" / "cumpleaños 2.jpg").exists() and (orig / "FOTO1.JPG").exists()


def test_borrar_solo_los_viejos(tmp_path):
    orig = tmp_path / "o"; orig.mkdir()
    viejo, nuevo = orig / "viejo.tmp", orig / "nuevo.tmp"
    viejo.write_text("x"); nuevo.write_text("x")
    hace40 = time.time() - 40 * 86400
    os.utime(viejo, (hace40, hace40))
    m = motor(tmp_path, tipo="borrar", filtro={"extensiones": [".tmp"], "mas_antiguo_que_dias": 30})
    assert [r.origen.name for r in m.ejecutar("a", orig, simular=True)] == ["viejo.tmp"]
    assert viejo.exists()
    m.ejecutar("a", orig, simular=False)
    assert not viejo.exists() and nuevo.exists()


def clasificador():
    return Ordenar({"nombre": "o", "descripcion": "d", "tipo": "ordenar",
                    "carpetas": {"sistemas": ["so", "linux", "redes"],
                                 "bases-datos": ["sql", "bases de datos"],
                                 "programacion": ["python"]},
                    "por_extension": {".sql": "bases-datos"}})


@pytest.mark.parametrize("nombre, esperado", [
    ("resolucion_ejercicio.txt", None),             # «so» dentro de «resolucion» NO cuenta
    ("apuntes_SO_tema1.pdf", "sistemas"),           # «so» como palabra sí
    ("Bases de Datos tema 2.pdf", "bases-datos"),   # frase con espacios
    ("consulta.sql", "bases-datos"),                # por extensión
    ("practicas_linux.txt", "sistemas"),
    ("PYTHON-ejercicios.txt", "programacion"),
    ("foto.png", None),
])
def test_ordenar_clasifica_palabras_completas(tmp_path, nombre, esperado):
    f = tmp_path / nombre
    f.write_text("x")
    assert clasificador().clasificar(f) == esperado


def test_ordenar_pdf_roto_no_revienta(tmp_path):
    f = tmp_path / "raro.pdf"
    f.write_bytes(b"%PDF-1.4 esto no es un pdf de verdad")
    assert clasificador().clasificar(f) is None


def test_ordenar_mueve_y_deja_sin_clasificar(tmp_path):
    (tmp_path / "linux.txt").write_text("x")
    (tmp_path / "misterio.txt").write_text("x")
    cfg = clasificador().config
    r = Motor([cfg]).ejecutar("o", tmp_path, simular=False)
    estados = {x.origen.name: x.estado for x in r}
    assert estados == {"linux.txt": "hecho", "misterio.txt": "saltado"}
    assert (tmp_path / "sistemas" / "linux.txt").exists()


def test_convertir_webp_sin_duplicar_ni_tocar_original(tmp_path):
    foto(tmp_path / "a.png"); foto(tmp_path / "b.jpg", "JPEG")
    (tmp_path / "falsa.png").write_text("no soy una imagen")
    m = motor(tmp_path, tipo="convertir", filtro={"extensiones": [".png", ".jpg"]})
    r = {x.origen.name: x for x in m.ejecutar("a", tmp_path, simular=False)}
    assert r["a.png"].estado == "hecho" and r["b.jpg"].estado == "hecho"
    assert r["falsa.png"].estado == "saltado" and not (tmp_path / "falsa.webp").exists()
    assert (tmp_path / "a.webp").exists() and (tmp_path / "a.png").exists()
    r2 = {x.origen.name: x for x in m.ejecutar("a", tmp_path, simular=False)}
    assert r2["a.png"].estado == "saltado"  # ya existe el .webp


def test_accion_o_carpeta_inexistente(tmp_path):
    m = motor(tmp_path, tipo="borrar", filtro={"extensiones": [".tmp"]})
    with pytest.raises(TareasError, match="No hay ninguna acción"):
        m.ejecutar("nada", tmp_path, True)
    with pytest.raises(TareasError, match="no existe"):
        m.ejecutar("a", tmp_path / "x", True)


def test_fabrica_no_usa_if_por_tipo():
    assert {"mover", "copiar", "renombrar", "borrar", "ordenar", "convertir"} <= set(Accion._registro)


def test_cli_borrar_pide_confirmacion(tmp_path):
    (tmp_path / "v.tmp").write_text("x")
    os.utime(tmp_path / "v.tmp", (1_600_000_000, 1_600_000_000))
    cfg = tmp_path / "acciones.json"
    cfg.write_text(json.dumps({"version": 1, "acciones": [
        {"nombre": "limpiar", "descripcion": "d", "tipo": "borrar",
         "filtro": {"extensiones": [".tmp"]}}]}), encoding="utf-8")
    run = CliRunner()
    r = run.invoke(app, ["--config", str(cfg), "ejecutar", "limpiar", str(tmp_path)], input="n\n")
    assert r.exit_code != 0 and (tmp_path / "v.tmp").exists()
    r = run.invoke(app, ["--config", str(cfg), "ejecutar", "limpiar", str(tmp_path), "--simular"])
    assert r.exit_code == 0 and (tmp_path / "v.tmp").exists() and "SIMULACIÓN" in r.output
    r = run.invoke(app, ["--config", str(cfg), "ejecutar", "limpiar", str(tmp_path)], input="s\n")
    assert r.exit_code == 0 and not (tmp_path / "v.tmp").exists()


def test_cli_errores_sin_traza(tmp_path):
    cfg = tmp_path / "a.json"
    cfg.write_text(json.dumps({"version": 1, "acciones": [
        {"nombre": "m", "descripcion": "d", "tipo": "mover", "destino": "x"}]}), encoding="utf-8")
    run = CliRunner()
    r = run.invoke(app, ["--config", str(cfg), "ejecutar", "nada", str(tmp_path)])
    assert r.exit_code == 1 and "Traceback" not in r.output
    r = run.invoke(app, ["listar", str(tmp_path / "no-existe")])
    assert r.exit_code == 1


def test_ordenar_el_nombre_de_la_carpeta_tambien_cuenta(tmp_path):
    f = tmp_path / "apuntes bases datos.txt"
    f.write_text("x")
    o = Ordenar({"nombre": "o", "descripcion": "d", "tipo": "ordenar",
                 "carpetas": {"bases-datos": ["sql"]}})
    assert o.clasificar(f) == "bases-datos"


def test_cli_ordenar_con_confirmar_muestra_tabla_y_cuenta_solo_los_que_se_mueven(tmp_path):
    (tmp_path / "linux.txt").write_text("x"); (tmp_path / "misterio.txt").write_text("x")
    cfg = tmp_path / "a.json"
    cfg.write_text(json.dumps({"version": 1, "acciones": [
        {"nombre": "o", "descripcion": "d", "tipo": "ordenar", "confirmar": True,
         "carpetas": {"sistemas": ["linux"]}}]}), encoding="utf-8")
    run = CliRunner()
    r = run.invoke(app, ["--config", str(cfg), "ejecutar", "o", str(tmp_path)], input="n\n")
    assert r.exit_code != 0 and (tmp_path / "linux.txt").exists() and "1 fichero(s)" in r.output
    r = run.invoke(app, ["--config", str(cfg), "ejecutar", "o", str(tmp_path)], input="si\n")
    assert r.exit_code == 0 and (tmp_path / "sistemas" / "linux.txt").exists()
