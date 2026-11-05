"""dam pendientes. Documentación de mentira en tmp_path."""
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import pendientes
from tareas.cli import app

run = CliRunner()

README = """# Proyecto

### Cómo leer esta ficha
- **[Verificado]** — comprobado en una fuente.
- **[Hipótesis]** — suposición del equipo.
- **[Pendiente]** — no lo sabemos todavía.

Vicente pierde 2-3 horas al mes. **[Verificado, entrevista 4, 29/10/2026]**
El problema es pasar el cuaderno al ordenador. **[Hipótesis]**
Cuánto tiempo exactamente: **[Pendiente]**.
Documentación: [Pendiente](docs/pendientes.md)
Capterra lo confirma. **[Verificado]**
Esto no cuenta [Pendiente] dam:ignore
"""

ARQUITECTURA = """Etiquetas: **[Verificado]** (con fuente y fecha), **[Hipótesis]**, **[Pendiente]**.

| Pieza | Elección | Coste |
|---|---|---|
| PDF | WeasyPrint. **[Pendiente]** probarlo en Docker | 0 € |
| BD | Neon. Límites **[Verificado]**; uso **[Pendiente]** | 0 € |
"""

REGISTRO = """# Datos pendientes

| Pieza | Coste |
|---|---|
| Esta tabla no es un registro | 0 € |

| # | Dato | Dónde aparece | Responsable | Estado |
|---|---|---|---|---|
| 1 | Una persona real | README | Gabi | **Verificado** Vicente (29/10/2026) |
| 2 | Horas semanales | README | Todos | **En curso**: falta la entrevista 2 |
| 7 | Precio con sentido | README | Gabi | **Pendiente**; precio de trabajo 29 € |
| 8 | Electricistas en España | pitch | Mar | Pendiente |
| 13 | Precios de WhatsApp | — | Sergio | **Descartado** (Decisión 5) |
| 25 | Stack final | arquitectura | Javi y Gabi | Pendiente |
| 49 | PWA instalable | arquitectura | Mario (iconos: Mar) | Pendiente |
| 53 | (no recuperado) | — | — | |
"""


def escribir(ruta: Path, texto: str) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


@pytest.fixture
def proyecto(tmp_path) -> Path:
    escribir(tmp_path / "README.md", README)
    escribir(tmp_path / "docs" / "arquitectura.md", ARQUITECTURA)
    escribir(tmp_path / "docs" / "pendientes.md", REGISTRO)
    escribir(tmp_path / "docs" / "historico" / "viejo.md", "Esto ya no vale **[Pendiente]**\n")
    escribir(tmp_path / "notas.txt", "No es Markdown **[Pendiente]**\n")
    return tmp_path


def test_cuenta_las_etiquetas_por_fichero(proyecto):
    informe = pendientes.revisar(proyecto)
    assert informe.cuenta("README.md") == {"Verificado": 2, "Hipótesis": 1, "Pendiente": 1, "sin fecha": 1}
    assert informe.cuenta("docs/arquitectura.md") == {"Verificado": 1, "Hipótesis": 0, "Pendiente": 2, "sin fecha": 1}
    assert informe.cuenta()["Pendiente"] == 3


def test_no_cuenta_leyendas_enlaces_ignorados_historico_ni_otros_ficheros(proyecto):
    informe = pendientes.revisar(proyecto)
    lineas = {(e.fichero, e.linea) for e in informe.etiquetas}
    assert not {("README.md", n) for n in (4, 5, 6)} & lineas  # «Cómo leer esta ficha»
    assert ("docs/arquitectura.md", 1) not in lineas  # «Etiquetas: [Verificado]..., [Hipótesis], [Pendiente]»
    assert ("README.md", 11) not in lineas and ("README.md", 13) not in lineas  # enlace y dam:ignore
    assert not any("historico" in e.fichero for e in informe.etiquetas)
    assert "notas.txt" not in informe.ficheros


@pytest.mark.parametrize("linea", [
    "Etiquetas: **[Verificado]** (documentación de Render, 22/10/2026), **[Pendiente]**.",
    "Etiquetas de datos: **[Hipótesis]** (vocabulario de partida), **[Pendiente]** (ver pendientes.md).",
    "**Etiquetas:** [Pendiente]",
])
def test_una_linea_de_etiquetas_es_leyenda_aunque_no_tenga_las_tres(linea):
    assert pendientes.etiquetas_de_texto("a.md", linea) == []


def test_una_frase_que_menciona_etiquetas_si_cuenta():
    linea = "Las etiquetas del pitch siguen [Pendiente] de revisar"
    assert [e.tipo for e in pendientes.etiquetas_de_texto("a.md", linea)] == ["Pendiente"]


