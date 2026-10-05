#!/usr/bin/env python3
"""
Geo Homes LLC - generador automático de videos verticales (9:16).

Uso:
    python3 generar_video.py guion.json salida.mp4

El guion es un JSON con una lista de escenas. Tipos de escena:
  - "hook":  texto grande de apertura            {"type","text","dur"}
  - "text":  frase con encabezado pequeño        {"type","kicker","text","dur"}
  - "list":  título + puntos que aparecen uno a uno {"type","title","items","dur"}
  - "cta":   cierre con logo y botón             {"type","text","sub","button","dur"}
             opcional "phone": "(239) 204-6336" → muestra el teléfono dentro de la tarjeta
Las palabras entre *asteriscos* se resaltan con el color de acento.
Si el guion trae "audio": "ruta.mp3" (voz o música), se mezcla en el video.
"""
import json, math, random, subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/truetype/google-fonts"
F_BOLD = os.path.join(FONT_DIR, "Poppins-Bold.ttf")
F_MED = os.path.join(FONT_DIR, "Poppins-Medium.ttf")

NAVY = (23, 47, 76)
NAVY_DARK = (10, 22, 38)
ACCENT = (79, 209, 255)
WHITE = (255, 255, 255)
SAFE_X = 90  # margen lateral seguro


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_back(x):
    x = max(0.0, min(1.0, x))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------- logo ----------
def load_logos(path):
    src = Image.open(path).convert("RGB")
    arr = np.asarray(src).astype(np.float32)
    lum = arr.mean(axis=2)
    alpha = np.clip((232 - lum) * 3.0, 0, 255).astype(np.uint8)
    white = np.zeros((*alpha.shape, 4), np.uint8)
    white[..., :3] = 255
    white[..., 3] = alpha
    white_logo = Image.fromarray(white).crop(Image.fromarray(alpha).getbbox())
    navy = np.zeros((*alpha.shape, 4), np.uint8)
    navy[..., :3] = NAVY
    navy[..., 3] = alpha
    navy_logo = Image.fromarray(navy).crop(Image.fromarray(alpha).getbbox())
    return white_logo, navy_logo


# ---------- fondo animado (red de nodos, como el lobo del logo) ----------
class Background:
    def __init__(self, seed=7):
        rnd = random.Random(seed)
        g = np.linspace(0, 1, H)[:, None]
        base = (np.array(NAVY) * (1 - g) + np.array(NAVY_DARK) * g)
        self.base = Image.fromarray(np.repeat(base[:, None, :], W, axis=1).reshape(H, W, 3).astype(np.uint8))
        self.nodes = [(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(0, 6.28), rnd.uniform(20, 60)) for _ in range(46)]

    def frame(self, t):
        img = self.base.copy()
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        pts = [(x + math.sin(t * 0.5 + p) * a, y + math.cos(t * 0.4 + p) * a) for x, y, p, a in self.nodes]
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                dx, dy = pts[i][0] - pts[j][0], pts[i][1] - pts[j][1]
                dist = math.hypot(dx, dy)
                if dist < 300:
                    a = int(60 * (1 - dist / 300))
                    d.line([pts[i], pts[j]], fill=(120, 190, 255, a), width=2)
        for x, y in pts:
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill=(150, 215, 255, 110))
        img.paste(ov, (0, 0), ov)
        return img


# ---------- texto palabra por palabra ----------
def parse_words(text):
    out, accent = [], False
    for raw in text.split():
        w = raw
        start = w.startswith("*")
        if start:
            accent = True
            w = w[1:]
        end = w.endswith("*")
        if end:
            w = w[:-1]
        out.append((w, accent))
        if end:
            accent = False
    return out


def layout_words(text, fnt, max_w, line_gap=1.12):
    words = parse_words(text)
    space = fnt.getlength(" ")
    lines, cur, cur_w = [], [], 0
    for w, acc in words:
        ww = fnt.getlength(w)
        if cur and cur_w + space + ww > max_w:
            lines.append((cur, cur_w))
            cur, cur_w = [], 0
        cur_w = cur_w + (space if cur else 0) + ww
        cur.append((w, acc, ww))
    if cur:
        lines.append((cur, cur_w))
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * line_gap)
    placed = []
    for li, (ws, lw) in enumerate(lines):
        x = (W - lw) / 2
        for w, acc, ww in ws:
            placed.append({"w": w, "acc": acc, "x": x, "line": li, "ww": ww})
            x += ww + space
    return placed, lh, len(lines)


