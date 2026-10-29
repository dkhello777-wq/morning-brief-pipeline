#!/usr/bin/env python3
"""Weekly save-for-later carousel ("이번 주 돈 되는 뉴스 5").
Usage: python3 carousel.py week.json out_dir
week.json schema: see week_example.json (3-7 items; each tag, headline, optional num, body, source;
"dates" e.g. "10.19–10.25" is shown large on the cover beside week_label).
A breaking post uses the same slides: "kind": "breaking" plus kicker/sub/cover_foot/end on the cover and end slide, and a
"summary" (optional "caption_title", "notes", "save", per-item "caption_line") for its caption; see breaking_example.json.
Output: out_dir/slide_01.png ... (1080x1350, Instagram 4:5 carousel), out_dir/caption.txt,
and out_dir/carousel.mp4 (the same slides as a 1080x1920 slideshow reel, 3.5s each, for publish tools that only take reels).
"""
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
week = json.load(open(sys.argv[1]))
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
assert 3 <= len(week["items"]) <= 7, "a carousel holds 3-7 items"
SLIDE_S = 3.5

def run(cmd): subprocess.run(cmd, check=True)

html = (HERE / "carousel_tpl.html").read_text().replace("__CONTENT__", json.dumps(week, ensure_ascii=False))
html = html.replace("__FONT__", (HERE / "fonts" / "PretendardVariable.ttf").resolve().as_uri())
(out / "carousel.html").write_text(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception:  # pip playwright newer than the preinstalled browser: use the bundled chromium directly
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1080, "height": 1350})
    pg.goto((out / "carousel.html").resolve().as_uri()); pg.wait_for_timeout(600)
    n = pg.evaluate("window.N")
    for k in range(n):
        pg.evaluate(f"window.show({k})"); pg.screenshot(path=str(out / f"slide_{k+1:02d}.png"))
    b.close()

# slideshow reel: each 4:5 slide centred on a 9:16 canvas of the brand yellow (the ivory cover on ivory)
inputs = []
for k in range(n): inputs += ["-loop", "1", "-t", str(SLIDE_S), "-i", str(out / f"slide_{k+1:02d}.png")]
pads = "".join(f"[{k}:v]pad=1080:1920:0:285:color={'0xF5F2EA' if k == 0 else '0xFFE600'},setsar=1,fps=24[v{k}];" for k in range(n))
run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-f", "lavfi", "-t", str(SLIDE_S * n), "-i", "anullsrc=r=44100:cl=stereo",
     "-filter_complex", pads + "".join(f"[v{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[v]",
     "-map", "[v]", "-map", f"{n}:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-shortest",
     "-movflags", "+faststart", str(out / "carousel.mp4")])

one = lambda x: " ".join(str(x or "").split())
FOLLOW = "매일 07:00 세계·시장 / 18:00 국내 이슈를 3분 브리핑으로 → 팔로우하고 받아보기"
sources = " · ".join(dict.fromkeys(s.strip() for it in week["items"] for s in str(it.get("source") or "").split("·") if s.strip()))
if week.get("kind") == "breaking":
    # breaking post (CONTENT_RULES.md "Breaking"): headline, summary, one line per slide, notes, save/question, sources
    lines = [f"📌 [속보] {one(week.get('caption_title') or week['title'])}", "", one(week["summary"]), ""]
    lines += [f"{'➊➋➌➍➎➏➐'[i]} {one(it.get('caption_line') or it['headline'])}" + (f" — {one(it['num'])}" if it.get("num") and not it.get("caption_line") else "")
              for i, it in enumerate(week["items"])]
    if week.get("notes"): lines += [""] + [one(n) for n in week["notes"]]
    lines += ["", f"🔖 {one(week.get('save') or '저장해두고 다시 보세요')}"]
    if week.get("question"): lines.append(f"💬 {one(week['question'])}")
    lines += [FOLLOW, "출처: " + sources,
              " ".join("#" + k.replace(" ", "") for k in dict.fromkeys(list(week.get("keywords") or [])[:3] + ["오늘의뉴스", "경제뉴스"]))]
    (out / "caption.txt").write_text("\n".join(lines) + "\n")
    print("DONE", n, "slides", out / "slide_01.png", "reel", out / "carousel.mp4", "caption", out / "caption.txt")
    sys.exit(0)
lines = [f"📌 {one(week['title'])} ({week.get('week_label', '')})", ""]
lines += [f"{'➊➋➌➍➎➏➐'[i]} {one(it['headline'])}" + (f" — {one(it['num'])}" if it.get("num") else "") for i, it in enumerate(week["items"])]
lines += ["", "🔖 저장해두고 월요일 아침에 다시 보세요"]
if week.get("question"): lines.append(f"💬 {one(week['question'])}")
lines += [FOLLOW,
          "출처: " + " · ".join(dict.fromkeys(it.get("source") for it in week["items"] if it.get("source"))),
          " ".join("#" + k.replace(" ", "") for k in dict.fromkeys(list(week.get("keywords") or [])[:3] + ["주간뉴스", "경제뉴스"]))]
(out / "caption.txt").write_text("\n".join(lines) + "\n")
print("DONE", n, "slides", out / "slide_01.png", "reel", out / "carousel.mp4", "caption", out / "caption.txt")
