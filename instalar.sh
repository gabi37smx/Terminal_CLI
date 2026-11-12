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
# Tu terminal (bash o zsh) y su fichero de arranque: aquí van el PATH, el TAB y DAM_ALMACEN
case "$(basename "${SHELL:-}")" in
    bash) TERMINAL=bash; RC="$HOME/.bashrc" ;;
    zsh)  TERMINAL=zsh;  RC="$HOME/.zshrc" ;;
    *)    TERMINAL="" ;;
esac
# Ojo: arriba añadí ~/.local/bin al PATH de ESTE script, así que «uv tool update-shell» (y el
# instalador de uv) creen que ya está y no lo apuntan en ningún sitio. Pasó en un Linux de clase
# recién instalado: «dam» no se encontraba ni abriendo otra terminal. Por eso miro el PATH que
# tenías al empezar y lo apunto yo en tu fichero de arranque.
MARCA_PATH="# Para que la terminal encuentre dam (lo añadió instalar.sh)"
case ":$PATH_ORIGINAL:" in
    *":$CARPETA_BIN:"*) ok "Tu terminal ya encuentra los comandos de $CARPETA_BIN" ;;
    *)
        if [ -n "$TERMINAL" ]; then
            if ! grep -qF "$MARCA_PATH" "$RC" 2>/dev/null; then
                {
                    echo ""
                    echo "$MARCA_PATH"
                    echo "case \":\$PATH:\" in *\":$CARPETA_BIN:\"*) ;; *) export PATH=\"$CARPETA_BIN:\$PATH\" ;; esac"
                } >> "$RC"
            fi
            ok "Añadido $CARPETA_BIN al PATH en $RC"
            aviso "Al terminar, cierra esta terminal y abre otra (o en esta misma:  source $RC )."
        else
            # Otra terminal: que lo haga uv, pero con el PATH de antes para que no se lo salte
            PATH="$PATH_ORIGINAL" "$(command -v uv)" tool update-shell \
                || aviso "Añade tú $CARPETA_BIN al PATH de tu terminal."
            aviso "Al terminar, cierra esta terminal y abre otra para que «dam» funcione."
        fi
        ;;
esac

# 4. Dónde van tus acciones (las configura el paso 6b, con el almacén ya clonado)
CONFIG="$HOME/.config/dam/acciones.json"

# 4b. Autocompletado con TAB -----------------------------------------------
# No uso «dam --install-completion»: miraría la terminal de ESTE script (bash), y en macOS la
# tuya es zsh. Así se mira la tuya ($SHELL) y se puede repetir sin duplicar nada.
paso "Activo el autocompletado con TAB"
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
# Un correo sin @ (por ejemplo el usuario de GitHub) no vale: GitHub no te reconoce los commits
correo_actual="$(git config --global user.email || true)"
case "$correo_actual" in
    *@*) ;;
    *)
        if [ -n "$correo_actual" ]; then
            aviso "Tu correo de git («$correo_actual») no es un correo: le falta la @."
        fi
        echo "    Pon el de tu cuenta de GitHub. Si no quieres que se vea, usa el …@users.noreply.github.com"
        echo "    que sale en https://github.com/settings/emails"
        correo=""
        read -rp "    Tu correo de GitHub: " correo || true
        case "$correo" in
            *@*) git config --global user.email "$correo" ;;
            "")  ;;
            *)   aviso "«$correo» no es un correo (falta la @): no lo guardo." ;;
        esac
        ;;
esac
correo_actual="$(git config --global user.email || true)"
if [ -n "$(git config --global user.name || true)" ] && [[ "$correo_actual" == *@* ]]; then
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
ALMACEN="${DAM_ALMACEN:-}"
if [ -z "$ALMACEN" ]; then
    # ¿Ya está clonado en otro sitio (por ejemplo en ~/Documents o ~/Documentos)? Se busca hasta
    # 3 niveles un repo git cuyo remoto sea DAM-almacen, se llame como se llame la carpeta.
    encontrados=()
    while IFS= read -r git_dir; do
        carpeta="$(dirname "$git_dir")"
        if git -C "$carpeta" remote get-url origin 2>/dev/null | grep -qi "/dam-almacen"; then
            encontrados+=("$carpeta")
        fi
    done < <(find "$HOME" -maxdepth 4 \( -path "$HOME/.*" -o -name node_modules \) -prune \
                  -o -type d -name .git -print 2>/dev/null | sort || true)
    if [ "${#encontrados[@]}" -gt 0 ]; then
        ALMACEN="${encontrados[0]}"
        if [ "${#encontrados[@]}" -gt 1 ]; then
            aviso "Hay ${#encontrados[@]} copias del almacén: ${encontrados[*]}"
            aviso "Uso la primera. Para usar otra: export DAM_ALMACEN=RUTA en $RC"
        fi
        if [ "$ALMACEN" != "$HOME/DAM-almacen" ] && [ -n "${RC:-}" ]; then
            # dam lo busca en ~/DAM-almacen (acciones.json): si está en otro sitio, se lo digo con DAM_ALMACEN
            if ! grep -q "DAM_ALMACEN=" "$RC" 2>/dev/null; then
                printf '\n# Dónde está el almacén de apuntes (lo añadió instalar.sh)\nexport DAM_ALMACEN="%s"\n' "$ALMACEN" >> "$RC"
                ok "Guardado DAM_ALMACEN=$ALMACEN en $RC"
            elif ! grep -qF "DAM_ALMACEN=\"$ALMACEN\"" "$RC"; then
                aviso "En $RC ya hay otro DAM_ALMACEN: revísalo a mano (aquí lo he encontrado en $ALMACEN)."
            fi
        fi
        export DAM_ALMACEN="$ALMACEN"
    else
        ALMACEN="$HOME/DAM-almacen"
    fi
