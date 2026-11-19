# Historial de pull requests

Cada cambio entró en `main` desde su propia rama, con una PR que GitHub Actions prueba en Linux, Windows
y macOS. Aquí está la lista entera, agrupada por la versión en la que salió. El detalle de lo que nota
quien usa `mochila` está en el [CHANGELOG](../CHANGELOG.md), y el porqué de cada paso, en la
[bitácora de prompts](prompts.md).

**53 PR fusionadas**, 7 issues y 3 versiones publicadas.

**Cómo leerlo:**
- **Rama:** `feature/` añade algo nuevo; `arreglo/` o `fix/` corrige un fallo; `docs/` toca documentación
  o la bitácora; `ci/` las pruebas automáticas; `release-X` prepara una versión.
- **El nombre del comando:** en la #1 era `gabriel`, después `dam` y, desde la #41, `mochila`. Los títulos
  se quedan con el nombre de entonces.
- **Los números que faltan** (#17, #18, #19, #20, #22, #46, #53) son issues: GitHub numera issues y
  PR con la misma cuenta.

Este fichero se genera con `uv run python scripts/historial_pr.py` (lo saca de GitHub con `gh`): no se
edita a mano.

## 1.0.0 · 11-nov-2026 (#1 a #16)

Las cuatro semanas del curso: las acciones con `acciones.json`, los comandos de seguridad, de proyectos y para organizar el PC, la capa de IA con su modo sin red, las pruebas en GitHub Actions (Linux, Windows y macOS) y la primera release.

| PR | Fusionada | Rama | Qué cambia | Cierra |
|---|---|---|---|---|
| [#1](https://github.com/gabi37smx/Terminal_CLI/pull/1) | 27-oct | `feature/cli-listar` | Añade la lógica real de ordenar, limpiar y convertir, y el comando pasa a llamarse gabriel |  |
| [#2](https://github.com/gabi37smx/Terminal_CLI/pull/2) | 1-nov | `feature/seguridad-y-web` | Comandos de seguridad y web: scan-secrets, test-links, check-headers e instalar-hook |  |
| [#3](https://github.com/gabi37smx/Terminal_CLI/pull/3) | 6-nov | `feature/doctor-entregar-pendientes` | Añade dam doctor, dam pendientes y dam entregar; arregla el TAB de PowerShell |  |
| [#4](https://github.com/gabi37smx/Terminal_CLI/pull/4) | 10-nov | `feature/inventario` | Añade dam inventario: qué hay en una carpeta antes de organizarla |  |
| [#5](https://github.com/gabi37smx/Terminal_CLI/pull/5) | 10-nov | `feature/duplicados` | Añade dam duplicados: ficheros repetidos y carpetas que son copia de otra |  |
| [#6](https://github.com/gabi37smx/Terminal_CLI/pull/6) | 11-nov | `fix/ordenar-sistemas` | ordenar: palabras de arquitectura de ordenadores para sistemas |  |
| [#7](https://github.com/gabi37smx/Terminal_CLI/pull/7) | 11-nov | `feature/readme` | Añade dam readme: tabla «Qué hay dentro» en el README de cada carpeta |  |
| [#8](https://github.com/gabi37smx/Terminal_CLI/pull/8) | 11-nov | `feature/ayuda-tabla-y-ordenar-almacen` | Ayuda en tabla y ordenar mete los apuntes en el almacén |  |
| [#9](https://github.com/gabi37smx/Terminal_CLI/pull/9) | 11-nov | `feature/ordenar-por-tipo` | ordenar: plan B a ~/Datos/POR-TIPO y nunca mueve ficheros del sistema |  |
| [#10](https://github.com/gabi37smx/Terminal_CLI/pull/10) | 11-nov | `docs/pendientes-11-nov` | Marca como hechos el README del almacén, el zip grande y el hook |  |
| [#11](https://github.com/gabi37smx/Terminal_CLI/pull/11) | 11-nov | `ci/github-actions` | GitHub Actions con los tests (Linux y Windows) y dos arreglos para Linux |  |
| [#12](https://github.com/gabi37smx/Terminal_CLI/pull/12) | 11-nov | `arreglo/instalar-en-clase` | Instaladores: encuentran el almacén donde esté y avisan si la config es vieja |  |
| [#13](https://github.com/gabi37smx/Terminal_CLI/pull/13) | 11-nov | `docs/prueba-acciones-11nov` | punto_actual: prueba de verdad de ordenar, limpiar-temporales y convertir-webp |  |
| [#14](https://github.com/gabi37smx/Terminal_CLI/pull/14) | 11-nov | `arreglo/almacen-windows` | instalar.ps1: busca el almacén donde esté (como instalar.sh) |  |
| [#15](https://github.com/gabi37smx/Terminal_CLI/pull/15) | 11-nov | `capa-ia` | Semana 3: capa IA (ProveedorIA), 3 acciones con IA y modo sin red |  |
| [#16](https://github.com/gabi37smx/Terminal_CLI/pull/16) | 11-nov | `release-1.0` | Release 1.0.0: CHANGELOG, Actions en 3 sistemas, revisar.sh y desinstalación |  |

## 1.0.1 · 11-nov-2026 (#21 a #23)

Los arreglos del ensayo de instalación en un Ubuntu recién instalado, siguiendo solo el README (issues #17 a #22).

| PR | Fusionada | Rama | Qué cambia | Cierra |
|---|---|---|---|---|
| [#21](https://github.com/gabi37smx/Terminal_CLI/pull/21) | 11-nov | `arreglo/instalar-sin-clonar` | 1.0.1: arreglos del ensayo de instalación en Ubuntu (#17 #18 #19 #20) | [#17](https://github.com/gabi37smx/Terminal_CLI/issues/17), [#18](https://github.com/gabi37smx/Terminal_CLI/issues/18), [#19](https://github.com/gabi37smx/Terminal_CLI/issues/19), [#20](https://github.com/gabi37smx/Terminal_CLI/issues/20) |
| [#23](https://github.com/gabi37smx/Terminal_CLI/pull/23) | 11-nov | `arreglo/instalador-almacen` | Instaladores: usuario de GitHub y token al clonar DAM-almacen (#22) | [#22](https://github.com/gabi37smx/Terminal_CLI/issues/22) |

## 1.1.0 · 17-nov-2026 (#24 a #48)

`configurar` y `crear-almacen` para cualquier ciclo, la IA gratis con OpenCode, `ordenar` por unidades, lo que salió probando en clase y con otra persona, y el cambio de nombre a `mochila`.

| PR | Fusionada | Rama | Qué cambia | Cierra |
|---|---|---|---|---|
| [#24](https://github.com/gabi37smx/Terminal_CLI/pull/24) | 11-nov | `docs/ensayo-portatil` | prompts: resultado del ensayo en el portátil con la 1.0.1 |  |
| [#25](https://github.com/gabi37smx/Terminal_CLI/pull/25) | 11-nov | `feature/dam-configurar` | dam configurar: tu ciclo y tus asignaturas, como adduser |  |
| [#26](https://github.com/gabi37smx/Terminal_CLI/pull/26) | 12-nov | `arreglo/configurar-smx` | configurar: pregunta de asignaturas nuevas más clara y vocabulario de SMX |  |
| [#27](https://github.com/gabi37smx/Terminal_CLI/pull/27) | 12-nov | `arreglo/configurar-palabras-al-dia` | configurar trae las palabras clave nuevas; ordenar no ofrece sync sin git |  |
| [#28](https://github.com/gabi37smx/Terminal_CLI/pull/28) | 12-nov | `feature/ejecutar-un-fichero` | ejecutar acepta un solo fichero; ejemplos en dam acciones -h; prompts y punto actual |  |
| [#29](https://github.com/gabi37smx/Terminal_CLI/pull/29) | 12-nov | `docs/configurar-primera-persona` | docs: dam configurar en primera persona y ADR-0003 |  |
| [#30](https://github.com/gabi37smx/Terminal_CLI/pull/30) | 12-nov | `feature/ia-opencode-gratis` | dam configurar-ia: la IA de dam con los modelos gratis de OpenCode |  |
| [#31](https://github.com/gabi37smx/Terminal_CLI/pull/31) | 12-nov | `feature/ordenar-dentro-y-unidad` | ordenar lee los .odt y .docx por dentro y mete cada fichero en su unidad |  |
| [#32](https://github.com/gabi37smx/Terminal_CLI/pull/32) | 12-nov | `arreglo/ia-lista-al-dia` | configurar-ia pide la lista de modelos al día; clasificar acepta .ods |  |
| [#33](https://github.com/gabi37smx/Terminal_CLI/pull/33) | 12-nov | `docs/prueba-ia-smx` | Prueba con apuntes de SMX: clasificar ve el nombre del fichero y más palabras de seguridad |  |
| [#34](https://github.com/gabi37smx/Terminal_CLI/pull/34) | 12-nov | `arreglo/instalar-linux-nuevo` | instalar.sh: dam se encuentra en un Linux nuevo; correo con @; dam --version |  |
| [#35](https://github.com/gabi37smx/Terminal_CLI/pull/35) | 12-nov | `docs/prueba-linux-clase` | Prueba de instalación desde cero en un Linux de clase, y dos detalles |  |
| [#36](https://github.com/gabi37smx/Terminal_CLI/pull/36) | 13-nov | `docs/repaso-textos` | Repaso para la entrega: huecos de casa y errores amables |  |
| [#37](https://github.com/gabi37smx/Terminal_CLI/pull/37) | 13-nov | `feature/almacen-por-ciclo` | dam crear-almacen: cada ciclo con su almacén, y crearlo sin saber git |  |
| [#38](https://github.com/gabi37smx/Terminal_CLI/pull/38) | 13-nov | `arreglo/fallos-pc-clase` | Fallos vistos en clase el 13-nov y pruebas como pide la Sesión 4 |  |
| [#39](https://github.com/gabi37smx/Terminal_CLI/pull/39) | 13-nov | `arreglo/sesiones-1-2` | Repaso de las sesiones 1 y 2, servidor del centro desde OpenCode y doctor en ~ |  |
| [#40](https://github.com/gabi37smx/Terminal_CLI/pull/40) | 15-nov | `arreglo/tab-windows-limpio` | instalar.ps1: el TAB funciona en un Windows recién instalado |  |
| [#41](https://github.com/gabi37smx/Terminal_CLI/pull/41) | 15-nov | `feature/nombre-mochila` | El comando pasa a llamarse mochila (antes dam) |  |
| [#42](https://github.com/gabi37smx/Terminal_CLI/pull/42) | 15-nov | `feature/ordenar-unidades` | ordenar: crea la carpeta de la unidad, reconoce siglas y explica sus errores |  |
| [#43](https://github.com/gabi37smx/Terminal_CLI/pull/43) | 15-nov | `feature/resumenes-en-su-sitio` | resumir-tema: resumen a la medida del tema y al lado del apunte |  |
| [#44](https://github.com/gabi37smx/Terminal_CLI/pull/44) | 15-nov | `arreglo/preguntas-por-defecto` | Preguntas: Sí por defecto donde Enter debía seguir adelante |  |
| [#45](https://github.com/gabi37smx/Terminal_CLI/pull/45) | 15-nov | `arreglo/avisos-pypdf` | Lectura de PDF: sin los avisos de pypdf que llenaban la terminal |  |
| [#47](https://github.com/gabi37smx/Terminal_CLI/pull/47) | 15-nov | `feature/ayuda-corta-y-larga` | Ayuda corta y guía con ejemplos, y avisos del instalador en LTSC | [#46](https://github.com/gabi37smx/Terminal_CLI/issues/46) |
| [#48](https://github.com/gabi37smx/Terminal_CLI/pull/48) | 17-nov | `release-1.1` | Release 1.1.0: versión, CHANGELOG, README y nota del primer commit |  |

## Sin publicar (#49 a #60)

Lo que saldrá en la próxima versión: las fusionadas ya están en `main`; las abiertas, aún no.

| PR | Fusionada | Rama | Qué cambia | Cierra |
|---|---|---|---|---|
| [#49](https://github.com/gabi37smx/Terminal_CLI/pull/49) | 17-nov | `feature/revisor-y-simular-real` | Ideas del vídeo de la Sesión 2: simular de verdad, borrar en Windows y el revisor en cada commit |  |
| [#50](https://github.com/gabi37smx/Terminal_CLI/pull/50) | 18-nov | `docs/completar-revisor` | prompts.md: rellena los [COMPLETAR] que ya tienen datos reales |  |
| [#51](https://github.com/gabi37smx/Terminal_CLI/pull/51) | 18-nov | `docs/readme-windows-y-comandos` | README y comandos.md: restos de dam y crear-almacen |  |
| [#52](https://github.com/gabi37smx/Terminal_CLI/pull/52) | 18-nov | `docs/historial-pr` | docs/historial-pr.md: todas las PR por versión, con sus issues |  |
| [#54](https://github.com/gabi37smx/Terminal_CLI/pull/54) | 19-nov | `arreglo/asir-ia` | IA: elige modelo si no hay ninguno, sin red en español y prueba sin choque (#53) |  |
| [#55](https://github.com/gabi37smx/Terminal_CLI/pull/55) | 19-nov | `arreglo/asir-ordenar` | ordenar y resumir-tema: css en Lenguaje de marcas, por_tipo solo si existe y PDF sin cabeceras (#53) |  |
| [#56](https://github.com/gabi37smx/Terminal_CLI/pull/56) | 19-nov | `arreglo/asir-almacen-local` | crear-almacen: el almacén «solo en este equipo» para quien aún no tiene GitHub (#53) |  |
| [#57](https://github.com/gabi37smx/Terminal_CLI/pull/57) | 19-nov | `arreglo/asir-ordenar` | Lleva a main lo de #55 y #56 (se fusionaron en sus ramas de debajo) | [#53](https://github.com/gabi37smx/Terminal_CLI/issues/53) |
| [#58](https://github.com/gabi37smx/Terminal_CLI/pull/58) | 19-nov | `docs/clase-19nov` | Clase 19-nov: pruebas con el modelo del centro y arreglo de nombrar-descargas |  |
| [#59](https://github.com/gabi37smx/Terminal_CLI/pull/59) | 19-nov | `docs/historial-pr-58` | historial-pr.md: la PR 58 |  |
| [#60](https://github.com/gabi37smx/Terminal_CLI/pull/60) | 19-nov | `docs/readme-empieza-aqui` | README: «Empieza aquí» para quien lo prueba por primera vez |  |

## Issues

Lo que encontré instalando en un ordenador limpio y lo que encontró otra persona al instalarlo.
Cada uno se cerró desde la PR que lo arreglaba («Closes #N»).

| Issue | Abierto | Qué pasaba | Lo cerró |
|---|---|---|---|
| [#17](https://github.com/gabi37smx/Terminal_CLI/issues/17) | 11-nov | README: en un Ubuntu recién instalado faltan git, curl y uv | [#21](https://github.com/gabi37smx/Terminal_CLI/pull/21) |
| [#18](https://github.com/gabi37smx/Terminal_CLI/issues/18) | 11-nov | Instalado con la orden única, no sé cómo crear acciones.json | [#21](https://github.com/gabi37smx/Terminal_CLI/pull/21) |
| [#19](https://github.com/gabi37smx/Terminal_CLI/issues/19) | 11-nov | comprobar-ia sin clonar: «mira .env.example», pero ese fichero no está | [#21](https://github.com/gabi37smx/Terminal_CLI/pull/21) |
| [#20](https://github.com/gabi37smx/Terminal_CLI/issues/20) | 11-nov | Detalles de la ayuda para quien instala sin clonar o usa el nombre tareas | [#21](https://github.com/gabi37smx/Terminal_CLI/pull/21) |
| [#22](https://github.com/gabi37smx/Terminal_CLI/issues/22) | 11-nov | instalar.sh: no queda claro qué usuario pide para clonar DAM-almacen ni qué poner en Username/Password | [#23](https://github.com/gabi37smx/Terminal_CLI/pull/23) |
| [#46](https://github.com/gabi37smx/Terminal_CLI/issues/46) | 15-nov | Instalación cruzada (1º DAW, Windows 11 LTSC y VM Windows): TAB, ordenar y la ayuda confunden | [#47](https://github.com/gabi37smx/Terminal_CLI/pull/47) |
| [#53](https://github.com/gabi37smx/Terminal_CLI/issues/53) | 19-nov | Instalación cruzada (1º ASIR, VM Windows 11 limpia): almacén sin GitHub, IA sin elegir y ordenar fuera de DAM | [#57](https://github.com/gabi37smx/Terminal_CLI/pull/57) |
