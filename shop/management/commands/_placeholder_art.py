"""
Generates original, code-drawn placeholder imagery — not copied or traced from any
photograph or existing artwork. Each product gets a hand-coded line illustration of a
traditional Mithila/Madhubani motif (fish, peacock, tree of life, elephant, lotus, sun
and moon), picked to match the product's name, drawn with plain geometry (arcs, curves
built from point lists, polygons). These are generic, centuries-old folk-art motifs
common to the whole tradition, not a reproduction of any specific artist's painting.
Used by seed_demo so the demo catalogue doesn't ship with blank boxes; sellers replace
these with real photography from their own dashboard.
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


def _bg(size, bg_hex):
    w, h = size
    bg = _hex(bg_hex)
    img = Image.new("RGB", size, bg)
    draw = ImageDraw.Draw(img)
    top = _lerp(bg, (255, 255, 255), 0.12)
    bottom = _lerp(bg, (0, 0, 0), 0.05)
    for y in range(h):
        draw.line([(0, y), (w, y)], fill=_lerp(top, bottom, y / h))
    return img, draw


def _dot_ring(draw, cx, cy, r, fg, n=26, phase=0.0, size_a=5, size_b=3):
    for i in range(n):
        angle = 2 * math.pi * i / n + phase
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle) * 0.92
        s = size_a if i % 2 == 0 else size_b
        draw.ellipse((x - s, y - s, x + s, y + s), fill=fg)


def _frame(draw, w, h, fg):
    m = 34
    draw.rectangle((m, m, w - m, h - m), outline=fg, width=2)
    m2 = 44
    draw.rectangle((m2, m2, w - m2, h - m2), outline=fg, width=1)


def _smooth_path(draw, points, fg, width=3, closed=False):
    """Approximate a smooth curve through `points` with short Catmull-Rom segments."""
    pts = list(points)
    if closed:
        pts = [pts[-1]] + pts + [pts[0], pts[1]]
    else:
        pts = [pts[0]] + pts + [pts[-1]]
    line = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for t in [j / 10 for j in range(11)]:
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2*p0[0] - 5*p1[0] + 4*p2[0] - p3[0]) * t2 + (-p0[0] + 3*p1[0] - 3*p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2*p0[1] - 5*p1[1] + 4*p2[1] - p3[1]) * t2 + (-p0[1] + 3*p1[1] - 3*p2[1] + p3[1]) * t3)
            line.append((x, y))
    draw.line(line, fill=fg, width=width, joint="curve")
    return line


# --- individual motifs, each drawn centred at (cx, cy) with a characteristic size `r` ---

def _motif_fish(draw, cx, cy, r, fg):
    for flip in (-1, 1):
        ox = cx + flip * r * 0.55
        body = [(ox - r*0.5*flip, cy), (ox - r*0.2*flip, cy - r*0.28), (ox + r*0.35*flip, cy - r*0.12),
                (ox + r*0.5*flip, cy), (ox + r*0.35*flip, cy + r*0.12), (ox - r*0.2*flip, cy + r*0.28)]
        _smooth_path(draw, body, fg, width=3, closed=True)
        tail = [(ox - r*0.5*flip, cy), (ox - r*0.8*flip, cy - r*0.22), (ox - r*0.68*flip, cy), (ox - r*0.8*flip, cy + r*0.22), (ox - r*0.5*flip, cy)]
        draw.line(tail, fill=fg, width=2, joint="curve")
        draw.ellipse((ox + r*0.28*flip - 3, cy - r*0.08 - 3, ox + r*0.28*flip + 3, cy - r*0.08 + 3), fill=fg)
        for k in range(3):
            yy = cy - r*0.12 + k * r*0.12
            draw.arc((ox - r*0.15*flip - r*0.14, yy - r*0.1, ox - r*0.15*flip + r*0.14, yy + r*0.1), 200, 340, fill=fg, width=1)


def _motif_peacock(draw, cx, cy, r, fg):
    body_cx, body_cy = cx, cy + r * 0.32
    # tail: a clean fan of almond-shaped feathers, each tipped with a small "eye"
    n = 9
    for i in range(n):
        t = i / (n - 1)
        angle = math.radians(-100 + t * 200)
        length = r * (1.05 - 0.1 * abs(t - 0.5))
        tip = (body_cx + length * math.cos(angle), body_cy + r * 0.05 + length * math.sin(angle) * 0.85)
        base_l = (body_cx + r*0.05*math.cos(angle+1.4), body_cy + r*0.05*math.sin(angle+1.4)*0.85)
        base_r = (body_cx + r*0.05*math.cos(angle-1.4), body_cy + r*0.05*math.sin(angle-1.4)*0.85)
        mid = (body_cx + length*0.55*math.cos(angle + 0.12), body_cy + r*0.05 + length*0.55*math.sin(angle + 0.12)*0.85)
        mid2 = (body_cx + length*0.55*math.cos(angle - 0.12), body_cy + r*0.05 + length*0.55*math.sin(angle - 0.12)*0.85)
        _smooth_path(draw, [base_l, mid, tip, mid2, base_r], fg, width=1, closed=False)
        ex, ey = body_cx + length*0.78*math.cos(angle), body_cy + r*0.05 + length*0.78*math.sin(angle)*0.85
        draw.ellipse((ex-5, ey-5, ex+5, ey+5), outline=fg, width=1)
        draw.ellipse((ex-1.5, ey-1.5, ex+1.5, ey+1.5), fill=fg)
    # body
    draw.ellipse((body_cx - r*0.24, body_cy - r*0.3, body_cx + r*0.24, body_cy + r*0.28), outline=fg, width=2)
    # neck + head
    neck = [(body_cx + r*0.02, body_cy - r*0.26), (body_cx - r*0.1, body_cy - r*0.55), (body_cx + r*0.02, body_cy - r*0.82)]
    _smooth_path(draw, neck, fg, width=3)
    hx, hy = body_cx + r*0.02, body_cy - r*0.82
    draw.ellipse((hx - r*0.08, hy - r*0.08, hx + r*0.08, hy + r*0.08), outline=fg, width=2)
    for a in (-25, 0, 25):
        rad = math.radians(a - 90)
        draw.line((hx, hy - r*0.06, hx + r*0.1*math.cos(rad), hy - r*0.06 + r*0.1*math.sin(rad)), fill=fg, width=1)
    draw.polygon([(hx + r*0.08, hy + r*0.02), (hx + r*0.16, hy + r*0.05), (hx + r*0.07, hy + r*0.07)], outline=fg)
    # legs
    for dx in (-r*0.08, r*0.08):
        draw.line((body_cx + dx, body_cy + r*0.24, body_cx + dx, body_cy + r*0.42), fill=fg, width=2)


def _motif_elephant(draw, cx, cy, r, fg):
    bx, by = cx - r*0.05, cy + r*0.05  # body centre
    bw, bh = r*0.62, r*0.4
    # body + head as one continuous rounded silhouette
    body_box = (bx - bw*0.55, by - bh*0.65, bx + bw*0.55, by + bh*0.65)
    draw.rounded_rectangle(body_box, radius=int(bh*0.6), outline=fg, width=2)
    head_cx, head_cy = bx - bw*0.62, by - bh*0.15
    head_r = bh*0.55
    draw.ellipse((head_cx-head_r, head_cy-head_r, head_cx+head_r, head_cy+head_r), outline=fg, width=2)
    # ear
    ear_cx, ear_cy = head_cx - head_r*0.15, head_cy - head_r*0.35
    draw.ellipse((ear_cx-head_r*0.75, ear_cy-head_r*0.7, ear_cx+head_r*0.2, ear_cy+head_r*0.7), outline=fg, width=2)
    # trunk, curling down and slightly forward
    trunk = [
        (head_cx - head_r*0.75, head_cy + head_r*0.25),
        (head_cx - head_r*1.05, head_cy + head_r*0.9),
        (head_cx - head_r*0.8, head_cy + head_r*1.5),
        (head_cx - head_r*1.15, head_cy + head_r*1.95),
    ]
    _smooth_path(draw, trunk, fg, width=4)
    # tusk + eye
    draw.line((head_cx - head_r*0.6, head_cy + head_r*0.35, head_cx - head_r*0.35, head_cy + head_r*0.55), fill=fg, width=2)
    draw.ellipse((head_cx - head_r*0.05 - 2, head_cy - head_r*0.05 - 2, head_cx - head_r*0.05 + 2, head_cy - head_r*0.05 + 2), fill=fg)
    # legs, evenly spaced under the body
    leg_y0 = by + bh*0.6
    for fx in (-0.35, -0.05, 0.3, 0.5):
        lx = bx + bw*fx
        draw.rounded_rectangle((lx - bw*0.08, leg_y0, lx + bw*0.08, leg_y0 + bh*0.7), radius=4, outline=fg, width=2)
    # tail
    draw.line((bx + bw*0.55, by - bh*0.1, bx + bw*0.72, by + bh*0.15), fill=fg, width=2)
    draw.line((bx + bw*0.72, by + bh*0.15, bx + bw*0.68, by + bh*0.3), fill=fg, width=1)
    # blanket pattern (howdah-cloth dots) on the back
    for i in range(4):
        px = bx - bw*0.15 + i * bw*0.2
        draw.ellipse((px-2.5, by - bh*0.45 - 2.5, px+2.5, by - bh*0.45 + 2.5), fill=fg)


def _motif_tree(draw, cx, cy, r, fg):
    base = (cx, cy + r * 0.85)
    top = (cx, cy - r * 0.55)
    draw.line((base[0], base[1], top[0], top[1]), fill=fg, width=5)
    draw.line((base[0]-10, base[1]+10, base[0], base[1]-10), fill=fg, width=4)
    draw.line((base[0]+10, base[1]+10, base[0], base[1]-10), fill=fg, width=4)
    branches = []
    n = 10
    for i in range(n):
        t = i / (n - 1)
        along = base[1] + (top[1] - base[1]) * (0.15 + 0.8 * t)
        side = 1 if i % 2 == 0 else -1
        length = r * (0.55 - 0.32 * t)
        angle = math.radians(55 - 35 * t)
        ex = cx + side * length * math.cos(angle)
        ey = along - length * math.sin(angle) * 0.6
        draw.line((cx, along, ex, ey), fill=fg, width=2)
        draw.ellipse((ex - 9, ey - 9, ex + 9, ey + 9), outline=fg, width=1)
        for k in range(5):
            pa = 2 * math.pi * k / 5
            px, py = ex + 9*math.cos(pa), ey + 9*math.sin(pa)*0.9
            draw.ellipse((px-2, py-2, px+2, py+2), fill=fg)
        if i % 3 == 0:
            bx, by = ex + side*14, ey - 6
            draw.polygon([(bx, by), (bx+side*8, by+3), (bx, by+6)], outline=fg)
    draw.ellipse((top[0]-10, top[1]-10, top[0]+10, top[1]+10), outline=fg, width=2)


def _motif_lotus(draw, cx, cy, r, fg):
    for n, scale, rot in ((8, 1.0, 0), (8, 0.62, math.pi / 8)):
        for i in range(n):
            a = 2 * math.pi * i / n + rot
            tip = (cx + r*scale*math.cos(a), cy + r*scale*math.sin(a)*0.92)
            side1 = (cx + r*scale*0.4*math.cos(a - 0.28), cy + r*scale*0.4*math.sin(a - 0.28)*0.92)
            side2 = (cx + r*scale*0.4*math.cos(a + 0.28), cy + r*scale*0.4*math.sin(a + 0.28)*0.92)
            _smooth_path(draw, [side1, tip, side2], fg, width=2, closed=False)
    draw.ellipse((cx - r*0.18, cy - r*0.18*0.92, cx + r*0.18, cy + r*0.18*0.92), outline=fg, width=2)


def _motif_mandala(draw, cx, cy, r, fg):
    for rr in (r*0.68, r*0.5, r*0.32):
        draw.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), outline=fg, width=2)
    for i in range(4):
        a = math.pi/2*i + 0.2
        px, py = cx + r*0.5*math.cos(a), cy + r*0.5*math.sin(a)*0.92
        draw.ellipse((px-13, py-19, px+13, py+19), outline=fg, width=2)
    for i in range(28):
        a = 2*math.pi*i/28
        s = 6 if i % 2 == 0 else 3
        x, y = cx + r*0.85*math.cos(a), cy + r*0.85*math.sin(a)*0.92
        draw.ellipse((x-s, y-s, x+s, y+s), fill=fg)


def _motif_vessel(draw, cx, cy, r, fg):
    top_w, mid_w, base_w = r*0.34, r*0.5, r*0.28
    outline = [
        (cx-top_w, cy-r*0.75), (cx-top_w*1.1, cy-r*0.6), (cx-mid_w, cy-r*0.1), (cx-mid_w, cy+r*0.35),
        (cx-base_w, cy+r*0.7), (cx+base_w, cy+r*0.7), (cx+mid_w, cy+r*0.35), (cx+mid_w, cy-r*0.1),
        (cx+top_w*1.1, cy-r*0.6), (cx+top_w, cy-r*0.75),
    ]
    _smooth_path(draw, outline, fg, width=3, closed=False)
    draw.arc((cx-top_w, cy-r*0.83, cx+top_w, cy-r*0.69), 0, 360, fill=fg, width=2)
    for i in range(3):
        yy = cy - r*0.05 + i * r*0.18
        ww = mid_w * (0.9 - i*0.12)
        draw.arc((cx-ww, yy-10, cx+ww, yy+10), 200, 340, fill=fg, width=1)
    _dot_ring(draw, cx, cy + r*0.5, base_w*0.75, fg, n=14, size_a=3, size_b=2)


_MOTIFS = {
    "fish": _motif_fish, "peacock": _motif_peacock, "tree": _motif_tree,
    "elephant": _motif_elephant, "lotus": _motif_lotus, "mandala": _motif_mandala,
    "vessel": _motif_vessel,
}

_KEYWORDS = [
    (("fish",), "fish"),
    (("peacock", "bird"), "peacock"),
    (("tree", "life", "leaf", "leaves", "branch"), "tree"),
    (("elephant", "wood", "carv", "dhokra"), "elephant"),
    (("lotus", "motif", "panel", "print"), "lotus"),
    (("sun", "moon", "lamp", "pendant", "light", "mandala"), "mandala"),
    (("pot", "vase", "terracotta", "diya", "urn", "mask", "jar"), "vessel"),
]


def _pick_motif(name):
    n = name.lower()
    for keys, motif in _KEYWORDS:
        if any(k in n for k in keys):
            return motif
    order = ["mandala", "lotus", "vessel", "tree", "fish", "peacock", "elephant"]
    return order[_seed(name) % len(order)]


def product_placeholder(name, size=(900, 1125)):
    n = _seed(name)
    bg_hex, fg_hex = PALETTE[n % len(PALETTE)]
    fg = _hex(fg_hex)
    w, h = size
    img, draw = _bg(size, bg_hex)
    cx, cy = w // 2, int(h * 0.42)

    _dot_ring(draw, cx, cy, 235, fg, n=30, phase=(n // 7) % 5, size_a=5, size_b=3)
    for i in range(4):
        angle = math.pi / 2 * i + (n % 5) * 0.3
        px = cx + 165 * math.cos(angle)
        py = cy + 165 * math.sin(angle) * 0.94
        draw.ellipse((px - 12, py - 17, px + 12, py + 17), outline=fg, width=2)

    motif = _pick_motif(name)
    _MOTIFS[motif](draw, cx, cy, 118, fg)

    _frame(draw, w, h, fg)
    return img


def banner_placeholder(text, size=(1000, 750)):
    n = _seed(text)
    bg_hex, fg_hex = PALETTE[(n // 5) % len(PALETTE)]
    fg = _hex(fg_hex)
    w, h = size
    img, draw = _bg(size, bg_hex)
    cx, cy = w // 2, h // 2
    _dot_ring(draw, cx, cy, 330, fg, n=40, size_a=6, size_b=3)
    for rr in (260, 210, 160):
        draw.ellipse((cx-rr, cy-rr, cx+rr, cy+rr), outline=fg, width=2)
    motif = _pick_motif(text)
    _MOTIFS[motif](draw, cx, cy, 150, fg)
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
    head_r = int(w * 0.15)
    head_cy = int(h * 0.38)
    draw.ellipse((cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r), fill=fg)
    shoulder_w = int(w * 0.34)
    draw.pieslice((cx - shoulder_w, int(h * 0.55), cx + shoulder_w, int(h * 1.15)), 180, 360, fill=fg)
    r = int(w * 0.42)
    draw.ellipse((cx - r, h - r * 2 + 20, cx + r, h + 20), outline=fg, width=2)
    return img
