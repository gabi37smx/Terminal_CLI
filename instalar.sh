#!/usr/bin/env bash
# Instala y configura mochila en Linux o macOS.
# Uso (desde la carpeta del repositorio clonado):  bash instalar.sh
# Se puede ejecutar todas las veces que quieras: lo que ya está hecho se salta.
set -euo pipefail

cd "$(dirname "$0")"   # trabaja siempre desde la carpeta del repositorio
PATH_ORIGINAL="$PATH"  # para saber después si tu terminal ya encuentra «mochila»

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

# 3. Dependencias y comando mochila --------------------------------------------
paso "Instalo las dependencias (uv descarga Python 3.12 si hace falta)"
uv sync

paso "Instalo el comando mochila para todo el sistema"
uv tool install --editable . --force
CARPETA_BIN="$(uv tool dir --bin)"
# Tu terminal (bash o zsh) y su fichero de arranque: aquí van el PATH, el TAB y MOCHILA_ALMACEN
case "$(basename "${SHELL:-}")" in
    bash) TERMINAL=bash; RC="$HOME/.bashrc" ;;
    zsh)  TERMINAL=zsh;  RC="$HOME/.zshrc" ;;
    *)    TERMINAL="" ;;
esac
# Ojo: arriba añadí ~/.local/bin al PATH de ESTE script, así que «uv tool update-shell» (y el
# instalador de uv) creen que ya está y no lo apuntan en ningún sitio. Pasó en un Linux de clase
# recién instalado: «mochila» no se encontraba ni abriendo otra terminal. Por eso miro el PATH que
# tenías al empezar y lo apunto yo en tu fichero de arranque.
MARCA_PATH="# Para que la terminal encuentre mochila (lo añadió instalar.sh)"
# Con bash o zsh lo apunto SIEMPRE (una vez): un «export PATH=...» escrito a mano solo dura en esa
# terminal, y si mirara solo el PATH de ahora me lo saltaría y en la siguiente terminal no estaría.
if [ -n "$TERMINAL" ]; then
    # (la marca vieja es de cuando se llamaba dam: ese PATH sigue valiendo, no lo repito)
    if grep -qF -e "$MARCA_PATH" -e "# Para que la terminal encuentre dam (lo añadió instalar.sh)" "$RC" 2>/dev/null; then
        ok "$RC ya pone $CARPETA_BIN en el PATH"
    else
        {
            echo ""
            echo "$MARCA_PATH"
            echo "case \":\$PATH:\" in *\":$CARPETA_BIN:\"*) ;; *) export PATH=\"$CARPETA_BIN:\$PATH\" ;; esac"
        } >> "$RC"
        ok "Añadido $CARPETA_BIN al PATH en $RC"
    fi
    case ":$PATH_ORIGINAL:" in
        *":$CARPETA_BIN:"*) ;;
        *) aviso "Al terminar, cierra esta terminal y abre otra (o en esta misma:  source $RC )." ;;
    esac
else
    case ":$PATH_ORIGINAL:" in
        *":$CARPETA_BIN:"*) ok "Tu terminal ya encuentra los comandos de $CARPETA_BIN" ;;
        *)
            # Otra terminal: que lo haga uv, pero con el PATH de antes para que no se lo salte
            PATH="$PATH_ORIGINAL" "$(command -v uv)" tool update-shell                 || aviso "Añade tú $CARPETA_BIN al PATH de tu terminal."
            aviso "Al terminar, cierra esta terminal y abre otra para que «mochila» funcione."
            ;;
    esac
fi

# 4. Dónde van tus acciones (las configura el paso 6b, con el almacén ya clonado)
CONFIG="$HOME/.config/mochila/acciones.json"

# Antes se llamaba «dam»: lo que ya elegiste (acciones.json, ia.json) se copia a ~/.config/mochila.
# La carpeta vieja se queda como copia de seguridad; puedes borrarla cuando quieras.
if [ -d "$HOME/.config/dam" ] && [ ! -e "$(dirname "$CONFIG")" ]; then
    cp -R "$HOME/.config/dam" "$(dirname "$CONFIG")"
    rm -f "$(dirname "$CONFIG")"/completado.*
    ok "Lo que tenías de dam pasa a $(dirname "$CONFIG")"
fi
# Y en tu fichero de arranque, las líneas del TAB de dam (cargaban un script que ya no se usa)
if [ -n "${RC:-}" ] && grep -qF ".config/dam/completado." "$RC" 2>/dev/null; then
    grep -vF -e "# Autocompletado de dam (lo añadió instalar.sh)" -e ".config/dam/completado." "$RC" > "$RC.mochila-tmp" \
        && cat "$RC.mochila-tmp" > "$RC" && rm -f "$RC.mochila-tmp"
    ok "Quitado de $RC el TAB de dam"
fi

