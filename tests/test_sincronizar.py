"""Pruebas del almacén con un «GitHub» falso (repo bare local) y dos «PCs» (clase y casa).
Nunca tocan tu repo real: todo ocurre dentro de tmp_path."""
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas.cli import app
from tareas.errores import GitError, TareasError
from tareas.sincronizar import Almacen, traducir_error


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
    casa = tmp_path / "casa"
    subprocess.run(["git", "clone", str(remoto), str(casa)], check=True, capture_output=True)
    return Almacen(clase), Almacen(casa)


def test_todo_actualizado(pcs):
    clase, _ = pcs
    assert clase.sincronizar(None, None).estado == "actualizado"


def test_status_clasifica_modificados_nuevos_y_borrados(pcs):
    clase, _ = pcs
    escribir(clase.ruta / "asignaturas/programacion/tema1.md", "cambiado")
    escribir(clase.ruta / "asignaturas/bd/nuevo.md")
    (clase.ruta / "asignaturas/bd/tema1.md").unlink()
    s = clase.analizar()
    assert {(c.estado, c.ruta) for c in s.locales} == {
        ("modificado", "asignaturas/programacion/tema1.md"),
        ("nuevo", "asignaturas/bd/nuevo.md"),
        ("borrado", "asignaturas/bd/tema1.md")}


def test_solo_local_hace_add_commit_push_con_mensaje(pcs):
    clase, casa = pcs
    escribir(clase.ruta / "asignaturas/programacion/tema2.md")
    r = clase.sincronizar("programacion", "añade tema 2")
    assert r.estado == "subido"
    assert git(clase.ruta, "log", "-1", "--format=%s").strip() == "[programacion]: añade tema 2"
    assert casa.sincronizar(None, None).estado == "descargado"
    assert (casa.ruta / "asignaturas/programacion/tema2.md").exists()


def test_solo_remoto_hace_pull(pcs):
    clase, casa = pcs
    escribir(clase.ruta / "asignaturas/bd/tema2.md"); clase.sincronizar(None, "bd")
    s = casa.analizar()
    assert s.hay_remoto and not s.hay_local and s.remotos[0].ruta == "asignaturas/bd/tema2.md"
    assert casa.sincronizar(None, None).estado == "descargado"


def test_filtro_por_asignatura_limita_el_add(pcs):
    clase, _ = pcs
    escribir(clase.ruta / "asignaturas/programacion/a.md")
    escribir(clase.ruta / "asignaturas/bd/b.md")
    clase.sincronizar("programacion", "solo prog")
    pendientes = {c.ruta for c in clase.analizar().locales}
    assert pendientes == {"asignaturas/bd/b.md"}


def test_asignatura_inexistente_o_con_ruta_rara(pcs):
    clase, _ = pcs
    with pytest.raises(TareasError, match="Hay: bd, programacion"):
        clase.sincronizar("matematicas", None)
    with pytest.raises(TareasError, match="no es un nombre"):
        clase.analizar("../fuera")


def test_ambos_se_detiene_y_no_toca_nada(pcs):
    clase, casa = pcs
    escribir(casa.ruta / "asignaturas/bd/remoto.md"); casa.sincronizar(None, "desde casa")
    escribir(clase.ruta / "asignaturas/programacion/local.md")
    antes = git(clase.ruta, "rev-parse", "HEAD")
    r = clase.sincronizar(None, None)
    assert r.estado == "pendiente" and "Cambios en GitHub" in r.detalle
    assert git(clase.ruta, "rev-parse", "HEAD") == antes
    assert (clase.ruta / "asignaturas/programacion/local.md").exists()
    assert not (clase.ruta / "asignaturas/bd/remoto.md").exists()


def test_integrar_une_cambios_distintos(pcs):
    clase, casa = pcs
    escribir(casa.ruta / "asignaturas/bd/remoto.md"); casa.sincronizar(None, "desde casa")
    escribir(clase.ruta / "asignaturas/programacion/local.md")
    assert clase.sincronizar(None, "desde clase", integrar=True).estado == "integrado"
    assert (clase.ruta / "asignaturas/bd/remoto.md").exists()
    assert casa.sincronizar(None, None).estado == "descargado"
    assert (casa.ruta / "asignaturas/programacion/local.md").exists()


def test_integrar_con_conflicto_deshace_y_no_pierde_nada(pcs):
    clase, casa = pcs
    f = "asignaturas/programacion/tema1.md"
    escribir(casa.ruta / f, "version casa"); casa.sincronizar(None, "casa")
    escribir(clase.ruta / f, "version clase")
    with pytest.raises(GitError, match="Conflicto real"):
        clase.sincronizar(None, "clase", integrar=True)
    assert not (clase.ruta / ".git/rebase-merge").exists()
    assert not (clase.ruta / ".git/rebase-apply").exists()
    assert (clase.ruta / f).read_text() == "version clase"
    assert "clase" in git(clase.ruta, "log", "-1", "--format=%s")


