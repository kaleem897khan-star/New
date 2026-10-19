"""Sound track for one reel: mouse clicks + bell for every Like/Comment/Subscribe pop-up. usage: reel_sfx.py <job_dir> <dur> <out.wav>"""
import json, os, sys, numpy as np, scipy.io.wavfile as wav
from scipy.signal import butter, sosfilt
SR = 48000; rng = np.random.default_rng(7)
CLICKS = (1.6, 2.8, 4.0, 5.2)
def hp(x, f): return sosfilt(butter(2, f, btype="high", fs=SR, output="sos"), x)
def click():
    n = int(.12 * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for off, amp, f in ((0, 1, 3200), (.055, .6, 3800)):
        i = int(off * SR); tt = t[:n - i]
        s[i:] += amp * (hp(rng.standard_normal(n - i), 2000) * np.exp(-tt / .0015) + .6 * np.sin(2 * np.pi * f * tt) * np.exp(-tt / .006) + .25 * np.sin(2 * np.pi * 900 * tt) * np.exp(-tt / .01))
    return s / np.max(np.abs(s)) * 10 ** (-21 / 20)
def bell():
    n = int(1.6 * SR); t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * 1568 * r * t) * np.exp(-t / d) for r, a, d in ((1, 1, .55), (2, .35, .35), (2.76, .25, .22), (5.4, .12, .12), (.5, .15, .6)))
    s *= np.minimum(1, t / .002); k = int(.16 * SR); s[k:] += s[:n - k] * .55
    return s / np.max(np.abs(s)) * 10 ** (-23 / 20)
job = json.load(open(os.path.join(sys.argv[1], "job.json"))); dur = float(sys.argv[2])
out = np.zeros(int(dur * SR) + SR)
for L in job.get("lcs", []):
    for c in CLICKS:
        s = click(); st = int((L + c) * SR); out[st:st + len(s)] += s[:len(out) - st]
    s = bell(); st = int((L + CLICKS[3] + .05) * SR); out[st:st + len(s)] += s[:len(out) - st]
out = out[:int(dur * SR)]
wav.write(sys.argv[3], SR, (np.clip(np.stack([out, out], 1), -1, 1) * 32767).astype(np.int16))
