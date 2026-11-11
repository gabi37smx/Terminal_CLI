# Guía rápida de `dam`

> Ejecuta siempre desde:
> `C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\PROJECTE TERMINAL CLI\Terminal_CLI`
>
> Si ya instalaste el comando, usa `dam` en vez de `uv run dam`.

## 0. Ayuda integrada

```powershell
dam              # manual completo: todos los comandos, opciones y ejemplos
dam -h           # lo mismo
dam sync -h      # ayuda detallada de un comando, con sus ejemplos
```

## 1. Comandos

| Comando | Qué hace | Ejemplo |
|---|---|---|
| `dam --help` | Ayuda general | `uv run dam --help` |
| `dam version` | Versión instalada | `uv run dam version` |
| `dam configurar [--ciclo C] [--curso N] [--simular] [--si]` | Pregunta tu ciclo y curso y pone tus asignaturas en `acciones.json` | `uv run dam configurar --ciclo smx --curso 1 --simular` |
| `dam listar [CARPETA]` | Lista ficheros en una tabla | `uv run dam listar "C:\Users\HP\Desktop\DAM\SISTEMES"` |
| `dam validar` | Comprueba `acciones.json` | `uv run dam validar` |
| `dam acciones` | Lista tus acciones | `uv run dam acciones` |
| `dam ejecutar NOMBRE [CARPETA] [--simular] [--si]` | Ejecuta una acción | `uv run dam ejecutar ordenar --simular` |
| `dam comprobar-ia` | ¿Llego al servidor de IA del centro? (nunca enseña la clave) | `uv run dam comprobar-ia` |
| `dam status [ASIGNATURA]` | Qué hay pendiente (no toca nada) | `uv run dam status programacion` |
| `dam scan-secrets [RUTA] [--staged] [--historial] [--alta]` | Busca claves y contraseñas expuestas | `uv run dam scan-secrets --staged` |
| `dam instalar-hook [REPO] [--quitar] [--forzar]` | Revisa claves en cada `git commit` | `uv run dam instalar-hook` |
| `dam doctor [CARPETA]` | Revisa que un proyecto esté sano (git, `.env`, README, tests...) | `uv run dam doctor .` |
| `dam pendientes [CARPETA] [--quien NOMBRE] [--resumen]` | Cuenta `[Verificado]`, `[Hipótesis]` y `[Pendiente]` y resume `pendientes.md` | `uv run dam pendientes ~/Electrician --quien Gabi` |
| `dam entregar [CARPETA] [--destino D] [--nombre N] [--simular]` | Proyecto en un `.zip` limpio, sin `.env` ni claves | `uv run dam entregar . --simular` |
| `dam inventario [CARPETA] [--guardar INFORME.md] [--top N]` | Qué hay en una carpeta: tamaños, repos, tipos, instaladores y basura (solo lee) | `uv run dam inventario ~/Desktop` |
| `dam duplicados [CARPETA] [--guardar INFORME.md] [--top N]` | Ficheros repetidos y carpetas que son copia de otra (no borra nada) | `uv run dam duplicados ~/Datos` |
| `dam readme [CARPETA] [--niveles N] [--simular] [--si]` | README de cada carpeta con una tabla de lo que hay dentro (no toca lo que escribes tú) | `uv run dam readme ~/Datos --simular` |
| `dam test-links [FUENTE] [--sin-externos] [--timeout S]` | Busca enlaces rotos en tu web | `uv run dam test-links ~/portfolio` |
| `dam check-headers URL [--timeout S]` | Cabeceras de seguridad de tu web o API | `uv run dam check-headers https://tu-web.com` |
| `dam sync [ASIGNATURA] [-m MENSAJE] [--integrar] [--simular]` | Sincroniza con GitHub | `uv run dam sync programacion -m "tema 3"` |

## 2. Tus 9 acciones

| Nombre | Tipo | IA | Qué hace |
|---|---|---|---|
| `ordenar` | ordenar | — | Reparte apuntes por asignatura |
| `limpiar-temporales` | borrar | — | Borra temporales de más de 30 días |
| `convertir-webp` | convertir | — | JPEG/PNG a WebP sin tocar el original |
| `renombrar-capturas` | renombrar | — | Renombra capturas con fecha y número |
| `copiar-entregas` | copiar | — | Copia entregas y prácticas a una carpeta de seguridad |
| `mover-zips` | mover | — | Mueve los `.zip` a la subcarpeta `comprimidos` |
| `resumir-tema` | resumir | sí | Resume cada tema en un `.resumen.md` (en castellano aunque el apunte esté en valenciano) |
| `nombrar-descargas` | renombrar-ia | sí | Pone nombre por su contenido a `escaneo_0042.pdf`, `documento (3).pdf`... |
| `clasificar-asignatura` | clasificar | sí | Lleva cada apunte a la carpeta de su asignatura (o a `otros`) |

