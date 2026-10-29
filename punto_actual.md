# Punto actual del proyecto

> **Cambio de nombre (27/10 noche):** el comando ya NO es `gabriel` (chocaba con otra herramienta de tu terminal), ahora es **`dam`**. Variable del almacén: `DAM_ALMACEN`. Config global: `~/.config/dam/acciones.json`. Tras actualizar `pyproject.toml`: `uv tool uninstall tareas` y `uv tool install --editable .`

**Fecha:** 2026-10-29 (en casa, Windows)
**Proyecto:** `dam` / paquete `tareas` (carpeta `Terminal_CLI`)
**Repo:** https://github.com/gabi37smx/Terminal_CLI
**Estado:** **75 tests**; **22 commits** (23 con el commit de cierre); `main` al día con `origin/main` antes de ese commit.

## Qué hay hecho

- [x] Puntos 0-4 de la Sesión 1: terminal, herramientas, proyecto con uv, `.gitignore`/`.gitattributes`, `opencode.json` y `AGENTS.md`.
- [x] Recuperado de tu código original: extensiones temporales (.temp, .cache, .swp, .download, .crdownload), `.db`/`.htm`, y la confirmación antes de mover o convertir (`"confirmar": true`).
- [x] Punto 5: spec v0 en `README.md`, `listar` y `version`.
- [x] Punto 6: configuración, `validar`, `acciones`, `ejecutar --simular`.
- [x] Casa (Windows) preparada: uv 0.13.6, Python 3.12.16, OpenCode 1.18.35, `uv sync` y `uv run dam --help` funcionan.
- [x] Comando renombrado a `dam` (`[project.scripts] dam = "tareas.cli:app"`).

## Qué se ha rehecho (revisión frente a la Sesión 2 del profe)

El código se ha probado con **75 tests (pytest)**, también en Windows (29/10).

- [x] `acciones.json` sustituye a `tareas.toml` (mínimo eliminatorio). Tus 3 acciones: `ordenar`, `limpiar-temporales`, `convertir-webp`.
- [x] `errores.py`: `TareasError` (1), `ConfigError` (3), `AccionNoValida` (3) y `GitError` (1).
- [x] `config.py`: valida todo antes de tocar nada; los mensajes dicen acción y campo; acepta el BOM de PowerShell.
- [x] `acciones.py` y `motor.py`: clase base `Accion`, fábrica `desde_config` con registro (sin if por tipo) y las clases `Mover`, `Copiar`, `Renombrar`, `Borrar`, `Ordenar`, `Convertir`.
- [x] `cli.py`: `--config`, `listar`, `validar`, `acciones`, `ejecutar --simular/--si` (confirmación en español: s/sí/y), `status` y `sync`.
- [x] `sincronizar.py`: almacén git en Python (subprocess sin shell). `status` y `sync [asignatura] [mensaje]` con `--integrar` y `--simular`.
- [x] `ordenar`: compara palabras completas (`\b`); `diagrama_redes.png` y `practicas_linux.txt` van a `sistemas` porque «redes» y «linux» son palabras clave de esa carpeta.
- [x] `docs/adr/0001-configuracion-externa.md` redactado en primera persona.
- [x] `.opencode/skills/acciones-json/`, `.opencode/commands/nueva-accion.md` y `.opencode/agents/revisor.md`.
- [x] `opencode.json` y `AGENTS.md` actualizados al comando `dam`. `sync` y `ejecutar` quedan en `ask`.
- [x] README con el esquema, las órdenes, el almacén y los códigos de salida.
- [x] Almacén privado `DAM-almacen` clonado en `C:\Users\HP\DAM-almacen` y subido (551 ficheros, ~571 MB). `DAM_ALMACEN` definido con `setx`.
- [x] `.gitignore` del almacén excluye MV/OVA, `.env`, credenciales, `node_modules`, `.venv`, etc.
- [x] Ayuda `dam --help` estilo terminal: `Uso`, `Comandos`, `Opciones` y `Ejemplos`; los subcomandos conservan `--help`. Commit `a1e8c87`.
- [x] `docs/comandos.md`: guía rápida de comandos y ejemplos.
- [x] Guardián de `sync` ampliado: bloquea `.env`, `.env.local`, `clave.env`, `atlas-credentials.env` y `clave.env.local`; permite `.env.example`; no bloquea borrados.

## Qué falta (por orden)

1. Probar las 3 acciones de verdad (sin `--simular`) en `~/pruebas-tareas/prueba-final` y apuntar el resultado. La carpeta existe, pero no está confirmado que las 3 se hayan ejecutado.
2. Añadir una 4ª acción con `/nueva-accion` y pasar `@revisor` antes de commitear.
3. Crear `docs/prompts.md` con los prompts y lo que corregiste.
4. Instalar en clase: `uv tool install --editable .` y comprobar `dam --help` / `dam validar`.
5. Siguiente comando propuesto: `scan-secrets` (busca `mongodb+srv`, `re_`, `ghp_`, `AIza`, `sk-`, claves PEM...). No se ha empezado.

## Commits

- **22 commits** en total (objetivo ≥10, cumplido). Con el commit de cierre, **23**.
- Último con hash conocido: `a1e8c87` — ayuda de `dam` con uso, comandos, opciones y ejemplos.
- Commit de cierre: guardián `.env` + este documento.

## Cómo retomar

```powershell
cd "C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\PROJECTE TERMINAL CLI\Terminal_CLI"
uv sync
uv run pytest
uv run dam --help
uv run dam validar
uv run dam status
```

## Recordatorios

- `Sesion1.md` es material del profesor y no se sube al repo.
- Los commits y el push los haces tú; el agente solo commitea si se lo pides expresamente. El agente no ejecuta `sync` ni `ejecutar`.
- Probar siempre en `~/pruebas-tareas` y con `--simular` primero.
- Si se cambia `opencode.json`, cerrar y volver a abrir OpenCode.
- Nada de claves en el repo ni en su historial (mínimo eliminatorio). Un repo del almacén con apuntes: privado.
