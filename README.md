# dam (proyecto `tareas`)

Mi herramienta de línea de órdenes para automatizar tareas repetitivas con ficheros y mantener
mis apuntes de 1º DAM sincronizados entre el PC de clase, el de casa y el USB.

> Nota: en la spec v0 el comando se llamaba `tareas`; ahora se llama **`dam`** (el paquete
> Python sigue siendo `tareas`).

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
10. **Instalación:** `uv tool install --editable .` (lo completo en la semana 4).

## Instalación

### Lo rápido: un script que lo hace todo

Solo necesitas git. Clona el repositorio y ejecuta el instalador de tu sistema:

```bash
git clone https://github.com/gabi37smx/Terminal_CLI.git
cd Terminal_CLI
bash instalar.sh          # Linux y macOS
```

En Windows: doble clic en `instalar.cmd` (o `powershell -ExecutionPolicy Bypass -File instalar.ps1`).

El script instala uv si no está (y uv baja Python 3.12), instala el comando `dam`, copia
`acciones.json` a `~/.config/dam/`, te pide nombre y correo para git si faltan y clona tu
`DAM-almacen` en `~/DAM-almacen`. Se puede repetir sin miedo: lo que ya está hecho se salta.
Al terminar, abre una terminal nueva. Si git te pide contraseña al clonar o al hacer `sync`, pega un
**token de GitHub**, porque la contraseña normal no vale.

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

## Órdenes

| Orden | Qué hace |
|---|---|
| `dam version` | Muestra la versión. |
| `dam listar [CARPETA]` | Tabla con nombre, tipo, tamaño y fecha. |
| `dam validar` | Comprueba `acciones.json`. Sale con 3 si está mal. |
| `dam acciones` | Lista las acciones configuradas. |
| `dam ejecutar NOMBRE [CARPETA] [--simular] [--si]` | Ejecuta una acción. `--simular` enseña qué haría sin tocar nada; borrar pide confirmación salvo `--si`. |
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

**Códigos de salida:** 0 bien · 1 fallo al ejecutar (carpeta inexistente, permiso denegado, sync pendiente, claves, enlaces rotos o cabeceras básicas que faltan...) · 2 error de uso (lo pone Typer) · 3 configuración inválida.

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
| `nombre` | sí | Único; minúsculas, números y guiones. Es lo que escribes en `dam ejecutar NOMBRE`. |
| `descripcion` | sí | Lo que muestra `dam acciones`. |
| `tipo` | sí | `mover`, `copiar`, `renombrar`, `borrar`, `ordenar` o `convertir`. |
| `origen` | no | Carpeta por defecto si no pasas CARPETA. `~` se expande en los tres sistemas. |
| `destino` | mover / copiar | Dónde van los ficheros (se crea si no existe). |
| `plantilla` | renombrar | Nombre nuevo: `{fecha:%Y-%m-%d}`, `{n:03}`, `{ext}`, `{nombre}`. |
| `filtro` | no (borrar: sí) | `extensiones`, `patron` (regex), `mas_antiguo_que_dias`, `mayor_que_mb`; se cumplen todos. |
| `carpetas` | ordenar | `{"asignatura": ["palabra clave", ...]}`. Se comparan palabras completas, sin tildes ni mayúsculas. |
| `por_extension` | no (ordenar) | `{".sql": "bases-datos"}`: pista extra por extensión. |
| `calidad` | no (convertir) | 1-100, por defecto 80. |
| `confirmar` | no | `true` = pide confirmación antes de actuar (salvo `--si`). |

**Mis 6 acciones:** `ordenar` (reparte apuntes por asignatura, mirando nombre, extensión y las
páginas de los PDF), `limpiar-temporales` (borra `.tmp/.bak/.part` de más de 30 días, con
confirmación), `convertir-webp` (JPEG/PNG a WebP sin tocar el original), `renombrar-capturas`
(capturas con fecha y número), `copiar-entregas` (copia entregas y prácticas a una carpeta de
seguridad) y `mover-zips` (mueve los `.zip` a la subcarpeta `comprimidos`).

Garantías: nunca sobrescribe (añade « (1)»), `--simular` no toca el disco ni crea carpetas y
la configuración se valida entera antes de mover un solo fichero.

Ojo con `mover` y `copiar`: si pasas una `CARPETA`, los ficheros se cogen de ahí, pero van al `destino`
fijo de `acciones.json`, aunque esté fuera de esa carpeta. Mira la tabla de `--simular` antes.

## Almacén de apuntes (status y sync)

Un repositorio git (mejor **privado**) con una carpeta por asignatura (`asignaturas/programacion/`...).
Los nombres deben coincidir con las claves de `carpetas` en `acciones.json`.
Lo clonas en cada sitio (clase, casa, USB) y `dam sync` mantiene todo igual sin perder nada.
La carpeta `Documentacio` nunca se sube: `status` y `sync` la ignoran siempre.

```bash
git clone https://github.com/TU_USUARIO/DAM-almacen.git ~/DAM-almacen
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
uv run pytest        # config, acciones, motor, sync, ayuda, scan-secrets, test-links, check-headers, hook, doctor, pendientes, entregar, inventario, duplicados y readme
```

Ejecútalo desde la raíz del repositorio. Los tests de red usan un servidor local de mentira: no necesitan internet.

## Ideas futuras

- Ayudarme a proponer el mensaje de commit según los cambios hechos.
- Más comandos para la web del portfolio (ideas en `docs/ideas/`).
- La capa de IA (semana 3): acciones que usen los modelos del centro, con la clave fuera del repo y un modo sin red.
- Más acciones de limpieza y organización conforme las vaya necesitando.
