# Punto actual del proyecto

> **Cambio de nombre (27/10 noche):** el comando ya NO es `gabriel` (chocaba con otra herramienta de tu terminal), ahora es **`dam`**. Variable del almacén: `DAM_ALMACEN`. Config global: `~/.config/dam/acciones.json`.

**Fecha:** 2026-11-03 (en casa, Windows)
**Proyecto:** `dam` / paquete `tareas` (carpeta `Terminal_CLI`)
**Repo:** https://github.com/gabi37smx/Terminal_CLI
**Estado:** en GitHub hay 42 commits; falta subir `054b63f` y la documentación completada el 3-nov; la rama `feature/seguridad-y-web` ya entró con el PR #2 (1-nov). Lo del 3-nov se subió en dos tandas: primero `demo.md` completado, `Sesion1.md` fuera del repo, este punto actual y 2 acciones nuevas; después, los `[COMPLETAR]` de `docs/prompts.md` y esta línea. Para comprobar que no queda nada sin subir: `git log --oneline origin/main..` (si no sale nada, está al día).
**Tests:** `uv run pytest -q` → **162 passed** (3-nov, desde la raíz).

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

## Qué falta (por orden)

1. Antes de cerrar, `git log --oneline origin/main..`: si sale algún commit, `git push`.
2. Probar de verdad (sin `--simular`) en `~/pruebas-tareas` las 3 acciones antiguas (`ordenar`, `limpiar-temporales`, `convertir-webp`) y apuntar el resultado. No está confirmado que se hayan ejecutado. (`renombrar-capturas` y `copiar-entregas` ya están probadas de verdad.)
3. Pasar `@revisor` sobre `renombrar-capturas` y `copiar-entregas` (en `mover-zips` ya está), pasar `/review` y rellenar los **[COMPLETAR]** de `docs/prompts.md` con lo que hice en clase.
4. `dam instalar-hook` en `DAM-almacen` (en `Terminal_CLI` ya está).
5. Pendiente del portfolio: borrar o excluir `_backup_mejoras/` (67 enlaces rotos, todos ahí).
6. Instalar en otro equipo con `uv tool install git+https://github.com/gabi37smx/Terminal_CLI` y seguir solo el README (sin probar todavía).
7. **Comprobación de proceso del 6 nov (semipresencial):** 3 acciones propias funcionando, ADR y commits reales.

Después (semanas 3 y 4): capa IA y modo sin red (las 5 o más acciones propias ya están: hay 6), pruebas en GitHub Actions, release v1.0.

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

- Los commits y el push los haces tú; el agente solo commitea si se lo pides expresamente. El agente no ejecuta `sync` ni `ejecutar`.
- Probar siempre en `~/pruebas-tareas` y con `--simular` primero.
- Si se cambia `opencode.json`, cerrar y volver a abrir OpenCode.
- Nada de claves en el repo ni en su historial (mínimo eliminatorio). Un repo del almacén con apuntes: privado.
- Lo que no sé explicar, no lo entrego: antes del 6 nov, repasar `config.py`, `acciones.py`, `motor.py` y los tres módulos nuevos (`escanear.py`, `web.py`, `hook.py`) hasta poder explicar cada aserción.
