"""Pruebas de la ayuda principal y de la ayuda de cada subcomando."""

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

    assert __version__ == "1.0.0"
    monkeypatch.setattr("sys.argv", ["/home/alumno/.local/bin/dam"])
    assert runner.invoke(app, ["version"]).output.strip() == "dam 1.0.0"
    monkeypatch.setattr("sys.argv", [r"C:\Users\alumno\.local\bin\tareas.exe"])
    assert runner.invoke(app, ["version"]).output.strip() == "tareas 1.0.0"


def test_pyproject_y_paquete_tienen_la_misma_version():
    import tomllib
    from pathlib import Path

    from tareas import __version__

    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    datos = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert datos["project"]["version"] == __version__
    assert datos["project"]["scripts"]["tareas"] == datos["project"]["scripts"]["dam"]
