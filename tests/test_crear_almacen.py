"""Pruebas de mochila crear-almacen y del nombre del almacén por ciclo (ADR-0005).

GitHub es de mentira: una carpeta con repos «bare» (como los de GitHub, sin ficheros a la vista).
Nunca se abre el navegador ni se toca tu almacén: MOCHILA_ALMACEN no existe y el acciones.json va a una
carpeta temporal.
"""

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import configurar, almacen_nuevo
from tareas.errores import GitError
from tareas.cli import app

runner = CliRunner()
PLANTILLA = Path(__file__).parent.parent / "acciones.json"  # la del repo: 1º de DAM


def plano(r) -> str:
    return " ".join(r.output.split())


@pytest.fixture
def github(tmp_path, monkeypatch):
    """Un GitHub de mentira en una carpeta, un HOME vacío y un navegador que solo apunta lo que abre."""
    remotos = tmp_path / "github"
    remotos.mkdir()
    monkeypatch.setattr(almacen_nuevo, "GITHUB", remotos.as_uri())
    abiertas: list[str] = []
    monkeypatch.setattr(almacen_nuevo, "abrir_navegador", lambda url: abiertas.append(url) or True)
    casa = tmp_path / "casa"
    casa.mkdir()
    monkeypatch.setenv("HOME", str(casa))
    monkeypatch.setenv("USERPROFILE", str(casa))
    monkeypatch.delenv("MOCHILA_ALMACEN", raising=False)
    monkeypatch.chdir(tmp_path)
    for k, v in {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "t@t.es",
                 "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "t@t.es"}.items():
        monkeypatch.setenv(k, v)

    def crear_repo(usuario: str, nombre: str) -> Path:
        """Lo que hace el alumno al pulsar «Create repository»: un repo vacío."""
        ruta = remotos / usuario / f"{nombre}.git"
        subprocess.run(["git", "init", "--bare", "-b", "main", str(ruta)], check=True, capture_output=True)
        return ruta

    return {"casa": casa, "abiertas": abiertas, "crear_repo": crear_repo,
            "config": tmp_path / "config" / "acciones.json"}


def configurar_sin_almacen(github, ciclo="asir"):
    r = runner.invoke(app, ["--config", str(github["config"]), "configurar", "--plantilla", str(PLANTILLA),
                            "--ciclo", ciclo, "--curso", "1", "--si"])
    assert r.exit_code == 0, r.output
    return r


def preparar(github, entrada):
    return runner.invoke(app, ["--config", str(github["config"]), "crear-almacen"], input=entrada)


def ficheros_en_github(repo: Path) -> list[str]:
    p = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "--name-only", "main"],
                       capture_output=True, text=True, check=True)
    return p.stdout.splitlines()  # una ruta por línea: los nombres pueden llevar espacios


# ---------- el nombre y la ruta ----------
@pytest.mark.parametrize("ciclo, esperado", [("dam", "DAM-almacen"), ("asir", "ASIR-almacen"),
                                             ("smx", "SMX-almacen"), ("otro", "APUNTES-almacen"), (None, "APUNTES-almacen")])
def test_el_almacen_se_llama_como_tu_ciclo(ciclo, esperado):
    assert almacen_nuevo.nombre(ciclo) == esperado


@pytest.mark.parametrize("ruta, ciclo, esperado", [
    ("~/DAM-almacen", "asir", "~/ASIR-almacen"),   # la del acciones.json del repo pasa a tu ciclo
    ("~/DAM-almacen", "dam", "~/DAM-almacen"),     # con DAM no cambia nada
    ("~/smx-almacen", "daw", "~/DAW-almacen"),
    ("D:/apuntes", "asir", "D:/apuntes"),          # la que escribiste tú no se toca
    ("~/Documentos/DAM-almacen", "asir", "~/Documentos/DAM-almacen"),
])
def test_la_ruta_solo_cambia_si_la_puso_dam(ruta, ciclo, esperado):
    assert almacen_nuevo.ruta_para(ruta, ciclo) == esperado


