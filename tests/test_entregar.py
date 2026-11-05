"""dam entregar. Proyectos de mentira en tmp_path; la clave falsa se monta por trozos."""
import subprocess
import zipfile
from datetime import date
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import entregar
from tareas.cli import app
from tareas.errores import TareasError

run = CliRunner()
RELLENO = "aB3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0hJ3kL6"  # 36 caracteres
TOKEN_FALSO = "gh" + "p_" + RELLENO


def escribir(ruta: Path, texto: str = "x") -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


@pytest.fixture
def proyecto(tmp_path) -> Path:
    """Un proyecto sin git con un poco de todo: lo que debe entrar y lo que no."""
    p = tmp_path / "Electrician"
    escribir(p / "app" / "main.py", "print('hola')\n")
    escribir(p / "README.md", "# Proyecto\n")
    escribir(p / ".env.example", "GROQ_API_KEY=\n")  # la plantilla sí se entrega
    escribir(p / ".env", "MODO=pruebas\n")
    escribir(p / "id_rsa", "no es una clave de verdad")
    escribir(p / "id_rsa.pub", "parte pública")
    escribir(p / ".venv" / "lib" / "a.py")
    escribir(p / "web" / "node_modules" / "x" / "index.js")
    escribir(p / "app" / "__pycache__" / "main.cpython-312.pyc")
    escribir(p / "Thumbs.db")
    return p


def nombres_en_zip(ruta: Path) -> set[str]:
    with zipfile.ZipFile(ruta) as z:
        return set(z.namelist())


def test_elige_lo_que_entra_y_lo_que_no(proyecto):
    plan = entregar.preparar(proyecto)
    assert set(plan.incluidos) == {"app/main.py", "README.md", ".env.example", "id_rsa.pub"}
    assert plan.excluidos["secretos"] == [".env"]
    assert plan.excluidos["claves privadas"] == ["id_rsa"]
    assert plan.excluidos["basura del sistema"] == ["Thumbs.db"]
    # Las carpetas pesadas salen una vez, no fichero a fichero
    assert set(plan.excluidos["carpetas que se regeneran"]) == {".venv/", "web/node_modules/", "app/__pycache__/"}
    assert not plan.con_git and not plan.bloqueado


def test_crea_el_zip_al_lado_con_la_fecha_y_una_carpeta_dentro(proyecto, tmp_path):
    plan = entregar.preparar(proyecto, hoy=date(2026, 11, 5))
    assert plan.zip == tmp_path / "Electrician_2026-11-05.zip"  # al lado, no dentro del proyecto
    entregar.crear_zip(plan)
    assert nombres_en_zip(plan.zip) == {
        "Electrician/app/main.py", "Electrician/README.md", "Electrician/.env.example", "Electrician/id_rsa.pub",
    }


def test_preparar_no_escribe_nada(proyecto, tmp_path):
    antes = set(tmp_path.rglob("*"))
    entregar.preparar(proyecto)
    assert set(tmp_path.rglob("*")) == antes


def test_no_sobrescribe_un_zip_que_ya_existe(proyecto, tmp_path):
    escribir(tmp_path / "Electrician_2026-11-05.zip", "entrega anterior")
    plan = entregar.preparar(proyecto, hoy=date(2026, 11, 5))
    assert plan.zip.name == "Electrician_2026-11-05 (1).zip"
    entregar.crear_zip(plan)
    assert (tmp_path / "Electrician_2026-11-05.zip").read_text(encoding="utf-8") == "entrega anterior"


def test_nombre_y_destino_propios(proyecto, tmp_path):
    destino = tmp_path / "entregas"
    destino.mkdir()
    plan = entregar.preparar(proyecto, destino, "Vidal_Gabriel_p3")
    assert plan.zip == destino / "Vidal_Gabriel_p3.zip"


@pytest.mark.parametrize("nombre", ["../fuera", "sub/entrega.zip", "   "])
def test_nombre_con_carpetas_o_vacio_no_vale(proyecto, nombre):
    with pytest.raises(TareasError):
        entregar.preparar(proyecto, nombre=nombre)


def test_destino_o_carpeta_que_no_existen(proyecto, tmp_path):
    with pytest.raises(TareasError):
        entregar.preparar(tmp_path / "no-existe")
    with pytest.raises(TareasError):
        entregar.preparar(proyecto, tmp_path / "no-existe")


def test_un_secreto_dentro_bloquea_la_entrega(proyecto, tmp_path):
    escribir(proyecto / "app" / "config.py", f'TOKEN = "{TOKEN_FALSO}"\n')
    r = run.invoke(app, ["entregar", str(proyecto)])
    assert r.exit_code == 1
    assert "no creo el zip" in r.output
    assert "app/config.py" in r.output
    assert TOKEN_FALSO not in r.output  # nunca se imprime entero
    assert not list(tmp_path.glob("*.zip"))


def test_un_secreto_en_el_env_no_bloquea_porque_no_entra(proyecto):
    escribir(proyecto / ".env", f"GITHUB_TOKEN={TOKEN_FALSO}\n")
    plan = entregar.preparar(proyecto)
    assert not plan.bloqueado and plan.hallazgos == []


def test_en_un_repositorio_respeta_el_gitignore(proyecto):
    subprocess.run(["git", "init", "-b", "main", str(proyecto)], check=True, capture_output=True)
    escribir(proyecto / ".gitignore", "*.log\nsalida/\n")
    escribir(proyecto / "registro.log")
    escribir(proyecto / "salida" / "informe.pdf")
    escribir(proyecto / "nuevo.py")  # sin commit pero no ignorado: entra
    plan = entregar.preparar(proyecto)
    assert plan.con_git
    assert "nuevo.py" in plan.incluidos and ".gitignore" in plan.incluidos
    assert not any(r.endswith(".log") or r.startswith("salida/") for r in plan.incluidos)
    assert not any(r.startswith(".git/") for r in plan.incluidos)


def test_en_un_repositorio_el_env_ignorado_tambien_sale_en_lo_que_queda_fuera(proyecto):
    subprocess.run(["git", "init", "-b", "main", str(proyecto)], check=True, capture_output=True)
    escribir(proyecto / ".gitignore", ".env\n.venv/\n")
    plan = entregar.preparar(proyecto)
    assert ".env" not in plan.incluidos
    assert plan.excluidos["secretos"] == [".env"]  # se ve, aunque ya lo quitara .gitignore
    assert ".venv/" in plan.excluidos["carpetas que se regeneran"]


def test_cli_simular_enseña_la_lista_y_no_crea_nada(proyecto, tmp_path):
    r = run.invoke(app, ["entregar", str(proyecto), "--simular"])
    assert r.exit_code == 0, r.output
    assert "app/main.py" in r.output and "SIMULACIÓN" in r.output
    assert ".env" in r.output and "Se queda fuera" in r.output
    assert not list(tmp_path.glob("*.zip"))


def test_cli_crea_el_zip(proyecto, tmp_path):
    r = run.invoke(app, ["entregar", str(proyecto), "--nombre", "entrega"])
    assert r.exit_code == 0, r.output
    assert "Creado" in r.output
    assert "Electrician/app/main.py" in nombres_en_zip(tmp_path / "entrega.zip")


def test_cli_carpeta_que_no_existe_sale_con_1(tmp_path):
    r = run.invoke(app, ["entregar", str(tmp_path / "no-existe")])
    assert r.exit_code == 1
    assert "Traceback" not in r.output
