# 7am.brief content rules

Rules for whoever writes `brief.json` (the scheduled tasks). They put the account plan into practice:
one hook cover, briefings of 60 seconds or less, one-issue shorts, and a fixed caption template.
`build.py` writes the captions and warns when a reel runs long; the rest is up to the writer.

## Posting schedule (KST)

| time | post | how |
|---|---|---|
| 07:00 | morning briefing (+ story) | `python3 build.py brief.json out` |
| 08:30 | morning short ① | `SHORT=n python3 build.py brief.json out` (same `out`, no extra TTS) |
| 12:20 | morning short ② | same, the other picked issue |
| 18:00 | evening briefing (+ story) | `python3 build.py brief_pm.json out_pm` |
| 21:30 | evening short | `SHORT=n python3 build.py brief_pm.json out_pm` |
| Sun 20:00 | weekly carousel | `python3 carousel.py week.json out_week` |
| 11:00, 15:00 | breaking card news, only when there is one | `python3 carousel.py breaking.json out_bk` |

Shorts use the two issues ranked highest by the cover order below (evening: one).

## Cover order: which issue leads

1. Hits your money or daily life: rates, loans, housing subscriptions, tax, prices, pay, pensions.
2. A big number or a striking turn: reversals, records, many people or large sums.
3. International politics and diplomacy.
4. Crime and accidents never lead; put them second or third.

The leading issue goes first in `issues` and gives the briefing its `hook`.

## Hook (`hook` on the brief and on each issue)

```json
"hook": {"q": "대통령 선거가\n2%p 차이?", "hi": "볼리비아 46 vs 44"}
```

- `q`: the question or twist, 10 characters or fewer per line, at most 2 lines.
- `hi`: the number line, 9 characters or fewer (it sits on the accent bar). Always include one number.
- Forms that work: a question ("~라고?", "왜 ~일까?"), a reversal ("알고 보니", "결국"), a link to the
  reader ("내 대출은?", "월급에 미치는").
- Never: "충격", "경악", "난리남", "~안무섭다", or anything that takes a side or generalises about a nationality or group.
  Neutral tone always; the hook teases the fact, it does not judge it.

## Scripts (target: briefing 60s or less, short 15s or less)

| scene | limit |
|---|---|
| opening | 45 characters. The first sentence is the hook itself, said in 2 seconds: 20 characters or fewer, with its number. Then one line that pays it off, then "오늘 ○○ 이슈, 1분 정리." No date, no list of what is coming ("세 가지와 AI, 증시까지"). |
| each issue | 55 characters. One fact with its number, one line of why it matters. |
| AI (morning) | 70 characters, ending "~할 때 쓰면 됩니다." |
| market | 60 characters. |
| closing | the one-liner, the brief's question, then "댓글로 남겨 주세요. 내일도 보려면 팔로우." |

An issue script must also stand alone, because the short plays it on its own, and its first words play under the
short's cover: lead with the fact and its number, never a lead-in ("다음 소식입니다").

The first 3 seconds decide whether a viewer from the Reels tab stays (10/24: about 80% skipped, 2-4s average watch).
The video opens on the hook in large type with subtitles; the script has to match it word for word in spirit, so the
first thing heard is the same question or number the screen shows.
`build.py` prints `WARN length` when a briefing passes 62s or a short 16s; shorten and rebuild.

## Caption fields (build.py writes `caption.txt` / `caption_short{n}.txt`)

- each issue: `summary` (2-3 sentences with the numbers, names and places spelled out, since Instagram search
  reads captions), `keywords` (1-2, no `#`), optional `question` for its short.
- brief: `question` (one line asking the reader's view), `keywords` (up to 3).
- Hashtags are capped at 5 (3 topic + #오늘의뉴스 #경제뉴스).
- Political issues: give both sides' positions in the summary, one clause each.

## Weekly carousel (`week.json`, see `week_example.json`)

Five items from the week that touch money: markets, rates, housing, policy, tools. Each has a `num` where one exists.
`carousel.py` writes the 4:5 slides for a carousel post, a 9:16 slideshow reel (`carousel.mp4`) for tools that
only publish reels, and the caption.

## Breaking card news (11:00 and 15:00, `breaking.json`, see `breaking_example.json`)

A scheduled check at about 10:47 and 14:47 looks for a breaking story and posts at most one card news per check.
Most checks should end with nothing posted; that is the expected result, not a failure.

A story is breaking only if it passes all three:

1. **New**: first reported since the last check (11:00 check: since 06:00; 15:00 check: since 10:40), and not already
   in today's morning briefing or an earlier breaking post.
2. **Confirmed**: an official announcement (ministry, Bank of Korea, Financial Services Commission, National Assembly
   vote, company disclosure) or at least two major outlets reporting it independently (Yonhap, KBS, MBC, SBS, JTBC,
   YTN, Reuters, AP, Bloomberg). Never a single outlet's exclusive, a rumour, or "under review".
3. **Big enough**, one of:
   - money and daily life, decided: rates, housing supply or lending rules, taxes, public fees, pensions, minimum
     wage, large support payments;
   - market shock: KOSPI or KOSDAQ ±3% intraday, a sidecar or circuit breaker, or the won moving 1.5% or more in a day;
   - national scale: a declared disaster or one with many deaths, the outbreak of armed conflict involving Korea or
     a major power, a decision at president or prime minister level, a deal or event at a top-10 Korean company worth
     trillions of won.

Never breaking: entertainment, sports, individual crimes and accidents, political spats and remarks, polls.

Slides: `kind: "breaking"`, `kicker: "BREAKING"`, `week_label: "속보"`, `dates` = today's `date_short`, `sub` = who
announced it, `title` = the fact and its number in 2 lines, `cover_foot` = what swiping shows, 3-7 items, `end`.
Body lines about 22 characters each (break with `\n` yourself), `num` about 8 characters.
Caption fields: `caption_title`, `summary` (2-3 sentences, numbers and places spelled out), optional per-item
`caption_line`, `notes`, `save`, `question`, `keywords` (up to 3). Tone and banned words are the same as hooks.
The reel carries the rotating music bed and no narration: leave out `scripts`.

## Measuring (2-week trial, judged 11/5)

Goal: median 100 views per post and 30 followers. If shorts average 3x the briefings' views, raise shorts to 4 a day;
if briefing watch-through stays under 40% at 60s, cut briefings to two issues.
