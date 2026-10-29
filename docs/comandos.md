# Guía rápida de `dam`

> Ejecuta siempre desde:
> `C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\PROJECTE TERMINAL CLI\Terminal_CLI`
>
> Si ya instalaste el comando, usa `dam` en vez de `uv run dam`.

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
| `dam sync [ASIGNATURA] [MENSAJE] [--integrar] [--simular]` | Sincroniza con GitHub | `uv run dam sync programacion "tema 3"` |

## 2. Tus 3 acciones

| Nombre | Tipo | Qué hace |
|---|---|---|
| `ordenar` | ordenar | Reparte apuntes por asignatura |
| `limpiar-temporales` | borrar | Borra temporales de más de 30 días |
| `convertir-webp` | convertir | JPEG/PNG a WebP sin tocar el original |

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

# Mensaje propio para todo el almacén
uv run dam sync "" "subida desde casa"

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

- `--simular` no crea, mueve ni borra nada.
- `dam` nunca sobrescribe: si existe, añade ` (1)`.
- `dam sync` no sube `.env`, `*.pem`, `*.key`, MV/OVA ni ficheros de más de 95 MB.
- La carpeta `Documentacio` se ignora siempre.
- Prueba primero en `~/pruebas-tareas` y con `--simular`.
- `dam sync` no pisa nada ante la duda: si hay cambios en ambos lados, para y avisa.

## 7. Renombrar acciones

Edita `"nombre"` en `acciones.json`. Reglas: minúsculas, números y guiones; sin espacios, tildes ni mayúsculas; no repetido. El `"tipo"` no se toca.

```json
"nombre": "limpiar"
```

Luego: `uv run dam ejecutar limpiar`.

## 8. Si algo falla

| Mensaje | Solución |
|---|---|
| `La rama actual no tiene remoto` | En el almacén: `git push -u origin main` |
| `GitHub no te reconoce` | `gh auth login` o Git Credential Manager |
| `Sin conexión con GitHub` | Comprueba internet; `dam status` sigue viendo lo local |
| `No sé dónde está tu almacén` | Define `DAM_ALMACEN` o usa `--almacen` |
| `Conflicto real` | `dam sync --integrar` o resuélvelo a mano |
| `No existe la asignatura` | `dam status` te dice las que hay |

## 9. Códigos de salida

| Código | Significado |
|---|---|
| `0` | Todo bien |
| `1` | Falló al ejecutar |
| `2` | Uso incorrecto del comando |
| `3` | `acciones.json` inválido |
