import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import config
from tareas.cli import app
from tareas.errores import AccionNoValida, ConfigError

BASE = {
    "version": 1,
    "acciones": [
        {"nombre": "mover-pdf", "descripcion": "d", "tipo": "mover", "destino": "x",
         "filtro": {"extensiones": [".pdf"]}},
    ],
}


def escribir(tmp_path: Path, datos, nombre="a.json") -> Path:
    ruta = tmp_path / nombre
    ruta.write_text(datos if isinstance(datos, str) else json.dumps(datos), encoding="utf-8")
    return ruta


def con_accion(**cambios) -> dict:
    accion = {**BASE["acciones"][0], **cambios}
    return {"version": 1, "acciones": [accion]}


def test_valido(tmp_path):
    assert len(config.cargar(escribir(tmp_path, BASE))) == 1


def test_acepta_bom_de_powershell(tmp_path):
    ruta = tmp_path / "a.json"
    ruta.write_bytes(b"\xef\xbb\xbf" + json.dumps(BASE).encode())
    assert config.cargar(ruta)


def test_json_roto_dice_linea_y_columna(tmp_path):
    with pytest.raises(ConfigError, match=r"línea \d+, columna \d+"):
        config.cargar(escribir(tmp_path, '{"version": 1, "acciones": [],}'))


def test_fichero_inexistente(tmp_path):
    with pytest.raises(ConfigError, match="No encuentro"):
        config.buscar(tmp_path / "nada.json")


@pytest.mark.parametrize("datos, campo", [
    (con_accion(tipo="mober"), "tipo"),
    (con_accion(destino=""), "destino"),
    (con_accion(filtro={"patron": "*.tmp"}), "filtro.patron"),
    (con_accion(filtro={"extensiones": ["pdf"]}), "filtro.extensiones"),
    (con_accion(filtro={"mas_antiguo_que_dias": -3}), "filtro.mas_antiguo_que_dias"),
    (con_accion(filtro={"inventado": 1}), "filtro.inventado"),
    (con_accion(nombre="Con Espacios"), "nombre"),
    (con_accion(tipo="renombrar", plantilla="{foo}"), "plantilla"),
    (con_accion(tipo="renombrar", plantilla="{fecha:%d/%m}_{n}"), "plantilla"),
    (con_accion(tipo="borrar", destino="x", filtro={}), "filtro"),
    (con_accion(tipo="ordenar", carpetas={"a": []}), "carpetas.a"),
    (con_accion(tipo="ordenar", carpetas={"a": ["x"]}, por_extension={".py": "b"}), "por_extension..py"),
    (con_accion(tipo="convertir", calidad=500), "calidad"),
    (con_accion(confirmar="si"), "confirmar"),
])
def test_casos_feos_dicen_accion_y_campo(tmp_path, datos, campo):
    with pytest.raises(AccionNoValida) as e:
        config.cargar(escribir(tmp_path, datos))
    assert e.value.campo == campo
    assert e.value.codigo_salida == 3
    assert "Acción «" in str(e.value)


def test_nombre_repetido(tmp_path):
    datos = {"version": 1, "acciones": [BASE["acciones"][0], BASE["acciones"][0]]}
    with pytest.raises(AccionNoValida, match="repetido"):
        config.cargar(escribir(tmp_path, datos))


def test_sin_version_o_sin_acciones(tmp_path):
    with pytest.raises(ConfigError):
        config.cargar(escribir(tmp_path, {"acciones": BASE["acciones"]}))
    with pytest.raises(ConfigError, match="vacía"):
        config.cargar(escribir(tmp_path, {"version": 1, "acciones": []}))


def test_almacen_mal(tmp_path):
    with pytest.raises(ConfigError, match="almacen"):
        config.cargar(escribir(tmp_path, {**BASE, "almacen": {"sitio": "x"}}))


def test_cli_validar_sale_con_3_sin_traza(tmp_path):
    ruta = escribir(tmp_path, '{"version": 1,}')
    r = CliRunner().invoke(app, ["--config", str(ruta), "validar"])
    assert r.exit_code == 3
    assert "Traceback" not in r.output


def test_cli_validar_ok(tmp_path):
    r = CliRunner().invoke(app, ["--config", str(escribir(tmp_path, BASE)), "validar"])
    assert r.exit_code == 0 and "1 acciones válidas" in r.output
