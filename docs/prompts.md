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

**A tener en cuenta:** `{fecha}` es la fecha de modificación del fichero, no la del nombre de la captura, y el patrón distingue mayúsculas.

**Prueba de verdad (3-nov, la lancé yo en mi terminal):** `dam --config <ruta>\acciones.json validar` → 5 acciones válidas. Después, cada acción primero con `--simular` y luego sin él, contestando `s`:
- `renombrar-capturas`: 3 hechos, 0 con error. Quedan `captura_2026-11-03_001.png`, `_002.png` y `_003.jpg`; `foto-vacaciones.png` y `captura minuscula.png`, sin tocar.
- `copiar-entregas`: 3 hechos, 0 con error. Las 3 copias están en `~/pruebas-tareas/entregas` y los originales siguen en `acciones-nuevas` (10 ficheros).
- Hay que pasar `--config`: fuera del repo, `dam` busca `~/.config/dam/acciones.json`, y ese fichero no existe.

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

---

## 2026-11-03 · 6.ª acción `mover-zips`, antes `comprimir-zips` (OpenCode)
**Herramienta:** OpenCode · modelo DeepSeek V4.1 Flash Free (el primer mensaje, con Qwen 3.8 Flash-Next del centro, no dio respuesta).
**Prompt:** pegué en OpenCode el plan de la 6.ª acción que me había preparado Claude. Empezaba así: «Crea la 6.ª acción con /nueva-accion. Escribe /nueva-accion y descríbela en una frase. Te propongo comprimir-zips: mover los .zip de la carpeta a una subcarpeta comprimidos. Es sencilla y no pisa a copiar-entregas. Cualquier otra idea tuya sirve igual.»
**Cómo se usó `/nueva-accion`:** no la lancé como orden. El agente leyó `.opencode/commands/nueva-accion.md` y siguió sus pasos, pero no propuso la entrada JSON ni esperó mi visto bueno antes de editar. Lanzó él `--simular` porque el plan se lo pedía.
**Qué se añadió:** una entrada en `acciones.json` con `tipo: "mover"`, `origen` y `destino` en `~/pruebas-tareas/prueba-final` (destino `.../comprimidos`) y filtro `extensiones: [".zip"]`. No hizo falta código nuevo: el tipo `mover` ya existía.
**Validación y prueba:** `dam --config <ruta completa>\acciones.json validar` dio 6 acciones válidas. En `~/pruebas-tareas/prueba-final`, OpenCode creó `apuntes.zip`, `practica.zip`, `foto.png` y `notas.txt`; `dam --config <ruta completa>\acciones.json ejecutar comprimir-zips --simular` dio 2 simulados y 0 errores, cogió solo los dos `.zip` y no creó `comprimidos/` ni movió nada. `uv run pytest -q` dio 162 passed. Después, OpenCode borró esos 4 ficheros de prueba con `Remove-Item`.

**Prueba de verdad (3-nov, 14:08, la lancé yo en mi terminal, desde `C:\Users\HP` y sin `--config`):** creé 4 ficheros vacíos con esos mismos nombres. `dam ejecutar comprimir-zips --simular` dio 2 simulados y 0 errores. Después, `dam ejecutar comprimir-zips`, contestando `s`, dio 2 hechos y 0 con error. `apuntes.zip` y `practica.zip` están en `comprimidos/`; `foto.png` y `notas.txt` siguen en `prueba-final`.

**Cambio de nombre (3-nov):** después de esa prueba, la acción pasó a llamarse `mover-zips`; las órdenes de arriba conservan el nombre con el que se lanzaron. Solo cambió `nombre` en `acciones.json`, también en la copia de `~/.config/dam/`. Lo comprobó Claude en una copia de prueba: 6 acciones válidas y `mover-zips --simular` eligió solo los `.zip`.

