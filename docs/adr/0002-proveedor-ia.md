# ADR-0002: La IA va detrás de una interfaz (ProveedorIA)

- Estado: aceptada
- Fecha: 2026-11-11
- Autor: Gabriel Vidal Badia

## Contexto

Mis acciones `resumir-tema`, `nombrar-descargas` y `clasificar-asignatura` necesitan un modelo de
lenguaje: una regla mira el nombre, la extensión y la fecha, pero no sabe de qué trata
`escaneo_0042.pdf`. Hoy uso el servidor del centro (API de chat de OpenAI, en `CENTRO_IA_URL`).

Mi situación concreta:

- Uso `dam` en tres sitios: el PC de clase (Linux), el de casa (Windows) y un USB. **El servidor del
  centro solo responde desde la red del instituto**: en casa no llego, así que allí tengo que poder
  trabajar con `--simular` y con las acciones sin IA.
- Las pruebas pasan en GitHub Actions, que tampoco llega al servidor del centro. Si las acciones
  hablaran directamente con él, no podría probarlas sin red ni sin gastar tokens.
- El año que viene, o en casa, puede ser otro servidor (Ollama en local, otro proveedor...). Casi
  todos hablan la misma API de chat de OpenAI.
- La clave es personal: si se filtra, hay que avisar al profesor y anularla. No puede acabar en el
  código, en el repo ni en el historial.

## Decisión

Toda llamada a un modelo pasa por la clase abstracta `ProveedorIA`, con un único método
`completar(sistema, usuario, max_tokens)` que devuelve una `Respuesta` (texto, tokens de entrada y
de salida, segundos). `ProveedorCentro` la implementa con `httpx` contra `{url}/chat/completions` y
se crea con la fábrica `ProveedorCentro.desde_entorno()`, que lee las variables de entorno (o un
`.env` que está en `.gitignore`).

Las acciones (`AccionIA` y sus subclases) solo conocen `completar()`: no importan `httpx` ni saben
qué servidor hay detrás. El proveedor lo pone el motor, y la CLI solo lo crea si la acción usa IA y
no hay `--simular`. Cualquier fallo (sin clave, sin red, sin certificado, 401, 429, tiempo agotado)
es una `IANoDisponible`, que sale con código 4 y deja funcionar las acciones sin IA.

## Alternativas consideradas

1. **Llamar a httpx directamente desde cada acción.**
   - A favor: menos clases; para una sola acción es lo más rápido de escribir.
   - En contra: el código de la petición, el certificado y los mensajes de error se repetiría en las
     tres acciones; cambiar de servidor obligaría a tocarlas todas; y para probarlas sin red tendría
     que interceptar `httpx` en cada prueba en vez de pasarles un proveedor falso.

2. **Usar la librería oficial de OpenAI (`uv add openai`).**
   - A favor: ya trae los tipos de la respuesta, los reintentos y el streaming.
   - En contra: es una dependencia mucho más grande para hacer una sola petición POST; uso cuatro
     campos de la respuesta. Además, quería entender qué viaja por la red (el JSON, la cabecera
     `Authorization`, los tokens) y con `httpx` lo veo y lo controlo línea a línea, incluido el
     certificado del instituto con `ssl.create_default_context`.

3. **Un agente con herramientas (como OpenCode) en vez de una sola llamada.**
   - A favor: podría decidir solo qué hacer con cada fichero.
   - En contra: un modelo con herramientas puede leer, borrar o ejecutar, y un PDF con «Ignora tus
     instrucciones...» (inyección de prompt) se vuelve peligroso. En `dam` el modelo solo devuelve
     texto y lo que pasa en el disco lo decide mi código, que limpia y valida esa respuesta.

## Consecuencias

- **Positivas:**
  - Cambiar de servidor es escribir otra subclase de `ProveedorIA`, sin tocar las acciones.
  - Las pruebas usan `ProveedorFalso` (`tests/conftest.py`): sin red, sin clave y sin gastar tokens,
    también en GitHub Actions.
  - En casa, sin el servidor, `dam` sigue funcionando: `--simular` dice cuánto mandaría y las seis
    acciones sin IA no necesitan nada.
  - Los mensajes de error están en un solo sitio (`ia.py`) y en español.
- **Negativas:**
  - Una capa más que entender (clase abstracta, fábrica y subclase) para lo que hoy es un solo servidor.
  - Las respuestas del modelo pueden cambiar de una vez a otra, incluso con temperatura 0,2:
    `--simular` no puede enseñar el nombre o la categoría que saldrá. Por eso
    mis acciones con IA que cambian ficheros llevan `"confirmar": true`.
  - Solo hablo la API de OpenAI; un proveedor con otra API necesitaría su propia subclase.
- **La clave:** vive en variables de entorno (o en un `.env` local) y nunca en un fichero que suba
  a git. `.env` y `.env.*` están en `.gitignore` desde el primer commit, `.env.example` documenta qué
  hace falta sin ningún valor real y `git log --all -- .env` no saca nada. OpenCode tampoco la ve:
  `opencode.json` le prohíbe leer `*.env`. `comprobar-ia` solo dice «clave: definida».