# 4b. Autocompletado con TAB -----------------------------------------------
# No uso «mochila --install-completion»: miraría la terminal de ESTE script (bash), y en macOS la
# tuya es zsh. Así se mira la tuya ($SHELL) y se puede repetir sin duplicar nada.
paso "Activo el autocompletado con TAB"
if [ -z "$TERMINAL" ]; then
    aviso "Tu terminal (${SHELL:-desconocida}) no es bash ni zsh: actívalo a mano con  mochila --install-completion"
else
    SCRIPT_TAB="$HOME/.config/mochila/completado.$TERMINAL"
    mkdir -p "$(dirname "$SCRIPT_TAB")"
    # Con esta variable, mochila no ejecuta nada: solo escribe el script de autocompletado
    if _MOCHILA_COMPLETE="source_$TERMINAL" "$CARPETA_BIN/mochila" > "$SCRIPT_TAB"; then
        if ! grep -qF "$SCRIPT_TAB" "$RC" 2>/dev/null; then
            {
                echo ""
                echo "# Autocompletado de mochila (lo añadió instalar.sh)"
                if [ "$TERMINAL" = zsh ] && ! grep -q compinit "$RC" 2>/dev/null; then
                    echo "autoload -Uz compinit && compinit"
                fi
                echo "[ -f \"$SCRIPT_TAB\" ] && source \"$SCRIPT_TAB\""
            } >> "$RC"
        fi
        ok "TAB activado para $TERMINAL (en $RC). En una terminal nueva prueba: mochila ej<TAB>"
    else
        aviso "No he podido generar el autocompletado. Puedes probar a mano: mochila --install-completion"
    fi
fi

# 5. git: identidad y credenciales -----------------------------------------
paso "Preparo git para los commits de mochila sync"
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
# Solo se busca si ya lo tienes. Si no, se baja o se crea en el paso 6b, después de elegir el ciclo:
# se llama como tu ciclo (DAM-almacen, ASIR-almacen...) y mochila te ayuda a crearlo (ADR-0005).
paso "Almacén de apuntes"
ALMACEN="${MOCHILA_ALMACEN:-}"
if [ -n "$ALMACEN" ]; then
    ok "Uso el de MOCHILA_ALMACEN: $ALMACEN"
else
    # ¿Ya está clonado (por ejemplo en ~/Documents o ~/Documentos)? Se busca hasta 3 niveles un repo
    # git cuyo remoto sea CICLO-almacen, se llame como se llame la carpeta.
    encontrados=()
    while IFS= read -r git_dir; do
        carpeta="$(dirname "$git_dir")"
        if git -C "$carpeta" remote get-url origin 2>/dev/null | grep -qiE "/(smx|dam|daw|asir|apuntes)-almacen(\.git)?/?$"; then
            encontrados+=("$carpeta")
        fi
    done < <(find "$HOME" -maxdepth 4 \( -path "$HOME/.*" -o -name node_modules \) -prune                   -o -type d -name .git -print 2>/dev/null | sort || true)
    if [ "${#encontrados[@]}" -gt 0 ]; then
        ALMACEN="${encontrados[0]}"
        ok "Ya lo tienes en $ALMACEN"
        if [ "${#encontrados[@]}" -gt 1 ]; then
            aviso "Hay ${#encontrados[@]} copias del almacén: ${encontrados[*]}"
            aviso "Uso la primera. Para usar otra: export MOCHILA_ALMACEN=RUTA en $RC"
        fi
        # mochila lo busca en ~/CICLO-almacen (acciones.json): si está en otro sitio, se lo digo con MOCHILA_ALMACEN
        en_su_sitio=0
        case "$ALMACEN" in
            "$HOME"/SMX-almacen|"$HOME"/DAM-almacen|"$HOME"/DAW-almacen|"$HOME"/ASIR-almacen|"$HOME"/APUNTES-almacen) en_su_sitio=1 ;;
        esac
        if [ "$en_su_sitio" = 0 ] && [ -n "${RC:-}" ]; then
            if ! grep -q "MOCHILA_ALMACEN=" "$RC" 2>/dev/null; then
                printf '\n# Dónde está el almacén de apuntes (lo añadió instalar.sh)\nexport MOCHILA_ALMACEN="%s"\n' "$ALMACEN" >> "$RC"
                ok "Guardado MOCHILA_ALMACEN=$ALMACEN en $RC"
            elif ! grep -qF "MOCHILA_ALMACEN=\"$ALMACEN\"" "$RC"; then
                aviso "En $RC ya hay otro MOCHILA_ALMACEN: revísalo a mano (aquí lo he encontrado en $ALMACEN)."
            fi
        fi
        export MOCHILA_ALMACEN="$ALMACEN"
    else
        echo "    Aún no lo tienes en este equipo: después de elegir tu ciclo te ayudo a bajarlo o a crearlo."
    fi
fi

