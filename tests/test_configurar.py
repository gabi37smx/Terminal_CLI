"""Pruebas de dam configurar y del vocabulario de ciclos (ciclos.py).

Nunca tocan tu almacén ni tu ~/.config: DAM_ALMACEN apunta a una carpeta temporal y el
acciones.json se guarda con --config en otra.
"""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from tareas import ciclos, config, configurar
from tareas.cli import app
from tareas.errores import ConfigError

runner = CliRunner()
PLANTILLA = Path(__file__).parent.parent / "acciones.json"  # la del repo: 1º de DAM


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    """Almacén de mentira con asignaturas/ vacío y una carpeta para guardar el acciones.json."""
    almacen = tmp_path / "almacen"
    (almacen / "asignaturas").mkdir(parents=True)
    monkeypatch.setenv("DAM_ALMACEN", str(almacen))
    monkeypatch.chdir(tmp_path)  # sin acciones.json en la carpeta actual
    return {"almacen": almacen / "asignaturas", "destino": tmp_path / "config" / "acciones.json"}


def lanzar(entorno, *argumentos, entrada=None):
    return runner.invoke(app, ["--config", str(entorno["destino"]), "configurar",
                               "--plantilla", str(PLANTILLA), *argumentos], input=entrada)


def guardado(entorno) -> dict:
    return json.loads(entorno["destino"].read_text(encoding="utf-8"))


# ---------- el vocabulario ----------
def test_cada_asignatura_de_cada_ciclo_existe_y_su_carpeta_es_valida():
    for clave, ciclo in ciclos.CICLOS.items():
        for curso, lista in ciclo.cursos.items():
            assert lista, f"{clave} {curso}º no tiene asignaturas"
            assert len(lista) == len(set(lista)), f"{clave} {curso}º repite asignaturas"
            for nombre in lista:
                assert nombre in ciclos.ASIGNATURAS, f"{nombre} ({clave} {curso}º) no está en ASIGNATURAS"
                assert config.NOMBRE_VALIDO.match(nombre)  # minúsculas y guiones: vale como carpeta


def test_las_palabras_clave_estan_escritas_como_las_compara_ordenar():
    from tareas.acciones import _normalizar

    for nombre, a in ciclos.ASIGNATURAS.items():
        assert a.palabras and a.castellano and a.valenciano, nombre
        for palabra in a.palabras:
            # Si no estuviera normalizada (tildes, puntos...), nunca coincidiría con nada
            assert _normalizar(palabra) == palabra, f"{nombre}: «{palabra}»"
        assert all(e.startswith(".") and e == e.lower() for e in a.extensiones), nombre


def test_1_de_dam_es_justo_lo_que_hay_en_el_acciones_json_del_repo():
    plantilla = json.loads(PLANTILLA.read_text(encoding="utf-8"))
    assert ciclos.asignaturas_de("dam", [1]) == configurar.asignaturas_actuales(plantilla)


@pytest.mark.parametrize("texto, esperado", [("ASIX", "asir"), ("asir", "asir"), (" Smx ", "smx"), ("otro", "otro")])
def test_ciclo_valido_acepta_asix_y_mayusculas(texto, esperado):
    assert ciclos.ciclo_valido(texto) == esperado


def test_ciclo_desconocido_dice_cuales_hay():
    with pytest.raises(ValueError, match="smx, dam, daw, asir, asix, otro"):
        ciclos.ciclo_valido("teleco")


def test_los_dos_cursos_ponen_primero_los_de_1_y_no_repiten_los_comunes():
    lista = list(ciclos.asignaturas_de("daw", [2, 1]))
    assert lista[:8] == ciclos.CICLOS["daw"].cursos[1]
    assert lista.count("ipo") == 1 and lista.count("proyecto") == 1
    assert "servidor" in lista and "cliente" in lista


def test_por_extension_gana_la_primera_asignatura():
    assert ciclos.por_extension(["bases-datos", "admin-bases-datos"])[".sql"] == "bases-datos"
    assert ciclos.por_extension(["admin-bases-datos"])[".sql"] == "admin-bases-datos"
    assert ciclos.por_extension(["fol"]) == {}  # una asignatura tuya no tiene extensiones


