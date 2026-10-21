#!/usr/bin/env python3
"""Morning/evening brief reel builder.
Usage: TYPECAST_API_KEY=... python3 build.py brief.json out_dir
Needs: playwright (chromium), ffmpeg, numpy, Noto Sans CJK KR fonts.
brief.json schema: see brief_example.json (AM) / brief_pm_example.json (PM).
Output: out_dir/final.mp4 (1080x1920, narration + ducked music bed), out_dir/cover.jpg, out_dir/preview_*.png

Cover: Instagram picks the reel's grid/feed cover from the video itself (the publish tool has no cover option),
so the opening scene is drawn fully composed on every frame (no typing, no cursor) and kept inside the 3:4 grid crop.
Set NO_TTS=1 for a silent test build (no Typecast call; durations estimated from script length).

Issue art (center of scenes 2-4): each issue may set "icon" (a Fluent Emoji 3D name such as "Fire engine", or a glyph
such as "🇺🇸"; a list = fallbacks in order) plus optional "motion" (bob|sway|pulse|shake|spin|drive). One issue may set
"image_prompt" for an AI illustration (needs GEMINI_API_KEY; falls back to its icon). RECENT_ICONS=path to a text file
of icon names used in recent reels (one per line) so they are skipped. CHECK_ART=1 resolves the art and exits.
"""
import base64, json, os, pathlib, subprocess, sys, time, unicodedata, urllib.parse, urllib.request, wave
import numpy as np

HERE = pathlib.Path(__file__).parent
brief = json.load(open(sys.argv[1]))
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
NO_TTS = os.environ.get("NO_TTS") == "1"
CHECK_ART = os.environ.get("CHECK_ART") == "1"
KEY = "" if NO_TTS or CHECK_ART else os.environ["TYPECAST_API_KEY"]
VOICE = brief.get("voice_id", "tc_68d4b115f0486108a7eefb37")
FPS = 24; PAD = 0.9; SR = 44100
n_scenes = 6 if brief.get("edition") == "pm" else 7
assert len(brief["scripts"]) == n_scenes, f"scripts must have {n_scenes} entries"

def run(cmd): subprocess.run(cmd, check=True)

# ---------- 0. issue art ----------
FLUENT = "https://raw.githubusercontent.com/microsoft/fluentui-emoji/main/assets/"
STYLE = ("Bold flat editorial illustration for a news card, thick black outlines, flat colors limited to black, white, "
         "red #E8202A and blue #1F5FD6 accents, one clear central subject, simple shapes, centered, plain solid {bg} "
         "background, no text, no letters, no numbers, no logos, no real or recognizable people. Subject: ")

def fetch(url, data=None, headers={}, timeout=25):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=timeout) as r:
            return r.read()
    except Exception as e:
        if getattr(e, "code", None) != 404: print("art fetch failed", url[:90], e, flush=True)
        return None

def fluent(name):
    g = name.replace("\ufe0f", "")
    if not name.isascii():  # a single-codepoint glyph maps to its Unicode name; flags etc. stay glyphs
        if len(g) != 1: return None
        try: name = unicodedata.name(g).lower()
        except ValueError: return None
    n = name.strip(); n = n[:1].upper() + n[1:].lower(); sn = n.lower().replace(" ", "_")
    for path in (f"{n}/3D/{sn}_3d.png", f"{n}/Default/3D/{sn}_3d_default.png"):
        png = fetch(FLUENT + urllib.parse.quote(path))
        if png and png[:4] == b"\x89PNG": return png
    return None

