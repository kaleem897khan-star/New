#!/bin/bash
# Renders reel frames [START, START+DUR) of a job in SUB parallel pieces.  usage: reel_segment.sh <job_dir> <idx> <start> <dur> <out.mp4> [sub=4]
set -euo pipefail
JOB=$1; IDX=$2; START=$3; DUR=$4; OUT=$5; SUB=${6:-4}
R=$(cd "$(dirname "$0")" && pwd); L=$(cd "$R/../../long-template/render" && pwd)
export ANN_FILE="$JOB/annotations.py" ANN_OUT=1036x583
TMP=$(mktemp -d)
piece() {
  local n=$1 s=$2 d=$3 fifo="$TMP/ann_$1"; mkfifo "$fifo"
  python3 "$L/annotate.py" "$d" "$s" > "$fifo" &
  python3 "$R/reel_ui.py" "$JOB" "$s" "$d" | ffmpeg -v error -y \
    -f rawvideo -pix_fmt rgb24 -s 1080x1920 -r 30 -i - \
    -ss "$s" -t "$d" -i "$JOB/input.mp4" -i "$R/vmask_reel.png" \
    -f rawvideo -pix_fmt rgba -s 1036x583 -r 30 -i "$fifo" \
    -filter_complex "[1:v]setpts=PTS-STARTPTS,scale=1036:583:flags=lanczos[src];[src][3:v]overlay=0:0:format=auto,format=rgba[v];[2:v]format=gray[m];[v][m]alphamerge[vm];[0:v][vm]overlay=22:318:shortest=1,format=yuv420p[out]" \
    -map "[out]" -an -c:v libx264 -crf 19 -preset fast -r 30 "$TMP/p_$n.mp4"
  wait
}
python3 - "$START" "$DUR" "$SUB" > "$TMP/plan" <<'PY'
import sys
s, d, k = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]); fr = round(d * 30); st = fr // k
for i in range(k):
    a = i * st; b = fr if i == k - 1 else (i + 1) * st; print(i, round(s + a / 30, 4), round((b - a) / 30, 4))
PY
while read n s d; do piece "$n" "$s" "$d" & done < "$TMP/plan"; wait
for n in $(cut -d' ' -f1 "$TMP/plan"); do echo "file '$TMP/p_$n.mp4'"; done > "$TMP/l.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$TMP/l.txt" -c copy "$OUT"; rm -rf "$TMP"; echo "segment $IDX done"
