"""scan-secrets. Las claves falsas se montan por trozos para que este fichero NO parezca un secreto."""
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import escanear
from tareas.cli import app
from tareas.errores import TareasError

R = "aB3dE6gH9jK2mN5pQ8sT1vW4yZ7cF0hJ3kL6"  # relleno alfanumérico de 36 caracteres
FALSAS = {
    "github": "gh" + "p_" + R,
    "google": "AI" + "za" + R[:35],
    "resend": "r" + "e_" + R[:24],
    "aws": "AK" + "IA" + "7Q3M9X2B5C8D1F4G"[:16],
    "slack": "xo" + "xb-" + "1234567890-abcdefghij",
    "openai": "s" + "k-" + R[:30],
    "mongo": "mongodb" + "+srv:" + "//gabi:Pa55w0rdReal@cluster0.abcde.mongodb.net/db",
    "privada": "-----BEGIN " + "RSA PRIVATE KEY-----",
    "generica": 'DB_PASSWORD = "' + R[:14] + '"',
    "jwt": "e" + "yJ" + R[:20] + ".e" + "yJ" + R[:20] + "." + R[:24],
}


@pytest.fixture(autouse=True)
def identidad(monkeypatch):
    for k, v in {"GIT_AUTHOR_NAME": "T", "GIT_AUTHOR_EMAIL": "t@t.es",
                 "GIT_COMMITTER_NAME": "T", "GIT_COMMITTER_EMAIL": "t@t.es"}.items():
        monkeypatch.setenv(k, v)


def git(carpeta: Path, *args):
    subprocess.run(["git", "-C", str(carpeta), *args], check=True, capture_output=True, encoding="utf-8")


def escribir(ruta: Path, texto: str):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-b", "main", str(tmp_path)], check=True, capture_output=True)
    escribir(tmp_path / ".gitignore", ".env\n")
    escribir(tmp_path / "README.md", "limpio")
    git(tmp_path, "add", "-A"); git(tmp_path, "commit", "-m", "inicial")
    return tmp_path


@pytest.mark.parametrize("clave", sorted(FALSAS))
def test_detecta_cada_tipo(clave):
    encontrados = escanear.analizar_linea("x = " + FALSAS[clave] if clave != "generica" else FALSAS[clave])
    assert encontrados, clave
    assert any(c == ("alta" if clave != "generica" else "posible") for _, _, c in encontrados)


@pytest.mark.parametrize("linea", [
    'api_key = "your_api_key_here"',
    '"apiKey": "{env:CENTRO_IA_KEY}"',
    "token = os.environ['TOKEN_SECRETO_1']",
    "password = input('Contraseña: ')",
    "AWS = AKIAIOSFODNN7EXAMPLE",
    "mongodb+srv://<usuario>:<contraseña>@cluster.mongodb.net",
    "MONGODB_URI=mongodb+srv://usuario:password@cluster.mongodb.net/portfolio",
    "DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres",
    "DATABASE_URL=postgresql://postgres:tu_contraseña@db.abcdefg.supabase.co:5432/postgres",
    "SUPABASE_SERVICE_KEY=eyJ...",
    "OPENAI_API_KEY=sk-...",
    "secret = valorsinnumeros",
    "def get_token(self): pass",
])
def test_no_avisa_con_marcadores_ni_codigo(linea):
    assert escanear.analizar_linea(linea) == []


def test_dam_ignore_salta_la_linea():
    assert escanear.analizar_linea(FALSAS["github"] + "  # dam:ignore") == []


def test_la_muestra_nunca_es_el_secreto_entero():
    for clave, valor in FALSAS.items():
        for h in escanear._hallazgos_de_texto("f", f"x = {valor}\n", False):
            assert valor not in h.muestra and R[:20] not in h.muestra


def test_arbol_respeta_gitignore_y_avisa_de_env_sin_ignorar(repo):
    escribir(repo / ".env", "TOKEN=" + R)          # ignorado: no cuenta
    escribir(repo / "config.env", "A=1")            # NO ignorado: peligro
    escribir(repo / ".env.example", "TOKEN=tu_clave_aqui")
    hallazgos, revisados, _ = escanear.escanear_arbol(repo)
    assert [h.donde for h in hallazgos] == ["config.env"]
    assert revisados >= 2


def test_arbol_claves_privadas_binarios_y_enormes(repo):
    escribir(repo / "servidor.pem", "lo que sea")
    (repo / "foto.bin").write_bytes(b"\0\1\2" + FALSAS["github"].encode())
    (repo / "grande.txt").write_text("a" * (escanear.MAX_BYTES + 10))
    escribir(repo / "ok.pub", "publica"); escribir(repo / "id_rsa.pub", "publica")
    hallazgos, _, omitidos = escanear.escanear_arbol(repo)
    assert [h.tipo for h in hallazgos] == ["Fichero de clave privada"]
    assert omitidos == 2


