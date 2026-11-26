# Spec de `mochila` (antes `tareas`)

La spec de 10 líneas que escribí en la Sesión 1 (paso 6), **tal cual**. La misma está al principio del
[README](../README.md#spec-versión-0--26102026). Debajo, en qué ha quedado cada punto.

## Versión 0 · 26/10/2026

1. **Problema:** cada semana pierdo tiempo ordenando Descargas a mano, limpiando ficheros temporales y convirtiendo fotos a WebP para que pesen menos.
2. **Para quién:** para mí y para mis compañeros de 1º DAM.
3. **Cómo se usa:** `tareas ORDEN [CARPETA] [opciones]` desde cualquier terminal.
4. **Órdenes de la semana 1:** `tareas --help`, `tareas version`, `tareas listar [CARPETA]`.
5. **Órdenes previstas:** `tareas acciones`, `tareas validar`, `tareas ejecutar NOMBRE --simular`.
6. **Mis 3 acciones (borrador):** organizar Descargas por tipo de fichero, borrar temporales de más de 30 días, convertir imágenes a WebP.
7. **Nunca hará:** borrar sin preguntar ni tocar ficheros fuera de la carpeta que le indique.
8. **Plataformas:** Linux primero; también Windows y macOS.
9. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida.
10. **Instalación:** `uv tool install --editable .` (lo completo en la semana 4).

## En qué ha quedado (26-nov, versión 1.3.1)

1. Cumplido: `ordenar` reparte por asignatura y unidad, `limpiar-temporales` borra los viejos y `convertir-webp` pasa a WebP sin tocar el original.
2. Más de lo previsto: sirve para SMX, DAM, DAW y ASIR (`mochila configurar`, [ADR-0003](adr/0003-configurar-por-ciclo.md)), y lo han instalado otras personas en sus equipos (`docs/prompts.md`).
3. Igual, con otro nombre: `mochila ORDEN [CARPETA] [opciones]` ([ADR-0006](adr/0006-nombre-mochila.md)); `tareas` sigue funcionando.
4. y 5. Todas existen (`version`, `listar`, `acciones`, `validar`, `ejecutar NOMBRE --simular`), y muchas más: [docs/comandos.md](comandos.md).
6. Son 10 acciones propias: 6 sin IA, 3 con IA y una secuencia que combina cuatro ([ADR-0007](adr/0007-acciones-combinables.md)).
7. Cumplido: lo que borra o mueve pregunta antes (salvo `--si`), `--simular` no toca nada y nunca se sobrescribe un fichero.
8. Cumplido: pruebas en verde en Ubuntu, Windows y macOS en cada push (GitHub Actions).
9. Cumplido, y uno más: 4 = sin IA (sin clave, sin red o el servidor no responde), y las acciones sin IA siguen funcionando.
10. Una sola orden: `uv tool install git+https://github.com/gabi37smx/Terminal_CLI@v1.3.1`, o el instalador (`bash instalar.sh` / `instalar.cmd`).
