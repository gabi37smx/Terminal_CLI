# dam · CLI de tareas con ficheros (proyecto de 1º DAM)

## Stack y órdenes
- Python 3.12 + Typer + Rich (+ Pillow y pypdf), gestionado con uv (src layout, paquete src/tareas).
- El comando se llama `dam`. Ejecutar: `uv run dam --help` · Validar config: `uv run dam validar` · Pruebas: `uv run pytest`.
- Módulos: errores.py, config.py (valida acciones.json), acciones.py (clases Accion), motor.py, sincronizar.py (almacén git), cli.py (solo interfaz).

## Normas
- Mensajes y comentarios en español; código claro antes que listo.
- pathlib siempre, encoding="utf-8", nada de os.system ni shell=True: tiene que funcionar en Linux, Windows y macOS.
- git solo con subprocess y lista de argumentos. Nunca ejecutes `dam sync` ni `dam ejecutar`: los ejecuta el alumno.
- Nunca ejecutes acciones sobre carpetas reales: solo en ~/pruebas-tareas y con --simular. Los tests de sync usan repos temporales (tmp_path), nunca el repo real.
- No toques .env ni escribas claves en ningún fichero. No hagas git push ni commits: los hace el alumno.
- Antes de cambiar un fichero, explica en 2-3 líneas qué vas a hacer.
