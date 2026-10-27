# Punto actual del proyecto

**Fecha:** 2026-10-27 (tarde)
**Proyecto:** `tareas` (carpeta `Terminal_CLI`)
**Repo:** https://github.com/gabi37smx/Terminal_CLI

## Qué hay hecho

- [x] Punto 0-1 · Terminal y carpeta de pruebas (`~/pruebas-tareas`).
- [x] Punto 2 · Instalados git, uv 0.13.5 y Python 3.12.15.
  - OpenCode instalado: 1.18.32 (el enunciado pide 1.18.35; pendiente de actualizar).
- [x] Punto 3 · Proyecto creado con `uv init --package --name tareas --python 3.12 .`
  - `pyproject.toml`: descripción y `tareas = "tareas.cli:app"`.
  - `src/tareas/__init__.py`: solo docstring y `__version__ = "0.1.0"`.
  - `.gitignore` con `.venv/`, cachés y `.env`.
  - `.gitattributes` con `* text=auto`.
  - Primer commit hecho: `Crea el proyecto con uv y Typer, con .gitignore y .gitattributes`.
- [x] Punto 4 · `opencode.json` con los permisos del agente y `AGENTS.md` con las normas.
- [x] Punto 5.1 · Spec v0 escrita en `README.md` (10 puntos + ideas futuras).
- [x] Punto 5.2 · Plan de `cli.py` explicado y aprobado (27/10).
- [x] Punto 5.3 · Implementado `src/tareas/cli.py` (`version` y `listar`) y `src/tareas/__main__.py`.
  - Working en rama `feature/cli-listar` (main intacta).
  - Probado en `~/pruebas-tareas`: carpeta con espacios y corchetes, `/no/existe` (salida 2), fichero en vez de carpeta (salida 2), carpeta vacía (salida 0).
- [x] Instalado como comando real con `uv tool install --editable .` · funciona `tareas` desde cualquier carpeta.
- [x] Punto 6 · Comandos de configuración implementados y probados.
  - `src/tareas/config.py`: lee `tareas.toml` con `tomllib` (busca en el directorio actual o en `~/.config/tareas/`).
  - `tareas validar` (salida 3 si es inválida), `tareas acciones` (tabla Rich), `ejecutar NOMBRE --simular` (sin `--simular` se niega, salida 1).
  - Probado en `~/pruebas-tareas`: config válida (0), TOML roto (3), config inexistente (3), acción inexistente (2), simulación sin tocar ficheros (0). Queda `~/pruebas-tareas/mala.toml` de prueba (el alumno lo borra: `rm ~/pruebas-tareas/mala.toml`).
- [x] Lógica real de las 3 acciones en `src/tareas/acciones.py` (nuevo):
  - `ordenar`: clasifica por palabras clave del nombre, extensión (.py/.sql/.xml/.html/.sh...) y contenido de las 3 primeras/últimas páginas de PDFs (con pypdf). Mueve con `rename` sin sobrescribir (añade " (1)" si collide).
  - `limpiar-temporales`: borra .tmp/.bak/.part... con más de N días (mtime).
  - `convertir-webp`: convierte JPEG/PNG a WebP con Pillow, sin tocar el original ni duplicar si ya existe el .webp.
  - Depuradas en `~/pruebas-tareas`: hay carpetas de asignatura (programacion, bases-datos...) y ficheros de prueba; `~/pruebas-tareas/prueba-final` es la carpeta limpia de simulación.
- [x] Añadidas dependencias `pillow` y `pypdf` al pyproject (uv sync hecho).
- [x] ⚠️ El comando se RENOMBRÓ: en `pyproject.toml` ahora `[project.scripts] gabriel = "tareas.cli:app"`. El comando es `gabriel`, NO `tareas` (reinstalar con `uv tool install --editable .` si hace falta).
- [x] Acciones en el TOML renombradas: `ordenar`, `limpiar-temporales`, `convertir-webp` (ya no "organizar-descargas"). Simulación de las 3 verificada OK en `~/pruebas-tareas/prueba-final` sin tocar ficheros.

## Qué falta (por orden)

1. Ejecutar las 3 acciones de VERDAD (sin `--simular`, con confirmación) en `~/pruebas-tareas/prueba-final` y comprobar el resultado. Ojo: el `ordenar` de simulación clasifica `diagrama_redes.png` y `practicas_linux.txt` en `sistemas` por error (falta afinar palabras clave).
2. Tests con pytest (semana 4): `uv add --dev pytest` y probar `config.py` y `acciones.py`.
3. Crear `docs/prompts.md` con los prompts y correcciones.
4. Merge de `feature/cli-listar` a main (commit y push los hace el alumno).
5. Decidir el nombre definitivo del comando (`gabriel` vs `tareas`) y ajustar AGENTS.md/README si procede.
6. Pendiente: commit de los ficheros nuevos sin seguimiento (`cli.py`, `config.py`, `acciones.py`, `__main__.py`, `tareas.toml`) — los hace el alumno.

## Cómo retomar

```bash
cd ~/Documents/Proyecto_CLI/Terminal_CLI
export PATH="$HOME/.local/bin:$PATH"
uv sync
git log --oneline
uv run gabriel --help   # ya funciona: version, listar, validar, acciones, ejecutar
```

## Recordatorios

- `Sesion1.md` es material del profesor y no se sube al repo (queda sin seguimiento).
- Los commits y el push los hace el alumno.
- Antes de probar la herramienta, usar siempre `~/pruebas-tareas`, nunca carpetas reales.
- Si se cambia `opencode.json`, hay que cerrar y volver a abrir OpenCode.
