"""dam doctor. Proyectos de mentira en tmp_path; los valores «secretos» se montan por trozos."""
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import doctor
from tareas.cli import app

run = CliRunner()
TOKEN_FALSO = "gh" + "p_" + "aB3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0hJ3kL6"
VALOR_PRIVADO = "valor" + "Privado" + "123"  # no debe salir nunca por pantalla


def escribir(ruta: Path, texto: str = "x") -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def git(carpeta: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(carpeta), *args], check=True, capture_output=True)


def estado(informe: doctor.Informe, nombre: str) -> str:
    return next(c.estado for c in informe.comprobaciones if c.nombre == nombre)


def detalle(informe: doctor.Informe, nombre: str) -> str:
    return next(c.detalle for c in informe.comprobaciones if c.nombre == nombre)


@pytest.fixture
def sano(tmp_path) -> Path:
    """Un proyecto que lo cumple todo."""
    p = tmp_path / "proyecto"
    subprocess.run(["git", "init", "-b", "main", str(p)], check=True, capture_output=True)
    escribir(p / ".gitignore", ".env\n.venv/\n")
    escribir(p / ".env", f"API_KEY={VALOR_PRIVADO}\nexport PUERTO=3000\n# comentario\n")
    escribir(p / ".env.example", "API_KEY=\nPUERTO=\n")
    escribir(p / "README.md", "# Proyecto\n\nQué es.\n\nCómo se instala.\n\nCómo se usa.\n\nLicencia.\n")
    escribir(p / "requirements.txt", "fastapi\n")
    escribir(p / "app" / "main.py", "print('hola')\n")
    escribir(p / "tests" / "test_main.py", "def test_x():\n    assert True\n")
    escribir(p / ".github" / "workflows" / "ci.yml", "name: CI\n")
    git(p, "add", "-A")
    return p


def test_proyecto_sano_lo_cumple_todo(sano):
    informe = doctor.revisar(sano)
    assert informe.fallan_basicas == []
    assert [c.nombre for c in informe.comprobaciones if c.estado != "ok"] == []


def test_cli_proyecto_sano_sale_con_0_y_no_enseña_valores(sano):
    r = run.invoke(app, ["doctor", str(sano)])
    assert r.exit_code == 0, r.output
    assert "Lo básico está bien" in r.output
    assert VALOR_PRIVADO not in r.output


def test_lee_solo_los_nombres_de_las_variables(sano):
    assert doctor.nombres_de_variables(sano / ".env") == {"API_KEY", "PUERTO"}


def test_env_example_con_variables_que_faltan(sano):
    lineas = ["API" + "_KEY=" + VALOR_PRIVADO, "PUERTO=3000", "GROQ" + "_KEY=" + VALOR_PRIVADO]
    escribir(sano / ".env", "\n".join(lineas) + "\n")
    informe = doctor.revisar(sano)
    assert estado(informe, ".env.example al día") == "falta"
    assert "GROQ_KEY" in detalle(informe, ".env.example al día")
    r = run.invoke(app, ["doctor", str(sano)])
    assert r.exit_code == 1
    assert VALOR_PRIVADO not in r.output


def test_env_example_con_variables_de_mas_solo_avisa(sano):
    escribir(sano / ".env.example", "API_KEY=\nPUERTO=\nVIEJA=\n")
    informe = doctor.revisar(sano)
    assert estado(informe, ".env.example al día") == "aviso"
    assert informe.fallan_basicas == []


def test_env_sin_plantilla(sano):
    (sano / ".env.example").unlink()
    assert estado(doctor.revisar(sano), ".env.example al día") == "falta"


def test_sin_env_ni_plantilla_no_aplica(sano):
    (sano / ".env").unlink()
    (sano / ".env.example").unlink()
    assert estado(doctor.revisar(sano), ".env.example al día") == "no aplica"


def test_env_subido_a_git(sano):
    git(sano, "add", "-f", ".env")
    informe = doctor.revisar(sano)
    assert estado(informe, "Ningún .env subido a git") == "falta"
    assert ".env" in detalle(informe, "Ningún .env subido a git")


def test_sin_gitignore(sano):
    (sano / ".gitignore").unlink()
    informe = doctor.revisar(sano)
    assert estado(informe, ".gitignore") == "falta"
    assert estado(informe, ".env en .gitignore") == "falta"


def test_carpeta_sin_git(tmp_path):
    escribir(tmp_path / ".gitignore", ".env\n")
    escribir(tmp_path / ".env", f"API_KEY={VALOR_PRIVADO}\n")
    escribir(tmp_path / ".env.example", "API_KEY=\n")
    informe = doctor.revisar(tmp_path)
    assert estado(informe, "Repositorio git") == "falta"
    assert estado(informe, "Ningún .env subido a git") == "no aplica"
    assert estado(informe, ".env en .gitignore") == "ok"  # se lee el .gitignore a mano
    # el .env es el sitio correcto para las claves: no cuenta como secreto a la vista
    assert estado(informe, "Sin secretos a la vista") == "ok"


def test_readme_que_falta_o_muy_corto(sano):
    (sano / "README.md").unlink()
    assert estado(doctor.revisar(sano), "README") == "falta"
    escribir(sano / "readme.md", "# Hola\n")
    assert estado(doctor.revisar(sano), "README") == "aviso"


