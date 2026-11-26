# Entrega 2 · CLI: dónde está cada cosa

Guía para quien corrige: cada punto de la rúbrica y de las listas de la
[Sesión 4](https://aulaenlanube.com/programacion-ia/cli/sesion-04/), con el fichero o la orden que lo
demuestra. Revisada el 24-nov-2026, con la versión **1.2.0**, al día el 25-nov con la **1.2.1** y el 26-nov con la **1.2.2** y la **1.3.0**.

- **Repo:** https://github.com/gabi37smx/Terminal_CLI (rama `main`)
- **Comando:** `mochila` (el paquete Python es `tareas`, y `tareas` también funciona como comando:
  es el mismo programa; por qué cambió de nombre en [ADR-0006](adr/0006-nombre-mochila.md)).
- **Etiquetas y releases:** `v1.0.0` (la que pide la Sesión 4), `v1.0.1`, `v1.1.0`, `v1.2.0`, `v1.2.1`, `v1.2.2` y `v1.3.0`.
  Qué trae cada una: [CHANGELOG.md](../CHANGELOG.md).
- **Todas las PR e issues, por versión:** [historial-pr.md](historial-pr.md).
- **Qué le pedí a la IA y qué le corregí:** [prompts.md](prompts.md).
- **Estado y lo que falta:** [punto_actual.md](../punto_actual.md).

## Requisitos mínimos

| Mínimo | Dónde se ve |
|---|---|
| Se instala siguiendo el README y `--help` funciona | [README · En una orden](../README.md#en-una-orden-si-ya-tienes-uv): `uv tool install git+https://github.com/gabi37smx/Terminal_CLI@v1.3.0` y `mochila --help`. Con el instalador: `bash instalar.sh` o `instalar.cmd`. Probado en un Ubuntu recién instalado (issues #17-#22) y en una VM con Windows 11 limpia (#53). |
| Al menos 3 acciones propias en `acciones.json` | [acciones.json](../acciones.json) tiene **10** (una de ellas, `repasar-carpeta`, combina cuatro); `mochila validar` → 10 válidas; `mochila acciones` las lista. |
| Ningún secreto en el repo ni en su historial | `.env` en [.gitignore](../.gitignore) desde el primer commit con código; solo se sube [.env.example](../.env.example) con los nombres. `mochila scan-secrets --historial` sale limpio. Hook antes de cada commit (`mochila instalar-hook`). |
| Historial git real (mínimo 10 commits) | Más de 190 commits y más de 60 PR, cada una en su rama: `git log --oneline` y [historial-pr.md](historial-pr.md). |

## Rúbrica

### Acciones predefinidas funcionando (20)

- 10 acciones de 10 tipos: `ordenar` (ordenar), `limpiar-temporales` (borrar), `convertir-webp`
  (convertir), `renombrar-capturas` (renombrar), `copiar-entregas` (copiar), `mover-zips` (mover), y con IA
  `resumir-tema` (resumir), `nombrar-descargas` (renombrar-ia) y `clasificar-asignatura` (clasificar).
- **Combinables** (1.3.0): `repasar-carpeta` es de tipo `secuencia` y ejecuta seguidas
  `limpiar-temporales → renombrar-capturas → convertir-webp → mover-zips`. Cada paso ve lo que dejó el
  anterior, pregunta como siempre y, si uno falla, los demás no se ejecutan. Una combinación nueva es
  editar el JSON: [ADR-0007](adr/0007-acciones-combinables.md) y
  [tests/test_secuencia.py](../tests/test_secuencia.py). Pruébala con `mochila ejecutar repasar-carpeta --simular`.
- Todas tienen `--simular`; las que mueven o borran preguntan antes (`--si` para no preguntar). Nunca
  sobrescriben: si el destino existe, crean `nombre (1).ext`.
- **Sin efectos sorpresa con el destino** (1.3.1): un `destino` relativo, como el `comprimidos` de
  `mover-zips`, se queda dentro de la carpeta que le pasas; uno con `~` es fijo y la tabla de `--simular`
  lo enseña. Pruebas: `test_destino_relativo_va_dentro_de_la_carpeta_y_no_donde_esta_la_terminal` en
  [tests/test_acciones.py](../tests/test_acciones.py).
- Una prueba comprueba que **lo que dice `--simular` es lo que pasa de verdad** en los seis tipos sin IA:
  [tests/test_simular_igual_que_real.py](../tests/test_simular_igual_que_real.py).
- Probadas de verdad (no solo simuladas): entradas del 11-nov y del 19-nov en [prompts.md](prompts.md).

### Configuración externa: `acciones.json` (15)

- Añadir una acción es editar el JSON, sin tocar el código: [ADR-0001](adr/0001-configuracion-externa.md).
- [src/tareas/config.py](../src/tareas/config.py) lo valida todo **antes** de tocar ningún fichero (tipo
  inexistente, destino vacío, sin descripción, regex rota, nombre repetido, JSON roto con su línea).
- Esquema explicado en el [README](../README.md#esquema-de-accionesjson). Skill y comando de OpenCode
  para crear acciones: `.opencode/skills/acciones-json/` y `.opencode/commands/nueva-accion.md`.

### Capa IA, secretos y modo sin red (15)

- 3 acciones con IA (arriba). La IA va detrás de una interfaz, `ProveedorIA`, con dos proveedores: el
  servidor del centro y los modelos gratis de OpenCode ([ADR-0002](adr/0002-proveedor-ia.md),
  [ADR-0004](adr/0004-ia-gratis-opencode.md), [src/tareas/ia.py](../src/tareas/ia.py)).
- La clave solo está en variables de entorno o en `.env` (ignorado): `CENTRO_IA_URL`, `CENTRO_IA_KEY`,
  `CENTRO_IA_CA`.
- Sin clave o sin red: `IANoDisponible`, **código de salida 4**, un mensaje que dice qué hacer y
  «Las acciones sin IA siguen funcionando». `mochila comprobar-ia` lo prueba. Probado en clase
  rompiéndolo a propósito (sin clave, URL mala, clave mala y sin certificado → `echo $?` da 4): entrada
  del 19-nov en [prompts.md](prompts.md). Vuelto a probar el 25-nov desde mi portátil con Windows:
  «Hola» en 0,2 s, y con una clave falsa, «responde 401: la clave no es válida» (entrada del 25-nov).

### Robustez: excepciones y entradas erróneas (15)

- Excepciones propias en [src/tareas/errores.py](../src/tareas/errores.py): `TareasError`, `ConfigError`,
  `AccionNoValida`, `GitError` e `IANoDisponible`.
- Códigos de salida: 0 bien · 1 acción que no existe o fallo de una acción · 2 uso incorrecto (opción que
  no existe, en español) · 3 `acciones.json` mal (con la línea, sin traza) · 4 IA no disponible.
- Ningún error previsible enseña un `Traceback`: entrada «Repaso de los errores amables» (13-nov) en
  [prompts.md](prompts.md), con 26 errores provocados.

### Pruebas y calidad (15)

- `uv run pytest` → **675 pruebas que pasan** (y 1 que se salta según el sistema: hay pruebas solo de Windows o que necesitan permisos). Las de la Sesión 4 están en
  [conftest.py](../tests/conftest.py), [test_config.py](../tests/test_config.py),
  [test_acciones.py](../tests/test_acciones.py), [test_ia.py](../tests/test_ia.py) y
  [test_cli.py](../tests/test_cli.py) (códigos 0 a 4 con `CliRunner`: `test_codigo_0_…` a `test_codigo_4_…`).
- Ninguna prueba toca carpetas reales ni llama a la IA: la fixture `aislado` (autouse) pone el directorio,
  `HOME` y `USERPROFILE` en `tmp_path` y borra las variables `CENTRO_IA_*`; la IA se prueba con
  `ProveedorFalso`.
- Camino feliz y casos feos con `parametrize` (tipo inexistente, destino vacío, sin descripción, regex
  rota, JSON roto, fichero que no existe...).
- **Roto a propósito:** en `Mover.aplicar` cambié `if not simular:` por `if True:` y falló
  `test_simular_no_toca_nada_ni_crea_carpetas`; con `resumir` preguntando al modelo en `--simular` fallaron
  2 pruebas. Restaurado con `git restore` ([prompts.md](prompts.md), Sesión 3 y Sesión 4).
- GitHub Actions en Ubuntu, Windows y macOS en cada push y PR:
  [.github/workflows/pruebas.yml](../.github/workflows/pruebas.yml) (explicado línea a línea). Pestaña
  **Actions** del repo: en verde.
- Cobertura: `uv run pytest --cov=tareas` → **93 %** del código (`cli.py`, 92 %), medida el 24-nov.

### Diseño en clases y módulos (10)

- Interfaz: [cli.py](../src/tareas/cli.py) (Typer: solo recoge opciones, llama al motor y pinta).
- Motor: [motor.py](../src/tareas/motor.py) (busca los ficheros, aplica el filtro y llama a la acción).
- Acciones: [acciones.py](../src/tareas/acciones.py), una clase base `Accion` con una subclase por tipo
  (`Mover`, `Copiar`, `Renombrar`, `Borrar`, `Ordenar`, `Convertir`) y `AccionIA` para las de IA
  (`Resumir`, `RenombrarIA`, `Clasificar`).
- Proveedor de IA: [ia.py](../src/tareas/ia.py) (`ProveedorIA` → `ProveedorCentro`, `ProveedorOpenCode`).
- Configuración: [config.py](../src/tareas/config.py). Errores: [errores.py](../src/tareas/errores.py).
  Lo demás (almacén, seguridad, proyectos) en su propio módulo: lista en [AGENTS.md](../AGENTS.md).

### Instalación, documentación y proceso (10)

- Instalación en una orden (`uv tool install git+…@v1.3.0`), primeros pasos, IA opcional y
  desinstalación: [README](../README.md).
- `pyproject.toml` y `src/tareas/__init__.py` con la misma versión (una prueba lo comprueba);
  `mochila version` la enseña.
- [CHANGELOG.md](../CHANGELOG.md) en formato Keep a Changelog, revisado a mano. El borrador que hizo la IA
  está tal cual en [changelog-borrador.md](changelog-borrador.md), y en [prompts.md](prompts.md) (19-nov)
  apunto en qué se equivocó.
- Rama `release-1.0` con su PR (#16), etiqueta `v1.0.0` y su release; después `release-1.1` (#48) y
  `release-1.2`, `release-1.2.1`, `release-1.2.2` y `release-1.3.0`.
- Revisor con `opencode run`: [scripts/revisar.sh](../scripts/revisar.sh) (agente de solo lectura
  `.opencode/agents/revisor.md`, permisos exactos en [opencode.json](../opencode.json), máximo 180 s,
  sale con 0 solo si dice `VEREDICTO: OK`). Resultados reales en [prompts.md](prompts.md) (17 y 19-nov).
- Instalación en otros equipos e issues: #17-#22 (Ubuntu recién instalado), #46 (un compañero de DAW en
  Windows 11 LTSC) y #53 (VM con Windows 11 limpio, siguiendo solo el README como alumno de 1º de ASIR; la hice yo).
  Cada fallo con su issue, arreglado con «Closes #N» y publicado en una versión. Y la de otra persona
  de verdad (25 y 26-nov): un amigo, en su portátil con Windows 10 y **con su cuenta de GitHub**, abrió
  él sus issues (#69, #70 y #71), arreglados y publicados en la 1.2.2. Qué probó y con qué
  resultado: [prompts.md](prompts.md) (entrada del 25 y 26-nov).
- ADR: [0001](adr/0001-configuracion-externa.md) a [0007](adr/0007-acciones-combinables.md). La spec: [spec.md](spec.md).

## Las preguntas de la defensa: dónde está la respuesta

| Pregunta | Dónde |
|---|---|
| Por qué las acciones viven en un JSON | [ADR-0001](adr/0001-configuracion-externa.md) |
| Qué viaja por la red en una acción con IA | [ADR-0002](adr/0002-proveedor-ia.md) y [ia.py](../src/tareas/ia.py): las instrucciones de la acción y el texto del documento (recortado y entre `<documento>`), nunca el fichero entero; la clave va en la cabecera `Authorization`, por HTTPS |
| Qué pasa sin red | Código 4 y mensaje claro: `test_codigo_4_ia_sin_clave_y_las_demas_siguen` en [test_cli.py](../tests/test_cli.py) |
| Qué comprueba una prueba y qué cambio la pondría en rojo | `test_simular_no_toca_nada_ni_crea_carpetas` en [test_acciones.py](../tests/test_acciones.py): quitar el `if not simular:` de `Mover.aplicar` |
| Por qué un proveedor falso en las pruebas | Las pruebas no pueden depender de la red ni gastar llamadas, y tienen que dar siempre lo mismo: `ProveedorFalso` en [conftest.py](../tests/conftest.py) |
| Qué corregí del trabajo del agente | [prompts.md](prompts.md): cada entrada tiene «Qué corregí» y «Qué aprendí» |
