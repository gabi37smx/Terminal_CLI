---
name: acciones-json
description: Reglas del fichero acciones.json de la CLI dam (campos, tipos, filtros, plantillas, sección almacen y validación). Úsala siempre que crees o cambies acciones o el código que las lee (config.py, acciones.py, motor.py, sincronizar.py).
---
# Esquema de acciones.json
- Raíz: {"version": 1, "acciones": [...], "almacen": {"ruta": "~/DAM-almacen", "asignaturas": "asignaturas"}}. «almacen» es opcional.
- Cada acción: nombre (único, minúsculas-con-guiones), descripcion, tipo, y opcionales origen, destino, filtro, confirmar.
- Tipos: mover y copiar (requieren destino), renombrar (requiere plantilla), borrar (requiere filtro; siempre pide confirmación salvo --si),
  ordenar (requiere carpetas: {"asignatura": ["palabras clave"]}; opcional por_extension: {".sql": "asignatura"}),
  convertir (JPEG/PNG a WebP; opcional calidad 1-100). Con IA: resumir, renombrar-ia y clasificar (ver abajo).
- filtro opcional: extensiones (lista con punto), patron (regex válida), mas_antiguo_que_dias, mayor_que_mb. Si hay varios, se cumplen todos.
- plantilla: huecos {fecha:%Y-%m-%d}, {n:03}, {ext}, {nombre}; sin caracteres prohibidos en Windows.
## Reglas al programar
- Valida el JSON en config.py ANTES de ejecutar; errores con AccionNoValida(accion, campo, motivo) (código de salida 3).
- pathlib y shutil; encoding="utf-8"; nunca shell=True; nunca sobrescribir (destino_libre, que también reserva nombres en simulación).
- Toda acción admite --simular y devuelve list[Resultado]; con simular=True no se llama a mkdir, move, rename, unlink ni save.
- Las palabras clave de «ordenar» se comparan como palabras COMPLETAS, sin tildes ni mayúsculas.
- Si añades un campo o un tipo nuevo, documéntalo en el README y en esta skill, y añade su test.
## Acciones con IA (semana 3)
- Tipos con IA (TIPOS_IA en config.py): resumir, renombrar-ia y clasificar (clasificar pide categorias y destino; en resumir, destino es opcional).
- Campos: instrucciones (texto: el prompt del usuario), max_caracteres (500-50000, por defecto 12000) y categorias (solo clasificar; lista sin repetir). En tipos sin IA, estos campos son un error.
- La IA va SIEMPRE por ProveedorIA (src/tareas/ia.py): las acciones no importan httpx. ProveedorCentro.desde_entorno() lee CENTRO_IA_URL, CENTRO_IA_KEY, CENTRO_IA_CA y CENTRO_IA_MODELO (o un .env, que nunca se lee ni se sube).
- --simular no llama al modelo (solo «enviaría N caracteres»). Un PDF sin texto se salta sin preguntar.
- La respuesta del modelo nunca se usa tal cual: nombres por a_nombre_seguro(), categorías solo de la lista (si no, sin-clasificar).
- Sin clave o sin red: IANoDisponible (sale con 4); las acciones sin IA siguen funcionando. Si se cae a mitad, lo hecho se queda y el resto no se toca.
- Las pruebas usan ProveedorFalso (tests/conftest.py): nunca el servidor de verdad.
