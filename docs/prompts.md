# Prompts clave del proyecto

Cuaderno de bitácora de `dam`: qué pedí, qué comprobé yo y qué corregí.

**Herramientas.** En clase uso OpenCode con los modelos del centro; en casa, además, Claude (chat) y, desde el 3-nov, Claude Code. Cada entrada dice cuál usé.
Lo marcado con **[COMPLETAR]** es lo que solo yo sé (lo que hice en clase con OpenCode o el resultado de una prueba): se rellena con datos reales, no se inventa.

---

## Sesión 1 · Primera orden: `listar` (OpenCode) — [COMPLETAR]
**Herramienta:** OpenCode 1.18.35 · modelo centro/qwen3.8-flash-next
**Prompt del plan (agente plan):** [COMPLETAR] (no consta en las sesiones exportadas de OpenCode)
**Qué corregí del plan:** [COMPLETAR] (no consta en las sesiones exportadas de OpenCode)
**Diffs que rechacé o deshice (/undo) y por qué:** no consta ninguno. Solo hubo un bloqueo: el agente intentó hacer `git push` y la regla `"git push *": "deny"` de `opencode.json` lo impidió; el push lo hice yo.
**Funcionaba a la primera:** [COMPLETAR] (no consta en las sesiones exportadas de OpenCode)
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
**Diffs rechazados:** no consta ninguno.

## 2026-10-27 · Cambio de nombre del comando a `dam`
**Prompt:** «Ya tenía asignado `gabriel` en el terminal para otros procesos de CLI; cámbialo a `dam`.»
**Qué hice yo:** reinstalar con `uv tool install --editable .` y comprobar `dam --help` desde otra carpeta.

## 2026-10-29 · Cambios pedidos a OpenCode
**Herramienta:** OpenCode · modelo DeepSeek V4.1 Flash Free (en todos los puntos).
- **ADR-0001:** lo redactó el agente porque se lo pedí («razónalo tú para defenderlo y redacta ese documento»), y lo revisé después.
- **`docs/comandos.md` y `docs/flujo-trabajo.md`:** mi guía de uso diario del almacén; los pedí a OpenCode.
- **`sincronizar.py`:** la carpeta `Documentacio` nunca se sube, el guardián de `.env` y la normalización de nombres de asignatura. Lo hizo OpenCode a petición mía.
- **`cli.py`:** la ayuda estilo Linux de `dam --help` (`mostrar_ayuda`, `-h`). La hizo OpenCode a petición mía.
- **Commits:** los hizo OpenCode por petición explícita, 12 commits en la rama `feature/acciones-json`; luego la fusión a `main` y el push.

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

## Antes del 3-nov · Cómo entró en el repo la entrega de Claude (chat)
Con Claude (chat) se generó una entrega con `test-links`, `check-headers`, `instalar-hook`, aserciones, docs y ADR. La apliqué yo y se fusionó en `main` con el PR #2.

## 2026-11-03 · Acciones `renombrar-capturas` y `copiar-entregas` (Claude Code)
**Herramienta:** Claude Code. No se usó `/nueva-accion`.
**Prompt:** «Añade 2 acciones propias nuevas en acciones.json siguiendo la skill acciones-json. Pruébalas con dam ejecutar --simular en ~/pruebas-tareas.»
**Qué decidí yo:** de las 4 que propuso el agente (`renombrar-capturas`, `copiar-entregas`, `mover-instaladores`, `archivar-pesados`) elegí `renombrar-capturas` (tipo `renombrar`) y `copiar-entregas` (tipo `copiar`). Los dos tipos ya existían: solo cambió `acciones.json`.
**Qué se comprobó (las órdenes las lanzó Claude Code en mi equipo):**
- `dam validar`: 5 acciones válidas, código de salida 0.
- Con `--simular` en `~/pruebas-tareas/acciones-nuevas` (10 ficheros vacíos de prueba): `renombrar-capturas` coge 3 (`Captura de pantalla….png` ×2 y `Screenshot_….jpg`) y deja fuera `foto-vacaciones.png` y `captura minuscula.png`; `copiar-entregas` coge 3 (`.pdf`, `.docx` y `.zip` con «entrega» o «practica» en el nombre) y deja fuera `entrega-notas.txt` y `apuntes tema1.pdf`.
- No se tocó nada: siguen los 10 ficheros y la carpeta `entregas/` no se creó.
- `uv run pytest -q`: 162 passed.

**A tener en cuenta:** `{fecha}` es la fecha de modificación del fichero, no la del nombre de la captura, y el patrón distingue mayúsculas. **Pendiente:** ejecutarlas de verdad, sin `--simular`.

---

## Sesión 2 · Skill, `/nueva-accion` y `@revisor` (OpenCode) — [COMPLETAR]
**Herramienta:** OpenCode · modelo DeepSeek V4.1 Flash Free
**Prompt de la validación (plan y build):** [COMPLETAR] (no consta en las sesiones exportadas de OpenCode)
**`/nueva-accion`:** no se usó. La skill `acciones-json` se cargó en la sesión del 28/10.
**Comandos y cambios pedidos a OpenCode:** el sistema de sincronización con el repo de asignaturas (`sync` y `status`, `DAM-almacen`), nombres de asignaturas en valenciano en `acciones.json` y excluir la carpeta privada del almacén.
**`@revisor` y `/review`:** no consta que se usaran.
**Revisión del agente build:** al preguntar si la CLI funcionaba en Windows, Linux y Mac, hizo una revisión multiplataforma del código (`shell=True`, rutas, codificaciones).
**Revisión en el chat de Claude:** al comparar el repo con los requisitos del profe, faltaban `test-links`, `check-headers`, el hook pre-commit y las aserciones.
**Qué aprendí:** que se puede tener una CLI personalizada con los comandos que quieras; que, aunque usemos IA, las cosas cuestan y necesitan su tiempo para funcionar bien; y que aún me falta mucho por aprender.
