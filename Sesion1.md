Esta semana pierdes el miedo a la pantalla negra y empiezas a programar como se programa ya: con un agente. Aprendes a moverte por la terminal, instalas las herramientas, creas tu proyecto en Python y construyes tu primera orden con OpenCode: tú decides y apruebas, el agente escribe. Todo paso a paso: si nunca has abierto una terminal, empiezas en el paso 0 y llegas igual que el resto.

El producto al acabar la semana

    •Tu comando tareas instalado: lo escribes en cualquier carpeta y responde.
    •tareas --help, tareas version y tareas listar funcionando (tabla con nombre, tipo, tamaño y fecha), construidos con OpenCode aprobando tú cada cambio.
    •Un repo público en GitHub con .gitignore correcto desde el primer commit, opencode.json (los permisos de tu agente) y AGENTS.md (sus normas).
    •Al menos 4 commits hechos por ti con mensajes que cuentan qué has hecho.

⏱ 4 horas🐧 Linux primero · 🪟 Windows · 🍎 macOS🧭 100 % guiada📦 Python 3.12 · uv · Typer🤖 OpenCode 1.18.35
🏫 Grupo presencial

Trabajas en los equipos Linux del aula: sigue los bloques de bash. El código lo construyes con OpenCode conectado a los modelos del centro; el chat del centro queda para consultas. Son 4 h de línea individual que van en paralelo a las 4 h de la startup en grupo: no mezcles los repos.
🏠 Grupo semipresencial

La terminal y la puesta en marcha se hacen en la tutoría colectiva de arranque, de presencia obligatoria (fecha en el aula virtual): trae tu portátil. Allí el profesor explica cómo conectarte desde casa a los modelos del centro. En casa usas OpenCode en la terminal integrada de VS Code; el chat de Copilot de Microsoft 365 queda solo para consultas. Si tu equipo es Windows, sigue los bloques de PowerShell. El 6 nov hay comprobación de proceso.
🤖 Guía completa: OpenCode, tu agente de programaciónLa usarás todo el curso: instalación, conexión, agentes, permisos, AGENTS.md, skills y MCP. Esta sesión te da lo justo para empezar; la guía, el resto. Y fíjate: la herramienta con la que programas tu CLI es… una CLI.→
0 · Abre la terminal
1 · Supervivencia
2 · Herramientas
3 · Proyecto y primer commit
4 · Prepara a tu agente
5 · Tu primera orden
6 · Instálala
7 · Audita y commitea
Checklist final
Si te atascas
Paso 0 · Abre la terminal 10 min

La terminal es una ventana donde escribes órdenes en lugar de hacer clic. Es más rápida, se puede automatizar y es donde vive casi todo lo que hace un programador: Git, Python, servidores. Ábrela así:
Sistema	Cómo abrirla	Qué intérprete usas
🐧 Linux (aula)	Ctrl+Alt+T, o busca «Terminal» en el menú	bash (o zsh)
🪟 Windows	Tecla Windows → escribe «Terminal» → Windows Terminal. Si no la tienes, «PowerShell». Evita «Símbolo del sistema» (cmd).	PowerShell
🍎 macOS	Cmd+Espacio → «Terminal»	zsh (casi igual que bash)
💻 VS Code	Menú Ver → Terminal, o Ctrl+ñ (teclado español). Se abre en la carpeta del proyecto.	la de tu sistema
Lee el prompt antes de escribir

El prompt es el texto que la terminal escribe sola antes del cursor. Te dice quién eres, en qué máquina y, lo más importante, en qué carpeta estás:
prompt
ana@aula-23:~/pruebas-tareas$         Linux: usuario@equipo:carpeta$
ana@MacBook-de-Ana pruebas-tareas %    macOS: usuario@equipo carpeta %
PS C:\Users\ana\pruebas-tareas>        Windows (PowerShell): PS carpeta>
Regla de oro: en esta página, las órdenes van sin el prompt. No copies el $ ni el PS C:\...>. Lo que hay detrás de un # es un comentario para ti: la terminal lo ignora. Escribe una orden, pulsa Intro y lee lo que responde. Si no responde nada, normalmente es que todo ha ido bien.
Paso 1 · Supervivencia en la terminal 15 min de práctica + reto

Con quince órdenes te mueves por cualquier ordenador. Antes, dos ideas: todo fichero vive en un árbol de carpetas, y para llegar a él escribes una ruta.
📁 / (la raíz)📁 home📁 ana ← ~ (tu carpeta personal)📁 Descargas📁 pruebas-tareas ← estás aquí📁 fotosIMG_0001.jpgRuta ABSOLUTA (empieza en /):/home/ana/pruebas-tareas/fotos/IMG_0001.jpgLa misma con ~:~/pruebas-tareas/fotos/IMG_0001.jpgRuta RELATIVA (desde donde estás):fotos/IMG_0001.jpg. = aquí · .. = sube a ana../Descargas = la carpeta hermana
Una ruta absoluta funciona estés donde estés; una relativa depende de tu carpeta actual (la que te dice pwd). En Windows la raíz es C:\ y la carpeta personal es C:\Users\ana, pero ~, . y .. funcionan igual en PowerShell.
Las órdenes básicas (bash: Linux y macOS)

Escríbelas una a una, no las pegues todas a la vez: el objetivo es que tus dedos las aprendan.
bash
pwd                     # ¿dónde estoy?
ls                      # ¿qué hay aquí?
ls -la                  # todo, también lo oculto (.git, .env...), con detalles
cd Descargas            # entra en una carpeta (ruta relativa)
cd ..                   # sube un nivel
cd ~                    # vuelve a tu carpeta personal (o solo: cd)
cd /tmp                 # ve a una ruta absoluta
mkdir -p ~/zona/a/b     # crea carpetas, también las intermedias
touch ~/zona/nota.txt   # crea un fichero vacío
cp ~/zona/nota.txt ~/zona/copia.txt
mv ~/zona/copia.txt ~/zona/a/renombrada.txt
cat ~/zona/nota.txt     # muestra el contenido de un fichero
rm ~/zona/a/renombrada.txt
rm -r ~/zona            # borra una carpeta entera. SIN papelera.
ls --help               # ayuda corta de casi cualquier orden
man ls                  # manual completo (sal con q)
Las mismas en PowerShell (Windows)

