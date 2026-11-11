"""Capa IA: lo único que el resto del programa sabe de un modelo es «le das texto y te devuelve texto».

ProveedorIA es la interfaz (clase abstracta). ProveedorCentro habla con el servidor del centro
(API de chat de OpenAI) con httpx. Las acciones no importan httpx: si mañana cambia el servidor,
o en las pruebas no hay red, se cambia la clase de abajo sin tocar las acciones.

La clave se lee de las variables de entorno (o de un .env que NUNCA se sube a git) y nunca
se imprime ni se escribe en ningún fichero.
"""

from __future__ import annotations

import os
import re
import ssl
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import httpx
from dotenv import find_dotenv, load_dotenv

from .errores import IANoDisponible

MODELO_POR_DEFECTO = "qwen3.8-flash-next"
# Los modelos «thinking» pueden devolver su razonamiento entre <think> y </think>: no es la respuesta
PENSAMIENTO = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


@dataclass
class Respuesta:
    texto: str
    tokens_entrada: int
    tokens_salida: int
    segundos: float

    def resumen(self) -> str:
        return f"{self.tokens_entrada}+{self.tokens_salida} tokens · {self.segundos:.1f} s"


class ProveedorIA(ABC):
    """Lo único que el resto del programa sabe de la IA: le das texto y te devuelve texto."""

    @abstractmethod
    def completar(self, sistema: str, usuario: str, max_tokens: int = 800) -> Respuesta: ...


def _leer_dotenv() -> None:
    """Carga el .env de la carpeta actual (o de una superior) si lo hay. No pisa variables que ya existen.

    Va aparte para que las pruebas lo puedan apagar: nunca deben leer tu .env de verdad.
    """
    load_dotenv(find_dotenv(usecwd=True))


class ProveedorCentro(ProveedorIA):
    """Un servidor compatible con la API de OpenAI: el del centro (o cualquier otro)."""

    def __init__(self, url: str, clave: str, modelo: str = MODELO_POR_DEFECTO, ca: str | None = None):
        self.url = url.rstrip("/")
        self.modelo = modelo
        self._clave = clave  # «_»: es privada; nunca se imprime
        self._tls = ssl.create_default_context()
        if ca:
            ruta_ca = Path(ca).expanduser()
            try:
                self._tls.load_verify_locations(ruta_ca)
            except (OSError, ssl.SSLError):
                raise IANoDisponible(
                    f"No puedo leer el certificado del centro en «{ruta_ca}»: revisa CENTRO_IA_CA"
                ) from None

    def __repr__(self) -> str:  # por si alguien lo imprime: la clave nunca sale
        return f"ProveedorCentro(url={self.url!r}, modelo={self.modelo!r}, clave=«definida»)"

    @staticmethod
    def desde_entorno() -> ProveedorCentro:
        """Fábrica: lee .env (si lo hay) y las variables de entorno."""
        _leer_dotenv()
        url = os.environ.get("CENTRO_IA_URL", "").strip()
        clave = os.environ.get("CENTRO_IA_KEY", "").strip()
        if not url or not clave:
            raise IANoDisponible("Faltan CENTRO_IA_URL o CENTRO_IA_KEY: ponlas en .env (mira .env.example)")
        modelo = os.environ.get("CENTRO_IA_MODELO", "").strip() or MODELO_POR_DEFECTO
        return ProveedorCentro(url, clave, modelo, os.environ.get("CENTRO_IA_CA") or None)

    def completar(self, sistema: str, usuario: str, max_tokens: int = 800) -> Respuesta:
        cuerpo = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }
        inicio = time.perf_counter()
        try:
            r = httpx.post(
                f"{self.url}/chat/completions",
                json=cuerpo,
                headers={"Authorization": f"Bearer {self._clave}"},
                timeout=httpx.Timeout(60, connect=5),
                verify=self._tls,  # verify="ruta" está obsoleto en httpx 0.28
            )
            r.raise_for_status()
            datos = r.json()
            texto = datos["choices"][0]["message"]["content"] or ""
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            if "CERTIFICATE" in str(e).upper():
                raise IANoDisponible("No me fío del servidor: falta el certificado del centro (CENTRO_IA_CA)") from None
            raise IANoDisponible("No llego al servidor de IA: ¿estás en la red del centro?") from None
        except httpx.TimeoutException:
            raise IANoDisponible("El servidor de IA no ha respondido a tiempo") from None
        except httpx.HTTPStatusError as e:
            codigo = e.response.status_code
            motivo = {
                401: "la clave no es válida",
                404: "esa dirección no es la del servidor (revisa CENTRO_IA_URL: suele acabar en /v1)",
                429: "demasiadas peticiones, espera un minuto",
            }
            raise IANoDisponible(f"El servidor de IA responde {codigo}: {motivo.get(codigo, 'algo ha fallado')}") from None
        except httpx.HTTPError as e:  # cualquier otro fallo de red (la conexión se corta a medias...)
            raise IANoDisponible(f"Fallo de red al hablar con el servidor de IA ({type(e).__name__})") from None
        except (ValueError, KeyError, IndexError, TypeError):  # no es JSON, o no trae «choices»
            raise IANoDisponible("El servidor de IA ha respondido algo que no entiendo (¿es la URL buena?)") from None
        uso = datos.get("usage") or {}
        return Respuesta(
            PENSAMIENTO.sub("", texto).strip(),
            int(uso.get("prompt_tokens") or 0),
            int(uso.get("completion_tokens") or 0),
            time.perf_counter() - inicio,
        )
