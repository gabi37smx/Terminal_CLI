"""Modelos gratis con OpenCode (ProveedorOpenCode y dam configurar-ia) sin lanzar opencode de verdad.

Un «opencode de mentira» sustituye a subprocess.run: apunta qué se le pidió y responde como lo haría
«opencode run --format json» (un evento JSON por línea). Ninguna prueba usa la red.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import configurar_ia as configurar_ia_mod
from tareas import ia
from tareas.cli import app
from tareas.errores import ConfigError, IANoDisponible
from tareas.ia import ProveedorCentro, ProveedorOpenCode, crear_proveedor, leer_eventos

run = CliRunner()
MODELOS = ["opencode/big-pickle", "opencode/beam-free", "opencode/glm-5.3-flash-free",
           "opencode/deepseek-v4.1-flash-free", "otro/de-pago"]


def eventos(texto: str = "ok", entrada: int = 10, salida: int = 2) -> bytes:
    lineas = [
        {"type": "step_start", "part": {"type": "step-start"}},
        {"type": "text", "part": {"type": "text", "text": texto}},
        {"type": "step_finish", "part": {"tokens": {"input": entrada, "output": salida}}},
    ]
    return "\n".join(json.dumps(l) for l in lineas).encode("utf-8")


class OpencodeFalso:
    """Hace de opencode: «run» responde con eventos, «models» da la lista y «--version» la versión."""

    def __init__(self, stdout: bytes | None = None, codigo: int = 0, stderr: bytes = b"", excepcion=None):
        self.stdout = eventos() if stdout is None else stdout
        self.codigo, self.stderr, self.excepcion = codigo, stderr, excepcion
        self.llamadas: list[dict] = []

    def __call__(self, orden, **kw):
        llamada = {"orden": orden, **kw}
        if "run" in orden:
            agente = Path(kw["cwd"]) / ".opencode" / "agents" / "dam-ia.md"
            llamada["agente"] = agente.read_text(encoding="utf-8")
        self.llamadas.append(llamada)
        if self.excepcion:
            raise self.excepcion
        if "models" in orden:
            return subprocess.CompletedProcess(orden, 0, ("\r\n".join(MODELOS) + "\r\n").encode(), b"")
        if "--version" in orden:
            return subprocess.CompletedProcess(orden, 0, b"1.18.35\n", b"")
        return subprocess.CompletedProcess(orden, self.codigo, self.stdout, self.stderr)


@pytest.fixture
def opencode(monkeypatch):
    """Instala un opencode de mentira; devuelve una fábrica para cambiar lo que responde."""
    monkeypatch.setattr(ia.shutil, "which", lambda nombre: "/usr/bin/opencode" if nombre == "opencode" else None)

    def instalar(**kw) -> OpencodeFalso:
        falso = OpencodeFalso(**kw)
        monkeypatch.setattr(subprocess, "run", falso)
        return falso

    instalar()
    return instalar


# ---------- ProveedorOpenCode ----------
def test_devuelve_el_texto_y_los_tokens(opencode):
    falso = opencode(stdout=eventos("redes", 900, 3))
    r = ProveedorOpenCode("opencode/glm-5.3-flash-free").completar("Clasifica: redes u otros.", "Tema 3: subredes «IP» & |")
    assert (r.texto, r.tokens_entrada, r.tokens_salida) == ("redes", 900, 3)
    llamada = falso.llamadas[0]
    orden = llamada["orden"]
    assert orden[:2] == ["/usr/bin/opencode", "run"]
    assert orden[orden.index("--agent") + 1] == "dam-ia"
    assert orden[orden.index("-m") + 1] == "opencode/glm-5.3-flash-free"
    assert orden[orden.index("--dir") + 1] == str(llamada["cwd"])  # opencode trabaja en la carpeta temporal
    assert "--title" in orden  # sin título, opencode se lo pide a tu small_model (el del centro, en casa falla)
    # el texto del fichero va por la entrada estándar, nunca en la línea de órdenes
    assert llamada["input"] == "Tema 3: subredes «IP» & |".encode("utf-8")
    assert all("subredes" not in parte for parte in orden)
    assert not Path(llamada["cwd"]).exists()  # la carpeta temporal se borra al acabar


def test_el_agente_no_tiene_herramientas(opencode):
    falso = opencode()
    ProveedorOpenCode().completar("Resume en una frase.", "texto")
    agente = falso.llamadas[0]["agente"]
    assert '"*": false' in agente and '"*": deny' in agente
    assert "external_directory: deny" in agente  # read solo dentro de su carpeta vacía
    assert agente.rstrip().endswith("Resume en una frase.")  # las instrucciones de la acción van al final


def test_quita_el_razonamiento_de_los_modelos_thinking(opencode):
    opencode(stdout=eventos("<think>a ver...</think>\nprogramacion"))
    assert ProveedorOpenCode().completar("s", "u").texto == "programacion"


def test_error_del_servidor_de_opencode(opencode):
    error = {"type": "error", "error": {"name": "UnknownError", "data": {"message": "Rate limit exceeded"}}}
    opencode(stdout=json.dumps(error).encode(), codigo=1)
    with pytest.raises(IANoDisponible, match="OpenCode dice: Rate limit exceeded"):
        ProveedorOpenCode().completar("s", "u")


def test_falla_sin_eventos_y_enseña_la_ultima_linea_sin_colores(opencode):
    opencode(stdout=b"", codigo=1, stderr=b"\x1b[91mError:\x1b[0m algo\nModel not found: opencode/x\n")
    with pytest.raises(IANoDisponible, match=r"código 1\): Model not found: opencode/x$"):
        ProveedorOpenCode().completar("s", "u")


def test_tiempo_agotado(opencode):
    opencode(excepcion=subprocess.TimeoutExpired("opencode", 5))
    with pytest.raises(IANoDisponible, match="no ha respondido en 5 s"):
        ProveedorOpenCode(segundos=5).completar("s", "u")


def test_respuesta_vacia(opencode):
    opencode(stdout=eventos(""))
    with pytest.raises(IANoDisponible, match="no ha devuelto texto"):
        ProveedorOpenCode().completar("s", "u")


def test_sin_opencode_instalado(monkeypatch):
    monkeypatch.setattr(ia.shutil, "which", lambda nombre: None)
    with pytest.raises(IANoDisponible, match="No encuentro opencode"):
        ProveedorOpenCode().completar("s", "u")


def test_en_wsl_no_vale_el_opencode_de_windows(monkeypatch):
    monkeypatch.setattr(ia.sys, "platform", "linux")
    monkeypatch.setattr(ia.shutil, "which", lambda nombre: "/mnt/c/Users/alumno/AppData/Roaming/npm/opencode")
    with pytest.raises(IANoDisponible, match="es el de Windows"):
        ProveedorOpenCode().completar("s", "u")


def test_leer_eventos_salta_lo_que_no_es_json():
    salida = "aviso suelto\n" + eventos("hola ").decode() + "\n[1, 2]\n" + eventos("mundo", 5, 1).decode()
    assert leer_eventos(salida) == ("hola mundo", 15, 3, "")


# ---------- qué proveedor usa dam ----------
def test_sin_elegir_nada_es_el_servidor_del_centro():
    with pytest.raises(IANoDisponible, match="Faltan CENTRO_IA_URL") as e:
        crear_proveedor()
    assert "dam configurar-ia" in str(e.value)  # y le dice que fuera del instituto tiene los gratis


def test_lo_que_guardo_configurar_ia():
    ia.guardar_ajustes({"proveedor": "opencode", "modelo": "opencode/beam-free"})
    p = crear_proveedor()
    assert isinstance(p, ProveedorOpenCode) and p.modelo == "opencode/beam-free"


def test_dam_ia_lo_cambia_solo_en_esa_terminal(monkeypatch):
    ia.guardar_ajustes({"proveedor": "opencode", "modelo": "opencode/beam-free"})
    monkeypatch.setenv("CENTRO_IA_URL", "https://servidor/v1")
    monkeypatch.setenv("CENTRO_IA_KEY", "sk-" + "de-prueba")
    monkeypatch.setenv("DAM_IA", "centro")
    assert isinstance(crear_proveedor(), ProveedorCentro)
    monkeypatch.setenv("DAM_IA", "opencode")
    monkeypatch.setenv("DAM_IA_MODELO", "opencode/glm-5.3-flash-free")
    assert crear_proveedor().modelo == "opencode/glm-5.3-flash-free"
    monkeypatch.setenv("DAM_IA", "chatgpt")
    with pytest.raises(IANoDisponible, match="No conozco el proveedor"):
        crear_proveedor()


def test_ia_json_roto():
    ia.ruta_ajustes().write_text("{roto", encoding="utf-8")
    with pytest.raises(IANoDisponible, match="está roto"):
        crear_proveedor()


# ---------- configurar_ia: modelos y configuración global de OpenCode ----------
def test_modelos_gratis_recomendados_primero(opencode):
    assert configurar_ia_mod.modelos_gratis("/usr/bin/opencode") == [
        "opencode/deepseek-v4.1-flash-free", "opencode/glm-5.3-flash-free", "opencode/beam-free",
    ]  # big-pickle no acaba en -free y otro/de-pago no es de OpenCode


def test_nota_de_cada_modelo():
    assert "no guarda" in configurar_ia_mod.nota("opencode/deepseek-v4.1-flash-free")
    assert "opencode.ai/docs/zen" in configurar_ia_mod.nota("opencode/uno-nuevo-free")


def test_poner_modelo_global_crea_el_fichero(tmp_path):
    ruta = tmp_path / "opencode" / "opencode.json"
    assert configurar_ia_mod.poner_modelo_global(ruta, "opencode/beam-free") is None
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos == {"$schema": configurar_ia_mod.ESQUEMA, "model": "opencode/beam-free", "small_model": "opencode/beam-free"}


def test_poner_modelo_global_no_toca_lo_demas_y_guarda_copia(tmp_path):
    ruta = tmp_path / "opencode.json"
    antes = {"provider": {"centro": {"options": {"baseURL": "{env:CENTRO_IA_URL}"}}}, "model": "centro/qwen"}
    ruta.write_text(json.dumps(antes), encoding="utf-8")
    copia = configurar_ia_mod.poner_modelo_global(ruta, "opencode/beam-free")
    assert json.loads(copia.read_text(encoding="utf-8")) == antes
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["provider"] == antes["provider"] and datos["model"] == "opencode/beam-free"
    assert configurar_ia_mod.modelo_global(ruta) == "opencode/beam-free"


def test_con_comentarios_no_la_toca(tmp_path):
    ruta = tmp_path / "opencode.json"
    ruta.write_text('{\n  // mi modelo\n  "model": "centro/qwen"\n}', encoding="utf-8")
    with pytest.raises(ConfigError, match="no la toco"):
        configurar_ia_mod.poner_modelo_global(ruta, "opencode/beam-free")
    assert "// mi modelo" in ruta.read_text(encoding="utf-8")


def test_usa_el_jsonc_que_crea_opencode_la_primera_vez():
    carpeta = configurar_ia_mod.ruta_opencode_global().parent
    assert configurar_ia_mod.ruta_opencode_global().name == "opencode.json"  # sin ninguno, el .json
    carpeta.mkdir(parents=True)
    jsonc = carpeta / "opencode.jsonc"
    jsonc.write_text('{\n  "$schema": "https://opencode.ai/config.json"\n}', encoding="utf-8")
    assert configurar_ia_mod.ruta_opencode_global() == jsonc
    configurar_ia_mod.poner_modelo_global(jsonc, "opencode/beam-free")
    assert configurar_ia_mod.modelo_global(jsonc) == "opencode/beam-free"
    (carpeta / "opencode.json").write_text("{}", encoding="utf-8")
    assert configurar_ia_mod.ruta_opencode_global().name == "opencode.json"  # si están los dos, el .json


def test_configurar_ia_propone_opencode_la_primera_vez(opencode):
    r = run.invoke(app, ["configurar-ia"], input="\n\nn\n")  # Enter, Enter: lo que propone
    assert r.exit_code == 0, r.output
    assert ia.leer_ajustes() == {"proveedor": "opencode", "modelo": "opencode/deepseek-v4.1-flash-free"}


# ---------- dam configurar-ia y dam comprobar-ia ----------
def test_configurar_ia_sin_preguntas(opencode):
    r = run.invoke(app, ["configurar-ia", "--proveedor", "opencode", "--modelo", "opencode/beam-free", "--si"])
    assert r.exit_code == 0, r.output
    assert ia.leer_ajustes() == {"proveedor": "opencode", "modelo": "opencode/beam-free"}
    # sin modelo por defecto en OpenCode, con --si lo pone
    global_ = configurar_ia_mod.ruta_opencode_global()
    assert configurar_ia_mod.modelo_global(global_) == "opencode/beam-free"


def test_configurar_ia_con_si_no_cambia_el_modelo_que_ya_tenias(opencode):
    global_ = configurar_ia_mod.ruta_opencode_global()
    global_.parent.mkdir(parents=True)
    global_.write_text('{"model": "centro/qwen"}', encoding="utf-8")
    r = run.invoke(app, ["configurar-ia", "--proveedor", "opencode", "--si"])
    assert r.exit_code == 0, r.output
    assert ia.leer_ajustes()["modelo"] == "opencode/deepseek-v4.1-flash-free"  # el primer recomendado
    assert configurar_ia_mod.modelo_global(global_) == "centro/qwen"


def test_configurar_ia_preguntando(opencode):
    # 1 = OpenCode; 2 = el segundo de la lista (glm); s = también por defecto en OpenCode
    r = run.invoke(app, ["configurar-ia"], input="1\n2\ns\n")
    assert r.exit_code == 0, r.output
    salida = " ".join(r.output.split())
    assert "(recomendado)" in salida and "no guarda lo que le mandas" in salida
    assert "Responde «ok»" in salida
    assert ia.leer_ajustes()["modelo"] == "opencode/glm-5.3-flash-free"
    assert configurar_ia_mod.modelo_global(configurar_ia_mod.ruta_opencode_global()) == "opencode/glm-5.3-flash-free"


def test_configurar_ia_ninguno_no_guarda_nada(opencode):
    r = run.invoke(app, ["configurar-ia"], input="3\n")
    assert r.exit_code == 0 and "No cambio nada" in r.output
    assert ia.leer_ajustes() == {}


def test_configurar_ia_si_el_modelo_no_responde_no_guarda(opencode):
    opencode(stdout=b"", codigo=1, stderr=b"sin red\n")
    r = run.invoke(app, ["configurar-ia", "--proveedor", "opencode", "--si"])
    assert r.exit_code == 4 and "No responde" in r.output
    assert ia.leer_ajustes() == {}


def test_configurar_ia_centro():
    r = run.invoke(app, ["configurar-ia", "--proveedor", "centro"])
    assert r.exit_code == 0 and "comprobar-ia" in r.output
    assert ia.leer_ajustes() == {"proveedor": "centro"}


def test_configurar_ia_sin_opencode(monkeypatch):
    monkeypatch.setattr(ia.shutil, "which", lambda nombre: None)
    r = run.invoke(app, ["configurar-ia", "--proveedor", "opencode", "--si"])
    assert r.exit_code == 4 and "No encuentro opencode" in r.output


def test_comprobar_ia_con_opencode(opencode):
    ia.guardar_ajustes({"proveedor": "opencode", "modelo": "opencode/beam-free"})
    r = run.invoke(app, ["comprobar-ia"])
    assert r.exit_code == 0, r.output
    assert "OpenCode" in r.output and "opencode/beam-free" in r.output and "El modelo responde «ok»" in r.output
