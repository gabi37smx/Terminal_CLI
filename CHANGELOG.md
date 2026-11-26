# Changelog

Todos los cambios importantes de `tareas` (el comando `mochila`; hasta la 1.0.1, `dam`) se apuntan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y las versiones siguen
[Versionado Semántico](https://semver.org/lang/es/): 1.0.1 arregla fallos, 1.1.0 añade cosas sin
romper nada y 2.0.0 rompería algo (por ejemplo, el esquema de `acciones.json`).

## [Sin publicar]

## [1.3.0] - 2026-11-26

Acciones combinables (lo que pide el nivel excelente de la rúbrica) y la spec en su propio fichero.

### Añadido

- **Tipo de acción `secuencia`**: ejecuta varias acciones seguidas sobre la misma carpeta
  (`"pasos": ["limpiar-temporales", "renombrar-capturas", ...]`). Cada paso ve lo que dejó el
  anterior, enseña su tabla y pregunta como si lo lanzaras solo; si uno falla o le dices que no, los
  demás no se ejecutan y se dice cuáles. Con `--simular` avisa de que cada paso se calcula con la
  carpeta tal como está. Si algún paso necesita IA y no hay modelo, sale con 4 antes de empezar.
  `config.py` comprueba que cada paso existe, que no es otra secuencia ni la propia y que hay al
  menos dos (código 3). Antes de empezar comprueba también que no le has pasado un fichero suelto y que, sin
  CARPETA, cada paso tiene su `origen`. Decisión y alternativas en el ADR-0007.
- `acciones.json` de ejemplo: `repasar-carpeta` (limpiar-temporales → renombrar-capturas →
  convertir-webp → mover-zips). `mochila acciones` enseña los pasos de cada secuencia.
- `docs/spec.md`: la spec de 10 líneas de la Sesión 1, tal cual, y en qué ha quedado cada punto.
- 28 pruebas nuevas en `tests/test_secuencia.py`.

## [1.2.2] - 2026-11-26

Lo que salió de la instalación cruzada de un amigo (25 y 26-nov): otra persona, en su portátil con
Windows 10, con su cuenta de GitHub, y con sus issues (#69, #70 y #71).

### Arreglado

- **Las preguntas s/n ya no toman como «no» lo que no entienden** (#69). En `mochila configurar`
  escribió `7` en un `[s/N]` (quería quitar la asignatura 7) y siguió como si nada; una errata (`sw`)
  en un `[S/n]` canceló el guardado. Ahora dice «No te he entendido» y vuelve a preguntar; Enter
  sigue siendo lo de la mayúscula, y `n`/`no` es «no».
- **`--simular` avisa de que su estimación de tokens es solo la del texto** (#70). Anunciaba
  «~57 tokens» y la ejecución real gastó 1191+11: el modelo suma sus instrucciones (con OpenCode, un
  simple «Hola» ya gasta unos 900). Ahora dice «~N tokens de texto, más las instrucciones del
  modelo», y el README lo explica.
- **PowerShell de Administrador** (#71). Esa ventana empieza en `C:\Windows\System32` y el
  `git clone` acabó ahí. El README pide un PowerShell normal y `cd $HOME` antes de clonar, e
  `instalar.ps1` avisa si se ejecuta como Administrador o desde la carpeta de Windows.

## [1.2.1] - 2026-11-25

La IA del centro probada desde mi portátil con Windows, en clase, y el arreglo que salió de esa prueba.
Queda pendiente que un compañero de ASIR lo instale con su propia cuenta de GitHub (lo que salga
irá en una 1.2.2).

### Arreglado

- **En Windows, el tiempo máximo de OpenCode (300 s) no se cumplía.** Probado el 25-nov en la red
  del centro: el modelo gratis no contestaba y `mochila comprobar-ia` siguió esperando más de 7
  minutos. El motivo: `opencode` es `opencode.CMD`, que lanza `cmd.exe` y este el `opencode.exe` de
  verdad; al acabarse el tiempo solo moría `cmd.exe`, y Python se quedaba esperando la salida del
  otro. Ahora `ia.ejecutar` mata el proceso con todos sus hijos (`taskkill /T` en Windows, el grupo
  de procesos en Linux y macOS) y sale el aviso «no ha respondido en 300 s» con código 4. Lo usan
  las acciones con IA, `comprobar-ia` y la lista de modelos de `configurar-ia`.

## [1.2.0] - 2026-11-24

Lo que salió de probar en clase con el modelo del centro (19-nov) y de la instalación cruzada como
alumno de 1º de ASIR en un Windows 11 recién instalado (#53), y la revisión final frente a la
Sesión 4 antes de la entrega.

### Añadido

- `docs/entrega.md`: para quien corrige, dónde está cada cosa que pide la rúbrica (con la orden o el
  fichero que lo demuestra).
- `mochila instalar-hook --revisor`: además de buscar claves, el hook pasa cada commit que lleve
  código por el agente revisor de OpenCode (`scripts/revisar.sh`). Si dice `VEREDICTO: CAMBIAR`, el
  commit se cancela; si no se puede revisar (sin red), avisa y deja seguir. Solo documentación: no
  lo llama. Para saltarlo una vez: `MOCHILA_SIN_REVISOR=1`.
- `scripts/revisar.sh` usa el modelo que elegiste con `mochila configurar-ia` (en casa, uno gratis
  de OpenCode) o el de `MOCHILA_REVISOR_MODELO`; antes siempre usaba el de OpenCode por defecto.
- Una prueba que comprueba que **lo que dice `--simular` es lo que pasa de verdad** en los seis
  tipos de acción sin IA: mismos ficheros, mismos destinos y mismos saltados, y después cada
  fichero está donde dijo la simulación.
- **El almacén «solo en este equipo»**, para quien aún no tiene GitHub (#53): en `mochila
  crear-almacen`, pulsa Enter en el usuario y di que sí a «¿Lo creo solo en este equipo?»: lo crea
  en `~/CICLO-almacen` con tus carpetas, sin subir nada, y ya puedes ordenar. Cuando tengas cuenta, repite `mochila crear-almacen` y lo sube a
  tu repo (vacío). Hasta entonces, `ordenar` no ofrece `sync`, y `sync` y `status` dicen qué hacer
  en vez de `git push -u origin main` (ADR-0005, actualizado).

### Cambiado

- `scripts/revisar.sh` sale con **1** si no hay nada preparado para el commit, como pide la Sesión 4
  (antes salía con 0). Así el 0 solo significa «el revisor ha dicho `VEREDICTO: OK`».
- `.github/workflows/pruebas.yml`: `actions/checkout@v5` y un comentario en cada línea que explica qué
  hace.

### Arreglado

- `nombrar-descargas`: un PDF que no dice de qué trata, o que da órdenes al modelo, se llama `revisar-a-mano.pdf`.
  Antes podía quedarse con otro nombre genérico (`descarga.pdf` → `documento.pdf`), que el filtro volvía a
  coger. Visto en clase con el modelo del centro; arreglado en las instrucciones de `acciones.json`.
- `scripts/revisar.sh` lanzado desde un hook de git ya no estropea el commit: OpenCode heredaba
  `GIT_INDEX_FILE` y guardaba sus instantáneas en el índice del repositorio (`invalid object`).
- Lo que salió en la instalación cruzada de 1º de ASIR (#53), en lo de la IA:
  - Si aún no has elegido modelo, las acciones con IA y `comprobar-ia` te dicen que lo elijas con
    `mochila configurar-ia`, en vez de pedir `CENTRO_IA_URL` y `CENTRO_IA_KEY`. Si ya tienes esas
    variables (o un `.env`), se sigue usando el servidor del centro sin elegir nada.
  - Sin internet, OpenCode decía `Cannot connect to API: Was there a typo in the url or port?`; ahora
    sale «No hay conexión con OpenCode: ¿tienes internet?».
  - La pregunta de prueba de `comprobar-ia` y `configurar-ia` es un saludo. Antes pedía «responde solo
    ok», y el modelo contestaba con una nota: el agente de mochila le dice que no obedezca
    instrucciones que lleguen en el mensaje. Además, solo se enseña la primera línea de la respuesta.
  - Si `npm` se cierra al instalar OpenCode (dentro de una máquina virtual pasa a veces), el
    instalador lo intenta otra vez y, si no hay OpenCode, lo repite al final con la orden para
    instalarlo.
- Lo que salió en la instalación cruzada de 1º de ASIR (#53), en `ordenar` y `resumir-tema`:
  - Un tema de CSS iba a Bases de datos (hablaba de «tablas» y «consultas de medios»). Lenguaje de
    marcas reconoce ahora `css`, «hojas de estilo», `dtd`, `xsd`, `xpath`, `xslt` y `xquery`.
  - Lo que no es de ninguna asignatura solo va a `por_tipo` (`~/Datos/POR-TIPO`) **si esa carpeta ya
    existe**. Es cómo ordeno yo mi PC: a otro alumno se le creaba sin pedirla. Si no está, el fichero
    se queda donde estaba.
  - `resumir-tema` quita las cabeceras y los pies de un PDF (las líneas que se repiten arriba o abajo
    en más de la mitad de las páginas, aunque cambie el número de página). Un PDF que solo tiene
    cabeceras se salta como «sin texto», sin preguntar al modelo: antes gastaba una llamada y dejaba
    un resumen que decía «contenido no disponible».

### Seguridad

- El agente de OpenCode ya no puede borrar ficheros con las órdenes de Windows (`Remove-Item`,
  también en minúsculas, `del`, `erase`, `rmdir`, `rd`) ni con `git clean`, y tampoco tirar cambios sin
  guardar con `git restore` o `git checkout --`: antes solo estaba prohibido `rm`. Una prueba
  avisa si alguien quita una de estas reglas de `opencode.json`.

## [1.1.0] - 2026-11-17

### Cambiado

- Las preguntas en las que Enter tenía que seguir adelante ahora tienen **Sí** por defecto (`[S/n]`):
  guardar lo que eliges en `configurar` (guarda copia de lo anterior), crear las carpetas de tus
  asignaturas, preparar el almacén, usar el servidor del centro que ya tiene OpenCode y, en el
  instalador, rehacer `acciones.json` con las acciones nuevas. Lo que mueve, borra, sube a GitHub o
  cambia otro programa sigue con **No** por defecto (`[s/N]`).
- **El comando se llama `mochila`** (antes `dam`): a un compañero de DAW le confundía que se llamara
  como otro ciclo (ADR-0006). `tareas` sigue valiendo. Tu configuración pasa a `~/.config/mochila`
  y las variables a `MOCHILA_ALMACEN`, `MOCHILA_IA`...; al repetir el instalador se copia lo que ya
  tenías, y las variables `DAM_…`, `dam:ignore` y el hook de `dam` siguen funcionando.

### Añadido

- **Dos ayudas:** `mochila -h` es corta (una pantalla: lo más usado y los comandos por temas) y
  `mochila help` es una guía con los primeros pasos, cada comando con un ejemplo para copiar y
  trucos (`.`, `--simular`, TAB...). `mochila help COMANDO` sigue explicando uno entero. Los
  ejemplos de `ejecutar` llevan siempre la carpeta (`mochila ejecutar ordenar . --simular`).

- `resumir-tema` hace resúmenes **a la medida del tema**: lee el tema entero (de uno largo, un trozo
  de cada página, no solo las primeras) y pide una viñeta por cada 2 páginas, entre 6 y 40, en
  apartados. Antes, de un tema de 71 páginas salían 6 viñetas. El `.resumen.md` se guarda **al lado
  del apunte** (en su asignatura y su unidad), no en `pruebas-tareas/resumenes`. El tiempo máximo
  de espera del modelo sube a 5 minutos.

- `ordenar` **crea la carpeta de la unidad** si el apunte dice de cuál es («UD1», «Tema 4») y aún no
  está: `UD01`, `UD02`... o con el estilo de las que ya tengas («Tema 2»). Con `"crear_unidades": false`
  solo usa las que existen.
- `ordenar` reconoce las **siglas del módulo** en el nombre del fichero (`LM_Tema01.pdf`,
  `ED_Git.pdf`, `BD`, `PRG`, `DWEC`, `ISO`...). Solo en el nombre: dentro de un PDF, «si» o «pi»
  salen por casualidad. `mochila configurar` pone las de tu ciclo.

- Si OpenCode ya usa el servidor del centro, `dam configurar-ia` ofrece usar esos mismos datos: no
  hace falta copiar la dirección ni la clave (la clave se queda en OpenCode y se lee al momento). Y si
  no defines `CENTRO_IA_CA`, `dam` usa el certificado de `NODE_EXTRA_CA_CERTS`, como OpenCode.

- `dam crear-almacen`: deja listo tu almacén de apuntes aunque no sepas git. Si ya lo tienes en
  GitHub, lo baja; si no, abre GitHub con el nombre y **Private** ya puestos, y solo pulsas «Create
  repository». Luego crea las carpetas de tus asignaturas y, si el repo es nuevo, las sube (así
  `dam sync` ya sabe adónde subir). `dam` nunca ve tu contraseña ni tu token (ADR-0005).
- El almacén se llama como tu ciclo: `SMX-almacen`, `DAM-almacen`, `DAW-almacen` o `ASIR-almacen`.
  `dam configurar` pone esa ruta en `acciones.json` (con DAM no cambia nada) y, si no tienes
  almacén, ofrece crearlo.

- `ordenar` mete cada fichero en la carpeta de **su unidad** si la asignatura ya la tiene: si el
  nombre, o si no el principio del contenido, dice «UD1», «UD-01», «Unitat 1», «Unidad 01» o
  «Tema 1», va a `sistemas/1 Avaluacio/unitat 1` (busca hasta 3 niveles y nunca crea la carpeta).
  Con `"unidades": false` se queda en la carpeta de la asignatura, como antes.
- `ordenar`, `resumir` y `clasificar` leen por dentro los documentos de LibreOffice y de Office
  (`.odt`, `.ods`, `.odp`, `.docx`, `.pptx`, `.xlsx`), empezando por la cabecera y el pie de página,
  que es donde un examen o unos apuntes suelen decir la asignatura y la unidad. Antes, `ordenar`
  solo leía los PDF y las acciones con IA le habrían mandado al modelo el zip tal cual.
- `resumir-tema` y `clasificar-asignatura` (en el `acciones.json` del repo) aceptan `.odt`, `.docx`,
  `.odp` y `.pptx`.

- `dam configurar-ia`: elige con qué modelo trabajan las acciones con IA. Con los **modelos gratis de
  OpenCode** (sin cuenta ni clave) también funcionan en casa: enseña los que hay ese día y qué hace
  cada uno con lo que le mandas, hace una pregunta mínima y lo guarda en `~/.config/dam/ia.json`. Si
  quieres, pone ese modelo por defecto en tu `~/.config/opencode/opencode.json` (con copia). Lo lanzan
  los instaladores, que instalan OpenCode 1.18.35 con `npm` si no lo tienes (ADR-0004).
- `ProveedorOpenCode`: usa `opencode run` con un agente propio sin herramientas, en una carpeta
  temporal vacía; el texto va por la entrada estándar. `DAM_IA=centro|opencode` y `DAM_IA_MODELO`
  cambian el proveedor o el modelo solo en esa terminal.

- `dam ejecutar ACCIÓN FICHERO`: una acción sobre un solo fichero (por ejemplo, convertir solo
  `portada.png`), siempre que cumpla el filtro de la acción; si no, dice por qué y no hace nada.
  Antes solo aceptaba carpetas y decía «La carpeta … no existe» aunque el fichero existiera.
- `dam acciones -h` trae ejemplos de cómo usar las acciones, y `dam acciones` recuerda al final cómo
  ejecutar una.

- `dam configurar`: como `adduser` en Linux, pregunta tu ciclo (SMX, DAM, DAW, ASIR/ASIX u otro) y
  curso, y pone tus asignaturas en `acciones.json` (carpetas y palabras clave de `ordenar`,
  categorías e instrucciones de `clasificar`). Deja quitar y añadir asignaturas, guarda una copia
  del anterior, recuerda lo que elegiste (`perfil`) y ofrece crear las carpetas en el almacén.
- `ciclos.py`: las asignaturas de 1º y 2º de los cuatro ciclos de Informática, con palabras clave en
  castellano y en valenciano.
- Campo opcional `perfil` en `acciones.json`.

### Arreglado

- `instalar.cmd` en Windows 11 LTSC: si la política de PowerShell no deja activar el TAB, ahora lo
  repite al final, donde se ve (antes se perdía entre la salida). Y si falta Git o Node.js, da su
  web antes que `winget`, que LTSC no trae (#46).
- Al leer algunos PDF (resúmenes, `ordenar`), pypdf llenaba la terminal de avisos como «fontTools is
  required...» aunque el texto salía bien. Ahora solo se ven sus errores de verdad.
- Lo que no entendió el compañero de la instalación cruzada: `mochila ordenar` dice que `ordenar` es
  una acción y da la orden buena (`mochila ejecutar ordenar CARPETA --simular`); `ejecutar` sin
  carpeta explica que hay que decirla (`.` es la carpeta en la que estás) en vez de quejarse de la
  carpeta de pruebas; una acción mal escrita propone la parecida (`clasificar` → `clasificar-asignatura`);
  y sin almacén o sin carpetas de asignaturas dice qué escribir (`crear-almacen` o `configurar`).
- `ordenar` ya no mete un instalador en una asignatura porque su nombre diga «git» o «linux»: va a
  `INSTALADORES`. Y un `.html` de bases de datos («BD», «SGBD») ya no va a lenguaje de marcas.
- `instalar.cmd` en un Windows recién instalado ya no da un error en rojo al activar el TAB: crea la
  carpeta `.config\dam` antes de guardar el script, y si no puede generarlo no toca tu perfil de
  PowerShell. Lo encontró la instalación cruzada con un compañero de ASIR.
- `dam doctor` en tu carpeta personal ya no la revisa entera (salían como «secretos» los certificados
  de `.cache` y tardaba): avisa de que no es un proyecto y te dice qué proyectos hay dentro.
- `dam --help | head` (o cualquier salida cortada) en Windows ya no acaba con una traza de una pantalla.
- Servidor de IA del centro: el modelo por defecto (`qwen3.8-flash-next`) daba **403**. Ahora es
  `Qwen38-DualSpark-medium`, el mismo que trae el OpenCode del centro. Un 403 ya no dice «algo ha
  fallado»: dice que tu clave no puede usar ese modelo y que pruebes otro con `CENTRO_IA_MODELO`.
- El servidor del centro puede tardar más de 30 s en responder: `dam` espera hasta 120 s (antes, 60).
- `dam status` ya no parte en dos líneas una ruta larga con espacios (parecían dos ficheros).
- `dam crear-almacen`: si `acciones.json` se quedó con la ruta de otro ciclo (`~/DAM-almacen` siendo de
  DAW), la cambia a la de tu ciclo antes de clonar, salvo que ahí ya tengas tu almacén.
- `instalar.sh` en un Linux recién instalado: `dam` no se encontraba ni abriendo otra terminal. El
  script añade `~/.local/bin` a su propio PATH para usar `uv`, y por eso `uv tool update-shell` (y el
  instalador de uv) creían que ya estaba y no lo apuntaban en ningún sitio. Ahora lo apunta el
  instalador en `~/.bashrc` o `~/.zshrc`, una sola vez (pasó en un PC de clase con Ubuntu).
- `instalar.sh` ya no acepta como correo de git algo sin `@` (por ejemplo el usuario de GitHub): lo
  vuelve a preguntar, también si ya estaba mal guardado. Y si el clonado del almacén falla con
  «Invalid username or token», explica que en *Password* va el token, no la contraseña.
- `dam --version` (y `-V`) funcionan, igual que `dam version`. Antes daban «No existe la opción».
- `ordenar`, si el almacén no tiene las carpetas de asignatura, dice que `dam configurar` las crea.
- El título de la tabla de `dam ejecutar` ya no se parte en dos líneas cuando la tabla es estrecha.

- `dam configurar-ia` pide a OpenCode la lista de modelos al día (`--refresh`). Recién instalado,
  OpenCode enseñaba la lista que trae dentro, con modelos que ya no están (pasó en WSL). Si no hay
  ningún recomendado, propone primero uno que no guarde lo que le mandas.
- `clasificar-asignatura` acepta también `.ods`: en ofimática casi todo son hojas de cálculo.
- `clasificar` le manda al modelo también el **nombre del fichero** (dentro de `<documento>`, como
  texto para leer). En la prueba con apuntes de SMX, `Practiques CALC Diagrames.ods` fue a «otros»:
  por dentro solo tenía números y «CALC» estaba en el nombre.
- Más palabras clave de seguridad (`spam`, `phishing`, `virus`, `hacking`, `iptables`, `lista negra`,
  `malicioso`...). Unos apuntes sobre Spamhaus iban a redes locales porque hablaban de redes y TCP.
  Para tenerlas en tu `acciones.json`, vuelve a lanzar `dam configurar`.

### Cambiado

- `dam comprobar-ia` y las acciones con IA usan el proveedor que elegiste (sin elegir nada, el
  servidor del centro, como antes). Sin clave del centro, el mensaje recuerda `dam configurar-ia`.
- Los instaladores ya no copian `acciones.json` tal cual: después de clonar el almacén lanzan
  `dam configurar`. Si lo cancelas, copian el de 1º de DAM como antes.

### Corregido

- En `dam configurar`, al escribir números en «asignaturas que añades» (pensando que eran las que
  te quedas) se creaban asignaturas llamadas «3», «4»... Ahora la pregunta dice que son NUEVAS y por
  nombre, se ve con cuáles te quedas y, si escribes un número, lo explica y vuelve a preguntar.
- Vocabulario de SMX, tras probarlo con apuntes reales de 1º: `.pka` (actividades de Packet Tracer)
  a redes, `.odb` (LibreOffice Base) a ofimática, discos y cajas a montaje, las siglas MME y SOX,
  cambio climático a sostenibilidad y John the Ripper y contraseñas a seguridad.
- Al repetir `dam configurar`, «tus asignaturas de la última vez» traían las palabras clave viejas:
  las que aprende el vocabulario después no llegaban nunca (solo las extensiones). Ahora se añaden,
  sin quitar las tuyas.
- `ejecutar ordenar` con un almacén que no es un repositorio git (uno de prueba) ofrecía `dam sync`
  y fallaba. Ahora avisa de que los apuntes ya están en él pero no se pueden subir.

## [1.0.1] - 2026-11-11

Arreglos que salieron al instalar la 1.0.0 en un portátil con Ubuntu 24.04 recién instalado,
siguiendo solo el README.

### Corregido

- El README no decía que hacen falta `git` y `curl`, ni cómo instalar uv: nuevo apartado «Antes de
  empezar» para Ubuntu/Debian, Fedora, macOS y Windows, y aviso de no usar el uv de snap (#17).
- Quien instalaba con la orden única no tenía `acciones.json` ni sabía cómo hacerlo. Ahora el
  mensaje de error y el README dicen de dónde bajar el ejemplo, dónde guardarlo y dónde está el
  esquema (#18).
- `comprobar-ia` sin clave mandaba a `.env.example`, que no existe si no has clonado. Ahora explica
  las dos formas: variables de la terminal (Linux, macOS y PowerShell) o un `.env` en la carpeta
  desde la que ejecutas `dam` (#19).
- La ayuda dice que `tareas` es el mismo programa, y cómo activar el TAB si no has clonado (#20).
- Los errores de uso salían en inglés dentro de un panel en español («No such command…»). Ahora se
  traducen los de Click antes de pintarlos: «No existe el comando «versiones». ¿Querías decir
  'version'?». La línea `Usage:` sigue en inglés (#20).
- Al clonar `DAM-almacen`, el instalador no dejaba claro que pide el usuario de github.com (no el
  del ordenador) ni qué escribir cuando git pide *Username* y *Password*. Ahora lo explica antes de
  clonar y, si falla, dice qué significa «Repository not found» y que se puede repetir (#22).

## [1.0.0] - 2026-11-11

Primera versión estable: lo de las semanas 1 a 4 del proyecto de 1º DAM.

### Añadido

- **Semana 1:** el comando `dam` con Typer y Rich: `--help`, `version` y `listar [CARPETA]`, con
  códigos de salida 0 (bien), 1 (fallo al ejecutar), 2 (uso incorrecto) y 3 (configuración no válida).
- **Semana 2:** las acciones viven en `acciones.json`, fuera del código (ADR-0001), y se validan
  antes de tocar un solo fichero: el error dice qué acción y qué campo fallan.
  - Órdenes `validar`, `acciones` y `ejecutar NOMBRE` con `--simular`, `--si` y `--config`.
  - Tipos `mover`, `copiar`, `renombrar`, `borrar`, `ordenar` y `convertir` (JPEG/PNG a WebP).
  - Mis seis acciones sin IA: `ordenar`, `limpiar-temporales`, `convertir-webp`,
    `renombrar-capturas`, `copiar-entregas` y `mover-zips`.
  - El almacén de apuntes en git: `status` y `sync` para tenerlos igual en clase, en casa y en el USB.
  - Skill `acciones-json`, comando `/nueva-accion` y agente `revisor` de solo lectura para OpenCode.
- **Semana 3:** la capa IA detrás de una interfaz, `ProveedorIA` (ADR-0002), con el servidor del
  centro en `ProveedorCentro`.
  - Orden `comprobar-ia` y código de salida 4 (sin clave, sin red o sin certificado). Las acciones
    sin IA siguen funcionando, y en `dam acciones` una columna dice cuáles usan IA.
  - Tipos `resumir`, `renombrar-ia` y `clasificar`, con mis acciones `resumir-tema`,
    `nombrar-descargas` y `clasificar-asignatura`.
  - `.env.example` documentado y el bloque `mcp` (context7) en `opencode.json`, apagado por defecto.
- **Semana 4:** las pruebas se pasan en GitHub Actions en Ubuntu, Windows y macOS
  (`.github/workflows/pruebas.yml`), y `pytest-cov` mide la cobertura (93 %).
  - `scripts/revisar.sh`: el agente revisor da `VEREDICTO: OK` o `CAMBIAR` sobre lo preparado
    para el commit, con un máximo de 180 s.
  - El mismo programa se instala también como `tareas` (el nombre de la spec v0):
    `tareas version` → `tareas 1.0.0`.
  - El README explica cómo instalar en una orden y cómo desinstalar.
- **Extras:**
  - Seguridad y web: `scan-secrets`, `instalar-hook`, `test-links` y `check-headers`.
  - Organización (todas solo leen, menos `readme`): `doctor`, `pendientes`, `entregar`,
    `inventario`, `duplicados` y `readme`.
  - `help` y autocompletado con TAB en bash, zsh y PowerShell.
- Instaladores `instalar.sh` (Linux y macOS) e `instalar.ps1` / `instalar.cmd` (Windows).
  - Instalan uv, el comando y la configuración.
  - Activan el TAB y configuran git.
  - Encuentran el almacén esté donde esté.

### Cambiado

- El comando se llamaba `tareas` en la spec v0 y pasó a llamarse `dam`. El paquete Python sigue
  siendo `tareas`.
- La configuración pasó de `tareas.toml` a `acciones.json`.
- `ordenar` lleva los apuntes al almacén. Lo que no reconoce va a `~/Datos/POR-TIPO`, y nunca mueve
  ficheros del sistema.
- El agente `revisor` pasa de `mode: subagent` a `mode: all`: con `subagent`, `opencode run --agent
  revisor` lo ignoraba y usaba el agente por defecto, que sí puede editar.

### Corregido

- Dos fallos que solo salían en Linux, encontrados al poner GitHub Actions. Además, los tests de la
  ayuda ya no fallan por los colores de Typer ni por el ancho de la terminal.
- El autocompletado con TAB en PowerShell.
- Los instaladores avisan si `~/.config/dam/acciones.json` es de una instalación vieja y ofrecen
  cambiarla, guardando antes una copia.

### Seguridad

- `.env` y `.env.*` están en `.gitignore` desde el principio, y `dam scan-secrets --historial`
  confirma que ninguna clave ha llegado nunca al repositorio.
- `dam sync` se niega a subir claves privadas, y el hook pre-commit revisa cada commit.
- La respuesta del modelo nunca se usa tal cual:
  - Los nombres pasan por `a_nombre_seguro()`, así que no hay `../` ni nombres reservados de Windows.
  - Las categorías solo pueden ser las de la lista.
  - El documento va entre `<documento>` para frenar la inyección de prompt.
- `comprobar-ia` nunca enseña la clave (solo dice «clave: definida»), y OpenCode no puede leer `*.env`.

[Sin publicar]: https://github.com/gabi37smx/Terminal_CLI/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/gabi37smx/Terminal_CLI/compare/v1.2.2...v1.3.0
[1.2.2]: https://github.com/gabi37smx/Terminal_CLI/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/gabi37smx/Terminal_CLI/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/gabi37smx/Terminal_CLI/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/gabi37smx/Terminal_CLI/compare/v1.0.1...v1.1.0
[1.0.1]: https://github.com/gabi37smx/Terminal_CLI/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/gabi37smx/Terminal_CLI/releases/tag/v1.0.0
