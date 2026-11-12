# ADR-0004: Modelos gratis de OpenCode para la IA de dam (dam configurar-ia)

- Estado: aceptada
- Fecha: 2026-11-12
- Autor: Gabriel Vidal Badia

## Contexto

Mis acciones con IA (`resumir-tema`, `nombrar-descargas` y `clasificar-asignatura`) solo funcionaban
con el servidor del centro, y ese servidor solo responde desde la red del instituto (ADR-0002). En
casa no tenía IA, y un compañero que instale `dam` sin clave del centro tampoco.

Mi situación concreta:

- OpenCode trae modelos gratis (los que acaban en `-free`: DeepSeek, GLM, MiniMax...) que no piden
  cuenta ni clave. Pero **solo funcionan desde dentro de OpenCode**: no tienen una API a la que llamar
  con `httpx` como hago con el servidor del centro.
- En el ADR-0002 descarté usar un agente con herramientas: un PDF con «Ignora tus instrucciones...»
  podría hacer que el modelo leyera, borrara o ejecutara algo.
- Los modelos gratis cambian: OpenCode quita unos y pone otros. Y no todos tratan igual lo que les
  mandas: unos no lo guardan, otros lo usan para mejorar el modelo.
- En clase usamos OpenCode 1.18.35. La web de OpenCode ya documenta la versión 2, que cambia el
  formato de la configuración de los agentes.
- Quería que fuera automático, como `dam configurar`: que el instalador lo pregunte y lo deje listo,
  también el `opencode.json`.

## Decisión

Una subclase nueva de `ProveedorIA`, `ProveedorOpenCode`, que lanza `opencode run` con un agente
propio (`dam-ia`) en una carpeta temporal vacía:

- El agente **no tiene herramientas**: `tools: "*": false` y `permission: "*": deny`. La única que no
  se puede quitar es `read` (sin ninguna herramienta, la 1.18.35 se queda colgada), así que solo puede
  leer dentro de su carpeta vacía: `external_directory: deny`. Lo probé pidiéndole, dentro del texto,
  que leyera un fichero de fuera: la regla se lo impidió.
- Las instrucciones de la acción van en el agente y el texto del fichero, por la entrada estándar
  (sin límite de largo y sin pasar por la línea de órdenes, donde `&` o `|` darían problemas en Windows).
- `--title dam`, para que OpenCode no le pida el título de la sesión a mi `small_model`, que es el
  del centro y en casa falla.
- `--dir` con la carpeta temporal: sin él, OpenCode trabajaba en la carpeta desde la que lancé `dam`.

Un comando, `dam configurar-ia`, que lo lanza el instalador: pregunta si quiero los modelos gratis o
el servidor del centro, enseña los modelos gratis de ese día con lo que hace cada uno con mis datos
(los recomendados primero), hace una pregunta mínima y lo guarda en `~/.config/dam/ia.json`. Si
quiero, pone ese modelo por defecto en mi `~/.config/opencode/opencode.json`, con copia del anterior.
`DAM_IA=centro` cambia de proveedor solo en esa terminal.

El instalador instala OpenCode 1.18.35 con `npm` si no lo tengo: la misma versión de clase.

## Alternativas consideradas

1. **OpenRouter con un modelo `:free`** (por ejemplo, DeepSeek).
   - A favor: habla la misma API de OpenAI que el servidor del centro; bastaba con cambiar el `.env`.
   - En contra: hay que crear una cuenta y una clave, y solo deja 50 peticiones al día. No es «instalar
     y listo».

2. **Llamar directamente a la API de OpenCode Zen.**
   - A favor: sería otra subclase con `httpx`, sin lanzar `opencode`.
   - En contra: según su documentación, los modelos gratis solo se pueden usar desde OpenCode.

3. **Ollama con un modelo en local.**
   - A favor: no sale nada de mi ordenador y funciona sin internet.
   - En contra: hay que bajar varios GB por modelo y, sin una buena tarjeta gráfica, va lento.

4. **Usar el agente por defecto de OpenCode (`build`).**
   - A favor: no hay que crear ningún agente.
   - En contra: tiene todas las herramientas (editar, `bash`...). Es justo lo que descarté en el ADR-0002.

## Consecuencias

- **Positivas:**
  - Las acciones con IA funcionan en casa, sin clave y gratis. Probado en Windows: `dam comprobar-ia`
    responde en unos 5 s, y una clasificación de prueba acertó «redes».
  - No cambia ninguna acción: es otra subclase de `ProveedorIA`, como decía el ADR-0002.
  - Las pruebas no lanzan `opencode` de verdad: un `opencode` de mentira responde como lo haría
    `opencode run --format json`.
- **Negativas:**
  - Lo que mando sale a un servidor de fuera. Por eso enseño qué hace cada modelo con los datos y
    recomiendo los que no los guardan.
  - Los modelos gratis cambian: el que elijo hoy puede desaparecer. Entonces `dam` dice el error de
    OpenCode y hay que repetir `dam configurar-ia`.
  - Va atado a OpenCode 1.18.35: con la 2 puede que el agente haya que escribirlo de otra forma.
  - Es más lento que el servidor del centro (5-15 s por fichero) y no se puede limitar `max_tokens`.
  - En WSL se ven el `npm` y el `opencode` de Windows, que no sirven desde Linux: el instalador y `dam`
    no los usan y piden el de Linux.
