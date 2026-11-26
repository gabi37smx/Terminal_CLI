# ADR-0007: Acciones combinables con el tipo «secuencia»

- Estado: aceptada
- Fecha: 2026-11-26
- Autor: Gabriel Vidal Badia

## Contexto

Cuando repaso la carpeta de pruebas (o mis Descargas) siempre lanzo las mismas órdenes, en el mismo
orden: borrar temporales viejos, renombrar las capturas, pasarlas a WebP y guardar los `.zip` en
`comprimidos`. Son cuatro `mochila ejecutar` seguidos, y si me salto uno o los hago en otro orden el
resultado cambia: si convierto antes de renombrar, el `.webp` se queda con el nombre feo de la captura.

El nivel excelente de la rúbrica pide acciones «combinables». Hasta la 1.2.2, `mochila ejecutar` solo
aceptaba una acción cada vez.

## Decisión

Un tipo nuevo de acción, `secuencia`, que solo lleva la lista de acciones que ejecuta, en orden:

```json
{ "nombre": "repasar-carpeta", "descripcion": "Todo seguido: ...", "tipo": "secuencia",
  "origen": "~/pruebas-tareas/prueba-final",
  "pasos": ["limpiar-temporales", "renombrar-capturas", "convertir-webp", "mover-zips"] }
```

- **Se combina en el JSON, no en el código** (sigue el ADR-0001): una combinación nueva es editar
  `acciones.json`. La secuencia no tiene filtro ni destino propios: cada paso usa los de su acción.
- **Cada paso ve lo que dejó el anterior.** El motor vuelve a elegir los ficheros antes de cada paso
  (`Motor.pasos` y `Motor.preparar`), así que `convertir-webp` convierte la captura ya renombrada.
- **Sin efectos sorpresa.** Cada paso enseña su tabla y pregunta exactamente igual que si lo lanzaras
  solo (`--si` se salta todas las preguntas). Si un paso falla, o le dices que no, los que faltan no se
  ejecutan y se dice cuáles. Si algún paso necesita IA y no hay modelo, sale con 4 **antes** del
  primer paso: mejor no empezar que quedarse a medias.
- **La simulación lo avisa.** Con `--simular` no se toca nada, así que cada paso se calcula con la
  carpeta tal como está ahora; la salida lo dice en la primera línea.
- **Sin bucles.** `config.py` comprueba que cada paso existe, que no es otra secuencia ni la propia
  secuencia, que no se repite y que hay al menos dos (código 3 si no).
- La CARPETA de la orden vale para todos los pasos; sin ella, el `origen` de la secuencia; y sin
  ninguno de los dos, cada paso usa su propio `origen` (si a alguno le falta, se dice antes de empezar).
  Una secuencia no trabaja sobre un fichero suelto: el paso 1 podría renombrarlo y el 2 ya no lo vería.

## Alternativas consideradas

1. **Varias acciones en la orden: `mochila ejecutar limpiar-temporales convertir-webp CARPETA`.**
   - A favor: no hay que tocar el JSON para combinar.
   - En contra: no se sabe si el último argumento es una acción o una carpeta (una carpeta puede
     llamarse como una acción), y la combinación que uso cada semana no queda guardada en ningún sitio.
2. **Un campo `despues` en cada acción («al acabar, lanza esta otra»).**
   - A favor: no hace falta un tipo nuevo.
   - En contra: la cadena queda repartida por el fichero, es fácil hacer un bucle (A → B → A) y una
     acción ya no se puede lanzar sola sin arrastrar a las demás.
3. **Un script de PowerShell o bash con las cuatro órdenes.**
   - A favor: cero código nuevo.
   - En contra: uno por sistema operativo, no pasa por la validación de `acciones.json` y no para si un
     paso falla.

## Consecuencias

- Positivas: la combinación queda escrita en el JSON con nombre y descripción, sale en
  `mochila acciones` con sus pasos, se valida como el resto y se prueba en `tests/test_secuencia.py`
  (28 pruebas: validación, que cada paso ve el anterior, `--simular`, preguntas, fallo a mitad, fichero
  suelto, pasos sin origen y sin IA).
- Negativas: la simulación de una secuencia no puede enseñar el resultado exacto de los pasos que
  dependen de los anteriores (lo avisa); y una secuencia no puede contener otra (si algún día hace
  falta, habría que comprobar los bucles).
- Ninguna acción ni tipo anterior cambia: un `acciones.json` sin secuencias funciona igual.
