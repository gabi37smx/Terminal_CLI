"""dam inventario. Carpetas de mentira en tmp_path: nunca se recorre el PC de verdad."""
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import inventario
from tareas.cli import app

run = CliRunner()


def escribir(ruta: Path, bytes_: int = 10) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(b"x" * bytes_)


@pytest.fixture
def pc(tmp_path) -> Path:
    """Un «usuario» pequeño con un poco de todo."""
    raiz = tmp_path / "usuario"
    escribir(raiz / "suelto.txt", 5)
    escribir(raiz / "DAM" / "apuntes.pdf", 100)
    escribir(raiz / "DAM" / "foto.PNG", 50)
    escribir(raiz / "DAM" / "Thumbs.db", 7)
    escribir(raiz / "DAM" / "~$trabajo.docx", 3)
    escribir(raiz / "Descargas" / "setup.exe", 1000)
    escribir(raiz / "Descargas" / "pelicula.mp4.crdownload", 20)
    escribir(raiz / "Programa" / "programa.exe", 400)
    escribir(raiz / "Programa" / "motor.dll", 400)
    # un repo con remoto, con su .venv y su node_modules
    repo = raiz / "repos" / "web"
    escribir(repo / "main.py", 30)
    escribir(repo / ".git" / "HEAD", 2)
    (repo / ".git" / "config").write_bytes(b'[core]\n[remote "origin"]\n')  # 25 bytes en todos los sistemas
    escribir(repo / ".venv" / "lib" / "paquete.py", 200)
    escribir(repo / "front" / "node_modules" / "a" / "index.js", 300)
    # un repo sin remoto
    sin_remoto = raiz / "repos" / "local"
    escribir(sin_remoto / "notas.md", 4)
    (sin_remoto / ".git").mkdir(parents=True)
    (sin_remoto / ".git" / "config").write_bytes(b"[core]\n")  # 7 bytes
    escribir(raiz / "AppData" / "Local" / "cache.bin", 5000)  # del sistema: no se recorre
    return raiz


def rutas(lista) -> set[str]:
    return {f.ruta for f in lista}


def test_tipo_de_por_extension():
    assert inventario.tipo_de("Tema1.PDF") == "documentos"
    assert inventario.tipo_de("red.pkt") == "redes"
    assert inventario.tipo_de("disco.vdi") == "maquinas-virtuales"
    assert inventario.tipo_de("setup.exe") == "instaladores"
    assert inventario.tipo_de("setup.exe", hay_dll_al_lado=True) == "programas"
    assert inventario.tipo_de("sin_extension") == "otros"


@pytest.mark.parametrize("nombre", ["Thumbs.db", ".DS_Store", "~$trabajo.docx", "a.tmp", "video.crdownload"])
def test_es_basura(nombre):
    assert inventario.es_basura(nombre)


@pytest.mark.parametrize("nombre", ["desktop.ini", "apuntes.pdf", "backup.zip"])
def test_no_es_basura(nombre):
    assert not inventario.es_basura(nombre)


def test_totales_y_tamano_por_carpeta(pc):
    informe = inventario.revisar(pc)
    sin_appdata = 5 + 100 + 50 + 7 + 3 + 1000 + 20 + 400 + 400 + 30 + 2 + 25 + 200 + 300 + 4 + 7
    assert informe.tamano == sin_appdata
    assert informe.por_carpeta[inventario.SUELTOS] == 5
    assert informe.por_carpeta["DAM"] == 160
    assert informe.por_carpeta["Descargas"] == 1020
    assert "AppData" not in informe.por_carpeta
    assert "AppData" in informe.saltadas


def test_repos_con_su_tamano_y_remoto(pc):
    informe = inventario.revisar(pc)
    repos = {r.ruta: r for r in informe.repos}
    assert set(repos) == {"repos/web", "repos/local"}
    assert repos["repos/web"].con_remoto is True
    assert repos["repos/local"].con_remoto is False
    # el tamaño del repo incluye .git, .venv y node_modules
    assert repos["repos/web"].tamano == 30 + 2 + 25 + 200 + 300


