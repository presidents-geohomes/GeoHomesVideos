#!/usr/bin/env python3
"""Portada (miniatura) de cada episodio: 1080x1920, lista para Reels y TikTok.

Usa una foto LIMPIA del episodio (la foto de partida del plano más llamativo, sin subtítulos),
un título corto (el gancho) y la marca. El texto va dentro de la zona segura 4:5 (el centro
que Instagram muestra en la cuadrícula del perfil: y de 285 a 1635).

Uso: python3 sistema/portada.py <imagen> "<título>" <salida.jpg>
     (añade --abajo para poner el título abajo si las caras están arriba; etiqueta opcional: <imagen> "<título>" "<etiqueta>" <salida.jpg>; por defecto sin etiqueta ni logo)
"""
import os
import sys
import textwrap
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
NAVY = (27, 48, 80)


def _fuente(peso, tam):
    rutas = {"bold": ["/tmp/fonts/Poppins-SemiBold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
             "regular": ["/tmp/fonts/Poppins-Regular.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]}[peso]
    for r in rutas:
        if os.path.exists(r):
            return ImageFont.truetype(r, tam)
    return ImageFont.load_default()


def _bajar_fuentes():
    os.makedirs("/tmp/fonts", exist_ok=True)
    for f in ("Poppins-SemiBold.ttf", "Poppins-Regular.ttf"):
        d = f"/tmp/fonts/{f}"
        if not os.path.exists(d):
            try:
                urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/poppins/" + f, d)
            except Exception:
                pass


def crear_portada(imagen, titulo, etiqueta, destino, logo=None, posicion="arriba"):
    """Por defecto SIN etiqueta de episodio y SIN logo (pedido del cliente): foto cercana y emotiva + gancho."""
    _bajar_fuentes()
    im = Image.open(imagen).convert("RGB")
    esc = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * esc), int(im.height * esc)), Image.LANCZOS)
    x0, y0 = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x0, y0, x0 + W, y0 + H))

    # degradado oscuro (arriba o abajo) para que el título se lea sin tapar las caras
    sombra = Image.new("L", (W, H), 0)
    ds = ImageDraw.Draw(sombra)
    for y in range(0, 1000):
        yy = y if posicion == "arriba" else H - 1 - y
        ds.line([(0, yy), (W, yy)], fill=int(190 * (1 - y / 1000) ** 1.6))
    negro = Image.new("RGB", (W, H), (10, 16, 28))
    im = Image.composite(negro, im, sombra.filter(ImageFilter.GaussianBlur(4)))
    d = ImageDraw.Draw(im)

    # etiqueta de la serie (solo si se pide explícitamente)
    f_et = _fuente("bold", 34)
    if not etiqueta:
        f_et = None
    if f_et:
        tw = d.textlength(etiqueta, font=f_et)
        y = 330
        d.rounded_rectangle(((W - tw) / 2 - 28, y - 14, (W + tw) / 2 + 28, y + 50), radius=32, fill=(255, 255, 255))
        d.text(((W - tw) / 2, y - 2), etiqueta, font=f_et, fill=NAVY)

    # título (gancho)
    f_t = _fuente("bold", 88)
    ancho = 13 if len(titulo) <= 13 else max(9, (len(titulo) + 1) // 2 + 1)
    lineas = textwrap.wrap(titulo, ancho)[:3]  # cortes equilibrados
    y = (440 if etiqueta else 360) if posicion == "arriba" else 1600 - 104 * len(lineas)
    for linea in lineas:
        tw = d.textlength(linea, font=f_t)
        d.text(((W - tw) / 2 + 3, y + 4), linea, font=f_t, fill=(0, 0, 0))
        d.text(((W - tw) / 2, y), linea, font=f_t, fill=(255, 255, 255))
        y += 104

    # logo pequeño abajo, dentro de la zona segura
    if logo and os.path.exists(logo):
        lg = Image.open(logo).convert("RGBA")
        lw = 170
        lg = lg.resize((lw, int(lg.height * lw / lg.width)), Image.LANCZOS)
        base = Image.new("RGBA", (lw + 60, lg.height + 50), (0, 0, 0, 0))
        ImageDraw.Draw(base).rounded_rectangle((0, 0, base.width, base.height), radius=30, fill=(10, 16, 28, 150))
        base.paste(lg, (30, 25), lg)
        im.paste(base, ((W - base.width) // 2, 1620 - base.height), base)
    os.makedirs(os.path.dirname(destino) or ".", exist_ok=True)
    im.save(destino, quality=92)
    return destino


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a not in ("--abajo",)]
    crear_portada(args[0], args[1], args[2] if len(args) > 3 else "", args[-1],
                  posicion="abajo" if "--abajo" in sys.argv else "arriba")
