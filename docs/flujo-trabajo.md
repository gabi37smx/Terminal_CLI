# Cómo trabajar a partir de ahora (clase y casa)

> **Chuleta rápida:** trabaja dentro de `DAM-almacen` y usa `dam sync` al empezar y al terminar.
> No hace falta clonar cada día ni llevar un USB: GitHub es el puente.

## 1. Los dos repositorios

| Repo | Qué es | Dónde está en casa | Cómo se actualiza |
|---|---|---|---|
| `Terminal_CLI` | El código de la CLI `dam` | `C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\PROJECTE TERMINAL CLI\Terminal_CLI` | `git pull` / commit / `git push` (lo haces tú) |
| `DAM-almacen` | Tus apuntes y prácticas | `C:\Users\HP\DAM-almacen` | `dam status` y `dam sync` |

- **No trabajes en `Desktop\DAM`**: eso fue el origen. A partir de ahora editas en `DAM-almacen`.
- **No clones `DAM-almacen` dentro de `Terminal_CLI`**: son repos separados.
- El repo del almacén es **privado**.
- Si cambias el código de la CLI, eso va al repo `Terminal_CLI`, no al almacén.

## 2. Primera vez en el PC de clase

Necesitas Git y `uv`. Si no están:

```powershell
winget install --id Git.Git -e
winget install --id=astral-sh.uv -e
```

Luego:

```powershell
# 1. Traer la CLI
git clone https://github.com/gabi37smx/Terminal_CLI.git
cd Terminal_CLI
uv sync
uv tool install --editable .

# 2. Traer los apuntes (fuera de Terminal_CLI)
git clone https://github.com/gabi37smx/DAM-almacen.git "$HOME\DAM-almacen"

# 3. Decirle a dam dónde está el almacén (permanente, nuevas terminales)
setx DAM_ALMACEN "$HOME\DAM-almacen"
```

Cierra y abre la terminal. Comprueba:

```powershell
dam --help
dam validar
dam status
```

En Linux/macOS:

```bash
git clone https://github.com/gabi37smx/Terminal_CLI.git
cd Terminal_CLI && uv sync && uv tool install --editable .
git clone https://github.com/gabi37smx/DAM-almacen.git "$HOME/DAM-almacen"
export DAM_ALMACEN="$HOME/DAM-almacen"   # añádelo a ~/.bashrc o ~/.zshrc
dam status
```

Si no defines `DAM_ALMACEN`, `dam` usará `almacen.ruta` de `acciones.json` (ahora `~/DAM-almacen`); también puedes pasar `--almacen RUTA`.

Si el PC ya tiene el almacén clonado, **no lo clones otra vez**: salta a la rutina diaria.

GitHub te pedirá login porque el repo es privado (`gh auth login` o Git Credential Manager).
No guardes tokens en ficheros del repo.

## 3. Rutina de cada día

### Al empezar (clase o casa)

```powershell
dam status
dam sync
```

- `dam status` no toca nada: te dice qué has cambiado tú y qué hay nuevo en GitHub.
- `dam sync` baja lo de GitHub si solo hay cambios remotos. Si hay cambios en los dos lados, se para y no toca nada.

### Mientras trabajas

- Edita y crea ficheros **dentro de `DAM-almacen`**.
- Para las acciones: `dam ejecutar ...` (mejor `--simular` primero).
- No hagas `git commit` a mano en el almacén: lo hace `dam sync`.

### Al terminar (clase o casa)

```powershell
dam status
dam sync "" "lo que he hecho"
```

El `""` vacío es para que `dam` entienda que el siguiente argumento es el mensaje y no una asignatura. Eso hace `add` + `commit` + `push` de tus cambios. Si solo había cambios en GitHub, hace `pull`.

### La regla de oro

> **Sync al terminar donde trabajas. Sync al empezar en el otro PC.**

- Si trabajas en casa y luego vas a clase: `dam sync` en casa antes de salir; al llegar a clase, `dam status` y `dam sync` para bajar.
- Si trabajas en clase y luego vas a casa: `dam sync` en clase antes de irte; al llegar a casa, `dam status` y `dam sync` para bajar.

## 4. Comandos que vas a usar

| Comando | Cuándo | Qué hace |
|---|---|---|
| `dam status` | al empezar/terminar | Solo mira; funciona sin internet (muestra lo último que sabe) |
| `dam sync` | al empezar/terminar | Baja o sube; necesita internet; si hay cambios en ambos lados, para |
| `dam sync "mensaje"` | **mal** | Interpreta `"mensaje"` como asignatura. Para todo el almacén: `dam sync "" "mensaje"` |
| `dam sync programacion "tema 3"` | una asignatura | Sube solo `asignaturas/programacion/` |
| `dam sync "" "subida desde casa"` | todo el almacén | Mensaje propio sin filtrar asignatura |
| `dam sync --simular` | antes de subir | Enseña qué haría; no toca nada, pero necesita internet |
| `dam sync --integrar` | cambios en ambos lados | Guarda lo tuyo, hace `pull --rebase` y sube; si hay conflicto, lo deshace |
| `dam status --almacen RUTA` | ruta alternativa | Si no está `DAM_ALMACEN` |
| `dam ejecutar NOMBRE --simular` | acciones | Prueba sin tocar; luego sin `--simular` |

> **Nota:** el filtro por asignatura limita lo que **subes**, pero `dam sync` mira todo el repo para ver si hay cambios en GitHub. Si hay cambios en ambos lados (aunque sean de otra asignatura), usa `dam sync --integrar`.

## 5. Si hay cambios en los dos lados

`dam status` te avisa en rojo. `dam sync` **no hace nada** y sale con error 1. Tienes dos opciones:

1. **Los cambios son en ficheros distintos:** `dam sync --integrar`. Junta lo tuyo con lo de GitHub y sube.
2. **Hay conflicto real:** `dam sync --integrar` lo detecta, deshace el rebase y te avisa. Tus cambios locales se quedan; resuélvelo a mano o pide ayuda.

Antes de integrar, si dudas, haz una copia de la carpeta o mira `dam status`.

## 6. Sin internet

- `dam status` **sí funciona**: muestra lo local y lo último que sabe de GitHub.
- `dam sync` **necesita internet** (hace `fetch`). Si no hay, trabaja en local y sincroniza al llegar a casa/clase.
- `dam sync --simular` también necesita internet, porque consulta GitHub.

## 7. Seguridad

- `dam sync` bloquea `.env`, `.env.local`, `clave.env`, `atlas-credentials.env`, etc.; deja pasar `.env.example`.
- `dam sync` también bloquea ficheros de más de 95 MB.
- El `.gitignore` del almacén ignora MV/OVA, `node_modules`, `.venv`, credenciales, etc.
- La carpeta `Documentacio` no se sube nunca.
- No metas claves en apuntes ni en `acciones.json`.
- `dam ejecutar` con `--si` se salta la confirmación: úsalo solo si estás seguro.

## 8. Chuleta rápida

```powershell
# Empezar
dam status
dam sync

# Terminar
dam status
dam sync "" "lo que he hecho"

# Solo una asignatura
dam sync programacion "tema 3"

# Mensaje para todo el almacén
dam sync "" "subida desde casa"

# Cambios en ambos lados
dam sync --integrar

# Ver sin tocar
dam sync --simular

# Ruta alternativa
dam status --almacen "$HOME\DAM-almacen"
```

## 9. Ver también

- `docs/comandos.md`: referencia de todos los comandos y acciones.
- `README.md`: qué es `dam` y cómo está montado.
- `punto_actual.md`: estado actual y pendientes.
