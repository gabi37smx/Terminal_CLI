"""La ayuda es parte del producto: cada comando debe aparecer, tener ejemplos y funcionar con -h y --help."""
import typer
import pytest
from typer.testing import CliRunner

from tareas.cli import EJEMPLOS, GRUPOS, app

run = CliRunner()
COMANDOS = sorted(typer.main.get_command(app).commands)


def test_todos_los_comandos_tienen_ejemplos_y_grupo():
    assert set(COMANDOS) == set(EJEMPLOS), "añade EJEMPLOS para el comando nuevo"
    agrupados = {n for _, nombres in GRUPOS for n in nombres}
    assert set(COMANDOS) == agrupados, "añade el comando nuevo a GRUPOS"


@pytest.mark.parametrize("args", [[], ["-h"], ["--help"]])
def test_ayuda_general_lista_todo(args):
    r = run.invoke(app, args)
    assert r.exit_code == 0
    for nombre in COMANDOS:
        assert f"dam {nombre}" in r.output
    for texto in ("--config", "DAM_ALMACEN", "Códigos de salida", "--integrar", "-m, --mensaje", "--simular"):
        assert texto in r.output
    assert "Traceback" not in r.output


@pytest.mark.parametrize("flag", ["-h", "--help"])
@pytest.mark.parametrize("nombre", COMANDOS)
def test_ayuda_de_cada_comando(nombre, flag):
    r = run.invoke(app, [nombre, flag])
    assert r.exit_code == 0, r.output
    assert "Ejemplos" in r.output
    assert f"dam {nombre}" in r.output
    assert "Traceback" not in r.output


def test_ayuda_de_sync_conserva_los_corchetes_y_esta_en_espanol():
    r = run.invoke(app, ["sync", "-h"])
    assert "[asignatura]: texto" in r.output
    assert "Argumentos" in r.output and "Opciones" in r.output


def test_error_de_uso_sale_con_2():
    assert run.invoke(app, ["ejecutar"]).exit_code == 2
    assert run.invoke(app, ["comando-que-no-existe"]).exit_code == 2