PowerShell entiende muchos nombres de bash (ls, cd, pwd, cat, cp, mv, rm) como alias, pero las opciones cambian. Los nombres «de verdad» son estos:
PowerShell
Get-Location                       # pwd también funciona
Get-ChildItem                      # ls y dir también funcionan
Get-ChildItem -Force               # incluye ocultos
Set-Location Descargas             # cd también funciona
Set-Location ..
Set-Location ~
New-Item -ItemType Directory -Force "$HOME\zona\a\b"
New-Item -ItemType File "$HOME\zona\nota.txt"
Copy-Item "$HOME\zona\nota.txt" "$HOME\zona\copia.txt"
Move-Item "$HOME\zona\copia.txt" "$HOME\zona\a\renombrada.txt"
Get-Content "$HOME\zona\nota.txt"  # cat también funciona
Remove-Item "$HOME\zona\a\renombrada.txt"
Remove-Item -Recurse "$HOME\zona"  # SIN papelera
Get-Help Get-ChildItem             # ayuda de una orden
Para qué	bash (Linux/macOS)	PowerShell (Windows)
¿Dónde estoy?	pwd	Get-Location
Listar (con ocultos)	ls -la	Get-ChildItem -Force
Entrar / subir	cd carpeta · cd ..	cd carpeta · cd ..
Crear carpetas	mkdir -p a/b/c	New-Item -ItemType Directory -Force a\b\c
Crear fichero vacío	touch f.txt	New-Item -ItemType File f.txt
Copiar	cp a b	Copy-Item a b
Mover / renombrar	mv a b	Move-Item a b
Borrar (sin papelera)	rm f · rm -r carpeta	Remove-Item f · -Recurse
Ver un fichero	cat f.txt	Get-Content f.txt
Ayuda	orden --help · man orden	Get-Help orden
Ver el PATH	echo $PATH	$env:Path
¿De dónde sale una orden?	which git	Get-Command git
⚠ La terminal no tiene papelera. rm y Remove-Item borran para siempre, sin preguntar. Antes de un rm -r, haz pwd y ls para comprobar dónde estás y qué vas a borrar. Nunca escribas rm -rf con rutas que no entiendes, ni las copies de internet o de una IA sin leerlas.
Cuatro trucos que te ahorran horas

    •↑ y ↓: recorren las órdenes que ya escribiste. No vuelvas a teclear una orden larga.
    •Tab: autocompleta nombres de carpetas y ficheros. Escribe cd pru + Tab. Si no completa, pulsa Tab dos veces y verás las opciones. Así no hay erratas.
    •Ctrl+C: corta la orden que está en marcha (si algo se queda «colgado»). En la terminal no sirve para copiar: usa Ctrl+Shift+C / Ctrl+Shift+V en Linux, o selecciona con el ratón.
    •--help: casi toda orden explica sus opciones con orden --help. Tu herramienta también lo hará.

Mini-reto: tu carpeta de pruebas para toda la semana

Tu herramienta va a mover, renombrar y borrar ficheros. Nunca la pruebes con tus ficheros reales: créate una carpeta de pruebas con ficheros de mentira (vacíos). Ejecuta el bloque de tu sistema y comprueba el resultado con ls -la. Si lo rompes, bórrala y vuelve a crearla: para eso está.

🐧🍎 bash (Linux y macOS)
bash
mkdir -p ~/pruebas-tareas/fotos ~/pruebas-tareas/docs
cd ~/pruebas-tareas
touch factura-octubre.pdf apuntes-tema1.pdf contrato.docx
touch fotos/IMG_0001.jpg fotos/IMG_0002.jpg fotos/captura.png
touch cache-1.tmp cache-2.tmp borrador.tmp
touch -t 202609010000 viejo-1.tmp viejo-2.tmp    # fecha: 1 sep 2026 (más de 30 días)
touch "mi fichero con espacios.pdf"
echo "hola, soy un fichero con texto" > docs/notas.txt
ls -la
ls -la fotos docs

🪟 PowerShell (Windows)
PowerShell
New-Item -ItemType Directory -Force "$HOME\pruebas-tareas\fotos", "$HOME\pruebas-tareas\docs" | Out-Null
Set-Location "$HOME\pruebas-tareas"
"factura-octubre.pdf", "apuntes-tema1.pdf", "contrato.docx",
"fotos\IMG_0001.jpg", "fotos\IMG_0002.jpg", "fotos\captura.png",
"cache-1.tmp", "cache-2.tmp", "borrador.tmp", "viejo-1.tmp", "viejo-2.tmp",
"mi fichero con espacios.pdf" | ForEach-Object { New-Item -ItemType File -Force $_ | Out-Null }
"viejo-1.tmp", "viejo-2.tmp" | ForEach-Object { (Get-Item $_).LastWriteTime = Get-Date "2026-09-01" }
"hola, soy un fichero con texto" | Set-Content "docs\notas.txt" -Encoding utf8
Get-ChildItem -Force
Get-ChildItem fotos, docs

Comprueba que tienes 3 .pdf (uno con espacios), un .docx, 5 .tmp (dos de ellos con fecha de septiembre), 3 imágenes en fotos/ y un notas.txt con texto en docs/. En ls -la, fíjate en la columna de la fecha de los viejo-*.tmp: la usarás en la semana 2 para «borrar temporales de más de 30 días».
Permisos: por qué a veces dice «Permiso denegado»

En Linux y macOS cada fichero tiene permisos de lectura (r), escritura (w) y ejecución (x) para ti, tu grupo y el resto. ls -l los enseña en la primera columna. Pruébalo con un script de una línea:
bash
cd ~/pruebas-tareas
printf '#!/bin/sh\necho "Hola desde un script"\n' > saludo.sh
ls -l saludo.sh      # -rw-r--r--  → nadie puede ejecutarlo
./saludo.sh          # Permiso denegado
chmod +x saludo.sh   # +x = dale permiso de ejecución
ls -l saludo.sh      # -rwxr-xr-x  → ahora sí
./saludo.sh          # Hola desde un script
saludo.sh            # orden no encontrada: esta carpeta NO está en el PATH

En Windows no hay chmod: lo que decide si algo se ejecuta es la extensión (.exe, .ps1) y la política de ejecución de PowerShell. Tu comando tareas lo instalará uv con los permisos correctos en los tres sistemas.
El PATH: la lista de sitios donde la terminal busca órdenes

¿Por qué ls funciona en cualquier carpeta y saludo.sh no? Porque cuando escribes una orden sin ruta, la terminal la busca en una lista de carpetas llamada PATH, por orden, y ejecuta la primera que encuentra. ls está en /usr/bin, que está en el PATH. Tu carpeta de pruebas no; por eso hay que escribir ./saludo.sh (ruta relativa).

🐧🍎 bash
bash
echo $PATH                  # lista de carpetas separadas por :
echo $PATH | tr ':' '\n'    # la misma lista, una por línea
which ls                    # ¿de qué carpeta sale ls?
which python3 git

🪟 PowerShell
PowerShell
$env:Path -split ";"         # carpetas separadas por ;
Get-Command git              # ¿de dónde sale git?
Get-Command python

Guárdate la idea: en el paso 6 instalarás tareas en una carpeta que debe estar en el PATH. Si un día escribes una orden y te dice «orden no encontrada» o «no se reconoce como nombre de un cmdlet», el 99 % de las veces es el PATH.
Paso 2 · Instala las herramientas: git, uv y OpenCode 35 min

Necesitas tres cosas: git (ya lo usaste en la web de marca), uv, el gestor de proyectos Python que usaremos (crea el proyecto, instala Python, gestiona dependencias y entornos virtuales y convierte tu código en un comando: una sola herramienta en lugar de pip, venv, pipx y pyenv), y OpenCode, el agente que va a escribir código contigo. En los equipos del aula puede que ya estén instalados: compruébalo con git --version, uv --version y opencode --version antes de instalar nada.
2.1 · git y uv

