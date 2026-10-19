"""Synthesize a SFX track (48k stereo wav) for a clip.
Usage: sfx.py <dur> <t0> <out.wav>"""
import numpy as np, sys, scipy.io.wavfile as wav
from scipy.signal import butter, sosfilt
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from annotate import SFX_EVENTS
SR = 48000
DUR = float(sys.argv[1]); T0 = float(sys.argv[2]); OUTF = sys.argv[3]
rng = np.random.default_rng(7)
def db(x): return 10 ** (x / 20)
def bp(x, lo, hi, order=4): return sosfilt(butter(order, [lo, hi], btype="band", fs=SR, output="sos"), x)
def hp(x, f): return sosfilt(butter(2, f, btype="high", fs=SR, output="sos"), x)

def pencil(d):
    n = int((d + 0.15) * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    tex = bp(noise, 1800, 7000) * 0.7 + bp(noise, 600, 1800) * 0.3
    # grain texture: paper fibre micro-bumps
    grains = np.clip(bp(rng.standard_normal(n), 20, 90, 2) * 6, -1, 1) * 0.35 + 0.65
    # speed envelope: matches ease-out draw (fast start, slowing) + soft attack/release
    u = np.clip(t / d, 0, 1)
    speed = 3 * (1 - u) ** 2 * 0.75 + 0.25
    env = speed * np.minimum(1, t / 0.03) * np.clip((d + 0.12 - t) / 0.12, 0, 1)
    s = tex * grains * env
    return s / (np.sqrt(np.mean(s ** 2)) + 1e-9) * db(-41)

def click():
    n = int(0.12 * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for off, amp, f in ((0.0, 1.0, 3200), (0.055, 0.6, 3800)):
        i = int(off * SR); m = n - i; tt = t[:m]
        burst = hp(rng.standard_normal(m), 2000) * np.exp(-tt / 0.0015)
        ring = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.006) * 0.6
        body = np.sin(2 * np.pi * 900 * tt) * np.exp(-tt / 0.01) * 0.25
        s[i:] += amp * (burst + ring + body)
    return s / np.max(np.abs(s)) * db(-21)

def bell():
    n = int(1.6 * SR); t = np.arange(n) / SR; f0 = 1568.0
    s = np.zeros(n)
    for ratio, amp, dec in ((1.0, 1.0, 0.55), (2.0, 0.35, 0.35), (2.76, 0.25, 0.22), (5.4, 0.12, 0.12), (0.5, 0.15, 0.6)):
        s += amp * np.sin(2 * np.pi * f0 * ratio * t) * np.exp(-t / dec)
    s *= np.minimum(1, t / 0.002)
    # second softer strike (ding-ding)
    k = int(0.16 * SR); s2 = np.zeros(n); s2[k:] = s[:n - k] * 0.55
    s = s + s2
    return s / np.max(np.abs(s)) * db(-23)

out = np.zeros(int(DUR * SR) + SR)
for kind, t, d in SFX_EVENTS:
    if kind in ("pop", "pencil"): continue
    st = int((t - T0) * SR)
    if st < 0 or st >= len(out): continue
    s = pencil(d) if kind == "pencil" else click() if kind == "click" else bell()
    e = min(len(out), st + len(s)); out[st:e] += s[:e - st]
out = out[:int(DUR * SR)]
st = np.stack([out, out], 1)
wav.write(OUTF, SR, (np.clip(st, -1, 1) * 32767).astype(np.int16))
print("peak dB", round(20 * np.log10(np.max(np.abs(out)) + 1e-9), 1))