**Qué señaló `@revisor` y qué se decidió:** las decisiones de esta lista las redactó OpenCode durante la sesión; no las tomé yo una a una. Las repasé después con Claude y las mantengo.
- El nombre `comprimir-zips` no comprime: el tipo `mover` solo mueve y el `.zip` ya está comprimido. Primero se mantuvo el nombre, pero después decidí cambiarlo a `mover-zips`, que dice lo que hace. La subcarpeta sigue siendo `comprimidos`.
- Documentación desfasada: `README.md` decía «Mis 3 acciones», `docs/comandos.md` «Tus 3 acciones» y `punto_actual.md` seguía con 5. Decidí actualizarlas a 6 en este mismo cambio.
- Ningún test carga el `acciones.json` real, solo JSON sintético. Decidí no añadirlo ahora: `dam validar` valida el fichero real y el tipo `mover` ya tiene tests.
- Las salvaguardas con `assert` de `acciones.py` desaparecen con `python -O`. No lo cambié: es código anterior y ajeno a esta acción.
- Si se pasa una `CARPETA` distinta del `origen`, el `destino` no cambia y los `.zip` acaban en `prueba-final/comprimidos`. Decidí usar siempre la acción sin `CARPETA`, con su `origen`, que es el caso previsto.
- Si se pasa como `CARPETA` la propia `comprimidos`, `destino_libre` renombraría en cadena (`x (1).zip`, `x (1) (1).zip`...). Decidí no tocar código y no ejecutarla nunca sobre `comprimidos`.
- Si el destino ya existe, se añade « (1)» en silencio. Decidí aceptarlo: es la garantía de no sobrescribir que ya usa `dam`.
- Si el destino es un fichero o no hay permisos, el error sale por cada fichero. Decidí aceptarlo: es el comportamiento actual de `mover`.
- No es recursiva: solo mira ficheros sueltos de la carpeta. Decidí dejarlo así y no usar `rglob`, que además podría reprocesar `comprimidos`.
- Solapamiento con `copiar-entregas` y `ordenar`, que también cogen `.zip`. Decidí documentarlo en `docs/comandos.md`: si quiero copiar primero las entregas, ejecuto `copiar-entregas` antes que `mover-zips`.
- En Windows, mover entre volúmenes es copiar y borrar, y puede quedar una copia si falla el borrado; un `.zip` abierto da error y la acción queda a medias. Decidí aceptarlo: el `origen` y el `destino` están en el mismo volumen.
- `os.path.normcase` solo ignora mayúsculas en Windows; en macOS/Linux no. Decidí no cambiarlo: el filtro de extensiones ya compara en minúsculas y `Path.exists()` cubre el caso normal.

**Pregunta de `@revisor`:** si ejecuto `dam ejecutar mover-zips ~/pruebas-tareas/prueba-final/comprimidos`, ¿qué pasa con los `.zip` y por qué `destino_libre` no lo impide?
**Mi respuesta:** `motor.preparar` usa esa carpeta como origen y selecciona sus `.zip`. `Mover.aplicar` calcula el destino `comprimidos/x.zip`, que es el propio fichero. Como ya existe, `destino_libre` devuelve `x (1).zip` y `shutil.move` lo renombra dentro de la misma carpeta. `destino_libre` solo evita sobrescribir: no comprueba si origen y destino son el mismo sitio. En una copia de prueba, `--simular` sí enseñó los nombres nuevos (`apuntes (2).zip`, por ejemplo), pero no avisa de que no tiene sentido mover esos ficheros.

**Comando de prueba:** `dam ejecutar mover-zips --simular`. Ya no hace falta `--config`: OpenCode copió `acciones.json` a `~/.config/dam/` y `dam validar` funciona desde `C:\Users\HP`. Si cambio el del repo, hay que volver a copiarlo.

---

## 2026-11-03 · Por qué no funcionaba en el PC de clase, instalador, `dam help` y TAB (Claude Code)
**Herramienta:** Claude Code, en casa (Windows), con una prueba mía en Ubuntu 24.04 (WSL).

