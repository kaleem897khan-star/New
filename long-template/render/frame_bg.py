"""Animated frame background (mockup 1 style). Writes raw RGB 1920x1080 frames to stdout.
Usage: frame_bg.py <duration_sec> [fps]   — video area is left for ffmpeg to overlay."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np, sys, math
W, H = 1920, 1080
TS = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
DUR = float(sys.argv[1]); FPS = int(sys.argv[2]) if len(sys.argv) > 2 else 30
import os as _os
BASE = _os.path.dirname(_os.path.abspath(__file__))
FD = BASE + "/fonts/"
def F(w, s): return ImageFont.truetype(FD + f"Poppins-{w}.ttf", s)

# geometry (same as mockup 1)
VW, VH = 1617, 910; VX, VY = (W - VW) // 2, 50; R = 30
BX0, BY0, BX1, BY1 = VX + 180, 990, VX + VW - 180, 1046   # glass bar

SW, SH = 480, 270; K = W / SW   # low-res bg render scale
WHITE = np.array((255, 255, 255)); GOLD = np.array((255, 196, 0)); LBLUE = np.array((80, 160, 255))
CYAN = np.array((0, 190, 230)); PEACH = np.array((255, 214, 150)); DEEP = np.array((40, 90, 230))
PALETTE = [WHITE, GOLD, LBLUE, PEACH, CYAN, WHITE, DEEP, GOLD]

yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
base_top = np.array((12, 40, 110), np.float32); base_bot = np.array((4, 12, 40), np.float32)
BASE = (base_top[None, None] * (1 - yy[..., None] / SH) + base_bot[None, None] * (yy[..., None] / SH))

def col_at(phase):
    n = len(PALETTE); p = phase % n; i = int(p); f = p - i
    f = f * f * (3 - 2 * f)  # smoothstep
    return PALETTE[i] * (1 - f) + PALETTE[(i + 1) % n] * f

# blobs: (anchor x, y in full res, radius, orbit, speed, palette offset, strength)
BLOBS = [(200, 150, 520, 90, 0.11, 0.0, 0.55), (1750, 950, 560, 110, 0.09, 1.0, 0.60),
         (1650, 120, 380, 80, 0.13, 2.0, 0.55), (150, 1000, 420, 90, 0.10, 3.5, 0.45)]
CYCLE = 0.18  # palette steps per second (very slow)

def background(t):
    img = BASE.copy()
    for (ax, ay, r, orb, sp, off, st) in BLOBS:
        cx = (ax + orb * math.cos(t * sp * 2 * math.pi + off)) / K
        cy = (ay + orb * math.sin(t * sp * 2 * math.pi * 0.8 + off)) / K
        rr = r / K * (1 + 0.08 * math.sin(t * 0.5 + off))
        d2 = ((xx - cx) ** 2 + (yy - cy) ** 2) / (rr * rr)
        m = (np.exp(-d2 * 1.6) * st)[..., None]
        img = img * (1 - m) + col_at(t * CYCLE + off)[None, None] * m
    small = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    return small.resize((W, H), Image.BICUBIC)

# ---------- static layers (computed once)
def rr_mask(box, r, width=None):
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    if width: d.rounded_rectangle(box, r, outline=255, width=width)
    else: d.rounded_rectangle(box, r, fill=255)
    return m

shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(shadow).rounded_rectangle((VX, VY + 14, VX + VW, VY + VH + 14), R, fill=(0, 0, 0, 175))
shadow = shadow.filter(ImageFilter.GaussianBlur(26))
o = 4
bb = (VX - o, VY - o, VX + VW + o, VY + VH + o)
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(glow).rounded_rectangle(bb, R + o, outline=(255, 255, 255, 255), width=9)
g = np.array(glow.filter(ImageFilter.GaussianBlur(18))).astype(float); g[..., 3] = np.clip(g[..., 3] * 0.9, 0, 255)
glow = Image.fromarray(g.astype(np.uint8))
border = Image.new("RGBA", (W, H), (0, 0, 0, 0)); border.paste((255, 255, 255, 255), (0, 0), rr_mask(bb, R + o, 5))
static_under = Image.alpha_composite(Image.alpha_composite(shadow, glow), border)


import sys as _s; _s.path.insert(0, BASE)
from icons import whatsapp, instagram, facebook, tiktok, youtube
bar_mask = rr_mask((BX0, BY0, BX1, BY1), 28).crop((BX0, BY0, BX1 + 1, BY1 + 1))
bw, bh = BX1 - BX0 + 1, BY1 - BY0 + 1
glass = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); gd = ImageDraw.Draw(glass)
gd.rounded_rectangle((0, 0, bw - 1, bh - 1), 28, fill=(255, 255, 255, 46))
hl = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); ImageDraw.Draw(hl).rounded_rectangle((2, 2, bw - 3, bh // 2), 26, fill=(255, 255, 255, 40))
glass.alpha_composite(hl.filter(ImageFilter.GaussianBlur(6)))
gd = ImageDraw.Draw(glass)
gd.rounded_rectangle((0, 0, bw - 1, bh - 1), 28, outline=(255, 255, 255, 150), width=2)
gd.rounded_rectangle((3, 3, bw - 4, bh - 4), 25, outline=(255, 255, 255, 40), width=1)

ICON = 36
def content(parts):
    """parts: list of ('icon', img) | ('text', str, font) | ('div',)"""
    lay = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    widths = []
    for p in parts:
        if p[0] == "icon": widths.append(ICON)
        elif p[0] == "text": widths.append(d.textlength(p[1], font=p[2]))
        else: widths.append(36)
    gap = 14; total = sum(widths) + gap * (len(parts) - 1)
    x = (bw - total) / 2; cy = bh // 2
    sh = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    pos = []
    for p, w in zip(parts, widths):
        if p[0] == "text": sd.text((x + 1, cy + 2), p[1], font=p[2], fill=(0, 20, 60, 170), anchor="lm")
        pos.append(x); x += w + gap
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(2))); d = ImageDraw.Draw(lay)
    for p, x in zip(parts, pos):
        if p[0] == "icon": lay.alpha_composite(p[1], (int(x), cy - ICON // 2))
        elif p[0] == "text": d.text((x, cy), p[1], font=p[2], fill=(255, 255, 255), anchor="lm")
        else: d.line((x + 18, cy - 14, x + 18, cy + 14), fill=(255, 255, 255, 120), width=2)
    return lay
fB = F("SemiBold", 27); fL = F("Medium", 24); fX = F("ExtraBold", 27)
ITEMS = [
    content([("text", "Get Your VPS Just in 5 Minutes", fB), ("div",), ("icon", whatsapp(ICON)), ("text", "+92-313-8303-109", fB)]),
    content([("icon", instagram(ICON)), ("text", "Follow us on Instagram", fL), ("div",), ("text", "@rdpxcloud", fX)]),
    content([("icon", facebook(ICON)), ("text", "Like our Facebook Page", fL), ("div",), ("text", "@rdpxcloud", fX)]),
    content([("icon", tiktok(ICON)), ("text", "Follow us on TikTok", fL), ("div",), ("text", "@rdpxcloud", fX)]),
    content([("icon", youtube(ICON)), ("text", "Subscribe on YouTube", fL), ("div",), ("text", "RDP School", fX)]),
]
SLOT = 6.0; TR = 0.5
def ease(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)
def bar_content(t):
    k = int(t // SLOT); lt = t - k * SLOT
    lay = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    cur = ITEMS[k % len(ITEMS)]
    a_in = ease(lt / TR) if k > 0 else 1.0
    a_out = ease((SLOT - lt) / TR)
    a = min(a_in, a_out)
    dy = int((1 - a_in) * 18) if a_in < 1 else -int((1 - a_out) * 18)
    c = cur.copy(); arr = np.array(c); arr[..., 3] = (arr[..., 3] * a).astype(np.uint8)
    lay.alpha_composite(Image.fromarray(arr), (0, dy)) if 0 <= dy < bh else None
    if dy < 0:
        lay = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); lay.alpha_composite(Image.fromarray(arr).crop((0, -dy, bw, bh)), (0, 0))
    return lay

out = sys.stdout.buffer
for i in range(int(DUR * FPS)):
    t = TS + i / FPS
    bg = background(t).convert("RGBA")
    bg.alpha_composite(static_under)
    reg = bg.crop((BX0, BY0, BX1 + 1, BY1 + 1)).filter(ImageFilter.GaussianBlur(14))
    reg = Image.blend(reg, Image.new("RGBA", reg.size, (255, 255, 255, 255)), 0.10)
    reg.alpha_composite(glass); reg.alpha_composite(bar_content(t))
    bg.paste(reg, (BX0, BY0), bar_mask)
    out.write(bg.convert("RGB").tobytes())
