"""Tests extra del almacén: opción -m, pista de mensaje, claves privadas y carpeta Documentacio.
Fichero independiente (no depende de test_sincronizar.py)."""
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas.cli import app
from tareas.errores import TareasError
from tareas.sincronizar import Almacen


@pytest.fixture(autouse=True)
def identidad(monkeypatch):
    for k, v in {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@t.es",
                 "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@t.es"}.items():
        monkeypatch.setenv(k, v)


def git(carpeta: Path, *args):
    return subprocess.run(["git", "-C", str(carpeta), *args], check=True,
                          capture_output=True, text=True, encoding="utf-8").stdout


def escribir(ruta: Path, texto="x"):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


@pytest.fixture
def pcs(tmp_path):
    remoto = tmp_path / "github.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(remoto)], check=True, capture_output=True)
    clase = tmp_path / "clase"
    subprocess.run(["git", "init", "-b", "main", str(clase)], check=True, capture_output=True)
    escribir(clase / "asignaturas/programacion/tema1.md", "uno")
    escribir(clase / "asignaturas/bd/tema1.md", "uno")
    git(clase, "add", "-A"); git(clase, "commit", "-m", "inicial")
    git(clase, "remote", "add", "origin", str(remoto)); git(clase, "push", "-u", "origin", "main")
    return Almacen(clase), None


def test_sync_con_opcion_m_para_todo_el_almacen(pcs):
    clase, _ = pcs
    escribir(clase.ruta / "asignaturas/bd/x.md")
    r = CliRunner().invoke(app, ["sync", "-m", "lo que he hecho", "--almacen", str(clase.ruta)])
    assert r.exit_code == 0, r.output
    assert git(clase.ruta, "log", "-1", "--format=%s").strip() == "[sync]: lo que he hecho"


def test_asignatura_inexistente_sugiere_la_opcion_m(pcs):
    clase, _ = pcs
    with pytest.raises(TareasError, match=r'dam sync -m'):
        clase.sincronizar("tema 3", None)


def test_no_sube_claves_privadas(pcs):
    clase, _ = pcs
    for nombre in ("servidor.pem", "id_rsa", "cert.PFX"):
        escribir(clase.ruta / "asignaturas/bd" / nombre, "secreto")
        with pytest.raises(TareasError, match="secretos"):
            clase.sincronizar(None, "m")
        (clase.ruta / "asignaturas/bd" / nombre).unlink()
    escribir(clase.ruta / "asignaturas/bd/id_rsa.pub", "publica")
    assert clase.sincronizar(None, "m").estado == "subido"


def test_documentacio_nunca_se_sube(pcs):
    clase, _ = pcs
    escribir(clase.ruta / "asignaturas/bd/Documentació/apuntes.pdf")
    escribir(clase.ruta / "asignaturas/bd/real.md")
    assert {c.ruta for c in clase.analizar().locales} == {"asignaturas/bd/real.md"}
    clase.sincronizar(None, "m")
    assert "Documentaci" not in git(clase.ruta, "ls-files")
