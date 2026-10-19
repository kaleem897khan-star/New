# RDP School – Reels v2 (1080x1920) – "Design 6 / Caption Style" (owner approved 2026-10-20)

Renders the vertical reels (YouTube Shorts / Facebook / Instagram) of a long video on GitHub Actions (this public repo, free minutes).
**Always render here, never on the AI sandbox, and always with the maximum number of parallel segments** (`SEGMENTS: 20` = free-plan job limit) so it is fast.

## Split rule (owner, 2026-10-20)
Every reel 60–120 s, all reels of a video **equal length**, **as few reels as possible**: `n = ceil(video_seconds / 120)`, length = video / n.
Example: 8:51 (531.3 s) → 5 reels × 106.3 s. Plus a 2.5 s end card per reel.

## Layout (top → bottom)
| Element | Spec |
|---|---|
| Background | one blue theme, big blurred glows (white, gold, light blue, peach, cyan) drifting and cross-fading slowly (same as the long video) |
| Header | RDP X CLOUD glass pill (white text) left, green `PART n` right (never the total) |
| Title block | small spaced kicker (e.g. "WINDOWS VPS TUTORIAL") + gold line, title 56 px (auto-shrinks), subtitle 25 px |
| Video | **full 16:9, nothing cropped**: 1036x583 at (22,318), radius 26, white glow border, gold highlight circles/arrows inside (`annotations.py`) |
| Step caption | "STEP n" gold + 1–2 line caption 64 px (`captions` in job.json, English) |
| Ad card | ribbon **"AD • OUR SERVICES"** + ONE service at a time (9 s each, tiles light up one by one): VPS/RDP → OS → RAM → Locations → Dedicated → Installation → Bots → Websites → Mobile Apps → repeats. `ad_start` continues the rotation in the next part. |
| Like/Comment/Subscribe | pops up only at `lcs` times (start, middle, near end), cursor clicks Like → Comment → Subscribe → Bell, then disappears. Click + bell sounds. |
| Social bar | WhatsApp +92-313-8303-109 fixed, right side rotates Instagram / Facebook / TikTok @rdpxcloud / YouTube RDP School every 4 s |
| Bottom ~230 px | kept empty on purpose (platform buttons/caption cover it) |
| End card (2.5 s) | Thank You for Watching, TO BE CONTINUED in PART n+1 (last: SERIES COMPLETE), WhatsApp, website, socials |

## Make a reel
1. Cut the part from the **trimmed, IP-blurred** long-video input: `ffmpeg -ss <start> -t <len> -i input.mp4 -c:v libx264 -crf 16 -c:a aac jobs/<job>/input.mp4`
2. `jobs/<job>/job.json` (copy `jobs/rdp-login-p1/job.json`): part, total_parts, kicker, title, subtitle, ad_start, lcs, captions (times relative to the clip).
3. `jobs/<job>/annotations.py`: the long video's highlights that fall in this part, times shifted to the clip (see the example).
4. Preview one frame: `python3 reel-v2/render/reel_ui.py reel-v2/jobs/<job> --still 30 /tmp/s.png`
5. Render: push branch `reel/<job>` (input.mp4 is git-ignored on main: `git add -f`). Result branch `reel-out/<job>` → `cat reel.mp4.part_* > reel.mp4`. Then **delete both branches**.
