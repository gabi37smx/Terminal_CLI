# Changelog

Todos los cambios importantes de `tareas` (el comando `dam`) se apuntan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y las versiones siguen
[Versionado Semántico](https://semver.org/lang/es/): 1.0.1 arregla fallos, 1.1.0 añade cosas sin
romper nada y 2.0.0 rompería algo (por ejemplo, el esquema de `acciones.json`).

## [Sin publicar]

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

[Sin publicar]: https://github.com/gabi37smx/Terminal_CLI/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/gabi37smx/Terminal_CLI/releases/tag/v1.0.0
