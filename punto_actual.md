# Punto actual del proyecto

> **Cambio de nombre (27/10 noche):** el comando ya NO es `gabriel` (chocaba con otra herramienta de tu terminal), ahora es **`dam`**. Variable del almacén: `DAM_ALMACEN`. Config global: `~/.config/dam/acciones.json`.

**Fecha:** 2026-11-01 (en casa, Windows)
**Proyecto:** `dam` / paquete `tareas` (carpeta `Terminal_CLI`)
**Repo:** https://github.com/gabi37smx/Terminal_CLI
**Estado:** en GitHub, `main` tenía 24 commits (último: 29-oct, documentación del flujo clase/casa). Todo lo de `scan-secrets` y lo posterior estaba **solo en local** hasta subir la rama `feature/seguridad-y-web` (ver «Qué falta»).

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
- [x] Escrito el 1-nov, **pendiente de que lo ejecutes tú en Windows**: `dam instalar-hook`, `dam test-links` y `dam check-headers`, con sus tests; aserciones en `acciones.py` y `motor.py` (script `aplicar_aserciones.py`); `docs/prompts.md`; README, `docs/comandos.md` y `AGENTS.md` actualizados.

## Qué falta (por orden)

1. Subir lo pendiente: rama `feature/seguridad-y-web`, commits pequeños, `git push -u origin feature/seguridad-y-web`, pull request y merge a `main`.
2. `uv run pytest -q` desde la **raíz** del repo y apuntar aquí el resultado (sin contar los tests nuevos de web y hook, el último dato fue 75 pruebas el 29-oct).
3. Probar `dam test-links` y `dam check-headers` contra mi portfolio y mi backend de Render; apuntar qué salió y qué arreglé en `docs/prompts.md`.
4. Probar las 3 acciones de verdad (sin `--simular`) en `~/pruebas-tareas/prueba-final` y apuntar el resultado. No está confirmado que las 3 se hayan ejecutado.
5. Añadir una 4.ª acción con `/nueva-accion`, pasar `@revisor` y `/review`, y rellenar los **[COMPLETAR]** de `docs/prompts.md` con lo que hice en clase.
6. `dam instalar-hook` en `Terminal_CLI` y en `DAM-almacen`.
7. Instalar en otro equipo con `uv tool install git+https://github.com/gabi37smx/Terminal_CLI` y seguir solo el README (sin probar todavía).
8. **Comprobación de proceso del 6 nov (semipresencial):** 3 acciones propias funcionando, ADR y commits reales.

Después (semanas 3 y 4): capa IA y modo sin red, 5 o más acciones propias, pruebas en GitHub Actions, release v1.0.

## Cómo retomar

```powershell
cd "C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\PROJECTE TERMINAL CLI\Terminal_CLI"
uv sync
uv run pytest -q
dam -h
dam validar
dam status
dam scan-secrets --historial
```

## Recordatorios

- `Sesion1.md` es material del profesor y, aun así, está subido al repo público (se ve en GitHub). Decidir si se saca: `git rm --cached Sesion1.md` + una línea en `.gitignore`. Seguirá en el historial.
- Los commits y el push los haces tú; el agente solo commitea si se lo pides expresamente. El agente no ejecuta `sync` ni `ejecutar`.
- Probar siempre en `~/pruebas-tareas` y con `--simular` primero.
- Si se cambia `opencode.json`, cerrar y volver a abrir OpenCode.
- Nada de claves en el repo ni en su historial (mínimo eliminatorio). Un repo del almacén con apuntes: privado.
- Lo que no sé explicar, no lo entrego: antes del 6 nov, repasar `config.py`, `acciones.py`, `motor.py` y los tres módulos nuevos (`escanear.py`, `web.py`, `hook.py`) hasta poder explicar cada aserción.
