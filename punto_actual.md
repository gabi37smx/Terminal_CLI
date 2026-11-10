# Punto actual del proyecto

> **Cambio de nombre (27/10 noche):** el comando ya NO es `gabriel` (chocaba con otra herramienta de tu terminal), ahora es **`dam`**. Variable del almacén: `DAM_ALMACEN`. Config global: `~/.config/dam/acciones.json`.

**Fecha:** 2026-11-06 (en casa, Windows)
**Proyecto:** `dam` / paquete `tareas` (carpeta `Terminal_CLI`)
**Repo:** https://github.com/gabi37smx/Terminal_CLI
**Estado:** `main` en GitHub hasta `2f59e1d` (6-nov): los tres comandos nuevos (`doctor`, `pendientes` y `entregar`) y los arreglos del TAB entraron con el **PR #3** (rama `feature/doctor-entregar-pendientes`, commit `0893964`, subida por Claude Code porque se lo pedí; la fusión la hice yo). Antes: instalador (`40ff2e5`), `dam help` (`7e62593`) y TAB (`1f34747`), del 3-nov; la rama `feature/seguridad-y-web` entró con el PR #2 (1-nov). Para comprobar que no queda nada sin subir: `git log --oneline origin/main..` (si no sale nada, está al día).
**Tests:** `uv run pytest -q` → **353 passed, 1 skipped** (11-nov, desde la raíz).
**Estado (11-nov):** `main` al día con `dam inventario` (PR #4), `dam duplicados` (PR #5) las palabras de arquitectura en `sistemas` para `ordenar` (PR #6: «UD-01-ARQUITECTURA VON NEUMANN.pdf» iba a programación por la palabra «funció»), `dam readme` (PR #7), la ayuda en tabla + `ordenar` al almacén con `dam sync` al acabar (PR #8) y el plan B de `ordenar` a `POR-TIPO` (PR #9).
**Carpeta nueva (10-nov):** el repo está ahora en `C:\Users\HP\Datos\REPOS\TERMINAL_CLI` (antes en el Escritorio). `dam` se reinstaló desde aquí con `uv tool install --editable . --force`.

## Qué hay hecho

### Semana 1 (terminal y primera orden)
- [x] Terminal, herramientas (git, uv, Python 3.12, OpenCode 1.18.35) y proyecto con uv.
- [x] `.gitignore` (con `.env`) y `.gitattributes` desde el primer commit.
- [x] `opencode.json` y `AGENTS.md`.
- [x] Spec v0 en el README, `dam version` y `dam listar`; instalado con `uv tool install --editable .`.
- [x] Más de 10 commits; ya hubo una rama y un pull request (#1, `feature/cli-listar`).

### Semana 2 (acciones.json y motor)
- [x] `acciones.json` con mis 3 acciones: `ordenar`, `limpiar-temporales`, `convertir-webp` (sustituye a `tareas.toml`).
- [x] `errores.py`, `config.py` (valida todo antes de tocar nada), `acciones.py` y `motor.py` (clase base con fábrica y una clase por tipo).
- [x] `cli.py`: `--config`, `listar`, `validar`, `acciones`, `ejecutar --simular/--si`, `status`, `sync`.
- [x] `docs/adr/0001-configuracion-externa.md` en primera persona (corregido: la conversión es solo de JPEG y PNG).
- [x] `.opencode/skills/acciones-json/`, `.opencode/commands/nueva-accion.md` y `.opencode/agents/revisor.md`.
- [x] Almacén privado `DAM-almacen` y `dam sync` seguro (guardián de `.env`).
- [x] Ayuda estilo terminal: `dam`, `dam -h`, `dam COMANDO -h`.

### Seguridad (rúbrica: cero claves en el repo y su historial)
- [x] `dam scan-secrets`: `dam scan-secrets` y `dam scan-secrets --historial` salen limpios en `DAM-almacen` y en `Terminal_CLI` (comprobado el 1-nov).
- [x] `dam instalar-hook`, `dam test-links` y `dam check-headers`, con sus tests; aserciones en `acciones.py` y `motor.py`; `docs/prompts.md`; README, `docs/comandos.md` y `AGENTS.md` actualizados. Subido con el PR #2 (1-nov).
- [x] Hook de `scan-secrets --staged` activo en `Terminal_CLI`: revisó los commits del 3-nov.
- [x] `dam test-links` y `dam check-headers` probados contra el portfolio y el backend de Render (resultados en `docs/prompts.md`).
- [x] Backend con `helmet`: `check-headers` en Render pasa de 0 de 6 a **6 de 6**, desplegado y comprobado (`docs/demo.md`).
- [x] `Sesion1.md` (material del profesor) fuera del repo y en `.gitignore` (3-nov). Sigue en el historial antiguo.
- [x] 4.ª y 5.ª acción (3-nov, con Claude Code): `renombrar-capturas` (renombrar) y `copiar-entregas` (copiar). `dam validar` → 5 acciones válidas; probadas en `~/pruebas-tareas/acciones-nuevas`, primero con `--simular` y después **de verdad** (3-nov, lo lancé yo con `dam --config <ruta>\acciones.json ejecutar …`): 3 hechos y 0 con error en cada una. Las capturas quedaron como `captura_2026-11-03_001.png`, `_002.png` y `_003.jpg`, y las 3 entregas se copiaron a `~/pruebas-tareas/entregas` sin tocar los originales. Ojo: `{fecha}` es la fecha de modificación del fichero, no la del nombre, y el patrón distingue mayúsculas (`captura…` en minúscula no entra).
- [x] 6.ª acción (3-nov, OpenCode): `mover-zips`, antes `comprimir-zips`, (mover) mueve los `.zip` a `comprimidos/`. `dam validar` → 6 acciones válidas; probada con `--simular` en `~/pruebas-tareas/prueba-final` (2 simulados, 0 errores) y `uv run pytest -q` → 162 passed. Probada **de verdad** (3-nov, la lancé yo): 2 hechos y 0 con error; los dos `.zip` están en `comprimidos/`. Revisada con `@revisor`; sus avisos y las decisiones están en `docs/prompts.md`.
- [x] `acciones.json` copiado a `~/.config/dam/`: `dam` funciona sin `--config` fuera del repo. Si cambia el del repo, hay que volver a copiarlo.
- [x] `opencode --version` → 1.18.35 (3-nov), la misma versión apuntada en la semana 1. No se migra nada antes del 6 nov.

### Instalación en otros equipos (3-nov, Claude Code)
- [x] **Por qué en el PC de clase (Linux) no iba ni `dam --help` ni la subida a `DAM-almacen`:** el código está bien (un clon limpio pasa los tests). Lo que hace funcionar `dam` vive fuera del repo, en la carpeta personal de cada equipo: `uv` y `dam` en `~/.local/bin`, `~/.config/dam/acciones.json`, `~/DAM-almacen` y el token de GitHub. `git clone` no los trae.
- [x] **Instalador:** `bash instalar.sh` (Linux/macOS) y `instalar.cmd` (Windows, doble clic, lanza `instalar.ps1`). Comprueba git, instala uv, `uv sync`, instala `dam`, copia `acciones.json` a `~/.config/dam/`, pide nombre y correo de git si faltan, clona `DAM-almacen` y termina con `dam validar`. Se puede repetir: salta lo que ya está hecho. `.gitattributes` fija LF para `.sh` y CRLF para `.ps1`/`.cmd`.
- [x] **Probado en Ubuntu 24.04 (WSL), clonando desde GitHub (lo lancé yo):** todo bien menos clonar `DAM-almacen`: GitHub no acepta la contraseña, hace falta un token.
- [x] `dam help` y `dam help COMANDO` (igual que `--help`); `dam help noexiste` sale con 2.
- [x] **Autocompletado con TAB:** comandos, nombres de acciones (`dam ejecutar co<TAB>`) y asignaturas del almacén (`dam sync pr<TAB>`). Lo activan los instaladores en bash, zsh y PowerShell. Probado con un TAB real en Git Bash y PowerShell (entorno aislado); **falta probarlo en Linux de verdad**.

### Comandos para mis proyectos (5 y 6-nov, Claude Code)
Grupo nuevo en la ayuda: «Tus proyectos: revisar y entregar». Los tres solo leen, salvo `entregar`, que crea el zip. Detalle en `docs/prompts.md`.
- [x] **`dam entregar CARPETA [--destino] [--nombre] [--simular]`** (`entregar.py`): un `.zip` limpio, sin `.env`, claves, `.git`, `.venv`, `node_modules` ni `__pycache__`, y respetando `.gitignore`. Si `scan-secrets` encuentra un secreto dentro, no lo crea. Probado por mí en Electrician: 47 ficheros, 342,2 KB → zip de 143,3 KB, y `.env` y `.claude/` se quedaron fuera.
- [x] **`dam doctor CARPETA`** (`doctor.py`): 7 comprobaciones básicas (git, `.gitignore`, `.env` ignorado y sin subir, `.env.example` al día, README, secretos) y 4 recomendadas (tests, dependencias, CI, ficheros de más de 50 MB). Del `.env` solo lee los nombres. Probado por mí: Electrician **11 de 11**; `portfolio-backend` 8 de 11; `DAM-almacen` 6 de 9.
- [x] **`dam pendientes CARPETA [--quien NOMBRE] [--resumen]`** (`pendientes.py`): cuenta `[Verificado]`, `[Hipótesis]` y `[Pendiente]` en los `.md` (y los verificados sin fecha) y resume `docs/pendientes.md` por persona. Electrician: 39 verificados (15 sin fecha), 10 hipótesis y 33 pendientes; registro de 52 filas con 33 abiertas (Sergio 12 · Gabi 9 · Javi 9 · Mar 7 · Todos 3).
- [x] **Arreglo del TAB en PowerShell:** un TAB en una ruta dejaba `dam` atascado (solo imprimía líneas en blanco) hasta cerrar la ventana. El script del TAB ahora borra siempre sus variables. Mi `~/.config/dam/completado.ps1` ya está regenerado.
- [x] **Aviso de la `\` final:** `dam doctor "C:\carpeta\"` ya no dice «no existe»: explica que la `\` se come las comillas y da la orden corregida.

### Organizar el PC en `~/Datos` (10-nov, Claude Code)
Plan en 5 fases: 1 `dam inventario` → 2 `dam duplicados` (solo informa, nunca borra) → 3 `dam readme` → 4 `ordenar` con plan B por tipo (`POR-TIPO/`) → 5 la mudanza la hago yo por bloques.
- [x] **`dam inventario [CARPETA] [--guardar INFORME.md] [--top N]`** (`inventario.py`, solo lee): tamaño por carpeta, tipos, repos (y si tienen remoto), instaladores, basura, carpetas regenerables (`.venv`, `node_modules`) y ficheros de más de 100 MB. Los ficheros de OneDrive «solo en la nube» no cuentan como espacio en el disco. Probado en `~/Datos`: 73 170 ficheros en 4 s.
- [x] **Mudanza hecha** (fase 5 adelantada, con `~/mudanza-datos.ps1`): todo está en `~/Datos` con las carpetas en MAYÚSCULAS (`CURSOS`, `DAM`, `MAQUINAS-VIRTUALES`, `PERSONAL`, `POR-TIPO`, `REPOS`, `SMX`) y un README en cada carpeta hasta el tercer nivel. Dentro de los repos no se ha cambiado ningún nombre.
- [x] Los apuntes de DAM están solo en el almacén (`REPOS\DAM-ALMACEN`). En este PC, `dam` lo encuentra por la variable `DAM_ALMACEN`; `acciones.json` sigue con `~/DAM-almacen` porque es la ruta de los otros equipos.
- [x] **Fase 2 `dam duplicados [CARPETA] [--guardar INFORME.md] [--top N]`** (`duplicados.py`, solo lee): compara el contenido (SHA-256; primero por tamaño y por los primeros 64 KB, para ir rápido). Enseña primero las **carpetas que son copia de otra** (todos sus ficheros tienen copia fuera), las de fuera de los repos antes, y cada pareja una sola vez; después los grupos de ficheros repetidos, de más a menos espacio. Marca «(repo)» lo que está en un repo (eso se quita con un commit). Una carpeta con un repo dentro nunca sale como copia (su `.git` no se compara). No lee lo que está «solo en la nube». Probado en `~/Datos` (después de la limpieza a mano): 3746 ficheros, 327 grupos, 125 MB repetidos y 56 carpetas copia, en 20 s. Lo primero que sale: `SMX2/APLICACIONS WEB/APW-MAIN` repite lo del repo `APLICACIONS-WEB`, y los PDF de Java están dos veces en DAM-almacen (`entornos` y `lenguaje-marcas`).
- [x] **Fase 3 `dam readme [CARPETA] [--niveles N] [--simular] [--si]`** (`readme.py`): el apartado «## Qué hay dentro» de cada README es una tabla (📁 subcarpetas con su tamaño y la primera frase de su README, que dice «Repo git.» si lo es; 📄 archivos con tamaño y tipo; más de 15 archivos se resumen en una fila). Lo de encima del apartado (y lo que haya debajo, en otro `##`) es del alumno y no se toca; un README sin el apartado tampoco. No entra en repos (`.git`) ni en proyectos (`pyproject.toml`, `package.json`, `.venv`, `node_modules`...) y en un proyecto sin README no crea uno. Los README.md no cuentan en los tamaños y la fecha del pie no cuenta como cambio: si nada cambia, la segunda vez dice «No hay nada que hacer». Simulado en `~/Datos`: 63 a poner al día (las listas del 10-nov pasan a tabla), 0 nuevos, en 6 s.
- [x] La ayuda general tiene 38 líneas (límite: menos de 40): «dam help COMANDO» va en la línea de `dam help` y las dos del TAB son una.
- [x] Fase 4 (1.ª parte) `ordenar` al almacén: con `"al_almacen": true` (ya puesto en `acciones.json`) cada fichero va a `asignaturas/<asignatura>` del almacén (`DAM_ALMACEN` o «almacen» de acciones.json); si la asignatura no existe allí, se salta (no se inventan carpetas). Al acabar pregunta «¿Hago ahora dam sync…?» y, si dices sí, sincroniza con el mensaje `[sync]: ordenar: N apunte(s) nuevo(s)`; con `--si` no pregunta y solo lo recuerda.
- [x] Fase 4 (2.ª parte) `"por_tipo": "~/Datos/POR-TIPO"`: lo que no es de ninguna asignatura va a `POR-TIPO/<TIPO>` (los tipos de `dam inventario`, en MAYÚSCULAS; máquinas virtuales y lo desconocido a `OTROS`). La nota «por tipo» sale en la tabla y eso no cuenta para el `dam sync`. Nunca mueve `desktop.ini`, `Thumbs.db`, ocultos, temporales ni descargas a medias (`.crdownload`, `.part`), ni con plan B ni sin él.
- [x] La ayuda general (`dam`) es una tabla: tema (y para qué) · comando · qué hace, con una raya entre temas. 37 líneas; el test la mide a 120 columnas para no depender del terminal.

## Qué falta (por orden)

1. **⚠ AL LLEGAR A CLASE (Linux), lo primero:**
   - `which dam`. Si sale una ruta, `dam` sigue instalado: `cd ~/Terminal_CLI && git pull` y listo. No hace falta reinstalar: está en modo editable y el PR #3 no cambió dependencias ni instaladores.
   - Si no sale nada (el PC se restauró u otro usuario): `git clone https://github.com/gabi37smx/Terminal_CLI.git`, `cd Terminal_CLI`, `bash instalar.sh` (con el token a mano) y abrir otra terminal.
   - Comprobar: `dam help` (deben salir `doctor`, `pendientes` y `entregar`), `dam doc<TAB>`, `dam status` y `dam sync --simular`.
   - Apuntar qué pasó en `docs/prompts.md` (los **[COMPLETAR]** de la entrada del 3-nov): así se sabe por fin si el PC de clase guarda la carpeta personal.
2. **En otros equipos Windows:** después del `pull`, `instalar.cmd` otra vez para tener el TAB arreglado. En Linux/WSL no hace falta (el fallo era solo de PowerShell).
3. **Lo que han encontrado los comandos nuevos:**
   - `portfolio-backend`: añadir a `.env.example`, con el valor vacío, `GITHUB_TOKEN`, `GNEWS_API_KEY` y `Gemini_API_Key` (lo hago yo; el agente no toca ficheros `.env*`).
   - Electrician: poner fecha y fuente a los 15 `[Verificado]` sin fecha (7 en el README) y un estado a la fila 53 de `docs/pendientes.md`. Avisar al equipo de `dam pendientes --quien NOMBRE`.
   - `DAM-almacen`: añadir un README corto y sacar de git el `.zip` de más de 50 MB de `lenguaje-marcas`.
   - `Terminal_CLI`: añadir GitHub Actions que pase `uv run pytest` en cada push (lo único que le falta según `doctor`).
4. **Crear el token de GitHub** (Settings → Developer settings → Fine-grained tokens; solo `DAM-almacen`, permiso *Contents: Read and write*). No guardarlo en ningún fichero.
5. (El PC de clase está ahora en el punto 1.)
6. En Ubuntu (WSL): `git pull` en `~/Terminal_CLI` y `bash instalar.sh` otra vez para tener el TAB y clonar `DAM-almacen` con el token.
7. Probar de verdad (sin `--simular`) en `~/pruebas-tareas` las 3 acciones antiguas (`ordenar`, `limpiar-temporales`, `convertir-webp`) y apuntar el resultado. (`renombrar-capturas`, `copiar-entregas` y `mover-zips` ya están probadas de verdad.)
8. Pasar `@revisor` sobre `renombrar-capturas` y `copiar-entregas` (en `mover-zips` ya está), pasar `/review` y rellenar los **[COMPLETAR]** de `docs/prompts.md` con lo que hice en clase.
9. `dam instalar-hook` en `DAM-almacen` (en `Terminal_CLI` ya está).
10. Pendiente del portfolio: borrar o excluir `_backup_mejoras/` (67 enlaces rotos, todos ahí).
11. Instalar sin clonar con `uv tool install git+https://github.com/gabi37smx/Terminal_CLI` siguiendo solo el README (sin probar todavía).
12. **Comprobación de proceso del 6 nov (semipresencial):** 3 acciones propias funcionando, ADR y commits reales.

Ideas de comandos que quedan (de la lista del 5-nov): `revisar-web` (imágenes pesadas y `alt` en el portfolio), `informe` (juntar `scan-secrets`, `doctor`, `test-links` y `check-headers` en un `.md` con fecha) y `despertar` (despertar el backend de Render antes de una demo).

Después (semanas 3 y 4): capa IA y modo sin red (las 5 o más acciones propias ya están: hay 6), pruebas en GitHub Actions, release v1.0.

## Cómo retomar

```powershell
cd "C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\PROJECTE TERMINAL CLI\Terminal_CLI"
uv sync
uv run pytest -q
dam -h                # o: dam help
dam validar
dam status
dam scan-secrets --historial
```

En otro equipo (clase, WSL, Mac): `git clone https://github.com/gabi37smx/Terminal_CLI.git`, `cd Terminal_CLI`, `bash instalar.sh` y abrir otra terminal.

## Recordatorios

- Los commits y el push los haces tú; el agente solo commitea si se lo pides expresamente. El agente no ejecuta `sync` ni `ejecutar`.
- Probar siempre en `~/pruebas-tareas` y con `--simular` primero.
- Si se cambia `opencode.json`, cerrar y volver a abrir OpenCode.
- GitHub no acepta la contraseña en git: en *Password* va el token. En Linux, el instalador hace que git lo recuerde 8 horas solo en memoria.
- No usar `dam --install-completion` en Windows: cambia la política de PowerShell a `Unrestricted` y duplica el script en el perfil. El TAB lo activa el instalador.
- En PowerShell, nada de `\` justo antes de las comillas de cierre: `"C:\carpeta"`, no `"C:\carpeta\"`. El TAB de PowerShell la añade; `dam` ahora avisa.
- Si `dam` solo imprime una línea en blanco en PowerShell, es el script del TAB antiguo: `instalar.cmd` otra vez y abrir otra ventana.
- Al ejecutar `uv sync` desde WSL, nunca sobre la carpeta de Windows (`/mnt/c/...`): cambiaría el `.venv` de Windows por uno de Linux.
- Nada de claves en el repo ni en su historial (mínimo eliminatorio). Un repo del almacén con apuntes: privado.
- Lo que no sé explicar, no lo entrego: repasar `config.py`, `acciones.py`, `motor.py`, `escanear.py`, `web.py` y `hook.py` hasta poder explicar cada aserción, y también los tres del 5 y 6-nov (`doctor.py`, `pendientes.py` y `entregar.py`) y el arreglo del TAB en `cli.py` (por qué el `try/finally`).
