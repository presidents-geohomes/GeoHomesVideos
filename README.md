# Geo Homes LLC - Videos

Videos cortos para Instagram y TikTok, organizados por mes y por video.

## Videos automáticos con Higgsfield

1. Se sube una escena a `escenas/pendientes/NOMBRE.json`:
   ```json
   {
     "carpeta": "2026-09/2026-09-29_005_tema",
     "archivo": "005_ES.mp4",
     "prompt": "Descripción de la escena, diálogos entre comillas, estilo, cámara..."
   }
   ```
   Opcionales: `modelo` (ruta del modelo en Higgsfield; por defecto `kling-video/v3.0/std/text-to-video`),
   `duracion` (segundos, por defecto 10) y `parametros` (campos extra propios del modelo).
2. GitHub Actions (`.github/workflows/generar-video.yml`) pide el video a Higgsfield en vertical 9:16,
   lo deja en 1080x1920 y lo guarda en la carpeta indicada.
3. La escena pasa a `escenas/hechas/` (o a `escenas/errores/` con el motivo).

También se puede lanzar a mano: pestaña **Actions → Generar video con Higgsfield → Run workflow**.

Requisito: secreto `HF_API_KEY` (la clave completa de Higgsfield) en Settings → Secrets and variables → Actions.
