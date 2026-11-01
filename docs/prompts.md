# Prompts clave del proyecto

Cuaderno de bitácora de `dam`: qué pedí, qué comprobé yo y qué corregí.

**Herramientas.** En clase uso OpenCode con los modelos del centro; en casa, además, Claude (chat). Cada entrada dice cuál usé.
Lo marcado con **[COMPLETAR]** es lo que solo yo sé (lo que hice en clase con OpenCode o el resultado de una prueba): se rellena con datos reales, no se inventa.

---

## Sesión 1 · Primera orden: `listar` (OpenCode) — [COMPLETAR]
**Herramienta:** OpenCode 1.18.35 · modelo centro/qwen3.8-flash-next
**Prompt del plan (agente plan):** [COMPLETAR: pega tal cual el que enviaste]
**Qué corregí del plan:** [COMPLETAR: p. ej. escapar nombres con corchetes, saltar ficheros ilegibles]
**Diffs que rechacé o deshice (/undo) y por qué:** [COMPLETAR]
**Funcionaba a la primera:** [COMPLETAR sí/no y qué fallo expliqué]
**Qué aprendí:** `typer.Exit(code=1)` termina con código 1 sin traza; el error va a stderr.

---

## 2026-10-27 · Revisión del proyecto frente a la rúbrica (Claude)
**Prompt:** «Estoy con este proyecto de CLI personalizado pero no sé si va bien o es un desastre; revisa y vamos a probar. Quiero implementar el 1 de `implementar.md` y ya veremos el 2.» (adjunté AGENTS.md, README, pyproject, opencode.json, `tareas.toml`, `punto_actual.md` y la Sesión 1).
**Qué decidí yo:** pasar de `tareas.toml` a `acciones.json` (mínimo eliminatorio de la rúbrica) manteniendo MIS tres acciones (`ordenar`, `limpiar-temporales`, `convertir-webp`), y que `status`/`sync` fueran en Python, no en Node.
**Qué corregí:** el asistente dijo que el fallo de `ordenar` era la palabra clave «so» coincidiendo dentro de otras palabras. Al enviar mi código original se vio que ya comparaba palabras completas (`\b`): `diagrama_redes.png` va a `sistemas` porque «redes» es palabra clave de esa carpeta. Lo dejé como estaba y conservé mi lógica (nombre, extensión, PDF).
**Qué aprendí:** la rúbrica tiene 4 mínimos eliminatorios (instalable con README, ≥3 acciones en `acciones.json`, cero claves en repo e historial, ≥10 commits).

## 2026-10-27 · Instalar y probar en Windows (Claude)
**Prompt:** «No tengo instalado uv ni lo de clase, ¿cómo instalo y luego vemos?»
**Resultado:** uv 0.13.6, Python 3.12.16, `uv sync` y `uv run … --help` funcionando; OpenCode 1.18.35 ya instalado.
**Qué aprendí:** el PATH, y que `src/tareas` no estaba en git: había que traer los ficheros.

## 2026-10-27 · Rehacer los mínimos y crear el almacén de apuntes (Claude)
**Prompt:** «Arregla lo que pide el profe y que funcione todo fino. Esos comandos son un ejemplo: quiero implementar los míos. He hablado con él de crear un repositorio como almacén de todos los archivos para no perder nada, en clase, en casa o en el disco extraíble.»
**Qué se construyó:** `errores.py` (TareasError, ConfigError, AccionNoValida), `config.py` (valida antes de tocar nada), `acciones.py` + `motor.py` (clase base con fábrica y una subclase por tipo), `cli.py` y `sincronizar.py` (`status` y `sync`).
**Qué comprobé yo:** `uv run pytest` en mi Windows: 67/68. El fallo era del test, no del programa (leía el mensaje del commit en cp1252 y mostraba `aÃ±ade`): se corrigió leyendo en UTF-8. Probé las tres acciones en `~/pruebas-tareas` con `--simular` y con la confirmación s/N, y `status`/`sync` con un «GitHub» falso local (clase y casa).
**Qué descubrí al probar:** `dam sync "" "mensaje"` falla en PowerShell 5 (elimina el texto vacío y «mensaje» se toma por asignatura). Se añadió `-m`.
**Diffs rechazados:** [COMPLETAR si rechazaste algo]

## 2026-10-27 · Cambio de nombre del comando a `dam`
**Prompt:** «Ya tenía asignado `gabriel` en el terminal para otros procesos de CLI; cámbialo a `dam`.»
**Qué hice yo:** reinstalar con `uv tool install --editable .` y comprobar `dam --help` desde otra carpeta.

## 2026-10-29 · Mis ediciones en el repo — [COMPLETAR herramienta usada en cada punto]
- **ADR-0001:** el borrador era del asistente; lo reescribí con mis razones (el portfolio, el PC de clase/casa/USB, por qué JSON y no TOML).
- **`docs/comandos.md` y `docs/flujo-trabajo.md`:** mi guía de uso diario del almacén.
- **`sincronizar.py`:** la carpeta `Documentacio` nunca se sube y la detección de `.env` es más amplia.
- **`cli.py`:** ayuda propia (`mostrar_ayuda`, `-h`).

