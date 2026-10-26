# Punto actual del proyecto

**Fecha:** 2026-10-26
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
- [ ] Punto 5.2 · Plan de `cli.py` explicado (pendiente de aprobar).
- [ ] Punto 5.3 · Implementar `src/tareas/cli.py` y `src/tareas/__main__.py`.

## Qué falta (por orden)

1. Aprobar el plan y crear `src/tareas/cli.py` con `version` y `listar`.
2. Crear `src/tareas/__main__.py` para que funcione `python -m tareas`.
3. Probar en `~/pruebas-tareas` (carpeta vacía, ruta con espacios, corchetes, `/no/existe`).
4. Instalar como comando real: `uv tool install --editable .`.
5. Crear `docs/prompts.md` con los prompts y correcciones.
6. Hacer commit final y `git push`.

## Cómo retomar

```bash
cd ~/Documents/Proyecto_CLI/Terminal_CLI
export PATH="$HOME/.local/bin:$PATH"
uv sync
git log --oneline
uv run tareas --help   # todavía fallará: falta cli.py (es lo esperado)
```

## Recordatorios

- `Sesion1.md` es material del profesor y no se sube al repo (queda sin seguimiento).
- Los commits y el push los hace el alumno.
- Antes de probar la herramienta, usar siempre `~/pruebas-tareas`, nunca carpetas reales.
- Si se cambia `opencode.json`, hay que cerrar y volver a abrir OpenCode.