🐧🍎 Linux y macOS
bash
git --version               # si falla: sudo apt install git (Linux) · xcode-select --install (macOS)
curl -LsSf https://astral.sh/uv/install.sh | sh
# cierra la terminal y abre una nueva (o: source $HOME/.local/bin/env)
uv --version
uv python install 3.12
uv python list --only-installed

🪟 Windows (PowerShell)
PowerShell
git --version               # si falla: winget install --id Git.Git -e   (y abre otra terminal)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# cierra Windows Terminal y ábrela otra vez
uv --version
uv python install 3.12
uv python list --only-installed

Debes ver git (cualquiera reciente), uv y un Python 3.12 o superior. Fíjate en que el instalador de uv es un script descargado de internet que se ejecuta en tu máquina: está bien porque viene de la web oficial de Astral, pero nunca lo hagas con una URL que no conoces.
«uv: orden no encontrada» / «uv no se reconoce como nombre de un cmdlet» justo después de instalar: es el PATH. El instalador ha añadido su carpeta (~/.local/bin o %USERPROFILE%\.local\bin) al PATH, pero solo las terminales nuevas lo leen. Cierra la terminal (en VS Code, la papelera de la terminal; a veces hay que reiniciar VS Code entero) y abre otra. En Linux/macOS también vale source $HOME/.local/bin/env.

Alternativa clásica (solo si uv no te funciona y ya lo has consultado): Python 3.12 de python.org, python -m venv .venv + pip install typer, y pipx para instalar el comando. Funciona, pero son más pasos y en clase todo irá con uv.
2.2 · OpenCode 1.18.35 (versión fijada)

En clase usamos exactamente la 1.18.35. Conviven OpenCode 1 y OpenCode 2, con configuraciones incompatibles: si instalas «la última» te llevas la 2 y nada de lo que copies de estas páginas funcionará.

🐧🍎 Linux y macOS
bash
curl -fsSL https://opencode.ai/install | bash -s -- --version 1.18.35
# cierra la terminal y abre una nueva (el instalador añade ~/.opencode/bin al PATH)
opencode --version          # debe decir 1.18.35

🪟 Windows (PowerShell)
PowerShell
git --version               # Git for Windows: OpenCode lo necesita (ejecuta sus órdenes con Git Bash)
node --version              # Node LTS; si falla, instálalo desde nodejs.org y abre otra terminal
npm install -g opencode-ai@1.18.35
# cierra la terminal y abre una nueva
opencode --version          # debe decir 1.18.35

    •El script de Linux/macOS instala en ~/.opencode/bin y añade esa carpeta al PATH: por eso hay que abrir una terminal nueva.
    •En Windows, OpenCode necesita Git for Windows porque ejecuta sus órdenes con Git Bash, y Node LTS para instalarse con npm. Alternativa que recomienda su documentación: WSL (Ubuntu dentro de Windows) y el script de Linux.
    •No uses brew install opencode ni pacman -S opencode: instalan la versión 2.
    •Si un tutorial habla de permissions o agents en plural, es de OpenCode 2. Nosotros escribimos permission, agent y provider en singular.

2.3 · Conéctalo con los modelos del centro

OpenCode no trae inteligencia propia: habla con un modelo de IA. Usaremos los modelos locales del instituto (un servidor del centro con API compatible con OpenAI). La configuración va en tu carpeta personal, no en el repo: crea la carpeta y abre el fichero con tu editor.

🐧🍎 bash
bash
mkdir -p ~/.config/opencode
code ~/.config/opencode/opencode.json     # o nano, o el editor que uses

🪟 PowerShell
PowerShell
New-Item -ItemType Directory -Force "$HOME\.config\opencode" | Out-Null
code "$HOME\.config\opencode\opencode.json"

Pega esto tal cual (no cambies nada: la dirección y la clave salen de variables de entorno):
JSON · ~/.config/opencode/opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "autoupdate": false,
  "provider": {
    "centro": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "IA del centro",
      "options": {
        "baseURL": "{env:CENTRO_IA_URL}",
        "apiKey": "{env:CENTRO_IA_KEY}"
      },
      "models": {
        "qwen3.8-flash-next": {
          "name": "Qwen 3.8 Flash-Next (centro)",
          "limit": { "context": 524288, "output": 65536 },
          "tool_call": true
        }
      }
    }
  },
  "model": "centro/qwen3.8-flash-next",
  "small_model": "centro/qwen3.8-flash-next"
}

    •provider.centro: un proveedor que llamamos «centro», compatible con la API de OpenAI.
    •{env:CENTRO_IA_URL} y {env:CENTRO_IA_KEY}: OpenCode lee la dirección y la clave de dos variables de entorno. Así la clave no está escrita en ningún fichero que pueda acabar en git.
    •model: el modelo que usa por defecto, en formato proveedor/modelo.
    •"autoupdate": false: que no se actualice solo (y se pase a la 2).
    •Si tu editor marca provider como «deprecated», ignóralo: el esquema publicado ya es el de la versión 2.

Ahora las dos variables. La dirección (termina en /v1) y la clave te las da el profesor en clase o en el aula virtual. No las publiques en el repo, en el README ni en ningún chat.

🐧🍎 bash (Linux y macOS)
bash
# Sustituye lo que va entre comillas por lo que te da el profesor
echo 'export CENTRO_IA_URL="LA_URL_DEL_PROFESOR"' >> ~/.bashrc     # macOS (zsh): ~/.zshrc
echo 'export CENTRO_IA_KEY="LA_CLAVE_DEL_PROFESOR"' >> ~/.bashrc
# cierra la terminal y abre una nueva
# ¿te equivocaste? Corrige las dos líneas al final de ~/.bashrc con tu editor

🪟 PowerShell (Windows)
PowerShell
setx CENTRO_IA_URL "LA_URL_DEL_PROFESOR"
setx CENTRO_IA_KEY "LA_CLAVE_DEL_PROFESOR"
# setx solo afecta a las terminales NUEVAS: cierra esta (y reinicia VS Code)

En una terminal nueva, comprueba que todo encaja:
bash
opencode models centro              # debe salir: centro/qwen3.8-flash-next
opencode debug config               # la config que ha leído; la clave sale enmascarada
opencode run "Responde solo: hola"  # prueba real con el modelo del centro
# si no contesta y se queda reintentando: Ctrl+C y mira «Si te atascas»
Semipresencial: desde casa, cómo llegar al servidor del centro lo explica el profesor en la tutoría colectiva de arranque. Hasta entonces, deja hecha la instalación y la config: si opencode models centro ya lista el modelo, la parte que depende de ti está bien.
Paso 3 · Crea el proyecto a mano y haz el primer commit 35 min

El esqueleto lo haces tú, sin agente: son cuatro órdenes y así sabes qué hay en tu repo antes de dejar entrar a nadie. Ve a la carpeta donde guardas tus proyectos (no dentro de pruebas-tareas ni dentro del repo de la web de marca):
bash
cd ~                                     # o la carpeta donde guardes tus proyectos
uv init --package --name tareas --python 3.12 cli-tareas
cd cli-tareas
uv add typer
ls -la
ls src/tareas

