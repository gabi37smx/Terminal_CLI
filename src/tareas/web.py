"""test-links y check-headers: revisa enlaces rotos y cabeceras de seguridad de tu web o API.

Solo usa la biblioteca estándar (sin dependencias nuevas). Reglas de oro: nunca se imprime el
valor de una cookie, y toda petición lleva un tiempo máximo para que la orden no se cuelgue.
"""

from __future__ import annotations

import http.client
import os
import re
import socket
import ssl
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urljoin, urlsplit

from .errores import TareasError

USER_AGENT = "dam/1.0 (revisor de enlaces; +https://github.com/gabi37smx/Terminal_CLI)"
CARPETAS_IGNORADAS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}
EXTENSIONES_HTML = {".html", ".htm"}
# Webs que no dejan comprobar a robots (LinkedIn devuelve 999): se avisa, no se da por roto
CODIGOS_AVISO = {401, 403, 429, 999}
MAX_BYTES_PAGINA = 5_000_000
# Etiqueta HTML -> atributo que contiene el enlace
ATRIBUTOS = {"a": "href", "area": "href", "link": "href", "img": "src", "script": "src",
             "source": "src", "iframe": "src", "video": "src", "audio": "src", "embed": "src",
             "track": "src"}


# ======================= enlaces rotos =======================
@dataclass
class Problema:
    donde: str  # página donde está el enlace
    linea: int | None
    enlace: str  # tal como está escrito en el HTML
    motivo: str
    gravedad: str  # "roto" o "aviso"


@dataclass
class InformeEnlaces:
    paginas: int = 0
    revisados: int = 0
    omitidos: int = 0  # mailto:, tel:, ftp:, javascript:...
    problemas: list[Problema] = field(default_factory=list)

    @property
    def rotos(self) -> int:
        return sum(1 for p in self.problemas if p.gravedad == "roto")

    @property
    def avisos(self) -> int:
        return sum(1 for p in self.problemas if p.gravedad == "aviso")


@dataclass
class _Enlace:
    href: str
    linea: int


