# ADR-0003: Las asignaturas salen de mi ciclo y curso (dam configurar)

- Estado: aceptada
- Fecha: 2026-11-12
- Autor: Gabriel Vidal Badia

## Contexto

Hasta el 11-nov, `ordenar` y `clasificar` solo servían para 1º de DAM: mis 8 asignaturas, con sus
palabras clave, estaban escritas a mano en `acciones.json`. Cualquier otra persona tenía que
reescribir ese JSON entero para que `dam` le sirviera.

Pensé en mi cuñado, que está haciendo ASIR: sus asignaturas no son las mías. Y si sirve para DAM y
ASIR, ¿por qué no para DAW y para el grado medio (SMX)? El profesor nos dice que pensemos a lo
grande.

Mi situación concreta:

- En la familia de Informática hay cuatro ciclos (SMX, DAM, DAW y ASIR, que en valenciano es ASIX),
  cada uno con 1º y 2º. Los apuntes llegan en castellano y en valenciano.
- Lo que hace `ordenar` lo deciden las palabras clave: si no son las de tus asignaturas, todo acaba
  en POR-TIPO.
- Mi `acciones.json` ya funciona y está probado de verdad: no quería perder lo que tengo afinado.
- El ADR-0001 dice que la configuración va fuera del código. Lo que cambia de una persona a otra
  (sus asignaturas) tiene que acabar en su `acciones.json`, no en Python.

## Decisión

Un comando, `dam configurar`, pregunta como `adduser` en Linux: ciclo, curso y, sobre la lista que
propone, qué asignaturas quitar o añadir. Con eso reescribe solo `ordenar` (carpetas, palabras clave
y extensiones) y `clasificar` (categorías e instrucciones), valida el fichero entero antes de
guardarlo y deja una copia del anterior. Lo elegido queda en `perfil`, para proponerlo la próxima
vez. Los instaladores lo lanzan después de clonar el almacén.

El vocabulario de los cuatro ciclos (asignaturas, nombres en los dos idiomas, palabras clave y
extensiones) vive en `src/tareas/ciclos.py`. El resultado, lo de cada persona, vive en su
`acciones.json`.

Tres reglas:

1. **Si eliges las mismas asignaturas que ya había, esas acciones no se tocan.** Mi 1º de DAM en
   `ciclos.py` es idéntico a mi `acciones.json`, y una prueba lo vigila.
2. **Al repetirlo, las palabras nuevas del vocabulario se suman a las tuyas, sin quitar ninguna.**
3. **Una palabra clave no entra si es una palabra corriente en castellano o en valenciano**, aunque
   sea la sigla de un módulo: `ordenar` también lee el texto de los PDF.

## Alternativas consideradas

1. **Un `acciones.json` de ejemplo por ciclo** (`acciones-smx.json`, `acciones-asir.json`...).
   - A favor: no hace falta código nuevo; se copia el que toca.
   - En contra: serían 8 ficheros (4 ciclos × 2 cursos) con las otras 7 acciones repetidas. Si
     cambio una acción, hay que cambiarla en todos. Quitar o añadir una asignatura volvería a ser
     editar JSON a mano.

2. **El vocabulario en un JSON** (`ciclos.json`) en vez de en Python.
   - A favor: se podría cambiar sin tocar código.
   - En contra: es parte del programa, no de la configuración de cada persona. Lo que cada uno
     cambia ya acaba en su `acciones.json`. En Python lo comprueban las pruebas (que cada asignatura
     exista, que las palabras estén escritas como las compara `ordenar`) y no hay que empaquetar un
     fichero de datos aparte.

3. **Que la IA decida las asignaturas** (`clasificar` para todo, sin palabras clave).
   - A favor: no hay que mantener un vocabulario.
   - En contra: el servidor del centro solo responde desde la red del instituto (ADR-0002), y en casa
     me quedaría sin ordenar. Las palabras clave funcionan sin red, son rápidas y siempre dan lo
     mismo. La IA queda para lo que las palabras no saben colocar.

## Consecuencias

- **Positivas:**
  - Un alumno de cualquiera de los cuatro ciclos tiene `ordenar` y `clasificar` a su medida
    respondiendo unas preguntas, sin abrir el JSON.
  - Lo probé haciendo de alumno de 1º de SMX en WSL, con 15 apuntes reales: **11 de 15** a su
    asignatura.
  - A mí no me cambia nada: con 1º de DAM, mis acciones se quedan igual.
  - Para añadir un ciclo solo hay que tocar `ciclos.py`.
- **Negativas:**
  - El vocabulario hay que mantenerlo. Probándolo salieron dos fallos: palabras que faltaban
    (`discos`, `caixes`, `.pka`...) y que, al repetir `dam configurar`, las palabras nuevas no
    llegaban. Los dos están arreglados (PR #26 y #27).
  - En qué curso cae cada módulo común (Digitalización, Sostenibilidad, Proyecto intermodular)
    depende del centro. Lo puse según lo que tengo yo, y por eso se puede quitar y añadir.
  - Hay siglas que no puedo usar como palabra clave. `som` (Sistemes Operatius Monolloc) en
    valenciano es «somos»: mandaría a esa asignatura casi cualquier PDF en valenciano. Lo que las
    palabras no colocan va a POR-TIPO o a `clasificar`.
