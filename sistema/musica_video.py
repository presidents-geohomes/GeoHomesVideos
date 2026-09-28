#!/usr/bin/env python3
"""Pone una pista de la biblioteca de música a un video (los videos de texto salen mudos).

Uso:
  python3 sistema/musica_video.py <video.mp4> <id_pista> <salida.mp4>
  python3 sistema/musica_video.py --lista        # muestra las pistas y para qué sirven

La pista se recorta a la duración del video, con fundido de salida de 1.5 s y volumen
normalizado para redes (-14 LUFS). El video no se recodifica.
"""
import json
import os
import subprocess
import sys

BIBLIOTECA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "musica", "biblioteca")


def pistas():
    return json.load(open(os.path.join(BIBLIOTECA, "biblioteca.json"), encoding="utf-8"))["pistas"]


def duracion(ruta):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", ruta]).decode().strip())


def poner_musica(video, id_pista, salida):
    pista = next((p for p in pistas() if p["id"] == id_pista), None)
    if not pista:
        sys.exit(f"No existe la pista '{id_pista}'. Usa --lista para ver las disponibles.")
    audio = os.path.join(BIBLIOTECA, id_pista + ".mp3")
    d = duracion(video)
    filtro = (f"[1:a]atrim=0:{d:.2f},afade=t=in:d=0.2,afade=t=out:st={max(0, d - 1.5):.2f}:d=1.5,"
              "loudnorm=I=-14:TP=-1.5:LRA=11[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-i", audio, "-filter_complex", filtro,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "44100", "-shortest", "-movflags", "+faststart", salida], check=True)
    print(f"{salida}: {pista['estilo']} ({id_pista})")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--lista":
        for p in pistas():
            print(f"{p['id']:22} [{p['idioma']}] {p['estilo']} → {p['usar_para']}")
    elif len(sys.argv) == 4:
        poner_musica(*sys.argv[1:])
    else:
        sys.exit(__doc__)