**Prompt 1:** «Revisa el proyecto y mira por qué, si he clonado el repositorio en el PC de clase con Linux, no funcionaban en la terminal los comandos, y no he podido subir los archivos al repo de DAM-almacen. No funcionaba nada, ni `dam` ni `--help`. Tiene que funcionar en Linux, aquí en Windows y en Mac.»
**Qué pasó en clase:** [COMPLETAR] (los mensajes de error exactos que salieron en el PC de clase).
**Qué encontró:** el código no tenía la culpa. En un clon limpio, `uv sync` + `uv run dam --help` funcionan y pasan los 162 tests. En mi Windows tengo preparadas cosas que no están en el repo: `dam` instalado con `uv tool install` (`~/.local/bin`), `~/.config/dam/acciones.json`, la variable `DAM_ALMACEN` y `~/DAM-almacen`. Al clonar en otro equipo no hay nada de eso: `dam: command not found`, y `dam sync` no sabe dónde está el almacén. Para subir a GitHub hace falta un token, no la contraseña.
**Por qué el otro día sí funcionaba:** sin confirmar. Lo más probable es que fuera otro PC u otro usuario, o que el PC se restaure al reiniciar, y con eso se pierde la carpeta personal. Lo compruebo mañana con `which uv dam` y `ls ~/.config/dam ~/DAM-almacen`. Resultado: [COMPLETAR].

**Prompt 2:** «¿No puedes hacer un script o un ejecutable que, al clonar el repo en el PC que sea, lo ejecute y ya instale lo que tenga que instalar y configure lo que tenga que configurar?»
**Qué se construyó:** `instalar.sh` (Linux/macOS), `instalar.ps1` (Windows, en UTF-8 con BOM para que PowerShell 5 lea las tildes) e `instalar.cmd` (doble clic). Comprueban git, instalan uv si falta, hacen `uv sync`, instalan `dam`, copian `acciones.json` a `~/.config/dam/` (si ya existe, no lo tocan), piden nombre y correo de git si faltan, clonan `DAM-almacen` y terminan con `dam validar`. Se pueden repetir sin romper nada. `.gitattributes` fija LF para `.sh` y CRLF para `.ps1`/`.cmd`. El commit y el push de esto los hice yo (`40ff2e5`).
**Qué comprobó Claude Code:** los dos instaladores en un entorno aislado de mi Windows (HOME y carpetas de uv temporales), dos veces seguidas cada uno. Las dos veces terminaron con código 0, y la segunda saltó lo que ya estaba hecho.
**Un fallo durante la prueba:** en la primera prueba de `instalar.sh` se ejecutó de verdad `uv tool update-shell` y añadió una carpeta temporal a mi PATH de usuario de Windows. En Git Bash la ruta se escribió como `C:/...` y los dos puntos la partieron. Claude Code lo vio, quitó esa entrada y comprobó que el resto del PATH seguía igual. Repitió la prueba con la ruta en formato `/c/...`.

**Prueba de verdad en Ubuntu 24.04 (WSL, 3-nov, la lancé yo):** `git clone` desde GitHub y `bash instalar.sh`.
- Descargó uv 0.13.7 y usó el Python 3.12.3 de Ubuntu.
- Instaló `dam`, copió `acciones.json` a `/home/gabi/.config/dam/`, configuró git (nombre, correo y token 8 horas en memoria).
- `dam validar` → 6 acciones válidas, y `dam --help` funciona desde la terminal.
- **Falló** clonar `DAM-almacen`: «Invalid username or token. Password authentication is not supported». Lo que puse en *Password* no era un token válido. Pendiente: crear el token y repetir.
- `dam help` no existía («No such command 'help'»).

**Prompt 3:** «Añade `dam help` también.» → `dam help` muestra el manual completo y `dam help COMANDO` la ayuda de ese comando; si el comando no existe, sale con 2. Como `help` es una palabra de Python, el decorador `comando` acepta ahora `nombre=`. 3 tests nuevos → 167 passed. También se marcó `instalar.sh` como ejecutable. Commit y push los hizo Claude Code porque se lo pedí (`7e62593`).

