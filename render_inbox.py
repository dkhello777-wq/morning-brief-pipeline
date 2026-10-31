#!/usr/bin/env python3
"""GitHub Actions side of the pipeline (.github/workflows/render.yml): render one inbox file and publish the results.
Usage: python3 render_inbox.py inbox/<id>.json work_dir <id>
The inbox file is a brief (build.py) or, with "kind": "breaking" or a week "items" list, a carousel (carousel.py).
A brief may list "shorts_to_build": [1, 2] for one-issue shorts (default none). RECENT_ICONS come from "recent_icons".
Everything lands on the public release render-<id>: final*.mp4 / carousel.mp4, cover*.jpg, caption*.txt and
status.json {"id", "videos": {"main": url, "short1": url, ...}, "captions": {...}, "log": [...]}.
"""
import json, os, pathlib, subprocess, sys

src, work, rid = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
HERE = pathlib.Path(__file__).parent.resolve()
REPO = os.environ.get("GITHUB_REPOSITORY", "dkhello777-wq/morning-brief-pipeline")
work.mkdir(parents=True, exist_ok=True)
doc = json.loads(src.read_text())
carousel = doc.get("kind") == "breaking" or "items" in doc
brief_path = work / "brief.json"; brief_path.write_text(json.dumps(doc, ensure_ascii=False))
env = dict(os.environ)
icons = work / "recent_icons.txt"; icons.write_text("".join(i + "\n" for i in doc.get("recent_icons", [])))
env["RECENT_ICONS"] = str(icons)
log, files, videos, captions = [], [], {}, {}

def run(cmd, extra={}):
    p = subprocess.run(cmd, env={**env, **extra}, capture_output=True, text=True, cwd=HERE)
    keep = [l for l in (p.stdout + p.stderr).splitlines()
            if l.startswith(("art", "music", "photo", "tts", "DONE", "WARN", "Traceback")) or "Error" in l]
    log.extend(keep); print(p.stdout[-4000:], p.stderr[-4000:], flush=True)
    if p.returncode: raise SystemExit(f"{cmd} failed")

out = work / "out"
if carousel:
    run(["python3", "carousel.py", str(brief_path), str(out)])
    files += [out / "carousel.mp4", out / "caption.txt", out / "slide_01.png"]
    videos["main"] = "carousel.mp4"; captions["main"] = "caption.txt"
else:
    run(["python3", "build.py", str(brief_path), str(out)])
    files += [out / "final.mp4", out / "cover.jpg", out / "caption.txt", out / "icons_used.txt"]
    videos["main"] = "final.mp4"; captions["main"] = "caption.txt"
    for n in doc.get("shorts_to_build", []):
        run(["python3", "build.py", str(brief_path), str(out)], {"SHORT": str(n)})
        files += [out / f"final_short{n}.mp4", out / f"cover_short{n}.jpg", out / f"caption_short{n}.txt"]
        videos[f"short{n}"] = f"final_short{n}.mp4"; captions[f"short{n}"] = f"caption_short{n}.txt"
    files += sorted(out.glob("preview_*.png"))[:3]

tag = f"render-{rid}"
base = f"https://github.com/{REPO}/releases/download/{tag}/"
status = {"id": rid, "videos": {k: base + v for k, v in videos.items()},
          "captions": {k: (out / v).read_text() for k, v in captions.items()}, "log": log}
(out / "status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1))
files = [str(f) for f in files if f.exists()] + [str(out / "status.json")]
subprocess.run(["gh", "release", "create", tag, "--title", tag, "--notes", f"Rendered from inbox/{rid}.json",
                "--latest=false", *files], check=True, cwd=HERE)
print("released", base + "status.json")
