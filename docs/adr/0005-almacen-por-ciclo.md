# ADR-0005: El almacén se llama como tu ciclo y dam te ayuda a crearlo (dam crear-almacen)

- Estado: aceptada
- Fecha: 2026-11-13
- Autor: Gabriel Vidal Badia

## Contexto

Con `dam configurar` (ADR-0003), alguien de ASIR ya tiene sus asignaturas. Pero el almacén seguía
siendo cosa mía:

- Los instaladores clonaban siempre `https://github.com/USUARIO/DAM-almacen.git`. A alguien de ASIR
  le estábamos pidiendo un repo que se llamara «DAM».
- Nadie le decía que ese repo lo tenía que **crear él** en GitHub antes. Si no lo tenía, el
  instalador fallaba al clonar o lo saltaba, y `dam configurar` decía «cuando tengas el almacén
  clonado...».
- Un repo recién creado está vacío: aunque lo clonara, `dam sync` no sabía adónde subir (la rama
  no tenía remoto).
- El instalador clonaba el almacén **antes** de preguntar el ciclo, así que no podía saber cómo se
  llamaba.

Lo que quiero es que le sirva a un alumno de 1º de SMX que no sabe git.

## Decisión

1. **El almacén se llama como tu ciclo:** `SMX-almacen`, `DAM-almacen`, `DAW-almacen`,
   `ASIR-almacen` (`APUNTES-almacen` con «otro»). Al elegir ciclo, `dam configurar` cambia
   `almacen.ruta` a `~/CICLO-almacen`, pero solo si era una de las que pone dam. Si la escribiste tú,
   no se toca. Con DAM no cambia nada (regla 1 del ADR-0003).
2. **Comando nuevo, `dam crear-almacen`:**
   - Pide tu usuario de GitHub. Vale también si pegas `github.com/usuario`.
   - Pregunta si ya tienes el repo. Si no, abre `github.com/new` con el nombre y **Private** ya
     puestos, y tú solo pulsas «Create repository».
   - Lo clona, crea las carpetas de tus asignaturas y, si el repo es nuevo, hace el primer commit y
     `git push -u origin main`. A partir de ahí, `dam sync` ya sabe adónde subir.
   - `dam configurar` lo ofrece al acabar si no tienes almacén.
3. **Los instaladores** solo buscan un almacén que ya exista. Ahora vale cualquier remoto
   `CICLO-almacen`, no solo `DAM-almacen`. El almacén se prepara después de elegir el ciclo.

## Alternativas consideradas

1. **Crear el repo con la API de GitHub y un token.**
   - A favor: no hay ni que pulsar un botón.
   - En contra: crear un token es lo más difícil para quien empieza (permisos, caducidad, copiarlo
     entero). Además, `dam` tendría en la mano un token con permiso para crear repos. Con la página
     ya rellena, `dam` nunca ve ni tu contraseña ni tu token: de eso se encarga git.
2. **Las dos cosas: con token si lo tienes y, si no, la página.**
   - A favor: lo más cómodo para quien ya tiene token.
   - En contra: más código y más pruebas antes de la entrega, y los que menos saben no usarían la
     parte del token. No ayuda a quien más lo necesita.
3. **`gh repo create` (la CLI oficial de GitHub).**
   - A favor: crea el repo y lo clona de una vez.
   - En contra: hay que instalar `gh` y hacer `gh auth login`. En el Windows LTSC de mi cuñado no hay
     winget, y en los PC de clase no somos administradores.
4. **Seguir con `DAM-almacen` para todos.**
   - A favor: no hay que cambiar nada.
   - En contra: está mal que un alumno de ASIR tenga un repo que se llama DAM. Para eso hice
     `dam configurar`.

## Consecuencias

- **Positivas:**
  - Alguien de cualquier ciclo pasa de no tener nada a tener su almacén privado, con sus carpetas y
    subido, sin escribir ni un comando de git.
  - `dam` no maneja ningún secreto.
  - En otro equipo es lo mismo, pero contestando que ya lo tienes: solo lo baja.
  - 30 pruebas nuevas, con un «GitHub de mentira» (repos bare en una carpeta temporal) y sin abrir
    el navegador.
- **Negativas:**
  - En Linux y macOS, git sigue pidiendo el token para un repo privado (en Windows abre el
    navegador). No lo empeora, pero tampoco lo arregla: lo explican el comando y el README.
  - En un Linux sin escritorio no se abre el navegador (abriría uno de texto dentro de la
    terminal): se enseña la dirección para abrirla a mano.
  - Si GitHub cambia cómo rellena la página `github.com/new` (`name` y `visibility`), saldría sin
    rellenar. Por eso el texto dice qué comprobar antes de pulsar el botón.
  - El nombre `CICLO-almacen` lo busca el instalador. Si alguien le pone otro nombre, tiene que
    decirlo con `DAM_ALMACEN`.
