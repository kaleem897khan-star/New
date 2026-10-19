#!/bin/bash
# Joins all segments, mixes original voice + sound effects, writes final.mp4
# usage: finalize.sh <job_dir> <segments_dir> <out.mp4>
set -euo pipefail
JOB=$1; SEGS=$2; OUT=$3
R=$(cd "$(dirname "$0")" && pwd)
export ANN_FILE="$JOB/annotations.py"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$JOB/input.mp4")
python3 "$R/sfx.py" "$DUR" 0 /tmp/sfx.wav
ls "$(cd "$SEGS" && pwd)"/seg_*.mp4 | sort | sed "s/.*/file '&'/" > /tmp/segs.txt
ffmpeg -v error -y -f concat -safe 0 -i /tmp/segs.txt -c copy /tmp/video_only.mp4
ffmpeg -v error -y -i /tmp/video_only.mp4 -i "$JOB/input.mp4" -i /tmp/sfx.wav \
  -filter_complex "[1:a][2:a]amix=inputs=2:normalize=0:duration=first[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart -shortest "$OUT"
ffprobe -v error -show_entries format=duration,size -of default=nw=1 "$OUT"
