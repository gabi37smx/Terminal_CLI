"""La ayuda es parte del producto: cada comando debe aparecer, tener ejemplos y funcionar con -h y --help."""
import typer
import pytest
from typer.testing import CliRunner

from tareas.cli import EJEMPLOS, GRUPOS, app

run = CliRunner()
COMANDOS = sorted(typer.main.get_command(app).commands)


def test_todos_los_comandos_tienen_ejemplos_y_grupo():
    assert set(COMANDOS) == set(EJEMPLOS), "añade EJEMPLOS para el comando nuevo"
    agrupados = {n for _, _, nombres in GRUPOS for n in nombres}
    assert set(COMANDOS) == agrupados, "añade el comando nuevo a GRUPOS"


@pytest.mark.parametrize("args", [[], ["-h"], ["--help"]])
def test_ayuda_general_lista_todo(args, monkeypatch):
    from tareas import cli
    monkeypatch.setattr(cli.consola, "width", 120)  # un terminal normal: la tabla no depende de COLUMNS
    r = run.invoke(app, args)
    assert r.exit_code == 0
    for nombre in COMANDOS:
        assert f"dam {nombre}" in r.output
    for texto in ("dam help COMANDO", "--config"):
        assert texto in r.output
    # La ayuda general es corta: las opciones y los ejemplos van en dam help COMANDO
    assert "--integrar" not in r.output
    assert len(r.output.splitlines()) < 40
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


def test_dam_help_es_el_manual_completo():
    r = run.invoke(app, ["help"])
    assert r.exit_code == 0
    assert r.output == run.invoke(app, ["--help"]).output


def test_dam_help_comando_es_su_ayuda_detallada():
    r = run.invoke(app, ["help", "sync"])
    assert r.exit_code == 0, r.output
    assert "Ejemplos" in r.output and "--integrar" in r.output
    assert "Traceback" not in r.output


def test_dam_help_de_un_comando_que_no_existe_sale_con_2():
    r = run.invoke(app, ["help", "no-existe"])
    assert r.exit_code == 2
    assert "No existe el comando" in r.output


# ---------- una \ antes de las comillas de cierre (Windows) ----------
from tareas.cli import ruta_con_comillas_metidas  # noqa: E402


@pytest.mark.parametrize("argumentos, esperado", [
    (["doctor", r'C:\Users\HP\PROJECTE TERMINAL CLI"'], r'dam doctor "C:\Users\HP\PROJECTE TERMINAL CLI"'),
    # lo que va detrás se pega a la ruta: se separa otra vez
    (["entregar", r'C:\mi proyecto" --simular'], r'dam entregar "C:\mi proyecto" --simular'),
    (["listar", r'.\carpeta"'], r'dam listar ".\carpeta"'),
])
def test_detecta_la_ruta_con_comillas_metidas(argumentos, esperado):
    assert ruta_con_comillas_metidas(argumentos) == esperado


@pytest.mark.parametrize("argumentos", [
    ["doctor", r"C:\Users\HP\proyecto"],
    ["sync", "-m", 'arreglo del "menú"'],  # un mensaje con comillas no es una ruta
    [],
])
def test_no_molesta_con_argumentos_normales(argumentos):
    assert ruta_con_comillas_metidas(argumentos) is None


def test_dam_explica_la_barra_final_y_sale_con_2(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["dam", "doctor", r'C:\Users\HP\mi proyecto"'])
    with pytest.raises(SystemExit) as salida:
        app()
    assert salida.value.code == 2
    texto = " ".join(capsys.readouterr().err.split())  # Rich puede partir la línea
    assert "comillas metidas" in texto
    assert r'dam doctor "C:\Users\HP\mi proyecto"' in texto
