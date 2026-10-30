# day.brief content rules

Rules for whoever writes `brief.json` (the scheduled tasks). They put the account plan into practice:
one hook cover, briefings of 60 seconds or less, one-issue shorts, and a fixed caption template.
`build.py` writes the captions and warns when a reel runs long; the rest is up to the writer.

## Account topic: AI 테크 (from 2026-10-30)

팀장 decided on 2026-10-30 to narrow the account to AI tech. Concept: **"피할 수 없다, 정면으로 받아들이자. 알아야 써먹고,
그래야 살아남는다."** Every post answers two things: what happened in AI, and what it means for the viewer's work, money or
career. The tone faces AI head-on: no fear-mongering ("AI가 다 뺏는다"), no hype ("혁명", "미쳤다"); a calm "this is coming,
here is how to use it". Briefs, week.json and breaking.json set `"topic": "ai"`, which switches the on-screen tags, the
end card, the caption follow line and the base hashtags (#AI뉴스 #인공지능) to the AI account. See `brief_ai_example.json`.

What each slot covers (the rest of this file still applies: hooks, lengths, captions, proofreading):

| slot | issues (3) | AI scene → "오늘 써먹기" | market scene |
|---|---|---|---|
| 07:00 morning | overnight global AI: model and product launches (OpenAI, Google, Anthropic, Meta, Microsoft, Apple, Nvidia, xAI, Mistral, DeepSeek...), big-tech AI earnings and spending, AI and jobs/hiring, regulation (US, EU, China) | one tool the viewer can try today, ending "~할 때 쓰면 됩니다." | `market.rows`: Nasdaq plus the two AI stocks that moved most (Nvidia, Alphabet, Microsoft, Meta...) |
| 18:00 evening | Korea AI and tech: Samsung, SK hynix, Naver, Kakao, LG, startups; government AI policy (AI 기본법, GPU, data centres); AI at Korean workplaces, schools and jobs | none | `market.rows`: KOSPI, Samsung Electronics, SK hynix (or the AI stock that moved most) |
| Sun weekly carousel | "이번 주 꼭 알아야 할 AI 5" from the week's briefs: launches, money, jobs, one tool | | |

Picking issues (replaces "Cover order" below for the AI account):
1. Hits your work, money or career: AI changing a job or hiring, a tool that replaces a paid task, AI stocks moving
   sharply, prices of AI services.
2. A big launch or a striking number: a new frontier model, a record deal, a benchmark lead, a large layoff or hire.
3. Policy and regulation.
4. A rumour, a leak, a single outlet's exclusive or a CEO's prediction never leads; leave it out unless confirmed.

Sources: the company's own blog, docs or filing first; then Reuters, AP, Bloomberg, CNBC, The Verge, TechCrunch, Ars
Technica, The Register; Korean issues from 연합뉴스, KBS, 전자신문, 디지털타임스, 조선비즈 or the ministry's press release.
Read the article itself; aggregators and newsletters are only for finding stories.

Hooks in the concept's voice (still neutral and factual, still with a number):
- tie it to the viewer: "내 직무는?", "이제 ○○도 AI가?", "월 ○만 원 아끼는 법"
- the turn: "알고 보니", "결국", "AI가 더 잘해서?"
- banned in addition to the list below: "일자리 다 사라진다", "AI 종말", "미쳤다", "역대급 혁명", and anything that
  promises a stock will go up.

Closing script: the one-liner, the brief's question, then "댓글로 남겨 주세요. 내일도 보려면 팔로우." The one-liner can
carry the concept ("알아야 써먹습니다"); the end card already shows "알아야 써먹고 써먹어야 살아남는다".
Questions at the end of captions ask what the viewer will do, not what they fear: "내 일에는 언제 올까요?",
"여러분이라면 어디에 써먹겠어요?", "이 기능, 돈 내고 쓸 만할까요?"

Opening line ends "오늘 AI, 1분 정리." (morning) or "오늘 국내 AI, 45초 정리." (evening).

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

**AI account (`"topic": "ai"`, from 2026-10-30)** replaces the "Confirmed" sources and the "Big enough" list above:
- Confirmed: the company's official blog, docs, launch page or filing, or two of Reuters, AP, Bloomberg, CNBC,
  The Verge, TechCrunch, 연합뉴스, KBS reporting it independently.
- Big enough, one of:
  - launch: a new flagship model or product from OpenAI, Google, Anthropic, Meta, Microsoft, Apple, xAI, Nvidia,
    Samsung or Naver that people can use now (not "coming soon", not a research preview for a few partners);
  - market shock: Nvidia, Microsoft, Alphabet, Meta, Apple, Amazon, Samsung Electronics or SK hynix ±7% in a day,
    or the Philadelphia semiconductor index or Nasdaq ±3%;
  - money: an AI deal, investment or acquisition of $10B (about 14조 원) or more, or Korean government AI spending of
    1조 원 or more;
  - rules: a law, executive order or regulator decision on AI or AI chips taking effect or passed (US, EU, China,
    Korea), such as chip export controls or AI 기본법 enforcement rules;
  - jobs: a company cutting or hiring 1,000+ people and naming AI as the reason.
- Never breaking for the AI account: benchmark claims alone, leaks and rumours, CEO interviews and predictions,
  funding rounds under $10B, minor app updates.

Slides: `kind: "breaking"`, `kicker: "BREAKING"`, `week_label: "속보"`, `dates` = today's `date_short`, `sub` = who
announced it, `title` = the fact and its number in 2 lines, `cover_foot` = what swiping shows, 3-7 items, `end`.
Body lines about 22 characters each (break with `\n` yourself), `num` about 8 characters.
Caption fields: `caption_title`, `summary` (2-3 sentences, numbers and places spelled out), optional per-item
`caption_line`, `notes`, `save`, `question`, `keywords` (up to 3). Tone and banned words are the same as hooks.
The reel carries the rotating music bed and no narration: leave out `scripts`.

## Measuring (2-week trial, judged 11/5)

Goal: median 100 views per post and 30 followers. If shorts average 3x the briefings' views, raise shorts to 4 a day;
if briefing watch-through stays under 40% at 60s, cut briefings to two issues.