def test_nombre_de_carpeta_sin_tildes_ni_espacios():
    assert ciclos.a_nombre_de_carpeta("Formación y Orientación Laboral") == "formacion-y-orientacion-laboral"
    assert ciclos.etiqueta("dam", [1]) == "1º de DAM"
    assert ciclos.etiqueta("smx", [1, 2]) == "SMX"


# ---------- aplicar un perfil a la plantilla ----------
def test_si_eliges_1_de_dam_las_acciones_no_cambian():
    plantilla = json.loads(PLANTILLA.read_text(encoding="utf-8"))
    datos = configurar.aplicar(plantilla, "dam", [1], ciclos.asignaturas_de("dam", [1]))
    assert datos["perfil"] == {"ciclo": "dam", "cursos": [1]}
    assert datos["acciones"] == plantilla["acciones"]  # ni descripciones, ni instrucciones, ni extensiones


def test_1_de_smx_cambia_ordenar_y_clasificar_sin_tocar_la_plantilla():
    plantilla = json.loads(PLANTILLA.read_text(encoding="utf-8"))
    copia = json.loads(json.dumps(plantilla))
    datos = configurar.aplicar(plantilla, "smx", [1], ciclos.asignaturas_de("smx", [1]))
    assert plantilla == copia  # aplicar no modifica lo que recibe
    ordenar = next(a for a in datos["acciones"] if a["tipo"] == "ordenar")
    clasificar = next(a for a in datos["acciones"] if a["tipo"] == "clasificar")
    assert list(ordenar["carpetas"]) == ciclos.CICLOS["smx"].cursos[1]
    assert ordenar["por_extension"][".pkt"] == "redes-locales"  # Packet Tracer
    assert ".py" not in ordenar["por_extension"]  # en SMX no hay «programacion»
    assert "1º de SMX" in ordenar["descripcion"] and "DAM" not in ordenar["descripcion"]
    assert clasificar["categorias"] == [*ciclos.CICLOS["smx"].cursos[1], "otros"]
    assert "Redes locales" in clasificar["instrucciones"] and "DAM" not in clasificar["instrucciones"]
    config.validar_datos(datos)  # el resultado es un acciones.json válido


def test_cambiar_curso_en_los_textos():
    assert configurar._cambiar_curso("por asignatura del DAM y", "2º de DAW") == "por asignatura de 2º de DAW y"
    assert configurar._cambiar_curso("su asignatura de 1º de DAM", "SMX") == "su asignatura de SMX"
    assert configurar._cambiar_curso("apuntes de 1º de SMX", "tu curso") == "apuntes de tu curso"


def test_sin_asignaturas_no_se_aplica():
    with pytest.raises(ConfigError, match="al menos una"):
        configurar.aplicar({"version": 1, "acciones": []}, "otro", [1], {})


def test_perfil_mal_escrito_no_valida():
    datos = json.loads(PLANTILLA.read_text(encoding="utf-8"))
    datos["perfil"] = {"ciclo": "dam", "cursos": [3]}
    with pytest.raises(ConfigError, match="perfil"):
        config.validar_datos(datos)


# ---------- el comando ----------
def test_sin_preguntas_guarda_y_crea_las_carpetas_con_gitkeep(entorno):
    r = lanzar(entorno, "--ciclo", "asix", "--curso", "1", "--si", "--crear-carpetas")
    assert r.exit_code == 0, r.output
    datos = guardado(entorno)
    assert datos["perfil"] == {"ciclo": "asir", "cursos": [1]}
    for nombre in ciclos.CICLOS["asir"].cursos[1]:
        assert (entorno["almacen"] / nombre / ".gitkeep").is_file()  # git no sube carpetas vacías
    assert "dam sync" in r.output


def test_con_si_no_crea_carpetas_si_no_se_lo_pides(entorno):
    r = lanzar(entorno, "--ciclo", "dam", "--curso", "2", "--si")
    assert r.exit_code == 0, r.output
    assert list(entorno["almacen"].iterdir()) == []
    assert "Faltan en tu almacén" in r.output


def test_simular_no_guarda_nada(entorno):
    r = lanzar(entorno, "--ciclo", "daw", "--curso", "2", "--si", "--simular")
    assert r.exit_code == 0, r.output
    assert "(simulado)" in r.output
    assert not entorno["destino"].exists()
    assert list(entorno["almacen"].iterdir()) == []


