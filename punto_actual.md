# Punto actual del proyecto

**Fecha:** 2026-11-26 · **Versión publicada:** 1.3.1 (`v1.3.1`) · **Entrega:** viernes 27-nov-2026
(grupo presencial, con defensa de 5 minutos).
**Proyecto:** comando `mochila` (también `tareas`), paquete `tareas`, carpeta `Terminal_CLI`.
**Repo:** https://github.com/gabi37smx/Terminal_CLI · **Para quien corrige:** [docs/entrega.md](docs/entrega.md)
(cada punto de la rúbrica con el fichero o la orden que lo demuestra).
**Pruebas:** `uv run pytest -q` → **718 passed, 1 skipped** (26-nov, 1.3.1), y en verde en GitHub Actions
con Ubuntu, Windows y macOS.
**Historial:** más de 190 commits y 60 PR; todas, por versión y con sus issues, en
[docs/historial-pr.md](docs/historial-pr.md). Qué trae cada versión: [CHANGELOG.md](CHANGELOG.md).

> El comando se llamó `tareas` en la spec v0, después `dam` y desde el 15-nov `mochila`
> ([ADR-0006](docs/adr/0006-nombre-mochila.md)). Las entradas antiguas de este fichero y de
> `docs/prompts.md` dicen `dam` porque se escribieron entonces.

## Qué hay hecho (por semanas)

