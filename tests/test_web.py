"""test-links y check-headers contra un servidor local de mentira (sin internet)."""
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import web
from tareas.cli import app
from tareas.errores import TareasError

SEGURAS = {
    "Content-Security-Policy": "default-src 'self'",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=()",
}


class Falso(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _responder(self, con_cuerpo: bool):
        ruta = self.path
        codigo, cabeceras, cuerpo = 200, {}, b"ok"
        if ruta == "/roto":
            codigo = 404
        elif ruta == "/error":
            codigo = 500
        elif ruta == "/bot":
            codigo = 403
        elif ruta == "/redir":
            codigo, cabeceras = 302, {"Location": "/ok"}
        elif ruta == "/sinhead" and not con_cuerpo:
            codigo = 405
        elif ruta == "/seguro":
            cabeceras = dict(SEGURAS)
        elif ruta == "/inseguro":
            cabeceras = {"Server": "Apache/2.4.1", "X-Powered-By": "Express",
                         "Access-Control-Allow-Origin": "*", "Set-Cookie": "sid=abc123; Path=/"}
        elif ruta == "/pagina":
            cuerpo = (b'<a href="/ok">a</a><a href="/roto">b</a><a href="ok">c</a>'
                      b'<a href="mailto:x@y.es">m</a><img src="/ok">')
            cabeceras = {"Content-Type": "text/html; charset=utf-8"}
        self.send_response(codigo)
        for k, v in cabeceras.items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        if con_cuerpo:
            self.wfile.write(cuerpo)

    def do_GET(self):
        self._responder(True)

    def do_HEAD(self):
        self._responder(False)


@pytest.fixture
def servidor(monkeypatch):
    monkeypatch.setenv("NO_PROXY", "127.0.0.1,localhost")
    monkeypatch.setenv("no_proxy", "127.0.0.1,localhost")
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
    hilo = threading.Thread(target=srv.serve_forever, daemon=True)
    hilo.start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def escribir(ruta: Path, texto: str = ""):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


# ---------------- test-links: enlaces locales ----------------
@pytest.fixture
def sitio(tmp_path):
    escribir(tmp_path / "index.html", """<!doctype html><html><body id="top">
<a href="catalogo.html">ok</a>
<a href="catalogo.html#productos">ancla buena</a>
<a href="catalogo.html#nada">ancla mala</a>
<a href="css/estilos.css">hoja</a><link rel="stylesheet" href="/css/estilos.css">
<img src="img/falta.jpg">
<a href="#contacto">interno</a><a href="#fantasma">roto</a><a href="#top">arriba</a>
<a href="mailto:a@b.es">m</a><a href="tel:123">t</a><a href="ftp://x/y">f</a>
<a href="mi%20foto.png">espacio</a><a href="carpeta/">carpeta</a>
<link rel="preconnect" href="https://fonts.gstatic.com"><a href="{{ url }}">plantilla</a>
<section id="contacto"></section></body></html>""")
    escribir(tmp_path / "catalogo.html", '<h1 id="productos">Catálogo</h1>')
    escribir(tmp_path / "css/estilos.css", "body{}")
    escribir(tmp_path / "mi foto.png", "x")
    escribir(tmp_path / "carpeta/index.html", "hola")
    return tmp_path


def test_enlaces_locales(sitio):
    inf = web.revisar_enlaces(str(sitio), externos=False)
    motivos = {(p.enlace, p.gravedad) for p in inf.problemas}
    assert motivos == {("catalogo.html#nada", "aviso"), ("img/falta.jpg", "roto"), ("#fantasma", "roto")}
    assert inf.omitidos == 3  # mailto, tel y ftp
    assert inf.paginas == 3 and inf.rotos == 2  # index, catalogo y carpeta/index
    assert {p.linea for p in inf.problemas if p.enlace == "img/falta.jpg"} == {6}


def test_fuente_html_suelto_y_errores(sitio, tmp_path):
    assert web.revisar_enlaces(str(sitio / "catalogo.html"), externos=False).paginas == 1
    vacia = tmp_path / "vacia"; vacia.mkdir()
    with pytest.raises(TareasError, match="No hay ficheros .html"):
        web.revisar_enlaces(str(vacia))
    with pytest.raises(TareasError, match="no es un fichero"):
        web.revisar_enlaces(str(tmp_path / "nada"))


def test_carpetas_ignoradas(tmp_path):
    escribir(tmp_path / "a.html", "<a href='b.html'>x</a>"); escribir(tmp_path / "b.html")
    escribir(tmp_path / "node_modules/z/roto.html", "<a href='no.html'>x</a>")
    assert web.revisar_enlaces(str(tmp_path), externos=False).problemas == []


def test_mayusculas_distintas_en_sistemas_que_no_las_distinguen(tmp_path, monkeypatch):
    escribir(tmp_path / "Foto.jpg")
    monkeypatch.setattr(web.sys, "platform", "win32")
    assert web._existe_con_mayusculas(tmp_path / "Foto.jpg", tmp_path)
    assert not web._existe_con_mayusculas(tmp_path / "foto.jpg", tmp_path)  # lo que vería GitHub Pages


# ---------------- test-links: externos ----------------
def test_enlaces_externos(servidor, tmp_path):
    enlaces = "".join(f'<a href="{servidor}{r}">{r}</a>' for r in
                      ("/ok", "/roto", "/redir", "/sinhead", "/bot", "/error", "/roto"))
    escribir(tmp_path / "index.html", enlaces + '<a href="http://127.0.0.1:1/x">cerrado</a>')
    inf = web.revisar_enlaces(str(tmp_path), timeout=3)
    por_ruta = {p.enlace.replace(servidor, ""): (p.gravedad, p.motivo) for p in inf.problemas}
    assert por_ruta["/roto"] == ("roto", "devuelve 404")
    assert por_ruta["/error"] == ("roto", "devuelve 500")
    assert por_ruta["/bot"][0] == "aviso" and "403" in por_ruta["/bot"][1]
    assert por_ruta["http://127.0.0.1:1/x"][0] == "roto"
    assert not {"/ok", "/redir", "/sinhead"} & set(por_ruta)         # HEAD 405 y 302 funcionan
    assert [p.enlace for p in inf.problemas].count(servidor + "/roto") == 2  # cada aparición se avisa
    assert inf.revisados == 8


def test_url_como_fuente(servidor):
    inf = web.revisar_enlaces(servidor + "/pagina", timeout=3)
    assert inf.paginas == 1 and inf.omitidos == 1 and inf.revisados == 4
    assert [p.enlace for p in inf.problemas] == ["/roto"]
    with pytest.raises(TareasError, match="devuelve 404"):
        web.revisar_enlaces(servidor + "/roto")
    with pytest.raises(TareasError, match="No puedo abrir"):
        web.revisar_enlaces("http://127.0.0.1:1/", timeout=2)


def test_cli_test_links_codigos_de_salida(sitio, servidor):
    run = CliRunner()
    r = run.invoke(app, ["test-links", str(sitio), "--sin-externos"])
    assert r.exit_code == 1 and "img/falta.jpg" in r.output and "2 rotos" in r.output
    escribir(sitio / "limpio" / "index.html", f'<a href="{servidor}/ok">x</a><a href="../catalogo.html">y</a>')
    r = run.invoke(app, ["test-links", str(sitio / "limpio" / "index.html"), "--timeout", "3"])
    assert r.exit_code == 0 and "Sin enlaces rotos" in r.output
    assert run.invoke(app, ["test-links", str(sitio / "nada")]).exit_code == 1


# ---------------- check-headers ----------------
def cab(**kw):
    h = {k.lower(): v for k, v in SEGURAS.items()}
    h.update({k.replace("_", "-"): v for k, v in kw.items()})
    return h


def estados(h, https=True):
    return {c.nombre: c.estado for c in web.evaluar_cabeceras(h, https)}


def test_todo_bien():
    e = estados(cab())
    assert set(e.values()) == {"ok"} and len(e) == 6


def test_faltan_y_debiles():
    assert set(estados({}).values()) == {"falta"}
    assert estados(cab(), https=False)["Strict-Transport-Security"] == "falta"
    e = estados(cab(**{"content-security-policy": "default-src 'self' 'unsafe-inline'",
                       "strict-transport-security": "max-age=100", "x-frame-options": "ALLOW-FROM x",
                       "referrer-policy": "unsafe-url"}))
    assert [e[n] for n in ("Content-Security-Policy", "Strict-Transport-Security", "X-Frame-Options", "Referrer-Policy")] == ["debil"] * 4
    h = cab(**{"content-security-policy": "default-src 'self'; frame-ancestors 'none'"})
    del h["x-frame-options"]
    assert estados(h)["X-Frame-Options"] == "ok"


def test_avisos_de_fugas_cors_y_cookies():
    crudas = [("Server", "Apache/2.4.1"), ("X-Powered-By", "Express"), ("Access-Control-Allow-Origin", "*"),
              ("Set-Cookie", "sid=abc; Path=/; Secure"), ("Set-Cookie", "ok=1; Secure; HttpOnly; SameSite=Lax")]
    h = {k.lower(): v for k, v in crudas}
    avisos = web._avisos(crudas, h)
    assert len(avisos) == 4
    assert any("«sid»" in a and "HttpOnly" in a and "SameSite" in a and "abc" not in a for a in avisos)


def test_revisar_cabeceras_en_servidor(servidor):
    seguro = web.revisar_cabeceras(servidor + "/seguro", 3)
    assert seguro.codigo == 200 and seguro.faltan_basicas == ["Strict-Transport-Security"]  # solo porque es HTTP
    malo = web.revisar_cabeceras(servidor + "/inseguro", 3)
    assert len(malo.faltan_basicas) == 4 and len(malo.avisos) == 4
    assert web.revisar_cabeceras(servidor + "/roto", 3).codigo == 404      # un 404 también trae cabeceras


def test_revisar_cabeceras_errores():
    with pytest.raises(TareasError, match="--timeout 60"):
        web.revisar_cabeceras("http://127.0.0.1:1/", 2)
    with pytest.raises(TareasError, match="Solo se admiten"):
        web.revisar_cabeceras("ftp://x.es")


def test_cli_check_headers(servidor, monkeypatch):
    run = CliRunner()
    r = run.invoke(app, ["check-headers", servidor + "/inseguro", "--timeout", "3"])
    assert r.exit_code == 1 and "Faltan cabeceras básicas" in r.output and "abc123" not in r.output
    todo_ok = web.InformeCabeceras("https://x.es", 200, web.evaluar_cabeceras(cab(), True), [])
    monkeypatch.setattr(web, "revisar_cabeceras", lambda url, timeout: todo_ok)
    r = run.invoke(app, ["check-headers", "x.es"])
    assert r.exit_code == 0 and "6 de 6 cabeceras correctas" in r.output
