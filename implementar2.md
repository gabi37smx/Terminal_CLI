Comandos para blindar la web (Tu próximo paso)

Como vas a empezar a securizar el portfolio, tu CLI puede ser tu "centinela" personal.

    gabriel scan-secrets

        Qué hace: Escanea todos los archivos de tu proyecto (mi-web y portfolio-backend) en busca de contraseñas, tokens o claves API expuestas (busca patrones como mongodb+srv, re_, ghp_, AIza).

        Por qué mola: Antes de hacer un git push, lo ejecutas y te quedas tranquilo de que no has subido tu clave de Gemini o de Resend a GitHub por error.

    gabriel audit-web

        Qué hace: Lanza automáticamente Lighthouse en la URL de producción (o en local) y te genera un informe en PDF o HTML dentro de una carpeta docs/auditorias/.

        Por qué mola: Te permite tener un histórico de cómo evoluciona el rendimiento y la accesibilidad.

    gabriel check-headers

        Qué hace: Hace una petición HTTP a tu backend en Render y comprueba si tienes bien configuradas las cabeceras de seguridad (Content-Security-Policy, Strict-Transport-Security, X-Frame-Options).

        Por qué mola: Es un chequeo rapidísimo de seguridad para cuando implementes los blindajes.

    gabriel backup-db

        Qué hace: Se conecta a MongoDB Atlas, exporta las colecciones (mensajes, logs, passkeys) en formato JSON y lo guarda en una carpeta local backups/ con la fecha del día.

        Por qué mola: Si un día te equivocas y borras los logs desde Atlas (como pasó antes), tienes un backup local.

🚀 2. Comandos para el día a día del desarrollo

Para automatizar las tareas repetitivas de Git y el despliegue.

    gabriel deploy "mensaje del commit"

        Qué hace: Hace un git add ., luego un git commit -m "mensaje", y un git push origin main. Además, te puede preguntar: "¿Quieres desplegar también el backend?" y hacer un push al repo del servidor.

        Por qué mola: Te ahorra escribir 3 comandos cada vez que subes algo.

    gabriel new-post "Título de la noticia"

        Qué hace: Genera un archivo Markdown con la plantilla para una nueva noticia o entrada de blog (fecha, título, autor) para tu sección de Noticias IA.

    gabriel test-links

        Qué hace: Analiza tu index.html y comprueba que todos los enlaces (tanto internos como externos) devuelven un estado 200 OK.

        Por qué mola: Evita que en la defensa del proyecto el profesor haga clic en un enlace roto.

    gabriel update-deps

        Qué hace: Entra en la carpeta del backend, ejecuta npm update o npm audit fix y te muestra un resumen de qué paquetes se han actualizado o si hay vulnerabilidades.

🎮 3. Comandos relacionados con tu juego y assets

Tu web tiene muchos recursos (imágenes, fuentes, vídeos).

    gabriel optimize-img

        Qué hace: Convierte todas las imágenes de tu carpeta image/ a formato .webp y les genera versiones redimensionadas (ej. -400.webp, -800.webp).

        Por qué mola: Es lo que ya hiciste a mano para el portfolio, pero automatizado con un solo comando.

    gabriel game-version

        Qué hace: Lee la versión actual en juego-escalada.js (v73.0), la incrementa en 0.1 y actualiza el número en el HTML, el JS y el archivo language.js.

        Por qué mola: Evita que se te olvide actualizar la versión en algún sitio (como pasó con la v70.0 en las traducciones).

    gabriel clean-cache

        Qué hace: Borra la caché de recursos estáticos de tu backend o del navegador, o fuerza la recarga.

🎓 4. Comandos "Locos" pero útiles para la defensa

Si quieres sorprender al profesor, estos comandos demuestran un dominio técnico increíble.

    gabriel show-stats

        Qué hace: Hace una petición a tu backend (/admin) o a la base de datos y te imprime en la terminal cuántos mensajes has recibido, cuántos usuarios han jugado al juego o cuántas visitas has tenido. (Muy fácil de hacer si tu backend ya tiene un endpoint de estadísticas).

    gabriel pomodoro 25

        Qué hace: Inicia un temporizador en la terminal de 25 minutos para estudiar y emite un sonido cuando termina.

        Por qué mola: Demuestra que usas la terminal para tu productividad personal.

    gabriel ask "pregunta"

        Qué hace: Hace una petición a tu propio chatbot (Cordada) directamente desde la terminal, usando la API de Gemini a través de tu backend.

        Por qué mola: Le puedes decir al profesor: "Mi asistente no solo está en la web, también responde en mi terminal".

💡 ¿Cómo implementarlo? (Truco técnico)

Si lo estás haciendo con Node.js, te recomiendo usar la librería commander o yargs. Son estándares de la industria para crear CLIs.

Si lo estás haciendo con Python, usa la librería argparse (ya viene instalada) o click (más moderna).

Consejo para tu portfolio: Crea una sección en tu web (o un README en GitHub) explicando que tienes tu propia CLI llamada gabriel. Si añades capturas de la terminal funcionando, es un punto brutal. Puedes decir: "Para agilizar el desarrollo de este portfolio, me he creado una CLI personalizada en Node.js que automatiza las tareas repetitivas, gestiona las versiones del juego y audita la seguridad de la web".