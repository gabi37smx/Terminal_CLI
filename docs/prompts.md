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
**Por qué el otro día sí funcionaba:** sin confirmar. Lo más probable es que fuera otro PC u otro usuario, o que el PC se restaure al reiniciar, y con eso se pierde la carpeta personal. Lo compruebo mañana con `which uv dam` y `ls ~/.config/dam ~/DAM-almacen`. Resultado (13-nov, en el PC del aula donde lo instalé el 12-nov): un día después, `which dam` seguía dando `~/.local/bin/dam` y `~/.config/dam` seguía ahí. Ese PC **guarda la carpeta personal**, así que lo de que se restaura al reiniciar queda descartado (al menos en ese PC). Lo del otro día fue otro PC u otro usuario.

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
- Antes de hacer un commit hay que mirar en qué rama estoy: como estaba en `main`, Claude Code creó una rama nueva antes de guardar nada. Así `main` solo cambia cuando yo fusiono la PR.

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
**`dam comprobar-ia` en la red del centro:** probado el 13-nov en mi PC de clase (lo cuento en la entrada «Mi PC de clase: almacén real e IA del centro»). Con el modelo de entonces, `qwen3.8-flash-next`, el servidor respondía **403**. Con `Qwen38-DualSpark-medium`, el del OpenCode del centro: «✔ El modelo responde «ok» en 31.6 s (30+2 tokens)».
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
**Actions en macOS:** no salió verde a la primera. El 11-nov, la rama `release-1.0` falló en Ubuntu y en macOS, y en Windows pasó. La prueba `test_version_con_los_dos_nombres` le pasaba al programa una ruta de Windows (`C:\Users\alumno\...\tareas.exe`). En Linux y macOS esa ruta no se parte por las barras invertidas, así que el nombre no salía y respondía `dam 1.0.0` en vez de `tareas 1.0.0`. Se arregló en `bde3cb7`: ahora la prueba construye las rutas con `Path.home()` del sistema donde se ejecuta. Tres minutos después, verde en los tres. Para eso sirve probar en los tres sistemas: en mi Windows esa prueba pasaba siempre.
**Release:** PR de `release-1.0` fusionada, `git tag -a v1.0.0`, `git push --tags` y `gh release create`: la PR #16 la fusioné yo el 11-nov a las 15:40 y en los minutos siguientes creé la etiqueta `v1.0.0` y la release «tareas 1.0.0» en GitHub. Las órdenes me las dio Claude Code, pero las ejecuté yo. Esa misma tarde salió la `v1.0.1` con los arreglos del ensayo en el portátil (abajo).
**Ensayo en un ordenador limpio (hecho el 11-nov):** en mi portátil viejo con Ubuntu 24.04.4 recién instalado, siguiendo solo el README, mientras Claude Code me guiaba y arreglaba desde el PC de casa. Lo que salió, cada cosa con su issue (abiertos con `gh issue create`) y arreglado en la **1.0.1** con «Closes #N»:
- **#17:** Ubuntu no traía ni `git` ni `curl`, y al escribir `uv` sin tenerlo, Ubuntu sugiere el de snap. → Apartado «Antes de empezar» en el README.
- **#18:** con la orden única no hay `acciones.json`, y el error decía «Créalo» sin decir cómo. → El mensaje dice de dónde bajar el ejemplo y dónde guardarlo. Una prueba comprueba que ese ejemplo es válido.
- **#19:** `comprobar-ia` mandaba a `.env.example`, que sin clonar no existe. → El mensaje explica cómo definir las variables en la terminal o en un `.env`.
- **#20:** errores de uso en inglés dentro de un panel en español, ayuda que solo habla de `dam` y TAB que pedía `instalar.sh`. → Traduzco los mensajes de Click antes de que Typer los pinte (sin tocar la librería). La línea `Usage:` se queda en inglés.
- **#22 (en la Fase B, con `bash instalar.sh`):** en «Tu usuario de GitHub» puse `gabi`, el del portátil, y dejé vacíos el *Username* y el *Password* que pidió git → «Repository not found». → Los dos instaladores explican qué usuario es, qué poner en cada línea (Password = token) y qué significa ese error.

También vi que `uv tool install` no usa mi `uv.lock`: en el portátil se instaló pypdf 7.0.1 y en casa tengo la 6.21.3. Las pruebas de IA y de acciones pasan también con pypdf 7.0.1.

**Resultado final en el portátil con la 1.0.1** (tras `git pull` y `bash instalar.sh`):
- `dam version` → `dam 1.0.1`.
- `dam -status` → «No existe la opción -s», en español.
- `dam ejecutar listar` → «No hay ninguna acción «listar». Mira la lista con: dam acciones», sin traceback.
- `dam status` → avisa de que el almacén no existe en este equipo (no lo cloné en el portátil).
- El TAB funciona: `dam ej` + tecla Tab → `dam ejecutar`. La primera vez escribí `<TAB>` tal cual, sin entender que había que pulsar la tecla, y bash dio un error de sintaxis por el `<`. No era un fallo de `dam`.
- `uv run pytest -q` → **418 passed, 1 skipped** en Ubuntu 24.04.
- Release `v1.0.1` publicada con los arreglos de los issues #17-#22, todos cerrados.
**Instalación cruzada con otra persona:** quién la hizo, en qué sistema, qué issues abrió y cómo los contesté: [COMPLETAR]
**Qué aprendí:**
- **El README se prueba en un ordenador limpio y siguiéndolo al pie de la letra.** En mi PC funcionaba porque ya tenía `git`, `curl` y `uv`. En el portátil recién instalado salieron cinco fallos en una tarde, y ninguno era del código: eran del README y de los mensajes.
- **Un issue por fallo y `Closes #N` en el commit.** Así cada arreglo queda unido a su problema y la release dice qué arregla.
- **Un mensaje de error tiene que decir qué hacer, no solo qué pasa.** «Créalo» o «mira `.env.example`» no sirven si no dices cómo ni dónde.
- **`uv tool install` no usa mi `uv.lock`.** En otro equipo se pueden instalar otras versiones de las librerías, y las pruebas tienen que pasar también con ellas.

---