def test_secreto_en_el_codigo(sano):
    escribir(sano / "app" / "config.py", f'TOKEN = "{TOKEN_FALSO}"\n')
    informe = doctor.revisar(sano)
    assert estado(informe, "Sin secretos a la vista") == "falta"
    assert "app/config.py" in detalle(informe, "Sin secretos a la vista")
    r = run.invoke(app, ["doctor", str(sano)])
    assert r.exit_code == 1
    assert TOKEN_FALSO not in r.output


def test_las_recomendadas_avisan_pero_no_hacen_fallar(sano):
    for ruta in ("tests/test_main.py", ".github/workflows/ci.yml", "requirements.txt"):
        (sano / ruta).unlink()
    git(sano, "add", "-A")
    informe = doctor.revisar(sano)
    for nombre in ("Tests", "CI (GitHub Actions)", "Dependencias declaradas"):
        assert estado(informe, nombre) == "aviso", nombre
    assert run.invoke(app, ["doctor", str(sano)]).exit_code == 0


@pytest.mark.parametrize("nombre", ["app.test.js", "main_test.py", "boton.spec.tsx", "test_algo.py"])
def test_reconoce_tests_de_python_y_javascript(tmp_path, nombre):
    escribir(tmp_path / "src" / nombre)
    assert estado(doctor.revisar(tmp_path), "Tests") == "ok"


def test_web_estatica_no_necesita_dependencias(tmp_path):
    escribir(tmp_path / "index.html", "<html></html>")
    assert estado(doctor.revisar(tmp_path), "Dependencias declaradas") == "no aplica"


def test_dependencias_en_una_subcarpeta(tmp_path):
    escribir(tmp_path / "backend" / "package.json", "{}")
    informe = doctor.revisar(tmp_path)
    assert estado(informe, "Dependencias declaradas") == "ok"
    assert "backend/package.json" in detalle(informe, "Dependencias declaradas")


def test_ficheros_grandes(sano, monkeypatch):
    monkeypatch.setattr(doctor, "LIMITE_GRANDE", 10)
    escribir(sano / "video.mp4", "x" * 20)
    informe = doctor.revisar(sano)
    assert estado(informe, "Ficheros grandes") == "aviso"
    assert "video.mp4" in detalle(informe, "Ficheros grandes")


def test_no_cambia_nada(sano):
    antes = {p: p.stat().st_mtime_ns for p in sano.rglob("*") if ".git" not in p.parts}
    doctor.revisar(sano)
    assert {p: p.stat().st_mtime_ns for p in sano.rglob("*") if ".git" not in p.parts} == antes


def test_cli_carpeta_que_no_existe_sale_con_1(tmp_path):
    r = run.invoke(app, ["doctor", str(tmp_path / "no-existe")])
    assert r.exit_code == 1
    assert "Traceback" not in r.output


def test_una_sola_variable_en_singular(sano):
    escribir(sano / ".env", "PUERTO=3000\n")
    escribir(sano / ".env.example", "PUERTO=\n")
    assert detalle(doctor.revisar(sano), ".env.example al día") == "Tiene la misma variable que tu .env."


def test_carpeta_de_fuera_con_repos_dentro(tmp_path):
    for nombre in ("Terminal_CLI", "otro"):
        subprocess.run(["git", "init", str(tmp_path / nombre)], check=True, capture_output=True)
    escribir(tmp_path / "notas" / "a.txt")  # no es un repo
    informe = doctor.revisar(tmp_path)
    assert informe.repos_dentro == ["Terminal_CLI", "otro"]
    assert "Terminal_CLI/, otro/" in detalle(informe, "Repositorio git")
    r = run.invoke(app, ["doctor", str(tmp_path)])
    assert "Parece la carpeta de fuera" in r.output
    assert "Terminal_CLI" in r.output


def test_un_repo_no_mira_sus_subcarpetas(sano):
    subprocess.run(["git", "init", str(sano / "vendor")], check=True, capture_output=True)
    assert doctor.revisar(sano).repos_dentro == []


def test_en_tu_carpeta_personal_no_revisa_todo_y_dice_que_proyectos_hay(tmp_path):
    """13-nov: en una terminal nueva (que empieza en ~), doctor revisaba todo: .cache, .nvm..."""
    casa = Path.home()  # conftest la pone en una carpeta temporal
    for nombre in ("Terminal_CLI", ".nvm"):
        subprocess.run(["git", "init", str(casa / nombre)], check=True, capture_output=True)
    escribir(casa / ".cache" / "cacert.pem", "-----BEGIN CERTIFICATE-----")
    r = run.invoke(app, ["doctor", str(casa)])
    salida = " ".join(r.output.split())
    assert r.exit_code == 1
    assert "Estás en tu carpeta personal" in salida and "Terminal_CLI" in salida
    assert ".nvm" not in salida and "Revisión de" not in salida  # ni las ocultas ni la tabla


def test_si_tu_carpeta_personal_es_un_repo_si_la_revisa():
    casa = Path.home()
    subprocess.run(["git", "init", str(casa)], check=True, capture_output=True)  # p. ej., tus dotfiles
    r = run.invoke(app, ["doctor", str(casa)])
    assert "Revisión de" in r.output