def test_simular_no_cambia_nada(pcs):
    clase, _ = pcs
    escribir(clase.ruta / "asignaturas/bd/x.md")
    antes = git(clase.ruta, "rev-parse", "HEAD")
    r = clase.sincronizar(None, "m", simular=True)
    assert r.simulado and r.estado == "subido"
    assert git(clase.ruta, "rev-parse", "HEAD") == antes
    assert {c.estado for c in clase.analizar().locales} == {"nuevo"}


def test_no_sube_env_ni_ficheros_enormes(pcs, monkeypatch):
    clase, _ = pcs
    escribir(clase.ruta / "asignaturas/bd/.env", "CLAVE=1")
    with pytest.raises(TareasError, match="secretos"):
        clase.sincronizar(None, "m")
    (clase.ruta / "asignaturas/bd/.env").unlink()
    monkeypatch.setattr("tareas.sincronizar.MAX_MB", 0)
    escribir(clase.ruta / "asignaturas/bd/grande.bin", "algo")
    with pytest.raises(TareasError, match="pesa más"):
        clase.sincronizar(None, "m")
    assert git(clase.ruta, "log", "--oneline").count("\n") == 1  # no hubo commit


def test_nombres_con_tildes_y_espacios(pcs):
    clase, casa = pcs
    escribir(clase.ruta / "asignaturas/programacion/Práctica nº 1 (ñandú).md")
    clase.sincronizar(None, "tildes")
    casa.sincronizar(None, None)
    assert (casa.ruta / "asignaturas/programacion/Práctica nº 1 (ñandú).md").exists()


def test_status_sin_conexion_sigue_funcionando(pcs, tmp_path):
    clase, _ = pcs
    git(clase.ruta, "remote", "set-url", "origin", str(tmp_path / "no-existe.git"))
    escribir(clase.ruta / "asignaturas/bd/x.md")
    s = clase.analizar(tolerante=True)
    assert s.sin_conexion and s.locales
    with pytest.raises(GitError):
        clase.analizar(tolerante=False)


def test_rama_sin_remoto_o_carpeta_que_no_es_repo(tmp_path):
    with pytest.raises(GitError, match="no existe en este equipo"):
        Almacen(tmp_path / "nada").comprobar()
    (tmp_path / "vacia").mkdir()
    with pytest.raises(GitError, match="no es un repositorio"):
        Almacen(tmp_path / "vacia").comprobar()


@pytest.mark.parametrize("texto, esperado", [
    ("fatal: unable to access 'https://github.com/x': Could not resolve host: github.com", "Sin conexión"),
    ("fatal: Authentication failed for 'https://github.com/x'", "no te reconoce"),
    ("fatal: unable to access 'https://github.com/x': The requested URL returned error: 403", "no te reconoce"),
    (" ! [rejected] main -> main (fetch first)", "desactualizada"),
    ("fatal: detected dubious ownership in repository", "safe.directory"),
    ("Please tell me who you are.", "user.name"),
])
def test_traduccion_de_errores(texto, esperado):
    assert esperado in traducir_error(texto)


def test_cli_status_y_sync(pcs, tmp_path):
    clase, casa = pcs
    escribir(clase.ruta / "asignaturas/bd/nuevo.md")
    r = CliRunner().invoke(app, ["status", "--almacen", str(clase.ruta)])
    assert r.exit_code == 0 and "nuevo.md" in r.output and "Archivos nuevos" in r.output
    escribir(casa.ruta / "asignaturas/bd/otro.md"); casa.sincronizar(None, "casa")
    r = CliRunner().invoke(app, ["status", "--almacen", str(clase.ruta)])
    assert "Peligro" in r.output
    r = CliRunner().invoke(app, ["sync", "--almacen", str(clase.ruta)])
    assert r.exit_code == 1 and "No hago nada automático" in r.output
    r = CliRunner().invoke(app, ["sync", "--integrar", "--almacen", str(clase.ruta)])
    assert r.exit_code == 0


def test_cli_sin_almacen_configurado(tmp_path, monkeypatch):
    monkeypatch.delenv("DAM_ALMACEN", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path)); monkeypatch.setenv("USERPROFILE", str(tmp_path))
    r = CliRunner().invoke(app, ["status"])
    assert r.exit_code == 3 and "No sé dónde está tu almacén" in r.output


def test_cli_almacen_por_variable_de_entorno(pcs, monkeypatch):
    clase, _ = pcs
    monkeypatch.setenv("DAM_ALMACEN", str(clase.ruta))
    r = CliRunner().invoke(app, ["status"])
    assert r.exit_code == 0 and "Todo está actualizado" in r.output
