# Cómo trabajar a partir de ahora (clase y casa)

> **Chuleta rápida:** trabaja dentro de `DAM-almacen` y usa `mochila sync` al empezar y al terminar.
> No hace falta clonar cada día ni llevar un USB: GitHub es el puente.

## 1. Los dos repositorios

| Repo | Qué es | Dónde está en casa | Cómo se actualiza |
|---|---|---|---|
| `Terminal_CLI` | El código de la CLI `mochila` | `C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\PROJECTE TERMINAL CLI\Terminal_CLI` | `git pull` / commit / `git push` (lo haces tú) |
| `DAM-almacen` | Tus apuntes y prácticas | `C:\Users\HP\DAM-almacen` | `mochila status` y `mochila sync` |

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

# 3. Decirle a mochila dónde está el almacén (permanente, nuevas terminales)
setx MOCHILA_ALMACEN "$HOME\DAM-almacen"
```

Cierra y abre la terminal. Comprueba:

```powershell
mochila --help
mochila validar
mochila status
```

En Linux/macOS:

```bash
git clone https://github.com/gabi37smx/Terminal_CLI.git
cd Terminal_CLI && uv sync && uv tool install --editable .
git clone https://github.com/gabi37smx/DAM-almacen.git "$HOME/DAM-almacen"
export MOCHILA_ALMACEN="$HOME/DAM-almacen"   # añádelo a ~/.bashrc o ~/.zshrc
mochila status
```

Si no defines `MOCHILA_ALMACEN`, `mochila` usará `almacen.ruta` de `acciones.json` (ahora `~/DAM-almacen`); también puedes pasar `--almacen RUTA`.

Si el PC ya tiene el almacén clonado, **no lo clones otra vez**: salta a la rutina diaria.

GitHub te pedirá login porque el repo es privado (`gh auth login` o Git Credential Manager).
No guardes tokens en ficheros del repo.

## 3. Rutina de cada día

### Al empezar (clase o casa)

```powershell
mochila status
mochila sync
```

- `mochila status` no toca nada: te dice qué has cambiado tú y qué hay nuevo en GitHub.
- `mochila sync` baja lo de GitHub si solo hay cambios remotos. Si hay cambios en los dos lados, se para y no toca nada.

### Mientras trabajas

- Edita y crea ficheros **dentro de `DAM-almacen`**.
- Para las acciones: `mochila ejecutar ...` (mejor `--simular` primero).
- No hagas `git commit` a mano en el almacén: lo hace `mochila sync`.

### Al terminar (clase o casa)

```powershell
mochila status
mochila sync -m "lo que he hecho"
```

Con `-m` el texto es el mensaje y no se confunde con una asignatura (no uses `""` vacío: PowerShell lo elimina). Eso hace `add` + `commit` + `push` de tus cambios. Si solo había cambios en GitHub, hace `pull`.

### Antes de subir el código (`Terminal_CLI`)

```powershell
git add ...
mochila scan-secrets --staged    # ¿he preparado alguna clave sin querer?
git commit -m "..."
```

### La regla de oro

> **Sync al terminar donde trabajas. Sync al empezar en el otro PC.**

- Si trabajas en casa y luego vas a clase: `mochila sync` en casa antes de salir; al llegar a clase, `mochila status` y `mochila sync` para bajar.
- Si trabajas en clase y luego vas a casa: `mochila sync` en clase antes de irte; al llegar a casa, `mochila status` y `mochila sync` para bajar.

## 4. Comandos que vas a usar

| Comando | Cuándo | Qué hace |
|---|---|---|
| `mochila status` | al empezar/terminar | Solo mira; funciona sin internet (muestra lo último que sabe) |
| `mochila sync` | al empezar/terminar | Baja o sube; necesita internet; si hay cambios en ambos lados, para |
| `mochila sync "mensaje"` | **mal** | Interpreta `"mensaje"` como asignatura. Para todo el almacén: `mochila sync -m "mensaje"` |
| `mochila sync programacion "tema 3"` | una asignatura | Sube solo `asignaturas/programacion/` |
| `mochila sync -m "subida desde casa"` | todo el almacén | Mensaje propio sin filtrar asignatura |
| `mochila sync --simular` | antes de subir | Enseña qué haría; no toca nada, pero necesita internet |
| `mochila sync --integrar` | cambios en ambos lados | Guarda lo tuyo, hace `pull --rebase` y sube; si hay conflicto, lo deshace |
| `mochila status --almacen RUTA` | ruta alternativa | Si no está `MOCHILA_ALMACEN` |
| `mochila ejecutar NOMBRE --simular` | acciones | Prueba sin tocar; luego sin `--simular` |

> **Nota:** el filtro por asignatura limita lo que **subes**, pero `mochila sync` mira todo el repo para ver si hay cambios en GitHub. Si hay cambios en ambos lados (aunque sean de otra asignatura), usa `mochila sync --integrar`.

## 5. Si hay cambios en los dos lados

`mochila status` te avisa en rojo. `mochila sync` **no hace nada** y sale con error 1. Tienes dos opciones:

1. **Los cambios son en ficheros distintos:** `mochila sync --integrar`. Junta lo tuyo con lo de GitHub y sube.
2. **Hay conflicto real:** `mochila sync --integrar` lo detecta, deshace el rebase y te avisa. Tus cambios locales se quedan; resuélvelo a mano o pide ayuda.

Antes de integrar, si dudas, haz una copia de la carpeta o mira `mochila status`.

## 6. Sin internet

- `mochila status` **sí funciona**: muestra lo local y lo último que sabe de GitHub.
- `mochila sync` **necesita internet** (hace `fetch`). Si no hay, trabaja en local y sincroniza al llegar a casa/clase.
- `mochila sync --simular` también necesita internet, porque consulta GitHub.

## 7. Seguridad

- `mochila sync` bloquea `.env`, `.env.local`, `clave.env`, `atlas-credentials.env`, etc. (deja pasar `.env.example`) y las claves `.pem`, `.key`, `.pfx`, `id_rsa`...
- `mochila sync` también bloquea ficheros de más de 95 MB.
- El `.gitignore` del almacén ignora MV/OVA, `node_modules`, `.venv`, credenciales, etc.
- La carpeta `Documentacio` no se sube nunca.
- No metas claves en apuntes ni en `acciones.json`.
- `mochila ejecutar` con `--si` se salta la confirmación: úsalo solo si estás seguro.

## 8. Chuleta rápida

```powershell
# Empezar
mochila status
mochila sync

# Terminar
mochila status
mochila sync -m "lo que he hecho"

# Solo una asignatura
mochila sync programacion "tema 3"

# Mensaje para todo el almacén
mochila sync -m "subida desde casa"

# Cambios en ambos lados
mochila sync --integrar

# Ver sin tocar
mochila sync --simular

# Ruta alternativa
mochila status --almacen "$HOME\DAM-almacen"
```

## 9. Ayuda dentro del programa

`mochila` a secas enseña el manual completo; `mochila sync -h` explica un comando con sus ejemplos.

## 10. Ver también

- `docs/comandos.md`: referencia de todos los comandos y acciones.
- `README.md`: qué es `mochila` y cómo está montado.
- `punto_actual.md`: estado actual y pendientes.
