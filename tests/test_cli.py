"""Pruebas de la ayuda principal y de la ayuda de cada subcomando."""

import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas.cli import app

runner = CliRunner()


def test_ayuda_principal_tiene_secciones_y_ejemplos():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    for texto in ("Ficheros", "Almacén", "Seguridad", "mochila ejecutar", "mochila sync"):
        assert texto in r.output
    # Los ejemplos están en la ayuda de cada comando
    detalle = runner.invoke(app, ["sync", "--help"])
    assert "mochila sync --integrar" in detalle.output


def test_ayuda_sin_argumentos():
    r = runner.invoke(app, [])
    assert r.exit_code == 0
    assert "Uso:" in r.output


def test_los_subcomandos_conservan_su_ayuda():
    for comando in ("version", "listar", "validar", "acciones", "ejecutar", "status", "sync"):
        r = runner.invoke(app, [comando, "--help"])
        assert r.exit_code == 0, f"{comando} no muestra ayuda"
        assert "Usage:" in r.output


def test_version_con_los_dos_nombres(monkeypatch):
    from tareas import __version__

    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)  # versionado semántico: X.Y.Z
    bin_ = Path.home() / ".local" / "bin"  # rutas del sistema donde corre la prueba
    for argv0, nombre in [
        (bin_ / "mochila", "mochila"),
        (bin_ / "tareas", "tareas"),
        (bin_ / "tareas.exe", "tareas"),  # así lo llama Windows
        ("tareas", "tareas"),
    ]:
        monkeypatch.setattr("sys.argv", [str(argv0)])
        assert runner.invoke(app, ["version"]).output.strip() == f"{nombre} {__version__}", argv0


def test_version_tambien_como_opcion():
    """En un Linux de clase lo primero que se probó fue «mochila --version» y daba error."""
    from tareas import __version__

    for opcion in ("--version", "-V"):
        r = runner.invoke(app, [opcion])
        assert r.exit_code == 0, opcion
        assert r.output.strip().endswith(__version__), opcion


def test_pyproject_y_paquete_tienen_la_misma_version():
    import tomllib

    from tareas import __version__

    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    datos = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert datos["project"]["version"] == __version__
    assert datos["project"]["scripts"]["tareas"] == datos["project"]["scripts"]["mochila"]
    assert "dam" not in datos["project"]["scripts"]  # el comando ya no se llama dam: confundía a los de DAW


def test_las_variables_con_el_nombre_antiguo_siguen_valiendo(monkeypatch):
    from tareas import config

    monkeypatch.setenv("DAM_ALMACEN", "/viejo")
    assert config.entorno("ALMACEN") == "/viejo"
    monkeypatch.setenv("MOCHILA_ALMACEN", "/nuevo")
    assert config.entorno("ALMACEN") == "/nuevo"  # si están las dos, manda la nueva


@pytest.mark.parametrize(
    "orden, esperado",
    [
        (["versiones"], "No existe el comando «versiones». ¿Querías decir 'version'?"),
        (["--opcion-falsa"], "No existe la opción --opcion-falsa"),
        (["listar", "--niveles"], "No existe la opción --niveles"),
        (["ejecutar"], "Falta el argumento 'NOMBRE'."),
    ],
)
def test_errores_de_uso_en_espanol(orden, esperado):  # issue #20
    r = runner.invoke(app, orden)
    salida = " ".join(r.output.split())
    assert r.exit_code == 2
    assert esperado in salida
    assert "No such" not in salida and "Missing" not in salida and "Did you mean" not in salida


@pytest.mark.parametrize(
    "ingles, espanol",
    [
        ("Option '--calidad' requires an argument.", "La opción '--calidad' necesita un valor."),
        ("Got unexpected extra argument(s) (b c)", "Sobra: b c"),
        ("Invalid value for '--niveles': 'x' is not a valid integer.",
         "Valor no válido para '--niveles': 'x' no es un número entero."),
        ("Did you mean one of 'sync', 'status'?", "¿Querías decir uno de estos: 'sync', 'status'?"),
        ("Un mensaje que no está en la lista", "Un mensaje que no está en la lista"),
    ],
)
def test_traducir_error_click(ingles, espanol):
    from tareas.cli import traducir_error_click

    assert traducir_error_click(ingles) == espanol


def test_la_ayuda_dice_que_tareas_es_el_mismo_programa_y_el_tab_sin_clonar():  # issue #20
    salida = " ".join(runner.invoke(app, ["--help"]).output.split())
    assert "«tareas»: es el mismo programa" in salida
    assert "si clonaste el repo" in salida and "mochila --install-completion" in salida


# ---------- Un código de salida por prueba (Sesión 4, paso 5) ----------
def test_codigo_0_la_ayuda_funciona():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0 and "mochila ejecutar" in r.output