class _Pagina(HTMLParser):
    """Recoge los enlaces (con su línea) y los id de una página HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.enlaces: list[_Enlace] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        d = {k: (v or "") for k, v in attrs}
        if d.get("id"):
            self.ids.add(d["id"])
        if tag == "a" and d.get("name"):
            self.ids.add(d["name"])
        atributo = ATRIBUTOS.get(tag)
        if atributo is None or not d.get(atributo, "").strip():
            return
        if tag == "link" and set(d.get("rel", "").lower().split()) & {"preconnect", "dns-prefetch"}:
            return  # son pistas al navegador, no enlaces a una página
        self.enlaces.append(_Enlace(d[atributo].strip(), self.getpos()[0]))


def _analizar(html: str) -> _Pagina:
    pagina = _Pagina()
    pagina.feed(html)
    pagina.close()
    return pagina


def _leer_pagina(ruta: Path) -> _Pagina:
    return _analizar(ruta.read_text(encoding="utf-8", errors="replace"))


def _clasificar(href: str) -> str:
    """'plantilla' (se ignora), 'omitido' (mailto:...), 'externo' (http) o 'interno'."""
    if any(m in href for m in ("{{", "{%", "<%", "${")):
        return "plantilla"
    if href.startswith("//"):
        return "externo"
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*):", href)
    if m:
        return "externo" if m.group(1).lower() in ("http", "https") else "omitido"
    return "interno"


def _existe_con_mayusculas(ruta: Path, raiz: Path) -> bool:
    """¿Existe el fichero con EXACTAMENTE esas mayúsculas?

    Windows y macOS no distinguen Foto.jpg de foto.jpg, pero GitHub Pages y Linux sí: un
    enlace que «funciona» en tu PC se rompe al publicarlo.
    """
    if not ruta.exists():
        return False
    if sys.platform not in ("win32", "darwin"):
        return True
    try:
        partes, base = ruta.relative_to(raiz).parts, raiz
    except ValueError:  # fuera de la raíz (../otra-carpeta): solo se mira el último nombre
        partes, base = (ruta.name,), ruta.parent
    for parte in partes:
        try:
            nombres = {p.name for p in base.iterdir()}
        except OSError:
            return True
        if parte not in nombres:
            return False
        base = base / parte
    return True


def _falta_el_id(fragmento: str, ids: set[str]) -> bool:
    return bool(fragmento) and fragmento != "top" and fragmento not in ids  # #top vale siempre


def _comprobar_interno(href: str, pagina: Path, raiz: Path, ids_pagina: set[str],
                       cache_ids: dict[Path, set[str]]) -> tuple[str, str] | None:
    """Devuelve (motivo, gravedad) si el enlace local está mal, o None si está bien."""
    ruta_txt, _, fragmento = href.partition("#")
    ruta_txt, fragmento = unquote(ruta_txt.split("?", 1)[0]), unquote(fragmento)
    if not ruta_txt:  # solo ancla: #contacto
        if _falta_el_id(fragmento, ids_pagina):
            return f"no hay ningún elemento con id «{fragmento}» en esta página", "roto"
        return None
    base = raiz if ruta_txt.startswith("/") else pagina.parent
    destino = Path(os.path.normpath(base / ruta_txt.lstrip("/") if ruta_txt.startswith("/") else base / ruta_txt))
    if not _existe_con_mayusculas(destino, raiz):
        if destino.exists():
            return "las mayúsculas no coinciden (en Linux o GitHub Pages no se encontraría)", "roto"
        return "no existe ese fichero", "roto"
    if destino.is_dir():
        destino = destino / "index.html"
        if not destino.exists():
            return "es una carpeta sin index.html", "aviso"
    if fragmento and destino.suffix.lower() in EXTENSIONES_HTML:
        if destino not in cache_ids:
            cache_ids[destino] = _leer_pagina(destino).ids
        if _falta_el_id(fragmento, cache_ids[destino]):
            return f"el fichero existe pero no tiene el id «{fragmento}»", "aviso"
    return None


# ---------- peticiones HTTP ----------
def _motivo_error(error: Exception, timeout: float) -> str:
    razon = getattr(error, "reason", error)
    if isinstance(razon, (TimeoutError, socket.timeout)):
        return f"no responde (más de {timeout:g} s)"
    if isinstance(razon, socket.gaierror):
        return "no se encuentra ese dominio"
    if isinstance(razon, ConnectionRefusedError):
        return "conexión rechazada"
    if isinstance(razon, ssl.SSLError):
        return "error de certificado o SSL"
    if isinstance(error, ValueError):
        return "dirección no válida"
    return f"no se puede conectar ({razon})"


def _normalizar(url: str) -> str:
    """Quita el #ancla y codifica espacios y tildes de la ruta."""
    p = urlsplit(url)
    return p._replace(path=quote(p.path, safe="/%:@!$&'()*+,;=~-._"),
                      query=quote(p.query, safe="=&%+:/?@!$'()*,;~-._"), fragment="").geturl()