def test_configurar_pone_la_ruta_de_tu_ciclo_y_con_dam_no_cambia_nada():
    plantilla = json.loads(PLANTILLA.read_text(encoding="utf-8"))
    asir = configurar.aplicar(plantilla, "asir", [1], {"redes": ["redes"]})
    assert asir["almacen"]["ruta"] == "~/ASIR-almacen"
    mochila = configurar.aplicar(plantilla, "dam", [1], configurar.asignaturas_actuales(plantilla))
    assert mochila["almacen"] == plantilla["almacen"]


@pytest.mark.parametrize("texto", ["ana-22", " Ana-22 ", "https://github.com/Ana-22/", "github.com/ana-22", "@ana-22"])
def test_entiende_el_usuario_aunque_pegues_la_direccion(texto):
    assert almacen_nuevo.limpiar_usuario(texto).lower() == "ana-22"


@pytest.mark.parametrize("texto", ["ana garcia", "ana@correo.es", "-ana", "a" * 40])
def test_usuario_que_no_puede_ser_de_github(texto):
    with pytest.raises(ValueError, match="detrás de github.com/"):
        almacen_nuevo.limpiar_usuario(texto)


def test_la_pagina_de_github_va_rellena_y_privada():
    url = almacen_nuevo.url_crear("ASIR-almacen")
    assert url.startswith("https://github.com/new?")
    assert "name=ASIR-almacen" in url and "visibility=private" in url


# ---------- el comando ----------
def test_alumno_nuevo_de_asir_crea_su_almacen_privado_y_se_sube_solo(github):
    configurar_sin_almacen(github)
    remoto = github["crear_repo"]("ana", "ASIR-almacen")  # lo que hará al pulsar el botón verde
    r = preparar(github, "ana\nn\n\n")  # usuario, NO lo tengo aún, Enter cuando lo ha creado
    assert r.exit_code == 0, r.output
    assert github["abiertas"] == [almacen_nuevo.url_crear("ASIR-almacen")]
    assert "Create repository" in plano(r) and "Private" in plano(r)
    local = github["casa"] / "ASIR-almacen"
    assert (local / "asignaturas" / "redes" / ".gitkeep").is_file()
    assert "asignaturas/redes/.gitkeep" in ficheros_en_github(remoto)  # ya está en GitHub
    # Y mochila sync ya sabe adónde subir (la rama tiene remoto)
    s = runner.invoke(app, ["--config", str(github["config"]), "status"])
    assert s.exit_code == 0, s.output


def test_en_otro_equipo_solo_lo_baja(github, monkeypatch):
    configurar_sin_almacen(github)
    github["crear_repo"]("ana", "ASIR-almacen")
    assert preparar(github, "ana\nn\n\n").exit_code == 0
    # Otro PC: mismo usuario, nada en casa
    otra = github["casa"].parent / "otra-casa"
    otra.mkdir()
    monkeypatch.setenv("HOME", str(otra))
    monkeypatch.setenv("USERPROFILE", str(otra))
    r = preparar(github, "ana\ns\n")  # SÍ lo tengo
    assert r.exit_code == 0, r.output
    assert github["abiertas"] == [almacen_nuevo.url_crear("ASIR-almacen")]  # no lo vuelve a abrir
    assert (otra / "ASIR-almacen" / "asignaturas" / "redes" / ".gitkeep").is_file()
    assert "Creadas" not in plano(r)  # las carpetas ya venían de GitHub


def test_si_el_repo_no_existe_explica_que_revisar(github):
    configurar_sin_almacen(github)
    r = preparar(github, "ana\ns\n")
    assert r.exit_code != 0
    assert "Repository not found" in plano(r) and "ASIR-almacen" in plano(r)
    assert not (github["casa"] / "ASIR-almacen").exists()


def test_con_enter_y_sin_almacen_en_el_equipo_se_salta(github):
    configurar_sin_almacen(github)
    r = preparar(github, "\nn\n")  # sin usuario, y NO lo quiero ni en este equipo
    assert r.exit_code == 1
    assert "Saltado" in plano(r) and "mochila crear-almacen" in plano(r)
    assert github["abiertas"] == [] and not (github["casa"] / "ASIR-almacen").exists()


