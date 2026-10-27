# ADR-0001: Las acciones viven en acciones.json, no en el código

- Estado: aceptada
- Fecha: 2026-10-27
- Autor: Gabriel Vidal Badia

## Contexto

Mi herramienta `dam` automatiza tareas repetitivas con ficheros: ordenar apuntes por asignatura de 1º de DAM, borrar temporales viejos y convertir imágenes de cualquier formato a WebP , pensando en el proyecto del portfolio el juego via al cielo. De momento tengo tres acciones (`ordenar`, `limpiar-temporales` y `convertir-webp`), pero la idea es que la use yo en el PC de clase, en el de casa y en un USB, y que mis compañeros puedan usarla con
sus propias asignaturas y carpetas.

El problema es que cada persona tiene carpetas distintas y quiere reglas distintas. Si todo estuviera escrito dentro del código, cualquier cambio pequeño obligaría a tocar Python, volver a instalar y arriesgarse a romper lo que ya funcionaba. Además, un compañero que no programa no podría añadir una acción ni cambiar una palabra clave.

## Decisión

Las acciones se describen en un fichero externo, `acciones.json`, con un esquema documentado en el README y validado por `config.py` antes de tocar ningún fichero. El código solo contiene el motor que lee, valida y ejecuta; los datos (qué acción, qué carpetas, qué filtros)
están fuera.

Añadir una acción de un tipo que ya existe, o cambiar una palabra clave de `ordenar`, es editar el JSON. Solo hay que tocar código cuando se inventa un **tipo** nuevo de acción, y entonces se añade una clase siguiendo el patrón de las demás.

## Alternativas consideradas

1. **Una función de Python por acción.**
   - A favor: se puede hacer cualquier cosa y el editor ayuda con tipos y errores.
   - En contra: cada cambio exige tocar código, reinstalar y volver a probar; un compañero
     que no programa no puede personalizar nada; el fichero de código crece con cada acción.

2. **TOML (con lo que empecé: `tareas.toml`).**
   - A favor: admite comentarios y es muy legible; `tomllib` viene con Python 3.12.
   - En contra: el esquema que pide el curso y casi todas las herramientas web usan JSON;
     `tomllib` solo sirve para leer, así que escribir o generar configuración necesitaría otra
     dependencia; y mantener dos formatos a la vez duplicaría la validación.

3. **YAML.**
   - A favor: admite comentarios y es compacto.
   - En contra: necesita una dependencia externa y la indentación provoca errores difíciles de
     ver; para un fichero pequeño como este es más complicación que ventaja.

Elegí JSON porque es el formato del curso, viene incluido en Python (`json`), lo entienden
editores, herramientas web y APIs, y no añade dependencias. El precio es que no admite
comentarios, y por eso el esquema está explicado en el README y en la skill del proyecto.

## Consecuencias

- **Positivas:**
  - Añadir una acción o cambiar sus reglas no toca el código ni obliga a reinstalar.
  - La configuración se valida entera antes de ejecutar nada: si algo está mal, no se mueve ni
    se borra un solo fichero.
  - Los errores dicen qué acción y qué campo fallan, y salen con código 3, sin traza de Python.
  - El mismo `acciones.json` funciona en Linux, Windows y macOS porque las rutas se tratan con
    `pathlib` y `~` se expande en los tres sistemas.
  - Un compañero puede copiar el JSON y adaptarlo a sus asignaturas sin saber Python.
- **Negativas:**
  - JSON no admite comentarios; hay que documentar el esquema aparte y mantenerlo actualizado.
  - Hay que mantener `config.py` sincronizado cuando el esquema crezca.
  - Un JSON mal escrito falla; se mitiga validando antes y avisando de la línea y la columna.
- **Si el esquema cambia:** subiré `version` a 2 y `config.py` rechazará las versiones que no
  conozca, para no ejecutar configuración antigua con reglas nuevas.
