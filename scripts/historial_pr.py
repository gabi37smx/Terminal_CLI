"""Escribe docs/historial-pr.md: todas las pull requests del repo, por versión, con sus issues.

    uv run python scripts/historial_pr.py

Lo saca de GitHub con «gh» (tiene que estar instalado y con sesión iniciada) y de las etiquetas de git
(«git tag --contains»), así que no hay que escribir nada a mano: después de fusionar una PR o publicar
una versión, se vuelve a lanzar y se hace commit del .md.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "docs" / "historial-pr.md"
REPO = "https://github.com/gabi37smx/Terminal_CLI"
LIMITE = 500
# Las fechas, siempre en hora de España: el .md sale igual se genere donde se genere
try:
    ZONA = ZoneInfo("Europe/Madrid")
except ZoneInfoNotFoundError:   # Windows sin el paquete tzdata: hora de invierno, que es la de todo el curso
    ZONA = timezone(timedelta(hours=1))
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

# Lo que trae cada versión, en una frase (lo demás sale de GitHub)
QUE_TRAE = {
    "v1.0.0": "Las cuatro semanas del curso: las acciones con `acciones.json`, los comandos de seguridad, "
              "de proyectos y para organizar el PC, la capa de IA con su modo sin red, las pruebas en "
              "GitHub Actions (Linux, Windows y macOS) y la primera release.",
    "v1.0.1": "Los arreglos del ensayo de instalación en un Ubuntu recién instalado, siguiendo solo el "
              "README (issues #17 a #22).",
    "v1.1.0": "`configurar` y `crear-almacen` para cualquier ciclo, la IA gratis con OpenCode, `ordenar` "
              "por unidades, lo que salió probando en clase y con otra persona, y el cambio de nombre a `mochila`.",
    "v1.2.0": "Lo que salió probando en clase con el modelo del centro y en la instalación cruzada como alumno "
              "de ASIR (#53): el almacén «solo en este equipo», la IA sin elegir y sin red explicada, el "
              "revisor en el hook y la guía para quien corrige (`docs/entrega.md`).",
    None: "Lo que saldrá en la próxima versión: las fusionadas ya están en `main`; las abiertas, aún no.",
}
TITULO_VERSION = {"v1.0.0": "1.0.0", "v1.0.1": "1.0.1", "v1.1.0": "1.1.0", "v1.2.0": "1.2.0", None: "Sin publicar"}


def ejecutar(*orden: str) -> str:
    try:
        return subprocess.run(list(orden), cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
                              check=True).stdout
    except FileNotFoundError:
        sys.exit(f"No encuentro «{orden[0]}»: instálalo (y, si es gh, inicia sesión con  gh auth login).")
    except subprocess.CalledProcessError as error:
        sys.exit(f"«{' '.join(orden[:3])}...» ha fallado: {error.stderr.strip()}")


def gh_json(*orden: str) -> list[dict]:
    return json.loads(ejecutar("gh", *orden))


def fecha(iso: str | None, con_anio: bool = False) -> str:
    if not iso:
        return "—"
    dia = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(ZONA)
    return f"{dia.day}-{MESES[dia.month - 1]}" + (f"-{dia.year}" if con_anio else "")


def version_de(commit: str | None) -> str | None:
    """La primera etiqueta que contiene el commit (None si aún no se ha publicado o no está en este clon)."""
    if not commit:
        return None
    r = subprocess.run(["git", "tag", "--contains", commit, "--sort=creatordate"], cwd=RAIZ,
                       capture_output=True, text=True, encoding="utf-8")
    etiquetas = r.stdout.split() if r.returncode == 0 else []
    return etiquetas[0] if etiquetas else None


def version_de_pr(pr: dict) -> str | None:
    """La versión en la que salió una PR fusionada.

    Normalmente, la del commit de la fusión. Pero una PR encadenada que se fusionó en la rama de debajo
    (la #55, el 19-nov) tiene su fusión fuera de main: lo suyo llegó con otra PR (#57). Entonces vale
    la versión que contiene el último commit de la propia PR.
    """
    return (version_de((pr.get("mergeCommit") or {}).get("oid"))
            or version_de(pr.get("headRefOid")))


def celda(texto: str) -> str:
    return texto.replace("|", "\\|").replace("\n", " ")


def main() -> None:
    prs = gh_json("pr", "list", "--state", "all", "--limit", str(LIMITE), "--json",
                  "number,title,state,headRefName,headRefOid,mergedAt,createdAt,closingIssuesReferences,mergeCommit")
    issues = gh_json("issue", "list", "--state", "all", "--limit", str(LIMITE), "--json",
                     "number,title,state,createdAt,closedAt")
    if len(prs) >= LIMITE or len(issues) >= LIMITE:
        sys.exit(f"Hay {LIMITE} o más PR o issues: sube LIMITE en el script para no dejarte ninguna.")
    prs = [p for p in prs if p["state"] != "CLOSED"]          # las cerradas sin fusionar no cuentan
    prs.sort(key=lambda p: p["number"])

    por_version: dict[str | None, list[dict]] = {}
    cerrado_por: dict[int, int] = {}
    for p in prs:
        version = version_de_pr(p) if p["state"] == "MERGED" else None
        por_version.setdefault(version, []).append(p)
        if p["state"] == "MERGED":   # una PR abierta todavía no ha cerrado nada
            for issue in p["closingIssuesReferences"]:
                cerrado_por[issue["number"]] = p["number"]

    fusionadas = sum(p["state"] == "MERGED" for p in prs)
    abiertas = sum(p["state"] == "OPEN" for p in prs)
    huecos = sorted(i["number"] for i in issues)

    lineas = [
        "# Historial de pull requests",
        "",
        "Cada cambio entró en `main` desde su propia rama, con una PR que GitHub Actions prueba en Linux, Windows",
        "y macOS. Aquí está la lista entera, agrupada por la versión en la que salió. El detalle de lo que nota",
        "quien usa `mochila` está en el [CHANGELOG](../CHANGELOG.md), y el porqué de cada paso, en la",
        "[bitácora de prompts](prompts.md).",
        "",
        f"**{fusionadas} PR fusionadas**" + (f" y {abiertas} abiertas" if abiertas else "")
        + f", {len(issues)} issues y {len(ejecutar('git', 'tag', '--list', 'v*').split())} versiones publicadas.",
        "",
        "**Cómo leerlo:**",
        "- **Rama:** `feature/` añade algo nuevo; `arreglo/` o `fix/` corrige un fallo; `docs/` toca documentación",
        "  o la bitácora; `ci/` las pruebas automáticas; `release-X` prepara una versión.",
        "- **El nombre del comando:** en la #1 era `gabriel`, después `dam` y, desde la #41, `mochila`. Los títulos",
        "  se quedan con el nombre de entonces.",
        f"- **Los números que faltan** ({', '.join(f'#{n}' for n in huecos)}) son issues: GitHub numera issues y",
        "  PR con la misma cuenta.",
        "",
        "Este fichero se genera con `uv run python scripts/historial_pr.py` (lo saca de GitHub con `gh`): no se",
        "edita a mano.",
    ]

    orden = [v for v in ("v1.0.0", "v1.0.1", "v1.1.0", "v1.2.0") if v in por_version]
    orden += [v for v in por_version if v not in orden and v is not None]
    if None in por_version:
        orden.append(None)
    for version in orden:
        grupo = por_version[version]
        cabecera = TITULO_VERSION.get(version, version)
        if version:
            dia = ejecutar("git", "log", "-1", "--format=%cI", version).strip()
            cabecera += f" · {fecha(dia, con_anio=True)}"
        lineas += ["", f"## {cabecera} (#{grupo[0]['number']} a #{grupo[-1]['number']})", "",
                   QUE_TRAE.get(version, ""), "",
                   "| PR | Fusionada | Rama | Qué cambia | Cierra |",
                   "|---|---|---|---|---|"]
        for p in grupo:
            cuando = fecha(p["mergedAt"]) if p["state"] == "MERGED" else "abierta"
            cierra = ", ".join(f"[#{i['number']}]({REPO}/issues/{i['number']})" for i in p["closingIssuesReferences"])
            lineas.append(f"| [#{p['number']}]({REPO}/pull/{p['number']}) | {cuando} | `{p['headRefName']}` "
                          f"| {celda(p['title'])} | {cierra} |")

    lineas += ["", "## Issues", "",
               "Lo que encontré instalando en un ordenador limpio y lo que encontró otra persona al instalarlo.",
               "Cada uno se cerró desde la PR que lo arreglaba («Closes #N»).", "",
               "| Issue | Abierto | Qué pasaba | Lo cerró |", "|---|---|---|---|"]
    for i in sorted(issues, key=lambda i: i["number"]):
        pr = cerrado_por.get(i["number"])
        lineas.append(f"| [#{i['number']}]({REPO}/issues/{i['number']}) | {fecha(i['createdAt'])} "
                      f"| {celda(i['title'])} | {f'[#{pr}]({REPO}/pull/{pr})' if pr else ('abierto' if i['state'] == 'OPEN' else '—')} |")

    SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
    print(f"Escrito {SALIDA.relative_to(RAIZ)}: {len(prs)} PR y {len(issues)} issues.")


if __name__ == "__main__":
    main()
