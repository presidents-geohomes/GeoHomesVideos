#!/usr/bin/env python3
"""Monta un episodio completo de la serie de Geo Homes.

Lee episodios/pendientes/*.json:
{
  "id": "es_001_llegar_a_casa",
  "carpeta": "2026-09/2026-09-30_ES01_llegar-a-casa",
  "archivo": "ES01.mp4",
  "idioma": "es",
  "escenas": [
     {"imagen": "personajes/elegidos/casa_espanol.png", "duracion": 4,
      "prompt": "Qué pasa en la escena (sin diálogos)..."},
     ...
  ],
  "narracion": {"voice_id": "...", "texto": "..."},
  "cierre": {"frase": "Tu casa, a tu ritmo.", "lugar": "Geo Homes · Naples, FL", "segundos": 3},
  "subtitulos": true,
  "volumen_ambiente": 0.22
}

Pasos: 1) anima cada foto con Kling (image-to-video, sin diálogos), 2) genera la
narración con ElevenLabs, 3) une todo con transiciones suaves, subtítulos y el cierre
con el logo, 4) guarda el video en la carpeta y mueve el JSON a episodios/hechos/.
"""
import glob
import json
import os
import subprocess
import sys
import textwrap
import time
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import generar_higgsfield as hf  # noqa: E402
import voces  # noqa: E402

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

REPO_RAW = "https://raw.githubusercontent.com/presidents-geohomes/GeoHomesVideos/main/"
W, H, FPS = 1080, 1920, 30
XF = 0.5  # segundos de fundido entre escenas
NAVY = (27, 48, 80)
CREMA = (246, 242, 235)
TMP = "/tmp/episodio"
NEGATIVO = ("people talking, dialogue, lip movement, speaking to camera, text, captions, "
            "subtitles, watermark, logo, distorted face, extra fingers, morphing")