def test_un_usuario_mal_escrito_se_vuelve_a_preguntar(github):
    configurar_sin_almacen(github)
    r = preparar(github, "ana garcia\n\n")
    assert "detrás de github.com/" in plano(r)


def test_si_ya_lo_tienes_solo_crea_las_carpetas_que_faltan(github):
    configurar_sin_almacen(github)
    almacen = github["casa"] / "ASIR-almacen"
    subprocess.run(["git", "init", "-b", "main", str(almacen)], check=True, capture_output=True)
    (almacen / "apunte.txt").write_text("hola", encoding="utf-8")
    subprocess.run(["git", "-C", str(almacen), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(almacen), "commit", "-m", "x"], check=True, capture_output=True)
    r = preparar(github, "\n")  # es un almacén sin GitHub: ofrece subirlo, y con Enter sigue igual
    assert r.exit_code == 0, r.output
    assert "Ya tienes tu almacén" in plano(r) and "solo en este equipo" in plano(r)
    assert (almacen / "asignaturas" / "redes" / ".gitkeep").is_file()


def test_una_carpeta_que_no_es_git_no_se_toca(github):
    configurar_sin_almacen(github)
    (github["casa"] / "ASIR-almacen").mkdir()
    (github["casa"] / "ASIR-almacen" / "mis cosas.txt").write_text("no tocar", encoding="utf-8")
    r = preparar(github, "")
    assert r.exit_code == 1
    assert "no es un repositorio git" in plano(r)
    assert [p.name for p in (github["casa"] / "ASIR-almacen").iterdir()] == ["mis cosas.txt"]


def test_una_carpeta_vacia_de_un_intento_que_fallo_si_se_usa(github):  # lo vio el revisor en la PR de #53
    configurar_sin_almacen(github)
    (github["casa"] / "ASIR-almacen").mkdir()
    r = preparar(github, "\n\n")  # sin GitHub: solo en este equipo
    assert r.exit_code == 0, r.output
    assert (github["casa"] / "ASIR-almacen" / "asignaturas" / "redes" / ".gitkeep").is_file()


def _ruta_vieja(github, ruta="~/DAM-almacen"):
    datos = json.loads(github["config"].read_text(encoding="utf-8"))
    datos["almacen"]["ruta"] = ruta
    github["config"].write_text(json.dumps(datos), encoding="utf-8")


def _ruta_guardada(github) -> str:
    return json.loads(github["config"].read_text(encoding="utf-8"))["almacen"]["ruta"]


def test_si_acciones_json_se_quedo_con_la_ruta_de_otro_ciclo_la_corrige(github):
    """13-nov, PC1411: ciclo DAW pero la ruta aún en ~/DAM-almacen (dijo «n» a rehacer acciones.json)."""
    configurar_sin_almacen(github, "daw")
    _ruta_vieja(github)
    github["crear_repo"]("ana", "DAW-almacen")
    r = preparar(github, "ana\ns\n")  # usuario, SÍ lo tengo ya
    assert r.exit_code == 0, r.output
    assert "pasa de ~/DAM-almacen a ~/DAW-almacen" in plano(r)
    assert (github["casa"] / "DAW-almacen" / ".git").is_dir()
    assert not (github["casa"] / "DAM-almacen").exists()
    assert _ruta_guardada(github) == "~/DAW-almacen"


def test_una_ruta_de_otro_ciclo_que_ya_es_tu_almacen_no_se_cambia(github):
    configurar_sin_almacen(github, "daw")
    _ruta_vieja(github)
    remoto = github["crear_repo"]("ana", "DAM-almacen")  # su almacén de siempre, ya clonado
    subprocess.run(["git", "clone", "-q", str(remoto), str(github["casa"] / "DAM-almacen")],
                   check=True, capture_output=True)
    r = preparar(github, "")
    assert r.exit_code == 0, r.output
    assert "Ya tienes tu almacén" in plano(r)
    assert _ruta_guardada(github) == "~/DAM-almacen"


