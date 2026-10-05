#!/usr/bin/env python3
"""Plano de la casa de la familia 2 (Emma, Lily y Biscuit) -> familias/familia_2/plano.png"""
from PIL import Image, ImageDraw, ImageFont

S, M, W_FT, D_FT = 18, 60, 60, 92
Wd, Hd = W_FT * S + 2 * M, D_FT * S + 2 * M + 120
img = Image.new("RGB", (Wd, Hd), (250, 248, 243))
d = ImageDraw.Draw(img)
B = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
R = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
T = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
NAVY = (27, 48, 80)
top = M + 100


def P(x, y):  # y = 0 frente (abajo); crece hacia el patio (arriba)
    return (M + x * S, top + (D_FT - 14 - y) * S)


def rect(x0, y0, x1, y1, fill, label=None, sub=None, lw=4, col=NAVY):
    a, b = P(x0, y1), P(x1, y0)
    d.rectangle([a, b], fill=fill, outline=col, width=lw)
    if label:
        cx, cy = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        tw = d.textlength(label, font=B)
        d.text((cx - tw / 2, cy - (22 if sub else 12)), label, font=B, fill=NAVY)
        if sub:
            for k, line in enumerate(sub.split("\n")):
                tw = d.textlength(line, font=R)
                d.text((cx - tw / 2, cy + 8 + k * 20), line, font=R, fill=(80, 90, 110))


def dot(x, y, c, txt, dx=13):
    p = P(x, y)
    d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=c, outline="white", width=2)
    d.text((p[0] + dx, p[1] - 10), txt, font=R, fill=c)


d.text((M, M), "Casa de Emma, Lily y Biscuit · Naples, FL", font=T, fill=NAVY)
d.text((M, M + 44), "1 planta · 3 cuartos · 2 baños · garaje doble · porche trasero con malla · patio con huerto",
       font=R, fill=(80, 90, 110))

rect(0, 58, 60, 78, (232, 240, 232), "Patio trasero (cercado)", "huerto · columpio en el árbol · riego automático",
     lw=2, col=(120, 150, 120))
rect(22, 48, 60, 58, (240, 230, 210), "Porche trasero con malla", "hamaca · mesa · ventilador", lw=3)

rect(0, 0, 20, 22, (225, 225, 222), "Garaje doble", "SUV de Emma (izq.)\nbici de Lily y banco\nde trabajo (der.)")
rect(0, 22, 20, 30, (236, 236, 232), "Lavandería", "garaje ↔ cocina")
rect(0, 30, 22, 58, (245, 238, 225), "Cocina", "isla azul marino\ncon altavoz\ncomedero de Biscuit")
rect(20, 0, 34, 12, (240, 230, 210), "Porche delantero", "banco negro · timbre")
rect(20, 12, 34, 22, (245, 238, 225), "Entrada", "cerradura con teclado")
rect(22, 22, 44, 48, (250, 244, 232), "Sala", "sofá gris · chimenea\npersianas motorizadas\nventana de Biscuit")
rect(34, 0, 60, 12, (240, 236, 246), "Cuarto de Lily", "ventana al frente")
rect(34, 12, 44, 22, (236, 236, 236), "Pasillo")
rect(20, 22, 22, 30, (236, 236, 236))
rect(44, 12, 52, 22, (228, 238, 246), "Baño 2")
rect(52, 12, 60, 22, (228, 238, 246), "Baño 1")
rect(44, 22, 60, 34, (240, 236, 246), "Oficina / huéspedes", "Emma trabaja aquí")
rect(44, 34, 60, 48, (240, 236, 246), "Cuarto principal", "sale al porche")
rect(0, -12, 20, 0, (215, 215, 212), "Entrada de concreto", "SUV blanco de Emma", lw=2, col=(140, 140, 140))
rect(22, -12, 26, 0, (215, 215, 212), None, lw=2, col=(140, 140, 140))
d.line([P(0, -13), P(60, -13)], fill=(120, 120, 120), width=3)
tw = d.textlength("CALLE", font=B)
d.text(((Wd - tw) / 2, P(0, -13)[1] + 8), "CALLE", font=B, fill=(120, 120, 120))

dot(13, 36.5, (200, 120, 20), "altavoz")
dot(3, 33, (200, 120, 20), "comedero")
dot(3, 1.5, (180, 40, 40), "cámara")
dot(25, 1.5, (180, 40, 40), "timbre")
dot(24, 14, (40, 120, 60), "cerradura")
dot(35.5, 14, (200, 120, 20), "termostato")
dot(24, 27, (200, 120, 20), "cámara mascotas")
dot(6, 23.2, (40, 120, 60), "puerta al garaje")
dot(40, 57, (180, 40, 40), "cámara patio")

img.save("familias/familia_2/plano.png")
print(img.size)