def _estado_url(url: str, timeout: float) -> tuple[int | None, str | None]:
    """(código HTTP, None) o (None, motivo del fallo). Prueba HEAD y, si falla, GET."""
    codigo = 0
    for metodo in ("HEAD", "GET"):  # algunos servidores no aceptan HEAD
        peticion = urllib.request.Request(url, method=metodo,
                                          headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
                codigo = respuesta.status
        except urllib.error.HTTPError as e:
            codigo = e.code
            e.close()
            if codigo < 400:  # urllib se rinde tras demasiadas redirecciones
                return None, "bucle de redirecciones"
        except (urllib.error.URLError, OSError, http.client.HTTPException, ValueError) as e:
            return None, _motivo_error(e, timeout)
        if codigo < 400:
            return codigo, None
    return codigo, None


def _descargar_pagina(url: str, timeout: float) -> tuple[str, str]:
    """Devuelve (html, url_final). Si no se puede abrir, TareasError."""
    peticion = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
            datos, final = respuesta.read(MAX_BYTES_PAGINA), respuesta.geturl()
            codificacion = respuesta.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as e:
        raise TareasError(f"La página {url} devuelve {e.code}.") from None
    except (urllib.error.URLError, OSError, http.client.HTTPException, ValueError) as e:
        raise TareasError(f"No puedo abrir {url}: {_motivo_error(e, timeout)}.") from None
    try:
        return datos.decode(codificacion, errors="replace"), final
    except LookupError:
        return datos.decode("utf-8", errors="replace"), final


def _comprobar_externos(pendientes: list[tuple[str, int, str, str]], timeout: float,
                        informe: InformeEnlaces) -> None:
    """pendientes = [(página, línea, enlace tal cual, URL completa)]. Cada URL se pide una vez."""
    if not pendientes:
        return
    urls = sorted({url for *_, url in pendientes})
    with ThreadPoolExecutor(max_workers=min(8, len(urls))) as pool:
        estados = dict(zip(urls, pool.map(lambda u: _estado_url(u, timeout), urls)))
    for donde, linea, href, url in pendientes:  # cada aparición se avisa
        codigo, error = estados[url]
        if error:
            informe.problemas.append(Problema(donde, linea, href, error, "roto"))
        elif codigo is not None and codigo >= 400:
            if codigo in CODIGOS_AVISO:
                motivo = f"el sitio no deja comprobarlo (código {codigo})"
                informe.problemas.append(Problema(donde, linea, href, motivo, "aviso"))
            else:
                informe.problemas.append(Problema(donde, linea, href, f"devuelve {codigo}", "roto"))


# ---------- fuentes: carpeta, fichero o URL ----------
def revisar_enlaces(fuente: str, externos: bool = True, timeout: float = 8.0) -> InformeEnlaces:
    """Busca enlaces, imágenes, hojas CSS y scripts rotos en una carpeta, un .html o una URL."""
    if re.match(r"^https?://", fuente, re.IGNORECASE):
        return _revisar_url(fuente, externos, timeout)
    return _revisar_local(Path(fuente).expanduser(), externos, timeout)


def _paginas_html(fuente: Path) -> tuple[Path, list[Path]]:
    fuente = Path(os.path.abspath(fuente))
    if fuente.is_file():
        if fuente.suffix.lower() not in EXTENSIONES_HTML:
            raise TareasError(f"«{fuente}» no es un fichero .html.")
        return fuente.parent, [fuente]
    if fuente.is_dir():
        paginas: list[Path] = []
        for carpeta, subcarpetas, nombres in os.walk(fuente):
            subcarpetas[:] = sorted(d for d in subcarpetas if d not in CARPETAS_IGNORADAS)
            paginas += [Path(carpeta) / n for n in sorted(nombres) if Path(n).suffix.lower() in EXTENSIONES_HTML]
        if not paginas:
            raise TareasError(f"No hay ficheros .html en «{fuente}».")
        return fuente, paginas
    raise TareasError(f"«{fuente}» no es un fichero .html, una carpeta ni una URL (http:// o https://).")


def _revisar_local(fuente: Path, externos: bool, timeout: float) -> InformeEnlaces:
    raiz, paginas = _paginas_html(fuente)
    informe = InformeEnlaces()
    pendientes: list[tuple[str, int, str, str]] = []
    cache_ids: dict[Path, set[str]] = {}
    for ruta in paginas:
        informe.paginas += 1
        donde = ruta.relative_to(raiz).as_posix()
        pagina = _leer_pagina(ruta)
        cache_ids[ruta] = pagina.ids
        for enlace in pagina.enlaces:
            tipo = _clasificar(enlace.href)
            if tipo == "plantilla":
                continue
            if tipo == "omitido":
                informe.omitidos += 1
            elif tipo == "externo":
                if externos:
                    informe.revisados += 1
                    url = ("https:" + enlace.href) if enlace.href.startswith("//") else enlace.href
                    pendientes.append((donde, enlace.linea, enlace.href, _normalizar(url)))
            else:
                informe.revisados += 1
                fallo = _comprobar_interno(enlace.href, ruta, raiz, pagina.ids, cache_ids)
                if fallo:
                    informe.problemas.append(Problema(donde, enlace.linea, enlace.href, *fallo))
    _comprobar_externos(pendientes, timeout, informe)
    informe.problemas.sort(key=lambda p: (p.donde, p.linea or 0))
    return informe


def _revisar_url(url: str, externos: bool, timeout: float) -> InformeEnlaces:
    html, final = _descargar_pagina(url, timeout)
    pagina = _analizar(html)
    informe = InformeEnlaces(paginas=1)
    servidor = urlsplit(final).netloc.lower()
    pendientes: list[tuple[str, int, str, str]] = []
    for enlace in pagina.enlaces:
        tipo = _clasificar(enlace.href)
        if tipo == "plantilla":
            continue
        if tipo == "omitido":
            informe.omitidos += 1
            continue
        if enlace.href.startswith("#"):  # ancla dentro de esta misma página
            informe.revisados += 1
            fragmento = unquote(enlace.href[1:])
            if _falta_el_id(fragmento, pagina.ids):
                motivo = f"no hay ningún elemento con id «{fragmento}» en esta página"
                informe.problemas.append(Problema(url, enlace.linea, enlace.href, motivo, "roto"))
            continue
        completa = _normalizar(urljoin(final, enlace.href))
        if not externos and urlsplit(completa).netloc.lower() != servidor:
            continue
        informe.revisados += 1
        pendientes.append((url, enlace.linea, enlace.href, completa))
    _comprobar_externos(pendientes, timeout, informe)
    informe.problemas.sort(key=lambda p: p.linea or 0)
    return informe


# ======================= cabeceras de seguridad =======================
BASICAS = ["Content-Security-Policy", "Strict-Transport-Security", "X-Frame-Options", "X-Content-Type-Options"]
RECOMENDADAS = ["Referrer-Policy", "Permissions-Policy"]
HSTS_MINIMO = 15_552_000  # 180 días
CONSEJOS_FALTA = {
    "Content-Security-Policy": "Limita de dónde carga recursos tu web. Empieza por default-src 'self'.",
    "Strict-Transport-Security": "Obliga al navegador a usar HTTPS. Añade: max-age=31536000; includeSubDomains",
    "X-Frame-Options": "Evita que te metan en un iframe (clickjacking): DENY o SAMEORIGIN.",
    "X-Content-Type-Options": "Añade: nosniff",
    "Referrer-Policy": "Recomendado: strict-origin-when-cross-origin",
    "Permissions-Policy": "Recomendado: camera=(), microphone=(), geolocation=()",
}
CONSEJOS_DEBIL = {
    "Content-Security-Policy": "Evita 'unsafe-inline' y 'unsafe-eval' en default-src y script-src.",
    "Strict-Transport-Security": "max-age demasiado bajo: usa al menos 15552000 (6 meses), mejor 31536000.",
    "X-Frame-Options": "Valor no válido: usa DENY o SAMEORIGIN.",
    "X-Content-Type-Options": "El valor debe ser exactamente nosniff.",
    "Referrer-Policy": "Valor poco privado: usa strict-origin-when-cross-origin o no-referrer.",
}


@dataclass
class Comprobacion:
    nombre: str
    estado: str  # "ok", "falta" o "debil"
    valor: str  # el de la cabecera, o «—» si no está
    consejo: str
    basica: bool


@dataclass
class InformeCabeceras:
    url: str
    codigo: int
    comprobaciones: list[Comprobacion]
    avisos: list[str]

    @property
    def faltan_basicas(self) -> list[str]:
        return [c.nombre for c in self.comprobaciones if c.basica and c.estado == "falta"]

    @property
    def correctas(self) -> int:
        return sum(1 for c in self.comprobaciones if c.estado == "ok")


def _directivas(csp: str) -> dict[str, str]:
    resultado = {}
    for trozo in csp.split(";"):
        partes = trozo.strip().split(None, 1)
        if partes:
            resultado[partes[0].lower()] = partes[1] if len(partes) > 1 else ""
    return resultado


def _csp_debil(csp: str) -> bool:
    d = _directivas(csp)
    return any(x in d.get(nombre, "").lower() for nombre in ("default-src", "script-src")
               for x in ("'unsafe-inline'", "'unsafe-eval'"))


def evaluar_cabeceras(h: dict[str, str], https: bool) -> list[Comprobacion]:
    """h: cabeceras de la respuesta con los nombres en minúsculas. https: ¿se sirvió por HTTPS?"""
    csp = h.get("content-security-policy", "")
    resultado = []
    for nombre in BASICAS + RECOMENDADAS:
        valor = h.get(nombre.lower(), "")
        basica = nombre in BASICAS
        estado, consejo = "ok", ""
        if nombre == "Strict-Transport-Security" and not https:
            estado, consejo = "falta", "Tu web se ha servido por HTTP: usa HTTPS y después activa HSTS."
        elif nombre == "X-Frame-Options" and "frame-ancestors" in _directivas(csp):
            valor = valor or "(cubierto por CSP frame-ancestors)"
        elif not valor:
            estado, consejo = "falta", CONSEJOS_FALTA[nombre]
        elif _es_debil(nombre, valor):
            estado, consejo = "debil", CONSEJOS_DEBIL[nombre]
        resultado.append(Comprobacion(nombre, estado, valor or "—", consejo, basica))
    return resultado


def _es_debil(nombre: str, valor: str) -> bool:
    v = valor.strip().lower()
    if nombre == "Content-Security-Policy":
        return _csp_debil(valor)
    if nombre == "Strict-Transport-Security":
        m = re.search(r"max-age\s*=\s*(\d+)", v)
        return m is None or int(m.group(1)) < HSTS_MINIMO
    if nombre == "X-Frame-Options":
        return v not in ("deny", "sameorigin")
    if nombre == "X-Content-Type-Options":
        return v != "nosniff"
    if nombre == "Referrer-Policy":
        return v in ("unsafe-url", "no-referrer-when-downgrade")
    return False  # Permissions-Policy: si está, vale


def _avisos(crudas: list[tuple[str, str]], h: dict[str, str]) -> list[str]:
    """Fugas de información, CORS abierto y cookies flojas. Nunca incluye el valor de una cookie."""
    avisos = []
    if h.get("x-powered-by"):
        avisos.append(f"X-Powered-By revela tecnología ({h['x-powered-by']}): quítala.")
    if re.search(r"\d", h.get("server", "")):
        avisos.append(f"Server revela la versión ({h['server']}): oculta el número.")
    if h.get("access-control-allow-origin", "").strip() == "*":
        avisos.append("CORS abierto a todo el mundo (Access-Control-Allow-Origin: *): "
                      "limítalo a tu web si la API tiene datos.")
    for nombre, valor in crudas:
        if nombre.lower() != "set-cookie":
            continue
        trozos = valor.split(";")
        cookie = trozos[0].split("=")[0].strip()
        atributos = {t.strip().split("=")[0].lower() for t in trozos[1:]}
        faltan = [n for n, a in (("Secure", "secure"), ("HttpOnly", "httponly"), ("SameSite", "samesite"))
                  if a not in atributos]
        if faltan:
            avisos.append(f"La cookie «{cookie}» no lleva {', '.join(faltan)}.")
    return avisos


def revisar_cabeceras(url: str, timeout: float = 10.0) -> InformeCabeceras:
    """Pide la página y evalúa sus cabeceras de seguridad. Sin esquema, se asume https://."""
    url = url.strip()
    if "://" not in url:
        url = "https://" + url
    if urlsplit(url).scheme.lower() not in ("http", "https"):
        raise TareasError("Solo se admiten direcciones http:// o https://.")
    peticion = urllib.request.Request(_normalizar(url), headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
            codigo, crudas, final = respuesta.status, list(respuesta.headers.items()), respuesta.geturl()
    except urllib.error.HTTPError as e:  # un 404 también trae cabeceras
        codigo, crudas, final = e.code, list(e.headers.items()), url
        e.close()
    except (urllib.error.URLError, OSError, http.client.HTTPException, ValueError) as e:
        raise TareasError(
            f"No puedo conectar con {url}: {_motivo_error(e, timeout)}. "
            "Si es un servidor gratis que tarda en despertar (Render), prueba con --timeout 60."
        ) from None
    h = {nombre.lower(): valor for nombre, valor in crudas}
    https = urlsplit(final).scheme.lower() == "https"
    return InformeCabeceras(final, codigo, evaluar_cabeceras(h, https), _avisos(crudas, h))
