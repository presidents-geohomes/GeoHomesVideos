#!/usr/bin/env python3
"""Material de control de calidad para cada episodio (se genera solo al montar).

- hojas_por_plano(): una hoja de revisión por plano, a 4 fotogramas por segundo, para comprobar
  a simple vista que cada acción ocurre de verdad (y no "se funde"), la dirección de vehículos y
  personas, logos, objetos fuera de lugar, etc. Los detectores automáticos por píxeles probados
  no fueron fiables (fallaron el fundido del garaje de ES03 v1 y daban falsas alarmas con los
  subtítulos), así que la revisión es visual y obligatoria antes de entregar.
- transcribir(): transcribe la narración para compararla con el guion.
"""
import difflib
import json
import os
import re
import subprocess


def hojas_por_plano(video, planos, carpeta, fps=4):
    """planos = [(nombre, inicio, duracion)]. Guarda carpeta/plano_XX.jpg y devuelve las rutas."""
    os.makedirs(carpeta, exist_ok=True)
    rutas = []
    for k, (nombre, ini, dur) in enumerate(planos, 1):
        n = max(1, int(dur * fps))
        cols = min(n, 10)
        filas = (n + cols - 1) // cols
        destino = os.path.join(carpeta, f"plano_{k:02d}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{ini:.2f}", "-t", f"{dur:.2f}", "-i", video,
                        "-vf", f"fps={fps},scale=216:-1,tile={cols}x{filas}", "-frames:v", "1", destino],
                       check=True)
        rutas.append(destino)
    return rutas


def transcribir(audio, idioma="es"):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    modelo = WhisperModel("small", device="cpu", compute_type="int8")
    segs, _ = modelo.transcribe(audio, language=idioma)
    return " ".join(s.text.strip() for s in segs)


def parecido(a, b):
    limpiar = lambda s: re.sub(r"[^\wáéíóúñü ]", "", s.lower())
    return round(difflib.SequenceMatcher(None, limpiar(a), limpiar(b)).ratio(), 3)


def informe(ep, video, narracion_mp3, planos, carpeta):
    hojas = hojas_por_plano(video, planos, carpeta)
    esperado = " ".join(p["texto"] for p in ep["narracion"].get("partes", [])) or ep["narracion"].get("texto", "")
    oido = transcribir(narracion_mp3, ep.get("idioma", "es"))
    datos = {
        "hojas_por_plano": hojas,
        "narracion_esperada": esperado,
        "narracion_transcrita": oido,
        "parecido_narracion": parecido(esperado, oido) if oido else None,
        "revision_visual_pendiente": [
            "¿Cada acción clave ocurre de verdad (movimiento, no fundido)?",
            "¿Vehículos y personas miran en la dirección correcta?",
            "¿Sin logos ni letras raras?",
            "¿Aparatos y muebles en su lugar?",
            "¿Continuidad con el plano anterior?",
        ],
    }
    with open(os.path.join(carpeta, "qa.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    return datos
