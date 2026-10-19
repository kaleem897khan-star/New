#!/bin/bash
# Renders one segment [START, START+DUR) of the job video, split into SUB parallel pieces.
# usage: render_segment.sh <job_dir> <index> <start> <dur> <out.mp4> [sub=3]
set -euo pipefail
JOB=$1; IDX=$2; START=$3; DUR=$4; OUT=$5; SUB=${6:-3}
R=$(cd "$(dirname "$0")" && pwd)
export ANN_FILE="$JOB/annotations.py"
TMP=$(mktemp -d)
piece() {   # $1 = piece no, $2 = start, $3 = dur
  local n=$1 s=$2 d=$3 fifo="$TMP/ann_$1"
  mkfifo "$fifo"
  python3 "$R/annotate.py" "$d" "$s" > "$fifo" &
  python3 "$R/frame_bg.py" "$d" 30 "$s" | ffmpeg -v error -y \
    -f rawvideo -pix_fmt rgb24 -s 1920x1080 -r 30 -i - \
    -ss "$s" -t "$d" -i "$JOB/input.mp4" \
    -i "$R/assets/vmask.png" \
    -f rawvideo -pix_fmt rgba -s 1617x910 -r 30 -i "$fifo" \
    -i "$R/assets/logo_card.png" \
    -filter_complex "[1:v]setpts=PTS-STARTPTS,scale=1617:910:flags=lanczos[src];[src][3:v]overlay=0:0:format=auto,format=rgba[v];[2:v]format=gray[m];[v][m]alphamerge[vm];[0:v][vm]overlay=151:50:shortest=1[c];[c][4:v]overlay=0:0:format=auto,format=yuv420p[out]" \
    -map "[out]" -an -c:v libx264 -crf 18 -preset fast -r 30 "$TMP/p_$n.mp4"
  wait
}
python3 - "$START" "$DUR" "$SUB" > "$TMP/plan" <<'PY'
import sys
s, d, k = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
fr = round(d * 30); step = fr // k
for i in range(k):
    a = i * step; b = fr if i == k - 1 else (i + 1) * step
    print(i, round(s + a / 30, 4), round((b - a) / 30, 4))
PY
while read n s d; do piece "$n" "$s" "$d" & done < "$TMP/plan"
wait
for n in $(cut -d' ' -f1 "$TMP/plan"); do echo "file '$TMP/p_$n.mp4'"; done > "$TMP/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/list.txt" -c copy "$OUT"
rm -rf "$TMP"
echo "segment $IDX done -> $OUT"
