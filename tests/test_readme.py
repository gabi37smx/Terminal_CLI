"""dam readme: tabla «Qué hay dentro» en cada README, sin tocar lo que escribe el alumno."""
from datetime import date

import pytest
from typer.testing import CliRunner

from tareas import readme
from tareas.cli import app
from tareas.errores import TareasError

run = CliRunner()
HOY = date(2026, 11, 11)
VIEJO = """# PERSONAL

Cosas personales que no son de estudios.

## Qué hay dentro

**Carpetas:**

- `DOCUMENTOS/`

_README escrito el 10-nov-2026. Si cambias lo que hay, actualízalo._
"""


@pytest.fixture
def datos(tmp_path):
    """DATOS/ con PERSONAL (README viejo), SMX (sin README), un repo, un proyecto y un README propio."""
    raiz = tmp_path / "DATOS"
    personal = raiz / "PERSONAL"
    (personal / "DOCUMENTOS").mkdir(parents=True)
    (personal / "README.md").write_text(VIEJO, encoding="utf-8")
    (personal / "DOCUMENTOS" / "README.md").write_text("# DOCUMENTOS\n\nDNI y nóminas.\n", encoding="utf-8")
    (personal / "DOCUMENTOS" / "dni.pdf").write_bytes(b"x" * 2048)
    (personal / "notas.txt").write_text("hola", encoding="utf-8")
    (raiz / "SMX" / "SMX1").mkdir(parents=True)
    repo = raiz / "REPOS" / "MI-WEB"
    (repo / ".git").mkdir(parents=True)
    (repo / "README.md").write_text("# mi-web\n\nMi portfolio personal.\n", encoding="utf-8")
    (repo / "docs").mkdir()
    proyecto = raiz / "REPOS" / "SIN-GIT"
    (proyecto / "src").mkdir(parents=True)
    (proyecto / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    (raiz / "CURSOS").mkdir()
    (raiz / "CURSOS" / "README.md").write_text("# CURSOS\n\nEscrito a mano, sin tabla.\n", encoding="utf-8")
    return raiz


def por_carpeta(cambios, raiz):
    return {c.carpeta.relative_to(raiz).as_posix(): c.que for c in cambios}


# ---------- la primera frase del README ----------
@pytest.mark.parametrize("texto, esperado", [
    ("# X\n\nCosas **personales**.\nDos líneas.\n\n- lista\n", "Cosas personales. Dos líneas."),
    ("# X\n\n" + readme.PENDIENTE + "\n\n## Qué hay dentro\n", ""),
    ("# X\n\n![logo](a.png)\n\nPortfolio.\n", "Portfolio."),
    ("# X\n\n## Uso\n\nalgo\n", ""),
    ("", ""),
])
def test_descripcion(texto, esperado):
    assert readme.descripcion(texto) == esperado


def test_descripcion_larga_se_corta():
    frase = readme.descripcion("# X\n\n" + "palabra " * 40)
    assert len(frase) <= readme.MAX_DESCRIPCION + 1 and frase.endswith("…")


# ---------- qué hace en cada carpeta ----------
def test_plan_crea_actualiza_y_respeta(datos):
    plan = por_carpeta(readme.planear(datos, 3, HOY), datos)
    assert plan["."] == "crear"
    assert plan["PERSONAL"] == "actualizar"  # README viejo con «Qué hay dentro»
    assert plan["SMX"] == "crear" and plan["SMX/SMX1"] == "crear"
    assert plan["CURSOS"] == "propio"  # README sin el apartado: no es nuestro
    assert plan["PERSONAL/DOCUMENTOS"] == "propio"
    # ni dentro de repos ni de proyectos; y en un proyecto sin README no se crea uno
    assert not any(k.startswith(("REPOS/MI-WEB", "REPOS/SIN-GIT")) for k in plan)


def test_carpeta_con_venv_es_un_proyecto(datos):
    curso = datos / "CURSOS" / "BIG DATA IA"
    (curso / ".venv").mkdir(parents=True)
    (curso / "docs").mkdir()
    plan = por_carpeta(readme.planear(datos, 3, HOY), datos)
    assert "CURSOS/BIG DATA IA" not in plan and "CURSOS/BIG DATA IA/docs" not in plan


def test_niveles(datos):
    plan = por_carpeta(readme.planear(datos, 1, HOY), datos)
    assert "SMX" in plan and "SMX/SMX1" not in plan
    assert list(por_carpeta(readme.planear(datos, 0, HOY), datos)) == ["."]


def test_conserva_lo_de_arriba_y_lo_de_abajo(datos):
    readme_personal = datos / "PERSONAL" / "README.md"
    readme_personal.write_text(VIEJO + "\n## Notas\n\nEsto lo escribí yo.\n", encoding="utf-8")
    cambio = next(c for c in readme.planear(datos, 3, HOY) if c.carpeta.name == "PERSONAL")
    texto = cambio.texto
    assert texto.startswith("# PERSONAL\n\nCosas personales que no son de estudios.\n\n## Qué hay dentro\n")
    assert texto.rstrip().endswith("## Notas\n\nEsto lo escribí yo.")
    assert "_README escrito el" not in texto and "**Carpetas:**" not in texto  # el formato viejo se va
    assert "| 📁 **DOCUMENTOS** | 2.0 KB | DNI y nóminas. |" in texto  # la frase de su README
    assert "| 📄 notas.txt | 4 B | documento (.txt) |" in texto
    assert "(11-nov-2026)" in texto


def test_readme_nuevo(datos):
    texto = next(c for c in readme.planear(datos, 3, HOY) if c.carpeta == datos / "SMX").texto
    assert texto.startswith("# SMX\n\n" + readme.PENDIENTE + "\n\n## Qué hay dentro\n")
    assert "| 📁 **SMX1** | 0 B | 0 archivos |" in texto
    vacia = next(c for c in readme.planear(datos, 3, HOY) if c.carpeta.name == "SMX1").texto
    assert "_Vacía de momento._" in vacia


def test_repo_sale_marcado_en_la_tabla_del_padre(datos):
    texto = next(c for c in readme.planear(datos, 3, HOY) if c.carpeta.name == "REPOS").texto
    assert "**Repo git.** Mi portfolio personal." in texto
    assert "| 📁 **SIN-GIT** |" in texto


def test_escribir_y_la_segunda_vez_ya_esta_al_dia(datos):
    readme.aplicar(readme.planear(datos, 3, HOY))
    assert (datos / "SMX" / "README.md").is_file()
    cursos = (datos / "CURSOS" / "README.md").read_text(encoding="utf-8")
    assert cursos == "# CURSOS\n\nEscrito a mano, sin tabla.\n"
    assert not (datos / "REPOS" / "SIN-GIT" / "README.md").exists()
    assert (datos / "REPOS" / "MI-WEB" / "README.md").read_text(encoding="utf-8") == "# mi-web\n\nMi portfolio personal.\n"
    # otro día, sin cambios en las carpetas: no reescribe nada (la fecha sola no cuenta)
    otro_dia = readme.planear(datos, 3, date(2026, 12, 1))
    assert {c.que for c in otro_dia} <= {"igual", "propio"}
    # un README recién creado no tiene frase todavía: en la tabla del padre sale el número de archivos
    assert "| 📁 **SMX1** | 0 B | 0 archivos |" in (datos / "SMX" / "README.md").read_text(encoding="utf-8")


def test_si_cambia_la_carpeta_se_pone_al_dia(datos):
    readme.aplicar(readme.planear(datos, 3, HOY))
    (datos / "PERSONAL" / "foto.png").write_bytes(b"x" * 10)
    plan = por_carpeta(readme.planear(datos, 3, HOY), datos)
    assert plan["PERSONAL"] == "actualizar" and plan["SMX"] == "igual"


def test_muchos_archivos(tmp_path):
    for i in range(readme.MAX_ARCHIVOS + 4):
        (tmp_path / f"f{i:02}.txt").write_bytes(b"x" * 100)
    (tmp_path / "desktop.ini").write_text("x", encoding="utf-8")
    filas = readme.tabla(tmp_path)
    assert "| 📄 f00.txt | 100 B | documento (.txt) |" in filas
    assert filas[-1] == "| … | 400 B | y 4 archivos más |"
    assert not any("desktop.ini" in f for f in filas)


def test_la_barra_no_rompe_la_tabla():  # en Linux y macOS un nombre puede llevar «|»
    assert readme._celda("a|b") == "a\\|b"


def test_los_readme_no_cuentan_en_el_tamano(tmp_path):
    (tmp_path / "SUB").mkdir()
    (tmp_path / "SUB" / "README.md").write_text("# SUB\n\nAlgo.\n", encoding="utf-8")
    assert "| 📁 **SUB** | 0 B | Algo. |" in readme.tabla(tmp_path)


def test_errores(tmp_path):
    with pytest.raises(TareasError, match="no existe"):
        readme.planear(tmp_path / "no-esta")
    (tmp_path / ".git").mkdir()
    with pytest.raises(TareasError, match="repo git"):
        readme.planear(tmp_path)


# ---------- la orden ----------
def test_cli_simular_no_toca_nada(datos):
    r = run.invoke(app, ["readme", str(datos), "--simular"])
    assert r.exit_code == 0, r.output
    assert "SIMULACIÓN" in r.output and "crear" in r.output and "no se toca" in r.output
    assert not (datos / "README.md").exists()
    assert "_README escrito el" in (datos / "PERSONAL" / "README.md").read_text(encoding="utf-8")


def test_cli_pregunta_y_cancela(datos):
    r = run.invoke(app, ["readme", str(datos)], input="n\n")
    assert r.exit_code == 1 and not (datos / "README.md").exists()


def test_cli_escribe_y_despues_no_hay_nada_que_hacer(datos):
    r = run.invoke(app, ["readme", str(datos)], input="s\n")
    assert r.exit_code == 0, r.output
    assert "README escritos" in r.output and (datos / "README.md").is_file()
    r = run.invoke(app, ["readme", str(datos), "--si"])
    assert "No hay nada que hacer" in r.output


def test_cli_carpeta_que_no_existe(tmp_path):
    r = run.invoke(app, ["readme", str(tmp_path / "no-esta")])
    assert r.exit_code == 1
