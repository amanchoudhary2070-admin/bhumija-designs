"""
Generates original, code-drawn placeholder imagery (not copied or traced from any
reference image): soft tinted backgrounds with a simple dot-ring medallion for
products, and an abstract silhouette bust for artisan portraits. Used only by
seed_demo so the demo catalogue doesn't ship with a blank grey box.
"""
import hashlib
import math

from PIL import Image, ImageDraw

PALETTE = [
    ("#e7c9c6", "#8a4a3c"),  # dusty rose / terracotta
    ("#d7cdb8", "#7c6a3f"),  # sand / bronze
    ("#c9d3c0", "#4f6b4a"),  # sage / forest
    ("#e3d3a8", "#a9762c"),  # mustard / ochre
    ("#cdd6dd", "#3f5a6e"),  # dusty blue / indigo
    ("#e6d6df", "#7a4560"),  # mauve / plum
]


def _seed(text):
    return int(hashlib.md5(text.encode()).hexdigest(), 16)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _hex(c):
    return tuple(int(c[i : i + 2], 16) for i in (1, 3, 5))


def product_placeholder(name, size=(900, 1125)):
    n = _seed(name)
    bg_hex, fg_hex = PALETTE[n % len(PALETTE)]
    bg, fg = _hex(bg_hex), _hex(fg_hex)
    w, h = size
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)

    # soft vertical gradient
    top = _lerp(bg, (255, 255, 255), 0.10)
    bottom = _lerp(bg, (0, 0, 0), 0.06)
    for y in range(h):
        draw.line([(0, y), (w, y)], fill=_lerp(top, bottom, y / h))

    cx, cy = w // 2, int(h * 0.42)
    rng = (n // 7) % 5

    # concentric medallion rings
    for i, r in enumerate((170, 130, 92)):
        bbox = (cx - r, cy - r, cx + r, cy + r)
        draw.ellipse(bbox, outline=fg, width=2)

    # dot-work ring (a common folk-craft motif: a border of small dots)
    dot_r = 220
    dots = 28
    for i in range(dots):
        angle = 2 * math.pi * i / dots + rng
        x = cx + dot_r * math.cos(angle)
        y = cy + dot_r * math.sin(angle) * 0.94
        size_d = 5 if i % 2 == 0 else 3
        draw.ellipse((x - size_d, y - size_d, x + size_d, y + size_d), fill=fg)

    # four petal accents
    for i in range(4):
        angle = math.pi / 2 * i + rng * 0.3
        px = cx + 150 * math.cos(angle)
        py = cy + 150 * math.sin(angle) * 0.94
        draw.ellipse((px - 14, py - 20, px + 14, py + 20), outline=fg, width=2)

    # corner border frame (evokes a hand-bordered textile / painting mat)
    m = 34
    draw.rectangle((m, m, w - m, h - m), outline=fg, width=2)
    m2 = 44
    draw.rectangle((m2, m2, w - m2, h - m2), outline=fg, width=1)

    return img


def banner_placeholder(text, size=(1000, 750)):
    """A softer, wider version of the product medallion for hero/promo banners."""
    n = _seed(text)
    bg_hex, fg_hex = PALETTE[(n // 5) % len(PALETTE)]
    bg, fg = _hex(bg_hex), _hex(fg_hex)
    w, h = size
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    top = _lerp(bg, (255, 255, 255), 0.12)
    bottom = _lerp(bg, (0, 0, 0), 0.05)
    for y in range(h):
        draw.line([(0, y), (w, y)], fill=_lerp(top, bottom, y / h))
    cx, cy = w // 2, h // 2
    for r in (260, 210, 160, 60):
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=fg, width=2)
    dots = 40
    for i in range(dots):
        angle = 2 * math.pi * i / dots
        x = cx + 330 * math.cos(angle)
        y = cy + 330 * math.sin(angle) * 0.9
        size_d = 6 if i % 3 == 0 else 3
        draw.ellipse((x - size_d, y - size_d, x + size_d, y + size_d), fill=fg)
    for i in range(6):
        angle = math.pi / 3 * i
        px = cx + 205 * math.cos(angle)
        py = cy + 205 * math.sin(angle) * 0.9
        draw.ellipse((px - 16, py - 24, px + 16, py + 24), outline=fg, width=2)
    return img


def artisan_placeholder(name, size=(500, 500)):
    n = _seed(name)
    bg_hex, fg_hex = PALETTE[(n // 3) % len(PALETTE)]
    bg, fg = _hex(bg_hex), _hex(fg_hex)
    w, h = size
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        draw.line([(0, y), (w, y)], fill=_lerp(_lerp(bg, (255, 255, 255), 0.08), bg, t))

    cx = w // 2
    # simple abstract bust: head circle + shoulder arc (generic, non-identifying silhouette)
    head_r = int(w * 0.15)
    head_cy = int(h * 0.38)
    draw.ellipse((cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r), fill=fg)
    shoulder_w = int(w * 0.34)
    draw.pieslice((cx - shoulder_w, int(h * 0.55), cx + shoulder_w, int(h * 1.15)), 180, 360, fill=fg)
    r = int(w * 0.42)
    draw.ellipse((cx - r, h - r * 2 + 20, cx + r, h + 20), outline=fg, width=2)
    return img