**Prompt 4:** «Haz lo del autocompletado con tabulador» (con la explicación de otra conversación pegada).
**Qué se construyó:** autocompletado de comandos, de nombres de acciones (`dam ejecutar co<TAB>` → `convertir-webp`, `copiar-entregas`) y de asignaturas del almacén (`dam sync pr<TAB>` → `programacion`, `proyecto`; no ofrece `documentacio`). Si `acciones.json` está roto o no hay almacén, no sugiere nada y no da error. Los dos instaladores lo activan con una sola línea en `.bashrc`, `.zshrc` o el perfil de PowerShell, sin duplicarla. 6 tests nuevos (`tests/test_completado.py`) → **173 passed**. Commit y push los hizo Claude Code porque se lo pedí (`1f34747`).
**Qué se descubrió al revisar Typer:** `dam --install-completion` en PowerShell cambia en silencio la política de ejecución a `Unrestricted` y añade el script al perfil cada vez que se ejecuta. Además, desde `bash instalar.sh` detectaría bash aunque en macOS la terminal sea zsh. Por eso los instaladores no lo usan: miran `$SHELL` y, en Windows, si la política no deja cargar scripts, avisan sin cambiarla.
**Un error que salió en la prueba:** con `--config` escrito en la línea, el TAB daba una traza (`'str' object has no attribute 'expanduser'`): al completar, Typer deja los valores como texto. Se arregló convirtiéndolo con `Path()`, y hay un test para ese caso.
**Qué comprobó Claude Code:** un TAB real en Git Bash y en PowerShell (`TabExpansion2`) cargando el `.bashrc` y el perfil de prueba. Las sugerencias son correctas, y en PowerShell salen con descripción. Mi perfil real de PowerShell no se tocó. **Falta probarlo en Linux de verdad.**
**Prueba en el PC de clase (4-nov):** [COMPLETAR] (clonar, `bash instalar.sh`, token, `dam help`, `dam ej<TAB>`, `dam status`).

**A tener en cuenta:**
- Lo que hace funcionar `dam` en un equipo no viaja con `git clone`: hay que instalarlo en cada sitio (para eso está el instalador).
- En git, GitHub pide un token en lugar de la contraseña.
- No ejecutar `uv sync` desde WSL sobre la carpeta de Windows (`/mnt/c/...`): cambiaría el `.venv`.

---

## 2026-11-05 y 06 · `doctor`, `pendientes`, `entregar` y el TAB atascado (Claude Code)
**Herramienta:** Claude Code, en casa (Windows). Todas las pruebas sobre proyectos reales las lancé yo en mi terminal; Claude Code solo probó en `tmp_path`, en `~/pruebas-tareas` y, en modo lectura, en la documentación de Electrician.

**Prompt 1:** «Aparte de los comandos que tenemos, ¿cuáles crees que nos servirían para los proyectos que tenemos entre manos (la web portfolio, el de Electrician y este de CLI), o cuáles pondrías que son prácticos y el profesor valoraría?»
**Qué propuso:** seis comandos, por orden de utilidad: `entregar`, `doctor`, `pendientes`, `revisar-web`, `informe` y `despertar`. Desaconsejó tres ideas de `docs/ideas/`: `deploy` (`git add .` + push sin revisar), `backup-db` (necesitaría la contraseña de MongoDB Atlas) y `ask`/`pomodoro`/`game-version` (poco valor para la nota). Avisó de ficheros con claves en texto plano en mi escritorio; están fuera de los repos y no se sincronizan.
**Qué decidí yo:** hacer los tres primeros, en ese orden.

**Prompt 2:** «Empieza por `dam entregar`.»
**Qué se construyó:** `entregar.py`. Elige los ficheros como `scan-secrets` (respeta `.gitignore`) y quita siempre `.env`, claves privadas, `.git`, `.venv`, `node_modules`, `__pycache__` y la basura del sistema. Pasa `scan-secrets` solo sobre lo que va dentro: con un secreto seguro, no crea el zip. Nunca sobrescribe (añade ` (1)`). Para reutilizar código, tres funciones de `escanear.py` pasaron a ser públicas.
**Mi prueba (5-nov):** `dam entregar` sobre Electrician → «Creado … Electrician_2026-11-05.zip (47 ficheros · 342,2 KB sin comprimir · 143,3 KB el zip)».
**Qué se corrigió después:** en la línea «Se queda fuera» no salía `.env`, porque `.gitignore` ya lo había quitado antes. Ahora `.env` y las claves salen siempre en esa lista, aunque los ignore `.gitignore`. Claude Code comprobó con git que en mi zip no entraron ni `.env` ni `.claude/`.

