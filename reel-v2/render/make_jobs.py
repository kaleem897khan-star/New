"""Creates every reel job of one long video (owner split rule: max 90 s per reel incl. end card, equal, fewest reels).
usage: make_jobs.py <video.mp4> <long_annotations.py> <story.json> <job_prefix>
story.json = {"kicker": ..., "title": ..., "sections": [[start_sec, "Step 1", "Caption"], ...]}  (times of the trimmed long video)
Writes reel-v2/jobs/<prefix>-p<N>/{input.mp4, job.json, annotations.py}."""
import json, math, os, subprocess, sys
video, ann_file, story_file, prefix = sys.argv[1:5]
HERE = os.path.dirname(os.path.abspath(__file__)); JOBS = os.path.join(HERE, "..", "jobs")
dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video]))
MAX_VIDEO = 87.5   # owner rule 2026-10-20: a reel is at most 90 s INCLUDING the 2.5 s end card (Facebook Reels API limit)
n = max(1, math.ceil(dur / MAX_VIDEO)); L = dur / n
story = json.load(open(story_file)); secs = story["sections"]
g = {}; exec(open(ann_file).read(), g); ANN = g["ANN_FULL"]
AD_SEC, N_SERVICES = 9.0, 9
for p in range(n):
    a, b = p * L, (p + 1) * L
    caps = []
    for i, (s, st, lb) in enumerate(secs):
        e = secs[i + 1][0] if i + 1 < len(secs) else dur
        if e > a and s < b: caps.append([round(max(s, a) - a, 3), round(min(e, b) - a, 3), st, lb])
    caps[-1][1] = round(L + 0.1, 3)
    job = {"part": p + 1, "total_parts": n, "kicker": story["kicker"], "title": story["title"],
           "src_start": round(a, 3), "src_end": round(b, 3),
           "ad_start": (p * math.ceil(L / AD_SEC)) % N_SERVICES,          # rotation continues across parts
           "lcs": [3.0, round(L / 2 - 3, 1), round(L - 11, 1)], "captions": caps}
    d = os.path.join(JOBS, f"{prefix}-p{p + 1}"); os.makedirs(d, exist_ok=True)
    json.dump(job, open(os.path.join(d, "job.json"), "w"), indent=2)
    rows = [(round(max(s, a) - a, 3), round(min(e, b) - a, 3), k, box, lab, side) for (s, e, k, box, lab, side) in ANN if e > a and s < b]
    open(os.path.join(d, "annotations.py"), "w").write("# highlights for this reel (times relative to the reel clip)\nANN_FULL = " + repr(rows) + "\nLCS_TIMES = []\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-i", video, "-t", str(L), "-c:v", "libx264", "-crf", "16", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k", os.path.join(d, "input.mp4")], check=True)
    print(f"part {p + 1}/{n}: {a:.2f}-{b:.2f}s  ad_start={job['ad_start']}  captions={len(caps)}  highlights={len(rows)}")
