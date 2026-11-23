"""Zeichnet die ersten Entwürfe der Symbole (eigene Vektorzeichnungen).

Seit dem 23.11.2026 stammen die Symbole in icons/ vom Nutzer; dieses Skript wird für den Bau nicht mehr
gebraucht. Vorhandene Dateien überschreibt es nur mit --force.

Ausgabe: 102 x 98 px RGBA, wie die Lebensmittelsymbole im Spiel.
Aufruf: python tools/draw_icons.py <ausgabeordner> [--force]
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

W, H = 102, 98          # Zielgröße im Spiel
S = 4                   # Supersampling
CW, CH = W * S, H * S


def canvas():
    return Image.new("RGBA", (CW, CH), (0, 0, 0, 0))


def mask_of(draw_fn):
    m = Image.new("L", (CW, CH), 0)
    draw_fn(ImageDraw.Draw(m))
    return m


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


def gradient(direction, c0, c1, box, c_mid=None):
    """Farbverlauf über box (x0, y0, x1, y1); direction 'v' oder 'h'."""
    g = Image.new("RGBA", (CW, CH), c0)
    px = g.load()
    x0, y0, x1, y1 = box
    for y in range(CH):
        for x in range(CW):
            if direction == "v":
                t = (y - y0) / max(1, (y1 - y0))
            else:
                t = (x - x0) / max(1, (x1 - x0))
            t = min(1, max(0, t))
            if c_mid is not None:
                px[x, y] = lerp(c0, c_mid, t * 2) if t < .5 else lerp(c_mid, c1, (t - .5) * 2)
            else:
                px[x, y] = lerp(c0, c1, t)
    return g


def paste_fill(img, fill, mask):
    """fill: Farbe oder Bild; mask: L-Bild."""
    if isinstance(fill, tuple):
        layer = Image.new("RGBA", (CW, CH), fill)
    else:
        layer = fill
    img.paste(layer, (0, 0), ImageChops.multiply(mask, layer.getchannel("A")))


def shadow(img, ellipse, alpha=110, blur=10):
    m = mask_of(lambda d: d.ellipse(ellipse, fill=alpha))
    m = m.filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", (CW, CH), (0, 0, 0, 255))
    sh.putalpha(m)
    img.alpha_composite(sh)


# ---------------------------------------------------------------- Holzkiste
WOOD_L = (176, 148, 106, 255)
WOOD_M = (139, 112, 76, 255)
WOOD_D = (92, 72, 48, 255)
WOOD_X = (58, 44, 30, 255)


def wood_board(img, box, light=WOOD_L, dark=WOOD_M, grain_seed=0):
    x0, y0, x1, y1 = box
    m = mask_of(lambda d: d.rectangle(box, fill=255))
    paste_fill(img, gradient("v", light, dark, box), m)
    d = ImageDraw.Draw(img)
    rnd = random.Random(grain_seed)
    for _ in range(max(2, (y1 - y0) // 7)):
        y = rnd.randint(y0 + 3, y1 - 3)
        xa = rnd.randint(x0, x0 + (x1 - x0) // 3)
        xb = rnd.randint(x0 + 2 * (x1 - x0) // 3, x1)
        d.line([(xa, y), (xb, y + rnd.randint(-2, 2))], fill=(110, 86, 58, 140), width=2)
    d.rectangle(box, outline=WOOD_X, width=3)


def crate_back(img, top, bottom, left=40, right=368):
    """Rückwand und Innenraum der Kiste (wird vor dem Inhalt gezeichnet)."""
    wood_board(img, (left + 16, top - 26, right - 16, top + 14), WOOD_M, WOOD_D, 11)
    inner = mask_of(lambda d: d.rectangle((left + 16, top + 14, right - 16, bottom - 10), fill=255))
    paste_fill(img, (64, 50, 34, 255), inner)


def crate_front(img, top, bottom, left=40, right=368, boards=3):
    """Vorderseite mit Latten und Eckpfosten (wird nach dem Inhalt gezeichnet)."""
    h = (bottom - top) / boards
    gap = 7
    for i in range(boards):
        y0 = int(top + i * h)
        y1 = int(top + (i + 1) * h) - gap
        wood_board(img, (left, y0, right, y1), grain_seed=i + 1)
    d = ImageDraw.Draw(img)
    for x in (left, right - 26):
        post = (x, top - 6, x + 26, bottom)
        wood_board(img, post, (160, 132, 92, 255), WOOD_D, x)
        for yy in (top + 10, bottom - 18):
            d.ellipse((x + 9, yy - 4, x + 17, yy + 4), fill=(70, 70, 70, 255))


# ---------------------------------------------------------------- Spargel
def spear(img, base, tip, width, body0, body1, tip_col, seed):
    """Eine Spargelstange von base nach tip."""
    bx, by = base
    tx, ty = tip
    ang = math.atan2(ty - by, tx - bx)
    nx, ny = -math.sin(ang), math.cos(ang)
    length = math.hypot(tx - bx, ty - by)
    half = width / 2

    def pt(t, off):
        return (bx + (tx - bx) * t + nx * off, by + (ty - by) * t + ny * off)

    body = [pt(0, -half), pt(0.86, -half * .92), pt(0.86, half * .92), pt(0, half)]
    m = mask_of(lambda d: d.polygon(body, fill=255))
    xs = [p[0] for p in body]
    grad = gradient("h", body0, body1, (min(xs), 0, max(xs), 1), c_mid=lerp(body0, (235, 245, 210, 255), .35))
    paste_fill(img, grad, m)
    d = ImageDraw.Draw(img)
    d.polygon(body, outline=lerp(body1, (0, 0, 0, 255), .45))
    # Spitze: übereinanderliegende Schuppen
    head = [pt(0.80, -half * 1.05), pt(0.93, -half * .95), pt(1.0, 0), pt(0.93, half * .95), pt(0.80, half * 1.05)]
    d.polygon(head, fill=tip_col, outline=lerp(tip_col, (0, 0, 0, 255), .4))
    for t in (0.84, 0.89, 0.94):
        d.line([pt(t, -half * .8), pt(t + .03, 0), pt(t, half * .8)], fill=lerp(tip_col, (0, 0, 0, 255), .35), width=2)
    # Schuppen am Schaft
    rnd = random.Random(seed)
    for t in (0.35, 0.55, 0.7):
        t += rnd.uniform(-.04, .04)
        side = rnd.choice((-1, 1))
        a, b = pt(t, side * half * .9), pt(t + .05, side * half * .3)
        d.line([a, b], fill=lerp(body1, (0, 0, 0, 255), .3), width=2)


def draw_vegetables():
    img = canvas()
    shadow(img, (30, 330, 380, 385))
    top, bottom = 200, 370
    crate_back(img, top, bottom)
    rnd = random.Random(7)
    green0, green1 = (128, 168, 70, 255), (70, 110, 40, 255)
    white0, white1 = (238, 232, 205, 255), (196, 186, 150, 255)
    # zwei Bündel: hinten grün, vorne weiß, fächerförmig
    for bundle, (cx, c0, c1, tipc, n) in enumerate([
        (150, green0, green1, (96, 120, 60, 255), 9),
        (262, white0, white1, (170, 120, 150, 255), 9),
    ]):
        for i in range(n):
            f = (i - (n - 1) / 2) / ((n - 1) / 2)
            base = (cx + f * 34, bottom - 20)
            tip = (cx + f * 70 + rnd.uniform(-6, 6), 34 + abs(f) * 34 + rnd.uniform(-8, 8))
            spear(img, base, tip, 22, c0, c1, tipc, bundle * 100 + i)
        # Band um das Bündel
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((cx - 52, 196, cx + 52, 214), 6, fill=(178, 40, 36, 255), outline=(90, 20, 18, 255), width=2)
    crate_front(img, 236, bottom)
    return img


# ---------------------------------------------------------------- Bierdosen
def can(img, cx, top, bottom, rx, label, label_dark, seed):
    ry = rx * 0.32
    body = mask_of(lambda d: (d.rectangle((cx - rx, top, cx + rx, bottom), fill=255),
                              d.ellipse((cx - rx, bottom - ry, cx + rx, bottom + ry), fill=255)))
    metal = gradient("h", (120, 124, 128, 255), (96, 98, 102, 255), (cx - rx, 0, cx + rx, 1),
                     c_mid=(236, 238, 240, 255))
    paste_fill(img, metal, body)
    # Etikett
    l0, l1 = top + (bottom - top) * .18, bottom - (bottom - top) * .14
    lab = mask_of(lambda d: (d.rectangle((cx - rx, l0, cx + rx, l1), fill=255),
                             d.ellipse((cx - rx, l1 - ry, cx + rx, l1 + ry), fill=255)))
    lab = ImageChops.subtract(lab, mask_of(lambda d: d.ellipse((cx - rx, l0 - ry, cx + rx, l0 + ry), fill=255)))
    lab = ImageChops.add(lab, mask_of(lambda d: d.chord((cx - rx, l0 - ry, cx + rx, l0 + ry), 0, 180, fill=255)))
    paste_fill(img, gradient("h", label_dark, label_dark, (cx - rx, 0, cx + rx, 1), c_mid=label), lab)
    d = ImageDraw.Draw(img)
    # Emblem: helles Oval mit Bierkrug und Schaumkrone
    ey = (l0 + l1) / 2
    d.ellipse((cx - rx * .62, ey - rx * .7, cx + rx * .62, ey + rx * .7), fill=(244, 238, 220, 255),
              outline=(120, 80, 20, 255), width=2)
    mx0, mx1 = cx - rx * .3, cx + rx * .18
    my0, my1 = ey - rx * .3, ey + rx * .42
    d.rectangle((mx0, my0, mx1, my1), fill=(150, 92, 24, 255), outline=(80, 44, 10, 255), width=2)
    d.arc((mx1 - rx * .1, my0 + rx * .08, mx1 + rx * .22, my1 - rx * .12), 270, 90, fill=(80, 44, 10, 255), width=4)
    for k, fx in enumerate((-.32, -.14, .04, .2)):
        d.ellipse((cx + rx * fx - 6, my0 - 9 - (k % 2) * 3, cx + rx * fx + 6, my0 + 3), fill=(255, 255, 250, 255))
    # Glanzstreifen
    hl = mask_of(lambda dd: dd.rectangle((cx - rx * .45, top + 6, cx - rx * .3, bottom - 4), fill=110))
    paste_fill(img, (255, 255, 255, 255), hl)
    # Deckel
    d.ellipse((cx - rx, top - ry, cx + rx, top + ry), fill=(206, 210, 214, 255), outline=(80, 82, 86, 255), width=2)
    d.ellipse((cx - rx * .82, top - ry * .78, cx + rx * .82, top + ry * .78), fill=(176, 180, 186, 255))
    d.line([(cx - rx, top), (cx - rx, bottom)], fill=(60, 62, 66, 255), width=2)
    d.line([(cx + rx, top), (cx + rx, bottom)], fill=(60, 62, 66, 255), width=2)
    d.arc((cx - rx, bottom - ry, cx + rx, bottom + ry), 0, 180, fill=(60, 62, 66, 255), width=2)


def draw_canned_bread():
    img = canvas()
    shadow(img, (20, 320, 390, 385))
    gold, gold_d = (226, 178, 52, 255), (150, 104, 24, 255)
    # hintere Reihe
    for i, cx in enumerate((92, 178, 264)):
        can(img, cx, 70, 250, 40, gold, gold_d, i)
    # vordere Reihe
    for i, cx in enumerate((120, 206, 292)):
        can(img, cx, 120, 300, 40, gold, gold_d, 10 + i)
    wood_board(img, (14, 284, 396, 340), grain_seed=3)
    d = ImageDraw.Draw(img)
    for x in (22, 376):
        d.ellipse((x - 4, 308, x + 4, 316), fill=(70, 70, 70, 255))
    return img


# ---------------------------------------------------------------- Ananas
def pineapple(img, cx, cy, rx, ry, seed, tilt=0):
    rnd = random.Random(seed)
    # Krone
    d = ImageDraw.Draw(img)
    top = cy - ry
    for k in range(11):
        a = math.radians(-90 + (k - 5) * 15 + tilt + rnd.uniform(-5, 5))
        length = ry * (1.25 - abs(k - 5) * .1) * rnd.uniform(.85, 1.05)
        bx, by = cx + (k - 5) * 3, top + 8
        tx, ty = bx + math.cos(a) * length, by + math.sin(a) * length
        nx, ny = -math.sin(a) * 7, math.cos(a) * 7
        col = lerp((60, 118, 52, 255), (120, 168, 80, 255), rnd.random())
        d.polygon([(bx + nx, by + ny), (tx, ty), (bx - nx, by - ny)], fill=col, outline=(30, 64, 28, 255))
    # Frucht
    body = mask_of(lambda dd: dd.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255))
    grad = gradient("h", (214, 160, 52, 255), (132, 82, 22, 255), (cx - rx, 0, cx + rx, 1),
                    c_mid=(236, 196, 84, 255))
    paste_fill(img, grad, body)
    # Rautenmuster
    pat = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pat)
    step = rx * .55
    for i in range(-8, 9):
        off = i * step
        pd.line([(cx - rx * 2 + off, cy - ry * 1.2), (cx + rx * 2 + off, cy + ry * 1.2)], fill=(96, 60, 16, 220), width=3)
        pd.line([(cx + rx * 2 + off, cy - ry * 1.2), (cx - rx * 2 + off, cy + ry * 1.2)], fill=(96, 60, 16, 220), width=3)
    for i in range(-6, 7):
        for j in range(-6, 7):
            x = cx + i * step + (j % 2) * step / 2
            y = cy + j * step * .62
            pd.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(70, 96, 40, 230))
    pat.putalpha(ImageChops.multiply(pat.getchannel("A"), body))
    img.alpha_composite(pat)
    d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=(90, 56, 14, 255), width=3)


def draw_exotic_fruits():
    img = canvas()
    shadow(img, (30, 330, 380, 385))
    top, bottom = 214, 370
    crate_back(img, top, bottom)
    pineapple(img, 120, 196, 62, 82, 1, tilt=-8)
    pineapple(img, 292, 196, 62, 82, 2, tilt=8)
    pineapple(img, 206, 214, 66, 86, 3)
    crate_front(img, 250, bottom)
    return img


ICONS = {
    "Vegetables": draw_vegetables,
    "Canned Bread": draw_canned_bread,
    "Exotic Fruits": draw_exotic_fruits,
}


def render(name):
    big = ICONS[name]()
    return big.resize((W, H), Image.LANCZOS)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--force"]
    force = "--force" in sys.argv[1:]
    out = Path(args[0] if args else "entwuerfe")
    out.mkdir(parents=True, exist_ok=True)
    for name in ICONS:
        target = out / f"{name}.png"
        if target.exists() and not force:
            print("übersprungen (vorhanden, --force zum Überschreiben):", target)
            continue
        render(name).save(target)
        print("geschrieben:", target)