### Semana 1 (terminal y primera orden)
- [x] Terminal, herramientas (git, uv, Python 3.12, OpenCode 1.18.35) y proyecto con uv.
- [x] `.gitignore` (con `.env`) y `.gitattributes` desde el primer commit con código (`1195d31`). El primero de todos es el «Initial commit» que hizo GitHub con el README: explicado en `docs/prompts.md`.
- [x] `opencode.json` y `AGENTS.md`.
- [x] Spec v0 en el README, `mochila version` y `mochila listar`; instalado con `uv tool install --editable .`.
- [x] Más de 10 commits; ya hubo una rama y un pull request (#1, `feature/cli-listar`).

### Semana 2 (acciones.json y motor)
- [x] `acciones.json` con mis 3 acciones: `ordenar`, `limpiar-temporales`, `convertir-webp` (sustituye a `tareas.toml`).
- [x] `errores.py`, `config.py` (valida todo antes de tocar nada), `acciones.py` y `motor.py` (clase base con fábrica y una clase por tipo).
- [x] `cli.py`: `--config`, `listar`, `validar`, `acciones`, `ejecutar --simular/--si`, `status`, `sync`.
- [x] `docs/adr/0001-configuracion-externa.md` en primera persona (corregido: la conversión es solo de JPEG y PNG).
- [x] `.opencode/skills/acciones-json/`, `.opencode/commands/nueva-accion.md` y `.opencode/agents/revisor.md`.
- [x] Almacén privado `DAM-almacen` y `mochila sync` seguro (guardián de `.env`).
- [x] Ayuda estilo terminal: `mochila`, `mochila -h`, `mochila COMANDO -h`.

### Seguridad (rúbrica: cero claves en el repo y su historial)
- [x] `mochila scan-secrets`: `mochila scan-secrets` y `mochila scan-secrets --historial` salen limpios en `DAM-almacen` y en `Terminal_CLI` (comprobado el 1-nov).
- [x] `mochila instalar-hook`, `mochila test-links` y `mochila check-headers`, con sus tests; aserciones en `acciones.py` y `motor.py`; `docs/prompts.md`; README, `docs/comandos.md` y `AGENTS.md` actualizados. Subido con el PR #2 (1-nov).
- [x] Hook de `scan-secrets --staged` activo en `Terminal_CLI`: revisó los commits del 3-nov.
- [x] `mochila test-links` y `mochila check-headers` probados contra el portfolio y el backend de Render (resultados en `docs/prompts.md`).
- [x] Backend con `helmet`: `check-headers` en Render pasa de 0 de 6 a **6 de 6**, desplegado y comprobado (`docs/demo.md`).
- [x] `Sesion1.md` (material del profesor) fuera del repo y en `.gitignore` (3-nov). Sigue en el historial antiguo.
- [x] 4.ª y 5.ª acción (3-nov, con Claude Code): `renombrar-capturas` (renombrar) y `copiar-entregas` (copiar). `mochila validar` → 5 acciones válidas; probadas en `~/pruebas-tareas/acciones-nuevas`, primero con `--simular` y después **de verdad** (3-nov, lo lancé yo con `mochila --config <ruta>\acciones.json ejecutar …`): 3 hechos y 0 con error en cada una. Las capturas quedaron como `captura_2026-11-03_001.png`, `_002.png` y `_003.jpg`, y las 3 entregas se copiaron a `~/pruebas-tareas/entregas` sin tocar los originales. Ojo: `{fecha}` es la fecha de modificación del fichero, no la del nombre, y el patrón distingue mayúsculas (`captura…` en minúscula no entra).
- [x] 6.ª acción (3-nov, OpenCode): `mover-zips`, antes `comprimir-zips`, (mover) mueve los `.zip` a `comprimidos/`. `mochila validar` → 6 acciones válidas; probada con `--simular` en `~/pruebas-tareas/prueba-final` (2 simulados, 0 errores) y `uv run pytest -q` → 162 passed. Probada **de verdad** (3-nov, la lancé yo): 2 hechos y 0 con error; los dos `.zip` están en `comprimidos/`. Revisada con `@revisor`; sus avisos y las decisiones están en `docs/prompts.md`.
- [x] `acciones.json` copiado a `~/.config/mochila/`: `mochila` funciona sin `--config` fuera del repo. Si cambia el del repo, hay que volver a copiarlo.
- [x] `opencode --version` → 1.18.35 (3-nov), la misma versión apuntada en la semana 1. No se migra nada antes del 6 nov.

### Instalación en otros equipos (3-nov, Claude Code)
- [x] **Por qué en el PC de clase (Linux) no iba ni `mochila --help` ni la subida a `DAM-almacen`:** el código está bien (un clon limpio pasa los tests). Lo que hace funcionar `mochila` vive fuera del repo, en la carpeta personal de cada equipo: `uv` y `mochila` en `~/.local/bin`, `~/.config/mochila/acciones.json`, `~/DAM-almacen` y el token de GitHub. `git clone` no los trae.
- [x] **Instalador:** `bash instalar.sh` (Linux/macOS) y `instalar.cmd` (Windows, doble clic, lanza `instalar.ps1`). Comprueba git, instala uv, `uv sync`, instala `mochila`, copia `acciones.json` a `~/.config/mochila/`, pide nombre y correo de git si faltan, clona `DAM-almacen` y termina con `mochila validar`. Se puede repetir: salta lo que ya está hecho. `.gitattributes` fija LF para `.sh` y CRLF para `.ps1`/`.cmd`.
- [x] **Probado en Ubuntu 24.04 (WSL), clonando desde GitHub (lo lancé yo):** todo bien menos clonar `DAM-almacen`: GitHub no acepta la contraseña, hace falta un token.
- [x] `mochila help` y `mochila help COMANDO` (igual que `--help`); `mochila help noexiste` sale con 2.
- [x] **Autocompletado con TAB:** comandos, nombres de acciones (`mochila ejecutar co<TAB>`) y asignaturas del almacén (`mochila sync pr<TAB>`). Lo activan los instaladores en bash, zsh y PowerShell. Probado con un TAB real en Git Bash y PowerShell (entorno aislado); **falta probarlo en Linux de verdad**.

### Comandos para mis proyectos (5 y 6-nov, Claude Code)
Grupo nuevo en la ayuda: «Tus proyectos: revisar y entregar». Los tres solo leen, salvo `entregar`, que crea el zip. Detalle en `docs/prompts.md`.
- [x] **`mochila entregar CARPETA [--destino] [--nombre] [--simular]`** (`entregar.py`): un `.zip` limpio, sin `.env`, claves, `.git`, `.venv`, `node_modules` ni `__pycache__`, y respetando `.gitignore`. Si `scan-secrets` encuentra un secreto dentro, no lo crea. Probado por mí en Electrician: 47 ficheros, 342,2 KB → zip de 143,3 KB, y `.env` y `.claude/` se quedaron fuera.
- [x] **`mochila doctor CARPETA`** (`doctor.py`): 7 comprobaciones básicas (git, `.gitignore`, `.env` ignorado y sin subir, `.env.example` al día, README, secretos) y 4 recomendadas (tests, dependencias, CI, ficheros de más de 50 MB). Del `.env` solo lee los nombres. Probado por mí: Electrician **11 de 11**; `portfolio-backend` 8 de 11; `DAM-almacen` 6 de 9.
- [x] **`mochila pendientes CARPETA [--quien NOMBRE] [--resumen]`** (`pendientes.py`): cuenta `[Verificado]`, `[Hipótesis]` y `[Pendiente]` en los `.md` (y los verificados sin fecha) y resume `docs/pendientes.md` por persona. Electrician: 39 verificados (15 sin fecha), 10 hipótesis y 33 pendientes; registro de 52 filas con 33 abiertas (Sergio 12 · Gabi 9 · Javi 9 · Mar 7 · Todos 3).
- [x] **Arreglo del TAB en PowerShell:** un TAB en una ruta dejaba `mochila` atascado (solo imprimía líneas en blanco) hasta cerrar la ventana. El script del TAB ahora borra siempre sus variables. Mi `~/.config/mochila/completado.ps1` ya está regenerado.
- [x] **Aviso de la `\` final:** `mochila doctor "C:\carpeta\"` ya no dice «no existe»: explica que la `\` se come las comillas y da la orden corregida.

### Organizar el PC en `~/Datos` (10-nov, Claude Code)
Plan en 5 fases: 1 `mochila inventario` → 2 `mochila duplicados` (solo informa, nunca borra) → 3 `mochila readme` → 4 `ordenar` con plan B por tipo (`POR-TIPO/`) → 5 la mudanza la hago yo por bloques.
- [x] **`mochila inventario [CARPETA] [--guardar INFORME.md] [--top N]`** (`inventario.py`, solo lee): tamaño por carpeta, tipos, repos (y si tienen remoto), instaladores, basura, carpetas regenerables (`.venv`, `node_modules`) y ficheros de más de 100 MB. Los ficheros de OneDrive «solo en la nube» no cuentan como espacio en el disco. Probado en `~/Datos`: 73 170 ficheros en 4 s.
- [x] **Mudanza hecha** (fase 5 adelantada, con `~/mudanza-datos.ps1`): todo está en `~/Datos` con las carpetas en MAYÚSCULAS (`CURSOS`, `DAM`, `MAQUINAS-VIRTUALES`, `PERSONAL`, `POR-TIPO`, `REPOS`, `SMX`) y un README en cada carpeta hasta el tercer nivel. Dentro de los repos no se ha cambiado ningún nombre.
- [x] Los apuntes de DAM están solo en el almacén (`REPOS\DAM-ALMACEN`). En este PC, `mochila` lo encuentra por la variable `MOCHILA_ALMACEN`; `acciones.json` sigue con `~/DAM-almacen` porque es la ruta de los otros equipos.
- [x] **Fase 2 `mochila duplicados [CARPETA] [--guardar INFORME.md] [--top N]`** (`duplicados.py`, solo lee): compara el contenido (SHA-256; primero por tamaño y por los primeros 64 KB, para ir rápido). Enseña primero las **carpetas que son copia de otra** (todos sus ficheros tienen copia fuera), las de fuera de los repos antes, y cada pareja una sola vez; después los grupos de ficheros repetidos, de más a menos espacio. Marca «(repo)» lo que está en un repo (eso se quita con un commit). Una carpeta con un repo dentro nunca sale como copia (su `.git` no se compara). No lee lo que está «solo en la nube». Probado en `~/Datos` (después de la limpieza a mano): 3746 ficheros, 327 grupos, 125 MB repetidos y 56 carpetas copia, en 20 s. Lo primero que sale: `SMX2/APLICACIONS WEB/APW-MAIN` repite lo del repo `APLICACIONS-WEB`, y los PDF de Java están dos veces en DAM-almacen (`entornos` y `lenguaje-marcas`).
- [x] **Fase 3 `mochila readme [CARPETA] [--niveles N] [--simular] [--si]`** (`readme.py`): el apartado «## Qué hay dentro» de cada README es una tabla (📁 subcarpetas con su tamaño y la primera frase de su README, que dice «Repo git.» si lo es; 📄 archivos con tamaño y tipo; más de 15 archivos se resumen en una fila). Lo de encima del apartado (y lo que haya debajo, en otro `##`) es del alumno y no se toca; un README sin el apartado tampoco. No entra en repos (`.git`) ni en proyectos (`pyproject.toml`, `package.json`, `.venv`, `node_modules`...) y en un proyecto sin README no crea uno. Los README.md no cuentan en los tamaños y la fecha del pie no cuenta como cambio: si nada cambia, la segunda vez dice «No hay nada que hacer». Simulado en `~/Datos`: 63 a poner al día (las listas del 10-nov pasan a tabla), 0 nuevos, en 6 s.
- [x] La ayuda general tiene 38 líneas (límite: menos de 40): «mochila help COMANDO» va en la línea de `mochila help` y las dos del TAB son una.
- [x] Fase 4 (1.ª parte) `ordenar` al almacén: con `"al_almacen": true` (ya puesto en `acciones.json`) cada fichero va a `asignaturas/<asignatura>` del almacén (`MOCHILA_ALMACEN` o «almacen» de acciones.json); si la asignatura no existe allí, se salta (no se inventan carpetas). Al acabar pregunta «¿Hago ahora mochila sync…?» y, si dices sí, sincroniza con el mensaje `[sync]: ordenar: N apunte(s) nuevo(s)`; con `--si` no pregunta y solo lo recuerda.
- [x] Fase 4 (2.ª parte) `"por_tipo": "~/Datos/POR-TIPO"`: lo que no es de ninguna asignatura va a `POR-TIPO/<TIPO>` (los tipos de `mochila inventario`, en MAYÚSCULAS; máquinas virtuales y lo desconocido a `OTROS`). La nota «por tipo» sale en la tabla y eso no cuenta para el `mochila sync`. Nunca mueve `desktop.ini`, `Thumbs.db`, ocultos, temporales ni descargas a medias (`.crdownload`, `.part`), ni con plan B ni sin él.
- [x] La ayuda general (`mochila`) es una tabla: tema (y para qué) · comando · qué hace, con una raya entre temas. 37 líneas; el test la mide a 120 columnas para no depender del terminal.

### Tu ciclo y tus asignaturas: `mochila configurar` (11 y 12-nov, Claude Code)
Idea mía: que, como `adduser` en Linux, al instalar pregunte qué estudias, para que `ordenar` y `clasificar` no sirvan solo para 1º de DAM. Detalle en `docs/prompts.md`.
- [x] **`mochila configurar`** (PR #25): ciclo (SMX, DAM, DAW, ASIR/ASIX u otro) y curso; deja quitar y añadir asignaturas. Reescribe `ordenar` y `clasificar`, valida, guarda copia, recuerda lo elegido (`perfil`) y ofrece crear las carpetas en el almacén. El vocabulario está en `ciclos.py`. Los instaladores lo lanzan después de clonar el almacén.
- [x] Probado en WSL como alumno de 1º de SMX con 15 apuntes reales: de 7 a **11 de 15** colocados tras la #26 (vocabulario de SMX y pregunta más clara) y la #27 (palabras clave al día al repetir; no ofrece `mochila sync` sin git; pruebas que no dependen del ancho de la consola).
- [x] `bash instalar.sh` probado de verdad en WSL: el TAB funciona.
- [x] **`mochila ejecutar ACCIÓN FICHERO`** (PR #28): un solo fichero, solo si cumple el filtro de la acción. `mochila acciones -h` trae ejemplos.
- [x] **Instalación desde cero en un Linux de clase** (12-nov, un PC del aula que no es el mío): `git clone` + `bash instalar.sh` sin `uv` instalado. `mochila` no se encontraba en terminales nuevas (el PATH no se guardaba): arreglado en la PR #34 y comprobado allí mismo. Después: 527 pruebas, `doctor` 11 de 11, IA con OpenCode y las acciones (`resumir-tema`, `nombrar-descargas`, `limpiar-temporales`, `ordenar`) de verdad. Detalle en `docs/prompts.md`.

### Semanas 3 y 4: capa IA, pruebas y release 1.0 (11-nov, Claude Code)
- [x] `ia.py` con `ProveedorIA` ([ADR-0002](docs/adr/0002-proveedor-ia.md)), las acciones `resumir-tema`, `nombrar-descargas` y `clasificar-asignatura`, `mochila comprobar-ia` y el código 4 sin red.
- [x] Pruebas de la Sesión 4 (`conftest.py` con `aislado`, `ProveedorFalso`, códigos 0-4 con `CliRunner`), la prueba de mutación de `--simular` y `pytest-cov`.
- [x] `pruebas.yml` en Ubuntu, Windows y macOS; `scripts/revisar.sh`; `CHANGELOG.md`; instalación en una orden en el README.
- [x] **Release 1.0.0** (PR #16 de la rama `release-1.0`, etiqueta `v1.0.0`) y, con el ensayo en un Ubuntu recién instalado (issues #17-#22), la **1.0.1**.

### Del 13 al 25-nov (resumen; el detalle está en `docs/prompts.md`)
- [x] `mochila crear-almacen` (cada ciclo con su almacén, [ADR-0005](docs/adr/0005-almacen-por-ciclo.md)) y `mochila configurar-ia` con los modelos gratis de OpenCode ([ADR-0004](docs/adr/0004-ia-gratis-opencode.md)).
- [x] Mi PC de clase con el almacén real y la IA del centro (13-nov); repaso de los errores amables: 26 errores provocados, ninguna traza.
- [x] Instalación cruzada con un compañero de DAW en Windows 11 LTSC (15-nov, issue #46) → la ayuda nueva y el cambio de nombre a `mochila`.
- [x] **Release 1.1.0** (17-nov, PR #48 de la rama `release-1.1`).
- [x] El revisor de OpenCode en el hook de cada commit con código (`mochila instalar-hook --revisor`, PR #49) y una prueba de que `--simular` dice lo mismo que pasa de verdad.
- [x] Instalación desde cero en una VM con Windows 11 limpio, siguiendo solo el README como alumno de 1º de ASIR (18 y 19-nov, issue #53, arreglos en #54-#57).
- [x] En clase con el modelo del centro (19-nov): las 3 acciones con IA de verdad, romperlo a propósito (`echo $?` → 4), context7, el borrador del CHANGELOG con `opencode run --agent plan` y `scripts/revisar.sh` real (PR #58).
- [x] **Release 1.2.0** (24-nov, rama `release-1.2`): revisión final frente a la Sesión 4, `docs/entrega.md`, `revisar.sh` sale con 1 si no hay nada preparado y el workflow explicado línea a línea.
- [x] **IA del centro desde mi portátil (25-nov, en clase)**: `mochila comprobar-ia` responde «Hola» en 0,2 s con `Qwen38-DualSpark-medium`, y `opencode run` también, desde cualquier carpeta (la clave en una variable de entorno, nunca en un fichero). Arreglado de paso: en Windows el límite de 300 s de OpenCode no se cumplía (PR #64, publicado en la **1.2.1**, rama `release-1.2.1`).

## Qué falta

- [x] **Instalación en otros equipos:** Ubuntu recién instalado (#17-#22), mi cuñado de DAW en su
  portátil (15-nov, #46) y una VM con Windows 11 limpio siguiendo solo el README como alumno de 1º de
  ASIR (18 y 19-nov, #53, la hice yo). Cada fallo con su issue y «Closes #N»; todo publicado (1.2.1).
- [x] **Acciones combinables (26-nov, 1.3.0):** tipo `secuencia` (ADR-0007) y `repasar-carpeta` en el
  ejemplo; cada paso ve lo que dejó el anterior y, si uno falla, para. `docs/spec.md` con la spec de la
  Sesión 1. 28 pruebas nuevas (`tests/test_secuencia.py`).
- [x] **Intentar romperlo antes que el profe (26-nov, noche, 1.3.1):** más de 30 entradas feas sin
  ninguna traza y con el código de salida del README. Lo único raro: el `destino` de `mover-zips` se salía
  de la carpeta; ahora un destino relativo va dentro de ella y `mover`/`copiar` saltan lo que ya está en su
  destino (#78). IA del centro probada desde clase (comprobar-ia y nombrar-descargas).
- [x] **Instalación cruzada de otra persona con su cuenta (25 y 26-nov):** un amigo, en su portátil con
  Windows 10 y su cuenta de GitHub, lo instaló, creó su almacén y probó acciones con y sin IA y los
  códigos de salida. Abrió él sus issues (#69, #70 y #71): arreglados con prueba y «Closes #N»
  y publicados en la **1.2.2**. Detalle en `docs/prompts.md` (entrada del 25 y 26-nov).
- [ ] Ensayar la defensa: instalar desde cero, una acción con IA y otra sin red, y las 6 preguntas
  (dónde está cada respuesta: final de [docs/entrega.md](docs/entrega.md)).

Lo que faltaba en las versiones antiguas de este fichero (clase, release 1.0 y 1.1, `[COMPLETAR]` de
las sesiones 1 a 3) ya está hecho: se puede ver con `git log -p punto_actual.md`.

## Cómo retomar

```powershell
cd "C:\Users\HP\Datos\REPOS\TERMINAL_CLI"
uv sync
uv run pytest -q
mochila -h                # o: mochila help
mochila validar
mochila status
mochila scan-secrets --historial
```

En otro equipo (clase, WSL, Mac): `git clone https://github.com/gabi37smx/Terminal_CLI.git`, `cd Terminal_CLI`, `bash instalar.sh` y abrir otra terminal.

## Recordatorios

- Los commits y el push los haces tú; el agente solo commitea si se lo pides expresamente. El agente no ejecuta `sync` ni `ejecutar`.
- Tras cada fusión o release: `uv run python scripts/historial_pr.py` para regenerar `docs/historial-pr.md`.
- Probar siempre en `~/pruebas-tareas` y con `--simular` primero.
- Si se cambia `opencode.json`, cerrar y volver a abrir OpenCode.
- GitHub no acepta la contraseña en git: en *Password* va el token. En Linux, el instalador hace que git lo recuerde 8 horas solo en memoria.
- No usar `mochila --install-completion` en Windows: cambia la política de PowerShell a `Unrestricted` y duplica el script en el perfil. El TAB lo activa el instalador.
- En PowerShell, nada de `\` justo antes de las comillas de cierre: `"C:\carpeta"`, no `"C:\carpeta\"`. El TAB de PowerShell la añade; `mochila` ahora avisa.
- Si `mochila` solo imprime una línea en blanco en PowerShell, es el script del TAB antiguo: `instalar.cmd` otra vez y abrir otra ventana.
- Al ejecutar `uv sync` desde WSL, nunca sobre la carpeta de Windows (`/mnt/c/...`): cambiaría el `.venv` de Windows por uno de Linux.
- Nada de claves en el repo ni en su historial (mínimo eliminatorio). Un repo del almacén con apuntes: privado.
- Lo que no sé explicar, no lo entrego: repasar `config.py`, `acciones.py`, `motor.py`, `escanear.py`, `web.py` y `hook.py` hasta poder explicar cada aserción, y también los tres del 5 y 6-nov (`doctor.py`, `pendientes.py` y `entregar.py`) y el arreglo del TAB en `cli.py` (por qué el `try/finally`).
