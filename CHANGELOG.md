# Changelog

Todos los cambios importantes de `tareas` (el comando `dam`) se apuntan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y las versiones siguen
[Versionado Semántico](https://semver.org/lang/es/): 1.0.1 arregla fallos, 1.1.0 añade cosas sin
romper nada y 2.0.0 rompería algo (por ejemplo, el esquema de `acciones.json`).

## [Sin publicar]

### Añadido

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

[Sin publicar]: https://github.com/gabi37smx/Terminal_CLI/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/gabi37smx/Terminal_CLI/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/gabi37smx/Terminal_CLI/releases/tag/v1.0.0