def test_arbol_sin_git_salta_venv_y_node_modules(tmp_path):
    escribir(tmp_path / ".venv/lib/x.py", "k = " + FALSAS["github"])
    escribir(tmp_path / "node_modules/y.js", "k = " + FALSAS["github"])
    escribir(tmp_path / "app.py", "k = " + FALSAS["github"])
    hallazgos, _, _ = escanear.escanear_arbol(tmp_path)
    assert [h.donde for h in hallazgos] == ["app.py"] and hallazgos[0].linea == 1


def test_staged_solo_mira_lo_preparado(repo):
    escribir(repo / "a.py", "k = " + FALSAS["github"]); git(repo, "add", "a.py")
    escribir(repo / "b.py", "k = " + FALSAS["google"])      # sin git add
    hallazgos = escanear.escanear_staged(repo)
    assert [(h.donde, h.linea) for h in hallazgos] == [("a.py", 1)]
    git(repo, "reset", "-q"); assert escanear.escanear_staged(repo) == []


def test_historial_encuentra_claves_ya_borradas(repo):
    escribir(repo / "app.py", "ok = 1\nk = " + FALSAS["resend"] + "\n")
    git(repo, "add", "-A"); git(repo, "commit", "-m", "mala idea")
    escribir(repo / "app.py", "ok = 1\n")                    # la «arreglo» después
    git(repo, "add", "-A"); git(repo, "commit", "-m", "la quito")
    assert escanear.escanear_arbol(repo)[0] == []            # el árbol está limpio...
    hallazgos = escanear.escanear_historial(repo)            # ...pero el historial no
    assert len(hallazgos) == 1 and hallazgos[0].donde.endswith(":app.py") and hallazgos[0].linea == 2


def test_historial_y_staged_exigen_repo(tmp_path):
    for funcion in (escanear.escanear_historial, escanear.escanear_staged):
        with pytest.raises(TareasError, match="no es un repositorio"):
            funcion(tmp_path)


def test_cli_limpio_sale_con_0_y_sucio_con_1_sin_enseñar_el_secreto(repo):
    run = CliRunner()
    r = run.invoke(app, ["scan-secrets", str(repo)])
    assert r.exit_code == 0 and "Sin claves a la vista" in r.output
    escribir(repo / "app.py", "k = " + FALSAS["github"])
    r = run.invoke(app, ["scan-secrets", str(repo)])
    assert r.exit_code == 1 and "Token de GitHub" in r.output and "app.py" in r.output
    assert FALSAS["github"] not in r.output and R not in r.output


def test_cli_opciones(repo):
    run = CliRunner()
    escribir(repo / "a.py", "DB_PASSWORD = '" + R[:14] + "'")
    assert run.invoke(app, ["scan-secrets", str(repo)]).exit_code == 1
    assert run.invoke(app, ["scan-secrets", str(repo), "--alta"]).exit_code == 0
    assert run.invoke(app, ["scan-secrets", str(repo), "--staged", "--historial"]).exit_code == 2
    assert run.invoke(app, ["scan-secrets", str(repo / "nada")]).exit_code == 1


def test_el_propio_proyecto_esta_limpio():
    raiz = Path(__file__).resolve().parents[1]
    for carpeta in ("src", "tests", "docs"):
        hallazgos, _, _ = escanear.escanear_arbol(raiz / carpeta)
        assert hallazgos == [], hallazgos


def test_url_con_clave_que_parece_real_sigue_avisando():
    real = "mongodb" + "+srv:" + "//gabi:" + R[:12] + "@cluster0.ab1cd.mongodb.net/db"
    assert escanear.analizar_linea("MONGODB_URI=" + real)


def test_pdf_y_documentos_no_se_leen_como_texto(repo):
    # un PDF «de texto» (sin ceros) con algo que parece una asignación sospechosa
    (repo / "apuntes.pdf").write_bytes(b"%PDF-1.4\nstream\nsecret=" + R[:14].encode() + b"\nendstream")
    (repo / "notas.docx").write_bytes(b"PK\x03\x04 token=" + R[:14].encode())
    (repo / "imagen.dat").write_bytes(b"\x89PNG\r\n token=" + R[:14].encode())
    hallazgos, revisados, omitidos = escanear.escanear_arbol(repo)
    assert hallazgos == [] and omitidos == 3


def test_historial_tampoco_lee_pdfs(repo):
    (repo / "x.pdf").write_bytes(b"%PDF-1.4\nsecret=" + R[:14].encode() + b"\n")
    git(repo, "add", "-A"); git(repo, "commit", "-m", "pdf")
    assert escanear.escanear_historial(repo) == []