# ---------- tipografía ----------
def fuente(peso, tam):
    rutas = {
        "bold": ["/tmp/fonts/Poppins-SemiBold.ttf",
                 "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
        "regular": ["/tmp/fonts/Poppins-Regular.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
    }[peso]
    for r in rutas:
        if os.path.exists(r):
            return ImageFont.truetype(r, tam)
    return ImageFont.load_default()


def bajar_fuentes():
    os.makedirs("/tmp/fonts", exist_ok=True)
    base = "https://github.com/google/fonts/raw/main/ofl/poppins/"
    for f in ("Poppins-SemiBold.ttf", "Poppins-Regular.ttf"):
        destino = f"/tmp/fonts/{f}"
        if not os.path.exists(destino):
            try:
                urllib.request.urlretrieve(base + f, destino)
            except Exception as e:  # si falla, se usa DejaVu
                print(f"  (sin Poppins: {e})")


# ---------- utilidades ----------
def sh(*args):
    subprocess.run(list(args), check=True)


def duracion(ruta):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", ruta], capture_output=True, text=True).stdout
    return float(out.strip())


def url_publica(ruta):
    return ruta if ruta.startswith("http") else REPO_RAW + ruta


# ---------- 1. escenas ----------
def generar_escena(i, esc):
    cuerpo = {
        "image_url": url_publica(esc["imagen"]),
        "prompt": esc["prompt"] + " Cinematic, warm natural light, smooth slow camera movement, "
                  "no one speaks, ambient sound only.",
        "duration": int(esc.get("duracion", 5)),
        "aspect_ratio": "9:16",
        "sound": "on",
        "negative_prompt": NEGATIVO,
    }
    modelo = esc.get("modelo", hf.MODELO_IMAGEN_A_VIDEO)
    print(f"  Escena {i}: pidiendo a {modelo}")
    resp = hf.llamar(f"{hf.BASE}/{modelo}", cuerpo)
    rid = resp.get("request_id")
    url_estado = resp.get("status_url") or f"{hf.BASE}/requests/{rid}/status"
    return url_estado


def normalizar(origen, destino, segundos):
    """1080x1920, 30 fps, duración exacta, siempre con pista de audio."""
    tiene_audio = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", origen], capture_output=True, text=True).stdout.strip() != ""
    vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
          f"fps={FPS},format=yuv420p,tpad=stop_mode=clone:stop_duration=2")
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", origen]
    if not tiene_audio:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += ["-vf", vf, "-t", f"{segundos}", "-map", "0:v"]
    cmd += ["-map", "0:a" if tiene_audio else "1:a", "-af", "apad", "-ar", "44100", "-ac", "2",
            "-c:v", "libx264", "-preset", "fast", "-crf", "17", "-c:a", "aac", "-b:a", "192k",
            destino]
    sh(*cmd)


# ---------- 2. cierre ----------
def tarjeta_cierre(frase, lugar, destino_png):
    img = Image.new("RGB", (W, H), CREMA)
    d = ImageDraw.Draw(img)
    logo = Image.open("assets/logo_navy.png").convert("RGBA")
    lw = 520
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    y = 560
    img.paste(logo, ((W - lw) // 2, y), logo)
    y += logo.height + 90
    f1 = fuente("bold", 64)
    for linea in textwrap.wrap(frase, 24):
        tw = d.textlength(linea, font=f1)
        d.text(((W - tw) / 2, y), linea, font=f1, fill=NAVY)
        y += 84
    y += 30
    f2 = fuente("regular", 38)
    tw = d.textlength(lugar, font=f2)
    d.text(((W - tw) / 2, y), lugar, font=f2, fill=(90, 104, 128))
    img.save(destino_png)


# ---------- 3. subtítulos ----------
def frases_subtitulos(texto):
    """Parte la narración en frases cortas (máx. ~42 caracteres)."""
    import re
    trozos = [t.strip() for t in re.split(r"(?<=[.!?…:])\s+", texto) if t.strip()]
    salida = []
    for t in trozos:
        if len(t) <= 42:
            salida.append(t)
            continue
        partes = [p.strip() for p in re.split(r"(?<=,)\s+", t) if p.strip()]
        actual = ""
        for p in partes:
            if actual and len(actual) + len(p) + 1 > 42:
                salida.append(actual)
                actual = p
            else:
                actual = (actual + " " + p).strip()
        if actual:
            salida.append(actual)
    return salida


def png_subtitulo(texto, destino):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = fuente("bold", 50)
    lineas = textwrap.wrap(texto, 26)
    alto = len(lineas) * 66
    y0 = int(H * 0.70)
    ancho = max(d.textlength(l, font=f) for l in lineas)
    pad = 28
    d.rounded_rectangle(((W - ancho) / 2 - pad, y0 - pad, (W + ancho) / 2 + pad, y0 + alto + pad - 10),
                        radius=26, fill=(15, 22, 36, 150))
    y = y0
    for l in lineas:
        tw = d.textlength(l, font=f)
        d.text(((W - tw) / 2, y), l, font=f, fill=(255, 255, 255, 255))
        y += 66
    img.save(destino)


def tiempos_subtitulos(frases, inicio, dur_voz):
    total = sum(len(f) for f in frases)
    t, out = inicio, []
    for f in frases:
        dur = dur_voz * len(f) / total
        out.append((f, t, t + dur))
        t += dur
    return out


# ---------- montaje ----------
def montar(ep):
    os.makedirs(TMP, exist_ok=True)
    bajar_fuentes()
    escenas = ep["escenas"]

    # 1) pedir todas las escenas a la vez y la narración mientras tanto
    estados = [generar_escena(i + 1, e) for i, e in enumerate(escenas)]
    narr = f"{TMP}/narracion.mp3"
    voces.hablar(ep["narracion"]["voice_id"], ep["narracion"]["texto"], ep.get("idioma", "es"), narr)
    dur_voz = duracion(narr)
    print(f"  Narración: {dur_voz:.1f} s")

    clips = []
    for i, (url_estado, esc) in enumerate(zip(estados, escenas), 1):
        estado = hf.esperar(url_estado)
        url = hf.buscar_url_video(estado)
        if not url:
            raise RuntimeError(f"Escena {i} sin video: {json.dumps(estado)[:400]}")
        crudo = f"{TMP}/crudo_{i}.mp4"
        hf.descargar(url, crudo)
        norm = f"{TMP}/escena_{i}.mp4"
        normalizar(crudo, norm, float(esc.get("duracion", 5)))
        clips.append((norm, float(esc.get("duracion", 5))))
        print(f"  Escena {i} lista")

    # 2) cierre
    cierre = ep.get("cierre", {})
    seg_cierre = float(cierre.get("segundos", 3))
    tarjeta_cierre(cierre.get("frase", ""), cierre.get("lugar", "Geo Homes · Naples, FL"),
                   f"{TMP}/cierre.png")
    sh("ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", f"{TMP}/cierre.png",
       "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
       "-vf", f"fps={FPS},format=yuv420p,zoompan=z='1+0.0006*on':d=1:s={W}x{H}:fps={FPS}",
       "-t", f"{seg_cierre}", "-c:v", "libx264", "-preset", "fast", "-crf", "17",
       "-c:a", "aac", "-shortest", f"{TMP}/cierre.mp4")
    clips.append((f"{TMP}/cierre.mp4", seg_cierre))

    # 3) unir con fundidos
    entradas, fv, fa = [], [], []
    for c, _ in clips:
        entradas += ["-i", c]
    ultimo_v, ultimo_a, offset = "0:v", "0:a", 0.0
    for k in range(1, len(clips)):
        offset += clips[k - 1][1] - XF
        fv.append(f"[{ultimo_v}][{k}:v]xfade=transition=fade:duration={XF}:offset={offset:.3f}[v{k}]")
        fa.append(f"[{ultimo_a}][{k}:a]acrossfade=d={XF}[a{k}]")
        ultimo_v, ultimo_a = f"v{k}", f"a{k}"
    total = sum(d for _, d in clips) - XF * (len(clips) - 1)
    unido = f"{TMP}/unido.mp4"
    sh("ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(fv + fa),
       "-map", f"[{ultimo_v}]", "-map", f"[{ultimo_a}]", "-c:v", "libx264", "-preset", "fast",
       "-crf", "17", "-c:a", "aac", unido)

    # 4) subtítulos + mezcla de audio (ambiente bajo, narración encima)
    inicio_voz = float(ep.get("inicio_narracion", 0.4))
    fin_escenas = total - seg_cierre
    if inicio_voz + dur_voz > total - 0.2:
        print(f"  AVISO: la narración ({dur_voz:.1f}s) es larga para el video ({total:.1f}s)")
    overlays, filtros, prev = [], [], "0:v"
    if ep.get("subtitulos", True):
        subs = tiempos_subtitulos(frases_subtitulos(ep["narracion"]["texto"]), inicio_voz, dur_voz)
        for j, (texto, a, b) in enumerate(subs):
            # la tarjeta final ya muestra la frase de cierre: ahí no van subtítulos
            if a >= fin_escenas - 0.3:
                continue
            b = min(b, fin_escenas)
            png = f"{TMP}/sub_{j}.png"
            png_subtitulo(texto, png)
            overlays += ["-i", png]
            n_in = len(overlays) // 2 + 1
            filtros.append(f"[{prev}][{n_in}:v]overlay=0:0:enable='between(t,{a:.2f},{b:.2f})'[s{j}]")
            prev = f"s{j}"
    vol = float(ep.get("volumen_ambiente", 0.22))
    ms = int(inicio_voz * 1000)
    filtros.append(f"[0:a]volume={vol}[amb]")
    filtros.append(f"[1:a]adelay={ms}|{ms},volume=1.0[voz]")
    filtros.append("[amb][voz]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
                   "loudnorm=I=-14:TP=-1.5:LRA=11[aout]")
    final = os.path.join(ep["carpeta"], ep["archivo"])
    os.makedirs(ep["carpeta"], exist_ok=True)
    sh("ffmpeg", "-v", "error", "-y", "-i", unido, "-i", narr, *overlays,
       "-filter_complex", ";".join(filtros), "-map", f"[{prev}]", "-map", "[aout]",
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
       "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", final)
    # guardar también la narración sola
    sh("cp", narr, os.path.join(ep["carpeta"], os.path.splitext(ep["archivo"])[0] + "_narracion.mp3"))
    return final, total


def main():
    pendientes = sorted(glob.glob("episodios/pendientes/*.json"))
    if not pendientes:
        print("No hay episodios pendientes.")
        return
    for ruta in pendientes:
        ep = json.load(open(ruta, encoding="utf-8"))
        print(f"Episodio {ep.get('id', ruta)}")
        try:
            final, total = montar(ep)
            ep.update({"estado": "hecho", "video": final, "duracion": round(total, 2)})
            destino = "episodios/hechos"
            print(f"  Listo: {final} ({total:.1f} s)")
        except Exception as e:
            ep.update({"estado": "error", "error": str(e)})
            destino = "episodios/errores"
            print(f"  ERROR: {e}")
        ep["fecha"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        os.makedirs(destino, exist_ok=True)
        json.dump(ep, open(os.path.join(destino, os.path.basename(ruta)), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        os.remove(ruta)


if __name__ == "__main__":
    main()