Qué significa cada trozo de la orden importante:

    •uv init: crea un proyecto Python nuevo.
    •--package: con estructura de paquete instalable (carpeta src/). Es lo que permite convertirlo en un comando.
    •--name tareas: el paquete se llama tareas. Sin esto, uv lo llamaría cli_tareas (el nombre de la carpeta con guion bajo).
    •--python 3.12: fija la versión mínima de Python.
    •cli-tareas: la carpeta que crea (y el nombre de tu repo).
    •uv add typer: añade Typer, la librería para hacer CLIs (trae Rich, la de colores y tablas), y crea el entorno virtual .venv/.

Fichero / carpeta	Qué es	¿Al repo?
pyproject.toml	La ficha del proyecto: nombre, versión, Python mínimo, dependencias y qué comandos instala.	Sí
src/tareas/__init__.py	Convierte la carpeta en un paquete de Python. Aquí guardaremos la versión.	Sí
.python-version	Qué Python usa uv en este proyecto (3.12).	Sí
uv.lock	Las versiones EXACTAS de todo lo instalado. Así en otro ordenador se instala lo mismo.	Sí
README.md	La portada del repo. En el paso 5 pondrás aquí tu spec.	Sí
.venv/	El entorno virtual: Python y librerías de este proyecto. Pesa mucho y se regenera con uv sync.	NO
.git/	uv ya ha hecho git init por ti. Es la historia del repo.	(es el repo)
Dos ajustes a mano

Abre la carpeta en tu editor (en casa, code . abre VS Code aquí). Primero, en pyproject.toml, cambia la línea de [project.scripts]: ese bloque dice «cuando instalen esto, crea un comando tareas que ejecute el objeto app del módulo tareas/cli.py». Rellena también la descripción.
TOML
[project]
name = "tareas"
version = "0.1.0"
description = "Automatiza tareas repetitivas con ficheros desde la terminal"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.20",          # tu versión puede ser otra: la pone uv add
]
​
[project.scripts]
tareas = "tareas.cli:app"   # antes ponía: tareas = "tareas:main"
​
[build-system]
# lo que haya puesto uv aquí, déjalo tal cual

Segundo, sustituye el contenido de src/tareas/__init__.py (uv pone una función main de ejemplo que ya no usaremos) por solo la versión:
Python
"""tareas: automatiza tareas repetitivas con ficheros desde la terminal."""
​
__version__ = "0.1.0"

Todavía no funciona uv run tareas: falta cli.py, que construirá el agente en el paso 5. Si lo pruebas ahora verás ModuleNotFoundError: No module named 'tareas.cli', y es normal.
.gitignore y .gitattributes antes de nada

Antes del primer commit decides qué no entra nunca en el repo. Un secreto que llega a un commit se queda en el historial aunque lo borres después, y en la semana 3 tendrás una clave en .env. Sustituye el .gitignore que ha creado uv por este (el de uv no incluye .env):
.gitignore
# Entorno virtual que crea uv (se regenera con: uv sync)
.venv/
​
# Cachés de Python
__pycache__/
*.egg-info
dist/
​
# Secretos: claves de API y configuración privada. NUNCA al repo.
.env

Y crea .gitattributes con una sola línea. Hace que Git guarde los saltos de línea igual venga el fichero de Windows (CRLF) o de Linux/macOS (LF): sin ella, un compañero con Windows te cambiaría todas las líneas de todos los ficheros en un solo commit.
.gitattributes
* text=auto
Primer commit, ANTES de abrir OpenCode
¿Por qué ahora y no después? OpenCode guarda una instantánea de tus ficheros antes de cada cambio, en un git interno suyo (no crea commits en tu repo), y con ella /undo deshace lo que haya hecho el agente. Para eso necesita que la carpeta sea un repositorio git, y reconoce tu proyecto por su primer commit. Sin git y sin commit, /undo no puede devolverte tus ficheros.

Si Git te pregunta quién eres o no lo tienes configurado en este equipo, repasa la configuración global de la sesión 2 de la web de marca.
bash
git status                  # si dice "not a git repository": git init
git add .gitignore .gitattributes pyproject.toml uv.lock .python-version README.md src
git status                  # comprueba: NO debe aparecer .venv ni .env
git commit -m "Crea el proyecto con uv y Typer, con .gitignore y .gitattributes"
git branch -M main
git log --oneline

Fíjate en que añadimos los ficheros por su nombre y no con git add . a ciegas: así ves qué entra. Si en el git status aparece .venv o .env, para: tu .gitignore no está bien guardado.
Sube el repo a GitHub (público)
bash
# Opción A · con la CLI de GitHub (si tienes gh y has hecho: gh auth login)
gh repo create cli-tareas --public --source=. --push
​
# Opción B · desde la web: crea el repo VACÍO (sin README, sin .gitignore, sin licencia)
git remote add origin https://github.com/TU_USUARIO/cli-tareas.git
git push -u origin main

Si al hacer push te pide usuario y contraseña, la contraseña es un token, no la de tu cuenta: lo tienes explicado en «Usuario y contraseña: qué escribir exactamente». Abre tu repo en el navegador y comprueba que se ven src/, pyproject.toml y .gitignore, y que no se ve .venv.
Paso 4 · Prepara a tu agente: permisos y AGENTS.md 35 min

Un chat solo genera texto y tú copias y pegas. Un agente además usa herramientas: lee tus ficheros, los edita y ejecuta órdenes en tu terminal, mira el resultado y decide el siguiente paso. Por eso, antes de dejarlo trabajar, decides qué puede hacer solo, qué te tiene que preguntar y qué tiene prohibido. Eso va en un opencode.json en la raíz de cli-tareas, que sí se sube al repo (no lleva ninguna clave).
JSON · cli-tareas/opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "edit": "ask",
    "webfetch": "ask",
    "external_directory": "ask",
    "read": { "*": "allow", "*.env": "deny", "*.env.*": "deny", "*.env.example": "allow" },
    "bash": {
      "*": "ask",
      "ls *": "allow",
      "pwd": "allow",
      "cat *": "allow",
      "git status *": "allow",
      "git diff *": "allow",
      "git log *": "allow",
      "uv run tareas --help": "allow",
      "uv run tareas validar *": "allow",
      "uv run pytest *": "allow",
      "git commit *": "ask",
      "git push *": "deny",
      "git reset *": "deny",
      "rm *": "deny",
      "sudo *": "deny"
    }
  },
  "agent": {
    "plan": { "permission": { "edit": "deny" } }
  }
}
Regla	Qué significa	Por qué así
allow · ask · deny	Lo hace sin preguntar · te pregunta antes · bloqueado.	Tres niveles de confianza; tú los decides.
"edit": "ask"	Cada vez que quiera crear o cambiar un fichero te enseña el diff y espera.	En la semana 1 es obligatorio: lees cada cambio antes de aceptarlo.
read con *.env en deny	Puede leer todo el proyecto menos tus ficheros de secretos.	Tu clave de la semana 3 no debe viajar al modelo. .env.example sí (no lleva claves).
bash: "*": "ask"	Cualquier orden pregunta, salvo las de la lista.	Las de solo mirar (ls, git status, git diff, uv run tareas --help) no hacen daño y van en allow.
uv run tareas ejecutar … (no está)	Cae en el «*»: pregunta.	Desde la semana 2 esa orden mueve y borra ficheros: nunca sin que tú lo veas.
git push, git reset, rm, sudo en deny	Prohibidos para el agente.	El push y los commits son tuyos. Borrar o reescribir historia, nunca.
agent.plan	El agente plan no puede editar nada; las órdenes siguen las reglas de arriba (rm, git push… siguen bloqueadas).	Así plan es de verdad «solo pensar». Si le pusieras bash: ask aquí, anularía los deny de arriba.
Gana la ÚLTIMA regla que coincide. Por eso el "*": "ask" va primero (regla general) y los deny al final (excepciones que mandan). Si pusieras un "*": "allow" debajo, anularía todos los deny. Y nunca arranques OpenCode con --auto (aprueba todo sin preguntar).
Abre OpenCode en la carpeta del proyecto

