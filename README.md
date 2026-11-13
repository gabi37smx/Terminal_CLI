# dam (proyecto `tareas`)

Mi herramienta de línea de órdenes para automatizar tareas repetitivas con ficheros y mantener
mis apuntes de 1º DAM sincronizados entre el PC de clase, el de casa y el USB.

> Nota: en la spec v0 el comando se llamaba `tareas`; ahora se llama **`dam`** (el paquete
> Python sigue siendo `tareas`). Desde la 1.0.0 se instalan los dos nombres para el mismo programa:
> `tareas version` → `tareas 1.0.0` y `dam version` → `dam 1.0.0`. Cambios en [CHANGELOG.md](CHANGELOG.md).

## Spec (versión 0 · 26/10/2026)

1. **Problema:** cada semana pierdo tiempo ordenando Descargas a mano, limpiando ficheros temporales y convirtiendo fotos a WebP para que pesen menos.
2. **Para quién:** para mí y para mis compañeros de 1º DAM.
3. **Cómo se usa:** `tareas ORDEN [CARPETA] [opciones]` desde cualquier terminal.
4. **Órdenes de la semana 1:** `tareas --help`, `tareas version`, `tareas listar [CARPETA]`.
5. **Órdenes previstas:** `tareas acciones`, `tareas validar`, `tareas ejecutar NOMBRE --simular`.
6. **Mis 3 acciones (borrador):** organizar Descargas por tipo de fichero, borrar temporales de más de 30 días, convertir imágenes a WebP.
7. **Nunca hará:** borrar sin preguntar ni tocar ficheros fuera de la carpeta que le indique.
8. **Plataformas:** Linux primero; también Windows y macOS.
9. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida.
10. **Instalación:** `uv tool install --editable .` (lo completo en la semana 4). *Hecho: ahora es una sola orden, `uv tool install git+https://github.com/gabi37smx/Terminal_CLI`, o `bash instalar.sh`, que lo deja todo listo (ver [Instalación](#instalación)).*

## Instalación

### Antes de empezar: git, curl y uv

Un sistema recién instalado puede no traer ni `git` ni `curl` (le pasa a Ubuntu 24.04). Comprueba
con `git --version` y `curl --version`, e instala lo que falte:

| Sistema | Orden |
|---|---|
| Ubuntu, Debian, Mint | `sudo apt update && sudo apt install -y git curl` |
| Fedora | `sudo dnf install -y git curl` |
| macOS | `xcode-select --install` (trae git; curl ya viene) |
| Windows | `winget install --id Git.Git -e` (curl ya viene en Windows 10 y 11). Sin winget (Windows LTSC o sin Microsoft Store): descárgalo de https://git-scm.com/download/win y deja las opciones que trae |

Después, **uv** con su instalador oficial. En Ubuntu, si escribes `uv` sin tenerlo, te sugiere
`sudo snap install astral-uv`: **no lo uses**, el de snap no deja bien los comandos en `~/.local/bin`.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # Linux y macOS
source $HOME/.local/bin/env                         # o abre otra terminal
```

En Windows (PowerShell): `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`.
Si usas el script `instalar.sh` / `instalar.cmd` de abajo, uv lo instala él; git sí lo necesitas antes.

### En una orden (si ya tienes uv)

```bash
uv tool install git+https://github.com/gabi37smx/Terminal_CLI@v1.0.1
dam --help          # o «tareas --help»: es el mismo programa
```

Así instalas solo el comando: `dam` buscará tus acciones en `./acciones.json` o en
`~/.config/dam/acciones.json`, y sin clonar no tienes ninguno. Baja el de ejemplo (mis 9 acciones)
y cámbialo a tu gusto siguiendo el [esquema](#esquema-de-accionesjson):

```bash
mkdir -p ~/.config/dam
curl -fsSL https://raw.githubusercontent.com/gabi37smx/Terminal_CLI/main/acciones.json -o ~/.config/dam/acciones.json
dam validar && dam acciones
```

En Windows (PowerShell), lo mismo:

```powershell
New-Item -ItemType Directory -Force "$HOME\.config\dam" | Out-Null
curl.exe -fsSL https://raw.githubusercontent.com/gabi37smx/Terminal_CLI/main/acciones.json -o "$HOME\.config\dam\acciones.json"
dam validar; dam acciones
```

Todas las acciones del ejemplo trabajan en `~/pruebas-tareas`, así que no tocan nada tuyo hasta
que cambies las rutas; aun así, prueba siempre primero con `--simular`. Para dejarlo todo listo (uv, acciones, TAB, git y almacén), usa el script de abajo.

### Lo rápido: un script que lo hace todo

Solo necesitas git. Clona el repositorio y ejecuta el instalador de tu sistema:

```bash
git clone https://github.com/gabi37smx/Terminal_CLI.git
cd Terminal_CLI
bash instalar.sh          # Linux y macOS
```

En Windows: doble clic en `instalar.cmd` (o `powershell -ExecutionPolicy Bypass -File instalar.ps1`).

El script instala uv si no está (y uv baja Python 3.12), instala el comando `dam`, te pide nombre y
correo para git si faltan y, como `adduser` en Linux, **te pregunta qué estudias** (`dam configurar`):
con tu ciclo y curso deja `~/.config/dam/acciones.json` con tus asignaturas. Después **prepara tu
almacén de apuntes** (`dam crear-almacen`): si ya lo tienes en GitHub lo baja, y si no, te ayuda a
crearlo (mira [Tu almacén de apuntes](#tu-almacén-de-apuntes-si-aún-no-lo-tienes)). Por último, **te pregunta con qué IA
quieres trabajar** (`dam configurar-ia`): si eliges los modelos gratis, instala OpenCode si no lo tienes
y lo deja configurado (mira [IA gratis con OpenCode](#ia-gratis-con-opencode)). Se puede repetir sin
miedo: lo que ya está hecho se salta.
Al terminar, abre una terminal nueva. Si git te pide contraseña al clonar o al hacer `sync`, pega un
**token de GitHub**, porque la contraseña normal no vale.

**Si ya lo tenías instalado y haces `git pull`, vuelve a pasar el instalador.** Con `--editable` el código
nuevo se usa solo, pero las dependencias nuevas no se instalan (en la semana 3 llegaron `httpx` y
`python-dotenv`): sin reinstalar, `dam` falla al arrancar con `ModuleNotFoundError`.

### A mano

Necesitas [uv](https://docs.astral.sh/uv/) y git.

```bash
git clone https://github.com/gabi37smx/Terminal_CLI.git
cd Terminal_CLI
uv sync
uv run dam --help                 # probar sin instalar
uv tool install --editable .          # instalar el comando `dam` en todo el sistema
```

Para instalarlo sin clonar (otra persona, otro equipo):

```bash
uv tool install git+https://github.com/gabi37smx/Terminal_CLI
```

En Windows (PowerShell) es igual. Si `dam` no se encuentra tras instalar: `uv tool update-shell` y abre otra terminal.

### Autocompletado con TAB

El instalador lo deja activado en bash, zsh y PowerShell. En una terminal nueva:

```bash
dam ej<TAB>             # → dam ejecutar
dam ejecutar co<TAB>    # → convertir-webp, copiar-entregas (las acciones de tu acciones.json)
dam sync pr<TAB>        # → programacion, proyecto (las carpetas de asignaturas/ del almacén)
```

El script se guarda en `~/.config/dam/completado.*` y se carga con una sola línea en tu
`~/.bashrc`, `~/.zshrc` o perfil de PowerShell. Repetir el instalador no la duplica.
En Windows necesita que PowerShell pueda cargar scripts: si el instalador avisa, ejecuta una vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. No uses `dam --install-completion` en
Windows: cambia la política a `Unrestricted` y repite el script en el perfil cada vez.

### Desinstalación

Primero quita el hook de cada repo donde lo instalaste y después el programa:

```bash
dam instalar-hook --quitar      # en cada repo con el hook (solo quita el de dam)
uv tool uninstall tareas        # quita «dam» y «tareas»
rm -rf ~/.config/dam            # tus acciones y el script del TAB (guarda antes acciones.json si lo quieres)
```

Después, borra a mano en `~/.bashrc` o `~/.zshrc` las dos líneas que empiezan por
`# Autocompletado de dam (lo añadió instalar.sh)`.

En Windows (PowerShell):

```powershell
dam instalar-hook --quitar
uv tool uninstall tareas
Remove-Item -Recurse -Force "$HOME\.config\dam"
[Environment]::SetEnvironmentVariable('DAM_ALMACEN', $null, 'User')   # si el instalador la guardó
notepad $PROFILE.CurrentUserAllHosts    # borra la línea «# autocompletado de dam»
```

Si definiste `CENTRO_IA_URL`, `CENTRO_IA_KEY`, `CENTRO_IA_CA` o `CENTRO_IA_MODELO` como variables
de tu usuario, quítalas igual que `DAM_ALMACEN`. Si el instalador te puso OpenCode y ya no lo quieres:
`npm uninstall -g opencode-ai`. Si `dam configurar-ia` cambió tu `~/.config/opencode/opencode.json`,
al lado está la copia de antes (`opencode.json.antes-FECHA`). La carpeta del repo y tu almacén (`CICLO-almacen`) no se tocan:
bórralas tú si ya no las quieres (antes, `dam status` para no perder nada sin subir).

## Órdenes

| Orden | Qué hace |
|---|---|
| `dam version` | Muestra la versión (`tareas version` hace lo mismo). |
| `dam configurar [--ciclo C] [--curso N] [--quitar X] [--nueva NOMBRE=PALABRAS] [--simular] [--si]` | Pregunta tu ciclo (SMX, DAM, DAW, ASIR/ASIX u otro) y curso, y pone tus asignaturas en `acciones.json`. Mira [Tu ciclo y tus asignaturas](#tu-ciclo-y-tus-asignaturas-dam-configurar). |
| `dam listar [CARPETA]` | Tabla con nombre, tipo, tamaño y fecha. |
| `dam validar` | Comprueba `acciones.json`. Sale con 3 si está mal. |
| `dam acciones` | Lista las acciones configuradas. |
| `dam configurar-ia [--proveedor opencode\|centro] [--modelo M] [--si]` | Elige el modelo de las acciones con IA: los gratis de OpenCode (en casa, sin clave) o el servidor del centro. Mira [IA gratis con OpenCode](#ia-gratis-con-opencode). |
| `dam comprobar-ia` | ¿Responde el modelo que usa `dam`? Enseña cuál es (nunca la clave) y hace una pregunta mínima. Sale con 4 si no responde: sin clave, red, certificado u `opencode`. |
| `dam ejecutar NOMBRE [CARPETA\|FICHERO] [--simular] [--si]` | Ejecuta una acción sobre una carpeta o un solo fichero (si cumple el filtro de la acción). `--simular` enseña qué haría sin tocar nada; borrar pide confirmación salvo `--si`. `ordenar` (con `al_almacen`) mete los apuntes en el almacén, en la carpeta de su unidad si ya existe, y luego ofrece `dam sync`; con `por_tipo`, lo demás va a `~/Datos/POR-TIPO`. Nunca mueve `desktop.ini`, temporales ni descargas a medias. |
| `dam crear-almacen` | Deja listo tu almacén de apuntes: si ya lo tienes en GitHub lo baja; si no, abre GitHub con el nombre de tu ciclo y «privado» ya puestos. Luego crea las carpetas de tus asignaturas y, si es nuevo, las sube. |
| `dam status [ASIGNATURA]` | Qué has cambiado en local y qué hay nuevo en GitHub. No modifica nada. |
| `dam sync [ASIGNATURA] [MENSAJE] [-m TEXTO] [--integrar] [--simular]` | Sincroniza el almacén con GitHub de forma segura. |
| `dam scan-secrets [RUTA] [--staged] [--historial] [--alta]` | Busca claves, tokens y contraseñas expuestas. Sale con 1 si encuentra algo. |
| `dam instalar-hook [REPO] [--quitar] [--forzar]` | Revisa claves automáticamente en cada `git commit`. |
| `dam doctor [CARPETA]` | Revisa que un proyecto esté sano: git, `.env` ignorado, `.env.example` al día, README, secretos, tests y CI. |
| `dam pendientes [CARPETA] [--quien NOMBRE] [--resumen]` | Cuenta las etiquetas `[Verificado]`, `[Hipótesis]` y `[Pendiente]` de la documentación y resume el registro `pendientes.md` por persona. |
| `dam entregar [CARPETA] [--destino D] [--nombre N] [--simular]` | Empaqueta un proyecto en un `.zip` limpio (sin `.env`, claves ni `node_modules`); no lo crea si hay un secreto dentro. |
| `dam inventario [CARPETA] [--guardar INFORME.md] [--top N]` | Inventario de una carpeta antes de organizarla: tamaño por carpeta, tipos, repos (y si tienen remoto), instaladores, basura, `node_modules`/`.venv` y ficheros de más de 100 MB. Solo lee. |
| `dam duplicados [CARPETA] [--guardar INFORME.md] [--top N]` | Ficheros repetidos (por contenido, SHA-256) y carpetas que son copia de otra; marca las copias que están en un repo. No borra nada. |
| `dam readme [CARPETA] [--niveles N] [--simular] [--si]` | Pone en cada carpeta un README.md cuyo apartado «Qué hay dentro» es una tabla: subcarpetas (tamaño y la primera frase de su README) y archivos (tamaño y tipo). No toca lo que escribes encima, ni los README sin ese apartado, ni repos o proyectos de código. Pregunta s/N antes de escribir. |
| `dam test-links [FUENTE] [--sin-externos] [--timeout S]` | Busca enlaces rotos en una web (carpeta, `.html` o URL). |
| `dam check-headers URL [--timeout S]` | Revisa las cabeceras de seguridad de una web o API. |

Opción global: `dam --config RUTA ORDEN` usa otro `acciones.json`. Por defecto busca
`./acciones.json` y después `~/.config/dam/acciones.json`.

**Códigos de salida:** 0 bien · 1 fallo al ejecutar (carpeta inexistente, permiso denegado, sync pendiente, claves, enlaces rotos o cabeceras básicas que faltan...) · 2 error de uso (lo pone Typer) · 3 configuración inválida · 4 sin IA (sin clave, sin red o el servidor no responde: las acciones sin IA siguen funcionando).

`dam` (o `dam -h` o `dam help`) muestra el manual completo con todos los comandos, opciones y ejemplos; `dam COMANDO -h` (o `dam help COMANDO`) explica uno.

## Esquema de acciones.json

```json
{ "version": 1,
  "almacen": { "ruta": "~/DAM-almacen" },
  "acciones": [ { "nombre": "...", "descripcion": "...", "tipo": "...", "...": "..." } ] }
```

| Campo | Obligatorio | Qué hace |
|---|---|---|
| `version` | sí (raíz) | Versión del esquema (ahora 1). |
| `acciones` | sí (raíz) | Lista de acciones; vacía = error. |
| `almacen.ruta` | no (raíz) | Carpeta del almacén git para `status` y `sync`. |
| `perfil` | no (raíz) | Lo escribe `dam configurar`: `{"ciclo": "dam", "cursos": [1]}`. Sirve para proponerte lo mismo la próxima vez. |
| `nombre` | sí | Único; minúsculas, números y guiones. Es lo que escribes en `dam ejecutar NOMBRE`. |
| `descripcion` | sí | Lo que muestra `dam acciones`. |
| `tipo` | sí | Sin IA: `mover`, `copiar`, `renombrar`, `borrar`, `ordenar` o `convertir`. Con IA: `resumir`, `renombrar-ia` o `clasificar`. |
| `origen` | no | Carpeta por defecto si no pasas CARPETA. `~` se expande en los tres sistemas. |
| `destino` | mover / copiar / clasificar | Dónde van los ficheros (se crea si no existe). En `resumir` es opcional: dónde se escribe cada `.resumen.md` (si no, junto al fichero). |
| `plantilla` | renombrar | Nombre nuevo: `{fecha:%Y-%m-%d}`, `{n:03}`, `{ext}`, `{nombre}`. |
| `filtro` | no (borrar: sí) | `extensiones`, `patron` (regex), `mas_antiguo_que_dias`, `mayor_que_mb`; se cumplen todos. |
| `carpetas` | ordenar | `{"asignatura": ["palabra clave", ...]}`. Se comparan palabras completas, sin tildes ni mayúsculas. |
| `por_extension` | no (ordenar) | `{".sql": "bases-datos"}`: pista extra por extensión. |
| `al_almacen` | no (ordenar) | `true` = cada fichero va a `asignaturas/ASIGNATURA` de tu almacén (no a una subcarpeta del origen). Si la asignatura no existe en el almacén, se salta. Al acabar pregunta si haces `dam sync` (con `--si` solo te lo recuerda). No se puede usar junto a `destino`. |
| `unidades` | no (ordenar) | Por defecto `true`: si el nombre (o, si no, el principio del contenido) dice de qué unidad es —«UD1», «UD-01», «Unitat 1», «Unidad 01», «Tema 1»— y la asignatura ya tiene esa carpeta (hasta 3 niveles: `1 Avaluacio/unitat 1`), va dentro. La carpeta nunca se crea. `false` = siempre a la carpeta de la asignatura. |
| `por_tipo` | no (ordenar) | `"~/Datos/POR-TIPO"`: lo que no es de ninguna asignatura va a `POR-TIPO/DOCUMENTOS`, `IMAGENES`, `VIDEO`, `AUDIO`, `COMPRIMIDOS`, `INSTALADORES`, `CODIGO`, `REDES` u `OTROS` (no se sube con `dam sync`). Sin esta clave, se queda donde está. |
| `calidad` | no (convertir) | 1-100, por defecto 80. |
| `confirmar` | no | `true` = pide confirmación antes de actuar (salvo `--si`). En las acciones con IA que cambian tus ficheros, ponlo siempre. |
| `instrucciones` | no (con IA) | Lo que le pides al modelo, en tu idioma. Es configuración: se cambia sin tocar Python. |
| `max_caracteres` | no (con IA) | Tope de texto que se manda al modelo: 500-50000, por defecto 12000. |
| `categorias` | clasificar | Las únicas respuestas válidas. Si el modelo dice otra cosa, el fichero va a `sin-clasificar`. Pon siempre una salida tipo `otros`. |

**Mis 9 acciones.** Sin IA (funcionan sin red): `ordenar` (reparte apuntes por asignatura y por unidad, mirando nombre, extensión y, si hace falta,
el contenido de los PDF y de los `.odt`, `.docx`, `.pptx`... con su cabecera y pie), `limpiar-temporales` (borra `.tmp/.bak/.part` de más de 30 días, con
confirmación), `convertir-webp` (JPEG/PNG a WebP sin tocar el original), `renombrar-capturas`
(capturas con fecha y número), `copiar-entregas` (copia entregas y prácticas a una carpeta de
seguridad) y `mover-zips` (mueve los `.zip` a la subcarpeta `comprimidos`).
Con IA: `resumir-tema` (resume cada tema en un `.md`, en castellano aunque el apunte esté en
valenciano), `nombrar-descargas` (pone nombre por su contenido a los `escaneo_0042.pdf` o
`documento (3).pdf`) y `clasificar-asignatura` (lee los apuntes que `ordenar` no sabe colocar y los
lleva a la carpeta de su asignatura).

Garantías: nunca sobrescribe (añade « (1)»), `--simular` no toca el disco ni crea carpetas y
la configuración se valida entera antes de mover un solo fichero.

Ojo con `mover` y `copiar`: si pasas una `CARPETA`, los ficheros se cogen de ahí, pero van al `destino`
fijo de `acciones.json`, aunque esté fuera de esa carpeta. Mira la tabla de `--simular` antes.

## Tu ciclo y tus asignaturas (dam configurar)

El `acciones.json` del repo es el mío (1º de DAM). Para que `ordenar` y `clasificar` sirvan a
cualquiera de la familia de Informática, `dam configurar` pregunta, igual que `adduser`:

```text
$ dam configurar
¿Qué estudias?
  1. SMX — Sistemas Microinformáticos y Redes (grado medio)
  2. DAM — Desarrollo de Aplicaciones Multiplataforma
  3. DAW — Desarrollo de Aplicaciones Web
  4. ASIR — Administración de Sistemas Informáticos en Red (ASIX en valenciano)
  5. Otro ciclo (escribes tú las asignaturas)
Número o nombre: 1
¿Qué curso? 1, 2 o 1,2 (los dos) [1]: 1
  (tabla con las 7 asignaturas de 1º de SMX y sus palabras clave)
¿Quieres quitar o añadir alguna? [s/N]:
¿Lo guardo en ~/.config/dam/acciones.json? [s/N]: s
¿Creo en tu almacén las carpetas que faltan (...)? [s/N]: s
```

- Cada ciclo sabe sus asignaturas de 1º y 2º, con palabras clave en castellano y en valenciano y
  las extensiones típicas (`.pkt` de Packet Tracer → redes, `.php` → servidor...). Están en
  `src/tareas/ciclos.py`: para añadir un ciclo no hay que tocar nada más.
- Puedes quitar asignaturas y añadir las tuyas (`--nueva "fol=fol,contrato,nomina"`): el nombre
  pasa a carpeta sin tildes ni espacios.
- Cambia `carpetas` y `por_extension` de `ordenar`, y `categorias` e `instrucciones` de
  `clasificar` (con `otros` al final). Si eliges las mismas asignaturas que ya había, esas acciones
  no se tocan. El resto de acciones se quedan igual.
- Valida todo antes de guardar y deja una copia del anterior (`acciones.json.antes-FECHA`).
- Las carpetas nuevas del almacén llevan un `.gitkeep` (git no sube carpetas vacías): súbelas con
  `dam sync`.
- La próxima vez te propone lo mismo (lo guarda en `perfil`). Sin preguntas:
  `dam configurar --ciclo asix --curso 2 --si`.

Dónde cae cada módulo común (inglés, itinerario para la empleabilidad, proyecto intermodular,
digitalización y sostenibilidad) depende del centro: si no coincide con el tuyo, quítalo o añádelo.

Por qué funciona así (vocabulario en `ciclos.py`, qué no se toca y qué palabras no se usan): [`docs/adr/0003-configurar-por-ciclo.md`](docs/adr/0003-configurar-por-ciclo.md).

## Almacén de apuntes (status y sync)

Son **dos repos distintos**:

| Repo | Qué es | De quién es |
|---|---|---|
| `Terminal_CLI` (este) | El programa `dam` | Mío. Tú solo lo clonas para instalarlo: aquí no subes nada. |
| `CICLO-almacen` | Tus apuntes, con una carpeta por asignatura (`asignaturas/programacion/`...) | **Tuyo**, en tu cuenta de GitHub y **privado**. |

El almacén se llama como tu ciclo: `SMX-almacen`, `DAM-almacen`, `DAW-almacen` o `ASIR-almacen`
(`APUNTES-almacen` si elegiste «otro»). Lo tienes en cada sitio (clase, casa, USB) y `dam sync` lo
mantiene igual sin perder nada. Los nombres de las carpetas son las asignaturas que elegiste en
`dam configurar`. La carpeta `Documentacio` nunca se sube: `status` y `sync` la ignoran siempre.

### Tu almacén de apuntes (si aún no lo tienes)

No hace falta saber git. El instalador lo hace por ti; si lo saltaste, escribe:

```bash
dam crear-almacen
```

1. Te pide tu **usuario de GitHub** (lo que va detrás de `github.com/`). ¿No tienes cuenta? Créala
   gratis en <https://github.com/signup>.
2. Te pregunta si ya tienes el repo. Si es la primera vez, di que **no**: se abre GitHub con el
   nombre de tu ciclo y **Private** ya puestos. Solo pulsas el botón verde **Create repository** y
   vuelves a la terminal. Si el navegador no se abre, copia la dirección que sale en la terminal.
3. Lo baja a `~/CICLO-almacen`, crea una carpeta por asignatura y la sube a GitHub. Ya puedes usar
   `dam ejecutar ordenar` y `dam sync`.

En otro equipo (clase, casa) es lo mismo, pero a la pregunta de si ya lo tienes dices que **sí**:
solo lo baja.

> **Al bajarlo o subirlo, ¿qué contraseña pongo?** En Windows se abre el navegador para que inicies
> sesión en GitHub. En Linux y macOS, git pide `Username` (tu usuario) y `Password`: ahí **no vale tu
> contraseña**, va un *token* que creas en <https://github.com/settings/tokens> con permiso «repo»
> (al pegarlo no se ve: es normal). `dam` nunca ve ni guarda tu contraseña ni tu token: los pide git.

Si ya lo tenías clonado en otro sitio, el instalador lo encuentra solo (busca un repo cuyo remoto
acabe en `-almacen`). A mano también vale:

```bash
git clone https://github.com/TU_USUARIO/ASIR-almacen.git ~/ASIR-almacen
```

### Usarlo cada día

```bash
dam status                      # ¿qué hay pendiente?
dam sync programacion "tema 3"  # solo esa asignatura
dam sync                        # todo el almacén
```

Qué hace `sync` tras un `git fetch`:

| Situación | Acción |
|---|---|
| Nada nuevo en ningún lado | «Todo está actualizado». |
| Solo cambios en GitHub | `git pull --ff-only`. |
| Solo cambios tuyos | `git add` (solo la asignatura), `commit "[asignatura]: mensaje"` y `push`. |
| De los dos lados | **Se para** y muestra `git diff --stat`. Con `--integrar` guarda lo tuyo y hace `pull --rebase`; si hay conflicto real lo deshace y no pierde nada. |

Seguridad: se niega a subir ficheros `.env` o de más de 95 MB; no necesita red para `status` (avisa y
muestra lo último que sabe); los errores (sin internet, sesión caducada, rama desactualizada,
conflicto) salen en español y sin traza.

Ruta del almacén en cada equipo, por orden de prioridad: `--almacen RUTA` > variable
`DAM_ALMACEN` > `almacen.ruta` de `acciones.json`. En el USB la letra de unidad cambia entre
equipos, así que usa la variable de entorno. Si Git protesta por «dubious ownership» en un USB
exFAT/FAT32: `git config --global --add safe.directory RUTA`.

## IA gratis con OpenCode

El servidor del centro solo responde desde la red del instituto. Para usar las acciones con IA en
casa, `dam` puede usar los **modelos gratis de OpenCode**: no piden cuenta ni clave.

```bash
dam configurar-ia         # 1 = modelos gratis con OpenCode; luego eliges el modelo de la lista
dam comprobar-ia          # OpenCode · modelo: opencode/deepseek-v4.1-flash-free → ✔ El modelo responde «ok»
```

`dam configurar-ia`:

1. Busca `opencode` (el instalador lo instala con `npm install -g opencode-ai@1.18.35`, la versión de clase).
2. Enseña los modelos gratis que hay **ese día** (OpenCode los va cambiando) y qué hace cada uno con lo
   que le mandas. Los recomendados (DeepSeek V4.1 Flash, GLM-5.3-Flash y MiniMax M3.1 Flash) no lo
   guardan ni entrenan con ello; otros sí, y de los Nemotron dicen que no les mandes datos personales.
3. Hace una pregunta mínima y lo guarda en `~/.config/dam/ia.json`.
4. Si quieres, pone ese modelo por defecto en OpenCode (`model` y `small_model` de
   `~/.config/opencode/opencode.json`), con copia del fichero anterior. Lo demás del fichero no se toca;
   si tiene comentarios, no lo toca y te dice qué cambiar.

**Cómo lo usa `dam`:** los modelos gratis solo se pueden usar desde OpenCode (no tienen una API para
llamar con `httpx`), así que `dam` lanza `opencode run` con un agente propio, `dam-ia`, en una carpeta
temporal vacía que se borra al acabar. Ese agente **no tiene herramientas**: no puede editar, ejecutar
ni navegar, y solo puede leer dentro de esa carpeta vacía. El texto del fichero va por la entrada
estándar, y lo que responde el modelo pasa por las mismas comprobaciones que con el servidor del centro.
Por qué así: [`docs/adr/0004-ia-gratis-opencode.md`](docs/adr/0004-ia-gratis-opencode.md).

**En clase, con el servidor del centro:** `dam configurar-ia --proveedor centro`, o solo en esa
terminal: `DAM_IA=centro dam ejecutar ...` (en PowerShell, `$env:DAM_IA="centro"`). `DAM_IA_MODELO`
cambia el modelo de OpenCode solo esa vez.

| Qué pasa | Mensaje |
|---|---|
| No tienes OpenCode | No encuentro opencode. Vuelve a pasar el instalador de dam (te lo instala)... |
| En WSL solo está el de Windows | El opencode que encuentro (/mnt/c/...) es el de Windows y desde WSL no funciona |
| El modelo gratis falla o ya no existe | OpenCode dice: ... (elige otro con `dam configurar-ia`) |
| Tarda más de 180 s | El modelo de OpenCode no ha respondido en 180 s |

## IA (opcional): acciones con los modelos del centro

Las reglas (extensión, fecha, nombre) no saben de qué trata `escaneo_0042.pdf`: para eso hay que
leerlo. Las acciones `resumir`, `renombrar-ia` y `clasificar` mandan el texto del fichero al
modelo que elegiste con `dam configurar-ia`: el servidor de IA del centro (el mismo que usa OpenCode
en clase) o [uno gratis de OpenCode](#ia-gratis-con-opencode), y usan lo que responde. **La IA, solo donde
aporta:** lo que una regla resuelve (mover los `.pdf`, borrar los `.tmp` viejos) se hace sin IA:
es instantáneo, gratis y funciona sin red.

**1. La clave, fuera del repo.** Las variables se leen de tu terminal o de un `.env` en la carpeta
desde la que lanzas `dam`. `.env` está en `.gitignore` y nunca se sube; `.env.example` es la plantilla:

```bash
cp .env.example .env      # y rellénalo (o exporta las variables en ~/.bashrc / setx)
dam comprobar-ia          # Servidor: ... · modelo: Qwen38-DualSpark-medium · clave: definida
```

Si instalaste sin clonar no tienes `.env.example`: define las variables en la terminal
(`export CENTRO_IA_URL=...` en Linux y macOS; `$env:CENTRO_IA_URL="..."` en PowerShell) o crea tú
el `.env` con las líneas `CENTRO_IA_URL=...`, `CENTRO_IA_KEY=...` y `CENTRO_IA_CA=...`.

**¿OpenCode ya usa el servidor del centro?** Entonces no hace falta copiar nada. En
`dam configurar-ia`, elige «Servidor de IA del centro» y di «s» cuando pregunte si usa el de
OpenCode. `dam` lee la dirección, la clave y el modelo de `~/.config/opencode/opencode.json` cada
vez que los necesita: la clave no se copia a ningún sitio, y en `~/.config/dam/ia.json` solo queda el
nombre del servidor. Si defines `CENTRO_IA_URL` y `CENTRO_IA_KEY`, mandan ellas. El certificado sale
de `CENTRO_IA_CA` o, si no está, de `NODE_EXTRA_CA_CERTS`, el mismo que usa OpenCode.

| Variable | Para qué |
|---|---|
| `CENTRO_IA_URL` | Dirección del servidor (acaba en `/v1`). |
| `CENTRO_IA_KEY` | Tu clave personal. Nunca se imprime: `comprobar-ia` solo dice «definida». |
| `CENTRO_IA_CA` | Ruta del certificado del instituto (`ca-ies-simarro.crt`). Si no está, `dam` usa `NODE_EXTRA_CA_CERTS`, el de OpenCode. |
| `CENTRO_IA_MODELO` | Opcional: otro modelo del servidor (por defecto, `Qwen38-DualSpark-medium`; los que hay los ves en OpenCode con `/models`). |

**2. Primero, siempre `--simular`.** No llama al modelo ni gasta nada: dice cuánto mandaría
(«enviaría 338 caracteres (~84 tokens)»). Un PDF escaneado sin texto se salta: no se pregunta por nada.

```bash
dam ejecutar resumir-tema ~/pruebas-tareas/apuntes-ia --simular
dam ejecutar resumir-tema ~/pruebas-tareas/apuntes-ia        # de verdad: tokens y segundos en «Detalle»
```

**3. Lo que dice el modelo nunca se usa tal cual.** Un nombre propuesto pasa por
`a_nombre_seguro()` (solo `a-z`, `0-9` y `-`; `../../.bashrc` queda `bashrc`, dentro de su carpeta) y una
categoría que no está en `categorias` va a `sin-clasificar`. El modelo de `dam` no tiene herramientas:
solo devuelve texto, y lo que pasa en tu disco lo decide el código. El documento va entre
`<documento>` y `</documento>` y el mensaje de sistema avisa de que eso nunca son instrucciones.

**4. Sin red, sin clave o con el servidor caído:** un mensaje en una línea, sale con **4** y las
acciones sin IA siguen funcionando (`dam acciones` tiene una columna IA). Si se corta a mitad, lo
hecho se queda hecho y el resto, sin tocar.

| Qué pasa | Mensaje |
|---|---|
| Falta la URL o la clave | Faltan CENTRO_IA_URL o CENTRO_IA_KEY: ponlas en .env (mira .env.example) |
| Sin red | No llego al servidor de IA: ¿estás en la red del centro? |
| Sin certificado | No me fío del servidor: falta el certificado del centro (CENTRO_IA_CA) |
| Tarda más de 120 s | El servidor de IA no ha respondido a tiempo |
| HTTP 401 / 403 / 404 / 429 | La clave no es válida / tu clave no puede usar ese modelo (cámbialo con CENTRO_IA_MODELO) / revisa CENTRO_IA_URL / demasiadas peticiones, espera un minuto |

Por qué la IA va detrás de una interfaz (`ProveedorIA`): [`docs/adr/0002-proveedor-ia.md`](docs/adr/0002-proveedor-ia.md).

## Seguridad: claves y web

Ninguna clave en el repositorio ni en su historial. `dam scan-secrets` lo comprueba:

```bash
dam scan-secrets                  # lo que se subiría a git desde esta carpeta
dam scan-secrets --staged         # solo lo preparado con git add
dam scan-secrets --historial      # todo el historial de git
dam instalar-hook                 # lo ejecuta solo antes de cada git commit
```

Nunca imprime una clave entera (solo las primeras letras y la longitud). Si una clave ya llegó a GitHub, borrarla no basta: hay que cambiarla (revocarla) en el servicio. No lee binarios (PDF, imágenes, docx...). Un falso aviso se silencia con `dam:ignore` en esa línea.

Antes de subir o entregar un proyecto: `dam doctor CARPETA` revisa que esté sano y dice qué arreglar. Para entregarlo: `dam entregar CARPETA --simular` enseña qué entra en el zip y qué se queda fuera; sin `--simular` lo crea, pero solo si `scan-secrets` no encuentra nada seguro dentro.

Para tu web: `dam test-links` encuentra enlaces, imágenes y anclas rotas (también las que solo se rompen por las mayúsculas al publicar) y `dam check-headers` revisa las cabeceras de seguridad, el CORS y las cookies. Detalles y ejemplos en [`docs/comandos.md`](docs/comandos.md).

## Pruebas

```bash
uv run pytest -v               # config, acciones, motor, IA, sync, ayuda, scan-secrets, test-links, check-headers, hook, doctor, pendientes, entregar, inventario, duplicados y readme
uv run pytest --cov=tareas     # lo mismo, diciendo qué porcentaje del código pasa por las pruebas (93 %)
bash scripts/revisar.sh        # antes de un commit: el agente revisor de OpenCode mira lo que tienes con «git add»
```

Ejecútalo desde la raíz del repositorio. Los tests de red usan un servidor local de mentira: no necesitan internet.
Las acciones con IA se prueban con un `ProveedorFalso` (`tests/conftest.py`): ninguna prueba llama
al servidor del centro ni lee tu `.env`. GitHub Actions las pasa en Ubuntu, Windows y macOS en cada
push y en cada PR (`.github/workflows/pruebas.yml`).

`scripts/revisar.sh` sale con 0 si el revisor dice `VEREDICTO: OK`, con 1 si dice `CAMBIAR` (o no
da veredicto) y con 2 si no se pudo revisar (sin opencode o más de 180 s sin respuesta). El
revisor no puede editar ni navegar, y en bash solo puede `git diff/log/status`.

## Ideas futuras

- Ayudarme a proponer el mensaje de commit según los cambios hechos.
- Más comandos para la web del portfolio (ideas en `docs/ideas/`).
- Más acciones de limpieza y organización conforme las vaya necesitando.