**Prompt 3:** «La he probado y parece que funciona bien. Si lo ves bien, vamos al 2, `dam doctor`.»
**Qué se construyó:** `doctor.py`, con 7 comprobaciones básicas (si falla alguna, sale con 1) y 4 recomendadas (solo avisan). Del `.env` solo lee los nombres de las variables, y hay tests que comprueban que ningún valor sale por pantalla.
**Un fallo que cazó el propio proyecto:** el test que revisa que el repo no tenga claves detectó una línea de `test_doctor.py` que parecía una contraseña. Se montó por trozos, como dice `AGENTS.md`.
**Mis pruebas (5-nov):**
- Electrician: **11 de 11**.
- `portfolio-backend`: 8 de 11. A `.env.example` le faltan `GITHUB_TOKEN`, `GNEWS_API_KEY` y `Gemini_API_Key`; sin tests ni CI.
- `DAM-almacen`: 6 de 9. Falta README y hay un `.zip` de más de 50 MB en `lenguaje-marcas`. Los avisos de «tests» y «web estática» no tienen sentido en un almacén de apuntes: `doctor` está pensado para proyectos de código.
- `1 PROJECTE` y `PROJECTE TERMINAL CLI` son las carpetas de fuera, no los proyectos: por eso fallan git y README. Aun así, enseñaron claves en texto plano en carpetas que no están en ningún repo.

**Prompt 4:** «Analiza, dime por qué no hace nada con el repo de CLI, ni en el backend.» (con `dam doctor "…\portfolio-backend\"` y `dam doctor "…\PROJECTE TERMINAL CLI"` sin ninguna salida).
**Qué encontró (lo reprodujo en mi PowerShell):** dos problemas que coincidieron.
1. **El TAB atascaba `dam`:** al pulsar TAB en una ruta, `dam` no tiene sugerencias y devuelve una línea vacía. El script de Typer para PowerShell intenta crear una sugerencia vacía, PowerShell da error («el valor del argumento "completionText" es NULL») y el script se corta antes de borrar las variables `_DAM_COMPLETE`. Desde ese momento, cada `dam` de esa ventana cree que está sugiriendo: imprime una línea en blanco y sale con 0.
2. **La `\` final:** en `"C:\…\portfolio-backend\"`, Windows lee `\"` como unas comillas literales y a `dam` le llega una ruta acabada en `"`, que no existe. El TAB de PowerShell 5.1 añade esa `\`.

**Prompt 5:** «Sí, haz los tres arreglos.»
- El script del TAB de PowerShell lo genera ahora `dam` con un `try/finally` que borra siempre las variables, y se salta las sugerencias vacías. Se sustituye la plantilla de Typer, así que lo heredan `instalar.ps1`, `--install-completion` y `--show-completion`. Un test avisa si una versión nueva de Typer lo cambia.
- Si una ruta trae una `"` metida, `dam` explica el problema, da la orden corregida y sale con 2.
- `doctor` escribe «la misma variable» en singular y, en una carpeta de fuera, dice qué repos tiene dentro.

