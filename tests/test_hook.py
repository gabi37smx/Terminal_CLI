import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import hook
from tareas.cli import app
from tareas.errores import TareasError

R = "aB3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0hJ3kL6"


@pytest.fixture(autouse=True)
def identidad(monkeypatch):
    for k, v in {"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@t.es",
                 "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@t.es"}.items():
        monkeypatch.setenv(k, v)


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-b", "main", str(tmp_path)], check=True, capture_output=True)
    return tmp_path


def git(repo: Path, *args):
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, encoding="utf-8")


def test_instalar_y_quitar(repo):
    destino = repo / ".git/hooks/pre-commit"
    assert "Hook instalado" in hook.instalar(repo)
    texto = destino.read_bytes().decode("utf-8")
    assert hook.MARCA in texto and "dam scan-secrets --staged" in texto and "\r" not in texto
    if sys.platform != "win32":
        assert destino.stat().st_mode & 0o111
    hook.instalar(repo)                       # repetir no da error
    assert hook.quitar(repo) == "Hook quitado." and not destino.exists()
    assert "nada que quitar" in hook.quitar(repo)


def test_no_pisa_un_hook_ajeno(repo):
    destino = repo / ".git/hooks/pre-commit"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("#!/bin/sh\necho mio\n")
    with pytest.raises(TareasError, match="no es de dam"):
        hook.instalar(repo)
    with pytest.raises(TareasError, match="no lo toco"):
        hook.quitar(repo)
    hook.instalar(repo, forzar=True)
    assert hook.MARCA in destino.read_text()


def test_fuera_de_un_repo(tmp_path):
    with pytest.raises(TareasError, match="no es un repositorio"):
        hook.instalar(tmp_path)


def test_cli(repo):
    run = CliRunner()
    assert run.invoke(app, ["instalar-hook", str(repo)]).exit_code == 0
    assert (repo / ".git/hooks/pre-commit").exists()
    assert run.invoke(app, ["instalar-hook", str(repo), "--quitar"]).exit_code == 0
    assert run.invoke(app, ["instalar-hook", str(repo / "nada")]).exit_code == 1


@pytest.mark.skipif(shutil.which("dam") is None, reason="el comando dam no está en el PATH de los tests")
def test_el_hook_bloquea_un_commit_con_clave_y_deja_pasar_uno_limpio(repo):
    hook.instalar(repo)
    (repo / "bien.md").write_text("hola", encoding="utf-8")
    git(repo, "add", "bien.md")
    assert git(repo, "commit", "-m", "limpio").returncode == 0
    (repo / "app.py").write_text("k = '" + "gh" + "p_" + R + "'\n", encoding="utf-8")
    git(repo, "add", "app.py")
    r = git(repo, "commit", "-m", "con clave")
    assert r.returncode != 0 and "Commit cancelado" in (r.stdout + r.stderr)
    assert git(repo, "commit", "--no-verify", "-m", "forzado").returncode == 0
