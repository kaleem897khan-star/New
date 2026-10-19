"""Builds colored brand icons (PNG RGBA) from simple-icons / material SVGs."""
import cairosvg, io, re
from PIL import Image, ImageDraw
import os as _os
BASE = _os.path.dirname(_os.path.abspath(__file__))
SI = BASE + "/icons/si/"
MAT = BASE + "/icons/mat/"

def svg_img(path, size, color):
    s = open(path).read()
    s = re.sub(r"<svg ", f'<svg fill="{color}" ', s, count=1)
    png = cairosvg.svg2png(bytestring=s.encode(), output_width=size, output_height=size)
    return Image.open(io.BytesIO(png)).convert("RGBA")

def rounded_sq(size, fill, r=0.24):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, size - 1, size - 1), int(size * r), fill=fill)
    return im

def instagram(size):
    # official-style gradient square with white glyph
    import numpy as np
    yy, xx = np.mgrid[0:size, 0:size] / size
    t = np.clip((xx * 0.4 + (1 - yy) * 0.8) / 1.2, 0, 1)[..., None]
    stops = [(0.0, (254, 218, 117)), (0.25, (250, 126, 30)), (0.5, (214, 41, 118)), (0.75, (150, 47, 191)), (1.0, (79, 91, 213))]
    out = np.zeros((size, size, 3))
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        m = ((t >= a) & (t <= b)).astype(float); f = (t - a) / (b - a)
        out += m * (np.array(ca) * (1 - f) + np.array(cb) * f)
    g = Image.fromarray(np.clip(out, 0, 255).astype("uint8")).convert("RGBA")
    mask = rounded_sq(size, (255, 255, 255, 255)).split()[3]
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0)); base.paste(g, (0, 0), mask)
    gl = svg_img(SI + "instagram.svg", int(size * 0.66), "#FFFFFF")
    o = (size - gl.width) // 2; base.alpha_composite(gl, (o, o)); return base

def facebook(size):
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(base).ellipse((size * 0.2, size * 0.15, size * 0.85, size * 0.98), fill=(255, 255, 255, 255))
    base.alpha_composite(svg_img(SI + "facebook.svg", size, "#0866FF")); return base

def whatsapp(size):
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(base).ellipse((size * 0.08, size * 0.08, size * 0.92, size * 0.92), fill=(255, 255, 255, 255))
    base.alpha_composite(svg_img(SI + "whatsapp.svg", size, "#25D366")); return base

def tiktok(size):
    base = rounded_sq(size, (0, 0, 0, 255))
    s = int(size * 0.62); o = (size - s) // 2; d = max(2, size // 28)
    base.alpha_composite(svg_img(SI + "tiktok.svg", s, "#25F4EE"), (o - d, o - d))
    base.alpha_composite(svg_img(SI + "tiktok.svg", s, "#FE2C55"), (o + d, o + d))
    base.alpha_composite(svg_img(SI + "tiktok.svg", s, "#FFFFFF"), (o, o)); return base

def youtube(size):
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(base).rectangle((size * 0.3, size * 0.3, size * 0.7, size * 0.7), fill=(255, 255, 255, 255))
    base.alpha_composite(svg_img(SI + "youtube.svg", size, "#FF0000")); return base

def material(name, size, color): return svg_img(MAT + name + ".svg", size, color)
