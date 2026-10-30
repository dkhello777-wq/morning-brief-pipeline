#!/usr/bin/env python3
"""Weekly save-for-later carousel ("이번 주 돈 되는 뉴스 5").
Usage: python3 carousel.py week.json out_dir
week.json schema: see week_example.json (3-7 items; each tag, headline, optional num, body, source;
"dates" e.g. "10.19–10.25" is shown large on the cover beside week_label).
A breaking post uses the same slides: "kind": "breaking" plus kicker/sub/cover_foot/end on the cover and end slide, and a
"summary" (optional "caption_title", "notes", "save", per-item "caption_line") for its caption; see breaking_example.json.
Output: out_dir/slide_01.png ... (1080x1350, Instagram 4:5 carousel), out_dir/caption.txt,
and out_dir/carousel.mp4 (the same slides as a 1080x1920 slideshow reel, for publish tools that only take reels).
The reel has a synthesized royalty-free music bed (music.py, rotating by date like the briefings; MUSIC=<style> or a
week "music" field forces one) with a soft swish on each slide change. If week.json has "scripts" (one line per slide:
cover, each item, end card) and TYPECAST_API_KEY is set, each slide is narrated in the briefing voice (config voice_id,
or week "voice_id") with the music ducked under it, and stays up as long as its line takes (at least 3.5s).
Without scripts or a key (or with NO_TTS=1) the reel is music only, 3.5s a slide.
"""
import json, os, pathlib, subprocess, sys, time, urllib.request, wave
import numpy as np
import music

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

# ---------- narration (optional) ----------
SR = music.SR; PAD = 0.9; LEAD = 0.3
scripts = week.get("scripts") or []
KEY = os.environ.get("TYPECAST_API_KEY", "")
narrate = bool(scripts) and bool(KEY) and os.environ.get("NO_TTS") != "1"
if scripts: assert len(scripts) == n, f"scripts must have {n} lines (cover, {n - 2} items, end card)"
durs = [SLIDE_S] * n; speech = [0.0] * n
if narrate:
    for k, text in enumerate(scripts):
        mp3 = out / f"w{k+1}.mp3"
        if not mp3.exists():
            body = json.dumps({"text": text, "model": "ssfm-v30", "voice_id": week.get("voice_id", "tc_68d4b115f0486108a7eefb37"),
                               "prompt": {"emotion_preset": "normal", "emotion_intensity": 1},
                               "output": {"audio_format": "mp3"}}).encode()
            req = urllib.request.Request("https://api.typecast.ai/v1/text-to-speech", data=body,
                                         headers={"X-API-KEY": KEY, "Content-Type": "application/json"})
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(req, timeout=180) as r: mp3.write_bytes(r.read())
                    break
                except Exception:
                    if attempt == 3: raise
                    time.sleep(5)
        speech[k] = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)]))
        durs[k] = round(max(SLIDE_S, speech[k] + LEAD + PAD), 2); print("tts", k + 1, round(speech[k], 2), flush=True)
starts = [sum(durs[:k]) for k in range(n)]; total = sum(durs)
voice = np.zeros((int(SR * total) + 1, 2))
if narrate:
    for k in range(n):
        raw = subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i", str(out / f"w{k+1}.mp3"), "-f", "s16le", "-ar", str(SR), "-ac", "2", "-"])
        x = np.frombuffer(raw, np.int16).reshape(-1, 2) / 32768; a = int((starts[k] + (0.15 if k == 0 else LEAD)) * SR)
        x = x[:max(len(voice) - a, 0)]; voice[a:a + len(x)] += x
with wave.open(str(out / "narration.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(voice, -1, 1) * 32767).astype(np.int16).tobytes())
style = music.bed(total, out / "bed.wav", week.get("music"), fade_in=0.1, fade_out=2.0, cuts=starts[1:])
print("music", style, "narrated" if narrate else "music only", flush=True)
# same mix as the briefings: music ducked under the voice, then loudness-normalized
run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "narration.wav"), "-i", str(out / "bed.wav"), "-filter_complex",
     ("[1:a]volume=0.5[bed];[bed][0:a]sidechaincompress=threshold=0.05:ratio=6:attack=40:release=500:makeup=1[ducked];"
      "[0:a][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0," if narrate else "[1:a]")
     + "loudnorm=I=-15:TP=-1.5:LRA=11[a]", "-map", "[a]", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), str(out / "mix.m4a")])

# slideshow reel: each 4:5 slide centred on a 9:16 canvas of the brand yellow (the ivory cover on ivory)
inputs = []
for k in range(n): inputs += ["-loop", "1", "-t", str(durs[k]), "-i", str(out / f"slide_{k+1:02d}.png")]
pads = "".join(f"[{k}:v]pad=1080:1920:0:285:color={'0xF5F2EA' if k == 0 else '0xFFE600'},setsar=1,fps=24[v{k}];" for k in range(n))
run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-i", str(out / "mix.m4a"),
     "-filter_complex", pads + "".join(f"[v{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[v]",
     "-map", "[v]", "-map", f"{n}:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "copy",
     "-shortest", "-movflags", "+faststart", str(out / "carousel.mp4")])

one = lambda x: " ".join(str(x or "").split())
AI = week.get("topic") == "ai"  # AI 테크 계정 (CONTENT_RULES.md)
FOLLOW = ("매일 07:00 간밤의 AI / 18:00 국내 AI·테크를 1분 브리핑으로 → 알아야 써먹습니다, 팔로우" if AI else
          "매일 07:00 세계·시장 / 18:00 국내 이슈를 3분 브리핑으로 → 팔로우하고 받아보기")
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
              " ".join("#" + k.replace(" ", "") for k in dict.fromkeys(list(week.get("keywords") or [])[:3] + (["AI뉴스", "인공지능"] if AI else ["오늘의뉴스", "경제뉴스"])))]
    (out / "caption.txt").write_text("\n".join(lines) + "\n")
    print("DONE", n, "slides", round(total, 1), "seconds", out / "slide_01.png", "reel", out / "carousel.mp4", "caption", out / "caption.txt")
    sys.exit(0)
lines = [f"📌 {one(week['title'])} ({week.get('week_label', '')})", ""]
lines += [f"{'➊➋➌➍➎➏➐'[i]} {one(it['headline'])}" + (f" — {one(it['num'])}" if it.get("num") else "") for i, it in enumerate(week["items"])]
lines += ["", "🔖 저장해두고 월요일 아침에 다시 보세요"]
if week.get("question"): lines.append(f"💬 {one(week['question'])}")
lines += [FOLLOW,
          "출처: " + " · ".join(dict.fromkeys(it.get("source") for it in week["items"] if it.get("source"))),
          " ".join("#" + k.replace(" ", "") for k in dict.fromkeys(list(week.get("keywords") or [])[:3] + (["AI뉴스", "주간AI"] if AI else ["주간뉴스", "경제뉴스"])))]
(out / "caption.txt").write_text("\n".join(lines) + "\n")
print("DONE", n, "slides", round(total, 1), "seconds", out / "slide_01.png", "reel", out / "carousel.mp4", "caption", out / "caption.txt")
