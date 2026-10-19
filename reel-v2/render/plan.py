import json, subprocess, sys
job, n = sys.argv[1], int(sys.argv[2])
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", job + "/input.mp4"]))
fr = int(round(dur * 30)); st = -(-fr // n); segs = []
for i in range(n):
    a, b = i * st, min(fr, (i + 1) * st)
    if a < b: segs.append({"i": f"{i:02d}", "start": round(a / 30, 4), "dur": round((b - a) / 30, 4)})
print(json.dumps({"include": segs}))