def render_word_sprites(placed, fnt):
    asc, desc = fnt.getmetrics()
    for p in placed:
        pad = 30
        im = Image.new("RGBA", (int(p["ww"]) + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        col = ACCENT if p["acc"] else WHITE
        # sombra suave
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad, pad + 6), p["w"], font=fnt, fill=(0, 0, 0, 150))
        sh = sh.filter(ImageFilter.GaussianBlur(8))
        im = Image.alpha_composite(sh, im)
        ImageDraw.Draw(im).text((pad, pad), p["w"], font=fnt, fill=col)
        p["img"], p["pad"] = im, pad


def draw_words(frame, placed, lh, top, t, start=0.1, step=0.11, fade=1.0):
    for i, p in enumerate(placed):
        k = (t - start - i * step) / 0.35
        if k <= 0:
            continue
        s = 0.55 + 0.45 * ease_back(k)
        a = ease_out(k) * fade
        im = p["img"]
        if s != 1:
            im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
        if a < 1:
            al = im.getchannel("A").point(lambda v: int(v * a))
            im = im.copy()
            im.putalpha(al)
        cx = p["x"] + p["ww"] / 2
        cy = top + p["line"] * lh + lh / 2
        frame.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def fade_for(t, dur, out=0.25):
    return 1.0 if t < dur - out else max(0.0, (dur - t) / out)


