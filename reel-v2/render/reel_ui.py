"""RDP School vertical reel (1080x1920) - approved "Design 6 / Caption Style" (2026-10-20).

Draws everything except the screen recording: animated background, header, title, video frame,
step caption, rotating "AD - OUR SERVICES" card, Like/Comment/Subscribe pop-ups and the social bar.
The video (+ highlight overlay) is composited by ffmpeg into the hole at VIDEO_BOX.

usage:  reel_ui.py <job_dir> <start_sec> <dur_sec>            -> raw RGB 1080x1920 frames on stdout (30 fps)
        reel_ui.py <job_dir> --endcard <dur_sec>              -> end card frames
        reel_ui.py <job_dir> --still <t> <out.png> [video.png] -> one preview frame
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
SHARED = os.path.normpath(os.path.join(BASE, "../../long-template/render"))
sys.path.insert(0, SHARED)
from icons import whatsapp, instagram, facebook, tiktok, youtube, material, svg_img  # noqa: E402

W, H, FPS = 1080, 1920, 30
VIDEO_BOX = (22, 318, 1058, 901)          # 1036 x 583 = full 16:9, nothing cropped
NAVY = (11, 15, 23); CYAN = (0, 168, 204); GREEN = (25, 212, 121); GOLD = (255, 196, 0); WHITE = (255, 255, 255)
_fc = {}
def F(w, s):
    if (w, s) not in _fc: _fc[(w, s)] = ImageFont.truetype(f"{SHARED}/fonts/Poppins-{w}.ttf", s)
    return _fc[(w, s)]
LOGO = Image.open(f"{SHARED}/assets/logo.png").convert("RGBA")
def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def eout(x): x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3
def back(x):
    x = min(max(x, 0.0), 1.0); c1 = 1.70158; c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def hexc(c): return "#%02x%02x%02x" % c[:3]
def alpha(im, a):
    if a >= 0.999: return im
    arr = np.array(im); arr[..., 3] = (arr[..., 3] * max(a, 0)).astype(np.uint8); return Image.fromarray(arr)

# ------------------------------------------------------------------ background (one theme, colours drift slowly)
SW, SH = 270, 480; K = W / SW
yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32)
_top, _bot = np.array((14, 44, 120), np.float32), np.array((4, 12, 40), np.float32)
BASEG = _top[None, None] * (1 - yy[..., None] / SH) + _bot[None, None] * (yy[..., None] / SH)
PAL = [np.array(c, np.float32) for c in [(255, 255, 255), (255, 196, 0), (80, 160, 255), (255, 214, 150), (0, 190, 230), (255, 255, 255), (40, 90, 230), (255, 196, 0)]]
def pal(p):
    n = len(PAL); p %= n; i = int(p); f = p - i; f = f * f * (3 - 2 * f); return PAL[i] * (1 - f) + PAL[(i + 1) % n] * f
BLOBS = [(140, 260, 470, 90, 0.10, 0.0, 0.55), (950, 1720, 520, 110, 0.08, 1.0, 0.60), (960, 360, 400, 80, 0.12, 2.0, 0.55),
         (120, 1560, 430, 90, 0.09, 3.5, 0.50), (540, 1100, 380, 120, 0.07, 5.0, 0.30)]
def background(t):
    img = BASEG.copy()
    for ax, ay, r, orb, sp, off, st in BLOBS:
        cx = (ax + orb * math.cos(t * sp * 2 * math.pi + off)) / K; cy = (ay + orb * math.sin(t * sp * 2 * math.pi * .8 + off)) / K
        rr = r / K * (1 + .08 * math.sin(t * .5 + off)); m = (np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (rr * rr) * 1.6) * st)[..., None]
        img = img * (1 - m) + pal(t * 0.18 + off)[None, None] * m
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).convert("RGBA")

# ------------------------------------------------------------------ drawing helpers
def shadow(img, box, r, a=170, blur=16, dy=8):
    l = Image.new("RGBA", img.size, (0, 0, 0, 0)); x0, y0, x1, y1 = box
    ImageDraw.Draw(l).rounded_rectangle((x0, y0 + dy, x1, y1 + dy), r, fill=(0, 0, 0, a)); img.alpha_composite(l.filter(ImageFilter.GaussianBlur(blur)))
def glow_border(img, box, r, col, w=3, blur=10, a=0.7):
    l = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(l).rounded_rectangle(box, r, outline=col + (255,), width=w + 4)
    g = np.array(l.filter(ImageFilter.GaussianBlur(blur))).astype(float); g[..., 3] = np.clip(g[..., 3] * 2 * a, 0, 255)
    img.alpha_composite(Image.fromarray(g.astype(np.uint8))); ImageDraw.Draw(img).rounded_rectangle(box, r, outline=col + (255,), width=w)
def panel(img, box, r, tint=(255, 255, 255), ta=40, border=(255, 255, 255, 120), bw=2):
    """translucent glass panel (no live blur needed: the background is already soft)"""
    l = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(l)
    d.rounded_rectangle(box, r, fill=tint + (ta,))
    x0, y0, x1, y1 = box; d.rounded_rectangle((x0 + 2, y0 + 2, x1 - 2, y0 + (y1 - y0) * .45), max(r - 2, 1), fill=(255, 255, 255, 16))
    if border: d.rounded_rectangle(box, r, outline=border, width=bw)
    img.alpha_composite(l)
def text(img, xy, s, f, col=WHITE, anchor="mm", sh=True):
    if sh:
        l = Image.new("RGBA", img.size, (0, 0, 0, 0)); ImageDraw.Draw(l).text((xy[0] + 1, xy[1] + 3), s, font=f, fill=(0, 0, 0, 170), anchor=anchor)
        img.alpha_composite(l.filter(ImageFilter.GaussianBlur(3)))
    ImageDraw.Draw(img).text(xy, s, font=f, fill=col, anchor=anchor)
def spaced(img, xy, s, f, col, sp=4):
    d = ImageDraw.Draw(img); tw = sum(d.textlength(c, font=f) for c in s) + sp * (len(s) - 1); x = xy[0] - tw / 2
    for c in s: d.text((x, xy[1]), c, font=f, fill=col, anchor="lm"); x += d.textlength(c, font=f) + sp
def layer(w, h): return Image.new("RGBA", (w, h), (0, 0, 0, 0))

# ------------------------------------------------------------------ static layer (header, title, video frame) - built once
def build_static(job):
    s = layer(W, H)
    # logo pill
    h = 66; w = int(h * 4.06); x, y = 40, 46; b = (x, y, x + w, y + h); r = h // 2
    shadow(s, b, r, 160, 12, 6)
    a = np.linspace(0, 1, w)[None, :, None]; g = np.repeat((np.array((8, 18, 45)) * (1 - a) + np.array((10, 70, 160)) * a).astype(np.uint8), h, 0)
    gi = Image.fromarray(g).convert("RGBA"); gi.putalpha(235); m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
    s.paste(gi, (x, y), m); glow_border(s, b, r, CYAN, 2, 7, .55)
    ih = int(h * .68); ic = LOGO.resize((int(LOGO.width * ih / LOGO.height), ih), Image.LANCZOS); s.alpha_composite(ic, (x + 16, y + (h - ih) // 2))
    text(s, (x + 16 + ic.width + 12, y + h // 2), "RDP X CLOUD", F("ExtraBold", 25), anchor="lm")
    # part pill
    f = F("ExtraBold", 27); pt = f"PART {job['part']}"; pw = int(ImageDraw.Draw(s).textlength(pt, font=f)) + 46; pb = (W - 40 - pw, 49, W - 40, 109)
    shadow(s, pb, 30, 140, 10, 5); ImageDraw.Draw(s).rounded_rectangle(pb, 30, fill=GREEN); text(s, ((pb[0] + pb[2]) // 2, 79), pt, f, NAVY, sh=False)
    # title block (kicker / title / subtitle)
    spaced(s, (W // 2, 152), job["kicker"].upper(), F("SemiBold", 21), (120, 220, 255), 5)
    ImageDraw.Draw(s).rounded_rectangle((W // 2 - 40, 172, W // 2 + 40, 175), 2, fill=GOLD)
    tf = F("ExtraBold", 56)
    while ImageDraw.Draw(s).textlength(job["title"], font=tf) > W - 90: tf = F("ExtraBold", tf.size - 2)
    text(s, (W // 2, 222), job["title"], tf, (240, 248, 255))
    text(s, (W // 2, 279), job["subtitle"], F("Medium", 25), (200, 225, 245))
    # video frame (shadow + white glow border); the video itself is drawn by ffmpeg
    x0, y0, x1, y1 = VIDEO_BOX; shadow(s, VIDEO_BOX, 26, 190, 22, 12)
    glow_border(s, (x0 - 3, y0 - 3, x1 + 3, y1 + 3), 29, WHITE, 4, 14, .5)
    hole = layer(W, H); ImageDraw.Draw(hole).rounded_rectangle(VIDEO_BOX, 26, fill=(0, 0, 0, 255))
    return s

# ------------------------------------------------------------------ step caption
CAP_Y = 1010
def caption_layer(step, label):
    c = layer(W, 260)
    text(c, (W // 2, 26), step.upper(), F("ExtraBold", 28), GOLD)
    words = label.split(); f = F("ExtraBold", 64); d = ImageDraw.Draw(c)
    lines, cur = [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=f) > W - 120 and cur: lines.append(cur); cur = wd
        else: cur = t
    lines.append(cur)
    if len(lines) > 2:
        f = F("ExtraBold", 52); lines = [" ".join(words[:len(words) // 2]), " ".join(words[len(words) // 2:])]
    for i, ln in enumerate(lines[:2]):
        text(c, (W // 2, 100 + i * 82), ln, f, WHITE if i == 0 and len(lines) > 1 else GOLD if len(lines) > 1 else WHITE)
    return c

# ------------------------------------------------------------------ ads: one service at a time, repeats when the list ends
def si(name, size, col): return svg_img(f"{SHARED}/icons/si/{name}.svg", size, col)
def mi(name, size, col): return material(name, size, hexc(col))
WIN_SVG = os.path.join(BASE, "windows.svg")
if not os.path.exists(WIN_SVG):
    open(WIN_SVG, "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M3 5.6l7.4-1v7.1H3zM11.5 4.4L21 3v8.7h-9.5zM3 12.7h7.4v7.1L3 18.8zM11.5 12.7H21V21l-9.5-1.4z"/></svg>')
SERVICES = [
    ("VPS / RDP", ((124, 58, 237), (34, 211, 238)), "Windows & Linux VPS", "Your own powerful server, ready in 5 minutes",
     [("m:computer", "Full Admin", (0, 164, 239)), ("m:bolt", "Ready in 5 Min", GOLD), ("m:shield", "Secure", (52, 211, 153)), ("m:support_agent", "24/7 Support", (56, 189, 248))]),
    ("CLOUD VPS", ((124, 58, 237), (34, 211, 238)), "Multiple Operating Systems", "Choose the OS you need",
     [("w:windows", "Windows", (0, 164, 239)), ("s:ubuntu", "Ubuntu", (233, 84, 32)), ("s:debian", "Debian", (215, 10, 83)), ("s:centos", "CentOS", (180, 80, 200)), ("s:almalinux", "AlmaLinux", (31, 154, 214))]),
    ("CLOUD VPS", ((124, 58, 237), (34, 211, 238)), "VPS RAM Options", "From small projects to heavy workloads",
     [("t:2GB", "RAM", (56, 189, 248)), ("t:4GB", "RAM", (34, 211, 238)), ("t:8GB", "RAM", (52, 211, 153)), ("t:16GB", "RAM", (167, 139, 250)), ("t:32GB", "RAM", (244, 114, 182))]),
    ("CLOUD VPS", ((124, 58, 237), (34, 211, 238)), "Multiple Server Locations", "Low ping servers around the world",
     [("t:USA", "Location", (56, 189, 248)), ("t:UK", "Location", (52, 211, 153)), ("t:PK", "Pakistan", (25, 212, 121)), ("t:IN", "India", (251, 146, 60)), ("m:public", "& More", (167, 139, 250))]),
    ("DEDICATED", ((249, 115, 22), (236, 72, 153)), "Dedicated Servers", "Full machine power, RAM up to 512 GB",
     [("t:64GB", "RAM", (251, 146, 60)), ("t:128GB", "RAM", (249, 115, 22)), ("t:256GB", "RAM", (236, 72, 153)), ("t:512GB", "RAM", (168, 85, 247))]),
    ("INSTALLATION", ((245, 158, 11), (239, 68, 68)), "Installation Services", "We set everything up for you",
     [("w:windows", "Windows", (0, 164, 239)), ("s:linux", "Linux Setup", (251, 191, 36)), ("s:cpanel", "Panels", (255, 108, 44)), ("m:language", "Web Hosting", (52, 211, 153)), ("m:build", "Custom", (167, 139, 250))]),
    ("BOTS", ((16, 185, 129), (6, 182, 212)), "Automation Bots", "Work 24/7 without you",
     [("s:whatsapp", "WhatsApp", (37, 211, 102)), ("s:telegram", "Telegram", (38, 165, 228)), ("m:chat", "Auto Replies", (244, 114, 182)), ("m:schedule", "24/7 Running", GOLD)]),
    ("WEBSITES", ((236, 72, 153), (139, 92, 246)), "Website Development", "Fast, modern and mobile friendly",
     [("m:web", "Business Sites", (244, 114, 182)), ("m:smartphone", "Mobile Friendly", (56, 189, 248)), ("m:palette", "Custom Design", (167, 139, 250))]),
    ("MOBILE APPS", ((6, 182, 212), (59, 130, 246)), "Mobile Apps", "Your idea as an Android app",
     [("m:phone_android", "App Development", (56, 189, 248)), ("s:googleplay", "Play Store", (52, 211, 153))]),
]
AD_BOX = (40, 1268, W - 40, 1548); AD_SEC = 9.0
def icon_for(spec, size, col):
    k, v = spec.split(":", 1)
    if k == "m": return mi(v, size, col)
    if k == "s": return si(v, size, hexc(col))
    if k == "w": return svg_img(WIN_SVG, size, hexc(col))
    return None
def ad_layer(i):
    tag, tc, title, sub, items = SERVICES[i % len(SERVICES)]
    x0, y0, x1, y1 = AD_BOX; w, h = x1 - x0, y1 - y0
    c = layer(w + 40, h + 60); o = 20; b = (o, o + 20, o + w, o + 20 + h)
    shadow(c, b, 28, 150, 16, 8); panel(c, b, 28, tint=(18, 22, 55), ta=185, border=None); glow_border(c, b, 28, GOLD, 2, 8, .45)
    # "AD • OUR SERVICES" ribbon on the top edge
    f = F("ExtraBold", 20); rt = "AD  •  OUR SERVICES"; rw = ImageDraw.Draw(c).textlength(rt, font=f) + 44
    rb = (o + w / 2 - rw / 2, o + 2, o + w / 2 + rw / 2, o + 40)
    ImageDraw.Draw(c).rounded_rectangle(rb, 19, fill=(255, 183, 3), outline=(255, 243, 196), width=2)
    c.alpha_composite(mi("campaign", 24, (26, 11, 0)), (int(rb[0] + 14), int(rb[1] + 7)))
    text(c, ((rb[0] + rb[2]) / 2 + 12, (rb[1] + rb[3]) / 2), rt, f, (26, 11, 0), sh=False)
    # service tag + title + subtitle
    tf = F("ExtraBold", 19); tw = ImageDraw.Draw(c).textlength(tag, font=tf) + 30; tb = (b[0] + 26, b[1] + 34, b[0] + 26 + tw, b[1] + 66)
    a = np.linspace(0, 1, int(tw))[None, :, None]; g = np.repeat((np.array(tc[0]) * (1 - a) + np.array(tc[1]) * a).astype(np.uint8), 32, 0)
    gi = Image.fromarray(g).convert("RGBA"); m = Image.new("L", gi.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, gi.width - 1, 31), 16, fill=255)
    c.paste(gi, (int(tb[0]), int(tb[1])), m); text(c, ((tb[0] + tb[2]) / 2, (tb[1] + tb[3]) / 2), tag, tf, sh=False)
    text(c, (tb[2] + 16, (tb[1] + tb[3]) / 2 - 1), title, F("ExtraBold", 31), anchor="lm")
    text(c, (b[0] + 28, b[1] + 92), sub, F("Medium", 23), (205, 215, 245), anchor="lm")
    # item tiles
    n = len(items); iy0 = b[1] + 120; ih = h - 140; gap = 12; iw = (w - 52 - gap * (n - 1)) / n; tiles = []
    for j, (spec, lab, col) in enumerate(items):
        tx = b[0] + 26 + j * (iw + gap); tb2 = (tx, iy0, tx + iw, iy0 + ih)
        panel(c, tb2, 18, ta=24, border=(255, 255, 255, 70)); ImageDraw.Draw(c).rounded_rectangle((tb2[0] + 14, tb2[1], tb2[2] - 14, tb2[1] + 5), 3, fill=col)
        cx = (tb2[0] + tb2[2]) / 2
        if spec.startswith("t:"):
            text(c, (cx, iy0 + ih * .40), spec[2:], F("ExtraBold", 36 if len(spec) < 7 else 30), col)
        else:
            isz = int(ih * .40); ic = icon_for(spec, isz, col); c.alpha_composite(ic, (int(cx - isz / 2), int(iy0 + ih * .40 - isz / 2)))
        lf = F("SemiBold", 19)
        while ImageDraw.Draw(c).textlength(lab, font=lf) > iw - 14: lf = F("SemiBold", lf.size - 1)
        text(c, (cx, iy0 + ih * .80), lab, lf); tiles.append(tb2)
    return c, tiles

# ------------------------------------------------------------------ Like / Comment / Subscribe pop-up (comes, gets clicked, leaves)
LCS_Y = 1572; LCS_DUR = 7.0; CLICKS = (1.6, 2.8, 4.0, 5.2)
TH = mi("thumb_up", 34, WHITE); TH_B = mi("thumb_up", 34, (62, 166, 255)); CM = mi("comment", 34, WHITE); CM_B = mi("comment", 34, (62, 166, 255))
BELL = mi("notifications_active", 34, WHITE)
def cursor():
    c = layer(36, 46); d = ImageDraw.Draw(c); p = [(2, 2), (2, 34), (11, 26), (17, 40), (23, 37), (17, 24), (29, 24)]
    d.polygon(p, fill=(0, 0, 0)); d.polygon([(x * .86 + 2, y * .86 + 2) for x, y in p], fill=WHITE); return c
CUR = cursor()
def lcs(img, t):
    e = min(eout(t / .45), eout((LCS_DUR - t) / .45))
    if e <= 0: return
    c1, cc, c2, c3 = CLICKS; s = back(t / .6)
    row = layer(W, 120); x0, w = 60, W - 120; hgt = 84
    shadow(row, (x0, 10, x0 + w, 10 + hgt), 42, 140, 12, 6); panel(row, (x0, 10, x0 + w, 10 + hgt), 42, tint=(15, 15, 22), ta=225, border=(255, 255, 255, 70))
    cy = 10 + hgt // 2
    def press(c_): return 1 - .12 * max(0, 1 - abs(t - c_) / .12)
    def pop(ic, on, c_, x):
        k = (1 + .25 * max(0, 1 - abs(t - c_ - .1) / .25)) * press(c_) if on else 1
        im = ic.resize((int(34 * k),) * 2, Image.LANCZOS); row.alpha_composite(im, (int(x - im.width / 2), int(cy - im.height / 2)))
    liked, comm, sub, bell = t > c1, t > cc, t > c2, t > c3
    pop(TH_B if liked else TH, liked, c1, x0 + 50); text(row, (x0 + 78, cy), "Like", F("SemiBold", 25), (62, 166, 255) if liked else WHITE, anchor="lm")
    ImageDraw.Draw(row).line((x0 + 160, cy - 22, x0 + 160, cy + 22), fill=(255, 255, 255, 60), width=2)
    pop(CM_B if comm else CM, comm, cc, x0 + 200); text(row, (x0 + 228, cy), "Comment", F("SemiBold", 25), (62, 166, 255) if comm else WHITE, anchor="lm")
    k = press(c2); mx = x0 + 560; hw, hh = 150 * k, 30 * k
    ImageDraw.Draw(row).rounded_rectangle((mx - hw, cy - hh, mx + hw, cy + hh), 30, fill=(70, 70, 70) if sub else (230, 33, 23))
    text(row, (mx, cy), "SUBSCRIBED" if sub else "SUBSCRIBE", F("ExtraBold", 25), (225, 225, 225) if sub else WHITE, sh=False)
    bx = x0 + w - 70
    if bell: ImageDraw.Draw(row).ellipse((bx - 30, cy - 30, bx + 30, cy + 30), fill=(70, 70, 70))
    ang = 20 * math.sin((t - c3) * 20) * max(0, 1 - (t - c3)) if bell else 0
    bl = BELL.rotate(ang, resample=Image.BICUBIC, center=(17, 4)); row.alpha_composite(bl, (bx - 17, cy - 17))
    keys = [(.5, (W - 40, cy + 100)), (c1 - .2, (x0 + 50, cy)), (cc - .2, (x0 + 200, cy)), (c2 - .2, (mx, cy)), (c3 - .2, (bx, cy)), (LCS_DUR, (bx, cy))]
    for (ka, pa), (kb, pb) in zip(keys, keys[1:]):
        if ka <= t <= kb:
            u = eout((t - ka) / (kb - ka) * 1.3); px, py = pa[0] + (pb[0] - pa[0]) * u, pa[1] + (pb[1] - pa[1]) * u; break
    else: px, py = keys[-1][1]
    clk = [c_ for c_ in CLICKS if 0 <= t - c_ < .35]
    if clk:
        r = 8 + 30 * eout((t - clk[0]) / .35); ImageDraw.Draw(row).ellipse((px - r, py - r, px + r, py + r), outline=(255, 255, 255, int(220 * (1 - (t - clk[0]) / .35))), width=3)
    if t > .5: row.alpha_composite(CUR, (int(px), int(min(py, 118 - 46))))
    if s < .999: row = row.resize((W, max(1, int(120 * s))), Image.LANCZOS)
    img.alpha_composite(alpha(row, e), (0, int(LCS_Y + (120 - row.height) / 2)))

# ------------------------------------------------------------------ social bar: WhatsApp number fixed, the rest rotates
SOC_Y = 1690; SOC_H = 64
SOCIALS = [(instagram, "@rdpxcloud"), (facebook, "@rdpxcloud"), (tiktok, "@rdpxcloud"), (youtube, "RDP School")]
def build_social_static():
    s = layer(W, SOC_H + 20); x0, x1 = 50, W - 50
    panel(s, (x0, 10, x1, 10 + SOC_H), SOC_H // 2, ta=38, border=(255, 255, 255, 120))
    s.alpha_composite(whatsapp(40), (x0 + 22, 10 + (SOC_H - 40) // 2))
    text(s, (x0 + 72, 10 + SOC_H // 2), "+92-313-8303-109", F("ExtraBold", 27), (125, 255, 180), anchor="lm")
    ImageDraw.Draw(s).line((x0 + 380, 26, x0 + 380, 10 + SOC_H - 16), fill=(255, 255, 255, 110), width=2)
    return s
SOC_ITEMS = []
for fn, t_ in SOCIALS:
    it = layer(560, SOC_H); it.alpha_composite(fn(38), (0, (SOC_H - 38) // 2)); text(it, (52, SOC_H // 2), t_, F("SemiBold", 27), anchor="lm"); SOC_ITEMS.append(it)
SOC_SLOT = 4.0
def social(img, t, static):
    img.alpha_composite(static, (0, SOC_Y - 10))
    k = int(t // SOC_SLOT); lt = t - k * SOC_SLOT; a = min(eout(lt / .4) if k > 0 else 1, eout((SOC_SLOT - lt) / .4))
    dy = int((1 - min(1, lt / .4)) * 16) if k > 0 and lt < .4 else 0
    img.alpha_composite(alpha(SOC_ITEMS[k % len(SOC_ITEMS)], a), (50 + 410, SOC_Y + dy))

# ------------------------------------------------------------------ frame composer
class Reel:
    def __init__(self, job_dir):
        self.job = json.load(open(os.path.join(job_dir, "job.json")))
        self.static = build_static(self.job); self.soc = build_social_static()
        self.caps = self.job["captions"]; self.cap_cache = {}; self.ad_cache = {}
        self.ad0 = self.job.get("ad_start", 0); self.lcs = self.job.get("lcs", [])
    def caption(self, t):
        cur = None
        for i, (a, b, st, lb) in enumerate(self.caps):
            if a <= t < b: cur = i
        return cur
    def frame(self, t):
        img = background(t); img.alpha_composite(self.static)
        # caption with cross-fade between steps
        i = self.caption(t)
        if i is not None:
            a, b, st, lb = self.caps[i]
            if i not in self.cap_cache: self.cap_cache[i] = caption_layer(st, lb)
            k = min(eout((t - a) / .45), eout((b - t) / .35)) if i > 0 or t > .3 else 1
            img.alpha_composite(alpha(self.cap_cache[i], k), (0, CAP_Y - 40 + int((1 - k) * 18)))
        # ad card: one service every AD_SEC seconds, repeats
        n = int(t // AD_SEC); lt = t - n * AD_SEC; idx = (self.ad0 + n) % len(SERVICES)
        if idx not in self.ad_cache: self.ad_cache[idx] = ad_layer(idx)
        card, tiles = self.ad_cache[idx]
        ka = min(eout((lt - .15) / .5), eout((AD_SEC - lt) / .4))
        if ka > 0:
            cc = card.copy()
            # tiles light up one after another
            for j, tb in enumerate(tiles):
                x = lt - (1.2 + j * 1.0); kk = min(ease(x / .22), 1 - ease((x - .78) / .22)) if 0 < x < 1 else 0
                if kk > 0:
                    l = layer(cc.width, cc.height); ImageDraw.Draw(l).rounded_rectangle(tb, 18, fill=(255, 220, 90, int(55 * kk)), outline=(255, 220, 90, int(255 * kk)), width=3); cc.alpha_composite(l)
            img.alpha_composite(alpha(cc, ka), (AD_BOX[0] - 20, AD_BOX[1] - 40 + int((1 - ka) * 30)))
        for L in self.lcs:
            if L <= t <= L + LCS_DUR: lcs(img, t - L)
        social(img, t, self.soc)
        return img
    def endcard(self, t, dur):
        img = background(1000 + t); j = self.job
        k = min(eout(t / .35), eout((dur - t) / .35))
        e = layer(W, H)
        text(e, (W // 2, 420), "Thank You", F("ExtraBold", 110), (230, 255, 245)); text(e, (W // 2, 545), "for Watching!", F("ExtraBold", 90), (230, 255, 245))
        last = j["part"] >= j["total_parts"]
        bb = (110, 680, W - 110, 860); shadow(e, bb, 40, 160); ImageDraw.Draw(e).rounded_rectangle(bb, 40, fill=(25, 212, 121))
        text(e, (W // 2, 730), "SERIES COMPLETE" if last else "TO BE CONTINUED", F("ExtraBold", 30), (4, 33, 15), sh=False)
        if not last: text(e, (W // 2, 800), f"in PART {j['part'] + 1}", F("ExtraBold", 64), WHITE, sh=False)
        text(e, (W // 2, 960), "Need a VPS / RDP?", F("ExtraBold", 50)); text(e, (W // 2, 1025), "Contact us anytime, we are 24/7 online", F("Medium", 30), (210, 225, 245))
        cb = (150, 1090, W - 150, 1190); panel(e, cb, 50, tint=(37, 211, 102), ta=235, border=None)
        e.alpha_composite(whatsapp(60), (cb[0] + 40, cb[1] + 20)); text(e, (cb[0] + 120, cb[1] + 50), "+92-313-8303-109", F("ExtraBold", 42), anchor="lm")
        text(e, (W // 2, 1250), "www.rdpxcloud.com", F("SemiBold", 34), (170, 225, 255))
        for n_, (fn, lb) in enumerate([(facebook, "RDP X Cloud"), (instagram, "@rdpxcloud"), (tiktok, "@rdpxcloud"), (youtube, "RDP School")]):
            col, row_ = n_ % 2, n_ // 2; bx = 70 + col * 480; by = 1320 + row_ * 110
            panel(e, (bx, by, bx + 460, by + 90), 26, ta=34); e.alpha_composite(fn(52), (bx + 22, by + 19)); text(e, (bx + 92, by + 45), lb, F("ExtraBold", 30), anchor="lm")
        img.alpha_composite(alpha(e, k)); return img

if __name__ == "__main__":
    job_dir = sys.argv[1]; R = Reel(job_dir); out = sys.stdout.buffer
    if sys.argv[2] == "--still":
        t = float(sys.argv[3]); im = R.frame(t)
        if len(sys.argv) > 5:
            v = Image.open(sys.argv[5]).convert("RGBA").resize((VIDEO_BOX[2] - VIDEO_BOX[0], VIDEO_BOX[3] - VIDEO_BOX[1]), Image.LANCZOS)
            m = Image.new("L", v.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, v.width - 1, v.height - 1), 26, fill=255); im.paste(v, VIDEO_BOX[:2], m)
        im.convert("RGB").save(sys.argv[4])
    elif sys.argv[2] == "--endcard":
        d = float(sys.argv[3])
        for i in range(int(round(d * FPS))): out.write(R.endcard(i / FPS, d).convert("RGB").tobytes())
    else:
        s, d = float(sys.argv[2]), float(sys.argv[3])
        for i in range(int(round(d * FPS))): out.write(R.frame(s + i / FPS).convert("RGB").tobytes())
