#!/usr/bin/env python3
"""Genera videos verticales con Veo (API de Gemini) a partir de escenas JSON.

Cada archivo en escenas/pendientes/*.json describe un video:
{
  "carpeta": "2026-09/2026-09-29_005_tema",   # donde se guarda el video
  "archivo": "005_ES.mp4",                   # nombre del video
  "prompt": "Descripción de la escena...",   # lo que Veo debe crear
  "modelo": "veo-3.1-fast-generate-preview", # opcional
  "duracion": 8,                             # opcional: 4, 6 u 8 segundos
  "resolucion": "1080p",                     # opcional: 720p o 1080p
  "prompt_negativo": "texto, subtítulos"     # opcional
}

Al terminar, la escena pasa a escenas/hechas/ (o a escenas/errores/ con el motivo).
Necesita la variable de entorno GEMINI_API_KEY y ffmpeg instalado.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = "https://generativelanguage.googleapis.com/v1beta"
MODELOS = [
    "veo-3.1-fast-generate-preview",
    "veo-3.1-generate-preview",
    "veo-3.1-lite-generate-preview",
]
KEY = os.environ.get("GEMINI_API_KEY", "").strip()
ESPERA_MAX = 15 * 60  # segundos


def llamar(url, datos=None):
    req = urllib.request.Request(url, method="POST" if datos else "GET")
    req.add_header("x-goog-api-key", KEY)
    if datos:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(datos).encode()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode(errors="replace")[:800]
        raise RuntimeError(f"HTTP {e.code}: {cuerpo}") from None


def pedir_video(escena):
    params = {
        "aspectRatio": "9:16",
        "durationSeconds": int(escena.get("duracion", 8)),
        "resolution": escena.get("resolucion", "1080p"),
        "personGeneration": "allow_all",
    }
    if escena.get("prompt_negativo"):
        params["negativePrompt"] = escena["prompt_negativo"]
    cuerpo = {"instances": [{"prompt": escena["prompt"]}], "parameters": params}

    modelos = [escena["modelo"]] if escena.get("modelo") else MODELOS
    ultimo_error = None
    for modelo in modelos:
        try:
            op = llamar(f"{BASE}/models/{modelo}:predictLongRunning", cuerpo)
            print(f"  Modelo {modelo}: operación {op['name']}")
            return modelo, op["name"]
        except RuntimeError as e:
            ultimo_error = e
            print(f"  Modelo {modelo} no disponible: {e}")
            # Solo probamos el siguiente modelo si este no existe o no está permitido.
            if not any(c in str(e) for c in ("HTTP 404", "HTTP 400", "HTTP 403")):
                break
    raise RuntimeError(f"No se pudo pedir el video: {ultimo_error}")


def esperar(nombre_op):
    inicio = time.time()
    while time.time() - inicio < ESPERA_MAX:
        estado = llamar(f"{BASE}/{nombre_op}")
        if estado.get("done"):
            if "error" in estado:
                raise RuntimeError(f"Veo devolvió un error: {estado['error']}")
            resp = estado.get("response", {}).get("generateVideoResponse", {})
            muestras = resp.get("generatedSamples") or []
            if not muestras:
                filtro = resp.get("raiMediaFilteredReasons") or resp
                raise RuntimeError(f"Veo no entregó video (posible filtro de contenido): {filtro}")
            return muestras[0]["video"]["uri"]
        time.sleep(10)
    raise RuntimeError("Veo tardó más de 15 minutos")


def descargar(uri, destino):
    req = urllib.request.Request(uri)
    req.add_header("x-goog-api-key", KEY)
    with urllib.request.urlopen(req, timeout=300) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)


def a_vertical_1080(origen, destino):
    """Deja el video exactamente en 1080x1920, 30 fps, listo para TikTok/Reels."""
    vf = ("scale=1080:1920:force_original_aspect_ratio=increase,"
          "crop=1080:1920,format=yuv420p")
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", origen, "-vf", vf, "-r", "30",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", destino,
    ], check=True)


def procesar(ruta):
    nombre = os.path.basename(ruta)
    print(f"Escena {nombre}")
    escena = json.load(open(ruta, encoding="utf-8"))
    try:
        for campo in ("carpeta", "archivo", "prompt"):
            if not escena.get(campo):
                raise RuntimeError(f"Falta el campo '{campo}' en la escena")
        modelo, op = pedir_video(escena)
        uri = esperar(op)
        os.makedirs(escena["carpeta"], exist_ok=True)
        crudo = f"/tmp/{nombre}.veo.mp4"
        descargar(uri, crudo)
        final = os.path.join(escena["carpeta"], escena["archivo"])
        a_vertical_1080(crudo, final)
        escena.update({"estado": "hecho", "modelo_usado": modelo, "video": final,
                       "generado": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        destino_dir = "escenas/hechas"
        print(f"  Listo: {final}")
        ok = True
    except Exception as e:  # se registra y se sigue con la siguiente escena
        escena.update({"estado": "error", "error": str(e),
                       "fecha_error": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
        destino_dir = "escenas/errores"
        print(f"  ERROR: {e}")
        ok = False
    os.makedirs(destino_dir, exist_ok=True)
    with open(os.path.join(destino_dir, nombre), "w", encoding="utf-8") as f:
        json.dump(escena, f, ensure_ascii=False, indent=2)
    os.remove(ruta)
    return ok


def main():
    if not KEY:
        sys.exit("Falta el secreto GEMINI_API_KEY en GitHub (Settings → Secrets → Actions).")
    pendientes = sorted(glob.glob("escenas/pendientes/*.json"))
    if not pendientes:
        print("No hay escenas pendientes.")
        return
    resultados = [procesar(p) for p in pendientes]
    print(f"{sum(resultados)} de {len(resultados)} videos generados.")


if __name__ == "__main__":
    main()
