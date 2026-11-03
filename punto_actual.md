# Punto actual del proyecto

> **Cambio de nombre (27/10 noche):** el comando ya NO es `gabriel` (chocaba con otra herramienta de tu terminal), ahora es **`dam`**. Variable del almacén: `DAM_ALMACEN`. Config global: `~/.config/dam/acciones.json`.

**Fecha:** 2026-11-03 (en casa, Windows)
**Proyecto:** `dam` / paquete `tareas` (carpeta `Terminal_CLI`)
**Repo:** https://github.com/gabi37smx/Terminal_CLI
**Estado:** `main` subido a GitHub hasta `1f34747` (3-nov, tarde): instalador (`40ff2e5`, lo subí yo), `dam help` (`7e62593`) y autocompletado con TAB (`1f34747`), estos dos los subió Claude Code porque se lo pedí. La rama `feature/seguridad-y-web` ya entró con el PR #2 (1-nov). Esta actualización de `punto_actual.md` y `docs/prompts.md` también la subió Claude Code a petición mía. Para comprobar que no queda nada sin subir: `git log --oneline origin/main..` (si no sale nada, está al día).
**Tests:** `uv run pytest -q` → **173 passed** (3-nov, desde la raíz).

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

## Qué falta (por orden)

1. Antes de cerrar, `git log --oneline origin/main..`: si sale algún commit, `git push`.
2. **Crear el token de GitHub** (Settings → Developer settings → Fine-grained tokens; solo `DAM-almacen`, permiso *Contents: Read and write*). No guardarlo en ningún fichero.
3. **Mañana (4-nov) en el PC de clase (Linux):**
   - Antes de borrar nada, `which uv dam` y `ls ~/.config/dam ~/DAM-almacen`, para confirmar por qué falló (si no sale nada, la carpeta personal estaba vacía: otro PC, otro usuario o se restaura al reiniciar).
   - Borrar y clonar otra vez, `bash instalar.sh` con el token a mano, abrir otra terminal y probar `dam help`, `dam ej<TAB>`, `dam status` y `dam sync --simular`.
   - Apuntar el resultado en `docs/prompts.md` (los **[COMPLETAR]** de la entrada del 3-nov).
4. En Ubuntu (WSL): `git pull` en `~/Terminal_CLI` y `bash instalar.sh` otra vez para tener el TAB y clonar `DAM-almacen` con el token. En Windows: `instalar.cmd` otra vez para el TAB.
5. Probar de verdad (sin `--simular`) en `~/pruebas-tareas` las 3 acciones antiguas (`ordenar`, `limpiar-temporales`, `convertir-webp`) y apuntar el resultado. No está confirmado que se hayan ejecutado. (`renombrar-capturas` y `copiar-entregas` ya están probadas de verdad.)
6. Pasar `@revisor` sobre `renombrar-capturas` y `copiar-entregas` (en `mover-zips` ya está), pasar `/review` y rellenar los **[COMPLETAR]** de `docs/prompts.md` con lo que hice en clase.
7. `dam instalar-hook` en `DAM-almacen` (en `Terminal_CLI` ya está).
8. Pendiente del portfolio: borrar o excluir `_backup_mejoras/` (67 enlaces rotos, todos ahí).
9. Instalar sin clonar con `uv tool install git+https://github.com/gabi37smx/Terminal_CLI` siguiendo solo el README (sin probar todavía; con clon + `instalar.sh` ya está probado en WSL).
10. **Comprobación de proceso del 6 nov (semipresencial):** 3 acciones propias funcionando, ADR y commits reales.

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
- Al ejecutar `uv sync` desde WSL, nunca sobre la carpeta de Windows (`/mnt/c/...`): cambiaría el `.venv` de Windows por uno de Linux.
- Nada de claves en el repo ni en su historial (mínimo eliminatorio). Un repo del almacén con apuntes: privado.
- Lo que no sé explicar, no lo entrego: antes del 6 nov, repasar `config.py`, `acciones.py`, `motor.py` y los tres módulos nuevos (`escanear.py`, `web.py`, `hook.py`) hasta poder explicar cada aserción.