## 2026-11-11 y 12 · `dam configurar`: mi idea del «adduser» (Claude Code)
**Herramienta:** Claude Code, en casa (Windows), y mi Ubuntu de WSL para probarlo como si fuera otro alumno.
**Prompt 1 (la idea):** «Cuando instalamos el terminal CLI, ¿no podríamos hacer que, como en Linux cuando creas un usuario, pregunte datos y que en base a esos datos se configure? Lo digo porque ahora solo vale lo de las carpetas y asignaturas para alumnos de DAM. ¿Y si pudieras definir las asignaturas y ya en base a ello se ordenaran los archivos, PDF y demás?»
**Prompt 2 (el alcance):** «Yo cogería para empezar el medio de SMX, DAM que ya tenemos, DAW que es casi igual que DAM, y ASIR o ASIX (castellano o valenciano). Así tenemos la rama de informática; más adelante ya ampliaremos.»
**Por qué se me ocurrió:** fue el 11-nov por la tarde, pensando en que más gente pudiera usar esta CLI. Pensé en mi cuñado, que está haciendo ASIR: sus asignaturas no son exactamente las mías (este año se parecen bastante, pero no son las mismas), y tal como estaba, `ordenar` solo le servía a alguien de 1º de DAM. Y pensé: si cogemos DAM y ASIR, ¿por qué no DAW, y también los del grado medio? Me acordé de cuando creas un usuario en Linux con `adduser`, que te pregunta unos datos y con ellos lo deja configurado. Pues lo mismo: que `dam` pregunte qué estudias y se configure solo. Como el profesor dice que pensemos a lo grande, dicho y hecho: empecé por la familia de Informática, que es a quien más le sirve, y más adelante se puede ampliar.