**Qué comprobó Claude Code en un PowerShell real:** regeneró mi `~/.config/dam/completado.ps1` igual que el instalador y simuló el TAB con `TabExpansion2` en un PowerShell sin perfil. Un TAB en una ruta → PowerShell la completa y las variables quedan vacías. `dam doc<TAB>` → `doctor`. Después, `dam version` responde normal.
**Mi prueba (5-nov, antes de los arreglos):** en una ventana nueva y sin la `\` final, `dam doctor` sobre `portfolio-backend` y `PROJECTE TERMINAL CLI` ya funcionaban. Eso confirmó las dos causas.

**Prompt 6:** «Vamos con el 3, `dam pendientes`.»
**Qué se construyó:** `pendientes.py`. Antes de diseñarlo, Claude Code miró cómo usamos las etiquetas en Electrician (solo lectura). Cuenta `[Verificado]`, `[Hipótesis]` y `[Pendiente]` por fichero, también con texto detrás (`[Verificado, entrevista 4, 29/10/2026]`). Separa los `[Verificado]` sin fecha en su línea, porque nuestra leyenda dice «con fuente y fecha». Resume la tabla de `docs/pendientes.md` por estado y por persona; una fila de «Gabi y Javi» cuenta para los dos. `--quien` compara nombres enteros sin acentos («Mari» no encuentra a Mar) y añade lo de «Todos». No cuenta leyendas, enlaces `[Pendiente](x.md)`, `docs/historico/` ni líneas con `dam:ignore`.
**Qué se corrigió al probarlo con Electrician:** la fila 53, sin estado, salía como «otro» (ahora «sin estado»); «Gabi y Javi» y «Javi y Gabi» contaban como personas distintas. Al revisar mi salida antes del commit, dos líneas «Etiquetas: [Verificado]…, [Pendiente]» de `despliegue.md` y `voz-pruebas.md` contaban como pendientes: ahora cualquier línea que empiece por «Etiquetas…:» es leyenda.
**Resultado en Electrician (6-nov):** 27 `.md`; 39 verificados (15 sin fecha, 7 de ellos en el README), 10 hipótesis y 33 pendientes. Registro: 52 filas, 33 abiertas (27 *Pendiente* y 6 *En curso*); por persona, Sergio 12 · Gabi 9 · Javi 9 · Mar 7 · Todos 3.

**Prompt 7:** «Si lo ves correcto, haz el commit y el push al repo con los tres comandos nuevos y los arreglos.»
**Qué hizo Claude Code:** como estaba en `main`, creó la rama `feature/doctor-entregar-pendientes`, hizo un commit con los 13 ficheros (`0893964`) y la subió. El hook revisó el commit: «✔ Sin claves a la vista». `uv run pytest -q` → **249 passed**.
**Pull request y fusión a `main`:** PR #3, fusionado por mí el 6-nov (`2f59e1d`). No cambió `pyproject.toml`, `uv.lock` ni los instaladores: en un equipo donde `dam` ya esté instalado basta con `git pull`.

**Qué aprendí:**
- Un script que cambia variables de entorno tiene que dejarlas como estaban pase lo que pase: para eso está `try/finally`.
- En Windows, `\"` dentro de un argumento son unas comillas literales: una ruta nunca debe acabar en `\` antes de cerrar las comillas.
- Una herramienta que revisa mis proyectos me da datos concretos (variables que faltan en `.env.example`, verificados sin fecha) en vez de impresiones.
- [COMPLETAR] (lo que yo quiera añadir)

---

## 2026-11-11 · Sesión 3: la capa IA (Claude Code)
**Herramienta:** Claude Code, en casa (Windows). Desde casa no llego al servidor del centro: todo se probó con `--simular`, sin clave, con un servidor local de mentira y con un `ProveedorFalso`. Las ejecuciones de verdad con el modelo están en la entrada siguiente, **[COMPLETAR]** en clase.

**Prompt:** «Ahora toca poner los últimos comandos, y revisar si falta algo para que cuando lo analice la IA del profe esté todo perfecto» (con el contenido de la página de la Sesión 3).
**Cómo se hizo:** una rama `capa-ia` y un commit por pieza, en el orden de la sesión: `.env.example` → bloque `mcp` → `ia.py` y `comprobar-ia` → `resumir` → `renombrar-ia` y `clasificar` → modo sin red → pruebas → skill, README y ADR.

**Qué se construyó:**
- `.env.example` sin valores reales; `.gitignore` ignora también `.env.*` (salvo `.env.example`). Comprobado: `git check-ignore -v .env` → `.gitignore:10:.env` y `git log --all --oneline -- .env` no saca nada.
- `opencode.json`: `context7` y `apuntes` en el bloque `mcp`, los dos apagados.
- `src/tareas/ia.py`: `Respuesta`, `ProveedorIA` (abstracta), `ProveedorCentro` con `httpx` y la fábrica `desde_entorno()`. `IANoDisponible` (código 4) en `errores.py`. Orden `dam comprobar-ia`.
- `resumir`, `renombrar-ia` y `clasificar` en `acciones.py`, con `AccionIA` como base, `leer_texto()` y `a_nombre_seguro()`. `TIPOS_IA` y `validar_ia()` en `config.py`.
- Mis tres acciones con IA en `acciones.json`: `resumir-tema` (en castellano aunque el apunte esté en valenciano; no vuelve a resumir los `.resumen.md`), `nombrar-descargas` (`escaneo_0042.pdf`, `documento (3).pdf`...) y `clasificar-asignatura` (mis 8 asignaturas de 1º de DAM + `otros`, para lo que `ordenar` no sabe colocar).
- `dam acciones` con columna IA; la tabla de `ejecutar` con columna Detalle y rutas con `~`.
- `tests/conftest.py` (`aislado`, `ProveedorFalso`) y `tests/test_ia.py` (48 pruebas, sin red).

