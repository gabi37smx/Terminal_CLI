# Demo de `dam` para clase (≈ 2 minutos)

Chuleta para enseñar las comprobaciones de seguridad sin tener que recordar nada.
`dam` está instalado globalmente: todos los comandos se lanzan **desde cualquier carpeta**.

## Qué digo (y qué no)

> «`dam` automatiza comprobaciones básicas de seguridad: que no se filtren claves en mis repos
> y que mis servidores envíen las cabeceras de protección. No es una auditoría completa.»

- **Sí comprueba:** claves y tokens en el código y en el historial de git (`scan-secrets`), cabeceras de
  seguridad HTTP (`check-headers`), enlaces rotos (`test-links`, que es calidad, no seguridad).
- **No comprueba:** inyecciones, login, permisos de la API, la base de datos… Nunca decir «impenetrable».

## Rutas y direcciones

| Qué | Dónde |
|---|---|
| Portfolio (local) | `C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\1 PROJECTE\mi-web\mi-web` |
| Portfolio (publicado) | `https://gabi37smx.github.io/mi-web/` |
| Backend (Render) | `https://portfolio-backend-m07q.onrender.com` |
| Repo del backend | `C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\1 PROJECTE\portfolio-backend` |

## Guion

**1. La herramienta y su ayuda**
```powershell
dam -h
dam check-headers -h
```

**2. Cero claves en el historial** (lo pide la rúbrica)
```powershell
dam scan-secrets --historial
dam scan-secrets "C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\1 PROJECTE\portfolio-backend" --historial
```

**3. El hook: no me puedo colar una clave en un commit**
```powershell
dam instalar-hook "C:\Users\HP\Desktop\DAM\PROGRAMACIÓ IA\1 PROJECTE\portfolio-backend"
```
Cada `git commit` ejecuta `dam scan-secrets --staged` y lo cancela si encuentra una clave.

**4. Cabeceras del backend: el antes y el después**
```powershell
dam check-headers https://portfolio-backend-m07q.onrender.com --timeout 60
```
Render gratis tarda en despertar: por eso `--timeout 60`.

**5. Enlaces de la web publicada**
```powershell
dam test-links https://gabi37smx.github.io/mi-web/
```
Los avisos de LinkedIn (código 999) no son enlaces rotos: LinkedIn bloquea las comprobaciones automáticas.

## Antes y después del backend

| | Antes (1-nov) | Después de añadir `helmet` |
|---|---|---|
| `check-headers` en Render | **0 de 6** | **6 de 6** (1-nov, desplegado) |
| En local (`http://localhost`) | — | 5 de 6 (HSTS solo cuenta con HTTPS) |

**Qué cambié en `portfolio-backend`:**
- `helmet` en `server.js` con una CSP propia: `script-src 'self'` (ningún script en línea),
  `frame-ancestors 'none'` (nadie puede meter el panel en un iframe), HSTS de 1 año, `nosniff`,
  `Referrer-Policy` y `Permissions-Policy` (cámara, micro y ubicación apagados; las passkeys siguen funcionando).
- Los dos `<script>` en línea de `admin.html` pasan a `public/admin-tema.js` y `public/admin.js`.
  Es lo que permite prohibir scripts en línea, la defensa principal contra XSS.
- Comprobado en local: el panel de admin carga con sus estilos, sus fuentes y la passkey, sin errores de CSP en la consola.
- Comprobado en Render tras desplegar: entro al admin con contraseña y funcionan el chatbot, las noticias IA y el juego del portfolio.

**Lo que puede preguntar el profe:**
- *¿Por qué `'unsafe-inline'` en `style-src`?* El `<style>` de `admin.html` va en línea. El riesgo de CSS en línea es
  mucho menor que el de JS, y `script-src` sí lo prohíbe (eso es lo que mira `dam`).
- *¿Por qué no sale CSP en GitHub Pages?* GitHub Pages no deja configurar cabeceras. Solo se podría con un `<meta http-equiv>`.