def ai_image(prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key: return None
    model = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    bg = "near-black #111111" if brief.get("edition") == "pm" else "bright yellow #FFE600"
    body = json.dumps({"contents": [{"parts": [{"text": STYLE.format(bg=bg) + prompt}]}],
                       "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "1:1"}}}).encode()
    r = fetch(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", body,
              {"x-goog-api-key": key, "Content-Type": "application/json"}, timeout=120)
    try:
        for part in json.loads(r)["candidates"][0]["content"]["parts"]:
            if "inlineData" in part: return base64.b64decode(part["inlineData"]["data"])
    except Exception as e:
        print("ai image failed", e, flush=True)
    return None

rp = os.environ.get("RECENT_ICONS")
recent = {l.strip().lower() for l in pathlib.Path(rp).read_text().splitlines() if l.strip()} if rp and pathlib.Path(rp).exists() else set()
used, ai_done = set(), False
for k, it in enumerate(brief["issues"], 1):
    art = None
    if it.get("image_prompt") and not ai_done:
        png = ai_image(it["image_prompt"])
        if png:
            ai_done = True; art = {"src": "data:image/png;base64," + base64.b64encode(png).decode(), "ai": True}
            (out / f"art{k}.png").write_bytes(png); it["icon_used"] = "AI"
    cands = it.get("icon") or []
    cands = [cands] if isinstance(cands, str) else cands
    for fresh_only in (True, False):
        if art: break
        for c in cands:
            key_ = c.strip().lower()
            if key_ in used or (fresh_only and key_ in recent): continue
            png = fluent(c)
            if png: art = {"src": "data:image/png;base64," + base64.b64encode(png).decode()}
            elif not c.isascii(): art = {"glyph": c}  # flags and other glyphs Fluent lacks: drawn with the emoji font
            if art: used.add(key_); it["icon_used"] = c; break
    if art: art["motion"] = it.get("motion", "bob"); it["art"] = art
    print("art", k, it.get("icon_used", "none (code-drawn fallback)"), flush=True)
(out / "icons_used.txt").write_text("".join(it["icon_used"] + "\n" for it in brief["issues"] if it.get("icon_used") not in (None, "AI")))
if CHECK_ART: sys.exit(0)

# ---------- 1. TTS ----------
durs = []
for i, text in enumerate(brief["scripts"], 1):
    mp3 = out / f"v{i}.mp3"
    if not mp3.exists():
        if NO_TTS:
            run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono",
                 "-t", str(round(len(text) * 0.12, 2)), str(mp3)])
        else:
            body = json.dumps({"text": text, "model": "ssfm-v30", "voice_id": VOICE,
                               "prompt": {"emotion_preset": "normal", "emotion_intensity": 1},
                               "output": {"audio_format": "mp3"}}).encode()
            req = urllib.request.Request("https://api.typecast.ai/v1/text-to-speech", data=body,
                                         headers={"X-API-KEY": KEY, "Content-Type": "application/json"})
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(req, timeout=180) as r: mp3.write_bytes(r.read())
                    break
                except Exception as e:
                    if attempt == 3: raise
                    time.sleep(5)
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                       "-of", "csv=p=0", str(mp3)]))
    durs.append(round(d, 2)); print("tts", i, durs[-1], flush=True)
scene_durs = [d + PAD for d in durs]
brief["durations"] = scene_durs
total = sum(scene_durs)

# ---------- 2. render frames ----------
html = (HERE / "scene_tpl.html").read_text().replace("__CONTENT__", json.dumps(brief, ensure_ascii=False))
(out / "scene.html").write_text(html)
frames = out / "frames"; frames.mkdir(exist_ok=True)
for old in frames.glob("f*.png"): old.unlink()
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception:  # pip playwright newer than the preinstalled browser: use the bundled chromium directly
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto((out / "scene.html").resolve().as_uri()); pg.wait_for_timeout(600)
    n = int(total * FPS)
    for f in range(n):
        pg.evaluate(f"window.seek({f/FPS})"); pg.screenshot(path=str(frames / f"f{f:05d}.png"))
        if f % 300 == 0: print("frame", f, "/", n, flush=True)
    # preview sheet for QA
    for i, s in enumerate(scene_durs):
        T = sum(scene_durs[:i]) + s * 0.75; pg.evaluate(f"window.seek({T})")
        pg.screenshot(path=str(out / f"preview_{i+1}.png"))
    b.close()
# frame 0 is the reel cover; keep a copy so it can be checked before publishing
run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(frames / "f00000.png"), "-q:v", "2", str(out / "cover.jpg")])

# ---------- 3. narration track (padded) ----------
parts = []
for i, (d, L) in enumerate(zip(durs, scene_durs), 1):
    seg = out / f"seg{i}.wav"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / f"v{i}.mp3"), "-af", f"adelay=300|300,apad=whole_dur={L}",
         "-t", str(L), "-ar", str(SR), "-ac", "2", str(seg)])
    parts.append(seg.name)
(out / "list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(out / "list.txt"),
     "-c:a", "pcm_s16le", str(out / "narration.wav")])

# ---------- 4. music bed (synthesized, royalty-free) ----------
def music(LEN, path):
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
    fade = int(SR * 1.0); mix[:, :fade] *= np.linspace(0, 1, fade); mix[:, -int(SR*3):] *= np.linspace(1, 0, int(SR*3))
    mix /= np.max(np.abs(mix)) * 1.05; pcm = (mix.T * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
music(total, out / "bed.wav")

# ---------- 5. mix + mux ----------
run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / "narration.wav"), "-i", str(out / "bed.wav"), "-filter_complex",
     "[1:a]volume=0.5[bed];[bed][0:a]sidechaincompress=threshold=0.05:ratio=6:attack=40:release=500:makeup=1[ducked];"
     "[0:a][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]",
     "-map", "[a]", "-c:a", "aac", "-b:a", "192k", str(out / "mix.m4a")])
run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f%05d.png"), "-i", str(out / "mix.m4a"),
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-c:a", "copy", "-shortest",
     "-movflags", "+faststart", str(out / "final.mp4")])
print("DONE", out / "final.mp4", "seconds", round(total, 1), "cover", out / "cover.jpg")
