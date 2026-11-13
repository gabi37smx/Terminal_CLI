"""Pruebas de dam crear-almacen y del nombre del almacén por ciclo (ADR-0005).

GitHub es de mentira: una carpeta con repos «bare» (como los de GitHub, sin ficheros a la vista).
Nunca se abre el navegador ni se toca tu almacén: DAM_ALMACEN no existe y el acciones.json va a una
carpeta temporal.
"""

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import configurar, almacen_nuevo
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
    monkeypatch.delenv("DAM_ALMACEN", raising=False)
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
    return p.stdout.split()


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
    dam = configurar.aplicar(plantilla, "dam", [1], configurar.asignaturas_actuales(plantilla))
    assert dam["almacen"] == plantilla["almacen"]


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
    # Y dam sync ya sabe adónde subir (la rama tiene remoto)
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


def test_con_enter_se_salta(github):
    configurar_sin_almacen(github)
    r = preparar(github, "\n")
    assert r.exit_code == 1
    assert "dam crear-almacen" in plano(r)
    assert github["abiertas"] == []


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
    r = preparar(github, "")
    assert r.exit_code == 0, r.output
    assert "Ya tienes tu almacén" in plano(r) and "dam sync" in plano(r)
    assert (almacen / "asignaturas" / "redes" / ".gitkeep").is_file()


def test_una_carpeta_que_no_es_git_no_se_toca(github):
    configurar_sin_almacen(github)
    (github["casa"] / "ASIR-almacen").mkdir()
    r = preparar(github, "")
    assert r.exit_code == 1
    assert "no es un repositorio git" in plano(r)
    assert list((github["casa"] / "ASIR-almacen").iterdir()) == []


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
    assert "dam crear-almacen" in plano(r)
    assert not (github["casa"] / "ASIR-almacen").exists()
