# morning-brief-pipeline
Builds the 7am.brief morning/evening news reels: `TYPECAST_API_KEY=... python3 build.py brief.json out_dir`.

What to write into `brief.json` (hook, script lengths, cover order, caption fields, posting schedule) is in
[CONTENT_RULES.md](CONTENT_RULES.md).

## Hook cover, shorts, captions, weekly carousel

| | command | output |
|---|---|---|
| briefing | `python3 build.py brief.json out` | `final.mp4`, `cover.jpg`, `caption.txt` |
| one-issue short | `SHORT=2 python3 build.py brief.json out` | `final_short2.mp4`, `cover_short2.jpg`, `caption_short2.txt` |
| caption only | `CAPTION_ONLY=1 python3 build.py brief.json out` | prints the caption |
| weekly carousel | `python3 carousel.py week.json out_week` | `slide_01.png`..., `carousel.mp4`, `caption.txt` |

- `hook: {"q", "hi"}` on the brief turns the opening card into a two-line hook (the number line on an accent bar).
  Without it the old `title` is shown.
- Covers (briefing, short, weekly carousel) use a minimal editorial layout: ivory (morning) or ink (evening) background,
  the date in large type, the hook left-aligned with the number line on a yellow marker stroke, the issue list, and the
  lead issue's art. The date comes from `date_short` (`"10.22 THU"` → `10.22` beside `목요일 / 아침 브리핑`); the carousel
  shows `dates` (`"10.19–10.25"`) above `week_label`. The cover font is Pretendard (`fonts/`, SIL OFL), loaded from the repo.
- A short is the issue's hook cover (1.6s, narration already running), its scene with the briefing's own narration, and an end card pointing to the
  full briefing (2.4s): 10-15s. Run it after the briefing with the same `out` so it reuses `v{n+1}.mp3`, the AI art and
  the icon choice (`art_used.json`); it makes no TTS or image calls of its own.
- First 3 seconds (`HOOK_STYLE`, default `punch`): frame 0 is still the finished cover, then at 0.25s the reel cuts to
  the hook alone in large type (the number counts up, the marker stroke sweeps in, the lead art pops) with a soft whoosh.
  `live` keeps the cover on screen and moves it instead (slow push-in, number pulse, issue list lit in turn); `off` is the
  old static opening. With `punch`/`live` the voice starts on the first frame, the music starts without a slow fade, and
  burned-in subtitles follow the narration, numbers in yellow (`SUBTITLES=0` turns them off). A short no longer opens on a
  silent cover: its narration starts under the cover, so it is 1.6s shorter.
- Scenes are padded by 0.6s (was 0.9s), and the build prints `WARN length` past 62s (briefing) or 16s (short).

## Issue art (center of the issue scenes)

Each issue in `brief.json` can carry story-specific art on top of its data graphic (`ill`):

| field | meaning |
|---|---|
| `icon` | A [Fluent Emoji 3D](https://github.com/microsoft/fluentui-emoji) name (`"Fire engine"`, `"Balance scale"`, `"Ballot box with ballot"`) or an emoji glyph. A list gives fallbacks in order. Country flags (`"🇺🇸"`) are drawn with the emoji font because Fluent has none. |
| `motion` | Loop after the pop-in: `bob` (default), `sway`, `pulse`, `shake`, `spin`, `drive`. |
| `image_prompt` | English description of an AI illustration (Google Gemini, needs `GEMINI_API_KEY`). Only the first issue that has one gets it; on any failure the issue falls back to its `icon`. Never ask for real people or logos. |

`ill.kind` can now be `"icon"` (art only). `bars`, `bridge`, `alert` and `number` keep their charts/counters and show the art above them.
Without `icon` the old code-drawn graphics are used.

Avoiding repeats: set `RECENT_ICONS=recent_icons.txt` (one name per line, from recent reels). Fresh candidates win; an icon is never
used twice in one reel. The icons actually used are written to `out_dir/icons_used.txt`.

Check art before a full build: `CHECK_ART=1 python3 build.py brief.json out_dir` prints what each issue resolved to.

## Copy of every rendered video in Google Drive

[`drive_copy.gs`](drive_copy.gs) is a Google Apps Script that runs in the owner's Google account (not in this repo's
Actions). Every 10 minutes it reads the public `releases.atom` feed (GitHub API as a fallback), and for each new
`render-<id>` release that has `status.json` it saves every video in `status.json.videos` plus its caption to
My Drive > morning-brief > 제작 영상 > `<date>` as `2026-10-31 저녁.mp4`, `2026-10-31 저녁 숏컷1.mp4`,
`2026-11-01 속보 11시.mp4` and `... 캡션.txt`. A re-made release replaces the same-named files (the old ones go to the trash).
No secrets: it only reads public release files. Setup: paste it into a new project at https://script.new, run `setup`
once and allow the permissions; `stop` removes the 10-minute trigger. Copied releases are remembered in the script
properties; a release that fails 6 runs in a row is skipped and reported through the Apps Script failure e-mail.
