#!/usr/bin/env python3
"""Photo feed cards (AI account): a real photo behind a big before → after number and a two-line headline.
Usage: python3 feed_card.py cards.json out_dir
cards.json: {"cards": [{"photo": "path or URL", "kicker", "old", "new", "num_label", "tag", "sub", "head", "credit"}, ...]}
- "head": two lines split by \\n; wrap the accent words in [[ ]] (shown in the brand yellow).
- "old" is struck through, then "new" counts up; leave "old" out for a single number.
- "credit": the photo's source and licence (e.g. "사진 Wikimedia Commons · CC BY 2.0"); always fill it.
Output per card n: card{n}.png (4:5 still for a carousel), card{n}.mp4 (9:16, 6s, motion), and reel.mp4 (all cards in a row).
"""
import json, pathlib, subprocess, sys
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
cards = json.load(open(sys.argv[1]))["cards"]
out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
FPS = 24
tpl = (HERE / "feed_tpl.html").read_text()

def page_for(pg, card, reel):
    card = dict(card)
    if not str(card["photo"]).startswith(("http:", "https:", "data:")):
        card["photo"] = (pathlib.Path(sys.argv[1]).parent / card["photo"]).resolve().as_uri()
    html = tpl.replace("<script>", f"<script>window.CARD={json.dumps(card, ensure_ascii=False)};window.REEL={str(reel).lower()};</script><script>", 1)
    f = out / "card.html"; f.write_text(html.replace("url(fonts/", f"url({(HERE / 'fonts').resolve().as_uri()}/"))
    pg.set_viewport_size({"width": 1080, "height": 1920 if reel else 1350})
    pg.goto(f.as_uri()); pg.evaluate("document.fonts.ready.then(()=>{FIT=0})")

with sync_playwright() as p:
    try: b = p.chromium.launch()
    except Exception:
        b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page()
    for n, card in enumerate(cards, 1):
        page_for(pg, card, False); pg.evaluate("window.seek(99)")
        pg.locator("#stage").screenshot(path=str(out / f"card{n}.png"))
        page_for(pg, card, True)
        secs = float(card.get("seconds", 6)); frames = out / f"frames{n}"; frames.mkdir(exist_ok=True)
        for f in range(int(secs * FPS)):
            pg.evaluate(f"window.seek({f / FPS})"); pg.locator("#stage").screenshot(path=str(frames / f"f{f:04d}.png"))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f%04d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", str(out / f"card{n}.mp4")], check=True)
        print("card", n, out / f"card{n}.png", out / f"card{n}.mp4")
    b.close()

lst = out / "list.txt"; lst.write_text("".join(f"file 'card{n}.mp4'\n" for n in range(1, len(cards) + 1)))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out / "reel.mp4")], check=True)
print("DONE", out / "reel.mp4")