def test_verificado_con_fecha_en_la_etiqueta_o_en_la_linea():
    con = pendientes.etiquetas_de_texto("a.md", "Fuente: INE, consultado el 20/10/2026 **[Verificado]**")
    sin = pendientes.etiquetas_de_texto("a.md", "Lo dice Capterra **[Verificado]**")
    iso = pendientes.etiquetas_de_texto("a.md", "[Verificado 2026-10-29]")
    assert con[0].con_fecha and iso[0].con_fecha and not sin[0].con_fecha


@pytest.mark.parametrize("etiqueta, tipo", [
    ("[Pendiente de decidir]", "Pendiente"), ("[hipotesis]", "Hipótesis"),
    ("[Verificada, entrevista 2]", "Verificado"), ("[Verificado con una sola voz, 03/11/2026]", "Verificado"),
])
def test_reconoce_las_variantes(etiqueta, tipo):
    assert [e.tipo for e in pendientes.etiquetas_de_texto("a.md", f"Dato {etiqueta}")] == [tipo]


def test_lee_el_registro_y_salta_las_tablas_que_no_lo_son(proyecto):
    filas = pendientes.revisar(proyecto).registro
    assert [f.numero for f in filas] == ["1", "2", "7", "8", "13", "25", "49", "53"]
    estados = {f.numero: f.estado for f in filas}
    assert estados == {"1": "Verificado", "2": "En curso", "7": "Pendiente", "8": "Pendiente",
                       "13": "Descartado", "25": "Pendiente", "49": "Pendiente", "53": "sin estado"}
    assert [f.numero for f in filas if f.abierta] == ["2", "7", "8", "25", "49"]


def test_reparto_por_persona_cuenta_las_filas_compartidas_para_cada_uno(proyecto):
    abiertas = [f for f in pendientes.revisar(proyecto).registro if f.abierta]
    assert pendientes.reparto(abiertas) == {"Gabi": 2, "Mar": 2, "Javi": 1, "Mario": 1, "Todos": 1}


def test_quien_compara_nombres_enteros_y_sin_acentos(proyecto):
    filas = {f.numero: f for f in pendientes.revisar(proyecto).registro}
    assert pendientes.es_de(filas["25"], "gabi")      # «Javi y Gabi»
    assert pendientes.es_de(filas["2"], "Gabi")       # «Todos»
    assert pendientes.es_de(filas["49"], "MAR")       # «Mario (iconos: Mar)»
    assert not pendientes.es_de(filas["8"], "Mari")   # «Mar» no es «Mari»
    assert not pendientes.es_de(filas["7"], "Javi")


def test_cli_lista_lo_sin_verificar_y_el_registro(proyecto):
    r = run.invoke(app, ["pendientes", str(proyecto)])
    assert r.exit_code == 0, r.output
    for texto in ("Etiquetas por fichero", "Sin verificar en los documentos", "README.md:9",
                  "Verificado, pero sin fecha", "Registro docs/pendientes.md", "Precio con sentido"):
        assert texto in r.output, texto
    assert "Una persona real" not in r.output  # está verificada: no sale en las abiertas


def test_cli_quien_solo_enseña_lo_suyo(proyecto):
    r = run.invoke(app, ["pendientes", str(proyecto), "--quien", "Mar"])
    assert r.exit_code == 0, r.output
    assert "Electricistas en España" in r.output and "PWA instalable" in r.output
    assert "Horas semanales" in r.output  # «Todos»
    assert "Precio con sentido" not in r.output
    assert "Sin verificar en los documentos" not in r.output


def test_cli_quien_sin_nada_abierto(proyecto):
    r = run.invoke(app, ["pendientes", str(proyecto), "--quien", "Sergio"])
    assert "Horas semanales" in r.output  # lo de «Todos» sigue saliendo
    escribir(proyecto / "docs" / "pendientes.md", REGISTRO.replace("| Todos |", "| Gabi |"))
    r = run.invoke(app, ["pendientes", str(proyecto), "--quien", "Sergio"])
    assert "no le queda nada abierto" in r.output


def test_cli_resumen_no_saca_las_listas(proyecto):
    r = run.invoke(app, ["pendientes", str(proyecto), "--resumen"])
    assert r.exit_code == 0
    assert "Etiquetas por fichero" in r.output and "Registro" in r.output
    assert "Sin verificar en los documentos" not in r.output and "Precio con sentido" not in r.output


def test_cli_sin_etiquetas_ni_registro(tmp_path):
    escribir(tmp_path / "README.md", "# Nada que ver\n")
    r = run.invoke(app, ["pendientes", str(tmp_path)])
    assert r.exit_code == 0
    assert "No hay etiquetas" in r.output


def test_cli_carpeta_que_no_existe_sale_con_1(tmp_path):
    r = run.invoke(app, ["pendientes", str(tmp_path / "no-existe")])
    assert r.exit_code == 1
    assert "Traceback" not in r.output