fi
if [ -d "$ALMACEN/.git" ]; then
    ok "Ya está clonado en $ALMACEN"
elif [ -e "$ALMACEN" ]; then
    aviso "$ALMACEN existe pero no es un repositorio git: no lo toco."
else
    usuario=""
    echo "    Tu usuario de GitHub es el de github.com/TU_USUARIO (no el de este ordenador)."
    read -rp "    Usuario de GitHub para clonar DAM-almacen (Enter para saltar): " usuario || true
    if [ -n "$usuario" ]; then
        echo "    Si el repo es privado, git te pedirá dos cosas:"
        echo "      Username → $usuario"
        echo "      Password → un token (la contraseña normal no vale). Créalo en"
        echo "                 https://github.com/settings/tokens con permiso «repo». Al pegarlo no se ve: es normal."
        if git clone "https://github.com/$usuario/DAM-almacen.git" "$ALMACEN"; then
            ok "Clonado en $ALMACEN"
        else
            aviso "No he podido clonarlo. Si pone «Invalid username or token»: en Password pegaste la contraseña"
            aviso "o un token caducado; el token empieza por ghp_ o github_pat_ (cópialo entero al crearlo)."
            aviso "Si pone «Repository not found»: el usuario está mal, el token no vale"
            aviso "o el repo no se llama DAM-almacen (GitHub esconde así los repos privados)."
            aviso "Puedes repetir  bash instalar.sh : lo que ya está hecho se salta."
        fi
    else
        aviso "Saltado. Luego: git clone https://github.com/TU_USUARIO/DAM-almacen.git ~/DAM-almacen"
    fi
fi

# 6b. Tu ciclo y tus asignaturas --------------------------------------------
# Como adduser en Linux: pregunta qué estudias y deja acciones.json a tu medida. Va después del
# almacén para poder crear en él las carpetas de tus asignaturas.
paso "Tu ciclo y tus asignaturas (dam configurar)"
configurar() { uv run dam --config "$CONFIG" configurar --plantilla acciones.json; }
if [ ! -f "$CONFIG" ]; then
    if ! configurar; then
        mkdir -p "$(dirname "$CONFIG")"
        cp acciones.json "$CONFIG"
        aviso "No se ha configurado: he copiado las acciones de 1º de DAM a $CONFIG."
        aviso "Cuando quieras, elige tu ciclo con:  dam configurar"
    fi
elif cmp -s acciones.json "$CONFIG"; then
    ok "Ya tienes $CONFIG y está al día (para cambiar de ciclo o de curso: dam configurar)"
else
    # O ya elegiste tus asignaturas o es de una instalación vieja (le faltarían las acciones nuevas)
    aviso "Tu $CONFIG no es igual que la del repo: ya elegiste tus asignaturas o es de una instalación vieja."
    respuesta=""
    read -rp "    ¿La rehago con las acciones del repo? Te propongo lo que elegiste y guardo una copia [s/N]: " respuesta || true
    if [ "$respuesta" = "s" ] || [ "$respuesta" = "S" ]; then
        configurar || aviso "No he cambiado nada: dam seguirá usando la tuya."
    else
        aviso "No la toco: dam seguirá usando la tuya."
    fi
fi

# 6c. IA para las acciones que la usan --------------------------------------
# Modelos gratis con OpenCode: funcionan en casa y no piden clave (ADR-0004). Se instala la misma
# versión de OpenCode que usamos en clase: con ella está probado el agente de dam.
paso "IA para las acciones que la usan (dam configurar-ia)"
VERSION_OPENCODE="1.18.35"
# En WSL se ven los programas de Windows (/mnt/c/...): ese npm instalaría OpenCode en Windows y
# ese opencode no entiende las rutas de Linux. Solo cuentan los de Linux.
de_linux() {
    local ruta
    ruta="$(command -v "$1" 2>/dev/null)" || return 1
    case "$ruta" in /mnt/*) return 1 ;; esac
}
if [ -f "$HOME/.config/dam/ia.json" ]; then
    ok "Ya elegiste el modelo (para cambiarlo: dam configurar-ia)"
else
    if ! de_linux opencode; then
        respuesta=""
        read -rp "    Para usar modelos de IA gratis hace falta OpenCode. ¿Lo instalo? [S/n]: " respuesta || true
        if [ "$respuesta" != "n" ] && [ "$respuesta" != "N" ]; then
            if de_linux npm; then
                npm install -g "opencode-ai@$VERSION_OPENCODE" \
                    || aviso "npm no ha podido instalarlo. Si pone EACCES: sudo npm install -g opencode-ai@$VERSION_OPENCODE"
            else
                aviso "Para instalar OpenCode necesito npm (Node.js): Ubuntu/Debian: sudo apt install npm · macOS: brew install node"
                aviso "Después, repite  bash instalar.sh : lo que ya está hecho se salta."
            fi
        fi
    fi
    if de_linux opencode; then
        uv run dam configurar-ia || aviso "Sin IA de momento. Cuando quieras: dam configurar-ia"
    else
        aviso "Sin OpenCode, las acciones con IA usan el servidor del centro (o elige con: dam configurar-ia)."
    fi
fi

# 7. Comprobación final ----------------------------------------------------
paso "Compruebo que todo funciona"
uv run dam --config "$CONFIG" validar

printf '\nListo. Prueba:  dam --help   y   dam status\n'