**Qué se hizo (PR #25):**
- `ciclos.py`: el vocabulario. Las asignaturas de 1º y 2º de SMX, DAM, DAW y ASIR, con su nombre en castellano y en valenciano, palabras clave en los dos idiomas y extensiones propias (`.pkt` → redes, `.php` → servidor...).
- `dam configurar`:
  - Pregunta ciclo y curso, enseña las asignaturas y deja quitar y añadir.
  - Reescribe solo `ordenar` y `clasificar`.
  - Valida antes de guardar y guarda una copia del anterior.
  - Apunta lo elegido en `perfil` y ofrece crear las carpetas en el almacén.
- 1º de DAM es exactamente mi `acciones.json` de antes, y una prueba lo vigila. Si eliges las mismas asignaturas, esas acciones no cambian.
- Los instaladores lanzan `dam configurar` después de clonar el almacén.

**Cómo lo probé:**
- En WSL hice como si fuera un alumno de 1º de SMX: 15 apuntes reales míos en `~/Descargas`.
- Usé un `acciones.json` y un almacén de prueba (`dam --config ~/prueba-smx/acciones.json` y `DAM_ALMACEN=~/prueba-smx/almacen`).
- Primero `--simular` y después de verdad.

**Lo que salió al probar (cada cosa, arreglada en su PR):**
- **El `dam` de WSL no arrancaba** (`ModuleNotFoundError: httpx`). Claude Code me dijo que no hacía falta instalar nada, pero ese `dam` era de antes de la semana 3. Se arregló con `uv tool install --editable . --force`. Es el aviso del README: después de un `git pull` con dependencias nuevas, hay que reinstalar.
- **#26 · La pregunta confundía:** en «asignaturas que añades» escribí los números de las que me quedaba (`3,4,5,6,7`), y el programa empezó a crear asignaturas llamadas «3», «4»... Ahora:
  - La pregunta dice NUEVAS y por nombre.
  - Enseña con cuáles te quedas.
  - Si escribes un número, lo explica y vuelve a preguntar.
- **#26 · El vocabulario de SMX se quedaba corto:** solo colocaba 7 de 15. Se añadieron `.pka` y `.odb`, discos y cajas, las siglas MME y SOX, cambio climático y contraseñas.
  - `som` no se añadió, aunque es la sigla de Sistemes Operatius Monolloc: en valenciano «som» es «somos», y al leer el texto de los PDF mandaría cualquier apunte a esa asignatura.
  - `.odt` y `.ods` tampoco, porque los usan todas las asignaturas.
- **#27 · Las palabras nuevas no llegaban:** al repetir `dam configurar`, «tus asignaturas de la última vez» traían las palabras clave viejas. Solo se recalculaban las extensiones, por eso el `.odb` sí funcionó y «discos durs» no. Ahora se juntan las del vocabulario con las tuyas.
- **#27 · `dam sync` con un almacén que no es git:** al acabar, `ordenar` ofrecía `dam sync` con mi almacén de prueba (una carpeta normal) y fallaba. Ahora avisa y no lo ofrece.
- **#27 · GitHub en rojo en los 3 sistemas:** allí la consola mide 80 columnas y Rich partía la frase que buscaba una prueba. Ahora las pruebas de `configurar` comparan sin saltos de línea; pasan con 40, 60, 80 y 120 columnas.
- **Un error de Claude Code:** en una de sus pruebas creó 7 carpetas vacías en mi almacén de verdad, porque en este PC `DAM_ALMACEN` apunta a él. Se dio cuenta, comprobó que solo tenían el `.gitkeep`, las borró y `git status` del almacén quedó limpio. Desde entonces, las pruebas usan un almacén temporal.

**Resultado:** con la #27, **11 de 15** apuntes a su asignatura y 4 a POR-TIPO. Los 4 que faltan son el Examen_SOM, un `.ods` sin pistas en el nombre y dos que son de 2º (cambio climático y John the Ripper).

**El instalador, probado de verdad en Linux (WSL, 12-nov):** con `bash instalar.sh` el TAB funciona (`dam ej` + Tab). A «¿La rehago con las acciones del repo?» respondí N para no tocar mi configuración de WSL.

**#28 · Un solo fichero:** quise convertir solo `portada.png` con `dam ejecutar convertir-webp ~/Descargas/portada.png`, y `dam` decía «La carpeta … no existe», aunque el fichero sí existía. Ahora:
- Acepta un fichero suelto, solo si cumple el filtro de la acción (si no, dice por qué). Así, `borrar` no se salta los días.
- `dam acciones -h` trae ejemplos de cómo usar las acciones.

**Qué aprendí:**
- **Probarlo yo como si fuera otro es lo que más fallos saca.** Las pruebas automáticas pasaban todas y, aun así, haciendo de alumno de SMX en WSL salieron cinco cosas. Ninguna la habría visto sin usarlo de verdad, con mis apuntes y equivocándome como se equivocaría otro, como cuando escribí números donde iban nombres.
- **Una pregunta clara también es parte del programa.** Lo de «asignaturas que añades» no era un fallo del código, sino de cómo estaba escrita la pregunta.
- **Una palabra clave tiene que ser rara.** `som` es la sigla de SOM, pero en valenciano es «somos»: como `ordenar` también lee el texto de los PDF, metería en SOM cualquier apunte en valenciano. Por eso hay cosas que es mejor dejar a `clasificar` (la IA) o a POR-TIPO.
- **Al guardar algo calculado, piensa en cuando cambie la fuente.** Lo que guardaba `configurar` se quedaba con las palabras del vocabulario de aquel día, y las mejoras no llegaban nunca.
- **Hay que probar en un sitio que no sea el de verdad.** En una prueba se crearon carpetas en mi almacén real, porque `DAM_ALMACEN` apunta a él. Desde entonces pruebo con `--config` y un `DAM_ALMACEN` de prueba.
- **Después de un `git pull`, reinstalar si hay dependencias nuevas.** El `dam` de WSL no arrancaba (`ModuleNotFoundError: httpx`). Ya lo decía mi README.
- **GitHub Actions no es mi terminal.** Allí la consola mide 80 columnas y las frases se parten: una prueba que pasaba en casa falló en los tres sistemas. Las pruebas no deben depender del ancho de la pantalla.
- **Pensar a lo grande sin pasarse.** Empecé por los 4 ciclos de Informática, que es a quien más le sirve, y dejé escrito cómo añadir otro.

## 2026-11-12 · `dam configurar-ia`: la IA de dam con los modelos gratis de OpenCode (Claude Code)
**Herramienta:** Claude Code, en casa (Windows), y mi Ubuntu de WSL para el instalador.
**Prompt:** «Una cosa para lo de la IA, ¿no podríamos hacer que usara OpenCode con modelos gratuitos como DeepSeek u otro, el que sea, como un instalador más o que se autoinstale si quieres con IA, que lo pregunte, que se configure ya con los modelos gratuitos, que cuando se instale se cree el archivo de configuración de los modelos, el de opencode.json o algo así más automatizado?»
**Por qué se me ocurrió:** el servidor del centro solo responde desde la red del instituto. En casa, que es donde más trabajo en el proyecto, `resumir-tema`, `nombrar-descargas` y `clasificar-asignatura` no me servían para nada: solo podía probarlas con `--simular`. Yo ya usaba OpenCode con modelos gratis, así que pensé: si OpenCode puede hablar con esos modelos desde casa, ¿por qué no puede hacerlo `dam`? Y que lo dejara configurado el instalador, para que otro alumno no tuviera que pelearse con ficheros de configuración.

**Lo que me explicó antes de empezar:** los modelos gratis de OpenCode solo funcionan desde dentro de OpenCode, así que `dam` no los puede llamar con `httpx` como al servidor del centro. Propuso lanzar `opencode run` con un agente propio sin herramientas, para no romper lo que decidí en el ADR-0002 (que un PDF con «Ignora tus instrucciones...» no pueda hacer nada). También me avisó de que no todos los modelos gratis tratan igual lo que les mandas y de que los van cambiando.

**Qué se hizo (rama `feature/ia-opencode-gratis`):**
- `ProveedorOpenCode` en `ia.py`: otra subclase de `ProveedorIA`, como decía el ADR-0002. Las acciones no cambian.
- `dam configurar-ia`:
  - Pregunta: modelos gratis con OpenCode, servidor del centro o ninguno.
  - Enseña los modelos gratis de ese día con lo que hace cada uno con lo que le mandas (los recomendados, primero).
  - Hace una pregunta mínima y lo guarda en `~/.config/dam/ia.json`.
  - Si quiero, pone ese modelo por defecto en mi `opencode.json` global, con copia del anterior.
- `dam comprobar-ia` y `dam ejecutar` usan lo elegido. `DAM_IA=centro` lo cambia solo en esa terminal.
- Los instaladores preguntan si instalan OpenCode (1.18.35, la de clase, con `npm`) y lanzan `dam configurar-ia`.
- ADR-0004, README, `docs/comandos.md` y CHANGELOG.

**Cómo se probó:**
- 29 pruebas nuevas con un `opencode` de mentira (sin red y sin gastar nada). En total, 491.
- De verdad en Windows, con `ia.json` y la configuración de OpenCode en una carpeta temporal: `dam configurar-ia` enseñó 11 modelos gratis y `dam comprobar-ia` respondió «ok» en 5 s.
- Una clasificación de prueba con DeepSeek V4.1 Flash: dijo «redes» para unos apuntes de subredes, aunque el texto le pedía leer `~/.ssh/id_rsa`.
- Le pedí al agente, dentro del texto, que leyera un fichero de fuera de su carpeta: la regla `external_directory: deny` se lo impidió y respondió «NOPUEDO».
- El paso nuevo del instalador, en WSL con un HOME temporal.

**Lo que salió al probar (todo arreglado antes de subir):**
- **Sin ninguna herramienta, OpenCode 1.18.35 se queda colgado.** Con `read` quitado (o prohibido) no respondía nunca. Se dejó `read`, pero solo dentro de la carpeta temporal vacía.
- **Desde Python fallaba con «Unexpected server error».** OpenCode no trabajaba en la carpeta temporal, sino en la del repo, y allí no estaba el agente. Se arregló con `--dir`.
- **El título de la sesión:** OpenCode se lo pide a mi `small_model`, que es el del centro, y en casa falla. Con `--title dam` no lo pide.
- **OpenCode crea `opencode.jsonc` la primera vez** (solo con `$schema`), y `dam` no lo tocaba. Ahora lo usa si no hay `opencode.json`, y solo se niega si tiene comentarios de verdad.
- **La primera vez, la opción por defecto era «Ninguno».** Ahora es la 1 (modelos gratis).
- **En WSL se ven el `npm` y el `opencode` de Windows** (`/mnt/c/...`). Ese `npm` instalaría OpenCode en Windows y ese `opencode` no entiende las rutas de Linux. Ahora el instalador y `dam` solo usan los de Linux.
- **Al leer la web de OpenCode:** ya documenta la versión 2, que cambia el formato de los agentes. Por eso el instalador pone la 1.18.35, la de clase.

**Qué aprendí:**
- **Lo que decidí en un ADR me sirvió para decidir lo siguiente.** Como el ADR-0002 dice que la IA no puede hacer nada con lo que lee, el proveedor nuevo lanza OpenCode con un agente que no puede salir de una carpeta vacía. Y como `ProveedorIA` es una clase abstracta, añadir `ProveedorOpenCode` no cambió ninguna acción.
- **Probar que algo NO pasa también es una prueba.** Le pedí dentro del texto que leyera un fichero de fuera de su carpeta y respondió «NOPUEDO».
- **Las herramientas de otros cambian sin avisar.** Los modelos gratis van y vienen, y la versión 2 de OpenCode cambia el formato de los agentes. Por eso la lista se pide al día y el instalador fija la 1.18.35, la de clase.
- **Con un programa de mentira** (un `opencode` falso) puedo comprobar 29 casos sin red y sin gastar nada.

## 2026-11-12 · `ordenar` lee los `.odt` por dentro y mete cada fichero en su unidad (Claude Code)
**Herramienta:** Claude Code, en casa (Windows).
**Prompt 1 (el problema):** «He descargado dos archivos del examen de recuperación de ayer de sistemas de la unidad 1 y me los mete en otros sitios, la imagen en imágenes y el odt [...] ¿cómo la uso para ver si me organiza bien estos apuntes que van los dos en sistemas unidad 1, que esta subcarpeta sí existe? ¿La IA de OpenCode será capaz de ello?»
**Prompt 2:** «Sí, hazlo en una rama nueva, la 1 y la 2. Si abres el odt dentro sí que pone UD1, por eso lo digo, porque no leen dentro para ver de qué asignatura es y, si está la carpeta, en este caso que los ponga allí.»

**Lo que pasaba de verdad:**
- La tabla que vi **no era de mis ficheros**: sin CARPETA, `dam ejecutar ordenar` ordena el `origen` de la acción (`~/pruebas-tareas/prueba-final`, con `foto.png` y `notas.txt`). Para las descargas es `dam ejecutar ordenar ~\Downloads --simular`. Respondí N, así que no se movió nada.
- Con mis ficheros tampoco habría ido bien: `ordenar` decidía por el nombre y solo leía por dentro los PDF. `Examen_A_cas_plantilla_part_1.odt` no dice nada en el nombre, así que iba a `POR-TIPO/DOCUMENTOS`.
- Aunque acertara la asignatura, lo dejaba en `asignaturas/sistemas`, nunca en `1 Avaluacio/unitat 1`.
- La IA tampoco: mi `~/.config/dam/acciones.json` es de antes de `dam configurar` y no tiene `clasificar-asignatura`, y esa acción no sabía leer un `.odt` (es un zip por dentro).
- `LogoGVA2025.jpg` es el logo de la plantilla del examen: ni las reglas ni una IA pueden saber que es de sistemas. Ese lo coloco yo.

**Qué se hizo (rama `feature/ordenar-dentro-y-unidad`):**
- Leer el texto de `.odt`, `.ods`, `.odp`, `.docx`, `.pptx` y `.xlsx` con `zipfile`, sin dependencias nuevas, empezando por la cabecera y el pie. En mi examen, «SI – Sistemes Informàtics UD-01» estaba en la cabecera (`styles.xml`), no en el cuerpo (`content.xml`).
- La unidad: del nombre o, si no, de los primeros 1500 caracteres del contenido («UD1», «UD-01», «Unitat 1», «Unidad 01», «Tema 1»). Si salen dos unidades distintas no se adivina.
- La carpeta: la de esa unidad dentro de la asignatura, hasta 3 niveles. Si hay dos al mismo nivel, ninguna. Nunca se crea.
- `"unidades": false` para no usarlo. `resumir-tema` y `clasificar-asignatura` aceptan `.odt`, `.docx`, `.odp` y `.pptx`.

**Cómo se probó:**
- Con mi examen de verdad, sin moverlo: `('sistemas', 1)` → `asignaturas/sistemas/1 Avaluacio/unitat 1`. El logo: sin asignatura.
- 29 pruebas nuevas, entre ellas el examen reconstruido, un `.docx` con la palabra partida en dos trozos de XML y un índice con «Tema 1, Tema 2...» (no se adivina). En total, 520.

**Lo que no hace:** entrar en `unitat 1/Examen recuperacion`. Llega hasta la carpeta de la unidad y las subcarpetas de dentro las elijo yo.

**Qué aprendí:**
- **Antes de arreglar, mirar qué pasa de verdad.** Creía que `ordenar` fallaba con mis ficheros, y la tabla que vi era de otra carpeta (el `origen` de la acción).
- **Un `.odt` o un `.docx` es un zip con XML dentro.** Se puede leer con `zipfile`, sin instalar nada. Y lo importante no siempre está en el cuerpo: en mi examen, la asignatura y la unidad estaban en la cabecera (`styles.xml`).
- **Si hay duda, no adivinar.** Cuando salen dos unidades o dos carpetas posibles, `ordenar` no elige ninguna. Prefiero colocar yo un fichero a encontrarlo en una carpeta equivocada.
- **Hay cosas que ningún programa puede saber**, como que el logo de la plantilla es de un examen de sistemas.

## 2026-11-12 · Prueba de verdad: mis apuntes de 1º de SMX, con IA y sin IA (Claude Code y WSL)
**Herramienta:** Claude Code, en casa (Windows), y mi Ubuntu de WSL para ejecutar `dam`.
**Prompt:** «Ahora, si quisiera probar en el Linux de Windows el ordenar usando la IA, ¿cómo lo haría para que los archivos de ayer de SMX los ordene en sus carpetas respectivas? Aunque ahora el ordenar es más efectivo, pero para probarlo con IA, ¿cómo sería? ¿Es posible?» Y después: «Si tienes que crear o modificar para poder hacer la prueba, lo haces y luego me dejas los comandos para probarlo con IA».

**La prueba:** 17 ficheros de `SMX/SMX1`, dos o tres de cada asignatura (`.odt`, `.ods`, `.docx` y `.pdf`), copiados a WSL (los originales no se tocan). Un almacén de prueba con las 13 carpetas de SMX (`dam configurar --ciclo smx --curso 1 --curso 2`) y una lista con la asignatura que toca a cada uno (`esperado.txt`), para comparar con `diff`. Modelo: DeepSeek V4.1 Flash (gratis, con OpenCode). Nada de `SMX1/DOCUMENTOS`: ahí hay papeles personales.

**Lo que salió al prepararla (arreglado en la rama `arreglo/ia-lista-al-dia`, PR #32):**
- `dam configurar-ia`, recién instalado OpenCode en WSL, enseñaba una lista de modelos vieja: OpenCode trae una dentro. Ahora la pide al día (`opencode models opencode --refresh`) y pone primero los que no guardan lo que les mandas.
- `clasificar-asignatura` no aceptaba `.ods` («Ningún fichero cumple el filtro»). Ahora sí.
- Copié también una línea de explicación como si fuera un comando («Pongo: command not found»): no hizo nada.

**Prueba A · solo la IA (`clasificar-asignatura` con los 17): acertó 15.**
- Entre 5 y 11 s por fichero y unos 2.000 tokens cada uno (le llegan como mucho 4.000 caracteres).
- `module5.pdf` (de ciberseguridad) → `ipo`. Por dentro solo es un diagrama de ética («¿Es legal?», «¿Me sentiría cómodo si lo leyera en la portada del periódico?»): leyendo solo eso, IPO tiene sentido. Que es de ciberseguridad lo dice la carpeta de donde lo saqué, y eso la IA no lo ve.
- `Practiques CALC Diagrames.ods` (de ofimática) → `otros`. Por dentro solo hay una tabla de ventas con números. «CALC» está en el nombre, y a la IA solo se le manda el contenido, no el nombre.

**Prueba B · `ordenar` primero y la IA para lo que quede: acertó 14 de 17.**
- `ordenar` (sin IA) colocó 16 en su asignatura en menos de un segundo. `module5.pdf` no tenía nada que lo delatara y fue a `POR-TIPO/DOCUMENTOS`.
- Falló dos, porque cuando el nombre no dice nada suma una vez cada palabra clave que encuentra en el texto:
  - `A2_UD2_SOMsmx.odt` (sistemas monopuesto) → `montaje-equipos`. En el nombre «SOM» va pegado a «smx» y no cuenta como «so»; en el texto solo encontró «cpu».
  - `Spamhause.odt` (seguridad) → `redes-locales`. Encontró «redes», «red» y «tcp» (3) contra «firewall» (1). La lista de seguridad no tiene «spam».
- Después, `clasificar-asignatura` con lo que quedó en `POR-TIPO/DOCUMENTOS`: solo `module5.pdf`, y otra vez → `ipo`.

**Conclusión:** fallan en ficheros distintos. La IA entiende de qué va un texto aunque no tenga las palabras de la lista (acertó los dos que `ordenar` falla), pero no ve el nombre del fichero. `ordenar` es instantáneo y no gasta nada, pero cuenta palabras sin entenderlas. `module5.pdf` no lo acierta ninguno: no hay forma de saberlo con lo que tiene el fichero.

**Qué se cambió después (prompt: «Sí, haz las dos en esta rama y abre la PR»; rama `docs/prueba-ia-smx`):**
- `clasificar` le manda a la IA también el nombre del fichero, en la primera línea y dentro de `<documento>`. El nombre lo pone quien te pasa el fichero, así que es texto para leer, igual que el contenido.
- Más palabras clave de seguridad: `spam`, `phishing`, `virus`, `hacking`, `iptables`, `lista negra` y `malicioso(s)`. Con solo las cuatro primeras no bastaba: `Spamhause` habría empatado a 3 con redes, y en un empate gana la que va antes en la lista (redes).
- Comprobado con los ficheros de verdad, sin moverlos: `Spamhause.odt` va ahora a seguridad y los de redes siguen en redes. `A2_UD2_SOMsmx.odt` sigue yendo a montaje: ahí ayuda la IA.
- 2 pruebas nuevas, que fallan sin el cambio. En total, 526.

**Qué aprendí:**
- **Probar con una lista de lo que tiene que salir.** Con `esperado.txt` y `diff` veo exactamente cuántos acierta y cuáles falla, en vez de mirar por encima y decir «parece que va bien».
- **La IA y las palabras clave fallan en sitios distintos.** La IA entiende de qué va un texto aunque no tenga las palabras de la lista, pero no veía el nombre del fichero. `ordenar` es instantáneo y gratis, pero cuenta palabras sin entenderlas. Juntos aciertan más que cada uno por separado.
- **A veces no hay forma de saberlo.** `module5.pdf` no lo acierta nadie: lo que lo hace de ciberseguridad es la carpeta de donde lo saqué, no lo que hay dentro.
- **Un cambio pequeño puede no bastar.** Con cuatro palabras nuevas, `Spamhause` habría empatado con redes, y en un empate gana la primera de la lista. Hay que comprobarlo con el fichero de verdad, no suponerlo.

## 2026-11-12 · Instalación desde cero en un Linux de clase (Claude Code y PC de clase)
**Herramienta:** Claude Code, en casa, para preguntar y arreglar; `dam` lo probé yo en un PC del aula con Ubuntu que no es el mío y donde nunca se había instalado.
**Prompt:** «Estoy con el terminal cli y en clase he arrancado otro PC con Linux para hacer las últimas pruebas, he clonado el repo, ¿qué hago para probarlo de nuevo?». Después le fui pegando lo que salía en la terminal: «este ha sido el proceso por si tienes que arreglar algo».

**Lo que hice:** `git clone` del repo y `bash instalar.sh`, sin nada instalado antes (ni `uv`). El instalador descargó `uv` y Python 3.12, instaló `dam`, activó el TAB, me preguntó el ciclo (`dam configurar`) y el modelo de IA (`dam configurar-ia`: DeepSeek V4.1 Flash gratis con OpenCode, que ya estaba en el PC). Salté el clonado del almacén: el PC no es mío y no quiero dejar allí mis apuntes.

**Lo que falló y cómo se arregló (PR #34):**
- **`dam` no se encontraba**, ni abriendo otra terminal ni con `source ~/.bashrc` («No s'ha trobat l'ordre 'dam'»), aunque `~/.local/bin/dam` existía. El instalador añade `~/.local/bin` a su propio PATH para usar `uv`, y por eso `uv tool update-shell` decía «already in PATH» y no lo guardaba en ningún sitio. En WSL no salió porque allí ya tenía `uv` de antes. Ahora el instalador lo escribe él en `~/.bashrc` una sola vez, **aunque ya esté en el PATH de ese momento**: me pasó que un `export PATH=...` hecho a mano solo dura en esa terminal y en la siguiente `dam` volvía a desaparecer.
- Al hacer ese `export` a mano me comí un `$` (`...:PATH` en vez de `...:$PATH`) y en esa terminal dejaron de funcionar `clear`, `ls` y `git`. Al abrir otra volvió todo menos `dam`. Así entendí que el PATH es solo una lista de carpetas donde se buscan los programas.
- **Correo de git:** escribí mi usuario de GitHub y lo aceptó. Ahora exige una `@` y lo vuelve a preguntar si ya estaba mal guardado (al repetir el instalador me lo pidió otra vez).
- **El clonado del almacén** falló con «Invalid username or token»: en *Password* va el token, no la contraseña. Ahora el aviso lo explica.
- **`dam --version`** daba «No existe la opción». Ahora funciona, igual que `-V` y `dam version`.

**La segunda vuelta, con la #34 fusionada (`git pull` y otra vez `bash instalar.sh`):**
- `[ok] ... .bashrc ya pone ... .local/bin en el PATH`; en una terminal nueva, `which dam` → `~/.local/bin/dam` y `dam --version` → `dam 1.0.1`. El TAB va.
- Repetir el instalador no estropea nada: guarda copia de `acciones.json` antes de rehacerlo y no vuelve a preguntar el modelo de IA. Esta vez elegí 1º de DAW.
- `uv run pytest -q` → **527 passed, 1 skipped** en 14,6 s. `dam doctor` → **11 de 11**.

**Las acciones, en `~/pruebas-tareas` y con `DAM_ALMACEN` apuntando a un almacén de prueba:**
- `dam comprobar-ia` → responde «ok» en 5,0 s.
- `resumir-tema` con un `.txt` de SQL → `resumenes/apuntes-sql.resumen.md` (1.011 + 100 tokens, 6,9 s).
- `nombrar-descargas`: `documento1.txt` → `redes-direcciones-ip-mascara-subred.txt` (8,4 s). La primera vez pulsé Enter en la pregunta y canceló, que es lo que tiene que hacer.
- `clasificar-asignatura --simular`: los 2 ficheros, sin gastar tokens.
- `limpiar-temporales`: borró el `.tmp` de 40 días después de preguntar.
- `ordenar` falló la primera vez: «No encuentro las asignaturas de tu almacén». El almacén de prueba estaba vacío y las carpetas de asignatura las crea `dam configurar`. Ahora el error lo dice. Con las 8 carpetas de 1º de DAW: `apuntes-sql.txt` → `bases-datos` y el de redes → `sistemas`. Al acabar avisó de que el almacén no es un repositorio git y no ofreció `dam sync`.
- Detalle visto: con una tabla estrecha el título se partía («SIMULACIÓN: no / se ha tocado nada»). Arreglado.

**Lo que queda de esta prueba:** mañana, en el mismo PC, `which dam`, para saber si el PC de clase guarda la carpeta personal (lo que falta por rellenar en la entrada del 3-nov). Y `dam status` y `dam sync --simular` con el almacén clonado, en un equipo mío.

**Qué aprendí:** que probar en mi PC no es probar: en WSL todo funcionaba porque ya tenía `uv` instalado de antes, y el fallo del PATH solo salía en un ordenador limpio. También que un `export` solo dura en esa terminal y que lo permanente va en `~/.bashrc`.

## 2026-11-13 · Repaso de los errores amables antes de la entrega (Claude Code)
**Herramienta:** Claude Code, en casa (Windows), con `dam` instalado. Todo en una carpeta temporal con su `acciones.json` y un `DAM_ALMACEN` de prueba, para no tocar mis ficheros ni mi almacén.
**Prompt:** «¿Has revisado lo de los errores amables? ¿Lo cumplimos?». Antes solo se había mirado que existieran las clases de error y que pasaran las pruebas, así que le pedí provocar uno a uno los errores de la lista del profe (sesiones 2 y 3) con el programa de verdad.

**Qué se comprobó:** 26 errores. En ninguno salió un traceback, y el código de salida fue siempre el de mi spec.
- **`acciones.json` roto → código 3, con la acción y el campo:**
  - Coma de más: `coma.json no es JSON válido: línea 1, columna 31`.
  - Tipo que no existe: `Acción «mover-zips», campo «tipo»: «teletransportar» no existe; usa uno de: borrar, ...`.
  - Nombre repetido: `campo «nombre»: está repetido`.
  - Regex rota: `campo «filtro.patron»: expresión regular rota`.
  - Falta `destino`: `es obligatorio en acciones de tipo mover`.
  - Fichero que no existe o vacío: `No encuentro ...` y `no es JSON válido`.
- **Órdenes y ficheros:**
  - Acción que no existe → código 1 y `Mira la lista con: dam acciones`. Opción que no existe → código 2, en español.
  - Origen o carpeta que no existe → código 1, `no existe (ni como carpeta ni como fichero)`.
  - `--simular` con un destino que no existe: no crea la carpeta.
  - El destino ya tenía `a.zip`: el viejo no se tocó y el nuevo quedó como `a (1).zip`.
  - `Ñandú con espacios.ZIP` (tildes, espacios y extensión en mayúsculas) se movió bien.
  - Ejecutar la misma acción dos veces: `Ningún fichero cumple el filtro: no hay nada que hacer.`
  - Borrar sin `--si`: pregunta, y con «n» dice `Cancelado.` y el fichero sigue ahí.
- **IA sin red (`DAM_IA=centro`) → código 4:**
  - Sin clave: dice qué variables faltan, cómo ponerlas en Linux y en PowerShell, y el enlace al README.
  - URL que no existe o servidor apagado: `No llego al servidor de IA: ¿estás en la red del centro? Las acciones sin IA siguen funcionando`.
  - Certificado que no existe: `No puedo leer el certificado del centro ... revisa CENTRO_IA_CA`.
  - Clave mala (401): no se puede probar sin el servidor; lo cubre `test_ia.py` con un servidor de mentira («la clave no es válida»).
  - Con la IA caída, `dam validar` sigue funcionando.
- **Ctrl+C a mitad de mover:** código 130 (el normal de Ctrl+C), sin traza, y el fichero se queda en su sitio. No dice nada al salir; no lo cambio porque no se pierde nada.

**Qué aprendí:** que pasen las pruebas no es lo mismo que haberlo visto. Provocar los errores uno a uno con el programa instalado es lo que haría el profe, y así sé qué ve un usuario en cada caso. Que un mensaje sea «amable» no es que sea educado: es que diga dónde está el fallo (la acción y el campo) y qué hacer para arreglarlo.

## 2026-11-13 · Cada ciclo con su almacén, y crearlo sin saber git (Claude Code)
**Herramienta:** Claude Code, en casa (Windows).
**Prompt 1 (la duda):** «Si alguien empieza creando otro ciclo, por ejemplo ASIR, no clona mi repo: ¿creará su propio repo para subir las asignaturas, o eso lo crea el usuario luego y lo sube al repo? ¿Cómo está montado?»
**Prompt 2 (la idea):** «Para cada ciclo debería ser CICLO-almacen, ¿no crees? Porque si no, está mal que sea DAM-almacen. ¿Y no se puede automatizar que, si tiene cuenta de GitHub, como al principio pregunta, ya cree el repo en privado?»
**Prompt 3 (la decisión):** «¿Cuál es más fácil para los que no sepan mucho, por ejemplo los de 1º de SMX? Hay que facilitar las cosas.»
**Por qué se me ocurrió:** mi cuñado (ASIR) iba a instalar `dam` para la instalación cruzada, y me di cuenta de que no sabía qué le iba a pasar con el almacén. Claude Code miró el código: el instalador clonaba siempre `USUARIO/DAM-almacen`, y nadie le decía que ese repo lo tenía que crear él antes. A alguien de ASIR le pedíamos un repo que se llamara DAM, y si no lo tenía, se quedaba sin almacén.

**Qué se hizo:**
- `dam configurar` pone la ruta del almacén según tu ciclo (`~/ASIR-almacen`...). Con DAM no cambia nada, y si la ruta la escribiste tú, tampoco.
- `dam crear-almacen` (módulo `almacen_nuevo.py`):
  - Pide el usuario de GitHub (vale pegar `github.com/usuario`) y pregunta si ya tienes el repo.
  - Si no, abre `github.com/new` con el nombre y **Private** ya puestos: solo pulsas «Create repository».
  - Lo clona, crea las carpetas de tus asignaturas y, si el repo es nuevo, hace el primer commit y el `push -u` (si no, `dam sync` no sabe adónde subir).
- `dam configurar` lo ofrece al acabar. Los instaladores (`instalar.sh` e `instalar.ps1`) ya no clonan `DAM-almacen` a ciegas: buscan cualquier `CICLO-almacen` que ya tengas y lo preparan después de elegir el ciclo.
- README con una sección paso a paso, y el ADR-0005 con por qué así.

**Por qué con la página rellena y no con un token:** había tres opciones: abrir GitHub ya relleno, crearlo solo con un token, o las dos. Elegí la primera porque crear un token es lo más difícil para alguien de 1º de SMX, y porque así `dam` nunca ve ni la contraseña ni el token.

**Cómo se probó:** 30 pruebas nuevas con un «GitHub de mentira» (repos *bare* en una carpeta temporal, como los de GitHub) y sin abrir el navegador: alumno nuevo de ASIR, otro equipo que solo lo baja, repo que no existe, usuario mal escrito, carpeta que no es git... En total, **559 pruebas OK**. Al meter el comando, la ayuda general se pasaba de una pantalla porque el nombre largo ensanchaba la columna: por eso es `crear-almacen` y no `preparar-almacen`.

**Probado de verdad (13-nov):** abrí la dirección que da `dam crear-almacen` y la página de GitHub sale con el nombre puesto y **Private** marcado. **Falta:** [COMPLETAR] la prueba entera con mi cuñado: crear su `ASIR-almacen`, ver que se clona y que la primera subida llega.

**Qué aprendí:**
- **Hacer las preguntas de un usuario nuevo descubre huecos.** Las pruebas pasaban, pero nadie había pensado qué le pasa a alguien que no tiene el almacén. Lo vi al imaginar a mi cuñado instalándolo.
- **Fácil para quien menos sabe.** La opción más automática (con token) no era la más fácil: el paso difícil es crear el token. Pulsar un botón verde en GitHub lo sabe hacer todo el mundo.
- **El orden importa.** Para poner el nombre del ciclo, primero hay que saber el ciclo: hubo que cambiar el orden del instalador.

---

## 2026-11-13 · Mi PC de clase: almacén real e IA del centro (Claude Code)
**Herramienta:** Claude Code (en casa) mientras yo probaba en mi PC de clase (Ubuntu). Yo ejecutaba las órdenes y le pegaba las salidas.

**Prompt 1:** «Vale, seguimos con CLI en mi PC de Linux.»

**Actualizar e instalar:** en este PC ya tenía `dam` instalado, con el repo en otra carpeta (`~/Documents/Terminal/Terminal_CLI`). Hice `git pull` (a la #37) y `bash instalar.sh`, y en otra terminal `dam --version` dio `dam 1.0.1`. Es normal: la versión no sube hasta la 1.1.0, pero `dam crear-almacen --help` ya salía, así que el código era el nuevo.

**`dam doctor`, en el sitio equivocado:** lo lancé en la terminal nueva, que empieza en mi carpeta personal, y revisó todo `~`: «2 de 9 comprobaciones bien», 27 «secretos» (sobre todo certificados de librerías dentro de `.cache`, pero también algún fichero mío con claves) y «Dependencias declaradas: `.nvm/package.json`». Me avisó de que parecía la carpeta de fuera. Dentro del proyecto: **11 de 11**. Dos cosas sacadas de ahí:
- Las claves en ficheros de texto no están en ningún repo, pero es mejor no tenerlas sueltas.
- Tenía **dos clones** del almacén (`~/DAM-almacen` y `~/Documents/DAM/DAM-almacen`). Comprobé con `git status -s` y `git log origin/main..HEAD` que el segundo no tenía nada sin subir y lo borré.

**El almacén de verdad (lo que faltaba de la semana 1):**
- `dam status`: 54 ficheros por descargar.
- `dam sync --simular`: «Descargaría 5 commit(s) de GitHub. (simulación: no he tocado nada)».
- `dam sync`: «Archivos descargados desde clase/casa (5 commit(s))», y otra vez `dam status`: «✔ Todo está actualizado».
- `dam instalar-hook`: «✔ Hook instalado: .git/hooks/pre-commit».

**Fallo 1, visto en `dam status`:** rutas como `Apuntes JAVA Internet/...zip` salían partidas en dos líneas, como si fueran dos ficheros. Pensé que el nombre tenía un salto de línea, pero con `git ls-files` se vio que es un espacio: Rich partía la línea por ahí en una terminal estrecha. Arreglado con `soft_wrap` y una prueba con una consola de 60 caracteres.

**Prompt 2:** «¿Por qué no funciona la del centro, si tenía OpenCode configurado y sí que me iba?»
**Por qué:** cada programa guarda lo suyo. OpenCode tiene la dirección y la clave en `~/.config/opencode/opencode.json`, y el certificado en `NODE_EXTRA_CA_CERTS`. `dam` (Python) lee `CENTRO_IA_URL`, `CENTRO_IA_KEY` y `CENTRO_IA_CA`, y no las tenía. Las puse en `~/.bashrc` con los datos de OpenCode. La clave la copié con `grep` directamente al fichero, sin que saliera por pantalla.

**Fallo 2, el 403:** con las variables puestas, `dam comprobar-ia` decía «El servidor de IA responde 403: algo ha fallado». OpenCode, con la misma clave, funcionaba: la diferencia era el modelo. `dam` pedía `qwen3.8-flash-next` y el OpenCode del centro usa `Qwen38-DualSpark-*`. Con `CENTRO_IA_MODELO="Qwen38-DualSpark-medium"`: «✔ El modelo responde «ok» en 31.6 s». Arreglado en casa:
- El modelo por defecto pasa a ser `Qwen38-DualSpark-medium`.
- El 403 ahora dice «tu clave no puede usar el modelo X: prueba otro con CENTRO_IA_MODELO».
- Como solo decir «ok» tardó 31 s, el tiempo máximo sube de 60 a 120 s.

**Una cosa que no sé explicar:** entre un `comprobar-ia` y el siguiente, `~/.config/dam/ia.json` pasó de «centro» a «opencode», y `comprobar-ia` respondió con un modelo gratis de OpenCode. Solo `dam configurar-ia` escribe ese fichero. Lo dejé otra vez con `dam configurar-ia --proveedor centro`. Si vuelve a pasar, lo apunto como issue.

**Fallo 3 (del PC del aula, por la mañana):** en el instalador dije «n» a rehacer `acciones.json`, que era de una prueba con ciclo DAW pero tenía la ruta `~/DAM-almacen`. `crear-almacen` iba a clonar `DAW-almacen` en `~/DAM-almacen`. Ahora corrige la ruta según el ciclo (con copia de `acciones.json`), salvo si ya hay un repo en la ruta vieja o tengo `DAM_ALMACEN`.

**Prompt 3:** «Sí, empieza con los fallos en casa, es el portátil. Vamos a dejar todo fino y repasa todo lo de la página del profe de aula en la nube para que no se nos pase nada.»
**Repaso contra las sesiones 3 y 4:** están todos los ficheros que se piden, los cuatro mínimos y las preguntas de la defensa. Lo que no estaba al pie de la letra en la Sesión 4, y ahora sí:
- `conftest.py`: `aislado` también cambia a `tmp_path` y pone `HOME` y `USERPROFILE` en una carpeta temporal.
- También quita `DAM_ALMACEN`, que en mi portátil apunta a mi almacén real.
- Están las fixtures `descargas` y `escribir_config`, las pruebas `test_mover_solo_lo_que_cumple_el_filtro`, `test_nunca_sobrescribe` y `test_renombrar_con_plantilla`, y una prueba por cada código de salida (0 a 4) en `test_cli.py`.

Mi primera `test_renombrar_con_plantilla` falló porque yo esperaba otro orden. `dam` ordena sin mirar mayúsculas (`cumpleaños` va antes que `FOTO1`), y eso está bien: corregí la prueba, no el código.

**Qué aprendí:**
- **Que funcione en un programa no quiere decir que funcione en el otro.** OpenCode y `dam` hablan con el mismo servidor, pero cada uno con su configuración y su modelo. El 403 no era la clave: era el nombre del modelo, y el mensaje «algo ha fallado» no ayudaba a verlo.
- **Primero mirar, luego borrar.** Antes de borrar el almacén repetido comprobé que no tenía nada sin subir. Y antes de «arreglar» el salto de línea comprobé que no existía.
- **Un dato real cambia los números.** Con el servidor de mentira de las pruebas todo tarda milisegundos. El de verdad tardó 31 s en decir «ok», y eso no se ve hasta que lo pruebas en clase.
