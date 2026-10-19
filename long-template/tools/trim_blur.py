"""Trim the raw recording and blur rectangles. usage: trim_blur.py raw.mkv out.mp4 START END blur.json
blur.json = [[t_start, t_end, x, y, w, h], ...]  (times of the RAW file, pixels of the raw 1280x720/1920x1080 frame)"""
import json, subprocess, sys
raw, out, s, e, bj = sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
boxes = json.load(open(bj)); n = len(boxes)
if n:
    fc = f"[0:v]split={n + 1}[base]" + "".join(f"[c{i}]" for i in range(n)) + ";"
    for i, (a, b, x, y, w, h) in enumerate(boxes): fc += f"[c{i}]crop={w}:{h}:{x}:{y},boxblur=14:3[b{i}];"
    prev = "base"
    for i, (a, b, x, y, w, h) in enumerate(boxes): fc += f"[{prev}][b{i}]overlay={x}:{y}:enable='between(t,{a},{b})'[o{i}];"; prev = f"o{i}"
    fc += f"[{prev}]trim=start={s}:end={e},setpts=PTS-STARTPTS[v];[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a]"
else:
    fc = f"[0:v]trim=start={s}:end={e},setpts=PTS-STARTPTS[v];[0:a]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a]"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "18",
                "-preset", "veryfast", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out], check=True)
print("wrote", out)
