El Prompt para tu Agente de IA (Versión 2.0 con Diff)

Copia y pega esto en tu agente:

    "Actúa como un Arquitecto de Software Senior experto en automatización con Node.js, Git y DevOps.

    Contexto: Estoy desarrollando mi CLI personal gabriel en Node.js. Uso un PC de clase, un PC de casa y un USB. Tengo un repositorio centralizado en GitHub con una carpeta por asignatura de 1º DAM (asignaturas/programacion/, asignaturas/bd/, etc.).

    Objetivo: Implementar un sistema de sincronización inteligente (gabriel sync) y un escáner de estado (gabriel status) que compare los archivos locales con los del repositorio remoto (usando git diff) para evitar pérdidas de información y conflictos de fusión.

    Requisitos Técnicos y de Arquitectura:

        Comando gabriel status (El "Guardián"):

            Debe usar simple-git para obtener el estado del repositorio.

            Debe mostrar por consola (con colores de chalk) una lista de:

                Archivos Modificados (locales, no subidos).

                Archivos Nuevos (locales, no rastreados).

                Archivos Por descargar (cambios en el remoto que no tienes).

            Si detecta que hay cambios locales Y cambios remotos, debe advertir: "⚠️ Peligro: Tienes archivos sin subir y hay archivos nuevos en GitHub. Haz un commit o guarda una copia antes de sincronizar".

        Comando gabriel sync [asignatura] [mensaje]:

            Paso 1 (Comprobación de seguridad): Ejecuta un git fetch y luego compara el HEAD local con el origin/main usando git diff --name-status origin/main y git diff HEAD.

            Paso 2 (Lógica de Decisión):

                Si no hay cambios locales ni remotos: "Todo está actualizado".

                Si solo hay cambios remotos: Hace git pull automático y avisa: "Archivos descargados desde clase/casa".

                Si solo hay cambios locales: Hace git add, git commit -m "[asignatura]: [mensaje]" y git push.

                Si hay AMBOS (Conflicto potencial): Se detiene, muestra un git diff --stat de los archivos afectados y pide al usuario que decida manualmente (no hace el sync automático para no romper nada).

        Filtro por Asignatura: Si se pasa el argumento [asignatura], el script debe limitar el git add y el análisis de status solo a la carpeta de esa asignatura (ej. asignaturas/programacion/), ignorando el resto de materias.

        Manejo de Errores: Capturar si no hay conexión a internet, si hay un merge conflict real, o si la rama está desactualizada (ej. git pull --rebase).

    Entrega: Dame el código completo en Node.js usando simple-git y chalk. Explica cómo configurar el script para que lea la ruta del repositorio desde un archivo config.json. Incluye un ejemplo de cómo se vería la salida por consola del comando status cuando hay archivos modificados en local pero no subidos."