**Lo que se cambió respecto al código de referencia de la página, y por qué:**
- `a_nombre_seguro`: el de la página solo quita una extensión, y `redes-ip.pdf.pdf` quedaba `redes-ip-pdf`. Ahora quita las repetidas, pero no el `.0` de `ipv4.0`. También evita los nombres que Windows no deja crear (`con`, `nul`...).
- `clasificar`: además de la categoría que no existe, se limpian las comillas y el punto final («Sistemas».) antes de compararla.
- Un PDF escaneado sin texto se salta sin preguntar al modelo. Es una de las preguntas de la auditoría del paso 8.
- Si la IA se cae a mitad de una acción, lo hecho se queda hecho, el fichero en curso sale como error, el resto como «sin tocar» y la orden sale con 4. La página solo lo preguntaba.
- `ProveedorCentro`: mensajes también para 404 (URL sin `/v1`), una respuesta que no es JSON y un certificado que no existe; quita los bloques `<think>` de los modelos que razonan; y `repr()` nunca enseña la clave.
- Los mensajes de sistema de renombrar y clasificar también dicen que el documento nunca son instrucciones (la página solo lo ponía en resumir).

**Un fallo que salió por el camino:** al hacer el commit de `ia.py`, el hook pre-commit lo paró («hay claves a la vista»). No era una clave: el `dam` instalado en el sistema no tenía `httpx` y fallaba al arrancar. Con `--editable`, el código nuevo se usa solo, pero **las dependencias nuevas no**. Se arregló con `uv tool install --editable . --force`. Está apuntado en el README: tras un `git pull` con dependencias nuevas hay que volver a pasar el instalador. El hook hizo bien en no dejar pasar el commit si no podía revisarlo.

**Roto a propósito (paso de la Sesión 4):** con `resumir` preguntando al modelo también en `--simular`, fallan 2 pruebas y salta la aserción «--simular nunca puede dar hecho». Restaurado, todo pasa.

**Comprobado en este PC (Windows):**
- Sin clave: `dam comprobar-ia` → «✘ Faltan CENTRO_IA_URL o CENTRO_IA_KEY...» + «Las acciones sin IA siguen funcionando», y sale con 4. Igual con un servidor que no existe («No llego al servidor de IA») y con un certificado que no existe.
- `dam ejecutar resumir-tema --simular` en `~/pruebas-tareas/apuntes-ia`: 4 simulados («enviaría 211 caracteres (~52 tokens)»), el PDF escaneado saltado y el `.resumen.md` de antes fuera del filtro. No se creó la carpeta `resumenes`.
- Con el servidor «caído», `convertir-webp` (sin IA) sigue funcionando y sale con 0.
- `uv run pytest` → 403 pasan, 1 saltado.

---

## Sesión 3 · context7 y las acciones con IA de verdad (OpenCode, en clase) — [COMPLETAR]
**Herramienta:** OpenCode · modelo centro/qwen3.8-flash-next
**context7 (paso 2):** conectar con `/mcps` solo para esa sesión, preguntar en el agente plan cómo pasar a `httpx.post` un certificado de CA propio y desconectarlo. Qué respondió: [COMPLETAR]. ¿Propuso `verify="ruta"` (obsoleto en httpx 0.28) o `ssl.create_default_context`? [COMPLETAR]. Comprobado con `uv run python -W always -c "import httpx; ..."`: [COMPLETAR]. La frase para aquí: «context7 me trajo la doc, pero tuve que elegir yo» [COMPLETAR con lo que pasó de verdad].
**`dam comprobar-ia` en la red del centro:** [COMPLETAR] (servidor, modelo y segundos)
**`dam ejecutar resumir-tema` de verdad:** [COMPLETAR] (tokens y segundos de cada fichero, y si el resumen acaba en una línea «Para el examen:» con contenido)
**`dam ejecutar nombrar-descargas` y `clasificar-asignatura` de verdad:** [COMPLETAR] (qué nombres y categorías puso; qué hizo con `descarga.pdf`, el que intenta engañar al modelo)
**Un fallo real del modelo y cómo lo arreglé en el JSON (no en Python):** [COMPLETAR]
**Rómpelo a propósito en clase:** sin clave, con una URL que no existe, con una clave mala (401) y sin `CENTRO_IA_CA`; `echo $?` → 4 en los cuatro casos: [COMPLETAR]
**Qué aprendí:** [COMPLETAR]