# 6b. Tu ciclo, tus asignaturas y tu almacén ---------------------------------
# Como adduser en Linux: pregunta qué estudias y deja acciones.json a tu medida. Al acabar ofrece
# preparar el almacén (se llama como tu ciclo). Si no se configura, se prepara igual con crear-almacen.
paso "Tu ciclo y tus asignaturas (mochila configurar)"
configurar() { uv run mochila --config "$CONFIG" configurar --plantilla acciones.json; }
configurado=0
if [ ! -f "$CONFIG" ]; then
    if configurar; then
        configurado=1
    else
        mkdir -p "$(dirname "$CONFIG")"
        cp acciones.json "$CONFIG"
        aviso "No se ha configurado: he copiado las acciones de 1º de DAM a $CONFIG."
        aviso "Cuando quieras, elige tu ciclo con:  mochila configurar"
    fi
elif cmp -s acciones.json "$CONFIG"; then
    ok "Ya tienes $CONFIG y está al día (para cambiar de ciclo o de curso: mochila configurar)"
else
    # O ya elegiste tus asignaturas o es de una instalación vieja (le faltarían las acciones nuevas)
    aviso "Tu $CONFIG no es igual que la del repo: ya elegiste tus asignaturas o es de una instalación vieja."
    respuesta=""
    # Enter es «sí»: te propone lo que ya elegiste y guarda copia, y así te llegan las acciones nuevas
    read -rp "    ¿La rehago con las acciones del repo? Te propongo lo que elegiste y guardo una copia [S/n]: " respuesta || true
    case "$respuesta" in n|N|no|No|NO) respuesta=n ;; *) respuesta=s ;; esac
    if [ "$respuesta" = "s" ]; then
        if configurar; then configurado=1; else aviso "No he cambiado nada: mochila seguirá usando la tuya."; fi
    else
        aviso "No la toco: mochila seguirá usando la tuya."
    fi
fi
if [ "$configurado" = 0 ]; then
    paso "Tu almacén de apuntes (mochila crear-almacen)"
    uv run mochila --config "$CONFIG" crear-almacen || aviso "Sin almacén de momento. Cuando quieras:  mochila crear-almacen"
fi

# 6c. IA para las acciones que la usan --------------------------------------
# Modelos gratis con OpenCode: funcionan en casa y no piden clave (ADR-0004). Se instala la misma
# versión de OpenCode que usamos en clase: con ella está probado el agente de mochila.
paso "IA para las acciones que la usan (mochila configurar-ia)"
VERSION_OPENCODE="1.18.35"
# En WSL se ven los programas de Windows (/mnt/c/...): ese npm instalaría OpenCode en Windows y
# ese opencode no entiende las rutas de Linux. Solo cuentan los de Linux.
de_linux() {
    local ruta
    ruta="$(command -v "$1" 2>/dev/null)" || return 1
    case "$ruta" in /mnt/*) return 1 ;; esac
}
if [ -f "$HOME/.config/mochila/ia.json" ]; then
    ok "Ya elegiste el modelo (para cambiarlo: mochila configurar-ia)"
else
    if ! de_linux opencode; then
        respuesta=""
        read -rp "    Para usar modelos de IA gratis hace falta OpenCode. ¿Lo instalo? [S/n]: " respuesta || true
        if [ "$respuesta" != "n" ] && [ "$respuesta" != "N" ]; then
            if de_linux npm; then
                # En una máquina virtual, Node.js puede cerrarse a la primera (issue #53): otra vez y ya
                npm install -g "opencode-ai@$VERSION_OPENCODE" \
                    || { aviso "npm se ha cerrado sin instalar OpenCode. Lo intento otra vez..."
                         npm install -g "opencode-ai@$VERSION_OPENCODE"; } \
                    || aviso "npm no ha podido instalarlo. Si pone EACCES: sudo npm install -g opencode-ai@$VERSION_OPENCODE"
            else
                aviso "Para instalar OpenCode necesito npm (Node.js): Ubuntu/Debian: sudo apt install npm · macOS: brew install node"
                aviso "Después, repite  bash instalar.sh : lo que ya está hecho se salta."
            fi
        fi
    fi
    if de_linux opencode; then
        uv run mochila configurar-ia || aviso "Sin IA de momento. Cuando quieras: mochila configurar-ia"
    else
        aviso "Sin OpenCode no hay modelos gratis: las acciones con IA no funcionarán hasta que elijas uno."
        SIN_IA=1
    fi
fi

# 7. Comprobación final ----------------------------------------------------
paso "Compruebo que todo funciona"
uv run mochila --config "$CONFIG" validar

printf '\nListo. Prueba:  mochila --help   y   mochila status\n'
if [ "${SIN_IA:-0}" = 1 ]; then
    # Issue #53: si npm falla, el aviso sale en medio y la instalación parece perfecta
    printf '\n'
    aviso "Ojo: la IA NO está lista (no se ha instalado OpenCode). Para tenerla, una vez:"
    aviso "    npm install -g opencode-ai@$VERSION_OPENCODE"
    aviso "y después, en una terminal nueva:  mochila configurar-ia"
fi