def test_la_segunda_vez_guarda_copia_y_recuerda_tus_asignaturas(entorno):
    primera = lanzar(entorno, "--ciclo", "smx", "--curso", "1", "--quitar", "ingles",
                     "--nueva", "Formación y Orientación=fol,contrato", "--si")
    assert primera.exit_code == 0, primera.output
    # Sin --ciclo ni --curso: usa lo de la última vez, con tus cambios (sin inglés y con fol)
    segunda = lanzar(entorno, "--si")
    assert segunda.exit_code == 0, segunda.output
    carpetas = configurar.asignaturas_actuales(guardado(entorno))
    assert "ingles" not in carpetas
    assert carpetas["formacion-y-orientacion"] == ["fol", "contrato"]
    copias = list(entorno["destino"].parent.glob("acciones.json.antes-*"))
    assert len(copias) == 1
    assert "La versión anterior" in segunda.output


def test_con_preguntas_como_adduser(entorno):
    # ciclo 4 (ASIR), curso 2, sí quiero cambiar, quito la 1.ª, añado «fol» con sus palabras,
    # guardo y sí a crear las carpetas
    entrada = "4\n2\ns\n1\nfol\nfol, contrato\ns\ns\n"
    r = lanzar(entorno, entrada=entrada)
    assert r.exit_code == 0, r.output
    assert "¿Qué estudias?" in r.output and "ASIR" in r.output
    carpetas = configurar.asignaturas_actuales(guardado(entorno))
    assert "admin-bases-datos" not in carpetas  # era la 1.ª de 2º de ASIR
    assert carpetas["fol"] == ["fol", "contrato"]
    assert (entorno["almacen"] / "fol" / ".gitkeep").is_file()


def test_si_no_confirmas_no_guarda(entorno):
    r = lanzar(entorno, entrada="2\n1\n\nn\n")  # DAM, 1º, sin cambios, NO guardar
    assert r.exit_code == 1
    assert not entorno["destino"].exists()


def test_ciclo_desconocido_es_error_de_uso(entorno):
    r = lanzar(entorno, "--ciclo", "teleco", "--si")
    assert r.exit_code == 2
    assert "no es un ciclo que conozca" in r.output


def test_otro_ciclo_sin_asignaturas_no_guarda(entorno):
    r = lanzar(entorno, "--ciclo", "otro", "--si")
    assert r.exit_code == 3
    assert "--nueva" in r.output
    assert not entorno["destino"].exists()


def test_otro_ciclo_con_tus_asignaturas(entorno):
    r = lanzar(entorno, "--ciclo", "otro", "--nueva", "cocina=receta,horno", "--nueva", "sala", "--si")
    assert r.exit_code == 0, r.output
    datos = guardado(entorno)
    assert configurar.asignaturas_actuales(datos) == {"cocina": ["receta", "horno"], "sala": ["sala"]}
    ordenar = next(a for a in datos["acciones"] if a["tipo"] == "ordenar")
    assert "por_extension" not in ordenar  # tus asignaturas no tienen extensiones propias
    assert "tu curso" in ordenar["descripcion"]


def test_quitar_una_que_no_esta_es_error_de_uso(entorno):
    r = lanzar(entorno, "--ciclo", "dam", "--curso", "1", "--quitar", "cocina", "--si")
    assert r.exit_code == 2
    assert not entorno["destino"].exists()


# ---------- arreglos tras la prueba como alumno de SMX (11-nov) ----------
def test_un_numero_en_asignaturas_nuevas_se_explica_y_se_vuelve_a_preguntar(entorno):
    # SMX, 1º, quiero cambiar, quito la 1 y la 2, en «nuevas» escribo números (el fallo del 11-nov),
    # me lo explica, Enter (ninguna), guardo y no creo carpetas
    r = lanzar(entorno, entrada="1\n1\ns\n1, 2\n3,4,5\n\ns\nn\n")
    assert r.exit_code == 0, r.output
    assert "es un número" in r.output and "ya se quedan" in r.output
    assert "Te quedas con: montaje-equipos" in r.output
    carpetas = configurar.asignaturas_actuales(guardado(entorno))
    assert list(carpetas) == [a for a in ciclos.CICLOS["smx"].cursos[1] if a not in ("ingles", "ipo")]


