"""Lo que comparten todas las pruebas: ninguna llama al servidor de IA de verdad ni lee tu .env."""

from __future__ import annotations

import pytest

from tareas import configurar_ia, ia
from tareas.errores import IANoDisponible
from tareas.ia import ProveedorIA, Respuesta


@pytest.fixture(autouse=True)
def aislado(monkeypatch, tmp_path_factory):
    """Sin variables del servidor del centro y sin leer el .env de la carpeta: aunque tengas
    tu clave puesta en este equipo, ninguna prueba la ve ni gasta un solo token.

    Tampoco ven tu ~/.config/dam/ia.json (lo que elegiste con dam configurar-ia) ni tu
    configuración de OpenCode: las dos van a una carpeta temporal."""
    for variable in ("CENTRO_IA_URL", "CENTRO_IA_KEY", "CENTRO_IA_CA", "CENTRO_IA_MODELO", "DAM_IA", "DAM_IA_MODELO"):
        monkeypatch.delenv(variable, raising=False)
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
