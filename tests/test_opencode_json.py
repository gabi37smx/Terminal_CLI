"""Las reglas de opencode.json que protegen mis ficheros no se pueden perder sin que lo note.

El 3-nov, OpenCode creó ficheros de prueba y luego los borró con Remove-Item: «rm *» estaba
denegado, pero en Windows se borra con otras órdenes. Si alguien (o un agente) quita una de
estas reglas, esta prueba se pone en rojo.
"""

import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = json.loads((RAIZ / "opencode.json").read_text(encoding="utf-8"))
BASH = CONFIG["permission"]["bash"]

# Lo irreversible lo hago yo: borrar (Linux, macOS y Windows), tirar cambios sin guardar, deshacer
# commits y subir. Las reglas distinguen mayúsculas y PowerShell no: «remove-item» va aparte
# (lo vio el revisor el 17-nov).
PELIGROSAS = ["git push *", "git reset *", "git clean *", "git restore *", "git checkout -- *", "sudo *",
              "rm *", "Remove-Item *", "remove-item *", "ri *", "del *", "erase *", "rmdir *", "rd *"]


@pytest.mark.parametrize("orden", PELIGROSAS)
def test_las_ordenes_que_borran_o_suben_estan_denegadas(orden):
    assert BASH.get(orden) == "deny", f"«{orden}» tiene que estar en deny en opencode.json"


def test_lo_demas_pregunta_y_ejecutar_acciones_tambien():
    assert BASH["*"] == "ask"
    assert BASH["uv run mochila ejecutar *"] == "ask"   # el agente no ejecuta acciones sin preguntarme
    assert CONFIG["permission"]["edit"] == "ask"


def test_plan_y_explore_no_editan_y_las_claves_no_se_leen():
    for agente in ("plan", "explore"):
        assert CONFIG["agent"][agente]["permission"]["edit"] == "deny"
    lectura = CONFIG["permission"]["read"]
    assert lectura["*.env"] == "deny" and lectura["*.env.example"] == "allow"


def test_el_revisor_solo_lee():
    texto = (RAIZ / ".opencode" / "agents" / "revisor.md").read_text(encoding="utf-8")
    assert "edit: deny" in texto and "webfetch: deny" in texto
    assert '"*": deny' in texto            # en bash, todo denegado salvo git diff/log/status
    assert "VEREDICTO: OK" in texto and "VEREDICTO: CAMBIAR" in texto
