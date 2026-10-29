"""Pruebas de la ayuda principal y de la ayuda de cada subcomando."""

from typer.testing import CliRunner

from tareas.cli import app

runner = CliRunner()


def test_ayuda_principal_tiene_secciones_y_ejemplos():
    r = runner.invoke(app, ["--help"])
    assert r.exit_code == 0
    for texto in ("Uso:", "Comandos:", "Opciones:", "Ejemplos:"):
        assert texto in r.output
    assert "dam ejecutar ordenar --simular" in r.output
    assert "dam sync --integrar" in r.output


def test_ayuda_sin_argumentos():
    r = runner.invoke(app, [])
    assert r.exit_code == 0
    assert "Uso:" in r.output


def test_los_subcomandos_conservan_su_ayuda():
    for comando in ("version", "listar", "validar", "acciones", "ejecutar", "status", "sync"):
        r = runner.invoke(app, [comando, "--help"])
        assert r.exit_code == 0, f"{comando} no muestra ayuda"
        assert "Usage:" in r.output