Sin `CARPETA`, usan el `origen` de `acciones.json`: `~/pruebas-tareas/prueba-final` las seis sin IA,
`~/pruebas-tareas/apuntes-ia` y `~/pruebas-tareas/descargas-ia` las de IA.

Las de IA necesitan el servidor del centro (`CENTRO_IA_URL`, `CENTRO_IA_KEY` y `CENTRO_IA_CA`, en tu
terminal o en un `.env`: mira `.env.example`). Con `--simular` no llaman al modelo: dicen cuántos
caracteres mandarían. Sin red o sin clave salen con 4 y las demás acciones siguen funcionando.

```powershell
uv run dam comprobar-ia                                   # ¿llego al servidor?
uv run dam ejecutar resumir-tema --simular                # cuánto mandaría, sin gastar nada
uv run dam ejecutar resumir-tema                          # de verdad: tokens y segundos en «Detalle»
uv run dam ejecutar nombrar-descargas                     # pregunta s/N antes de renombrar
```

`mover-zips` no comprime: solo mueve los `.zip`. Con otra `CARPETA`, los lleva igualmente a `prueba-final/comprimidos`, y no hay que ejecutarla sobre `comprimidos`, porque renombraría los ficheros. Si quieres guardar antes las entregas, ejecuta `copiar-entregas` primero: después ya no verá los `.zip` que se hayan movido.

```powershell
# Ordenar (primero simular)
uv run dam ejecutar ordenar --simular
uv run dam ejecutar ordenar

# Ordenar una carpeta concreta (solo ficheros sueltos, no entra en subcarpetas)
uv run dam ejecutar ordenar "C:\Users\HP\Desktop\DAM\SISTEMES" --simular

# Limpiar temporales
uv run dam ejecutar limpiar-temporales --simular
uv run dam ejecutar limpiar-temporales --si

# Convertir imágenes
uv run dam ejecutar convertir-webp --simular
uv run dam ejecutar convertir-webp
```

## 3. Opciones importantes

| Opción | Dónde | Qué hace |
|---|---|---|
| `--simular` | `ejecutar`, `sync`, `entregar` | Enseña qué haría sin tocar nada |
| `-m, --mensaje TEXTO` | `sync` | Mensaje del commit (con o sin asignatura) |
| `--sin-externos` | `test-links` | Solo enlaces internos (no necesita internet) |
| `--timeout SEGUNDOS` | `test-links`, `check-headers` | Tiempo máximo de espera (Render gratis: `--timeout 60`) |
| `--quitar`, `--forzar` | `instalar-hook` | Desinstala el hook · reemplaza un hook que no sea de dam |
| `--si` | `ejecutar` | No pide confirmación (peligroso) |
| `--integrar` | `sync` | Si hay cambios en ambos lados, guarda lo tuyo y hace `pull --rebase` |
| `--almacen RUTA` | `status`, `sync` | Usa otro almacén |
| `--config RUTA` | global | Usa otro `acciones.json` (va antes del comando) |

```powershell
uv run dam --config .\acciones.json validar
uv run dam status --almacen "$HOME\DAM-almacen"
```

## 4. Flujo recomendado

```powershell
# 1. Validar configuración
uv run dam validar

# 2. Ver qué haría
uv run dam ejecutar ordenar --simular

# 3. Hacerlo de verdad
uv run dam ejecutar ordenar

# 4. Ver cambios del almacén
uv run dam status

# 5. Simular la subida
uv run dam sync --simular

# 6. Subir
uv run dam sync
```

## 5. Almacén y sincronización

```powershell
# Todo el almacén
uv run dam status
uv run dam sync

# Solo una asignatura
uv run dam status programacion
uv run dam sync programacion "tema 3"

# Mensaje propio para todo el almacén (-m funciona con o sin asignatura)
uv run dam sync -m "subida desde casa"

# También vale, con asignatura: el mensaje como segundo argumento
uv run dam sync programacion "tema 3"

# Si hay cambios tuyos Y en GitHub
uv run dam sync --integrar
```

Ruta del almacén, por prioridad:
1. `--almacen RUTA`
2. Variable `DAM_ALMACEN`
3. `almacen.ruta` de `acciones.json`

Normalmente no hace falta definirla a mano: `instalar.sh` e `instalar.ps1` buscan el almacén hasta 3 niveles dentro de tu carpeta personal (un repo cuyo remoto sea DAM-almacen, se llame como se llame la carpeta). Si no está en `~/DAM-almacen`, guardan `DAM_ALMACEN`: en `.bashrc`/`.zshrc` (Linux/macOS) o como variable de tu usuario (Windows).

