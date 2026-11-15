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
def test_ayuda_corta_cabe_en_una_pantalla(args, monkeypatch):
    from tareas import cli
    monkeypatch.setattr(cli.consola, "width", 80)  # el terminal más estrecho de lo normal
    r = run.invoke(app, args)
    assert r.exit_code == 0
    palabras = set(r.output.replace("·", " ").split())
    assert set(COMANDOS) <= palabras  # todos los comandos, aunque sea solo su nombre
    assert "mochila ejecutar ordenar . --simular" in r.output  # lo más usado, con su carpeta
    assert "mochila help" in r.output and "mochila help COMANDO" in r.output
    # Corta: ni opciones ni ejemplos de cada comando (eso va en mochila help)
    assert "--integrar" not in r.output and "$ mochila" not in r.output
    assert len(r.output.splitlines()) <= 27
    assert "Traceback" not in r.output


def test_la_guia_larga_explica_cada_comando_con_un_ejemplo(monkeypatch):
    from tareas import cli
    monkeypatch.setattr(cli.consola, "width", 100)
    r = run.invoke(app, ["help"])
    assert r.exit_code == 0
    for nombre in COMANDOS:
        assert f"mochila {nombre}" in r.output
    for orden, _ in cli.PRIMEROS_PASOS:
        assert orden in r.output
    assert "$ mochila ejecutar ordenar . --simular" in r.output and "$ mochila sync --simular" in r.output
    assert "Trucos" in r.output and "--config" in r.output and "--simular" in r.output
    assert "mochila help COMANDO" in r.output
    assert "Traceback" not in r.output


def test_los_ejemplos_de_ejecutar_dicen_la_carpeta():
    # Sin carpeta, ejecutar usa la de la acción, que es de pruebas: justo lo que confundió en la
    # instalación cruzada. En los ejemplos, siempre detrás del nombre de la acción.
    from tareas import cli
    ordenes = [c for lista in cli.EJEMPLOS.values() for c, _ in lista]
    ordenes += [c for c, _ in cli.MAS_USADO + cli.PRIMEROS_PASOS] + [c for c in cli.EJEMPLO_GUIA.values() if c]
    for orden in ordenes:
        partes = orden.split()
        if "ejecutar" in partes and partes[-1] not in ("-h", "--help"):
            detras = partes[partes.index("ejecutar") + 2:]
            assert detras and not detras[0].startswith("-"), orden


@pytest.mark.parametrize("flag", ["-h", "--help"])
@pytest.mark.parametrize("nombre", COMANDOS)
def test_ayuda_de_cada_comando(nombre, flag):
    r = run.invoke(app, [nombre, flag])
    assert r.exit_code == 0, r.output
    assert "Ejemplos" in r.output
    assert f"mochila {nombre}" in r.output
    assert "Traceback" not in r.output


def test_ayuda_de_sync_conserva_los_corchetes_y_esta_en_espanol():
    r = run.invoke(app, ["sync", "-h"])
    assert "[asignatura]: texto" in r.output
    assert "Argumentos" in r.output and "Opciones" in r.output


def test_error_de_uso_sale_con_2():
    assert run.invoke(app, ["ejecutar"]).exit_code == 2
    assert run.invoke(app, ["comando-que-no-existe"]).exit_code == 2


def test_mochila_help_es_la_guia_larga_y_help_la_corta():
    larga = run.invoke(app, ["help"])
    corta = run.invoke(app, ["--help"])
    assert larga.exit_code == corta.exit_code == 0
    assert len(larga.output.splitlines()) > 2 * len(corta.output.splitlines())


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
    (["doctor", r'C:\Users\HP\PROJECTE TERMINAL CLI"'], r'mochila doctor "C:\Users\HP\PROJECTE TERMINAL CLI"'),
    # lo que va detrás se pega a la ruta: se separa otra vez
    (["entregar", r'C:\mi proyecto" --simular'], r'mochila entregar "C:\mi proyecto" --simular'),
    (["listar", r'.\carpeta"'], r'mochila listar ".\carpeta"'),
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
    monkeypatch.setattr("sys.argv", ["mochila", "doctor", r'C:\Users\HP\mi proyecto"'])
    with pytest.raises(SystemExit) as salida:
        app()
    assert salida.value.code == 2
    texto = " ".join(capsys.readouterr().err.split())  # Rich puede partir la línea
    assert "comillas metidas" in texto
    assert r'mochila doctor "C:\Users\HP\mi proyecto"' in texto