## 2026-10-31 · Ayuda completa (Claude)
**Prompt:** «Quiero un `--help` más completo, con todos los comandos y opciones, bien explicados y con ejemplos.»
**Resultado:** la ayuda general se genera sola a partir de los comandos reales, cada comando tiene sus ejemplos y un test falla si añado un comando sin ellos.
**Qué comprobé yo:** la salida en Windows Terminal. `collected 0 items` en pytest no era un fallo: lo ejecuté desde `docs/` y hay que hacerlo desde la raíz.

## 2026-10-31 · `scan-secrets` (Claude)
**Prompt:** «¿Está correcto para que sigas con scan-secrets?» (idea de `implementar2.md`).
**Qué comprobé yo:** la primera pasada sobre `DAM-almacen` dio 3 avisos. Revisé las líneas a mano: 2 eran plantillas de `.env` con la contraseña literal `password` y 1 un PDF leído como texto. Pedí afinar: ahora ignora plantillas y binarios y detecta también JWT (Supabase).
**Resultado:** `dam scan-secrets` y `--historial` limpios en `Terminal_CLI` y en `DAM-almacen` (comprobado en mi terminal el 1-nov).
**Qué aprendí:** borrar una clave de los ficheros no la saca del historial; si algún día se sube una, hay que revocarla en el servicio. El escáner no lee binarios: una clave dentro de un `.docx` o un PDF no la vería.

## 2026-11-01 · `test-links`, `check-headers` e `instalar-hook` (Claude)
**Prompt:** «Implementa los otros comandos que propones, prepara `docs/prompts.md` y deja terminado lo que pide el profe en las dos sesiones.»
**Qué se construyó:** `test-links` (enlaces locales y externos, anclas y mayúsculas), `check-headers` (cabeceras de seguridad, CORS y cookies) e `instalar-hook` (revisa claves en cada commit). Los tests usan un servidor local de mentira, sin internet.
**Qué comprobé yo (1-nov, en mi Windows):**
- `uv run pytest -q` (lo lanzó Claude Code en mi equipo): primero 161 de 162; fallaba `test_cli.py` porque buscaba los títulos de la ayuda antigua («Comandos:», «Ejemplos:»). Se actualizó el test a la ayuda nueva por grupos → **162 de 162**.
- `dam test-links` sobre la carpeta de `mi-web`: 12 páginas, 544 enlaces, 67 rotos, **todos en `_backup_mejoras/`** (copia vieja sin sus `.js` ni imágenes). Las páginas reales no tienen ninguno roto.
- `dam test-links https://gabi37smx.github.io/mi-web/`: **0 rotos** en 81 enlaces. Los 2 avisos son LinkedIn (código 999: bloquea las comprobaciones automáticas, no está roto).
- `dam check-headers` en mi backend de Render: **0 de 6** cabeceras de seguridad. En GitHub Pages: 1 de 6 (solo HSTS) y CORS `*`, que es normal en una web estática y no se puede configurar.
- **Qué arreglé:** de momento nada en el portfolio. Pendiente: añadir las cabeceras al backend (por ejemplo con `helmet` en Express) y borrar o excluir `_backup_mejoras/`.

## 2026-11-01 · Revisión de los documentos antes del 6 nov (Claude)
**Prompt:** «Dejámelo todo pulido y las instrucciones claras» (adjunté `cli.py`, README, `comandos.md`, el ADR, `punto_actual.md`, la skill, `/nueva-accion`, `@revisor` y `AGENTS.md`).
**Qué cambió:** el ADR decía «imágenes de cualquier formato» y `convertir-webp` solo convierte JPEG y PNG: corregido. README, `docs/comandos.md`, `AGENTS.md` y `punto_actual.md` puestos al día; añadidas aserciones (`assert`) a `acciones.py` y `motor.py`.
**Qué comprobé yo:** las aserciones se aplicaron (4 en `acciones.py`, 1 en `motor.py`) y los 162 tests siguen pasando. Lo que dice el ADR sobre el JSON roto es cierto: con una copia rota de `acciones.json`, `dam validar` responde «línea 128, columna 1» y sale con código 3. El hook está instalado y revisó cada commit con `scan-secrets --staged`.

---

## Sesión 2 · Skill, `/nueva-accion` y `@revisor` (OpenCode) — [COMPLETAR]
**Prompt de la validación (plan y build):** [COMPLETAR]
**Prompt de `/nueva-accion` para mi 2.ª y 3.ª acción:** [COMPLETAR]
**Qué señaló `@revisor` (y `/review`) y qué decidí (arreglar, apuntar o descartar):** [COMPLETAR]
**Qué aprendí:** [COMPLETAR]
