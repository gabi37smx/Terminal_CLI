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
| `dam listar [CARPETA]` | Lista ficheros en una tabla | `uv run dam listar "C:\Users\HP\Desktop\DAM\SISTEMES"` |
| `dam validar` | Comprueba `acciones.json` | `uv run dam validar` |
| `dam acciones` | Lista tus acciones | `uv run dam acciones` |
| `dam ejecutar NOMBRE [CARPETA] [--simular] [--si]` | Ejecuta una acción | `uv run dam ejecutar ordenar --simular` |
| `dam status [ASIGNATURA]` | Qué hay pendiente (no toca nada) | `uv run dam status programacion` |
| `dam scan-secrets [RUTA] [--staged] [--historial] [--alta]` | Busca claves y contraseñas expuestas | `uv run dam scan-secrets --staged` |
| `dam instalar-hook [REPO] [--quitar] [--forzar]` | Revisa claves en cada `git commit` | `uv run dam instalar-hook` |
| `dam test-links [FUENTE] [--sin-externos] [--timeout S]` | Busca enlaces rotos en tu web | `uv run dam test-links ~/portfolio` |
| `dam check-headers URL [--timeout S]` | Cabeceras de seguridad de tu web o API | `uv run dam check-headers https://tu-web.com` |
| `dam sync [ASIGNATURA] [-m MENSAJE] [--integrar] [--simular]` | Sincroniza con GitHub | `uv run dam sync programacion -m "tema 3"` |

## 2. Tus 6 acciones

| Nombre | Tipo | Qué hace |
|---|---|---|
| `ordenar` | ordenar | Reparte apuntes por asignatura |
| `limpiar-temporales` | borrar | Borra temporales de más de 30 días |
| `convertir-webp` | convertir | JPEG/PNG a WebP sin tocar el original |
| `renombrar-capturas` | renombrar | Renombra capturas con fecha y número |
| `copiar-entregas` | copiar | Copia entregas y prácticas a una carpeta de seguridad |
| `comprimir-zips` | mover | Mueve los `.zip` a la subcarpeta `comprimidos` |

Sin `CARPETA`, usan el `origen` de `acciones.json` (ahora `~/pruebas-tareas/prueba-final`).

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
| `--simular` | `ejecutar`, `sync` | Enseña qué haría sin tocar nada |
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

## 10. Códigos de salida

| Código | Significado |
|---|---|
| `0` | Todo bien |
| `1` | Falló al ejecutar, o `scan-secrets`, `test-links` o `check-headers` encontraron problemas |
| `2` | Uso incorrecto del comando |
| `3` | `acciones.json` inválido |
