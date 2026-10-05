#!/usr/bin/env python3
"""Encuentra en qué momento ocurre cada acción de un plano, para colocar los efectos de sonido.

Uso:
  python3 sistema/momentos.py <video.mp4> <desde_s> <hasta_s> [x y ancho alto] [--hoja salida.png]

- Mide el movimiento cuadro a cuadro (15 por segundo) en la zona indicada (en píxeles del
  video 1080x1920; sin zona = todo el cuadro) e imprime una barra por instante.
  Los picos de movimiento son los momentos de acción (perro que se levanta, puerta que gira...).
- Con --hoja guarda una hoja de fotogramas recortados con su segundo encima, para confirmar
  a ojo (p. ej. el cuadro exacto donde el perro abre la boca para ladrar).
- Los fundidos entre planos (0,5 s) también dan picos: ignora el primer y el último medio segundo.
- Los textos y subtítulos que aparecen también mueven la imagen: elige una zona que no los incluya.
"""
import subprocess
import sys

import numpy as np


def cuadros(video, t0, t1, zona=None, fps=15):
    vf = [f"fps={fps}"]
    if zona:
        x, y, w, h = zona
        vf.append(f"crop={w}:{h}:{x}:{y}")
    else:
        w, h = 1080, 1920
    vf.append("scale=iw/2:ih/2,format=gray")
    w2, h2 = w // 2, h // 2
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(t1 - t0), "-i", video,
                          "-vf", ",".join(vf), "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8)[: (len(raw) // (w2 * h2)) * w2 * h2].reshape(-1, h2, w2)


def hoja(video, t0, t1, zona, salida, fps=15, cols=10):
    from PIL import Image, ImageDraw
    import io
    vf = [f"fps={fps}"]
    if zona:
        x, y, w, h = zona
        vf.append(f"crop={w}:{h}:{x}:{y}")
    vf.append("scale=200:-2")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(t1 - t0), "-i", video,
                          "-vf", ",".join(vf), "-f", "image2pipe", "-vcodec", "png", "-"],
                         capture_output=True, check=True).stdout
    imgs, marca = [], b"\x89PNG"
    partes = raw.split(marca)[1:]
    for p in partes:
        imgs.append(Image.open(io.BytesIO(marca + p)).convert("RGB"))
    if not imgs:
        return
    W, H = imgs[0].size
    filas = (len(imgs) + cols - 1) // cols
    lienzo = Image.new("RGB", (cols * W, filas * (H + 16)), "white")
    d = ImageDraw.Draw(lienzo)
    for k, im in enumerate(imgs):
        x, y = (k % cols) * W, (k // cols) * (H + 16)
        lienzo.paste(im, (x, y + 16))
        d.text((x + 3, y + 2), f"{t0 + k / fps:.2f}s", fill="black")
    lienzo.save(salida)


def main():
    args = [a for a in sys.argv[1:]]
    salida = None
    if "--hoja" in args:
        i = args.index("--hoja")
        salida = args[i + 1]
        del args[i:i + 2]
    if len(args) not in (3, 7):
        sys.exit(__doc__)
    video, t0, t1 = args[0], float(args[1]), float(args[2])
    zona = tuple(int(v) for v in args[3:7]) if len(args) == 7 else None
    a = cuadros(video, t0, t1, zona).astype(float)
    dif = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2))
    tope = max(dif.max(), 1e-6)
    for k, v in enumerate(dif):
        print(f"{t0 + (k + 1) / 15:6.2f} s {v:6.2f} " + "#" * int(40 * v / tope))
    if salida:
        hoja(video, t0, t1, zona, salida)
        print(f"Hoja de fotogramas: {salida}")


if __name__ == "__main__":
    main()
