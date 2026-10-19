"""Prints the GitHub Actions matrix (JSON) for a job: equal segments of the input video."""
import json, subprocess, sys
job, n = sys.argv[1], int(sys.argv[2])
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", job + "/input.mp4"]))
fr = int(round(dur * 30)); step = -(-fr // n)
segs = []
for i in range(n):
    a, b = i * step, min(fr, (i + 1) * step)
    if a >= b: break
    segs.append({"i": f"{i:02d}", "start": round(a / 30, 4), "dur": round((b - a) / 30, 4)})
print(json.dumps({"include": segs}))
