"""Lo que no entendió el compañero de la instalación cruzada: ahora cada error dice qué escribir."""
import json

from typer.testing import CliRunner

from tareas.cli import accion_en_vez_de_comando, app
from tareas.motor import sugerir

run = CliRunner()


def escribir_config(carpeta, **ordenar):
    cfg = carpeta / "acciones.json"
    cfg.write_text(json.dumps({"version": 1, "acciones": [
        {"nombre": "ordenar", "descripcion": "d", "tipo": "ordenar", "origen": "~/pruebas-tareas/prueba-final",
         "carpetas": {"sistemas": ["linux"]}, **ordenar},
        {"nombre": "clasificar-asignatura", "descripcion": "d", "tipo": "clasificar",
         "categorias": ["sistemas", "otros"], "destino": "~/x"},
    ]}), encoding="utf-8")
    return cfg


def plano(texto: str) -> str:
    return " ".join(texto.split())


def test_sugerir_solo_si_esta_claro():
    acciones = ["ordenar", "clasificar-asignatura", "convertir-webp", "copiar-entregas"]
    assert sugerir("clasificar", acciones) == "clasificar-asignatura"   # empieza igual
    assert sugerir("ordenr", acciones) == "ordenar"                     # una letra mal
    assert sugerir("co", acciones) is None                              # dos empiezan por «co»: no se adivina
    assert sugerir("cocinar", acciones) is None


def test_una_accion_escrita_como_comando_da_la_orden_buena(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    escribir_config(tmp_path)
    assert accion_en_vez_de_comando(["ordenar", "~/Downloads"]) == (
        "ordenar", "mochila ejecutar ordenar ~/Downloads --simular")
    assert accion_en_vez_de_comando(["ordenar"]) == ("ordenar", "mochila ejecutar ordenar CARPETA --simular")
    assert accion_en_vez_de_comando(["clasificar", "."])[1] == "mochila ejecutar clasificar-asignatura . --simular"
    # con --config delante, la orden buena también lo lleva
    otra = tmp_path / "otra"
    otra.mkdir()
    cfg = escribir_config(otra)
    citada = f'"{cfg}"' if " " in str(cfg) else str(cfg)  # una ruta con espacios va entre comillas
    assert accion_en_vez_de_comando(["--config", str(cfg), "ordenar", "C:\\Mis apuntes"])[1] == (
        f'mochila --config {citada} ejecutar ordenar "C:\\Mis apuntes" --simular')


def test_lo_que_no_es_una_accion_sigue_su_camino(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    escribir_config(tmp_path)
    assert accion_en_vez_de_comando(["listar"]) is None        # es un comando de verdad
    assert accion_en_vez_de_comando(["cocinar"]) is None       # ni comando ni acción: el error de siempre
    assert accion_en_vez_de_comando(["--help"]) is None
    assert accion_en_vez_de_comando([]) is None


def test_sin_acciones_json_no_falla(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # y el HOME de conftest tampoco tiene ~/.config/mochila
    assert accion_en_vez_de_comando(["ordenar"]) is None


def test_ejecutar_sin_carpeta_explica_que_hay_que_decirla(tmp_path):
    cfg = escribir_config(tmp_path)
    r = run.invoke(app, ["--config", str(cfg), "ejecutar", "ordenar", "--simular"])
    assert r.exit_code == 1
    salida = plano(r.output)
    assert "Dime qué carpeta o fichero: mochila ejecutar ordenar CARPETA" in salida
    assert "un punto, «.», es la carpeta en la que estás" in salida
    assert "Traceback" not in r.output


def test_ejecutar_una_accion_que_no_existe_propone_la_parecida(tmp_path):
    cfg = escribir_config(tmp_path)
    r = run.invoke(app, ["--config", str(cfg), "ejecutar", "clasificar", "."])
    assert r.exit_code == 1
    assert "¿Querías decir «clasificar-asignatura»?" in plano(r.output)


def test_ordenar_al_almacen_sin_almacen_dice_como_crearlo(tmp_path, monkeypatch):
    cfg = escribir_config(tmp_path, al_almacen=True)
    (tmp_path / "Descargas").mkdir()
    monkeypatch.setenv("MOCHILA_ALMACEN", str(tmp_path / "DAW-almacen"))
    r = run.invoke(app, ["--config", str(cfg), "ejecutar", "ordenar", str(tmp_path / "Descargas"), "--simular"])
    assert r.exit_code == 1 and "Prepáralo con: mochila crear-almacen" in plano(r.output)
    (tmp_path / "DAW-almacen").mkdir()  # ya está, pero sin asignaturas/
    r = run.invoke(app, ["--config", str(cfg), "ejecutar", "ordenar", str(tmp_path / "Descargas"), "--simular"])
    assert r.exit_code == 1
    assert "aún no tiene las carpetas de tus asignaturas. Créalas con: mochila configurar" in plano(r.output)