def test_listas_de_instaladores_basura_y_regenerables(pc):
    informe = inventario.revisar(pc)
    assert rutas(informe.instaladores) == {"Descargas/setup.exe"}  # programa.exe va con su .dll
    assert rutas(informe.basura) == {"DAM/Thumbs.db", "DAM/~$trabajo.docx", "Descargas/pelicula.mp4.crdownload"}
    assert rutas(informe.regenerables) == {"repos/web/.venv", "repos/web/front/node_modules"}
    assert inventario.en_disco(informe.regenerables) == 500
    # lo de dentro de .git y de las regenerables no se cuenta por tipo
    assert informe.cuantos_por_tipo["codigo"] == 1  # solo main.py


def test_ficheros_grandes(tmp_path, monkeypatch):
    monkeypatch.setattr(inventario, "LIMITE_GRANDE", 100)
    escribir(tmp_path / "grande.iso", 150)
    escribir(tmp_path / "pequeno.txt", 50)
    informe = inventario.revisar(tmp_path)
    assert rutas(informe.grandes) == {"grande.iso"}


def test_no_sigue_enlaces(tmp_path):
    escribir(tmp_path / "datos" / "a.pdf", 100)
    enlace = tmp_path / "enlace"
    try:
        os.symlink(tmp_path / "datos", enlace, target_is_directory=True)
    except OSError:
        pytest.skip("Este sistema no deja crear enlaces sin permisos de administrador")
    informe = inventario.revisar(tmp_path)
    assert informe.tamano == 100  # no lo cuenta dos veces
    assert "enlace" in informe.saltadas


@pytest.mark.skipif(os.name != "nt", reason="Las junctions solo existen en Windows")
def test_no_sigue_junctions_de_windows(tmp_path):
    """Como «Mis documentos» o «Datos de programa» en la carpeta de usuario."""
    import _winapi
    escribir(tmp_path / "datos" / "a.pdf", 100)
    _winapi.CreateJunction(str(tmp_path / "datos"), str(tmp_path / "Mis documentos"))
    informe = inventario.revisar(tmp_path)
    assert informe.tamano == 100
    assert "Mis documentos" in informe.saltadas


def test_no_cambia_nada(pc):
    antes = sorted((p, p.stat().st_size) for p in pc.rglob("*"))
    inventario.revisar(pc)
    assert sorted((p, p.stat().st_size) for p in pc.rglob("*")) == antes


def test_carpeta_que_no_existe(tmp_path):
    r = run.invoke(app, ["inventario", str(tmp_path / "no-existe")])
    assert r.exit_code == 1
    assert "no existe" in r.output


def test_cli_enseña_el_resumen(pc):
    r = run.invoke(app, ["inventario", str(pc)])
    assert r.exit_code == 0, r.output
    for texto in ("Tamaño por carpeta", "Por tipo", "Repos git (2)", "setup.exe", "Thumbs.db", "node_modules"):
        assert texto in r.output
    assert "Traceback" not in r.output


def test_cli_guarda_el_informe_en_markdown(pc, tmp_path):
    destino = tmp_path / "informes" / "inventario.md"
    r = run.invoke(app, ["inventario", str(pc), "--guardar", str(destino)])
    assert r.exit_code == 0, r.output
    texto = destino.read_text(encoding="utf-8")
    assert texto.startswith("# Inventario de")
    assert "`repos/web`" in texto and "## Basura (3" in texto
    # repetir la orden puede sobrescribir su propio informe
    assert run.invoke(app, ["inventario", str(pc), "--guardar", str(destino)]).exit_code == 0


def test_cli_no_sobrescribe_otro_md(pc, tmp_path):
    ajeno = tmp_path / "apuntes.md"
    ajeno.write_text("# Mis apuntes\n", encoding="utf-8")
    r = run.invoke(app, ["inventario", str(pc), "--guardar", str(ajeno)])
    assert r.exit_code == 1
    assert "no lo sobrescribo" in " ".join(r.output.split())  # Rich parte las líneas largas
    assert ajeno.read_text(encoding="utf-8") == "# Mis apuntes\n"


def test_cli_guardar_exige_md(pc, tmp_path):
    r = run.invoke(app, ["inventario", str(pc), "--guardar", str(tmp_path / "informe.txt")])
    assert r.exit_code == 1
    assert ".md" in r.output


