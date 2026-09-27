#!/usr/bin/env python3
"""Dibuja el plano de la casa de la familia en español (casa/plano_casa_espanol.png)."""
from PIL import Image, ImageDraw, ImageFont

S, M, W_FT, D_FT = 18, 60, 60, 96
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


d.text((M, M), "Casa de Daniel, Mariana y Floyd · Naples, FL", font=T, fill=NAVY)
d.text((M, M + 44), "1 planta · 3 cuartos · 2 baños · garaje doble · piscina con lanai", font=R, fill=(80, 90, 110))

rect(0, 50, 60, 80, (232, 240, 232), None, lw=2, col=(120, 150, 120))
d.text((P(1, 79)[0], P(1, 79)[1] + 4), "Jaula de malla (screen enclosure)", font=R, fill=(90, 120, 90))
rect(16, 62, 44, 76, (170, 215, 235), "Piscina", "luces de piscina · bomba", lw=3, col=(60, 130, 170))
rect(0, 50, 60, 58, (240, 230, 210), "Lanai cubierto", "mesa, parrilla, ventiladores de techo", lw=3)

rect(0, 0, 22, 22, (225, 225, 222), "Garaje doble", "puerta automática al frente")
rect(0, 22, 12, 30, (236, 236, 232), "Lavandería", "garaje ↔ cocina")
rect(12, 22, 22, 30, (236, 236, 232), "Despensa")
rect(0, 30, 22, 50, (245, 238, 225), "Cocina", "isla con altavoz\nventana al lanai")
rect(22, 0, 32, 14, (245, 238, 225), "Entrada", "arco + puerta\nde madera")
rect(32, 0, 42, 14, (250, 244, 232), "Comedor", "ventana al frente")
rect(22, 14, 42, 50, (250, 244, 232), "Sala", "sofá gris · TV\npuertas corredizas\nal lanai")
rect(42, 0, 60, 14, (240, 236, 246), "Cuarto 2")
rect(42, 14, 52, 22, (228, 238, 246), "Baño 2")
rect(52, 14, 60, 22, (228, 238, 246), "Baño 1")
rect(42, 22, 60, 34, (240, 236, 246), "Cuarto 3")
rect(42, 34, 60, 50, (240, 236, 246), "Cuarto principal", "sale al lanai")
rect(0, -12, 22, 0, (215, 200, 185), "Entrada de adoquín", "camioneta de Daniel", lw=2, col=(150, 120, 100))
rect(24, -12, 30, 0, (215, 200, 185), None, lw=2, col=(150, 120, 100))
d.line([P(0, -13), P(60, -13)], fill=(120, 120, 120), width=3)
tw = d.textlength("CALLE", font=B)
d.text(((Wd - tw) / 2, P(0, -13)[1] + 8), "CALLE", font=B, fill=(120, 120, 120))

dot(16, 35, (200, 120, 20), "altavoz")
dot(3, 1.5, (180, 40, 40), "cámara")
dot(27, 1.5, (180, 40, 40), "timbre")
dot(34, 20, (200, 120, 20), "cama de Floyd")
dot(6, 23.2, (40, 120, 60), "puerta al garaje")
dot(32, 49, (40, 120, 60), "corredizas")

img.save("casa/plano_casa_espanol.png")
print(img.size)
