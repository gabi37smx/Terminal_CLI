#!/usr/bin/env bash
# Revisa con el agente «revisor» de OpenCode lo que tienes preparado para el commit (git add).
#
#   bash scripts/revisar.sh        # 0 = VEREDICTO: OK · 1 = VEREDICTO: CAMBIAR (o sin veredicto)
#                                  # 2 = no se pudo revisar (sin opencode, tiempo agotado...)
#
# El revisor (.opencode/agents/revisor.md) no puede editar ni navegar, y en bash solo tiene
# «git diff/log/status». El diff le llega por la entrada estándar, así que no necesita más permisos.
# Sin nadie delante, un permiso «ask» cuenta como denegado: por eso aquí nunca va --auto.
set -euo pipefail

LIMITE=180   # segundos: si el servidor no contesta, el script no se queda colgado

cd "$(git rev-parse --show-toplevel)"

if git diff --staged --quiet; then
    echo "No hay nada preparado para el commit. Primero: git add <ficheros>"
    exit 0
fi

if ! command -v opencode >/dev/null 2>&1; then
    echo "No encuentro opencode: instálalo o revisa a mano con  git diff --staged" >&2
    exit 2
fi

# macOS no trae «timeout»; con Homebrew (coreutils) se llama gtimeout
if command -v timeout >/dev/null 2>&1; then
    CON_LIMITE=(timeout "$LIMITE")
elif command -v gtimeout >/dev/null 2>&1; then
    CON_LIMITE=(gtimeout "$LIMITE")
else
    CON_LIMITE=()
    echo "(aviso: sin «timeout» en este sistema, la revisión no tiene tiempo máximo)" >&2
fi

echo "Revisando $(git diff --staged --name-only | wc -l | tr -d ' ') fichero(s) con el agente revisor (máximo ${LIMITE} s)..."

estado=0
salida=$(git diff --staged | ${CON_LIMITE[@]+"${CON_LIMITE[@]}"} opencode run --agent revisor \
    "Revisa este diff (lo que voy a subir en el próximo commit). Acaba con la línea VEREDICTO: OK o VEREDICTO: CAMBIAR.") \
    || estado=$?

if [ "$estado" -eq 124 ]; then
    echo "El revisor no ha contestado en ${LIMITE} s (¿estás fuera de la red del centro?)." >&2
    exit 2
elif [ "$estado" -ne 0 ]; then
    echo "opencode ha fallado (código $estado): no se ha podido revisar." >&2
    exit 2
fi

echo "$salida"
echo

# Vale la ÚLTIMA línea con VEREDICTO (admite **negrita** o «comillas» alrededor)
veredicto=$(printf '%s\n' "$salida" | grep -Eo 'VEREDICTO: *(OK|CAMBIAR)' | tail -n 1 || true)
case "$veredicto" in
    *OK)      echo "✔ El revisor dice que se puede subir."; exit 0 ;;
    *CAMBIAR) echo "✘ El revisor pide cambios antes del commit." >&2; exit 1 ;;
    *)        echo "✘ El revisor no ha dado veredicto: lo cuento como no aprobado." >&2; exit 1 ;;
esac