# ---------- programas: miniconda3 y carpetas ocultas ----------
def test_programas_se_miden_pero_no_se_mezclan(tmp_path):
    escribir(tmp_path / ".vscode" / "extensions" / "ext" / "bin" / "claude.exe", 300)
    escribir(tmp_path / ".vscode" / "extensions" / "otra" / "node_modules" / "a.js", 50)
    escribir(tmp_path / "miniconda3" / "pkgs" / "paquete" / "suite" / ".git" / "HEAD", 2)
    escribir(tmp_path / "Descargas" / "setup.exe", 100)
    repo = tmp_path / "repo"
    escribir(repo / ".git" / "HEAD", 2)
    escribir(repo / ".github" / "workflows" / "ci.yml", 10)  # dentro de un repo, lo oculto es tuyo
    informe = inventario.revisar(tmp_path)
    assert rutas(informe.instaladores) == {"Descargas/setup.exe"}
    assert rutas(informe.regenerables) == set()
    assert [r.ruta for r in informe.repos] == ["repo"]
    assert {f.ruta: f.tamano for f in informe.programas} == {".vscode": 350, "miniconda3": 2}
    assert informe.tamano == 300 + 50 + 2 + 100 + 2 + 10  # se cuenta todo, aunque no se liste
    assert informe.cuantos_por_tipo["codigo"] == 1  # ci.yml


# ---------- OneDrive: «solo en la nube» ----------
@pytest.mark.parametrize("atributos, esperado", [
    (0x400020, True),   # RECALL_ON_DATA_ACCESS: lo que pone OneDrive a lo que no está descargado
    (0x1000, True),     # OFFLINE
    (0x20, False),      # ARCHIVE: un fichero normal
])
def test_esta_en_la_nube_por_atributos(atributos, esperado):
    from types import SimpleNamespace
    assert inventario.esta_en_la_nube(SimpleNamespace(st_file_attributes=atributos)) is esperado


def test_en_linux_y_macos_nunca_esta_en_la_nube():
    from types import SimpleNamespace
    assert inventario.esta_en_la_nube(SimpleNamespace(st_size=10)) is False


@pytest.fixture
def con_nube(tmp_path, monkeypatch):
    """Los ficheros de 777 bytes hacen de marcadores de OneDrive (en los tests no se puede poner el atributo)."""
    monkeypatch.setattr(inventario, "esta_en_la_nube", lambda datos: datos.st_size == 777)
    escribir(tmp_path / "OneDrive" / "ubuntu.iso", 777)
    escribir(tmp_path / "OneDrive" / "apuntes.pdf", 20)
    escribir(tmp_path / "Desktop" / "setup.exe", 100)
    return tmp_path


def test_lo_de_la_nube_no_cuenta_como_disco(con_nube):
    informe = inventario.revisar(con_nube)
    assert informe.tamano == 120
    assert informe.tamano_nube == 777
    assert informe.por_carpeta["OneDrive"] == 20
    assert informe.por_carpeta_nube["OneDrive"] == 777
    assert informe.tamano_por_tipo["instaladores"] == 100
    assert informe.nube_por_tipo["instaladores"] == 777
    assert {f.ruta: f.en_nube for f in informe.instaladores} == {"OneDrive/ubuntu.iso": True, "Desktop/setup.exe": False}
    assert inventario.resumen_tamano(informe.instaladores) == "100 B en el disco · 777 B en la nube"


def test_cli_separa_disco_y_nube(con_nube, tmp_path):
    r = run.invoke(app, ["inventario", str(con_nube), "--guardar", str(tmp_path / "inv.md")])
    assert r.exit_code == 0, r.output
    salida = " ".join(r.output.split())
    assert "120 B en el disco · 777 B solo en la nube" in salida
    assert "Solo en la nube" in r.output and "nube" in r.output
    texto = (tmp_path / "inv.md").read_text(encoding="utf-8")
    assert "| `OneDrive/ubuntu.iso` | 777 B | nube |" in texto


def test_sin_nube_no_salen_columnas_de_nube(pc):
    r = run.invoke(app, ["inventario", str(pc)])
    assert "Solo en la nube" not in r.output
    assert "sin remoto configurado" in " ".join(r.output.split())
