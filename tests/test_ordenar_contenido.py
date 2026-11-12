"""ordenar lee por dentro los documentos de LibreOffice y Office y mete cada fichero en la carpeta
de su unidad («unitat 1», «UD01», «Tema 1»...) si la asignatura ya la tiene.

Caso real (12-nov): «Examen_A_cas_plantilla_part_1.odt», un examen de recuperación de Sistemas. El
nombre no dice nada; la cabecera de la página dice «SI – Sistemes Informàtics UD-01».
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from tareas.acciones import Ordenar, carpeta_de_unidad, leer_texto, texto_ofimatica, unidad_de
from tareas.motor import Motor

CARPETAS = {
    "sistemas": ["sistemes", "sistemas", "sistemes informatics", "linux", "redes"],
    "programacion": ["programacion", "programacio", "python", "java"],
}


def documento(ruta: Path, partes: dict[str, str]) -> Path:
    """Un documento de mentira: un zip con esos XML dentro (como un .odt o un .docx de verdad)."""
    with zipfile.ZipFile(ruta, "w") as z:
        for nombre, xml in partes.items():
            z.writestr(nombre, xml)
    return ruta


def odt(ruta: Path, cabecera: str, cuerpo: str) -> Path:
    """Un .odt con la cabecera de la página en styles.xml (donde la guarda LibreOffice)."""
    return documento(ruta, {
        "mimetype": "application/vnd.oasis.opendocument.text",
        "styles.xml": f"<office:document-styles><style:header><text:p>{cabecera}</text:p></style:header></office:document-styles>",
        "content.xml": f"<office:document-content><office:body><text:p>{cuerpo}</text:p></office:body></office:document-content>",
    })


def ordenar(**extra) -> Ordenar:
    return Ordenar({"nombre": "o", "descripcion": "d", "tipo": "ordenar", "carpetas": CARPETAS, **extra})


# ---------- texto de los documentos ----------
def test_odt_cabecera_primero_y_sin_partir_palabras(tmp_path):
    f = odt(tmp_path / "examen.odt",
            "SI – Sistemes Inform<text:span>àtics</text:span><text:s/>UD-01",
            "Rúbrica de correcció &amp; notes<text:tab/>finals")
    texto = texto_ofimatica(f)
    assert texto.splitlines()[0] == "SI – Sistemes Informàtics UD-01"  # la cabecera, lo primero
    assert "Rúbrica de correcció & notes finals" in texto


def test_docx_cabecera_cuerpo_y_pie(tmp_path):
    f = documento(tmp_path / "a.docx", {
        "word/document.xml": "<w:document><w:body><w:p><w:r><w:t>Cuer</w:t></w:r><w:r><w:t>po</w:t></w:r></w:p></w:body></w:document>",
        "word/header1.xml": "<w:hdr><w:p><w:r><w:t>Programació · Tema 3</w:t></w:r></w:p></w:hdr>",
        "word/styles.xml": "<w:styles><w:style><w:name w:val='Normal'/></w:style></w:styles>",
    })
    assert texto_ofimatica(f).splitlines() == ["Programació · Tema 3", "Cuerpo"]


def test_pptx_en_orden_de_diapositiva_y_xlsx(tmp_path):
    diapositivas = {f"ppt/slides/slide{n}.xml": f"<p:sld><a:p><a:r><a:t>diapo {n}</a:t></a:r></a:p></p:sld>" for n in (10, 2, 1)}
    assert texto_ofimatica(documento(tmp_path / "a.pptx", diapositivas)).split("\n") == ["diapo 1", "diapo 2", "diapo 10"]
    hoja = documento(tmp_path / "a.xlsx", {"xl/sharedStrings.xml": "<sst><si><t>Notas UD2</t></si></sst>"})
    assert texto_ofimatica(hoja) == "Notas UD2"


@pytest.mark.parametrize("contenido", [b"no soy un zip", b"PK\x03\x04 roto"])
def test_documento_roto_da_vacio(tmp_path, contenido):
    f = tmp_path / "roto.odt"
    f.write_bytes(contenido)
    assert texto_ofimatica(f) == ""


def test_unos_apuntes_de_spam_van_a_seguridad_aunque_hablen_de_redes(tmp_path):
    """12-nov, con mis apuntes de SMX: «Spamhause.odt» iba a redes-locales (redes, red, tcp) en vez
    de a seguridad (solo encontraba firewall)."""
    from tareas import ciclos

    ordenar = Ordenar({"nombre": "o", "descripcion": "o", "tipo": "ordenar",
                       "carpetas": ciclos.asignaturas_de("smx", [1, 2])})
    f = odt(tmp_path / "Spamhause.odt", "",
            "Spamhaus publica una lista negra de redes y servidores que envían spam por TCP. "
            "Con iptables y un firewall puedes bloquear las direcciones maliciosas en tu red.")
    assert ordenar.clasificar(f) == "seguridad"


def test_leer_texto_de_un_odt_no_es_basura(tmp_path):
    """Antes, «clasificar» leía el .odt como texto: le mandaba al modelo el zip tal cual."""
    f = odt(tmp_path / "apuntes.odt", "Sistemes Informàtics", "La CPU i la memòria")
    texto = leer_texto(f, 1000)
    assert "La CPU i la memòria" in texto and "PK" not in texto
    assert len(leer_texto(f, 10)) == 10


# ---------- la unidad ----------
@pytest.mark.parametrize("texto, unidad", [
    ("si sistemes informatics ud 01", 1),    # «UD-01» normalizado
    ("apuntes so tema1", 1),
    ("unitat 2 arquitectura", 2),
    ("unidad 03", 3),
    ("u d 4 practica", 4),                  # «U.D. 4»
    ("unit 12", 12),
    ("ud 01 recuperacio ud 01", 1),          # la misma dos veces: vale
    ("tema 1 tema 2 tema 3", None),         # un índice: no se sabe
    ("1r bloc 1r dam 1 avaluacio", None),
    ("salud 3", None),                      # «ud» dentro de otra palabra no cuenta
    ("ud 2026", None),                      # un año no es una unidad
    ("", None),
])
def test_unidad_de(texto, unidad):
    assert unidad_de(texto) == unidad


def test_carpeta_de_unidad(tmp_path):
    for ruta in ("1 Avaluacio/unitat 1/Examen recuperacion", "1 Avaluacio/unitat 2", "Apuntes Internet",
                 "UD03", "a/b/c/Tema 4", ".git/ud5"):
        (tmp_path / ruta).mkdir(parents=True)
    assert carpeta_de_unidad(tmp_path, 1) == tmp_path / "1 Avaluacio" / "unitat 1"
    assert carpeta_de_unidad(tmp_path, 3) == tmp_path / "UD03"
    assert carpeta_de_unidad(tmp_path, 4) is None   # a 4 niveles: demasiado abajo
    assert carpeta_de_unidad(tmp_path, 5) is None   # las carpetas ocultas no cuentan
    assert carpeta_de_unidad(tmp_path, 9) is None


def test_carpeta_de_unidad_la_de_mas_arriba_y_si_empatan_ninguna(tmp_path):
    (tmp_path / "UD1").mkdir()
    (tmp_path / "2 Avaluacio" / "unitat 1").mkdir(parents=True)
    assert carpeta_de_unidad(tmp_path, 1) == tmp_path / "UD1"
    (tmp_path / "Tema 1").mkdir()
    assert carpeta_de_unidad(tmp_path, 1) is None  # «UD1» y «Tema 1»: no sé cuál es


# ---------- ordenar ----------
def test_el_examen_del_caso_real(tmp_path):
    f = odt(tmp_path / "Examen_A_cas_plantilla_part_1.odt",
            "SI – Sistemes Informàtics UD-01",
            "Rúbrica de correcció. Si hi ha algun exercici copiat, es qualificarà amb 0 punts.")
    assert ordenar().analizar(f) == ("sistemas", 1)


def test_la_unidad_del_nombre_manda_sobre_la_del_contenido(tmp_path, monkeypatch):
    monkeypatch.setattr("tareas.acciones._texto_pdf", lambda ruta: "Unitat 2 Arquitectura d'ordinadors")
    f = tmp_path / "UD-01-sistemas.pdf"
    f.write_bytes(b"%PDF")
    assert ordenar().analizar(f) == ("sistemas", 1)


def test_la_unidad_solo_se_busca_al_principio_del_contenido(tmp_path, monkeypatch):
    monkeypatch.setattr("tareas.acciones._texto_pdf", lambda ruta: "x " * 1000 + "tema 7")
    f = tmp_path / "linux.pdf"
    f.write_bytes(b"%PDF")
    assert ordenar().analizar(f) == ("sistemas", None)


def test_sin_asignatura_tampoco_hay_unidad(tmp_path):
    f = odt(tmp_path / "cosa.odt", "UD-01", "nada que ver")
    assert ordenar().analizar(f) == (None, None)


def entregar(tmp_path: Path, **extra):
    """Una carpeta de descargas con el examen y un almacén con sistemas/1 Avaluacio/unitat 1."""
    descargas = tmp_path / "Descargas"
    descargas.mkdir()
    odt(descargas / "Examen_A_cas_plantilla_part_1.odt", "SI – Sistemes Informàtics UD-01", "Rúbrica")
    destino = tmp_path / "asignaturas"
    (destino / "sistemas" / "1 Avaluacio" / "unitat 1").mkdir(parents=True)
    (destino / "programacion").mkdir()
    accion = {"nombre": "o", "descripcion": "d", "tipo": "ordenar", "carpetas": CARPETAS,
              "destino": str(destino), **extra}
    return Motor([accion]), descargas, destino


def test_ordenar_lo_mete_en_la_carpeta_de_su_unidad(tmp_path):
    motor, descargas, destino = entregar(tmp_path)
    [simulado] = motor.ejecutar("o", descargas, simular=True)
    assert simulado.estado == "simulado" and simulado.nota == "unidad 1"
    assert simulado.destino == destino / "sistemas" / "1 Avaluacio" / "unitat 1" / "Examen_A_cas_plantilla_part_1.odt"
    assert (descargas / "Examen_A_cas_plantilla_part_1.odt").exists()  # simulando no se toca
    [hecho] = motor.ejecutar("o", descargas, simular=False)
    assert hecho.estado == "hecho" and hecho.destino.exists()


def test_si_no_tiene_la_carpeta_de_la_unidad_va_a_la_asignatura(tmp_path):
    motor, descargas, destino = entregar(tmp_path)
    (destino / "sistemas" / "1 Avaluacio" / "unitat 1").rename(destino / "sistemas" / "1 Avaluacio" / "unitat 5")
    [r] = motor.ejecutar("o", descargas, simular=True)
    assert r.destino == destino / "sistemas" / "Examen_A_cas_plantilla_part_1.odt" and r.nota == ""
    assert not (destino / "sistemas" / "1 Avaluacio" / "unitat 1").exists()  # nunca se crea


def test_con_unidades_false_no_entra_en_la_unidad(tmp_path):
    motor, descargas, destino = entregar(tmp_path, unidades=False)
    [r] = motor.ejecutar("o", descargas, simular=True)
    assert r.destino == destino / "sistemas" / "Examen_A_cas_plantilla_part_1.odt"
