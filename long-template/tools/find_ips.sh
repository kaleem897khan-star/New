#!/bin/bash
# OCR every second of a video and list every IPv4 that appears (to decide what must be blurred).
# usage: find_ips.sh video.mp4   -> ips.txt  (frame_second ip)   needs: tesseract
set -e; V=$1; T=$(mktemp -d)
ffmpeg -v error -i "$V" -vf "fps=1,scale=2560:-1" "$T/f_%05d.png"
ls "$T"/f_*.png | xargs -P "$(nproc)" -I{} sh -c 'tesseract {} stdout --psm 11 2>/dev/null | grep -oE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" | sed "s#^#$(basename {} .png | sed s/f_//) #"' | sort > ips.txt
awk '{print $2}' ips.txt | sort | uniq -c | sort -rn; rm -rf "$T"; echo "-> ips.txt (second = line number - 1). Blur every IP that is not the demo IP."
