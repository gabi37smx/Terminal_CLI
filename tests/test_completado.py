"""Autocompletado con TAB: se simula lo que hace bash al pulsar TAB (variables COMP_WORDS y COMP_CWORD)."""
import json

from typer.testing import CliRunner

from tareas.cli import app

run = CliRunner()


def tab(linea: str, env: dict | None = None) -> list[str]:
    """Lo que dam sugeriría al pulsar TAB al final de «linea»."""
    palabras = linea.split(" ")
    entorno = {
        "_DAM_COMPLETE": "complete_bash",
        "COMP_WORDS": linea,
        "COMP_CWORD": str(len(palabras) - 1),
        **(env or {}),
    }
    r = run.invoke(app, [], env=entorno, prog_name="dam")
    assert r.exit_code == 0, r.output
    assert "Traceback" not in r.output
    return r.output.split()


def escribir_config(carpeta, acciones):
    (carpeta / "acciones.json").write_text(
        json.dumps({"version": 1, "acciones": acciones}), encoding="utf-8"
    )


def test_completa_los_comandos():
    assert {"status", "sync", "scan-secrets"} <= set(tab("dam s"))


def test_completa_los_nombres_de_las_acciones(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # dam busca primero ./acciones.json
    escribir_config(tmp_path, [
        {"nombre": "limpiar", "descripcion": "Borra .tmp", "tipo": "borrar",
         "filtro": {"extensiones": [".tmp"]}},
        {"nombre": "copiar-fotos", "descripcion": "Copia fotos", "tipo": "copiar",
         "destino": "~/pruebas-tareas/copia"},
    ])
    assert tab("dam ejecutar ") == ["limpiar", "copiar-fotos"]
    assert tab("dam ejecutar co") == ["copiar-fotos"]


def test_con_acciones_json_roto_no_sugiere_nada_ni_falla(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "acciones.json").write_text("{ esto no es json", encoding="utf-8")
    assert tab("dam ejecutar ") == []
    assert tab("dam --config no-existe.json ejecutar ") == []


def test_completa_las_asignaturas_del_almacen(tmp_path):
    asignaturas = tmp_path / "asignaturas"
    for nombre in ("programacion", "proyecto", "sistemas", "documentacio", ".oculta"):
        (asignaturas / nombre).mkdir(parents=True)
    (asignaturas / "notas.txt").write_text("no es una carpeta", encoding="utf-8")
    env = {"DAM_ALMACEN": str(tmp_path)}
    # documentacio nunca se sube, las ocultas tampoco se ofrecen y los ficheros no son asignaturas
    assert tab("dam status ", env) == ["programacion", "proyecto", "sistemas"]
    assert tab("dam sync pr", env) == ["programacion", "proyecto"]


def test_sin_almacen_no_sugiere_nada_ni_falla(tmp_path):
    assert tab("dam status ", {"DAM_ALMACEN": str(tmp_path / "no-existe")}) == []


def test_el_manual_explica_las_opciones_de_autocompletado_en_espanol():
    r = run.invoke(app, ["--help"])
    assert "--install-completion" in r.output and "Activa el TAB" in r.output
    assert "--show-completion" in r.output
