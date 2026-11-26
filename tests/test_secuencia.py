"""Acciones combinables: una acción de tipo «secuencia» ejecuta varias seguidas (ADR-0007).

Lo pide el nivel excelente de la rúbrica («acciones combinables»). Aquí se comprueba:
- que acciones.json rechaza las secuencias mal escritas, diciendo qué campo falla;
- que cada paso trabaja con lo que dejó el anterior (de verdad) y que --simular no toca nada;
- que cada paso pregunta como siempre, y que si uno falla o le dices que no, los demás no se ejecutan.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import config
from tareas.cli import app
from tareas.errores import AccionNoValida
from tareas.motor import Motor

runner = CliRunner()
RAIZ = Path(__file__).resolve().parent.parent

# Dos acciones que se notan si van seguidas: la 2.ª solo ve lo que ha renombrado la 1.ª
RENOMBRAR = {"nombre": "renombrar-capturas", "descripcion": "d", "tipo": "renombrar",
             "plantilla": "captura_{n:03}{ext}", "filtro": {"patron": "^Captura"}}
MOVER = {"nombre": "guardar-capturas", "descripcion": "d", "tipo": "mover",
         "destino": "prueba/capturas", "filtro": {"patron": "^captura_"}}  # relativo a la carpeta de la prueba
BORRAR = {"nombre": "limpiar", "descripcion": "d", "tipo": "borrar",
          "filtro": {"extensiones": [".tmp"], "mas_antiguo_que_dias": 30}}
SECUENCIA = {"nombre": "repasar", "descripcion": "Todo seguido", "tipo": "secuencia",
             "pasos": ["limpiar", "renombrar-capturas", "guardar-capturas"]}


@pytest.fixture
def carpeta(tmp_path):
    """Una carpeta con dos capturas, un temporal viejo y un fichero que no toca ningún paso."""
    c = tmp_path / "prueba"
    c.mkdir()
    for nombre in ("Captura 1.png", "Captura 2.png", "viejo.tmp", "apuntes.pdf"):
        (c / nombre).write_text(nombre, encoding="utf-8")
    hace_40_dias = time.time() - 40 * 24 * 3600
    os.utime(c / "viejo.tmp", (hace_40_dias, hace_40_dias))
    return c


def nombres(c: Path) -> list[str]:
    return sorted(str(p.relative_to(c)).replace("\\", "/") for p in c.rglob("*") if p.is_file())


def lanzar(escribir_config, acciones: list[dict], *argumentos, entrada: str | None = None):
    ruta = escribir_config(acciones)
    return runner.invoke(app, ["--config", str(ruta), "ejecutar", *argumentos], input=entrada)


def plano(r) -> str:
    return " ".join(r.output.split())


# ---------- acciones.json ----------
def test_una_secuencia_bien_escrita_es_valida():
    datos = config.validar_datos({"version": 1, "acciones": [BORRAR, RENOMBRAR, MOVER, SECUENCIA]})
    assert datos["acciones"][-1]["pasos"] == ["limpiar", "renombrar-capturas", "guardar-capturas"]


@pytest.mark.parametrize("cambio, campo, mensaje", [
    ({"pasos": None}, "pasos", "es obligatorio"),
    ({"pasos": "limpiar"}, "pasos", "lista de nombres"),
    ({"pasos": ["limpiar"]}, "pasos", "al menos 2 pasos"),
    ({"pasos": ["limpiar", "repasar"]}, "pasos", "a sí misma"),
    ({"pasos": ["limpiar", "limpiar"]}, "pasos", "repetido"),
    ({"pasos": ["limpiar", "no-existe"]}, "pasos", "«no-existe» no es ninguna acción"),
    ({"filtro": {"extensiones": [".png"]}}, "filtro", "ponlo en la acción de cada paso"),
    ({"destino": "x"}, "destino", "no vale en una secuencia"),
], ids=["sin-pasos", "pasos-texto", "un-paso", "a-si-misma", "repetido", "paso-inexistente", "con-filtro", "con-destino"])
def test_una_secuencia_mal_escrita_dice_que_campo_falla(cambio, campo, mensaje):
    secuencia = {**SECUENCIA, **cambio}
    with pytest.raises(AccionNoValida) as e:
        config.validar_datos({"version": 1, "acciones": [BORRAR, RENOMBRAR, MOVER, secuencia]})
    assert e.value.campo == campo and mensaje in str(e.value)


def test_un_paso_no_puede_ser_otra_secuencia():
    otra = {**SECUENCIA, "nombre": "otra", "pasos": ["limpiar", "repasar"]}
    with pytest.raises(AccionNoValida, match="es otra secuencia"):
        config.validar_datos({"version": 1, "acciones": [BORRAR, RENOMBRAR, MOVER, SECUENCIA, otra]})


def test_pasos_solo_vale_en_una_secuencia():
    with pytest.raises(AccionNoValida, match="solo vale en acciones de tipo secuencia"):
        config.validar_datos({"version": 1, "acciones": [{**BORRAR, "pasos": ["a", "b"]}]})


def test_el_acciones_json_del_repo_trae_una_secuencia_valida():
    acciones = config.cargar(RAIZ / "acciones.json")
    secuencias = [a for a in acciones if a["tipo"] == "secuencia"]
    assert secuencias and all(len(s["pasos"]) >= 2 for s in secuencias)


# ---------- el motor ----------
def test_cada_paso_trabaja_con_lo_que_dejo_el_anterior(carpeta):
    # «guardar-capturas» busca «captura_...»: solo existen porque «renombrar-capturas» va antes
    resultados = Motor([BORRAR, RENOMBRAR, MOVER, SECUENCIA]).ejecutar("repasar", carpeta, simular=False)
    assert nombres(carpeta) == ["apuntes.pdf", "capturas/captura_001.png", "capturas/captura_002.png"]
    assert [r.estado for r in resultados] == ["hecho"] * 5  # 1 borrado + 2 renombrados + 2 movidos


def test_simular_una_secuencia_no_toca_nada(carpeta):
    antes = nombres(carpeta)
    resultados = Motor([BORRAR, RENOMBRAR, MOVER, SECUENCIA]).ejecutar("repasar", carpeta, simular=True)
    assert nombres(carpeta) == antes
    assert {r.estado for r in resultados} == {"simulado"}
    assert not (carpeta / "capturas").exists()  # ni siquiera crea la carpeta de destino


# ---------- la orden mochila ejecutar ----------
def test_simular_desde_la_terminal_explica_cada_paso_y_no_toca_nada(escribir_config, carpeta):
    antes = nombres(carpeta)
    r = lanzar(escribir_config, [BORRAR, RENOMBRAR, MOVER, SECUENCIA], "repasar", str(carpeta), "--simular")
    assert r.exit_code == 0, r.output
    salida = plano(r)
    assert "3 pasos: limpiar → renombrar-capturas → guardar-capturas" in salida
    assert "Paso 1 de 3: limpiar" in salida and "Paso 3 de 3: guardar-capturas" in salida
    assert "cada paso mira la carpeta tal como está ahora" in salida  # sin efectos sorpresa
    assert salida.count("repite la orden sin --simular") == 1
    assert "Ningún fichero cumple el filtro" in salida  # el paso 3 no ve nada (aún no hay captura_...) y sigue
    assert nombres(carpeta) == antes


def test_con_si_hace_todos_los_pasos(escribir_config, carpeta):
    r = lanzar(escribir_config, [BORRAR, RENOMBRAR, MOVER, SECUENCIA], "repasar", str(carpeta), "--si")
    assert r.exit_code == 0, r.output
    assert "Secuencia «repasar» terminada: 3 pasos" in plano(r)
    assert nombres(carpeta) == ["apuntes.pdf", "capturas/captura_001.png", "capturas/captura_002.png"]


def test_cada_paso_que_borra_pregunta_como_siempre(escribir_config, carpeta):
    r = lanzar(escribir_config, [BORRAR, RENOMBRAR, MOVER, SECUENCIA], "repasar", str(carpeta), entrada="s\n")
    assert r.exit_code == 0, r.output
    assert "¿BORRAR 1 fichero(s)?" in plano(r)
    assert not (carpeta / "viejo.tmp").exists() and (carpeta / "capturas").is_dir()


def test_si_dices_que_no_a_un_paso_no_sigue_con_los_demas(escribir_config, carpeta):
    r = lanzar(escribir_config, [BORRAR, RENOMBRAR, MOVER, SECUENCIA], "repasar", str(carpeta), entrada="n\n")
    assert r.exit_code != 0 and "Traceback" not in r.output
    assert "No sigo con renombrar-capturas, guardar-capturas" in plano(r)
    assert nombres(carpeta) == ["Captura 1.png", "Captura 2.png", "apuntes.pdf", "viejo.tmp"]


def test_si_un_paso_falla_los_siguientes_no_se_ejecutan(escribir_config, carpeta, tmp_path):
    # Sin CARPETA, cada paso usa su «origen»: el del 2.º paso no existe
    roto = {**RENOMBRAR, "origen": str(tmp_path / "no-existe")}
    primero = {**BORRAR, "origen": str(carpeta)}
    tercero = {**MOVER, "origen": str(carpeta)}
    r = lanzar(escribir_config, [primero, roto, tercero, SECUENCIA], "repasar", "--si")
    assert r.exit_code == 1
    assert "no existe" in plano(r) and "No sigo con guardar-capturas" in plano(r)
    assert not (carpeta / "viejo.tmp").exists()  # el 1.º sí se hizo
    assert not (carpeta / "capturas").exists()   # el 3.º no


def test_el_origen_de_la_secuencia_vale_para_todos_los_pasos(escribir_config, carpeta):
    r = lanzar(escribir_config, [BORRAR, RENOMBRAR, MOVER, {**SECUENCIA, "origen": str(carpeta)}], "repasar", "--si")
    assert r.exit_code == 0, r.output
    assert (carpeta / "capturas" / "captura_001.png").is_file()


def test_sin_ia_una_secuencia_con_un_paso_de_ia_no_empieza(escribir_config, carpeta):
    # Mejor no empezar que dejarlo a medias: sin modelo elegido, sale con 4 antes del primer paso
    resumir = {"nombre": "resumir", "descripcion": "d", "tipo": "resumir", "filtro": {"extensiones": [".pdf"]}}
    secuencia = {**SECUENCIA, "pasos": ["limpiar", "resumir"]}
    r = lanzar(escribir_config, [BORRAR, resumir, secuencia], "repasar", str(carpeta), "--si")
    assert r.exit_code == 4
    assert (carpeta / "viejo.tmp").exists()  # el paso sin IA tampoco se ha hecho
    assert "Traceback" not in r.output


def test_la_lista_de_acciones_enseña_los_pasos(escribir_config):
    ruta = escribir_config([BORRAR, RENOMBRAR, MOVER, SECUENCIA])
    r = runner.invoke(app, ["--config", str(ruta), "acciones"])
    assert r.exit_code == 0
    assert "secuencia" in r.output and "limpiar → renombrar-capturas" in plano(r)


def test_validar_cuenta_la_secuencia(escribir_config):
    ruta = escribir_config([BORRAR, RENOMBRAR, MOVER, SECUENCIA])
    r = runner.invoke(app, ["--config", str(ruta), "validar"])
    assert r.exit_code == 0 and "4 acciones válidas" in plano(r)


def test_validar_con_un_paso_que_no_existe_sale_con_3(escribir_config):
    ruta = escribir_config([BORRAR, {**SECUENCIA, "pasos": ["limpiar", "ordenar-todo"]}])
    r = runner.invoke(app, ["--config", str(ruta), "validar"])
    assert r.exit_code == 3
    assert "«ordenar-todo» no es ninguna acción" in plano(r) and "Traceback" not in r.output


def test_si_falla_el_ultimo_paso_tambien_lo_dice(escribir_config, carpeta, tmp_path):
    ultimo = {**MOVER, "origen": str(tmp_path / "no-existe")}
    secuencia = {**SECUENCIA, "pasos": ["limpiar", "guardar-capturas"]}
    r = lanzar(escribir_config, [{**BORRAR, "origen": str(carpeta)}, ultimo, secuencia], "repasar", "--si")
    assert r.exit_code == 1
    assert "El paso «guardar-capturas» no ha terminado bien" in plano(r) and "No sigo con" not in plano(r)


def test_una_secuencia_no_trabaja_sobre_un_fichero_suelto(escribir_config, carpeta):
    # El paso 1 podría renombrarlo y el 2 no encontrarlo: se dice antes de empezar
    r = lanzar(escribir_config, [BORRAR, RENOMBRAR, MOVER, SECUENCIA], "repasar", str(carpeta / "Captura 1.png"), "--si")
    assert r.exit_code == 1 and "no sobre un fichero suelto" in plano(r)
    assert nombres(carpeta) == ["Captura 1.png", "Captura 2.png", "apuntes.pdf", "viejo.tmp"]


def test_sin_carpeta_y_con_un_paso_sin_origen_no_empieza(escribir_config, carpeta):
    primero = {**BORRAR, "origen": str(carpeta)}  # este sí tiene origen; RENOMBRAR y MOVER no
    r = lanzar(escribir_config, [primero, RENOMBRAR, MOVER, SECUENCIA], "repasar", "--si")
    assert r.exit_code == 1
    assert "renombrar-capturas, guardar-capturas no tiene" in plano(r)
    assert (carpeta / "viejo.tmp").exists()  # ni el primer paso se ha hecho


def test_el_destino_de_un_paso_puede_ser_el_origen_del_siguiente(escribir_config, carpeta, tmp_path):
    # Que el origen exista se mira al llegar al paso, porque puede crearlo uno anterior
    nueva = tmp_path / "nueva"
    mover = {"nombre": "a-nueva", "descripcion": "d", "tipo": "mover", "origen": str(carpeta),
             "destino": str(nueva), "filtro": {"extensiones": [".pdf"]}}
    copiar = {"nombre": "copiar-pdf", "descripcion": "d", "tipo": "copiar", "origen": str(nueva),
              "destino": str(tmp_path / "copia"), "filtro": {"extensiones": [".pdf"]}}
    secuencia = {"nombre": "mover-y-copiar", "descripcion": "d", "tipo": "secuencia", "pasos": ["a-nueva", "copiar-pdf"]}
    r = lanzar(escribir_config, [mover, copiar, secuencia], "mover-y-copiar", "--si")
    assert r.exit_code == 0, r.output
    assert (nueva / "apuntes.pdf").is_file() and (tmp_path / "copia" / "apuntes.pdf").is_file()
