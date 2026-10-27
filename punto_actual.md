# Punto actual del proyecto

> **Cambio de nombre (27/10 noche):** el comando ya NO es `gabriel` (chocaba con otra herramienta de tu terminal), ahora es **`dam`**. Variable del almacén: `DAM_ALMACEN`. Config global: `~/.config/dam/acciones.json`. Tras actualizar `pyproject.toml`: `uv tool uninstall tareas` y `uv tool install --editable .`

**Fecha:** 2026-10-27 (noche, en casa, Windows)
**Proyecto:** `dam` / paquete `tareas` (carpeta `Terminal_CLI`)
**Repo:** https://github.com/gabi37smx/Terminal_CLI

## Qué hay hecho

- [x] Puntos 0-4 de la Sesión 1: terminal, herramientas, proyecto con uv, `.gitignore`/`.gitattributes`, `opencode.json` y `AGENTS.md`.
- [x] Recuperado de tu código original: extensiones temporales (.temp, .cache, .swp, .download, .crdownload), `.db`/`.htm`, y la confirmación antes de mover o convertir (`"confirmar": true`).
- [x] Punto 5: spec v0 en `README.md`, `listar` y `version`.
- [x] Punto 6: configuración, `validar`, `acciones`, `ejecutar --simular`.
- [x] Casa (Windows) preparada: uv 0.13.6, Python 3.12.16, OpenCode 1.18.35, `uv sync` y `uv run dam --help` funcionan.
- [x] Comando renombrado a `dam` (`[project.scripts] dam = "tareas.cli:app"`).

## Qué se ha rehecho esta noche (revisión frente a la Sesión 2 del profe)

El código nuevo se ha probado con **68 tests (pytest)**, también en Windows (27/10 noche).

- [x] `acciones.json` sustituye a `tareas.toml` (el profe lo exige y es un mínimo eliminatorio). Tus 3 acciones se mantienen: `ordenar`, `limpiar-temporales`, `convertir-webp`.
- [x] `errores.py`: `TareasError` (1), `ConfigError` (3), `AccionNoValida` (3) y `GitError` (1).
- [x] `config.py`: valida todo antes de tocar nada; los mensajes dicen acción y campo; acepta el BOM de PowerShell.
- [x] `acciones.py` y `motor.py`: clase base `Accion`, fábrica `desde_config` con registro (sin if por tipo) y las clases `Mover`, `Copiar`, `Renombrar`, `Borrar`, `Ordenar`, `Convertir`.
- [x] `cli.py`: `--config`, `listar`, `validar`, `acciones`, `ejecutar --simular/--si` (confirmación en español: s/sí/y) y las nuevas `status` y `sync`.
- [x] `sincronizar.py`: almacén git en Python (subprocess sin shell). `status` y `sync [asignatura] [mensaje]` con `--integrar` y `--simular`.
- [x] `ordenar`: tu versión original YA comparaba palabras completas (`\b`); mi comentario sobre «so» era erróneo. `diagrama_redes.png` y `practicas_linux.txt` van a `sistemas` porque «redes» y «linux» son palabras clave de esa carpeta: si no lo quieres, cambia `acciones.json`. Se conserva tu lógica (nombre, extensión, PDF) y la carpeta cuenta como palabra clave.
- [x] Añadidos `.opencode/skills/acciones-json/`, `.opencode/commands/nueva-accion.md` y `.opencode/agents/revisor.md`.
- [x] `opencode.json` y `AGENTS.md` actualizados al comando `dam` (antes permitían `uv run tareas ...` y no coincidía nada). `sync` y `ejecutar` quedan en `ask`.
- [x] `docs/adr/0001-configuracion-externa.md`: redactado en primera persona (revísalo y ajústalo a tu forma de hablar).
- [x] README con el esquema, las órdenes, el almacén y los códigos de salida.

## Qué falta (por orden)

1. Copiar los ficheros nuevos al repo (hacer antes copia de seguridad de `src\tareas`, que NO está en git) y ejecutar `uv add --dev pytest` y `uv run pytest` **en Windows**.
2. Borrar `tareas.toml` y `~/pruebas-tareas/mala.toml` (ya no sirven).
3. Reescribir el ADR con tus razones.
4. Crear el almacén: repo privado `DAM-almacen` en GitHub, clonarlo en `~/DAM-almacen` y probar `dam status` y `dam sync --simular` ahí (nunca en `Terminal_CLI`).
5. Probar las 3 acciones de verdad (sin `--simular`) en `~/pruebas-tareas/prueba-final`.
6. Usar `/nueva-accion` para añadir una 4ª acción tuya y `@revisor` antes de commitear.
7. Crear `docs/prompts.md` con los prompts y lo que corregiste.
8. Merge a `main` y `git push` (los haces tú).
9. Instalar en casa y en clase: `uv tool install --editable .`

## Commits sugeridos (los haces tú; objetivo: ≥10 en total)

```powershell
git switch -c feature/acciones-json
git add acciones.json README.md ; git commit -m "Pasa la configuración a acciones.json con mis 3 acciones y documenta el esquema"
git add src/tareas/errores.py ; git commit -m "Añade excepciones propias con código de salida: TareasError, ConfigError, AccionNoValida"
git add src/tareas/config.py ; git commit -m "Valida acciones.json antes de ejecutar y dice qué acción y qué campo fallan"
git add src/tareas/acciones.py src/tareas/motor.py ; git commit -m "Clases Accion con fábrica y motor: --simular no toca el disco y nunca sobrescribe"
git add src/tareas/cli.py src/tareas/__main__.py ; git commit -m "Órdenes validar, acciones y ejecutar con tabla Rich, --si y --config"
git add src/tareas/sincronizar.py ; git commit -m "Añade el almacén git: status y sync seguros entre clase, casa y USB"
git add tests pyproject.toml uv.lock ; git commit -m "Añade pruebas con pytest de config, acciones y sincronización"
git add .opencode ; git commit -m "Skill acciones-json, comando /nueva-accion y subagente revisor de solo lectura"
git add opencode.json AGENTS.md ; git commit -m "Actualiza permisos y normas al comando dam"
git add docs/adr/0001-configuracion-externa.md ; git commit -m "ADR-0001: por qué configuración externa"
git rm tareas.toml   # solo si estaba en git; si no, bórralo a mano
```

## Cómo retomar

```powershell
cd "C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\PROJECTE TERMINAL CLI\Terminal_CLI"
uv sync
uv run pytest
uv run dam --help
uv run dam validar
```

## Recordatorios

- `Sesion1.md` es material del profesor y no se sube al repo.
- Los commits y el push los haces tú. El agente no ejecuta `sync` ni `ejecutar`.
- Probar siempre en `~/pruebas-tareas` y con `--simular` primero.
- Si se cambia `opencode.json`, cerrar y volver a abrir OpenCode.
- Nada de claves en el repo ni en su historial (mínimo eliminatorio). Un repo del almacén con apuntes: privado.