Trabaja con dos terminales: una con OpenCode y otra para ti (git, pruebas). En VS Code, el botón + o «dividir» de la terminal; en el aula, otra pestaña.
bash
cd ~/cli-tareas        # o donde creaste el proyecto
opencode

Lo que ves es una TUI (interfaz de texto): un programa de terminal con ventanas y atajos. La herramienta con la que vas a programar tu CLI es… otra CLI. Fíjate en cómo está hecha: es lo que estás aprendiendo a construir.
Tecla / texto	Qué hace
Tab	Cambia de agente: build (hace cambios) ↔ plan (solo piensa y propone). Lo ves abajo, junto al modelo.
@fichero	Adjunta un fichero al mensaje (con búsqueda: escribe @READ y elige). Es como decir «mira esto».
!orden	Ejecuta una orden tuya en la terminal y le pasa la salida al agente: !uv run tareas --help.
Esc	Interrumpe al agente mientras responde (si se va por las ramas).
ctrl+x y luego u · /undo	Deshace tu último mensaje y los cambios en ficheros que provocó. /redo lo rehace.
/new	Sesión nueva (conversación limpia). Una por tarea.
/compact	Resume la conversación cuando se alarga, para no llenar la memoria del modelo.
/export	Exporta la conversación a Markdown.
ctrl+p · /help	Paleta de comandos y ayuda.
ctrl+c	Sale de OpenCode. opencode -c continúa la última sesión.
/init: el AGENTS.md del proyecto

AGENTS.md es un fichero en la raíz con las normas de tu proyecto para el agente: con qué está hecho, cómo se ejecuta y qué no debe hacer nunca. OpenCode lo lee al empezar cada sesión, así no tienes que repetirlo en cada mensaje. Escribe en OpenCode (agente build):

/init

Analiza el repo y te propone un AGENTS.md. Como tienes edit: ask, te enseñará el fichero antes de escribirlo: léelo y acéptalo. Después edítalo tú en tu editor hasta que diga esto (o algo muy parecido; si /init no lo genera bien, créalo tú directamente con esta plantilla):
Markdown · cli-tareas/AGENTS.md
# tareas · CLI de tareas con ficheros (proyecto de 1º DAM)
## Stack y órdenes
- Python 3.12 + Typer + Rich, gestionado con uv (src layout, paquete src/tareas).
- Ejecutar: `uv run tareas --help` · Validar config: `uv run tareas validar` · Pruebas (semana 4): `uv run pytest`.
## Normas
- Mensajes y comentarios en español; código claro antes que listo.
- pathlib siempre, encoding="utf-8", nada de os.system ni shell=True: tiene que funcionar en Linux, Windows y macOS.
- Nunca ejecutes acciones sobre carpetas reales: solo en ~/pruebas-tareas y con --simular.
- No toques .env ni escribas claves en ningún fichero. No hagas git push ni commits: los hace el alumno.
- Antes de cambiar un fichero, explica en 2-3 líneas qué vas a hacer.

Cada línea tiene un motivo: la de ~/pruebas-tareas protege tus ficheros reales, la de .env tus claves y la de «explica antes de cambiar» te da tiempo a decir que no. Los cambios en opencode.json no se aplican en caliente: si lo tocas, sal (ctrl+c) y vuelve a abrir opencode.

En tu otra terminal, el commit de la configuración del agente:
bash
git status                  # deben aparecer opencode.json y AGENTS.md, y nada más
git add opencode.json AGENTS.md
git commit -m "Añade opencode.json con los permisos del agente y AGENTS.md con las normas del proyecto"
git push
Paso 5 · Tu primera orden, de forma agéntica 75 min

Así trabajaremos todo el curso, en todas las sesiones: tú decides, el agente propone, tú corriges el plan, el agente implementa, tú apruebas cada cambio, tú pruebas y tú commiteas. El agente no decide qué hace tu herramienta.

    1Tú

    Escribes la intención: spec, criterio de aceptación.

    2plan

    «Explícame cómo lo harías»: lees y corriges el plan.

    3build

    «Hazlo»: apruebas cada edición y cada orden leyendo el diff.

    4Tú

    Auditas y pruebas con !uv run tareas …. Si falla: /undo o le explicas el fallo.

    5Tú

    Commit pequeño hecho por ti. Prompt clave a docs/prompts.md.

    6/new

    Sesión nueva para la siguiente tarea.

5.1 · Escribe la spec en el README (tú, sin IA · 15 min)

Copia esta plantilla en tu README.md y rellena los huecos tú. Piensa en una tarea real que te aburra: ordenar descargas, renombrar fotos del móvil, limpiar temporales, organizar apuntes por asignatura... Es lo que leerá el agente para saber qué construir.

# tareas

Mi herramienta de línea de órdenes para automatizar tareas repetitivas con ficheros.

## Spec (versión 0 · 26/10/2026)
1. **Problema:** cada semana pierdo tiempo en ________ (ej.: ordenar Descargas a mano).
2. **Para quién:** para mí y para ________.
3. **Cómo se usa:** `tareas ORDEN [CARPETA] [opciones]` desde cualquier terminal.
4. **Órdenes de la semana 1:** `tareas --help`, `tareas version`, `tareas listar [CARPETA]`.
5. **Órdenes previstas:** `tareas acciones`, `tareas validar`, `tareas ejecutar NOMBRE --simular`.
6. **Mis 3 acciones (borrador):** ________, ________, ________.
7. **Nunca hará:** borrar sin preguntar ni tocar ficheros fuera de la carpeta que le indique.
8. **Plataformas:** Linux primero; también Windows y macOS.
9. **Códigos de salida:** 0 bien · 1 fallo al ejecutar · 2 uso incorrecto · 3 configuración inválida.
10. **Instalación:** `uv tool install --editable .` (lo completo en la semana 4).

bash
git add README.md
git commit -m "Escribe la spec v0 de la herramienta en el README"
5.2 · Agente plan: que te cuente cómo lo haría

Pulsa Tab hasta que abajo ponga plan. En plan no puede tocar ningún fichero (lo dice tu opencode.json), así que puedes pedirle ideas sin miedo. Envía:

