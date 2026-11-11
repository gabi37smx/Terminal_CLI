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