```powershell
# Windows: solo esta sesión
$env:DAM_ALMACEN = "$HOME\DAM-almacen"

# Windows: permanente (nuevas terminales)
setx DAM_ALMACEN "$HOME\DAM-almacen"
```

```bash
# Linux / macOS
export DAM_ALMACEN="$HOME/DAM-almacen"
```

## 6. Seguridad

### Buscar claves expuestas: `dam scan-secrets`

```powershell
dam scan-secrets                 # lo que se subiría a git desde la carpeta actual
dam scan-secrets --staged        # solo lo preparado con git add (antes de cada commit)
dam scan-secrets --historial     # TODO el historial de git (la rúbrica exige cero claves)
dam scan-secrets "$HOME\DAM-almacen" --historial    # también el almacén
dam scan-secrets --alta          # solo hallazgos seguros, sin avisos dudosos
```

- Detecta URLs con usuario y contraseña (MongoDB), tokens de GitHub, claves de Google/Gemini (`AIza`), Resend (`re_`), AWS, Slack, `sk-`, tokens JWT (las `SERVICE_KEY` de Supabase), claves privadas, `.env` sin ignorar y asignaciones sospechosas (`password = ...`).
- Ignora las plantillas de ejemplo (`password`, `tu_contraseña`, `xxx`, `eyJ...`) y no lee binarios (PDF, imágenes, docx, zip...): si apuntaste una clave dentro de un `.docx` o un PDF, tendrás que buscarla a mano.
- No cuenta lo que está en `.gitignore`. Nunca imprime la clave entera: solo las primeras letras y la longitud.
- Sale con **0** si está limpio y con **1** si encuentra algo. Un falso aviso se silencia añadiendo `dam:ignore` en esa línea.
- **Si una clave ya se subió**: borrarla NO basta, sigue en el historial. Hay que cambiarla (revocarla) en el servicio.

### Revisar claves en cada commit, sin acordarte

```powershell
dam instalar-hook            # una vez por repositorio (Terminal_CLI y DAM-almacen)
dam instalar-hook --quitar   # para desactivarlo
git commit --no-verify -m "..."   # salta la revisión UNA vez (solo si es un falso aviso)
```

El hook ejecuta `dam scan-secrets --staged` justo antes de cada commit y lo cancela si encuentra algo. Si `dam` no está en el PATH, avisa pero no bloquea. No sobrescribe un hook que no sea de dam (salvo `--forzar`).

### Revisar un proyecto antes de subirlo o entregarlo

```powershell
dam doctor                 # el proyecto de la carpeta actual
dam doctor ~/Electrician   # otro proyecto (no cambia nada)
```

- **Básicas** (si falla alguna, sale con **1**): repositorio git, `.gitignore`, `.env` ignorado y sin subir, `.env.example` con las mismas variables que tu `.env`, README y sin secretos a la vista.
- **Recomendadas** (solo avisan): tests, dependencias declaradas (`pyproject.toml`, `requirements.txt` o `package.json`), CI con GitHub Actions y ficheros de más de 50 MB.
- Del `.env` solo lee los **nombres** de las variables, nunca los valores.

### Qué está verificado y qué no: `dam pendientes`

```powershell
dam pendientes ~/Electrician               # etiquetas por fichero, lo sin verificar y el registro
dam pendientes ~/Electrician --quien Gabi  # solo lo tuyo (y lo de «Todos»)
dam pendientes ~/Electrician --resumen     # solo los números
```

- Cuenta en los `.md` las etiquetas `[Verificado]`, `[Hipótesis]` y `[Pendiente]`, también con texto detrás (`[Verificado, entrevista 4, 29/10/2026]`). Un `[Verificado]` **sin fecha** en su línea sale aparte: le falta la fuente.
- Si hay un `pendientes.md` con una tabla de columnas `#`, `Dato`, `Responsable` y `Estado`, resume el registro, reparte lo abierto por persona (una fila de «Gabi y Javi» cuenta para los dos) y lista lo que está *Pendiente* o *En curso*.
- No cuenta las leyendas («Etiquetas: [Verificado]…»), los enlaces `[Pendiente](x.md)`, `docs/historico/` ni las líneas con `dam:ignore`. No cambia nada.

### Entregar un proyecto en un .zip limpio

```powershell
dam entregar . --simular                           # qué entra y qué se queda fuera, sin crear nada
dam entregar .                                     # crea CARPETA_AAAA-MM-DD.zip al lado de la carpeta
dam entregar . --nombre "Vidal_Gabriel_p3" --destino ~/Escritorio
```

- Deja fuera `.env`, claves privadas, `.git`, `.venv`, `node_modules`, `__pycache__`, `dist`, `build` y la basura del sistema (`Thumbs.db`, `.DS_Store`). En un repositorio, tampoco entra lo que ignora `.gitignore`. `.env.example` sí entra.
- Antes de crear el zip pasa `scan-secrets` sobre lo que va dentro: con un secreto seguro **no lo crea** y sale con **1**. Los avisos «posibles» se enseñan pero no bloquean.
- Nunca sobrescribe (añade ` (1)`). Dentro del zip todo va en una carpeta con el nombre del proyecto.

