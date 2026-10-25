#!/usr/bin/env python3
"""Weekly save-for-later carousel ("이번 주 돈 되는 뉴스 5").
Usage: python3 carousel.py week.json out_dir
week.json schema: see week_example.json (3-7 items; each tag, headline, optional num, body, source;
"dates" e.g. "10.19–10.25" is shown large on the cover beside week_label).
Output: out_dir/slide_01.png ... (1080x1350, Instagram 4:5 carousel), out_dir/caption.txt,
and out_dir/carousel.mp4 (the same slides as a 1080x1920 slideshow reel, 3.5s each, for publish tools that only take reels),
with a synthesized royalty-free music bed (the same sound as the daily briefings) and a soft swish on each slide change.
"""
import json, pathlib, subprocess, sys, wave
import numpy as np

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

# ---------- music bed (synthesized, royalty-free; same chords and tempo as build.py) ----------
SR = 44100
def music(LEN, path, cuts):
    BPM = 108; beat = 60 / BPM; bar = beat * 4; N = int(SR * LEN); rng = np.random.default_rng(7)
    def env(n, a, d, s, r, hold):
        A = int(a * SR); Dd = int(d * SR); R = int(r * SR); H = max(int(hold * SR) - A - Dd, 0)
        e = np.concatenate([np.linspace(0, 1, A), np.linspace(1, s, Dd), np.full(H, s), np.linspace(s, 0, R)])
        return np.concatenate([e, np.zeros(max(n - len(e), 0))])[:n]
    def note(f, dur, a=.01, d=.15, s=.5, r=.25, bright=.4):
        n = int(SR * (dur + r)); tt = np.arange(n) / SR
        sig = np.sin(2*np.pi*f*tt) + bright*0.35*np.sin(2*np.pi*2*f*tt) + bright*0.12*np.sin(2*np.pi*3*f*tt)
        return sig * (1 + 0.004*np.sin(2*np.pi*5.5*tt)) * env(n, a, d, s, r, dur)
    mix = np.zeros((2, N))
    def add(sig, at, gain=1.0, pan=0.0):
        i = int(at * SR); j = min(i + len(sig), N)
        if i >= N: return
        s = sig[:j-i] * gain; mix[0, i:j] += s * (1 - max(pan, 0)); mix[1, i:j] += s * (1 + min(pan, 0))
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [[62, 66, 69, 74], [57, 61, 64, 69], [59, 62, 66, 71], [55, 59, 62, 67]]; bass = [38, 33, 35, 31]
    for b_ in range(int(LEN / bar) + 1):
        ch = chords[b_ % 4]; t0 = b_ * bar
        for m in ch: add(note(midi(m), bar*0.95, a=.25, d=.4, s=.6, r=.6, bright=.25), t0, .07, (m % 3 - 1) * 0.3)
        for k in range(8):
            m = ch[(k*2) % 4] + (12 if k % 3 == 2 else 0)
            add(note(midi(m), beat*0.35, a=.003, d=.12, s=.3, r=.2, bright=.8), t0 + k*beat/2, .09, .25*np.sin(k))
        for st in (0, beat*2): add(note(midi(bass[b_ % 4]), beat*1.2, a=.005, d=.2, s=.5, r=.2, bright=.2), t0 + st, .16)
        for k in range(4):
            n = int(SR * 0.18); tt = np.arange(n) / SR
            kick = np.sin(2*np.pi*(55 + 90*np.exp(-tt*40))*tt) * np.exp(-tt*22)
            if k % 2 == 0: add(kick, t0 + k*beat, .35)
            for h in range(2):
                n2 = int(SR * 0.05); sh = rng.standard_normal(n2) * np.exp(-np.arange(n2)/SR*120)
                add(sh, t0 + k*beat + h*beat/2, .035 if h else .02, .4)
    kern = np.ones(6) / 6; mix = np.array([np.convolve(c, kern, 'same') for c in mix])
    n = int(SR * 0.22); tt = np.arange(n) / SR  # page-turn swish ending on each slide change
    swish = np.convolve(rng.standard_normal(n), np.ones(7) / 7, "same") * np.sin(np.pi * tt / tt[-1]) ** 2 * 0.5
    for c in cuts: add(swish, c - 0.12, 1.0, 0.0)
    fade = int(SR * 0.1); mix[:, :fade] *= np.linspace(0, 1, fade); mix[:, -int(SR*2):] *= np.linspace(1, 0, int(SR*2))
    mix /= np.max(np.abs(mix)) * 1.05; pcm = (mix.T * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
music(SLIDE_S * n, out / "bed.wav", [SLIDE_S * k for k in range(1, n)])

# slideshow reel: each 4:5 slide centred on a 9:16 canvas of the brand yellow (the ivory cover on ivory)
inputs = []
for k in range(n): inputs += ["-loop", "1", "-t", str(SLIDE_S), "-i", str(out / f"slide_{k+1:02d}.png")]
pads = "".join(f"[{k}:v]pad=1080:1920:0:285:color={'0xF5F2EA' if k == 0 else '0xFFE600'},setsar=1,fps=24[v{k}];" for k in range(n))
run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-i", str(out / "bed.wav"),
     "-filter_complex", pads + "".join(f"[v{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[v];[{n}:a]loudnorm=I=-16:TP=-1.5:LRA=11[a]",
     "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
     "-shortest", "-movflags", "+faststart", str(out / "carousel.mp4")])

one = lambda x: " ".join(str(x or "").split())
lines = [f"📌 {one(week['title'])} ({week.get('week_label', '')})", ""]
lines += [f"{'➊➋➌➍➎➏➐'[i]} {one(it['headline'])}" + (f" — {one(it['num'])}" if it.get("num") else "") for i, it in enumerate(week["items"])]
lines += ["", "🔖 저장해두고 월요일 아침에 다시 보세요"]
if week.get("question"): lines.append(f"💬 {one(week['question'])}")
lines += ["매일 07:00 세계·시장 / 18:00 국내 이슈를 3분 브리핑으로 → 팔로우하고 받아보기",
          "출처: " + " · ".join(dict.fromkeys(it.get("source") for it in week["items"] if it.get("source"))),
          " ".join("#" + k.replace(" ", "") for k in dict.fromkeys(list(week.get("keywords") or [])[:3] + ["주간뉴스", "경제뉴스"]))]
(out / "caption.txt").write_text("\n".join(lines) + "\n")
print("DONE", n, "slides", out / "slide_01.png", "reel", out / "carousel.mp4", "caption", out / "caption.txt")