def test_configurar_lo_ofrece_al_acabar(github):
    github["crear_repo"]("ana", "SMX-almacen")
    # SMX, 1º, sin cambios, guardar, SÍ prepárame el almacén, usuario, ya lo tengo
    r = runner.invoke(app, ["--config", str(github["config"]), "configurar", "--plantilla", str(PLANTILLA)],
                      input="1\n1\nn\ns\ns\nana\ns\n")
    assert r.exit_code == 0, r.output
    assert (github["casa"] / "SMX-almacen" / "asignaturas" / "redes-locales" / ".gitkeep").is_file()


def test_configurar_con_si_no_pregunta_por_el_almacen(github):
    r = configurar_sin_almacen(github)
    assert "mochila crear-almacen" in plano(r)
    assert not (github["casa"] / "ASIR-almacen").exists()


# ---------- issue #53: sin GitHub, el almacén solo en este equipo ----------
def _commits(ruta: Path) -> int:
    p = subprocess.run(["git", "-C", str(ruta), "rev-list", "--count", "HEAD"], capture_output=True, text=True)
    return int(p.stdout.strip() or 0)


def test_sin_github_lo_crea_solo_en_este_equipo_y_ya_se_puede_ordenar(github):
    configurar_sin_almacen(github)
    r = preparar(github, "\n\n")  # Enter en el usuario y Enter (Sí) a crearlo solo en este equipo
    assert r.exit_code == 0, r.output
    local = github["casa"] / "ASIR-almacen"
    assert "solo en este equipo" in plano(r) and "mochila ejecutar ordenar" in plano(r)
    assert (local / "asignaturas" / "redes" / ".gitkeep").is_file() and _commits(local) == 1
    assert almacen_nuevo.solo_en_este_equipo(local) and github["abiertas"] == []
    # Y ordenar ya funciona: el apunte entra en el almacén y no intenta subirlo
    descargas = github["casa"] / "Downloads"
    descargas.mkdir()
    (descargas / "redes tema 1.pdf").write_bytes(b"%PDF")
    o = runner.invoke(app, ["--config", str(github["config"]), "ejecutar", "ordenar", str(descargas), "--si"])
    assert o.exit_code == 0, o.output
    assert list((local / "asignaturas" / "redes").rglob("redes tema 1.pdf"))
    assert "solo en este equipo" in plano(o) and "mochila crear-almacen" in plano(o)


def test_sync_de_un_almacen_sin_github_dice_que_hacer(github):
    configurar_sin_almacen(github)
    assert preparar(github, "\n\n").exit_code == 0
    r = runner.invoke(app, ["--config", str(github["config"]), "status"])
    assert r.exit_code != 0
    assert "solo en este equipo" in plano(r) and "mochila crear-almacen" in plano(r)
    assert "git push -u origin main" not in plano(r)


def test_despues_lo_sube_a_github_y_sync_ya_sabe_adonde(github):
    configurar_sin_almacen(github)
    assert preparar(github, "\n\n").exit_code == 0
    remoto = github["crear_repo"]("ana", "ASIR-almacen")  # lo que hará al pulsar el botón verde
    r = preparar(github, "ana\nn\n\n")  # usuario, NO lo tengo aún, Enter cuando lo ha creado
    assert r.exit_code == 0, r.output
    assert "Subido a GitHub" in plano(r) and github["abiertas"] == [almacen_nuevo.url_crear("ASIR-almacen")]
    assert "asignaturas/redes/.gitkeep" in ficheros_en_github(remoto)
    assert not almacen_nuevo.solo_en_este_equipo(github["casa"] / "ASIR-almacen")
    s = runner.invoke(app, ["--config", str(github["config"]), "status"])
    assert s.exit_code == 0, s.output


