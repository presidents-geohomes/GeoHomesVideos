# Geo Homes LLC - Videos

Videos cortos para Instagram y TikTok, organizados por mes y por video.

## Videos automáticos con Veo (Gemini)

1. Se sube una escena a `escenas/pendientes/NOMBRE.json`:
   ```json
   {
     "carpeta": "2026-09/2026-09-29_005_tema",
     "archivo": "005_ES.mp4",
     "prompt": "Descripción de la escena, diálogos entre comillas, estilo, cámara..."
   }
   ```
   Opcionales: `modelo`, `duracion` (4, 6 u 8), `resolucion` (720p o 1080p), `prompt_negativo`.
2. GitHub Actions (`.github/workflows/generar-video.yml`) pide el video a Veo en vertical 9:16,
   lo deja en 1080x1920 y lo guarda en la carpeta indicada.
3. La escena pasa a `escenas/hechas/` (o a `escenas/errores/` con el motivo).

También se puede lanzar a mano: pestaña **Actions → Generar video con Veo → Run workflow**.

Requisito: secreto `GEMINI_API_KEY` en Settings → Secrets and variables → Actions.