---

## 2026-11-11 · Sesión 4: pruebas, CI en tres sistemas, revisar.sh y versión 1.0.0 (Claude Code)
**Herramienta:** Claude Code, en casa (Windows).
**Prompt:** «Sí, súbela y sigue con la sesión 4» (después de subir la rama `capa-ia`, PR #15).
**Cómo se hizo:** rama `release-1.0` y un commit por pieza: `revisar.sh` → `pruebas.yml` → versión 1.0.0 → README → CHANGELOG y documentación.

**Qué había ya de antes:**
- `tests/` con `conftest.py`, `ProveedorFalso` y pruebas de los códigos de salida del 0 al 4 con `CliRunner`.
- GitHub Actions en Ubuntu y Windows.

Las pruebas ya pasaban de 28 (las que pide la página): ahora son 405.

**Qué se hizo:**
- `scripts/revisar.sh`:
  - Le pasa `git diff --staged` por la entrada estándar a `opencode run --agent revisor`, con `timeout 180` (en macOS, `gtimeout`).
  - Sale con 0 si el veredicto es `VEREDICTO: OK`, con 1 si es `CAMBIAR` o no hay veredicto, y con 2 si no se pudo revisar.
  - Probado con un `opencode` de mentira: OK → 0, CAMBIAR → 1, sin veredicto → 1, y más lento que el límite → 2.
- **Un fallo que encontré antes de que pasara:** el revisor era `mode: subagent`, y al buscarlo en el ejecutable de OpenCode sale el aviso «is a subagent, not a primary agent. Falling back to default agent». Es decir, `opencode run --agent revisor` habría usado el agente por defecto, que **sí puede editar**, y los permisos de solo lectura no habrían servido. Lo cambié a `mode: all` (sigue funcionando como `@revisor`) y le pedí la línea de veredicto.
- `.github/workflows/tests.yml` → `pruebas.yml`, con macOS, `fail-fast: false` y `pytest -v`.
- `pytest-cov`: `uv run pytest --cov=tareas` da 93 %. `.coverage` va a `.gitignore`.
- Versión 1.0.0 en `pyproject.toml` y `__init__.py`. Una prueba comprueba que las dos coinciden.
- Alias `tareas` del mismo programa, porque la spec v0 y la página usan `tareas version`: `tareas version` → `tareas 1.0.0` y `dam version` → `dam 1.0.0`.
- README: instalación en una orden (`uv tool install git+...@v1.0.0`) y desinstalación en Linux, macOS y Windows (hook, programa, `~/.config/dam`, línea del TAB y variables).
- `CHANGELOG.md` en formato Keep a Changelog, hecho a partir de `git log` y revisado contra el código.

**Roto a propósito (`--simular`):** en `Mover.aplicar` cambié `if not simular:` por `if True:`. Falla `test_simular_no_toca_nada_ni_crea_carpetas`, que encuentra la carpeta `NoExiste` creada. Con `git restore` vuelve a pasar todo (405 pasan, 1 saltado).

---

## Sesión 4 · borrador del CHANGELOG, release e instalación cruzada — [COMPLETAR]
**`opencode run --agent plan` → `docs/changelog-borrador.md` (en clase):** [COMPLETAR] (qué se inventó o qué se dejó comparado con `CHANGELOG.md`)
**`bash scripts/revisar.sh` de verdad:** [COMPLETAR] (veredicto, segundos y si lo que señaló era cierto)
**Actions en macOS:** [COMPLETAR] (¿verde a la primera? si no, qué falló)
**Release:** PR de `release-1.0` fusionada, `git tag -a v1.0.0`, `git push --tags` y `gh release create`: [COMPLETAR]
**Instalación cruzada:** quién la hizo, en qué sistema, qué issues abrió y cómo los contesté: [COMPLETAR]
**Qué aprendí:** [COMPLETAR]
