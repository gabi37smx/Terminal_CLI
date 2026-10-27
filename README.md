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

Necesitas [uv](https://docs.astral.sh/uv/) y git.

```bash
git clone https://github.com/gabi37smx/Terminal_CLI.git
cd Terminal_CLI
uv sync
uv run dam --help                 # probar sin instalar
uv tool install --editable .          # instalar el comando `dam` en todo el sistema
```

En Windows (PowerShell) es igual. Si `dam` no se encuentra tras instalar: `uv tool update-shell` y abre otra terminal.

## Órdenes

| Orden | Qué hace |
|---|---|
| `dam version` | Muestra la versión. |
| `dam listar [CARPETA]` | Tabla con nombre, tipo, tamaño y fecha. |
| `dam validar` | Comprueba `acciones.json`. Sale con 3 si está mal. |
| `dam acciones` | Lista las acciones configuradas. |
| `dam ejecutar NOMBRE [CARPETA] [--simular] [--si]` | Ejecuta una acción. `--simular` enseña qué haría sin tocar nada; borrar pide confirmación salvo `--si`. |
| `dam status [ASIGNATURA]` | Qué has cambiado en local y qué hay nuevo en GitHub. No modifica nada. |
| `dam sync [ASIGNATURA] [MENSAJE] [--integrar] [--simular]` | Sincroniza el almacén con GitHub de forma segura. |

Opción global: `dam --config RUTA ORDEN` usa otro `acciones.json`. Por defecto busca
`./acciones.json` y después `~/.config/dam/acciones.json`.

**Códigos de salida:** 0 bien · 1 fallo al ejecutar (carpeta inexistente, permiso denegado, sync pendiente...) · 2 error de uso (lo pone Typer) · 3 configuración inválida.

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

**Mis 3 acciones:** `ordenar` (reparte apuntes por asignatura, mirando nombre, extensión y las
páginas de los PDF), `limpiar-temporales` (borra `.tmp/.bak/.part` de más de 30 días, con
confirmación) y `convertir-webp` (JPEG/PNG a WebP sin tocar el original).

Garantías: nunca sobrescribe (añade « (1)»), `--simular` no toca el disco ni crea carpetas y
la configuración se valida entera antes de mover un solo fichero.

## Almacén de apuntes (status y sync)

Un repositorio git (mejor **privado**) con una carpeta por asignatura (`asignaturas/programacion/`...).
Lo clonas en cada sitio (clase, casa, USB) y `dam sync` mantiene todo igual sin perder nada.

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

## Pruebas

```bash
uv run pytest        # 68 pruebas (config, acciones, motor y sync con repos temporales)
```

## Ideas futuras

- Ayudarme a proponer el mensaje de commit según los cambios hechos.
- `scan-secrets`, `audit-web`, `check-headers`... (ver `implementar2.md`).
- Más acciones de limpieza y organización conforme las vaya necesitando.
