"""Finds where the OBS screen ends at the start and where it re-appears at the end of a raw recording
(big frame changes in the first / last 4 s). usage: find_cuts.py raw.mkv  -> prints START END"""
import subprocess, sys, numpy as np
raw = sys.argv[1]
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw]))
def jumps(ss, t):
    b = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(ss), "-t", str(t), "-i", raw, "-vf", "scale=160:90,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    d = np.frombuffer(b, np.uint8).reshape(-1, 90, 160).astype(float); df = np.abs(np.diff(d, axis=0)).mean((1, 2))
    return [round(ss + (i + 1) / 30, 3) for i, v in enumerate(df) if v > 3]
a = jumps(0, 4); b = jumps(max(0, dur - 4), 4)
start = (max(a) + 0.1) if a else 0.0; end = (min(b) - 0.1) if b else dur
print(f"{start:.2f} {end:.2f}   # check both frames by eye before using")
