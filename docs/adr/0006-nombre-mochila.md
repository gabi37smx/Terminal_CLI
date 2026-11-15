# ADR-0006: El comando se llama `mochila` (antes `dam`)

- Estado: aceptada
- Fecha: 2026-11-15
- Autor: Gabriel Vidal Badia

## Contexto

El comando se llamaba `dam` porque empezó siendo para mis apuntes de 1º de DAM. Desde la ADR-0003
y la ADR-0005 sirve para cualquier ciclo (SMX, DAM, DAW, ASIR): cada uno elige sus asignaturas y su
almacén se llama como su ciclo.

En la instalación cruzada del 15-nov, un compañero de **DAW** lo instaló siguiendo solo el README.
Le confundía escribir `dam` cuando él no es de DAM, y además su almacén se llama `DAW-almacen`:
`dam` y `DAW` se parecen demasiado. A uno de SMX o ASIR le pasaría lo mismo.

## Decisión

1. El comando pasa a llamarse **`mochila`**: es donde llevas los apuntes de clase a casa, que es lo
   que hace el almacén. Es corto, no es el nombre de ningún ciclo, se dice igual en castellano y en
   valenciano y no choca con ningún comando de Windows, Linux o macOS. Con `moc` + TAB ya sale.
2. Se queda el alias `tareas` (el nombre de la spec v0) y el paquete Python `tareas`. **No** se queda
   `dam`: si siguiera, la confusión seguiría.
3. Todo lo que llevaba el nombre pasa al nuevo: `~/.config/mochila`, `MOCHILA_ALMACEN`,
   `MOCHILA_IA`, `MOCHILA_IA_MODELO`, `MOCHILA_IA_CONFIG`, la marca `mochila:ignore`, el hook y el
   agente de OpenCode (`mochila-ia`).
4. Nadie que ya lo tenía instalado pierde nada:
   - Los instaladores copian `~/.config/dam` a `~/.config/mochila` (la vieja se queda como copia),
     pasan la variable `DAM_ALMACEN` de Windows a `MOCHILA_ALMACEN` y quitan del perfil o del
     `.bashrc` las líneas del TAB de `dam`.
   - Las variables `DAM_…` siguen valiendo si no está la `MOCHILA_…` (`config.entorno`).
   - `dam:ignore` sigue silenciando avisos, y `mochila instalar-hook` reconoce como suyo el hook de
     `dam` (lo sustituye sin `--forzar`).
5. El ciclo DAM no cambia: `DAM-almacen`, `--ciclo dam` y las asignaturas de DAM siguen igual.

## Consecuencias

- Hay que repetir el instalador para tener el comando nuevo (`git pull` y `instalar.cmd` o
  `bash instalar.sh`).
- El historial (`docs/prompts.md`, las ADR 0001-0005 y las entradas antiguas del CHANGELOG) sigue
  diciendo `dam`: es lo que se llamaba entonces y no se reescribe.
- Los hooks antiguos de `dam` en otros repos avisan «no encuentro el comando» y dejan hacer el
  commit (no bloquean) hasta que se repite `mochila instalar-hook` en ese repo.