def test_codigo_1_accion_que_no_existe(escribir_config, tmp_path):
    cfg = escribir_config([{"nombre": "mover-pdf", "descripcion": "d", "tipo": "mover", "destino": "PDF"}])
    r = runner.invoke(app, ["--config", str(cfg), "ejecutar", "no-existe", str(tmp_path)])
    assert r.exit_code == 1 and "no-existe" in r.output and "Traceback" not in r.output


def test_codigo_2_opcion_que_no_existe():
    r = runner.invoke(app, ["listar", "--niveles"])
    assert r.exit_code == 2 and "No existe la opción --niveles" in " ".join(r.output.split())


def test_codigo_3_json_roto_sin_traza(escribir_config):
    cfg = escribir_config('{"version": 1,\n  "acciones": [}')
    r = runner.invoke(app, ["--config", str(cfg), "validar"])
    assert r.exit_code == 3 and "línea" in r.output and "Traceback" not in r.output


def test_codigo_4_ia_sin_clave_y_las_demas_siguen(escribir_config, tmp_path):
    (tmp_path / "Apuntes").mkdir()
    (tmp_path / "Apuntes" / "tema1.txt").write_text("La CPU y la memoria", encoding="utf-8")
    cfg = escribir_config([{"nombre": "resumir-tema", "descripcion": "Resume", "tipo": "resumir"}])
    r = runner.invoke(app, ["--config", str(cfg), "ejecutar", "resumir-tema", str(tmp_path / "Apuntes"), "--si"])
    salida = " ".join(r.output.split())
    assert r.exit_code == 4 and "Las acciones sin IA siguen funcionando" in salida and "Traceback" not in salida


# ---------- «mochila --help | head» en Windows ----------
def _ayuda_que_falla(monkeypatch, error, salida_cerrada):
    from tareas import cli
    def romper():
        raise error
    monkeypatch.setattr(cli, "mostrar_ayuda", romper)
    monkeypatch.setattr(cli, "_salida_cerrada", lambda: salida_cerrada)
    monkeypatch.setattr(cli.os, "dup2", lambda *a: None)  # no tocar la salida de pytest
    monkeypatch.setattr("sys.argv", ["mochila", "--help"])
    return cli.app


def test_si_quien_lee_la_salida_se_va_no_hay_traza(monkeypatch):
    app_ = _ayuda_que_falla(monkeypatch, OSError(22, "Invalid argument"), salida_cerrada=True)
    with pytest.raises(SystemExit) as e:
        app_()
    assert e.value.code == 0


def test_otro_oserror_no_se_esconde(monkeypatch):
    app_ = _ayuda_que_falla(monkeypatch, OSError(22, "Invalid argument"), salida_cerrada=False)
    with pytest.raises(OSError):
        app_()


# ---------- preguntas s/n: lo que no se entiende se vuelve a preguntar (instalación cruzada, 26-nov) ----------
@pytest.mark.parametrize("respuestas, por_defecto, esperado, avisos", [
    (["7", "s"], False, True, 1),        # «7» en un [s/N]: lo dice y vuelve a preguntar
    (["sw", "n"], True, False, 1),       # errata en un [S/n]: ya no cancela en silencio
    (["sw", "", ], True, True, 1),       # tras el aviso, Enter sigue siendo lo de la mayúscula
    (["no"], True, False, 0),
    (["Sí"], False, True, 0),
])
def test_una_respuesta_que_no_es_si_ni_no_se_vuelve_a_preguntar(monkeypatch, respuestas, por_defecto, esperado, avisos):
    from tareas import cli
    pendientes = list(respuestas)
    monkeypatch.setattr(cli.typer, "prompt", lambda *a, **k: pendientes.pop(0))
    impreso = []
    monkeypatch.setattr(cli.consola, "print", lambda texto, *a, **k: impreso.append(texto))
    assert cli.preguntar("¿Lo guardo?", si_por_defecto=por_defecto) is esperado
    assert pendientes == []
    assert sum("No te he entendido" in t for t in impreso) == avisos


def test_si_se_acaba_la_entrada_tras_una_respuesta_rara_se_cancela(monkeypatch):
    # Lo señaló el revisor: con «7» y luego sin más entrada (una tubería) no se queda en bucle:
    # typer.prompt lanza Abort, como antes con la entrada vacía, y la orden se cancela sin hacer nada.
    import typer as typer_
    from tareas import cli
    pendientes = ["7"]

    def prompt(*a, **k):
        if not pendientes:
            raise typer_.Abort()
        return pendientes.pop(0)
    monkeypatch.setattr(cli.typer, "prompt", prompt)
    monkeypatch.setattr(cli.consola, "print", lambda *a, **k: None)
    with pytest.raises(typer_.Abort):
        cli.preguntar("¿Lo borro?")

