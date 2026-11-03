#!/usr/bin/env bash
# Instala y configura dam en Linux o macOS.
# Uso (desde la carpeta del repositorio clonado):  bash instalar.sh
# Se puede ejecutar todas las veces que quieras: lo que ya está hecho se salta.
set -euo pipefail

cd "$(dirname "$0")"   # trabaja siempre desde la carpeta del repositorio
PATH_ORIGINAL="$PATH"  # para saber después si tu terminal ya encuentra «dam»

paso()  { printf '\n==> %s\n' "$1"; }
ok()    { printf '    [ok] %s\n' "$1"; }
aviso() { printf '    [!] %s\n' "$1"; }

# 1. git -------------------------------------------------------------------
paso "Compruebo git"
if ! command -v git >/dev/null 2>&1; then
    aviso "No tienes git. Instálalo y vuelve a ejecutar este script:"
    aviso "  Ubuntu/Debian: sudo apt install git   ·   macOS: xcode-select --install"
    exit 1
fi
ok "$(git --version)"

# 2. uv --------------------------------------------------------------------
paso "Compruebo uv"
export PATH="$HOME/.local/bin:$PATH"   # aquí lo deja el instalador oficial
if ! command -v uv >/dev/null 2>&1; then
    echo "    No está instalado: lo descargo del instalador oficial (https://astral.sh/uv)"
    if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh
    else
        aviso "Necesito curl o wget para descargar uv."
        exit 1
    fi
fi
ok "$(uv --version)"

# 3. Dependencias y comando dam --------------------------------------------
paso "Instalo las dependencias (uv descarga Python 3.12 si hace falta)"
uv sync

paso "Instalo el comando dam para todo el sistema"
uv tool install --editable . --force
CARPETA_BIN="$(uv tool dir --bin)"
case ":$PATH_ORIGINAL:" in
    *":$CARPETA_BIN:"*) ok "Tu terminal ya encuentra los comandos de $CARPETA_BIN" ;;
    *)
        uv tool update-shell
        aviso "Al terminar, cierra esta terminal y abre otra para que «dam» funcione."
        ;;
esac

# 4. Configuración ---------------------------------------------------------
paso "Configuración de acciones"
CONFIG="$HOME/.config/dam/acciones.json"
if [ -f "$CONFIG" ]; then
    ok "Ya tienes $CONFIG (no la toco)"
else
    mkdir -p "$(dirname "$CONFIG")"
    cp acciones.json "$CONFIG"
    ok "Copiado acciones.json a $CONFIG (así dam funciona desde cualquier carpeta)"
fi

# 4b. Autocompletado con TAB -----------------------------------------------
# No uso «dam --install-completion»: miraría la terminal de ESTE script (bash), y en macOS la
# tuya es zsh. Así se mira la tuya ($SHELL) y se puede repetir sin duplicar nada.
paso "Activo el autocompletado con TAB"
case "$(basename "${SHELL:-}")" in
    bash) TERMINAL=bash; RC="$HOME/.bashrc" ;;
    zsh)  TERMINAL=zsh;  RC="$HOME/.zshrc" ;;
    *)    TERMINAL="" ;;
esac
if [ -z "$TERMINAL" ]; then
    aviso "Tu terminal (${SHELL:-desconocida}) no es bash ni zsh: actívalo a mano con  dam --install-completion"
else
    SCRIPT_TAB="$HOME/.config/dam/completado.$TERMINAL"
    mkdir -p "$(dirname "$SCRIPT_TAB")"
    # Con esta variable, dam no ejecuta nada: solo escribe el script de autocompletado
    if _DAM_COMPLETE="source_$TERMINAL" "$CARPETA_BIN/dam" > "$SCRIPT_TAB"; then
        if ! grep -qF "$SCRIPT_TAB" "$RC" 2>/dev/null; then
            {
                echo ""
                echo "# Autocompletado de dam (lo añadió instalar.sh)"
                if [ "$TERMINAL" = zsh ] && ! grep -q compinit "$RC" 2>/dev/null; then
                    echo "autoload -Uz compinit && compinit"
                fi
                echo "[ -f \"$SCRIPT_TAB\" ] && source \"$SCRIPT_TAB\""
            } >> "$RC"
        fi
        ok "TAB activado para $TERMINAL (en $RC). En una terminal nueva prueba: dam ej<TAB>"
    else
        aviso "No he podido generar el autocompletado. Puedes probar a mano: dam --install-completion"
    fi
fi

# 5. git: identidad y credenciales -----------------------------------------
paso "Preparo git para los commits de dam sync"
if [ -z "$(git config --global user.name || true)" ]; then
    nombre=""
    read -rp "    Tu nombre para los commits: " nombre || true
    if [ -n "$nombre" ]; then
        git config --global user.name "$nombre"
    fi
fi
if [ -z "$(git config --global user.email || true)" ]; then
    correo=""
    read -rp "    Tu correo de GitHub: " correo || true
    if [ -n "$correo" ]; then
        git config --global user.email "$correo"
    fi
fi
if [ -n "$(git config --global user.name || true)" ] && [ -n "$(git config --global user.email || true)" ]; then
    ok "git firmará como: $(git config --global user.name) <$(git config --global user.email)>"
else
    aviso "Sin nombre o correo, git no podrá hacer commits. Vuelve a ejecutar este script."
fi
# En Linux, que git recuerde el token un rato EN MEMORIA (nunca en un fichero).
# macOS ya lo guarda en el Llavero.
if [ "$(uname)" = "Linux" ] && [ -z "$(git config --global credential.helper || true)" ]; then
    git config --global credential.helper "cache --timeout=28800"
    ok "git recordará tu token 8 horas (solo en memoria)"
fi

# 6. Almacén de apuntes ----------------------------------------------------
paso "Almacén de apuntes"
ALMACEN="${DAM_ALMACEN:-$HOME/DAM-almacen}"
if [ -d "$ALMACEN/.git" ]; then
    ok "Ya está clonado en $ALMACEN"
elif [ -e "$ALMACEN" ]; then
    aviso "$ALMACEN existe pero no es un repositorio git: no lo toco."
else
    usuario=""
    read -rp "    Tu usuario de GitHub para clonar DAM-almacen (Enter para saltar): " usuario || true
    if [ -n "$usuario" ]; then
        echo "    Si git te pide contraseña, pega un token de GitHub: la contraseña normal no vale."
        if git clone "https://github.com/$usuario/DAM-almacen.git" "$ALMACEN"; then
            ok "Clonado en $ALMACEN"
        else
            aviso "No he podido clonarlo: revisa el usuario, el token y que el repo se llame DAM-almacen."
        fi
    else
        aviso "Saltado. Luego: git clone https://github.com/TU_USUARIO/DAM-almacen.git ~/DAM-almacen"
    fi
fi

# 7. Comprobación final ----------------------------------------------------
paso "Compruebo que todo funciona"
uv run dam --config "$CONFIG" validar

printf '\nListo. Prueba:  dam --help   y   dam status\n'
