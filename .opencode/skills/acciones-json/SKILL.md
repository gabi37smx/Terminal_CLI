---
name: acciones-json
description: Reglas del fichero acciones.json de la CLI dam (campos, tipos, filtros, plantillas, sección almacen y validación). Úsala siempre que crees o cambies acciones o el código que las lee (config.py, acciones.py, motor.py, sincronizar.py).
---
# Esquema de acciones.json
- Raíz: {"version": 1, "acciones": [...], "almacen": {"ruta": "~/DAM-almacen", "asignaturas": "asignaturas"}}. «almacen» es opcional.
- Cada acción: nombre (único, minúsculas-con-guiones), descripcion, tipo, y opcionales origen, destino, filtro, confirmar.
- Tipos: mover y copiar (requieren destino), renombrar (requiere plantilla), borrar (requiere filtro; siempre pide confirmación salvo --si),
  ordenar (requiere carpetas: {"asignatura": ["palabras clave"]}; opcional por_extension: {".sql": "asignatura"}),
  convertir (JPEG/PNG a WebP; opcional calidad 1-100).
- filtro opcional: extensiones (lista con punto), patron (regex válida), mas_antiguo_que_dias, mayor_que_mb. Si hay varios, se cumplen todos.
- plantilla: huecos {fecha:%Y-%m-%d}, {n:03}, {ext}, {nombre}; sin caracteres prohibidos en Windows.
## Reglas al programar
- Valida el JSON en config.py ANTES de ejecutar; errores con AccionNoValida(accion, campo, motivo) (código de salida 3).
- pathlib y shutil; encoding="utf-8"; nunca shell=True; nunca sobrescribir (destino_libre, que también reserva nombres en simulación).
- Toda acción admite --simular y devuelve list[Resultado]; con simular=True no se llama a mkdir, move, rename, unlink ni save.
- Las palabras clave de «ordenar» se comparan como palabras COMPLETAS, sin tildes ni mayúsculas.
- Si añades un campo o un tipo nuevo, documéntalo en el README y en esta skill, y añade su test.