def test_nueva_con_un_numero_no_guarda(entorno):
    r = lanzar(entorno, "--ciclo", "smx", "--curso", "1", "--nueva", "3", "--si")
    assert r.exit_code == 1
    assert "es un número" in r.output
    assert not entorno["destino"].exists()


@pytest.mark.parametrize("fichero, asignatura", [
    ("packet-tracer-acl.pka", "redes-locales"),  # actividad de Packet Tracer
    ("T06.02_Activitat discos durs.odt", "montaje-equipos"),
    ("ANALISIS DE CAIXES.odt", "montaje-equipos"),
    ("Concesionario.odb", "ofimatica"),  # LibreOffice Base
    ("Any bisiest.ods", None),  # .ods sin pistas en el nombre: no se adivina (lo hace clasificar)
])
def test_vocabulario_de_1_de_smx(tmp_path, fichero, asignatura):
    from tareas.acciones import Ordenar

    asignaturas = ciclos.asignaturas_de("smx", [1])
    ordenar = Ordenar({"nombre": "o", "descripcion": "o", "tipo": "ordenar", "carpetas": asignaturas,
                       "por_extension": ciclos.por_extension(list(asignaturas))})
    ruta = tmp_path / fichero
    ruta.write_text("x", encoding="utf-8")
    assert ordenar.clasificar(ruta) == asignatura


# ---------- la segunda vez, con un vocabulario que ha aprendido palabras (12-nov) ----------
def test_la_ultima_vez_trae_las_palabras_nuevas_del_vocabulario_y_respeta_las_tuyas(entorno):
    primera = lanzar(entorno, "--ciclo", "smx", "--curso", "1", "--nueva", "fol=fol", "--si")
    assert primera.exit_code == 0, primera.output
    # Simula un acciones.json guardado con un vocabulario viejo: montaje sin «discos» y con una palabra tuya
    datos = guardado(entorno)
    ordenar = next(a for a in datos["acciones"] if a["tipo"] == "ordenar")
    ordenar["carpetas"]["montaje-equipos"] = ["montaje", "torre"]
    entorno["destino"].write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")

    segunda = lanzar(entorno, "--si")
    assert segunda.exit_code == 0, segunda.output
    assert "palabras clave nuevas del vocabulario" in segunda.output
    carpetas = configurar.asignaturas_actuales(guardado(entorno))
    assert "discos" in carpetas["montaje-equipos"]  # la aprendió ciclos.py
    assert "torre" in carpetas["montaje-equipos"]  # la tuya se queda
    assert carpetas["montaje-equipos"].count("montaje") == 1  # sin repetir
    assert carpetas["fol"] == ["fol"]  # tu asignatura no cambia


def test_palabras_al_dia_no_cambia_lo_que_ya_esta_al_dia():
    actuales = ciclos.asignaturas_de("dam", [1])
    assert configurar.palabras_al_dia(actuales) == actuales


def test_ordenar_al_almacen_sin_git_no_ofrece_sync(tmp_path, monkeypatch):
    almacen = tmp_path / "almacen"
    (almacen / "asignaturas" / "redes-locales").mkdir(parents=True)
    origen = tmp_path / "descargas"
    origen.mkdir()
    (origen / "practica.pka").write_text("x", encoding="utf-8")
    acciones = {"version": 1, "acciones": [{
        "nombre": "ordenar", "descripcion": "o", "tipo": "ordenar", "al_almacen": True,
        "carpetas": {"redes-locales": ["redes"]}, "por_extension": {".pka": "redes-locales"}}]}
    ruta = tmp_path / "acciones.json"
    ruta.write_text(json.dumps(acciones), encoding="utf-8")
    monkeypatch.setenv("DAM_ALMACEN", str(almacen))
    r = runner.invoke(app, ["--config", str(ruta), "ejecutar", "ordenar", str(origen)], input="s\n")
    assert r.exit_code == 0, r.output
    assert (almacen / "asignaturas" / "redes-locales" / "practica.pka").is_file()
    salida = " ".join(r.output.split())  # sin los saltos de línea de la consola
    assert "no es un repositorio git" in salida
    assert "¿Hago ahora dam sync" not in salida
