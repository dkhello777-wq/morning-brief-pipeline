# morning-brief-pipeline
Builds the 7am.brief morning/evening news reels: `TYPECAST_API_KEY=... python3 build.py brief.json out_dir`.

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

## Reel performance (`analytics/`)

After a reel has been up for ~48 h, save the reels list from vidIQ `vidiq_instagram_owner_insights` (account day.brief)
as `analytics/snapshots/YYYY-MM-DD.json` (drop the signed `thumbnailUrl`s) and run `python3 analytics/analyze.py`.
It writes `analytics/report.md`: per-reel views/likes/saves/shares/watch %, and comparisons by AM/PM, lead topic,
topics covered and length. Add one row per published reel to `analytics/episodes.csv` (icons from `out_dir/icons_used.txt`,
cover style, hook line) so icons and covers can be compared too. The report flags every comparison as not yet meaningful
until the median reel has 100+ views and each group has 10+ reels.
