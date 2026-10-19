#!/bin/bash
# Joins segments + 2.5 s end card, mixes voice + click/bell sounds -> final reel.  usage: reel_finalize.sh <job_dir> <segs_dir> <out.mp4>
set -euo pipefail
JOB=$1; SEGS=$(cd "$2" && pwd); OUT=$3; R=$(cd "$(dirname "$0")" && pwd); END=2.5
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$JOB/input.mp4")
python3 "$R/reel_ui.py" "$JOB" --endcard $END | ffmpeg -v error -y -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - -c:v libx264 -crf 19 -preset fast -pix_fmt yuv420p -r 30 /tmp/endcard.mp4
{ ls "$SEGS"/seg_*.mp4 | sort | sed "s/.*/file '&'/"; echo "file '/tmp/endcard.mp4'"; } > /tmp/l.txt
ffmpeg -v error -y -f concat -safe 0 -i /tmp/l.txt -c copy /tmp/v.mp4
python3 "$R/reel_sfx.py" "$JOB" "$DUR" /tmp/sfx.wav
ffmpeg -v error -y -i /tmp/v.mp4 -i "$JOB/input.mp4" -i /tmp/sfx.wav \
  -filter_complex "[1:a][2:a]amix=inputs=2:normalize=0:duration=first,afade=t=out:st=$(python3 -c "print(max(0,$DUR-0.4))"):d=0.4,apad[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT"