Lee @README.md y @pyproject.toml. Quiero src/tareas/cli.py (app de Typer llamada app) y src/tareas/__main__.py con dos órdenes: version y listar [CARPETA].
No escribas código todavía: dime qué ficheros crearías, qué funciones tendría cada uno y cómo tratarías la carpeta inexistente, la vacía, los nombres con corchetes y los ficheros que no se pueden leer.

Criterio de aceptación:
- uv run tareas sin argumentos muestra la ayuda, en español y sin autocompletado.
- version imprime «tareas 0.1.0» leyendo __version__ del paquete.
- listar (por defecto la carpeta actual, acepta ~) pinta una tabla Rich: Nombre, Tipo (extensión o «carpeta»), Tamaño legible, Modificado (AAAA-MM-DD HH:MM). Carpetas primero, luego alfabético sin distinguir mayúsculas.
- Carpeta inexistente o que no es carpeta: mensaje en stderr, sin traza, código 1. Carpeta vacía: aviso en vez de tabla vacía.
- pathlib, sin os.system ni subprocess, sin dependencias nuevas. uv run python -m tareas también funciona.

El texto es corto porque el agente lee tu repo: con @README.md y @pyproject.toml ya tiene el contexto. Lo que no puede faltar es el criterio de aceptación: cómo sabrás tú que está bien. Lee su plan buscando esto:

    ¿Toca solo src/tareas/cli.py y src/tareas/__main__.py? Si quiere cambiar más ficheros, pregunta por qué.
    ¿Añade dependencias nuevas? No hacen falta: Typer ya trae Rich.
    ¿Usa pathlib y expanduser()? ¿Dice qué hace con la carpeta inexistente, la vacía y los corchetes?
    ¿Hay algo que no entiendes? Pregúntalo ahora, antes de que escriba código.

Corrige el plan con un mensaje corto, por ejemplo:

Dos cambios al plan:
1. Escapa los nombres con rich.markup.escape para que [borrador].pdf salga entero.
2. Si un fichero da error al leer su fecha o tamaño (enlace roto, sin permisos), sáltalo sin romper la tabla.
Repíteme el plan corregido en 5 líneas.

5.3 · Agente build: «hazlo», y tú apruebas cada cambio

Pulsa Tab para volver a build y envía:

Hazlo con el plan corregido. Toca solo src/tareas/cli.py y src/tareas/__main__.py.
Cuando acabes, ejecuta uv run tareas --help y dime qué órdenes pruebo yo en ~/pruebas-tareas.

Ahora el agente trabaja y, cada vez que quiera escribir un fichero o ejecutar una orden que no está en tu lista de allow, se para y te pregunta. Puedes contestar:
Respuesta	Qué hace	Cuándo
once	Lo permite solo esta vez.	Lo normal esta semana: lees, entiendes y aceptas.
always	Permite eso mismo durante el resto de la sesión.	Solo para órdenes inofensivas que se repiten. Nunca para ediciones esta semana.
reject	Lo rechaza. El agente lo ve y busca otra forma.	Si no entiendes el cambio o no es lo que pediste. Después explícale por qué.

Qué mirar en cada diff (líneas en verde: se añaden; en rojo: se quitan):

    ¿Es el fichero que esperabas? ¿Toca algo fuera de src/tareas/? Ojo especial con pyproject.toml y uv.lock.
    ¿Borra algo tuyo (líneas en rojo que no esperabas)?
    ¿Rutas escritas a mano con "/" o "\", os.system, subprocess o shell=True? Rechaza y pide pathlib.
    ¿Los mensajes al usuario están en español y los errores van por stderr?
    Si te pide ejecutar una orden: léela entera. ¿Sabes qué hace? ¿Toca algo fuera de cli-tareas? Si no lo tienes claro, reject y pregunta.

5.4 · Pruébalo tú

Que el agente diga «hecho» no significa que funcione. Pruébalo sin salir de OpenCode con ! (la salida le llega también al agente):

!uv run tareas version
!uv run tareas listar ~/pruebas-tareas
!uv run tareas listar /no/existe; echo $?

Y en tu otra terminal, la batería completa:
bash
uv run tareas --help
uv run tareas version
uv run tareas listar ~/pruebas-tareas
uv run tareas listar ~/pruebas-tareas/fotos
uv run tareas listar                        # la carpeta actual
uv run tareas listar /no/existe; echo $?    # debe imprimir 1
uv run tareas listar a b; echo $?           # error de uso: 2 (lo pone Typer)
uv run python -m tareas --help
PowerShell
uv run tareas --help
uv run tareas listar "$HOME\pruebas-tareas"
uv run tareas listar C:\no\existe; $LASTEXITCODE    # debe imprimir 1

echo $? (bash) y $LASTEXITCODE (PowerShell) muestran el código de salida de la última orden: 0 si fue bien y otro número si falló. Los scripts y GitHub Actions deciden con él si algo ha funcionado, así que tu herramienta debe devolver el correcto. Nuestro convenio: 0 bien · 1 fallo al ejecutar · 2 error de uso (lo pone Typer) · 3 configuración inválida (semana 2).
5.5 · Si algo sale mal: /undo o explícale el fallo

    •Lo ha estropeado o se ha ido por las ramas: Esc si aún está trabajando y luego /undo (o ctrl+x u). Tus ficheros vuelven a como estaban antes de ese mensaje. Reformula y vuelve a intentarlo.
    •Funciona casi, pero falla un caso: no lo arregles a ciegas ni le digas «no funciona». Dale la orden, lo que sale y lo que esperabas, con el fichero:

!uv run tareas listar ~/pruebas-tareas/contrato.docx; echo $?
Sale una traza de Python y código 1; esperaba el mensaje de error en stderr y código 1, sin traza.
Corrige solo eso en @src/tareas/cli.py y explícame en 2 líneas qué fallaba.

/undo deshace ficheros, pero no lo que ya salió de tu equipo (un git push) ni lo que instaló. Por eso el push lo tiene prohibido y lo haces tú.
5.6 · Lo que deberías tener: audítalo contra esto

No hace falta que tu cli.py sea idéntico, pero debe hacer lo mismo. Compáralo línea a línea: si al tuyo le falta algo de lo que hay aquí (el escape, el typer.Exit(code=1), el expanduser()), pregúntale al agente en plan por qué no lo puso y decide tú.
Python · src/tareas/cli.py
"""Interfaz de línea de órdenes: aquí solo hay órdenes, opciones y salida."""
​
from datetime import datetime
from pathlib import Path
from typing import Annotated
​
import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table
​
from tareas import __version__
​
app = typer.Typer(
    help="tareas: automatiza tareas repetitivas con tus ficheros.",
    no_args_is_help=True,
    add_completion=False,
)
consola = Console()
consola_err = Console(stderr=True)
​
​
def tamano_legible(n: int) -> str:
    """Convierte bytes en texto: 532 B, 1.2 KB, 3.4 MB..."""
    if n < 1024:
        return f"{n} B"
    tamano = float(n)
    unidad = "B"
    for unidad in ("KB", "MB", "GB", "TB"):
        tamano /= 1024
        if tamano < 1024:
            break
    return f"{tamano:.1f} {unidad}"
