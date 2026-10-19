#!/bin/bash
# OCR every second of a video and list everything that may be CONFIDENTIAL, so it can be blurred before publishing:
#   IPv4 addresses (with port), e-mails, URLs/domains with paths or ports, "password/pass/pwd/key/token/secret" lines,
#   long random strings (keys, licence codes, passwords), phone numbers other than the RDP X Cloud number, card-like numbers.
# usage: find_sensitive.sh video.mp4 [extra_regex_file]   -> sensitive.txt (second<TAB>type<TAB>text)
# The owner decides what may stay public (e.g. a demo IP). Everything else is blurred with trim_blur.py.
set -e; V=$1; EXTRA=${2:-}; T=$(mktemp -d)
ffmpeg -v error -i "$V" -vf "fps=1,scale=2560:-1" "$T/f_%05d.png"
ls "$T"/f_*.png | xargs -P "$(nproc)" -I{} sh -c 'tesseract {} {}.ocr --psm 11 >/dev/null 2>&1 || true'
python3 - "$T" "$EXTRA" <<'PY'
import glob, os, re, sys
from collections import Counter
T, extra = sys.argv[1], sys.argv[2]
P = [("ip", r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d{2,5})?\b"),
     ("email", r"[\w.+-]+@[\w-]+\.[\w.]+"),
     ("url", r"(?:https?://|www\.)\S+|\b[\w-]+\.(?:com|net|org|io|xyz|pk|info|cloud|app|dev)(?:/\S+|:\d+)"),
     ("password", r"(?i)\b(?:password|passwd|pass|pwd|pin|key|token|secret|api[_ -]?key|licen[cs]e)\b\s*[:=]?\s*\S+"),
     ("random", r"\b(?=[A-Za-z0-9@#$%^&*!_-]*\d)(?=[A-Za-z0-9@#$%^&*!_-]*[A-Za-z])[A-Za-z0-9@#$%^&*!_-]{16,}\b"),
     ("phone", r"\+?\d[\d -]{9,}\d"),
     ("card", r"\b(?:\d[ -]?){13,19}\b")]
if extra and os.path.exists(extra):
    P += [("custom", l.strip()) for l in open(extra) if l.strip()]
OK = ["923138303109", "92-313-8303-109", "rdpxcloud.com"]          # public brand info, never blurred
rows = []
for f in sorted(glob.glob(T + "/f_*.png.ocr.txt")):
    sec = int(os.path.basename(f)[2:7]) - 1
    txt = open(f, errors="ignore").read()
    for kind, rx in P:
        for m in re.findall(rx, txt):
            s = (m if isinstance(m, str) else m[0]).strip()
            if s and not any(o in s.replace(" ", "") for o in OK):
                rows.append((sec, kind, s))
with open("sensitive.txt", "w") as o:
    for r in sorted(set(rows)):
        o.write("%d\t%s\t%s\n" % r)
for (k, s), c in Counter((k, s) for _, k, s in rows).most_common(40):
    print(f"{c:4d}s  {k:8s} {s}")
print("-> sensitive.txt   Ask the owner what may stay visible; blur the rest (trim_blur.py).")
PY
rm -rf "$T"