def test_un_git_init_a_mano_en_master_tambien_se_sube_como_main(github):  # lo vio el revisor
    configurar_sin_almacen(github)
    almacen = github["casa"] / "ASIR-almacen"
    subprocess.run(["git", "init", "-b", "master", str(almacen)], check=True, capture_output=True)
    (almacen / "apunte.txt").write_text("hola", encoding="utf-8")
    subprocess.run(["git", "-C", str(almacen), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(almacen), "commit", "-m", "x"], check=True, capture_output=True)
    remoto = github["crear_repo"]("ana", "ASIR-almacen")
    r = preparar(github, "ana\ns\nn\n")  # usuario, ya lo tengo, y NO al sync de las carpetas nuevas
    assert r.exit_code == 0, r.output
    assert "apunte.txt" in ficheros_en_github(remoto)  # el commit de master, ahora en main
    assert runner.invoke(app, ["--config", str(github["config"]), "status"]).exit_code == 0


def test_si_git_no_sabe_quien_eres_lo_dice_antes_de_subir(github, monkeypatch):  # lo vio el revisor
    almacen = github["casa"] / "APUNTES-almacen"
    almacen_nuevo.crear_local(almacen)  # vacío: al subirlo hace falta un commit (sin nada)
    remoto = github["crear_repo"]("ana", "APUNTES-almacen")
    for k in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
        monkeypatch.delenv(k)
    subprocess.run(["git", "-C", str(almacen), "config", "user.useConfigOnly", "true"], check=True)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(github["casa"] / "no-hay-gitconfig"))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    with pytest.raises(GitError, match="git no sabe tu nombre ni tu correo"):
        almacen_nuevo.conectar(almacen, remoto.as_uri(), "APUNTES-almacen")
    assert almacen_nuevo.solo_en_este_equipo(almacen)  # no ha llegado a tocar el remoto


def test_si_el_repo_de_github_no_esta_vacio_lo_explica_y_no_pierde_nada(github, tmp_path):
    configurar_sin_almacen(github)
    assert preparar(github, "\n\n").exit_code == 0
    remoto = github["crear_repo"]("ana", "ASIR-almacen")
    otro = tmp_path / "con-readme"  # lo creó en GitHub marcando «Add a README»
    subprocess.run(["git", "clone", "-q", str(remoto), str(otro)], check=True, capture_output=True)
    (otro / "README.md").write_text("# ASIR-almacen", encoding="utf-8")
    subprocess.run(["git", "-C", str(otro), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(otro), "commit", "-m", "README"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(otro), "push", "-q", "origin", "HEAD:main"], check=True, capture_output=True)
    r = preparar(github, "ana\ns\n")
    assert r.exit_code != 0
    assert "no está vacío" in plano(r) and "siguen en tu equipo" in plano(r)
    local = github["casa"] / "ASIR-almacen"
    assert (local / "asignaturas" / "redes" / ".gitkeep").is_file()
    # Hace lo que dice el mensaje (lo borra y lo crea vacío) y repite: vuelve a ofrecer subirlo
    assert almacen_nuevo.solo_en_este_equipo(local)  # no se ha quedado con el remoto a medias
    shutil.rmtree(remoto, onexc=lambda f, ruta, e: (os.chmod(ruta, stat.S_IWRITE), f(ruta)))  # Windows: solo lectura
    github["crear_repo"]("ana", "ASIR-almacen")
    r = preparar(github, "ana\ns\n")
    assert r.exit_code == 0, r.output
    assert "Subido a GitHub" in plano(r)


def test_lo_que_ordeno_sin_github_se_sube_con_sync_al_conectarlo(github):
    configurar_sin_almacen(github)
    assert preparar(github, "\n\n").exit_code == 0
    descargas = github["casa"] / "Downloads"
    descargas.mkdir()
    (descargas / "redes tema 1.pdf").write_bytes(b"%PDF")
    o = runner.invoke(app, ["--config", str(github["config"]), "ejecutar", "ordenar", str(descargas), "--si"])
    assert o.exit_code == 0, o.output
    remoto = github["crear_repo"]("ana", "ASIR-almacen")
    r = preparar(github, "ana\ns\ns\n")  # usuario, ya lo tengo, SÍ haz sync de lo que tengo
    assert r.exit_code == 0, r.output
    assert "aún no están en GitHub" in plano(r)
    assert any(f.endswith("redes tema 1.pdf") for f in ficheros_en_github(remoto))
    assert not almacen_nuevo.hay_cambios(github["casa"] / "ASIR-almacen")
