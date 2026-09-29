#!/usr/bin/env python3
"""Pista de sonido de un episodio con efectos de ElevenLabs (sin el audio de Kling).

Uso:
  python3 sistema/sonido_episodio.py <episodio.json> <plan_sonido.json> <salida.mp4> [video_origen.mp4]

- episodio.json: el JSON del episodio (episodios/hechos/...). Se usan la carpeta, la
  narración y la música ya guardadas (<ID>_narracion.mp3 y <ID>_musica.mp3) y los tiempos
  de cada plano, así que NO se gasta nada en Higgsfield ni en ElevenLabs.
- plan_sonido.json:
  {"efectos": [
     {"archivo": "sonidos/ES03/ladrido_1.mp3",   # efecto generado (tipo "efectos" en voces.py)
      "escena": 3, "t": 1.85,                    # momento dentro del plano (o "en": segundos absolutos)
      "vol": 0.8,                                # volumen (1.0 = original)
      "alinear": true,                           # el GOLPE del sonido (no su silencio inicial) cae en ese momento
      "dur": 2.5,                                # opcional: cortar a esta duración
      "entrada": 0.2, "salida": 0.4}             # opcional: fundidos en segundos
  ]}
- video_origen: por defecto <carpeta>/<archivo> del episodio. Solo se reemplaza el audio;
  la imagen se copia tal cual.
"""
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

XF = 0.5
NIVELES_MUSICA = {"alta": 0.55, "media": 0.35, "baja": 0.08, "silencio": 0.0}


def sh(*args):
    subprocess.run(args, check=True)


def duracion(ruta):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", ruta], capture_output=True, text=True).stdout
    return float(out.strip())


def leer_audio(ruta, sr=44100):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-ac", "1", "-ar", str(sr),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def golpe(ruta, umbral_db=-20.0):
    """Segundo en que el sonido 'arranca' de verdad (primer tramo de 5 ms que supera
    umbral_db respecto del pico). Sirve para que un clic o un ladrido caiga justo en su sitio."""
    a = leer_audio(ruta)
    if not len(a):
        return 0.0
    ventana = 220  # 5 ms
    n = len(a) // ventana
    rms = np.sqrt((a[:n * ventana].reshape(n, ventana) ** 2).mean(axis=1) + 1e-12)
    limite = rms.max() * 10 ** (umbral_db / 20)
    idx = int(np.argmax(rms >= limite))
    return idx * ventana / 44100


def inicios_planos(ep):
    t, ini = 0.0, []
    for e in ep["escenas"]:
        ini.append(t)
        t += float(e.get("duracion", 5)) - XF
    ini.append(t)  # cierre
    total = t + float(ep.get("cierre", {}).get("segundos", 3))
    return ini, total


def envolvente_musica(ep, inicios, total):
    from montar_episodio import envolvente
    cierre = ep.get("cierre", {})
    puntos = []
    for k, esc in enumerate(ep["escenas"]):
        puntos.append((inicios[k] + float(esc.get("musica_desde", 0.0)),
                       NIVELES_MUSICA.get(esc.get("musica", "media"), 0.35)))
    puntos.append((inicios[-2], NIVELES_MUSICA.get(cierre.get("musica", "media"), 0.35)))
    puntos.append((total - 1.2, puntos[-1][1]))
    puntos.append((total, 0.0))
    return envolvente(puntos, rampa=0.6)


def momento(ef, inicios):
    if "en" in ef:
        return float(ef["en"])
    esc = ef["escena"]
    idx = len(inicios) - 1 if esc == "cierre" else int(esc) - 1
    return inicios[idx] + float(ef.get("t", 0.0))


def mezclar(ep, plan, salida, video=None):
    carpeta = ep["carpeta"]
    base = os.path.splitext(ep["archivo"])[0]
    video = video or os.path.join(carpeta, ep["archivo"])
    narr = os.path.join(carpeta, base + "_narracion.mp3")
    musica = os.path.join(carpeta, base + "_musica.mp3")
    inicios, total = inicios_planos(ep)
    total = min(total, duracion(video))

    entradas = ["-i", video, "-i", narr, "-i", musica]
    filtros = ["[1:a]aresample=44100,volume=1.0[voz]",
               f"[2:a]aresample=44100,atrim=0:{total:.2f},volume='{envolvente_musica(ep, inicios, total)}':eval=frame[mus]"]
    etiquetas = ["[voz]", "[mus]"]
    informe = []
    for k, ef in enumerate(plan["efectos"]):
        n = 3 + k
        entradas += ["-i", ef["archivo"]]
        t = momento(ef, inicios)
        adelanto = golpe(ef["archivo"]) if ef.get("alinear") else 0.0
        recorte = max(adelanto - 0.03, 0.0) if ef.get("alinear") else float(ef.get("desde", 0.0))
        inicio = max(t - (adelanto - recorte), 0.0)
        cadena = [f"aresample=44100", f"atrim=start={recorte:.3f}", "asetpts=PTS-STARTPTS"]
        if ef.get("dur"):
            cadena.append(f"atrim=0:{float(ef['dur']):.3f}")
            d = float(ef["dur"])
        else:
            d = duracion(ef["archivo"]) - recorte
        if ef.get("entrada"):
            cadena.append(f"afade=t=in:st=0:d={float(ef['entrada']):.2f}")
        if ef.get("salida"):
            cadena.append(f"afade=t=out:st={max(d - float(ef['salida']), 0):.2f}:d={float(ef['salida']):.2f}")
        ms = int(inicio * 1000)
        cadena += [f"volume={float(ef.get('vol', 0.5)):.3f}", f"adelay={ms}|{ms}"]
        filtros.append(f"[{n}:a]" + ",".join(cadena) + f"[e{k}]")
        etiquetas.append(f"[e{k}]")
        informe.append((os.path.basename(ef["archivo"]), round(t, 2), round(inicio, 2)))
    filtros.append("".join(etiquetas) + f"amix=inputs={len(etiquetas)}:duration=longest:"
                   "dropout_transition=0:normalize=0,"
                   f"atrim=0:{total:.2f},loudnorm=I=-14:TP=-1.5:LRA=11,"
                   f"afade=t=out:st={total - 0.4:.2f}:d=0.4[aout]")
    os.makedirs(os.path.dirname(salida) or ".", exist_ok=True)
    sh("ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(filtros),
       "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
       "-ar", "44100", "-movflags", "+faststart", "-t", f"{total:.2f}", salida)
    return informe


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    ep = json.load(open(sys.argv[1], encoding="utf-8"))
    plan = json.load(open(sys.argv[2], encoding="utf-8"))
    video = sys.argv[4] if len(sys.argv) > 4 else None
    for nombre, t, ini in mezclar(ep, plan, sys.argv[3], video):
        print(f"  {nombre:28s} golpe en {t:6.2f} s (archivo empieza en {ini:.2f} s)")
    print(f"Listo: {sys.argv[3]}")


if __name__ == "__main__":
    main()