# ---------- escenas ----------
class Scene:
    def __init__(self, spec, logos):
        self.s = spec
        self.dur = float(spec.get("dur", 3))
        self.logos = logos
        typ = spec["type"]
        if typ in ("hook", "text"):
            size = 118 if typ == "hook" else 104
            self.fnt = font(F_BOLD, size)
            self.placed, self.lh, n = layout_words(spec["text"], self.fnt, W - SAFE_X * 2)
            render_word_sprites(self.placed, self.fnt)
            self.top = (H - n * self.lh) / 2 - 80
            if spec.get("kicker"):
                self.kfnt = font(F_MED, 46)
        elif typ == "list":
            self.tfnt = font(F_BOLD, 82)
            self.placed, self.lh, n = layout_words(spec["title"], self.tfnt, W - SAFE_X * 2)
            render_word_sprites(self.placed, self.tfnt)
            self.top = 330
            max_item = W - SAFE_X * 2 - 180
            size = 58
            while size > 36 and max(font(F_MED, size).getlength(i) for i in spec["items"]) > max_item:
                size -= 2
            self.ifnt = font(F_MED, size)
            self.list_top = self.top + n * self.lh + 90
        elif typ == "cta":
            self.fnt = font(F_BOLD, 84)
            self.placed, self.lh, n = layout_words(spec["text"], self.fnt, W - SAFE_X * 2)
            render_word_sprites(self.placed, self.fnt)
            self.sfnt = font(F_MED, 50)
            self.bfnt = font(F_BOLD, 56)
            self.pfnt = font(F_BOLD, 74)
            self.phone = spec.get("phone")
            self.head_top = 220 if self.phone else 250
            self.card_top = self.head_top + n * self.lh + (45 if self.phone else 60)

    def draw(self, frame, t):
        typ = self.s["type"]
        f = fade_for(t, self.dur) if typ != "cta" else 1.0
        if typ in ("hook", "text"):
            if self.s.get("kicker"):
                a = ease_out(t / 0.4) * f
                txt = self.s["kicker"].upper()
                tw = self.kfnt.getlength(txt)
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                d = ImageDraw.Draw(ov)
                y = self.top - 130
                d.rounded_rectangle([(W - tw) / 2 - 34, y - 14, (W + tw) / 2 + 34, y + 72], 43,
                                    fill=(*ACCENT, int(255 * a)))
                d.text(((W - tw) / 2, y), txt, font=self.kfnt, fill=(*NAVY_DARK, int(255 * a)))
                frame.paste(ov, (0, 0), ov)
            draw_words(frame, self.placed, self.lh, self.top, t, fade=f)
        elif typ == "list":
            draw_words(frame, self.placed, self.lh, self.top, t, fade=f)
            items = self.s["items"]
            gap = (self.dur - 1.3) / max(1, len(items))
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            for i, it in enumerate(items):
                k = ease_out((t - 0.6 - i * gap) / 0.4)
                if k <= 0:
                    continue
                a = int(255 * k * f)
                y = self.list_top + i * 175
                x = SAFE_X + (1 - k) * -120
                d.rounded_rectangle([x, y, W - SAFE_X, y + 140], 36, fill=(255, 255, 255, int(28 * k * f)),
                                    outline=(*ACCENT, int(120 * k * f)), width=3)
                cx, cy = x + 75, y + 70
                d.ellipse([cx - 36, cy - 36, cx + 36, cy + 36], fill=(*ACCENT, a))
                d.line([(cx - 16, cy + 2), (cx - 4, cy + 15), (cx + 18, cy - 12)], fill=(*NAVY_DARK, a), width=9,
                       joint="curve")
                d.text((x + 140, cy), it, font=self.ifnt, fill=(255, 255, 255, a), anchor="lm")
            frame.paste(ov, (0, 0), ov)
        elif typ == "cta":
            k = ease_back(t / 0.6)
            card_w, card_h = (800, 860) if self.phone else (800, 760)
            cx, cy = W / 2, self.card_top + card_h / 2
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
            s = 0.6 + 0.4 * k
            cw, ch = card_w * s, card_h * s
            d.rounded_rectangle([cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2], 60, fill=(255, 255, 255, 255))
            frame.paste(ov, (0, 0), ov)
            logo = self.logos[1]
            lw = int((450 if self.phone else 540) * s)
            lg = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
            frame.paste(lg, (int(cx - lg.width / 2), int(cy - ch / 2 + 60 * s)), lg)
            d = ImageDraw.Draw(frame)
            if t > 0.5:
                a = ease_out((t - 0.5) / 0.4)
                sub = self.s.get("sub", "")
                d.text((cx, cy + ch / 2 - 75), sub, font=self.sfnt, fill=tuple(int(c * a + 255 * (1 - a)) for c in NAVY),
                       anchor="mm")
                if self.phone:
                    d.text((cx, cy + ch / 2 - 165), self.phone, font=self.pfnt,
                           fill=tuple(int(c * a + 255 * (1 - a)) for c in NAVY), anchor="mm")
            # texto grande arriba de la tarjeta
            draw_words(frame, self.placed, self.lh, self.head_top, t, start=0.3)
            # botón con pulso
            if t > 0.9:
                k2 = ease_back((t - 0.9) / 0.5)
                pulse = 1 + 0.04 * math.sin((t - 0.9) * 7)
                btn = self.s.get("button", "Escríbenos hoy")
                bw = (self.bfnt.getlength(btn) + 120) * k2 * pulse
                bh = 130 * k2 * pulse
                by = cy + card_h / 2 + (115 if self.phone else 130)
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                od = ImageDraw.Draw(ov)
                od.rounded_rectangle([W / 2 - bw / 2, by - bh / 2, W / 2 + bw / 2, by + bh / 2], int(bh / 2),
                                     fill=(*ACCENT, 255))
                if k2 > 0.6:
                    od.text((W / 2, by), btn, font=self.bfnt, fill=NAVY_DARK, anchor="mm")
                frame.paste(ov, (0, 0), ov)


def render(script_path, out_path):
    spec = json.load(open(script_path, encoding="utf-8"))
    logo_path = spec.get("logo", os.path.join(HERE, "logo.png"))
    logos = load_logos(logo_path)
    scenes = [Scene(s, logos) for s in spec["scenes"]]
    total = sum(s.dur for s in scenes)
    bg = Background()
    wm = logos[0].resize((150, int(logos[0].height * 150 / logos[0].width)), Image.LANCZOS)
    wm.putalpha(wm.getchannel("A").point(lambda v: int(v * 0.85)))

    audio = spec.get("audio")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-"]
    if audio:
        cmd += ["-i", audio]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += ["-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    n = int(total * FPS)
    for fi in range(n):
        t = fi / FPS
        acc = 0
        for sc in scenes:
            if t < acc + sc.dur:
                cur, lt = sc, t - acc
                break
            acc += sc.dur
        else:
            cur, lt = scenes[-1], scenes[-1].dur
        frame = bg.frame(t)
        cur.draw(frame, lt)
        if cur.s["type"] != "cta":
            frame.paste(wm, (W - wm.width - 60, 80), wm)
        # barra de progreso
        d = ImageDraw.Draw(frame)
        d.rectangle([0, 0, W * (t / total), 10], fill=ACCENT)
        proc.stdin.write(frame.convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    print(f"OK {out_path}  ({total:.1f}s)")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2])
