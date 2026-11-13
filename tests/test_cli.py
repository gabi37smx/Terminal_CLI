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
    for texto in ("Ficheros", "Almacén", "Seguridad", "dam ejecutar", "dam sync"):
        assert texto in r.output
    # Los ejemplos están en la ayuda de cada comando
    detalle = runner.invoke(app, ["sync", "--help"])
    assert "dam sync --integrar" in detalle.output


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
        (bin_ / "dam", "dam"),
        (bin_ / "tareas", "tareas"),
        (bin_ / "tareas.exe", "tareas"),  # así lo llama Windows
        ("tareas", "tareas"),
    ]:
        monkeypatch.setattr("sys.argv", [str(argv0)])
        assert runner.invoke(app, ["version"]).output.strip() == f"{nombre} {__version__}", argv0


def test_version_tambien_como_opcion():
    """En un Linux de clase lo primero que se probó fue «dam --version» y daba error."""
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
    assert datos["project"]["scripts"]["tareas"] == datos["project"]["scripts"]["dam"]


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
    assert "si clonaste el repo" in salida and "dam --install-completion" in salida


# ---------- Un código de salida por prueba (Sesión 4, paso 5) ----------
def test_codigo_0_la_ayuda_funciona():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0 and "dam ejecutar" in r.output


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


# ---------- «dam --help | head» en Windows ----------
def _ayuda_que_falla(monkeypatch, error, salida_cerrada):
    from tareas import cli
    def romper():
        raise error
    monkeypatch.setattr(cli, "mostrar_ayuda", romper)
    monkeypatch.setattr(cli, "_salida_cerrada", lambda: salida_cerrada)
    monkeypatch.setattr(cli.os, "dup2", lambda *a: None)  # no tocar la salida de pytest
    monkeypatch.setattr("sys.argv", ["dam", "--help"])
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
