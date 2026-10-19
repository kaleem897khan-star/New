"""Highlight annotations + Like/Comment/Subscribe, supersampled for smooth edges.
Outputs RGBA frames at OUT size (video box size inside the frame) to stdout.
Also exposes SFX_EVENTS for the sound-effects builder.
Usage: annotate2.py <dur> <t0>   (t0 = edited-video time of clip start)"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np, math, sys
import os as _os; BASE = _os.path.dirname(_os.path.abspath(__file__))
sys.path.insert(0, BASE)
from icons import material
VW, VH = 1280, 720            # source video coordinate space
OUT = tuple(int(v) for v in _os.environ.get("ANN_OUT", "1617x910").split("x"))   # output size (video box)
S = 2                         # supersample factor
CW, CH = VW * S, VH * S
FPS = 30
FD = BASE + "/fonts/"
_fc = {}
def F(w, s):
    k = (w, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(FD + f"Poppins-{w}.ttf", int(s * S))
    return _fc[k]
GOLD = (255, 196, 0); NAVY = (11, 15, 23); WHITE = (255, 255, 255); RED = (230, 33, 23)
def ease(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 3
def back(x):
    x = min(max(x, 0), 1); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def env(t, a, b, fi=0.3, fo=0.3):
    if t < a or t > b: return 0.0
    return min(ease((t - a) / fi), ease((b - t) / fo))
def P(*v): return tuple(x * S for x in v)

DRAW_T = 0.7   # seconds to draw a circle / arrow
exec(open(_os.environ["ANN_FILE"]).read()); ANN = ANN_FULL
LCS_LIST = LCS_TIMES   # set in the job annotations file
LCS_A, LCS_B = 140.0, 147.0
CLICKS = (1.6, 2.8, 4.0, 5.2)  # like, comment, subscribe, bell (relative to LCS_A)
SFX_EVENTS = [("pencil", a, DRAW_T) for (a, b, k, bx, l, s) in ANN] + \
             [("pop", a + 0.45, 0) for (a, b, k, bx, l, s) in ANN] + \
             [("click", L + c, 0) for L in LCS_LIST for c in CLICKS] + [("bell", L + CLICKS[3] + 0.05, 0) for L in LCS_LIST]

def smooth_line(d, pts, width, col):
    """thick polyline with round caps/joins (no gaps at corners)"""
    if len(pts) < 2: return
    d.line(pts, fill=col, width=width, joint="curve")
    r = width / 2
    for (x, y) in (pts[0], pts[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)

def stroke(im, pts, width, col, alpha):
    pts = [P(x, y) for x, y in pts]
    if len(pts) < 2: return
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    smooth_line(ImageDraw.Draw(sh), [(x + 2 * S, y + 3 * S) for x, y in pts], (width + 2) * S, (0, 0, 0, int(110 * alpha)))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3 * S)))
    smooth_line(ImageDraw.Draw(im), pts, width * S, col + (int(255 * alpha),))

def wobbly_ellipse(box, prog, seed):
    x0, y0, x1, y1 = box; px, py = 16, 12
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; rx, ry = (x1 - x0) / 2 + px, (y1 - y0) / 2 + py
    ph = np.random.default_rng(seed).uniform(0, 6.28, 3)
    n = 220; end = 1.12 * prog
    pts = []
    for i in range(int(n * end) + 1):
        a = -2.4 + 2 * math.pi * i / n
        w = 1 + 0.03 * math.sin(3 * a + ph[0]) + 0.015 * math.sin(5 * a + ph[1])
        grow = 1 + 0.06 * (i / n)
        pts.append((cx + rx * w * grow * math.cos(a), cy + ry * w * grow * math.sin(a)))
    return pts

def arrow_pts(box, prog):
    x0, y0, x1, y1 = box
    tip = (x0 - 12, (y0 + y1) / 2); start = (tip[0] - 120, tip[1] + 72); ctrl = (tip[0] - 112, tip[1] + 4)
    n = 80; pts = []
    for i in range(int(n * prog) + 1):
        u = i / n
        pts.append(((1 - u) ** 2 * start[0] + 2 * (1 - u) * u * ctrl[0] + u * u * tip[0],
                    (1 - u) ** 2 * start[1] + 2 * (1 - u) * u * ctrl[1] + u * u * tip[1]))
    return pts, tip, start

def draw_label(im, text, anchor_xy, side, a):
    f = F("SemiBold", 18); d = ImageDraw.Draw(im)
    tw = d.textlength(text, font=f) / S; pw, ph = tw + 30, 38
    x, y = anchor_xy
    bx, by = (x + 18, y - ph / 2) if side == "right" else (x - pw / 2, y + 14)
    bx = min(max(bx, 8), VW - pw - 8)
    s = back(a); al = min(a, 1); cxm, cym = bx + pw / 2, by + ph / 2
    box = (cxm - pw * s / 2, cym - ph * s / 2, cxm + pw * s / 2, cym + ph * s / 2)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(P(box[0] + 2, box[1] + 5, box[2] + 2, box[3] + 5), 19 * S, fill=(0, 0, 0, int(120 * al)))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6 * S)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(P(*box), 19 * S, fill=GOLD + (int(255 * al),))
    if s > 0.9: d.text(P(cxm, cym), text, font=f, fill=NAVY + (int(255 * al),), anchor="mm")

def annotations(im, T):
    for (a, b, kind, box, label, side) in ANN:
        e = env(T, a, b)
        if e <= 0: continue
        prog = ease((T - a) / DRAW_T)
        x0, y0, x1, y1 = box
        if kind == "circle":
            gl = Image.new("RGBA", im.size, (0, 0, 0, 0))
            ImageDraw.Draw(gl).rounded_rectangle(P(x0 - 6, y0 - 4, x1 + 6, y1 + 4), 8 * S, fill=GOLD + (int(45 * e * prog),))
            im.alpha_composite(gl)
            stroke(im, wobbly_ellipse(box, prog, int(a * 10)), 4, GOLD, e)
            anchor = (x1 + 14, (y0 + y1) / 2) if side == "right" else ((x0 + x1) / 2, y1 + 12)
        else:
            pulse = 1 + 0.06 * math.sin((T - a) * 6); pad = 5 * pulse
            d = ImageDraw.Draw(im)
            d.rounded_rectangle(P(x0 - pad, y0 - pad, x1 + pad, y1 + pad), 6 * S, outline=(0, 0, 0, int(120 * e)), width=6 * S)
            d.rounded_rectangle(P(x0 - pad, y0 - pad, x1 + pad, y1 + pad), 6 * S, outline=GOLD + (int(255 * e),), width=3 * S)
            pts, tip, start = arrow_pts(box, prog)
            stroke(im, pts, 5, GOLD, e)
            if prog > 0.95:
                ang = math.atan2(pts[-1][1] - pts[-6][1], pts[-1][0] - pts[-6][0]); L = 18
                head = [tip, (tip[0] - L * math.cos(ang - 0.5), tip[1] - L * math.sin(ang - 0.5)),
                        (tip[0] - L * math.cos(ang + 0.5), tip[1] - L * math.sin(ang + 0.5))]
                ImageDraw.Draw(im).polygon([P(*p) for p in head], fill=GOLD + (int(255 * e),))
            anchor = (start[0], start[1] - 4)
        la = env(T, a + 0.45, b, 0.35, 0.3)
        if la > 0: draw_label(im, label, anchor, side, la)

TH = material("thumb_up", 30 * S, "#FFFFFF"); TH_B = material("thumb_up", 30 * S, "#3EA6FF")
CM = material("comment", 30 * S, "#FFFFFF"); CM_B = material("comment", 30 * S, "#3EA6FF"); BELL = material("notifications_active", 30 * S, "#FFFFFF")
def cursor_img(scale=1.0):
    c = Image.new("RGBA", (int(36 * S * scale), int(46 * S * scale)), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    k = S * scale
    p = [(2 * k, 2 * k), (2 * k, 34 * k), (11 * k, 26 * k), (17 * k, 40 * k), (23 * k, 37 * k), (17 * k, 24 * k), (29 * k, 24 * k)]
    d.polygon(p, fill=(0, 0, 0));
    q = [(x * 0.86 + 3 * k * 0.6, y * 0.86 + 3 * k * 0.6) for x, y in p]
    d.polygon(q, fill=(255, 255, 255))
    return c
CUR, CUR_S = cursor_img(1.0), cursor_img(0.82)

def lcs(im, T):
    global LCS_A, LCS_B
    for L in LCS_LIST:
        if L <= T <= L + 7: LCS_A, LCS_B = L, L + 7
    e = env(T, LCS_A, LCS_B, 0.4, 0.4)
    if e <= 0: return
    t = T - LCS_A; x0, y0 = 40, 560
    s = back(t / 0.6); pw, ph = 470, 64
    card = Image.new("RGBA", P(pw + 20, ph + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(card)
    d.rounded_rectangle(P(10, 10, 10 + pw, 10 + ph), 32 * S, fill=(15, 15, 15, 225), outline=(255, 255, 255, 70), width=S)
    c1, cc, c2, c3 = CLICKS
    liked, commented, subbed, bell_on = t > c1, t > cc, t > c2, t > c3
    bx = 26
    def press(c): return 1 - 0.12 * max(0, 1 - abs(t - c) / 0.12)   # button squish on click
    pop = 1 + 0.25 * max(0, 1 - abs(t - c1 - 0.1) / 0.25) if liked else 1
    th = TH_B if liked else TH
    th2 = th.resize((int(30 * S * pop * press(c1)),) * 2, Image.LANCZOS)
    card.alpha_composite(th2, (int((bx + 15) * S - th2.width / 2), int(42 * S - th2.height / 2)))
    d.text(P(bx + 38, 42), "Like", font=F("SemiBold", 18), fill=(62, 166, 255) if liked else WHITE, anchor="lm")
    d.line(P(bx + 92, 26, bx + 92, 58), fill=(255, 255, 255, 60), width=S)
    cpop = 1 + 0.25 * max(0, 1 - abs(t - cc - 0.1) / 0.25) if commented else 1
    cm = CM_B if commented else CM
    cm2 = cm.resize((int(30 * S * cpop * press(cc)),) * 2, Image.LANCZOS)
    card.alpha_composite(cm2, (int((bx + 119) * S - cm2.width / 2), int(42 * S - cm2.height / 2)))
    d.text(P(bx + 140, 42), "Comment", font=F("SemiBold", 18), fill=(62, 166, 255) if commented else WHITE, anchor="lm")
    sx0 = bx + 240; sx1 = sx0 + 150; k = press(c2)
    mx, my = (sx0 + sx1) / 2, 42; hw, hh = 75 * k, 20 * k
    if subbed:
        d.rounded_rectangle(P(mx - hw, my - hh, mx + hw, my + hh), 20 * S, fill=(70, 70, 70))
        d.text(P(mx, my), "SUBSCRIBED", font=F("SemiBold", 15), fill=(220, 220, 220), anchor="mm")
    else:
        d.rounded_rectangle(P(mx - hw, my - hh, mx + hw, my + hh), 20 * S, fill=RED)
        d.text(P(mx, my), "SUBSCRIBE", font=F("ExtraBold", 16), fill=WHITE, anchor="mm")
    ang = 20 * math.sin((t - c3) * 20) * max(0, 1 - (t - c3) / 1.0) if bell_on else 0
    if bell_on: d.ellipse(P(sx1 + 12, 23, sx1 + 50, 61), fill=(70, 70, 70))
    card.alpha_composite(BELL.rotate(ang, resample=Image.BICUBIC, center=(15 * S, 4 * S)), P(sx1 + 16, 27))
    if s < 0.999 or e < 1:
        card = card.resize((max(1, int(card.width * s)), max(1, int(card.height * s))), Image.LANCZOS)
        arr = np.array(card); arr[..., 3] = (arr[..., 3] * e).astype(np.uint8); card = Image.fromarray(arr)
    im.alpha_composite(card, (int((x0 + (pw + 20) * (1 - s) / 2) * S), int((y0 + (ph + 20) * (1 - s) / 2) * S)))
    keys = [(0.6, (x0 + 300, y0 + 120)), (c1 - 0.2, (x0 + 40, y0 + 46)), (cc - 0.2, (x0 + 10 + bx + 119, y0 + 46)), (c2 - 0.2, (x0 + 10 + mx, y0 + 46)),
            (c3 - 0.2, (x0 + 10 + sx1 + 30, y0 + 46)), (6.6, (x0 + 10 + sx1 + 30, y0 + 46))]
    if t > 0.6:
        for (ka, pa), (kb, pb) in zip(keys, keys[1:]):
            if ka <= t <= kb:
                u = ease((t - ka) / (kb - ka) * 1.3)
                cx, cy = pa[0] + (pb[0] - pa[0]) * u, pa[1] + (pb[1] - pa[1]) * u; break
        else: cx, cy = keys[-1][1]
        clk = [c for c in CLICKS if 0 <= t - c < 0.35]
        if clk:
            r = 8 + 30 * ease((t - clk[0]) / 0.35); al = int(220 * (1 - (t - clk[0]) / 0.35))
            ImageDraw.Draw(im).ellipse(P(cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, al), width=3 * S)
        down = any(abs(t - c) < 0.1 for c in CLICKS)
        im.alpha_composite(CUR_S if down else CUR, P(int(cx), int(cy)))

def render(T):
    im = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    active = any(env(T, a, b) > 0 for (a, b, *_ ) in ANN) or any(env(T, L, L + 7, 0.4, 0.4) > 0 for L in LCS_LIST)
    if not active: return None
    annotations(im, T); lcs(im, T)
    return im.resize(OUT, Image.LANCZOS)

if __name__ == "__main__":
    DUR = float(sys.argv[1]); T0 = float(sys.argv[2])
    blank = bytes(OUT[0] * OUT[1] * 4)
    out = sys.stdout.buffer
    for i in range(int(round(DUR * FPS))):
        im = render(T0 + i / FPS)
        out.write(blank if im is None else im.tobytes())
