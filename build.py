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

Hook cover: "hook": {"q": "question line", "hi": "number line"} replaces the opening title with a two-line hook
(line 2 on an accent bar). Each issue may carry its own "hook" for its short.

First 3 seconds: HOOK_STYLE=punch (default) holds the finished cover for 0.25s, then cuts to the hook alone in large
type (number counting up, marker stroke, lead art) with a soft whoosh; live keeps the cover and moves it; off is the old
static opening. With punch/live the voice starts on frame 1, the music has no slow fade-in, and burned-in subtitles
follow the narration (SUBTITLES=0 turns them off). Frame 0, the reel cover, is the same in every style.

One-issue short: SHORT=n (1-3) builds a 10-15s reel of issue n (hook cover, the issue scene, an end card pointing to
the full briefing; with a HOOK_STYLE the issue's narration starts under the cover) into the same out_dir as the briefing, reusing its narration (v{n+1}.mp3), AI art and icon choice,
so a short costs no extra TTS or image calls. Outputs carry a _short{n} suffix (final_short1.mp4, cover_short1.jpg...).

Captions: out_dir/caption.txt (or caption_short{n}.txt) is written from the brief in the fixed account template
(see CONTENT_RULES.md); issues may set "summary" and "keywords", the brief "question" and "keywords".
"""
import base64, json, os, pathlib, re, subprocess, sys, time, unicodedata, urllib.parse, urllib.request, wave
import numpy as np

HERE = pathlib.Path(__file__).parent
brief = json.load(open(sys.argv[1]))
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
NO_TTS = os.environ.get("NO_TTS") == "1"
CHECK_ART = os.environ.get("CHECK_ART") == "1"
KEY = "" if NO_TTS or CHECK_ART else os.environ["TYPECAST_API_KEY"]
VOICE = brief.get("voice_id", "tc_68d4b115f0486108a7eefb37")
FPS = 24; PAD = 0.6; SR = 44100
PM = brief.get("edition") == "pm"
n_scenes = 6 if PM else 7
assert len(brief["scripts"]) == n_scenes, f"scripts must have {n_scenes} entries"
SHORT = int(os.environ.get("SHORT", "0"))
assert 0 <= SHORT <= len(brief["issues"]), "SHORT must name an issue (1-3)"
SFX = f"_short{SHORT}" if SHORT else ""
COVER_S, END_S = 1.6, 2.4  # hook cover and end card of a short
# first 3 seconds: HOOK_STYLE=punch (cut from the cover to the hook in large type), live (the cover moves) or off
# (the old static cover with the voice 0.3s in). With a style, the voice starts on frame 1, burned-in subtitles
# follow the narration (SUBTITLES=0 turns them off) and a short's narration starts under its cover.
HOOK_STYLE = os.environ.get("HOOK_STYLE", brief.get("hook_style", "punch"))
assert HOOK_STYLE in ("punch", "live", "off"), "HOOK_STYLE must be punch, live or off"
brief["hook_style"] = "" if HOOK_STYLE == "off" else HOOK_STYLE
SUBTITLES = HOOK_STYLE != "off" and os.environ.get("SUBTITLES", "1") != "0"

def run(cmd): subprocess.run(cmd, check=True)

# ---------- captions (fixed account template, CONTENT_RULES.md) ----------
def caption(b, short=0):
    one = lambda x: " ".join(str(x or "").split())
    hook = lambda h, fb: one(f"{h.get('q', '')} {h.get('hi', '')}") if h else one(fb)
    tags = lambda kws: " ".join("#" + k.replace(" ", "").lstrip("#") for k in dict.fromkeys(kws) if k)
    pm = b.get("edition") == "pm"
    follow = "매일 07:00 세계·시장 / 18:00 국내 이슈를 3분 브리핑으로 → 팔로우하고 받아보기"
    if short:
        it = b["issues"][short - 1]
        lines = [f"📌 {hook(it.get('hook'), it.get('headline'))}", "", one(it.get("summary") or it.get("headline")), ""]
        q = it.get("question") or b.get("question")
        if q: lines.append(f"💬 {one(q)}")
        lines += [f"{'오늘의 다른 국내 이슈' if pm else '간밤의 다른 세계 이슈'}는 → 프로필의 3분 브리핑에서",
                  f"출처: {it.get('source', '')}", tags((it.get("keywords") or [])[:3] + ["오늘의뉴스"])]
        return "\n".join(lines) + "\n"
    lines = [f"{'🌙' if pm else '🌅'} {hook(b.get('hook'), b.get('title'))}", ""]
    for n, it in zip("➊➋➌", b["issues"]):
        lines.append(f"{n} {one(it.get('short'))} — {one(it.get('summary') or it.get('headline'))}")
    m = b.get("market") or {}
    if m.get("headline"): lines.append(f"📈 {one(m['headline'])}" + (f" ({one(m['note'])})" if m.get("note") else ""))
    if (b.get("ai") or {}).get("short"): lines.append(f"🤖 {one(b['ai'].get('company'))} {one(b['ai']['short'])}")
    lines.append("")
    if b.get("question"): lines += [f"💬 {one(b['question'])}", ""]
    srcs = [it.get("source") for it in b["issues"]] + [(b.get("ai") or {}).get("source")]
    kws = list(b.get("keywords") or []) + [k for it in b["issues"] for k in (it.get("keywords") or [])[:1]]
    lines += [follow, "출처: " + " · ".join(dict.fromkeys(s for s in srcs if s)),
              tags(kws[:3] + ["오늘의뉴스", "경제뉴스"])]
    return "\n".join(lines) + "\n"

if os.environ.get("CAPTION_ONLY") == "1":
    print(caption(brief, SHORT)); sys.exit(0)

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
    g = name.replace(chr(0xFE0F), "")
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

chosen = json.loads((out / "art_used.json").read_text()) if (out / "art_used.json").exists() else {}
rp = os.environ.get("RECENT_ICONS")
recent = {l.strip().lower() for l in pathlib.Path(rp).read_text().splitlines() if l.strip()} if rp and pathlib.Path(rp).exists() else set()
used, ai_done = set(), False
for k, it in enumerate(brief["issues"], 1):
    art = None
    if it.get("image_prompt") and not ai_done:
        prev = out / f"art{k}.png"  # already generated for this brief (a short after its briefing, or a rerun)
        png = prev.read_bytes() if prev.exists() else ai_image(it["image_prompt"])
        if png:
            ai_done = True; art = {"src": "data:image/png;base64," + base64.b64encode(png).decode(), "ai": True}
            (out / f"art{k}.png").write_bytes(png); it["icon_used"] = "AI"
    cands = it.get("icon") or []
    cands = [cands] if isinstance(cands, str) else cands
    if SHORT and chosen.get(str(k)) not in (None, "AI"): cands = [chosen[str(k)]] + cands
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
if not SHORT:
    (out / "art_used.json").write_text(json.dumps({str(k): it["icon_used"] for k, it in enumerate(brief["issues"], 1) if it.get("icon_used")}))
    (out / "icons_used.txt").write_text("".join(it["icon_used"] + "\n" for it in brief["issues"] if it.get("icon_used") not in (None, "AI")))
if CHECK_ART: sys.exit(0)

# ---------- 1. TTS ----------
# scene i (1-based) speaks scripts[i-1] from v{i}.mp3; a short speaks only its issue's script, between silent cards
if SHORT:
    brief["short"] = SHORT
    voiced = [(None, COVER_S), (SHORT + 1, None), (None, END_S)]
else:
    voiced = [(i, None) for i in range(1, n_scenes + 1)]
durs = []
for i, fixed in voiced:
    if i is None:
        durs.append(fixed); continue
    text = brief["scripts"][i - 1]
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
scene_durs = [d if i is None else d + PAD for (i, _), d in zip(voiced, durs)]
starts = [sum(scene_durs[:k]) for k in range(len(scene_durs))]
# clips: (reel second the voice starts, scene number of its mp3, seconds of speech)
clips = [(st + 0.3, i, d) for st, (i, _), d in zip(starts, voiced, durs) if i is not None]
if brief["hook_style"]:
    if SHORT:  # the issue's narration starts under the cover and carries on into the issue scene
        d = durs[1]; scene_durs[1] = max(d + PAD - COVER_S, 1.5); clips = [(0.05, voiced[1][0], d)]
    else:
        clips[0] = (0.05,) + clips[0][1:]

def sub_chunks(text, n=14):
    """Split a script into subtitle lines: sentence by sentence; a long sentence into near-equal word runs,
    breaking after a comma where one falls late enough."""
    out = []
    for sent in re.split(r"(?<=[.?!])\s+", text.strip()):
        size = len(sent.replace(" ", ""))
        if size <= n + 4: out.append(sent); continue
        per = size / -(-size // n); cur = ""
        for w in sent.split():
            k = len(cur.replace(" ", ""))
            if cur and (k + len(w) / 2 > per or (cur.endswith(",") and k >= per * 0.6)): out.append(cur); cur = w
            else: cur = f"{cur} {w}".strip()
        out.append(cur)
    return [c for c in out if c]
subs = []
for at, i, d in clips if SUBTITLES else []:
    cs = sub_chunks(brief["scripts"][i - 1]); w = [len(c) + 2 for c in cs]; acc = 0
    for c, x in zip(cs, w):
        subs.append([round(at + d * acc / sum(w), 2), round(at + d * (acc + x) / sum(w), 2), c.rstrip(".,")]); acc += x
brief["subs"] = subs
total = sum(scene_durs)
brief["durations"] = scene_durs
LIMIT = 16 if SHORT else 62
if total > LIMIT: print(f"WARN length {total:.1f}s is over the {LIMIT}s target: shorten the scripts (CONTENT_RULES.md)", flush=True)

# ---------- 2. render frames ----------
html = (HERE / "scene_tpl.html").read_text().replace("__CONTENT__", json.dumps(brief, ensure_ascii=False))
html = html.replace("__FONT__", (HERE / "fonts" / "PretendardVariable.ttf").resolve().as_uri())
(out / f"scene{SFX}.html").write_text(html)
frames = out / f"frames{SFX}"; frames.mkdir(exist_ok=True)
for old in frames.glob("f*.png"): old.unlink()
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception:  # pip playwright newer than the preinstalled browser: use the bundled chromium directly
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 1080, "height": 1920})
    pg.goto((out / f"scene{SFX}.html").resolve().as_uri()); pg.wait_for_timeout(600)
    n = int(total * FPS)
    for f in range(n):
        pg.evaluate(f"window.seek({f/FPS})"); pg.screenshot(path=str(frames / f"f{f:05d}.png"))
        if f % 300 == 0: print("frame", f, "/", n, flush=True)
    # preview sheet for QA
    for i, s in enumerate(scene_durs):
        T = sum(scene_durs[:i]) + s * 0.75; pg.evaluate(f"window.seek({T})")
        pg.screenshot(path=str(out / f"preview{SFX}_{i+1}.png"))
    b.close()
# frame 0 is the reel cover; keep a copy so it can be checked before publishing
run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(frames / "f00000.png"), "-q:v", "2", str(out / f"cover{SFX}.jpg")])

# ---------- 3. narration track ----------
voice = np.zeros((int(SR * total), 2))
for at, i, _ in clips:
    raw = subprocess.check_output(["ffmpeg", "-loglevel", "error", "-i", str(out / f"v{i}.mp3"), "-f", "s16le",
                                   "-ar", str(SR), "-ac", "2", "-"])
    x = np.frombuffer(raw, np.int16).reshape(-1, 2) / 32768; a = int(at * SR); x = x[:max(len(voice) - a, 0)]
    voice[a:a + len(x)] += x
if brief["hook_style"] == "punch":  # a soft whoosh into the cut to the hook, and a low thump on it
    n = int(SR * 0.25); tt = np.arange(n) / SR; rng = np.random.default_rng(3)
    whoosh = np.convolve(rng.standard_normal(n), np.ones(9) / 9, "same") * (tt / tt[-1]) ** 2 * 0.12
    thump = np.sin(2 * np.pi * (48 + 70 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 14) * 0.35
    a = int(0.25 * SR); voice[max(a - n, 0):a] += whoosh[-min(a, n):, None]; voice[a:a + n] += thump[:, None]
with wave.open(str(out / f"narration{SFX}.wav"), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(voice, -1, 1) * 32767).astype(np.int16).tobytes())

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
    fade = int(SR * (0.1 if brief["hook_style"] else 1.0)); mix[:, :fade] *= np.linspace(0, 1, fade); mix[:, -int(SR*3):] *= np.linspace(1, 0, int(SR*3))
    mix /= np.max(np.abs(mix)) * 1.05; pcm = (mix.T * 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
music(total, out / f"bed{SFX}.wav")

# ---------- 5. mix + mux ----------
run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / f"narration{SFX}.wav"), "-i", str(out / f"bed{SFX}.wav"), "-filter_complex",
     "[1:a]volume=0.5[bed];[bed][0:a]sidechaincompress=threshold=0.05:ratio=6:attack=40:release=500:makeup=1[ducked];"
     "[0:a][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]",
     "-map", "[a]", "-c:a", "aac", "-b:a", "192k", str(out / f"mix{SFX}.m4a")])
run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f%05d.png"), "-i", str(out / f"mix{SFX}.m4a"),
     "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-c:a", "copy", "-shortest",
     "-movflags", "+faststart", str(out / f"final{SFX}.mp4")])
(out / f"caption{SFX}.txt").write_text(caption(brief, SHORT))
print("DONE", out / f"final{SFX}.mp4", "seconds", round(total, 1), "cover", out / f"cover{SFX}.jpg", "caption", out / f"caption{SFX}.txt")