​
​
@app.command()
def version() -> None:
    """Muestra la versión instalada."""
    consola.print(f"tareas {__version__}")
​
​
@app.command()
def listar(
    carpeta: Annotated[
        Path, typer.Argument(help="Carpeta que quieres ver (por defecto, la actual).")
    ] = Path("."),
) -> None:
    """Lista los ficheros de una carpeta en una tabla."""
    carpeta = carpeta.expanduser()
    if not carpeta.is_dir():
        consola_err.print(
            f"[red]Error:[/red] «{escape(str(carpeta))}» no existe o no es una carpeta."
        )
        raise typer.Exit(code=1)
​
    elementos = sorted(carpeta.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    if not elementos:
        consola.print(f"La carpeta «{escape(str(carpeta))}» está vacía.")
        return
​
    tabla = Table(title=f"Contenido de {escape(str(carpeta.resolve()))}")
    tabla.add_column("Nombre")
    tabla.add_column("Tipo")
    tabla.add_column("Tamaño", justify="right")
    tabla.add_column("Modificado")
​
    for ruta in elementos:
        try:
            datos = ruta.stat()
        except OSError:
            continue  # enlace roto o sin permisos: lo saltamos
        es_carpeta = ruta.is_dir()
        tipo = "carpeta" if es_carpeta else (ruta.suffix.lower() or "(sin extensión)")
        tamano = "—" if es_carpeta else tamano_legible(datos.st_size)
        fecha = datetime.fromtimestamp(datos.st_mtime).strftime("%Y-%m-%d %H:%M")
        tabla.add_row(escape(ruta.name), tipo, tamano, fecha)
​
    consola.print(tabla)
Python · src/tareas/__main__.py
"""Permite ejecutar el paquete con: python -m tareas"""
​
from tareas.cli import app
​
app(prog_name="tareas")

    •@app.command() convierte una función en una orden. El docstring ("""...""") es lo que sale en --help.
    •El argumento carpeta tiene tipo Path: Typer convierte lo que escribes en una ruta de pathlib, que funciona igual en Linux, Windows y macOS.
    •raise typer.Exit(code=1) termina el programa con código 1 sin soltar una traza de Python al usuario.
    •El error va a Console(stderr=True): la salida de errores, separada de la normal. Así otro programa puede distinguir resultado y error.

Paso 6 · Instálala como comando de verdad 15 min

uv run tareas solo funciona dentro de la carpeta del proyecto. Para que tareas funcione en cualquier sitio, como git, ls u opencode, instálala (en tu terminal, no se lo pidas al agente):
bash
uv tool install --editable .     # desde dentro de cli-tareas
cd ~                             # vete a otra carpeta cualquiera
tareas --help
tareas listar ~/pruebas-tareas
which tareas                     # Windows: Get-Command tareas
uv tool list                     # herramientas instaladas con uv

uv tool install crea un entorno aislado para tu herramienta y deja un ejecutable tareas en la carpeta de comandos de uv (~/.local/bin en Linux y macOS). --editable significa que apunta a tu código: cuando cambies cli.py, el comando instalado cambia también, sin reinstalar. Solo hay que reinstalar si tocas pyproject.toml (dependencias o el nombre del comando): uv tool install --editable . --force.

Si dice «orden no encontrada», esa carpeta no está en tu PATH (¿te suena?):
bash
uv tool dir --bin                # carpeta donde uv deja los comandos
uv tool update-shell             # la añade al PATH de tu terminal
# cierra la terminal, abre otra y prueba de nuevo: tareas --help

Para quitarla (por ejemplo, para probar la instalación desde cero como hará quien use tu repo):
bash
uv tool uninstall tareas
Paso 7 · Audita y commitea TÚ 30 min

«Lo que no sabes explicar, no lo entregas». Aprobar los diffs no basta: antes del commit, repasa esta lista. Si algo falla, pídele el arreglo al agente, pero entiende qué ha cambiado.

    ¿Entiendo cada línea de cli.py? Si hay una que no, pregúntale en plan: «explícame la línea N de @src/tareas/cli.py como si fuera mi primer año».
    ¿Qué pasa con una carpeta vacía? mkdir ~/pruebas-tareas/vacia && tareas listar ~/pruebas-tareas/vacia
    ¿Y con una ruta con espacios? tareas listar "~/pruebas-tareas/carpeta con espacios" (créala antes). Ojo: entre comillas, ~ no lo expande la terminal; lo tiene que hacer tu código con expanduser().
    ¿Y con un fichero en vez de carpeta? tareas listar ~/pruebas-tareas/contrato.docx; echo $? → mensaje y 1.
    ¿Y un nombre con corchetes? touch ~/pruebas-tareas/"[borrador].pdf" y lístalo: el nombre tiene que salir entero.
    ¿Funciona en Windows? Busca en el código barras escritas a mano dentro de rutas ("/"), os.system, shell=True o ficheros abiertos sin encoding="utf-8". Si tienes Windows, pruébalo; si no, pide a alguien que lo pruebe.
    ¿tareas --help se entiende sin haber leído el código? ¿Está en español?
    ¿El agente ha añadido dependencias u órdenes que no pediste? Mira git diff pyproject.toml y git status.

El agente propone el mensaje; el commit lo haces tú

El agente tiene prohibido el push y los commits los tiene que preguntar; además tu AGENTS.md le dice que no los haga. Pídele solo el texto:

Mira git diff y git status y propón un mensaje de commit en español, en imperativo, de una línea, que cuente qué cambia y para qué. No hagas el commit.

Léelo, cámbialo si no cuenta bien lo que hiciste, y commitea tú en tu terminal. Un commit = un paso con sentido. El mensaje dice qué cambia y para qué, en imperativo, como si terminara la frase «Este commit...».
bash
git status                  # ¿solo cli.py y __main__.py? Nada de .env ni .venv
git diff                    # repásalo una última vez
git add src/tareas/cli.py src/tareas/__main__.py
git commit -m "Añade las órdenes version y listar con tabla Rich"
git add docs/prompts.md
git commit -m "Guarda el prompt de la orden listar y lo que corregí"
git push
git log --oneline
❌ Mensajes que no cuentan nada	✅ Mensajes que cuentan el proceso
cambios	Añade la orden listar con tabla Rich
arreglos	Devuelve código 1 si la carpeta no existe
asdf	Escapa nombres con corchetes en la tabla
lo que me ha dado la IA	Guarda en docs/prompts.md el plan de listar y lo que corregí
version final final 2	Escribe la spec v0 en el README
Guarda tus prompts en docs/prompts.md

Crea docs/prompts.md y apunta los prompts clave con lo que corregiste tú. Es tu cuaderno de bitácora y una parte de la nota de proceso: demuestra que dirigiste al agente, no al revés. Si quieres guardar la conversación entera, /export (o ctrl+x x) la exporta a Markdown y la abre en tu editor; guárdala dentro de docs/ y revisa que no contenga ninguna clave antes del commit.

# Prompts clave del proyecto

## 2026-10-27 · Primera orden: listar
**Herramienta:** OpenCode 1.18.35 · modelo centro/qwen3.8-flash-next
**Prompt del plan (agente plan):** (pégalo tal cual lo enviaste)
**Qué corregí del plan:** ej.: no escapaba los nombres con corchetes; [foto].jpg salía sin corchetes.
**Diffs que rechacé o deshice (/undo) y por qué:** ej.: quería añadir la librería humanize.
**Funcionaba a la primera:** sí / no. Qué fallo le expliqué: ________
**Qué aprendí:** ej.: typer.Exit(code=1) termina con código 1 sin traza.

Una sesión por tarea. Cuando termines algo y lo commitees, /new para empezar limpio la siguiente (por ejemplo, «arreglar los corchetes»). Las conversaciones largas confunden al modelo; si una se alarga, /compact. Con el commit del proyecto, el de opencode.json + AGENTS.md, el de la spec, el de cli.py y el de docs/prompts.md ya tienes 5 commits tuyos.
Checklist de la semana (el producto)

    Tengo ~/pruebas-tareas con los ficheros de ejemplo (pdf, jpg, tmp viejos y nuevos, uno con espacios).
    git --version, uv --version y Python 3.12 o superior funcionan.
    opencode --version dice 1.18.35 y opencode models centro lista centro/qwen3.8-flash-next.
    La URL y la clave del centro están en variables de entorno, no en ningún fichero del repo.
    El proyecto cli-tareas tiene pyproject.toml con tareas = "tareas.cli:app".
    .gitignore (con .env y .venv/) y .gitattributes estaban en el primer commit, hecho antes de abrir OpenCode.
    El repo tiene opencode.json con los permisos del proyecto y un AGENTS.md que he revisado y editado yo.
    El README tiene mi spec de 10 líneas, rellenada por mí.
    He construido cli.py con plan → build, aprobando cada diff, y he usado /undo o le he explicado un fallo al menos una vez.
    Desde cualquier carpeta: tareas --help, tareas version y tareas listar ~/pruebas-tareas funcionan.
    tareas listar /no/existe da un mensaje claro y código de salida 1.
    docs/prompts.md tiene al menos el prompt del plan y lo que corregí.
    El repo es público en GitHub, tiene al menos 4 commits hechos por mí con mensajes que cuentan y no contiene .venv ni .env.
    Sé explicar en voz alta qué hace cada línea de cli.py y cada regla de opencode.json.

Si te atascas

Antes de pedir ayuda, lee el mensaje de error entero: casi siempre dice qué pasa. Si no lo entiendes, pégalo en el chat con la orden que escribiste y tu sistema operativo (sin claves). Estos son los habituales:
Terminal, uv y Git
Lo que ves	Qué pasa	Arreglo
tareas: orden no encontrada · «no se reconoce como nombre de un cmdlet»	La carpeta donde uv instala comandos no está en el PATH, o la terminal es anterior a la instalación.	uv tool update-shell, cierra y abre la terminal. Comprueba con uv tool list que está instalada.
uv: orden no encontrada justo después de instalarlo	La terminal todavía no ha leído el PATH nuevo.	Abre una terminal nueva (o reinicia VS Code). En Linux/macOS: source $HOME/.local/bin/env.
«Permiso denegado» / Permission denied	El fichero no tiene permiso de ejecución, o intentas escribir en una carpeta del sistema.	chmod +x fichero si es tu script. Trabaja siempre dentro de tu carpeta personal. Nunca uses sudo con uv ni con pip.
PowerShell: «la ejecución de scripts está deshabilitada en este sistema»	La política de ejecución de Windows bloquea scripts .ps1.	Set-ExecutionPolicy -Scope CurrentUser RemoteSigned (solo afecta a tu usuario).
requires-python · «No interpreter found» · Python 3.10	Python demasiado antiguo para el proyecto.	uv python install 3.12 y uv python pin 3.12 dentro del proyecto. No hace falta tocar el Python del sistema.
ModuleNotFoundError: No module named 'tareas.cli'	Falta src/tareas/cli.py, está en otra carpeta o el paquete se llama distinto.	ls src/tareas. El fichero tiene que estar ahí y [project.scripts] tiene que coincidir.
Push rechazado: ! [rejected] (fetch first)	Creaste el repo de GitHub con README o licencia y tiene un commit que tú no tienes.	git pull --rebase origin main y luego git push.
src refspec main does not match any	Aún no hay commits, o tu rama se llama master.	Haz el primer commit y git branch -M main.
Push: «Authentication failed» / pide contraseña sin parar	Estás usando la contraseña de GitHub en lugar de un token.	Sigue la sesión 2 de la web de marca.
Subiste .venv o .env por error	El .gitignore no estaba antes del commit.	git rm -r --cached .venv, revisa el .gitignore y haz commit. Si era una clave, cámbiala: sigue en el historial. Avisa al profesor.
OpenCode
Lo que ves	Qué pasa	Arreglo
opencode: orden no encontrada · «no se reconoce como nombre de un cmdlet»	La terminal es anterior a la instalación, o la carpeta del programa (~/.opencode/bin, o la de npm global en Windows) no está en el PATH.	Abre una terminal nueva (o reinicia VS Code). Si sigue, repite la instalación del paso 2.2 y mira el mensaje final del instalador.
opencode --version dice 2.x	Lo instalaste con brew install opencode, pacman o «la última versión».	Desinstálalo con el mismo gestor y repite el paso 2.2 con la versión fijada 1.18.35.
opencode models centro no lista nada	La config global no está donde toca, tiene un error de JSON, o usa claves en plural (de la V2).	opencode debug config te dice qué ha leído y dónde falla. Revisa la ruta ~/.config/opencode/opencode.json y que diga provider en singular.
Cannot connect to API · opencode run se queda reintentando sin fin	No llega al servidor del centro: variable vacía, dirección mal copiada (sin /v1) o no estás en la red del centro.	Ctrl+C. Abre una terminal nueva (después de setx o de editar .bashrc es obligatorio) y repite. Desde casa, sigue lo que explicó el profesor en la tutoría. Si en el aula le pasa a todos, avisa.
Error 401 / 403	La clave no llega o está mal copiada.	Revisa CENTRO_IA_KEY en una terminal nueva y opencode debug config (la clave sale enmascarada).
Me pregunta permiso para todo	Es lo que has configurado: edit: ask y bash "*": ask.	Es lo correcto esta semana. Para una orden inofensiva que se repite, responde always. Nunca --auto.
/undo no devuelve los ficheros	La carpeta no es un repositorio git o no tiene ningún commit.	Haz el primer commit (paso 3) y vuelve a abrir opencode. Mientras tanto, git restore fichero si ya estaba commiteado.
V2 permissions are not supported by OpenCode V1	Has copiado configuración de OpenCode 2 (permissions en plural).	Usa el opencode.json de esta página: permission, en singular.
He cambiado opencode.json y no hace caso	La configuración solo se lee al arrancar.	Sal con ctrl+c y vuelve a abrir opencode (o opencode -c para seguir la sesión).