### Otras protecciones

- `--simular` no crea, mueve ni borra nada.
- `dam` nunca sobrescribe: si existe, añade ` (1)`.
- `dam sync` no sube `.env`, claves (`.pem`, `.key`, `.pfx`, `id_rsa`...) ni ficheros de más de 95 MB (el límite también frena las MV/OVA grandes).
- La carpeta `Documentacio` se ignora siempre.
- Prueba primero en `~/pruebas-tareas` y con `--simular`.
- `dam sync` no pisa nada ante la duda: si hay cambios en ambos lados, para y avisa.

## 7. Tu web (portfolio)

```powershell
dam test-links ~/portfolio                 # todos los .html de la carpeta
dam test-links index.html                  # una sola página
dam test-links ~/portfolio --sin-externos  # solo enlaces internos (sin internet)
dam test-links https://tu-web.com          # una página ya publicada
dam check-headers https://tu-web.com
dam check-headers https://tu-api.onrender.com --timeout 60   # Render gratis tarda en despertar
```

**`test-links`** revisa enlaces, imágenes, hojas CSS y scripts. Los internos se comprueban en disco, incluidas las anclas `#id` y las **mayúsculas** (en Windows `Foto.jpg` y `foto.jpg` son el mismo fichero, pero en GitHub Pages o Linux no, y el enlace se rompería). Los externos se comprueban con una petición HTTP. Sale con **1** si hay enlaces rotos; los avisos (webs como LinkedIn que no dejan comprobar a robots) no hacen fallar. `mailto:` y `tel:` se omiten.

**`check-headers`** mira `Content-Security-Policy`, `Strict-Transport-Security`, `X-Frame-Options` y `X-Content-Type-Options` (básicas: si falta alguna, sale con **1**) y `Referrer-Policy` y `Permissions-Policy` (recomendadas). También avisa de cabeceras que revelan tecnología (`Server`, `X-Powered-By`), CORS abierto a todos y cookies sin `Secure`, `HttpOnly` o `SameSite`. Nunca imprime el valor de una cookie.

## 8. Renombrar acciones

Edita `"nombre"` en `acciones.json`. Reglas: minúsculas, números y guiones; sin espacios, tildes ni mayúsculas; no repetido. El `"tipo"` no se toca.

```json
"nombre": "limpiar"
```

Luego: `uv run dam ejecutar limpiar`.

## 9. Si algo falla

| Mensaje | Solución |
|---|---|
| `La rama actual no tiene remoto` | En el almacén: `git push -u origin main` |
| `GitHub no te reconoce` | `gh auth login` o Git Credential Manager |
| `Sin conexión con GitHub` | Comprueba internet; `dam status` sigue viendo lo local |
| `No sé dónde está tu almacén` | Define `DAM_ALMACEN` o usa `--almacen` |
| `Conflicto real` | `dam sync --integrar` o resuélvelo a mano |
| `No existe la asignatura` | `dam status` te dice las que hay. Si querías poner un mensaje, usa `-m` |
| `Una ruta lleva unas comillas metidas` | Quita la `\` del final: `"C:\carpeta\"` → `"C:\carpeta"` (en Windows, `\"` se come las comillas; el TAB de PowerShell la añade) |
| `ModuleNotFoundError: No module named 'httpx'` al arrancar | Tras un `git pull` con dependencias nuevas: vuelve a pasar el instalador (o `uv tool install --editable . --force`) |
| `Faltan CENTRO_IA_URL o CENTRO_IA_KEY` | Ponlas en tu terminal o en un `.env` (copia `.env.example`). Las acciones sin IA no las necesitan |
| `No llego al servidor de IA` | Solo responde desde la red del centro. En casa: `--simular` o acciones sin IA |
| `No me fío del servidor` | Falta `CENTRO_IA_CA` con la ruta del certificado del instituto |
| `dam` solo imprime una línea en blanco (PowerShell) | El script del TAB antiguo se atascaba al completar rutas. Vuelve a lanzar `instalar.cmd` (genera el arreglado) y abre otra ventana |

## 10. Códigos de salida

| Código | Significado |
|---|---|
| `0` | Todo bien |
| `1` | Falló al ejecutar, `scan-secrets`, `test-links` o `check-headers` encontraron problemas, `entregar` encontró un secreto, o `doctor` encontró un fallo básico |
| `2` | Uso incorrecto del comando |
| `3` | `acciones.json` inválido |
| `4` | Sin IA: sin clave, sin red, sin certificado o el servidor no responde (las acciones sin IA siguen funcionando) |
