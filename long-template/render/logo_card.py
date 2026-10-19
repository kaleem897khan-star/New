"""Builds the approved RDP X CLOUD pill logo card (navy->blue glass, cyan glow border, white text).
Writes assets/logo_card.png (RGBA, full 1920x1080 canvas) + assets/logo_card_mask.png (glass blur area)."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
BASE = os.path.dirname(os.path.abspath(__file__))
W, H = 1920, 1080
VX, VY = 151, 50                     # video box top-left in the frame
X0, Y0, PW, PH = VX - 36, VY - 26, 390, 96
CYAN = (0, 168, 204); WHITE = (255, 255, 255)
LOGO = Image.open(BASE + "/assets/logo.png").convert("RGBA")
F = ImageFont.truetype(BASE + "/fonts/Poppins-ExtraBold.ttf", int(PH * 0.385))
b = (X0, Y0, X0 + PW, Y0 + PH); r = PH // 2
card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(sh).rounded_rectangle((b[0], b[1] + 8, b[2], b[3] + 8), r, fill=(0, 0, 0, 180))
card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
a = np.linspace(0, 1, PW)[None, :, None]
g = np.repeat((np.array((8, 18, 45)) * (1 - a) + np.array((10, 70, 160)) * a).astype(np.uint8), PH, 0)
gi = Image.fromarray(g).convert("RGBA"); gi.putalpha(235)
hl = Image.new("RGBA", (PW, PH), (0, 0, 0, 0)); ImageDraw.Draw(hl).rounded_rectangle((3, 3, PW - 4, PH // 2), r - 3, fill=(255, 255, 255, 34))
gi.alpha_composite(hl.filter(ImageFilter.GaussianBlur(5)))
m = Image.new("L", (PW, PH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, PW - 1, PH - 1), r, fill=255)
layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); layer.paste(gi, b[:2], m)
card.alpha_composite(layer)
gl = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).rounded_rectangle(b, r, outline=CYAN + (255,), width=7)
ga = np.array(gl.filter(ImageFilter.GaussianBlur(8))).astype(float); ga[..., 3] = np.clip(ga[..., 3] * 1.2, 0, 255)
card.alpha_composite(Image.fromarray(ga.astype(np.uint8)))
d = ImageDraw.Draw(card); d.rounded_rectangle(b, r, outline=CYAN + (255,), width=3)
ih = int(PH * 0.68); ic = LOGO.resize((int(LOGO.width * ih / LOGO.height), ih), Image.LANCZOS)
card.alpha_composite(ic, (b[0] + 24, b[1] + (PH - ih) // 2))
tx, ty = b[0] + 24 + ic.width + 14, b[1] + PH // 2
ts = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(ts).text((tx + 1, ty + 3), "RDP X CLOUD", font=F, fill=(0, 0, 0, 200), anchor="lm")
card.alpha_composite(ts.filter(ImageFilter.GaussianBlur(2.5)))
ImageDraw.Draw(card).text((tx, ty), "RDP X CLOUD", font=F, fill=WHITE, anchor="lm")
card.save(BASE + "/assets/logo_card.png")
mk = Image.new("L", (W, H), 0); ImageDraw.Draw(mk).rounded_rectangle(b, r, fill=255); mk.save(BASE + "/assets/logo_card_mask.png")
print("logo card at", b)
