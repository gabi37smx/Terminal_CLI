"""instalar.ps1 en un Windows recién instalado: se ejecuta de verdad su paso del TAB (4b) con PowerShell.

Lo encontró la instalación cruzada: sin la carpeta .config\\mochila, Set-Content fallaba en rojo y aun así
se añadía al perfil una línea que cargaba un script inexistente.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

pytestmark = pytest.mark.skipif(
    sys.platform != "win32" or not shutil.which("powershell"), reason="instalar.ps1 es para Windows"
)


def paso_tab() -> str:
    """El trozo de instalar.ps1 entre «# 4b.» y «# 5.»."""
    texto = (RAIZ / "instalar.ps1").read_text(encoding="utf-8")
    return re.search(r"# 4b\..*?(?=\n# 5\.)", texto, re.S).group(0)


def ejecutar_paso_tab(casa: Path, perfil: Path, politica: str = "RemoteSigned") -> subprocess.CompletedProcess:
    # Lo que el resto de instalar.ps1 define antes, y $HOME y $PROFILE apuntando a una carpeta de prueba
    bloque = (paso_tab()
              .replace("$HOME", f"'{casa}'")
              .replace("$PROFILE.CurrentUserAllHosts", f"'{perfil}'")
              .replace('& (Join-Path $CarpetaBin "mochila.exe")', f"& '{sys.executable}' -m tareas"))
    script = casa / "paso_tab.ps1"
    script.write_text(
        f"function Get-ExecutionPolicy {{ param($Scope) '{politica}' }}\n"
        "function Paso($t) { Write-Host \"==> $t\" }\n"
        "function Ok($t) { Write-Host \"OK $t\" }\n"
        "function Aviso($t) { Write-Host \"AVISO $t\" }\n"
        "function Tiene($c) { $false }\n"
        + bloque,
        encoding="utf-8-sig",  # con BOM: Windows PowerShell 5.1 lee así las tildes
    )
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=RAIZ,
    )


def test_en_un_windows_limpio_crea_la_carpeta_y_el_script(tmp_path):
    casa = tmp_path / "Alumno"
    casa.mkdir()  # sin .config: como un usuario recién creado
    perfil = casa / "Documents" / "WindowsPowerShell" / "profile.ps1"
    r = ejecutar_paso_tab(casa, perfil)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "No se puede encontrar" not in r.stdout + r.stderr
    script_tab = casa / ".config" / "mochila" / "completado.ps1"
    assert "Register-ArgumentCompleter" in script_tab.read_text(encoding="utf-8-sig")
    assert str(script_tab) in perfil.read_text(encoding="utf-8-sig")


def test_repetir_el_instalador_no_duplica_la_linea_del_perfil(tmp_path):
    casa = tmp_path / "Alumno"
    casa.mkdir()
    perfil = casa / "profile.ps1"
    ejecutar_paso_tab(casa, perfil)
    ejecutar_paso_tab(casa, perfil)
    assert perfil.read_text(encoding="utf-8-sig").count("completado.ps1") == 1


def test_con_la_politica_restricted_no_toca_nada_y_explica_como_activarlo(tmp_path):
    casa = tmp_path / "Alumno"
    casa.mkdir()
    perfil = casa / "profile.ps1"
    r = ejecutar_paso_tab(casa, perfil, politica="Restricted")
    assert "Set-ExecutionPolicy -Scope CurrentUser RemoteSigned" in r.stdout
    assert not perfil.exists() and not (casa / ".config").exists()


def test_quita_del_perfil_la_linea_del_tab_de_cuando_se_llamaba_dam(tmp_path):
    casa = tmp_path / "Alumno"
    casa.mkdir()
    perfil = casa / "profile.ps1"
    vieja = f'. "{casa}\.config\dam\completado.ps1"  # autocompletado de dam (lo añadió instalar.ps1)'
    perfil.write_text(f"Set-Alias ll Get-ChildItem\r\n{vieja}\r\n", encoding="utf-8-sig")
    r = ejecutar_paso_tab(casa, perfil)
    assert r.returncode == 0, r.stdout + r.stderr
    texto = perfil.read_text(encoding="utf-8-sig")
    assert "autocompletado de dam" not in texto
    assert "Set-Alias ll Get-ChildItem" in texto  # lo tuyo no se toca
    assert "autocompletado de mochila" in texto


def ejecutar_paso_0(tmp_path: Path, carpeta_repo: str) -> str:
    """El aviso del paso 0 (Administrador y System32) con el repositorio en carpeta_repo."""
    texto = (RAIZ / "instalar.ps1").read_text(encoding="utf-8")
    bloque = re.search(r"# 0\..*?(?=\n# 1\.)", texto, re.S).group(0).replace("$PSScriptRoot", f"'{carpeta_repo}'")
    script = tmp_path / "paso_0.ps1"
    script.write_text("function Aviso($t) { Write-Host \"AVISO $t\" }\n" + bloque, encoding="utf-8-sig")
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_avisa_si_el_repo_quedo_en_system32(tmp_path):
    # La instalación cruzada del 26-nov: PowerShell de Administrador → el clone acabó en System32
    import os
    salida = ejecutar_paso_0(tmp_path, os.path.join(os.environ["SystemRoot"], "System32", "Terminal_CLI"))
    assert "carpeta de Windows" in salida and "PowerShell normal" in salida


def test_no_avisa_de_system32_si_el_repo_esta_en_tu_carpeta(tmp_path):
    assert "carpeta de Windows" not in ejecutar_paso_0(tmp_path, str(tmp_path / "Terminal_CLI"))
