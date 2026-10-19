# RDP School – Long Video Render (16:9)

Renders a finished long video (YouTube, 1920x1080) in the owner-approved style. **Shorts/Reels are NOT made here** – they live in the private repo `rdp-school-shorts` (`reel-template/`). This public repo only renders; it holds **no secrets** and never uploads anywhere.

## What the final video looks like (approved 2026-10-20)
| Part | Spec |
|---|---|
| Canvas | 1920x1080, 30 fps, H.264 CRF 18 + AAC 192k |
| Background | navy→blue gradient with 4 big blurred colour glows (white, gold, light blue, peach, cyan) that drift and slowly cross-fade (`frame_bg.py`, palette step every ~5.5 s) |
| Video frame | source scaled to 1617x910 at (151,50), radius 30, white 5 px border + soft white glow + drop shadow |
| Logo card | top-left, half over the frame corner: pill 390x96 at (115,24), navy→blue glass (alpha 235), cyan glow border, RDP X Cloud icon + white "RDP X CLOUD" (`logo_card.py`) |
| Bottom glass bar | centred under the video, frosted glass; rotates every 6 s: "Get Your VPS Just in 5 Minutes" + WhatsApp +92-313-8303-109 → Instagram @rdpxcloud → Facebook @rdpxcloud → TikTok @rdpxcloud → YouTube RDP School (real brand logos) |
| Highlights | gold hand-drawn circle or curved arrow + gold label pill, **English labels**, drawn in 0.7 s, 2x supersampled (`annotate.py`). **No pencil/draw sound.** |
| Like/Comment/Subscribe | 7 s card bottom-left of the video, cursor clicks Like → Comment → Subscribe → Bell (each turns blue/grey, bell rings). Sounds: mouse click + "ding-ding" bell (`sfx.py`) |
| Audio | original voice untouched (no denoise unless the owner asks) + sound effects |

## Before rendering (done by the AI, owner approves)
1. Trim the raw OBS recording (cut the OBS screen at start/end).
2. **Blur every IP that is not the demo IP** (e.g. Start menu "Recent" list). Only the blurred, trimmed file may be pushed here – this repo is public.
3. Write `jobs/<job>/annotations.py`: list `ANN_FULL` of `(start, end, "circle"|"arrow", (x0,y0,x1,y1), "English label", "below"|"right")` in 1280x720 source pixels, and `LCS_TIMES = [...]` (start of each Like/Subscribe card). Check each box on a frame at start+0.3 s and end-0.3 s.
4. Show the owner a 1-minute sample first; render the full video only after he approves.

## Render (GitHub Actions, free minutes because the repo is public)
```bash
git checkout -b render/<job> main
cp trimmed_blurred.mp4 long-template/jobs/<job>/input.mp4    # never commit to main
git add long-template/jobs/<job> && git commit -m "render <job>" && git push -u origin render/<job>
```
Workflow `long-render.yml` splits the video into 20 equal segments rendered in parallel (4 pieces per runner), joins them, mixes the sound and pushes `output/<job>` with `final.mp4.part_*` (45 MB parts). Download: `git fetch origin output/<job>` → `cat final.mp4.part_* > final.mp4`.

**Clean up right after downloading** (repo is public):
```bash
git push origin --delete render/<job> output/<job>
```
Segment artifacts expire after 1 day.

## Local render (slow, ~4 fps on 2 cores)
```bash
pip install -r long-template/render/requirements.txt && python3 long-template/render/logo_card.py
long-template/render/render_segment.sh $PWD/long-template/jobs/<job> 00 140 60 /tmp/sample.mp4 3   # 1-minute sample
```

## Files
`render/frame_bg.py` background + frame + glass bar (raw RGB to stdout) · `render/annotate.py` highlights + Like/Subscribe (RGBA to stdout) · `render/logo_card.py` logo card PNG · `render/sfx.py` click/bell track · `render/render_segment.sh` one segment · `render/finalize.sh` join + audio · `render/plan.py` segment matrix · `jobs/<job>/` per-video settings.
