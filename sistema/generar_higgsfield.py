#!/usr/bin/env python3
"""Genera videos verticales con la API de Higgsfield a partir de escenas JSON.

Cada archivo en escenas/pendientes/*.json describe un video:
{
  "carpeta": "2026-09/2026-09-29_005_tema",   # donde se guarda el video
  "archivo": "005_ES.mp4",                   # nombre del video
  "prompt": "Descripción de la escena...",   # lo que el modelo debe crear
  "modelo": "kling-video/v3.0/std/text-to-video",  # opcional (ruta del modelo en Higgsfield)
  "duracion": 10,                            # opcional, en segundos
  "parametros": {"sound": "on"},             # opcional: campos extra propios del modelo
  "imagen_inicial": "https://.../foto.jpg"   # opcional: anima esta foto (misma persona)
}

Para imágenes (fotos de personajes, casas...): "tipo": "imagen", y opcionales
"formato" (3:4, 9:16, 1:1...) y "cantidad" (1 o 4). Se guardan como archivo_1.jpg, archivo_2.jpg...

Al terminar, la escena pasa a escenas/hechas/ (o a escenas/errores/ con el motivo).
Necesita el secreto HF_API_KEY en GitHub y ffmpeg.
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

BASE = "https://api.higgsfield.ai"
MODELO_POR_DEFECTO = "kling-video/v3.0/std/text-to-video"
MODELO_IMAGEN = "higgsfield-ai/soul/v2/standard"
MODELO_IMAGEN_A_VIDEO = "kling-video/v3.0/std/image-to-video"
MODELO_EDICION = "xai/grok-imagine-image-2.0"
REPO_RAW = "https://raw.githubusercontent.com/presidents-geohomes/GeoHomesVideos/main/"
# Una sola clave (HF_API_KEY, tal como la copia el botón "Copy API key"),
# o bien el par antiguo HF_API_KEY_ID + HF_API_KEY_SECRET.
_ID = os.environ.get("HF_API_KEY_ID", "").strip()
_SECRET = os.environ.get("HF_API_KEY_SECRET", "").strip()
CLAVE = os.environ.get("HF_API_KEY", "").strip() or (f"{_ID}:{_SECRET}" if _ID and _SECRET else "")
if CLAVE.lower().startswith("key "):
    CLAVE = CLAVE[4:].strip()
ESPERA_MAX = 20 * 60  # segundos
# Cloudflare bloquea el agente por defecto de Python ("Python-urllib").
UA = "GeoHomesVideos/1.0 (+https://github.com/presidents-geohomes/GeoHomesVideos)"
FINALES = {"completed", "failed", "nsfw", "canceled", "cancelled"}


def llamar(url, datos=None):
    req = urllib.request.Request(url, method="POST" if datos is not None else "GET")
    req.add_header("Authorization", f"Key {CLAVE}")
    req.add_header("Accept", "application/json")
    req.add_header("User-Agent", UA)
    if datos is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(datos).encode()
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode(errors="replace")[:800]
        raise RuntimeError(f"HTTP {e.code}: {cuerpo}") from None


def es_imagen(escena):
    return escena.get("tipo") == "imagen"


def pedir_video(escena):
    if es_imagen(escena) and escena.get("referencias"):
        # Edición / continuidad: Grok Imagine conserva los detalles de las fotos de referencia
        modelo = escena.get("modelo") or MODELO_EDICION
        refs = [r if r.startswith("http") else REPO_RAW + r for r in escena["referencias"]]
        cuerpo = {
            "prompt": escena["prompt"],
            "image_urls": refs,
            "aspect_ratio": escena.get("formato", "9:16"),
            "resolution": escena.get("resolucion", "2k"),
            "quality": "medium",
        }
    elif es_imagen(escena):
        modelo = escena.get("modelo") or MODELO_IMAGEN
        cuerpo = {
            "prompt": escena["prompt"],
            "aspect_ratio": escena.get("formato", "3:4"),
            "resolution": "1080p",
            "batch_size": int(escena.get("cantidad", 4)),
            "enhance_prompt": False,
        }
    else:
        modelo = escena.get("modelo") or (
            MODELO_IMAGEN_A_VIDEO if escena.get("imagen_inicial") else MODELO_POR_DEFECTO)
        cuerpo = {
            "prompt": escena["prompt"],
            "aspect_ratio": "9:16",
            "duration": int(escena.get("duracion", 10)),
        }
        if "kling" in modelo:
            cuerpo["sound"] = "on"
        if escena.get("imagen_inicial"):
            cuerpo["image_url"] = escena["imagen_inicial"]
    cuerpo.update(escena.get("parametros") or {})
    resp = llamar(f"{BASE}/{modelo.strip('/')}", cuerpo)
    rid = resp.get("request_id") or resp.get("id")
    if not rid:
        raise RuntimeError(f"Higgsfield no devolvió request_id: {resp}")
    url_estado = resp.get("status_url") or f"{BASE}/requests/{rid}/status"
    print(f"  Modelo {modelo}: solicitud {rid}")
    return modelo, rid, url_estado


def buscar_url_video(dato):
    """Encuentra la URL del video en la respuesta, venga como venga."""
    if isinstance(dato, dict):
        v = dato.get("video")
        if isinstance(v, dict) and v.get("url"):
            return v["url"]
        for clave in ("videos", "outputs", "output", "result", "results", "jobs"):
            if clave in dato:
                u = buscar_url_video(dato[clave])
                if u:
                    return u
        for valor in dato.values():
            u = buscar_url_video(valor)
            if u:
                return u
    elif isinstance(dato, list):
        for x in dato:
            u = buscar_url_video(x)
            if u:
                return u
    elif isinstance(dato, str) and dato.startswith("http") and ".mp4" in dato.lower():
        return dato
    return None


def esperar(url_estado):
    inicio, pausa = time.time(), 2
    while time.time() - inicio < ESPERA_MAX:
        estado = llamar(url_estado)
        st = str(estado.get("status", "")).lower()
        if st in FINALES:
            if st != "completed":
                motivo = {"nsfw": "rechazado por el filtro de contenido (no se cobra)",
                          "failed": "la generación falló (no se cobra)"}.get(st, st)
                raise RuntimeError(f"Higgsfield: {motivo}. Detalle: {json.dumps(estado)[:500]}")
            return estado
        time.sleep(pausa)
        pausa = min(pausa + 2, 10)
    raise RuntimeError("Higgsfield tardó más de 20 minutos")


def urls_imagenes(estado):
    urls = []
    def recorrer(d):
        if isinstance(d, dict):
            for k, v in d.items():
                if k in ("url", "image_url") and isinstance(v, str) and v.startswith("http"):
                    urls.append(v)
                else:
                    recorrer(v)
        elif isinstance(d, list):
            for x in d:
                recorrer(x)
    recorrer(estado.get("images") or estado)
    return list(dict.fromkeys(urls))


def descargar(url, destino):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=300) as r, open(destino, "wb") as f:
        shutil.copyfileobj(r, f)


def a_vertical_1080(origen, destino):
    """Deja el video exactamente en 1080x1920, 30 fps, listo para TikTok/Reels."""
    vf = ("scale=1080:1920:force_original_aspect_ratio=increase,"
          "crop=1080:1920,format=yuv420p")
    tiene_audio = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=index", "-of", "csv=p=0", origen],
        capture_output=True, text=True).stdout.strip() != ""
    audio = ["-c:a", "aac", "-b:a", "192k"] if tiene_audio else ["-an"]
    subprocess.run([
        "ffmpeg", "-v", "error", "-y", "-i", origen, "-vf", vf, "-r", "30",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18", *audio,
        "-movflags", "+faststart", destino,
    ], check=True)


def procesar(ruta):
    nombre = os.path.basename(ruta)
    print(f"Escena {nombre}")
    escena = json.load(open(ruta, encoding="utf-8"))
    try:
        for campo in ("carpeta", "archivo", "prompt"):
            if not escena.get(campo):
                raise RuntimeError(f"Falta el campo '{campo}' en la escena")
        modelo, rid, url_estado = pedir_video(escena)
        estado = esperar(url_estado)
        os.makedirs(escena["carpeta"], exist_ok=True)
        if es_imagen(escena):
            urls = urls_imagenes(estado)
            if not urls:
                raise RuntimeError(f"Completado pero sin imágenes: {json.dumps(estado)[:800]}")
            base = os.path.splitext(escena["archivo"])[0]
            finales = []
            for i, u in enumerate(urls, 1):
                ext = os.path.splitext(u.split("?")[0])[1].lower() or ".jpg"
                if ext not in (".jpg", ".jpeg", ".png", ".webp"):
                    ext = ".jpg"
                destino = os.path.join(escena["carpeta"], f"{base}_{i}{ext}")
                descargar(u, destino)
                finales.append(destino)
            final = finales
        else:
            url = buscar_url_video(estado)
            if not url:
                raise RuntimeError(f"Completado pero sin URL de video: {json.dumps(estado)[:800]}")
            crudo = f"/tmp/{nombre}.hf.mp4"
            descargar(url, crudo)
            final = os.path.join(escena["carpeta"], escena["archivo"])
            a_vertical_1080(crudo, final)
        escena.update({"estado": "hecho", "modelo_usado": modelo, "request_id": rid,
                       "resultado": final,
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
    if not CLAVE:
        sys.exit("Falta el secreto HF_API_KEY en GitHub "
                 "(Settings → Secrets and variables → Actions).")
    pendientes = []
    for p in sorted(glob.glob("escenas/pendientes/*.json")):
        try:
            if json.load(open(p, encoding="utf-8")).get("tipo") in ("muestras_voz", "narracion", "musica"):
                continue  # las procesa sistema/voces.py
        except Exception:
            pass
        pendientes.append(p)
    if not pendientes:
        print("No hay escenas pendientes.")
        return
    resultados = [procesar(p) for p in pendientes]
    print(f"{sum(resultados)} de {len(resultados)} videos generados.")


if __name__ == "__main__":
    main()
