"""dam duplicados. Carpetas de mentira en tmp_path: nunca se recorre el PC de verdad."""
import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import duplicados
from tareas.cli import app

run = CliRunner()


def escribir(ruta: Path, contenido: bytes | str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(contenido.encode() if isinstance(contenido, str) else contenido)


def grupos(informe) -> list[list[str]]:
    return sorted(g.rutas for g in informe.grupos)


def copias(informe) -> dict[str, str | None]:
    return {c.ruta: c.original for c in informe.carpetas_copia}


@pytest.fixture
def datos(tmp_path) -> Path:
    """Como ~/Datos el 10-nov: una carpeta auxiliar que ya estaba entera en el almacén."""
    raiz = tmp_path / "Datos"
    for nombre, texto in {"notas.txt": "notas del proyecto", "img/logo.png": "PNG-logo", "img/fondo.png": "PNG-fondo"}.items():
        escribir(raiz / "DAM" / "AUX" / "1 PROJECTE" / nombre, texto)
        escribir(raiz / "REPOS" / "ALMACEN" / "asignaturas" / "1 PROJECTE" / nombre, texto)
    escribir(raiz / "REPOS" / "ALMACEN" / ".git" / "HEAD", "ref: refs/heads/main")
    # en la carpeta del grupo hay uno repetido y uno único: NO es copia completa
    escribir(raiz / "DAM" / "AUX" / "GRUPO" / "presentacion.pdf", "PDF-presentacion")
    escribir(raiz / "DAM" / "AUX" / "GRUPO" / "gestor-corregido.odt", "solo existe aquí")
    escribir(raiz / "PERSONAL" / "presentacion.pdf", "PDF-presentacion")
    # mismo tamaño, distinto contenido: no son iguales
    escribir(raiz / "SMX" / "a.txt", "aaaa")
    escribir(raiz / "SMX" / "b.txt", "bbbb")
    return raiz


def test_iguales_por_contenido_aunque_cambie_el_nombre(tmp_path):
    escribir(tmp_path / "apuntes.pdf", "mismo contenido")
    escribir(tmp_path / "copia" / "apuntes (1).pdf", "mismo contenido")
    escribir(tmp_path / "otro.pdf", "otro contenido!")  # mismo tamaño, distinto contenido
    informe = duplicados.revisar(tmp_path)
    assert grupos(informe) == [["apuntes.pdf", "copia/apuntes (1).pdf"]]
    assert informe.sobra == len("mismo contenido")


def test_mismo_principio_pero_distinto_final(tmp_path, monkeypatch):
    monkeypatch.setattr(duplicados, "PRINCIPIO", 4)
    escribir(tmp_path / "v1.mkv", "CABECERA-final-1")
    escribir(tmp_path / "v2.mkv", "CABECERA-final-2")
    escribir(tmp_path / "v3.mkv", "CABECERA-final-1")
    assert grupos(duplicados.revisar(tmp_path)) == [["v1.mkv", "v3.mkv"]]


def test_vacios_no_cuentan(tmp_path):
    escribir(tmp_path / "a.txt", "")
    escribir(tmp_path / "b.txt", "")
    informe = duplicados.revisar(tmp_path)
    assert informe.grupos == [] and informe.ficheros == 0


def test_carpeta_copia_completa_con_su_original(datos):
    informe = duplicados.revisar(datos)
    # la del almacén es la misma pareja vista desde el otro lado: sale solo la de fuera del repo
    assert copias(informe) == {"DAM/AUX/1 PROJECTE": "REPOS/ALMACEN/asignaturas/1 PROJECTE"}
    aux = next(c for c in informe.carpetas_copia if c.ruta == "DAM/AUX/1 PROJECTE")
    assert aux.ficheros == 3
    # la subcarpeta img también es copia, pero ya sale la de arriba
    assert "DAM/AUX/1 PROJECTE/img" not in copias(informe)
    # GRUPO tiene un fichero único: no es copia; AUX tampoco (contiene GRUPO)
    assert "DAM/AUX/GRUPO" not in copias(informe) and "DAM/AUX" not in copias(informe)


def test_una_carpeta_con_un_repo_nunca_es_copia(datos):
    """Aunque todos sus ficheros estén repetidos, su .git no se compara: borrarla perdería el historial."""
    informe = duplicados.revisar(datos)
    assert "REPOS" not in copias(informe) and "REPOS/ALMACEN" not in copias(informe)


def test_mayusculas_no_cambian_la_estructura(tmp_path):
    """En Windows «Entrega final/Fotos» y «ENTREGA FINAL/FOTOS» son la misma carpeta."""
    for nombre, texto in {"index.html": "<html>", "Fotos/a.jpg": "jpg-a"}.items():
        escribir(tmp_path / "SMX" / "ENTREGA FINAL" / nombre.upper(), texto)
        escribir(tmp_path / "REPO" / "Entrega final" / nombre, texto)
    escribir(tmp_path / "SMX" / "notas.txt", "solo en SMX")  # para que SMX y REPO no sean copia enteras
    escribir(tmp_path / "REPO" / "README.md", "solo en REPO")
    assert copias(duplicados.revisar(tmp_path)) == {"REPO/Entrega final": "SMX/ENTREGA FINAL"}


def test_parejas_salen_una_vez_y_primero_fuera_del_repo(tmp_path):
    for i in range(3):
        escribir(tmp_path / "web" / "img" / f"{i}.png", f"imagen {i}")
        escribir(tmp_path / "repo" / "img" / f"{i}.png", f"imagen {i}")
    escribir(tmp_path / "repo" / "web.html", "solo en el repo")  # para que el repo no sea copia entero
    escribir(tmp_path / "repo" / ".git" / "HEAD", "ref")
    informe = duplicados.revisar(tmp_path)
    assert copias(informe) == {"web": "repo"}  # la de fuera del repo es la que se puede borrar sin commit


def test_cli_top_limita_tambien_las_carpetas(tmp_path):
    for carpeta in ("a", "b", "c"):
        for i in range(2):
            escribir(tmp_path / carpeta / f"{i}.txt", f"carpeta {carpeta} {i}")
            escribir(tmp_path / f"{carpeta}-copia" / "dentro" / f"{i}.txt", f"carpeta {carpeta} {i}")
    r = run.invoke(app, ["duplicados", str(tmp_path), "--top", "1"])
    assert r.exit_code == 0
    salida = " ".join(r.output.split())
    assert "…y 2 más" in salida


def test_copia_repartida_en_varios_sitios(tmp_path):
    escribir(tmp_path / "mezcla" / "a.txt", "contenido A")
    escribir(tmp_path / "mezcla" / "b.txt", "contenido B")
    escribir(tmp_path / "uno" / "a.txt", "contenido A")
    escribir(tmp_path / "dos" / "otro-nombre.txt", "contenido B")
    assert copias(duplicados.revisar(tmp_path))["mezcla"] is None


def test_copia_dentro_de_la_misma_carpeta_no_la_hace_copia(tmp_path):
    """Si las dos copias están dentro, la carpeta no tiene nada «fuera»: no se puede borrar entera."""
    escribir(tmp_path / "fotos" / "a.jpg", "foto")
    escribir(tmp_path / "fotos" / "a (1).jpg", "foto")
    informe = duplicados.revisar(tmp_path)
    assert len(informe.grupos) == 1
    assert copias(informe) == {}


def test_marca_lo_que_esta_en_un_repo(datos):
    informe = duplicados.revisar(datos)
    assert informe.repos == ["REPOS/ALMACEN"]
    assert informe.repo_de("REPOS/ALMACEN/asignaturas/1 PROJECTE/notas.txt") == "REPOS/ALMACEN"
    assert informe.repo_de("DAM/AUX/1 PROJECTE/notas.txt") is None
    assert informe.repo_de("REPOS/ALMACEN-viejo/x.txt") is None  # no basta con que empiece igual


def test_se_salta_git_regenerables_y_sistema(tmp_path):
    for carpeta in ("repo/.git/objects", "repo/.venv/lib", "web/node_modules/a", "AppData/Local"):
        escribir(tmp_path / carpeta / "igual.bin", "repetido en todas partes")
    escribir(tmp_path / "repo" / ".git" / "HEAD", "ref")
    informe = duplicados.revisar(tmp_path)
    assert informe.grupos == []


def test_enlace_duro_no_es_una_copia(tmp_path):
    escribir(tmp_path / "a.pdf", "un solo fichero")
    try:
        os.link(tmp_path / "a.pdf", tmp_path / "otro-nombre.pdf")
    except OSError:
        pytest.skip("Este sistema no deja crear enlaces duros aquí")
    assert duplicados.revisar(tmp_path).grupos == []


def test_no_lee_lo_que_esta_en_la_nube(tmp_path, monkeypatch):
    """Leer un fichero «solo en la nube» lo descargaría: ni se abre."""
    monkeypatch.setattr(duplicados, "esta_en_la_nube", lambda datos: datos.st_size == 7)
    escribir(tmp_path / "OneDrive" / "a.iso", "1234567")
    escribir(tmp_path / "OneDrive" / "b.iso", "1234567")
    leer = duplicados.huella
    monkeypatch.setattr(duplicados, "huella", lambda ruta, hasta=None: (_ for _ in ()).throw(AssertionError(ruta))
                        if ruta.stat().st_size == 7 else leer(ruta, hasta))
    informe = duplicados.revisar(tmp_path)
    assert informe.grupos == [] and informe.en_nube == 2


def test_no_cambia_nada(datos):
    antes = sorted((p, p.stat().st_size, p.stat().st_mtime_ns) for p in datos.rglob("*"))
    duplicados.revisar(datos)
    assert sorted((p, p.stat().st_size, p.stat().st_mtime_ns) for p in datos.rglob("*")) == antes


def test_huella_entera_y_del_principio(tmp_path):
    escribir(tmp_path / "f", "abcdef")
    assert duplicados.huella(tmp_path / "f") != duplicados.huella(tmp_path / "f", 3)
    escribir(tmp_path / "g", "abcXYZ")
    assert duplicados.huella(tmp_path / "f", 3) == duplicados.huella(tmp_path / "g", 3)


# ---------- la orden ----------
def test_cli_carpeta_que_no_existe(tmp_path):
    r = run.invoke(app, ["duplicados", str(tmp_path / "no-existe")])
    assert r.exit_code == 1
    assert "no existe" in " ".join(r.output.split())  # Rich puede partir la línea


def test_cli_ensena_carpetas_y_grupos(datos):
    r = run.invoke(app, ["duplicados", str(datos)])
    assert r.exit_code == 0, r.output
    salida = " ".join(r.output.split())
    for texto in ("Carpetas que son copia de otra", "Ficheros repetidos", "4 grupos repetidos",
                  "(repo)", "no borra nada", "presentacion.pdf"):
        assert texto in salida, texto
    assert "Traceback" not in r.output


def test_cli_sin_duplicados(tmp_path):
    escribir(tmp_path / "a.txt", "uno")
    r = run.invoke(app, ["duplicados", str(tmp_path)])
    assert r.exit_code == 0
    assert "No hay ficheros repetidos" in r.output


def test_cli_guarda_el_informe(datos, tmp_path):
    destino = tmp_path / "informes" / "duplicados.md"
    r = run.invoke(app, ["duplicados", str(datos), "--guardar", str(destino)])
    assert r.exit_code == 0, r.output
    texto = destino.read_text(encoding="utf-8")
    assert texto.startswith("# Duplicados de")
    assert "| `DAM/AUX/1 PROJECTE` | 3 |" in texto
    assert "`REPOS/ALMACEN/asignaturas/1 PROJECTE/notas.txt` (repo)" in texto
    # repetir la orden puede sobrescribir su propio informe
    assert run.invoke(app, ["duplicados", str(datos), "--guardar", str(destino)]).exit_code == 0


def test_cli_no_sobrescribe_otro_md(datos, tmp_path):
    ajeno = tmp_path / "apuntes.md"
    ajeno.write_text("# Mis apuntes\n", encoding="utf-8")
    r = run.invoke(app, ["duplicados", str(datos), "--guardar", str(ajeno)])
    assert r.exit_code == 1
    assert "no lo sobrescribo" in " ".join(r.output.split())
    assert ajeno.read_text(encoding="utf-8") == "# Mis apuntes\n"


def test_cli_top_limita_los_grupos(tmp_path):
    for i in range(5):
        escribir(tmp_path / "a" / f"{i}.txt", f"contenido {i}")
        escribir(tmp_path / "b" / f"{i}.txt", f"contenido {i}")
    r = run.invoke(app, ["duplicados", str(tmp_path), "--top", "2"])
    assert r.exit_code == 0
    assert "…y 3 grupos más" in " ".join(r.output.split())
