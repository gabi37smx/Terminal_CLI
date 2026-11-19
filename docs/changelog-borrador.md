# Cambios

## [Sin publicar]

### Añadido
- `crear-almacen`: almacén «solo en este equipo» para quien aún no tiene GitHub (15877cc)
- `instalar-hook --revisor`: el agente revisor mira cada commit con código (21cb69a)
- IA: si no hay ningún modelo configurado, propone elegir uno, sin red, en español (a2ddf44)
- `historial-pr.md`: todas las PR por versión, con sus issues (1e0dece, bd7a9a9, e7cdadb)

### Cambiado
- `ordenar` y `resumir-tema`: css en Lenguaje de marcas, `por_tipo` solo si la carpeta existe y PDF sin cabeceras (1b071f1)
- `ejecutar`: la ayuda muestra `por_tipo` solo si esa carpeta ya existe (ceade10)

### Corregido
- `nombrar-descargas`: no acepta nombres genéricos ni órdenes del PDF (923ad10)
- `--simular`: lo que anuncia es lo que pasa de verdad, verificado con pruebas (82a9190)
- Prueba de IA sin choque de red (a2ddf44)

### Seguridad
- `opencode.json`: el agente tampoco puede borrar con las órdenes de Windows (63b6790)
- Revisión del agente: `remove-item`, `git restore` y comparar contenido antes de actuar (f3ea143)

### Documentación
- `README` y `comandos.md`: restos de `dam` y `crear-almacen` (b091ab0)
- `prompts.md`: historial de las PR y el primer CAMBIAR del revisor (35f6f78)
- `prompts.md`: rellena los `[COMPLETAR]` que ya tienen datos reales (697ac44)

## [1.x] – PR 54 a 57

### Corregido
- Arreglos de ASIR: IA (#54), almacén local (#56) y ordenar (#57)

## [1.x] – PR 49 a 52

### Añadido
- Agente revisor y comprobación de `--simular` contra el comportamiento real (#49)

### Documentación
- Completar el agente revisor (#50), README para Windows y comandos (#51), historial de PR (#52)
