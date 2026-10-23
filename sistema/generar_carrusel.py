#!/usr/bin/env python3
"""Genera un carrusel de Geo Homes (JPG 1080x1350, estilo azul marino) desde un JSON.

Uso:
  python3 sistema/generar_carrusel.py <guion.json> <carpeta_salida> <prefijo>
  -> <carpeta_salida>/<prefijo>_1.jpg ... <prefijo>_N.jpg

Formato del JSON:
{
  "slides": [
    {"tipo": "portada", "foto": "catalogo/seleccion/termostato_1.jpg",
     "etiqueta": "TERMOSTATO INTELIGENTE", "titulo": "Llegas y la casa ya está fresca",
     "texto": "Controla el aire desde tu celular."},
    {"tipo": "texto", "titulo": "¿Enfriando una casa vacía?", "texto": "En Florida el aire trabaja todo el día."},
    {"tipo": "foto", "foto": "...", "etiqueta": "ESCENA \\"ME VOY\\"", "titulo": "...", "texto": "..."},
    {"tipo": "lista", "foto": "...", "titulo": "Cómo te ayuda", "puntos": ["...", "..."]},
    {"tipo": "cta", "titulo": "¿Es para tu casa?", "puntos": ["Estimado gratis", "..."],
     "boton": "Escríbenos CASA", "telefono": "(239) 204-6336", "pie": "Geo Homes · Suroeste de Florida"}
  ]
}
Rutas de foto relativas a la raíz del repo. Textos cortos: el script reduce la letra si no cabe
y avisa por stderr si aun así se corta.
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1350
NAVY = (27, 47, 80)
WHITE = (255, 255, 255)
SOFT = (205, 214, 228)
PILL = (235, 236, 231)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = ["/usr/share/fonts/truetype/google-fonts", os.path.join(RAIZ, "sistema", "fuentes"),
           os.path.expanduser("~/.fonts"), "/usr/share/fonts/truetype/poppins"]
AVISOS = []


def fuente(peso, tam):
    alternativas = {"SemiBold": ["SemiBold", "Bold"], "Medium": ["Medium", "Regular"]}.get(peso, [peso])
    for pz in alternativas:
        for d in FUENTES:
            p = os.path.join(d, f"Poppins-{pz}.ttf")
            if os.path.exists(p):
                return ImageFont.truetype(p, tam)
    raise SystemExit("Falta la fuente Poppins (instala @expo-google-fonts/poppins o fonts-poppins)")


def envolver(draw, texto, f, ancho):
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if draw.textlength(prueba, font=f) <= ancho:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def bloque(draw, texto, peso, tam, ancho, max_lineas, minimo):
    """Devuelve (font, lineas) bajando la letra hasta que quepa."""
    t = tam
    while True:
        f = fuente(peso, t)
        ls = envolver(draw, texto, f, ancho)
        if len(ls) <= max_lineas or t <= minimo:
            if len(ls) > max_lineas:
                AVISOS.append(f"Texto demasiado largo: '{texto[:40]}...'")
                ls = ls[:max_lineas]
            return f, ls
        t -= 4


def escribir(draw, xy, lineas, f, color, interlinea=1.18):
    x, y = xy
    alto = int(f.size * interlinea)
    for l in lineas:
        draw.text((x, y), l, font=f, fill=color)
        y += alto
    return y


def foto_cubrir(ruta, w, h):
    im = Image.open(os.path.join(RAIZ, ruta)).convert("RGB")
    return ImageOps.fit(im, (w, h), Image.LANCZOS, centering=(0.5, 0.45))


def degradado(im, desde, hasta):
    """Oscurece hacia NAVY desde y=desde (transparente) hasta y=hasta (opaco)."""
    capa = Image.new("RGB", im.size, NAVY)
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    for y in range(desde, im.size[1]):
        a = min(255, int(255 * (y - desde) / max(1, hasta - desde)))
        md.line([(0, y), (im.size[0], y)], fill=a)
    return Image.composite(capa, im, mask)


def etiqueta(draw, x, y, texto):
    f = fuente("SemiBold", 22)
    tw = draw.textlength(texto, font=f)
    draw.rounded_rectangle([x, y, x + tw + 36, y + 44], radius=22, fill=PILL)
    draw.text((x + 18, y + 8), texto, font=f, fill=NAVY)
    return y + 44


def contador(draw, i, n, oscuro=False):
    f = fuente("Medium", 22)
    t = f"{i} / {n}"
    draw.text((W - 50 - draw.textlength(t, font=f), 40), t, font=f, fill=NAVY if oscuro else WHITE)


def logo(im, ancho, centro=None, esquina=None):
    p = os.path.join(RAIZ, "assets", "logo_white.png")
    if not os.path.exists(p):
        return 0
    lg = Image.open(p).convert("RGBA")
    lg = lg.resize((ancho, int(lg.height * ancho / lg.width)), Image.LANCZOS)
    if centro:
        pos = (centro[0] - lg.width // 2, centro[1])
    else:
        pos = esquina
    im.paste(lg, pos, lg)
    return lg.height


def s_portada(s, i, n):
    im = degradado(foto_cubrir(s["foto"], W, H), int(H * 0.42), int(H * 0.78))
    d = ImageDraw.Draw(im)
    logo(im, 110, esquina=(45, 35))
    contador(d, i, n)
    m, ancho = 60, W - 120
    ft, lt = bloque(d, s["titulo"], "Bold", 74, ancho, 3, 52)
    fx, lx = bloque(d, s.get("texto", ""), "Regular", 32, ancho, 3, 24) if s.get("texto") else (None, [])
    alto = len(lt) * int(ft.size * 1.12) + (len(lx) * int(fx.size * 1.3) + 20 if lx else 0)
    y = H - 90 - alto
    if s.get("etiqueta"):
        etiqueta(d, m, y - 70, s["etiqueta"])
    y = escribir(d, (m, y), lt, ft, WHITE, 1.12)
    if lx:
        escribir(d, (m, y + 20), lx, fx, SOFT, 1.3)
    return im


def s_foto(s, i, n):
    im = Image.new("RGB", (W, H), NAVY)
    alto_foto = int(H * 0.74)
    f = degradado(foto_cubrir(s["foto"], W, alto_foto), int(alto_foto * 0.62), alto_foto)
    im.paste(f, (0, 0))
    d = ImageDraw.Draw(im)
    contador(d, i, n)
    m, ancho = 60, W - 120
    ft, lt = bloque(d, s["titulo"], "Bold", 58, ancho, 2, 42)
    fx, lx = bloque(d, s["texto"], "Regular", 30, ancho, 3, 24) if s.get("texto") else (None, [])
    alto = len(lt) * int(ft.size * 1.12) + (len(lx) * int(fx.size * 1.3) + 16 if lx else 0)
    y = H - 80 - alto
    if s.get("etiqueta"):
        etiqueta(d, m, y - 68, s["etiqueta"])
    y = escribir(d, (m, y), lt, ft, WHITE, 1.12)
    if lx:
        escribir(d, (m, y + 16), lx, fx, SOFT, 1.3)
    return im


def s_texto(s, i, n):
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    contador(d, i, n)
    m, ancho = 80, W - 160
    ft, lt = bloque(d, s["titulo"], "Bold", 76, ancho, 4, 52)
    fx, lx = bloque(d, s.get("texto", ""), "Regular", 36, ancho, 4, 26) if s.get("texto") else (None, [])
    alto = len(lt) * int(ft.size * 1.12) + (len(lx) * int(fx.size * 1.3) + 30 if lx else 0)
    y = (H - alto) // 2
    d.rounded_rectangle([m, y - 50, m + 90, y - 40], radius=5, fill=PILL)
    y = escribir(d, (m, y), lt, ft, WHITE, 1.12)
    if lx:
        escribir(d, (m, y + 30), lx, fx, SOFT, 1.3)
    return im


def s_lista(s, i, n):
    im = Image.new("RGB", (W, H), NAVY)
    alto_foto = int(H * 0.42)
    if s.get("foto"):
        f = degradado(foto_cubrir(s["foto"], W, alto_foto), int(alto_foto * 0.55), alto_foto)
        im.paste(f, (0, 0))
    d = ImageDraw.Draw(im)
    contador(d, i, n)
    m, ancho = 70, W - 140
    y = alto_foto + 30 if s.get("foto") else 200
    ft, lt = bloque(d, s["titulo"], "Bold", 60, ancho, 2, 44)
    y = escribir(d, (m, y), lt, ft, WHITE, 1.12) + 30
    fp = fuente("Medium", 36)
    for p in s.get("puntos", [])[:5]:
        lp = envolver(d, p, fp, ancho - 50)[:2]
        d.ellipse([m, y + 16, m + 14, y + 30], fill=PILL)
        y = escribir(d, (m + 40, y), lp, fp, WHITE, 1.25) + 22
    if y > H - 40:
        AVISOS.append(f"Lista muy larga en slide {i}")
    return im


def s_cta(s, i, n):
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    contador(d, i, n)
    y = 260
    y += logo(im, 300, centro=(W // 2, y)) + 70
    ft, lt = bloque(d, s["titulo"], "Bold", 62, W - 160, 2, 44)
    for l in lt:
        d.text(((W - d.textlength(l, font=ft)) // 2, y), l, font=ft, fill=WHITE)
        y += int(ft.size * 1.15)
    y += 25
    fp = fuente("Medium", 32)
    for p in s.get("puntos", [])[:4]:
        t = "•  " + p
        d.text(((W - d.textlength(t, font=fp)) // 2, y), t, font=fp, fill=WHITE)
        y += 52
    if s.get("boton"):
        y += 30
        fb = fuente("SemiBold", 36)
        tw = d.textlength(s["boton"], font=fb)
        x0 = (W - tw - 90) // 2
        d.rounded_rectangle([x0, y, x0 + tw + 90, y + 84], radius=42, fill=PILL)
        d.text((x0 + 45, y + 18), s["boton"], font=fb, fill=NAVY)
        y += 84
    if s.get("telefono"):
        y += 45
        fT = fuente("Medium", 34)
        d.text(((W - d.textlength(s["telefono"], font=fT)) // 2, y), s["telefono"], font=fT, fill=WHITE)
    pie = s.get("pie", "")
    if pie:
        fpie = fuente("Regular", 22)
        d.text(((W - d.textlength(pie, font=fpie)) // 2, H - 80), pie, font=fpie, fill=SOFT)
    return im


TIPOS = {"portada": s_portada, "foto": s_foto, "texto": s_texto, "lista": s_lista, "cta": s_cta}


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    guion, salida, prefijo = sys.argv[1:]
    data = json.load(open(guion, encoding="utf-8"))
    slides = data["slides"]
    os.makedirs(salida, exist_ok=True)
    n = len(slides)
    for i, s in enumerate(slides, 1):
        im = TIPOS[s["tipo"]](s, i, n)
        ruta = os.path.join(salida, f"{prefijo}_{i}.jpg")
        im.save(ruta, quality=92)
        print(ruta)
    for a in AVISOS:
        print("AVISO:", a, file=sys.stderr)


if __name__ == "__main__":
    main()
