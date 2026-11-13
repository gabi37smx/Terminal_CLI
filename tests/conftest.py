"""Lo que comparten todas las pruebas: ninguna llama al servidor de IA de verdad ni lee tu .env."""

from __future__ import annotations

import json
import os
import time

import pytest

from tareas import configurar_ia, ia
from tareas.errores import IANoDisponible
from tareas.ia import ProveedorIA, Respuesta


@pytest.fixture(autouse=True)
def aislado(monkeypatch, tmp_path, tmp_path_factory):
    """Cada prueba en su carpeta temporal, con un HOME de mentira y sin tocar nada tuyo.

    - Sin variables del servidor del centro y sin leer el .env de la carpeta: aunque tengas
      tu clave puesta en este equipo, ninguna prueba la ve ni gasta un solo token.
    - Sin DAM_ALMACEN: en mi portátil apunta a mi almacén de verdad, y ninguna prueba debe verlo.
    - HOME y USERPROFILE (Windows) en una carpeta temporal: «~/...» nunca es tu carpeta personal.
      La carpeta no se crea, para no cambiar lo que hay en tmp_path.
    - Tampoco ven tu ~/.config/dam/ia.json (lo que elegiste con dam configurar-ia) ni tu
      configuración de OpenCode: las dos van a una carpeta temporal."""
    for variable in ("CENTRO_IA_URL", "CENTRO_IA_KEY", "CENTRO_IA_CA", "CENTRO_IA_MODELO", "DAM_IA", "DAM_IA_MODELO",
                     "DAM_ALMACEN"):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.setattr(ia, "_leer_dotenv", lambda: None)
    temporal = tmp_path_factory.mktemp("config-ia")
    monkeypatch.setenv("DAM_IA_CONFIG", str(temporal / "ia.json"))
    # No XDG_CONFIG_HOME: en Linux git también la lee y las pruebas de sync perderían tu identidad
    monkeypatch.setattr(configurar_ia, "_base_config", lambda: temporal / "config")


class ProveedorFalso(ProveedorIA):
    """Un modelo de mentira: responde lo que le digas, apunta lo que le preguntan y no usa la red.

    respuestas: una lista (una por llamada; la última se repite) o un texto fijo.
    Si una respuesta es una excepción, la lanza (para simular que se cae la red a mitad).
    """

    def __init__(self, respuestas: list | str = "ok"):
        self.respuestas = [respuestas] if isinstance(respuestas, str) else list(respuestas)
        self.llamadas: list[tuple[str, str, int]] = []

    def completar(self, sistema: str, usuario: str, max_tokens: int = 800) -> Respuesta:
        self.llamadas.append((sistema, usuario, max_tokens))
        indice = min(len(self.llamadas), len(self.respuestas)) - 1
        respuesta = self.respuestas[indice]
        if isinstance(respuesta, Exception):
            raise respuesta
        return Respuesta(respuesta, len(usuario) // 4, len(respuesta) // 4, 0.1)


@pytest.fixture
def modelo_falso():
    """Fábrica: modelo_falso("redes-ip") o modelo_falso(["sistemas", IANoDisponible("sin red")])."""
    return ProveedorFalso


@pytest.fixture
def sin_red():
    """La excepción que lanza el proveedor de verdad cuando no llega al servidor."""
    return IANoDisponible("No llego al servidor de IA: ¿estás en la red del centro?")


@pytest.fixture
def descargas(tmp_path):
    """Una carpeta Descargas como la de verdad: un poco de todo, y un temporal de hace 40 días."""
    carpeta = tmp_path / "Descargas"
    carpeta.mkdir()
    for nombre in ("factura.pdf", "apuntes de redes.docx", "FOTO1.JPG", "cumpleaños 2.png", "viejo.tmp"):
        (carpeta / nombre).write_text(f"contenido de {nombre}", encoding="utf-8")
    hace_40_dias = time.time() - 40 * 24 * 3600
    os.utime(carpeta / "viejo.tmp", (hace_40_dias, hace_40_dias))
    return carpeta


@pytest.fixture
def escribir_config(tmp_path):
    """Escribe un acciones.json y devuelve su ruta: escribir_config([{...}, ...]) o escribir_config('{roto').

    Con una lista, la pone dentro de {"version": 1, "acciones": [...]}. Con texto, lo escribe tal cual."""
    def escribir(contenido: list | str, nombre: str = "acciones.json"):
        ruta = tmp_path / nombre
        texto = contenido if isinstance(contenido, str) else json.dumps({"version": 1, "acciones": contenido})
        ruta.write_text(texto, encoding="utf-8")
        return ruta
    return escribir
