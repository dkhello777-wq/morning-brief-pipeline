# morning-brief-pipeline
Builds the 7am.brief morning/evening news reels: `TYPECAST_API_KEY=... python3 build.py brief.json out_dir`.

Since 2026-10-30 the account covers AI tech: set `"topic": "ai"` in the brief (see `brief_ai_example.json`).

What to write into `brief.json` (hook, script lengths, cover order, caption fields, posting schedule) is in
[CONTENT_RULES.md](CONTENT_RULES.md).

## Hook cover, shorts, captions, weekly carousel

| | command | output |
|---|---|---|
| briefing | `python3 build.py brief.json out` | `final.mp4`, `cover.jpg`, `caption.txt` |
| one-issue short | `SHORT=2 python3 build.py brief.json out` | `final_short2.mp4`, `cover_short2.jpg`, `caption_short2.txt` |
| caption only | `CAPTION_ONLY=1 python3 build.py brief.json out` | prints the caption |
| weekly carousel | `python3 carousel.py week.json out_week` | `slide_01.png`..., `carousel.mp4`, `caption.txt` |
| breaking card news | `python3 carousel.py breaking.json out_bk` (`"kind": "breaking"`) | same as the carousel, with the 속보 cover and caption |

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
- Music (`music.py`, synthesized, nothing downloaded): five styles, `bright` (the original bed), `lofi`, `pulse`,
  `piano`, `upbeat`, rotate by the KST date so the account doesn't play the same loop every day; the evening edition is
  two styles ahead of the morning one, and a short uses its briefing's style. `MUSIC=<style>` or a `"music"` field in
  brief.json / week.json forces one; `python3 music.py out` writes a 20s sample of each.
- Weekly carousel audio: the reel plays the day's music with a soft swish on each slide change. With `"scripts"` in
  week.json (one line per slide: cover, each item, end card; see week_example.json) and `TYPECAST_API_KEY` set, every
  slide is narrated in the briefing voice with the music ducked under it, and stays up as long as its line takes
  (at least 3.5s). Without scripts or a key the reel is music only, 3.5s a slide.
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
