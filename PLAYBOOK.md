# RDP School – full video playbook (owner approved 2026-10-20)

**Every new video is made exactly like the "RDP login" video of 2026-10-20. Do not redesign anything – only the video,
the highlights, the step captions and the titles change.** Owner chats in Roman Urdu; everything written on screen / in the repo is English.

| What | Where (this public repo) | Look |
|---|---|---|
| Long video 16:9 | `long-template/` (spec: `long-template/README.md`) | animated blurred-colour background, white-bordered rounded frame, RDP X CLOUD glass pill top-left (white text), rotating glass bar (VPS in 5 min + WhatsApp → Instagram → Facebook → TikTok → YouTube), gold English highlights, Like→Comment→Subscribe→Bell pop-ups with click + bell sounds, original voice |
| Reels 9:16 | `reel-v2/` (spec: `reel-v2/README.md`) | "Design 6 Caption Style": same background, kicker + title, full 16:9 video, big step caption, "AD • OUR SERVICES" card (one service at a time, repeats), Like/Comment/Subscribe + "Get Your RDP Just in 5 Minutes / Message Us" (start, middle, end), WhatsApp fixed + rotating FOLLOW US / SUBSCRIBE / VISIT WEBSITE, 2.5 s end card |
| Confidential info | `long-template/tools/find_sensitive.sh` + `trim_blur.py` | box-blurred for the exact seconds it is visible (long video, and therefore every reel) |
| Upload / schedule | private repo `zoya43135-byte/rdp-school-shorts` (`queue/`, `now/`, daily 7 PM PKT run) | YouTube Shorts + Facebook (video if > 90 s) + Instagram, same day |

## Steps
1. **Look at the raw recording** and tell the owner what it is about. Don't change anything he didn't ask for (e.g. don't denoise unless asked).
2. **Trim + blur:** `python3 long-template/tools/find_cuts.py raw.mkv` (OBS screen at start/end) → `long-template/tools/find_sensitive.sh raw.mkv` (OCR every second: IPs, e-mails, URLs, password/key/token lines, long random strings, phone/card numbers). **Show the list to the owner, ask what is confidential and blur all of it** (other clients' IPs, passwords, e-mails, panel URLs, licence keys, payment info ...). Only the brand number/website stay → write `jobs/<job>/blur.json` → `python3 long-template/tools/trim_blur.py raw.mkv trimmed.mp4 START END jobs/<job>/blur.json`. Show the owner a 15 s blur sample.
3. **Highlights:** `long-template/jobs/<job>/annotations.py` – gold circle/arrow + English label for every important click/field (check each box on a frame at start+0.3 s and end-0.3 s). `LCS_TIMES` = Like/Subscribe pop-ups (e.g. ~2:20 and on the outro screen).
4. **1-minute sample** (`long-template/render/render_segment.sh … 140 60`) → owner approval.
5. **Long render on GitHub Actions** (never on the AI sandbox): push `render/<job>` with `jobs/<job>/input.mp4` (= trimmed.mp4). 20 parallel segments, ~10 min. Download `output/<job>`, delete both branches.
6. **Reels:** write `reel-v2/jobs/<name>.story.json` (kicker, title, step captions over the whole video) → `python3 reel-v2/render/make_jobs.py trimmed.mp4 long-template/jobs/<job>/annotations.py reel-v2/jobs/<name>.story.json <name>` → push `reel/<name>-pN` for every part (all render in parallel). Equal parts, 60–120 s, fewest reels.
7. **Schedule (private repo):** push `schedule_now.json` so YouTube + Facebook show every part as Scheduled right away (private README). owner sends the Part 1 thumbnail → `assets/thumb_template.jpg` → `python thumb.py <part> <id>` for every part. Write title/description/tags (SEO research first, channel format), `fb_as_video: true` for reels > 90 s, `playlist` key, `release_date` = one per day at 7 PM PKT right after the last scheduled item. Long video already on YouTube → `now/NNNN.*` → `post-now.yml` posts it to Facebook + Instagram immediately.
8. Delete every temporary branch, tell the owner the dates, revoke-token reminder.
