import os
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
    assert hook.MARCA in texto and "mochila scan-secrets --staged" in texto and "\r" not in texto
    if sys.platform != "win32":
        assert destino.stat().st_mode & 0o111
    hook.instalar(repo)                       # repetir no da error
    assert hook.quitar(repo) == "Hook quitado." and not destino.exists()
    assert "nada que quitar" in hook.quitar(repo)


def test_no_pisa_un_hook_ajeno(repo):
    destino = repo / ".git/hooks/pre-commit"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("#!/bin/sh\necho mio\n")
    with pytest.raises(TareasError, match="no es de mochila"):
        hook.instalar(repo)
    with pytest.raises(TareasError, match="no lo toco"):
        hook.quitar(repo)
    hook.instalar(repo, forzar=True)
    assert hook.MARCA in destino.read_text()


def test_el_hook_de_cuando_se_llamaba_dam_tambien_es_nuestro(repo):
    # Los almacenes que ya tenían el hook de «dam» se pasan al de mochila sin --forzar
    destino = repo / ".git/hooks/pre-commit"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("#!/bin/sh\n# dam-hook: scan-secrets\ndam scan-secrets --staged\n")
    hook.instalar(repo)
    assert hook.MARCA in destino.read_text() and "mochila scan-secrets" in destino.read_text()
    destino.write_text("#!/bin/sh\n# dam-hook: scan-secrets\n")
    assert hook.quitar(repo) == "Hook quitado."


def test_fuera_de_un_repo(tmp_path):
    with pytest.raises(TareasError, match="no es un repositorio"):
        hook.instalar(tmp_path)


def test_cli(repo):
    run = CliRunner()
    assert run.invoke(app, ["instalar-hook", str(repo)]).exit_code == 0
    assert (repo / ".git/hooks/pre-commit").exists()
    assert run.invoke(app, ["instalar-hook", str(repo), "--quitar"]).exit_code == 0
    assert run.invoke(app, ["instalar-hook", str(repo / "nada")]).exit_code == 1


@pytest.mark.skipif(shutil.which("mochila") is None, reason="el comando mochila no está en el PATH de los tests")
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


# --- Con --revisor: el agente revisor mira cada commit con código -----------------------------------

def revisor_de_mentira(repo: Path, codigo: int):
    """Un scripts/revisar.sh que no llama a OpenCode: apunta que lo han llamado y sale con «codigo»
    (0 = VEREDICTO: OK, 1 = VEREDICTO: CAMBIAR, 2 = no se pudo revisar)."""
    (repo / "scripts").mkdir(exist_ok=True)
    (repo / "scripts" / "revisar.sh").write_bytes(
        f'#!/usr/bin/env bash\necho llamado >> .git/revisor-llamado\nexit {codigo}\n'.encode())
    return repo / ".git" / "revisor-llamado"


def commit(repo: Path, fichero: str):
    (repo / fichero).write_text("x = 1\n", encoding="utf-8")
    git(repo, "add", fichero)
    r = git(repo, "commit", "-m", f"cambio {fichero}")
    return r.returncode, r.stdout + r.stderr


def test_revisor_se_instala_solo_si_se_pide_y_si_hay_revisar_sh(repo):
    destino = repo / ".git/hooks/pre-commit"
    with pytest.raises(TareasError, match="no tiene scripts/revisar.sh"):
        hook.instalar(repo, revisor=True)
    revisor_de_mentira(repo, 0)
    hook.instalar(repo)
    assert hook.MARCA_REVISOR not in destino.read_text(encoding="utf-8")
    assert "revisor" in hook.instalar(repo, revisor=True)
    texto = destino.read_bytes().decode("utf-8")
    assert hook.MARCA in texto and hook.MARCA_REVISOR in texto and "\r" not in texto
    assert hook.quitar(repo) == "Hook quitado."     # sigue siendo nuestro: se quita igual


@pytest.mark.parametrize("codigo, pasa", [(0, True), (1, False), (2, True)],
                         ids=["veredicto-ok", "veredicto-cambiar", "sin-red"])
def test_el_revisor_decide_si_un_commit_con_codigo_pasa(repo, monkeypatch, codigo, pasa):
    monkeypatch.delenv("MOCHILA_SIN_REVISOR", raising=False)
    llamado = revisor_de_mentira(repo, codigo)
    hook.instalar(repo, revisor=True)
    estado, salida = commit(repo, "app.py")
    assert llamado.exists()
    assert (estado == 0) == pasa
    if codigo == 1:
        assert "el revisor pide cambios" in salida
    if codigo == 2:
        assert "No se ha podido pasar el revisor" in salida


def test_solo_documentacion_no_llama_al_revisor(repo, monkeypatch):
    monkeypatch.delenv("MOCHILA_SIN_REVISOR", raising=False)
    llamado = revisor_de_mentira(repo, 1)       # pediría cambios... pero no le toca
    hook.instalar(repo, revisor=True)
    estado, _ = commit(repo, "notas.md")
    assert estado == 0 and not llamado.exists()


def test_mochila_sin_revisor_lo_salta_una_vez(repo, monkeypatch):
    llamado = revisor_de_mentira(repo, 1)
    hook.instalar(repo, revisor=True)
    monkeypatch.setenv("MOCHILA_SIN_REVISOR", "1")
    estado, salida = commit(repo, "app.py")
    assert estado == 0 and not llamado.exists() and "MOCHILA_SIN_REVISOR" in salida


def test_cli_con_revisor(repo):
    revisor_de_mentira(repo, 0)
    r = CliRunner().invoke(app, ["instalar-hook", str(repo), "--revisor"])
    assert r.exit_code == 0 and hook.MARCA_REVISOR in (repo / ".git/hooks/pre-commit").read_text(encoding="utf-8")


def test_opencode_dentro_del_hook_no_estropea_el_indice(repo, monkeypatch, tmp_path_factory):
    """17-nov: OpenCode, lanzado desde el hook, guardó sus instantáneas en NUESTRO índice (heredó
    GIT_INDEX_FILE) y el commit falló con «invalid object». Este opencode de mentira hace lo mismo
    que el de verdad: «git add» en su propio repositorio. Usa el scripts/revisar.sh real."""
    monkeypatch.delenv("MOCHILA_SIN_REVISOR", raising=False)
    monkeypatch.setenv("MOCHILA_REVISOR_MODELO", "opencode/de-mentira")
    raiz = Path(__file__).resolve().parent.parent
    (repo / "scripts").mkdir()
    (repo / "scripts" / "revisar.sh").write_bytes((raiz / "scripts" / "revisar.sh").read_bytes())
    bin_falso = tmp_path_factory.mktemp("bin")
    instantaneas = tmp_path_factory.mktemp("instantaneas").as_posix()
    (bin_falso / "opencode").write_bytes(
        ("#!/usr/bin/env bash\n"
         f'git init -q --bare "{instantaneas}/snap" 2>/dev/null\n'
         f'git --git-dir="{instantaneas}/snap" --work-tree=. add -A\n'
         "cat >/dev/null\n"
         'echo "Todo bien."\necho "VEREDICTO: OK"\n').encode())
    (bin_falso / "opencode").chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_falso) + os.pathsep + os.environ["PATH"])
    hook.instalar(repo, revisor=True)

    estado, salida = commit(repo, "app.py")

    assert estado == 0, salida
    assert "El revisor dice que se puede subir" in salida
    assert git(repo, "fsck", "--no-dangling").returncode == 0
    assert git(repo, "status", "--porcelain").stdout.strip() == "?? scripts/"
