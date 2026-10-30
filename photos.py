"""Real photos for the AI account's scenes and slides, shared by build.py and carousel.py.
A "photo" field may be:
  - a search string ("Jensen Huang", "Googleplex"): the best freely licensed photo on Wikimedia Commons for it,
  - {"file": "File:Exact name.jpg"}: that Commons file,
  - {"query": "...", "credit": "..."} or a local path / {"path": "...", "credit": "..."} (tests, hand-picked photos).
Only CC0, public domain, CC BY and CC BY-SA photos are used, and the credit line ("사진 <author> · <licence> ·
Wikimedia Commons") is returned so it can be shown on the scene; CC BY / BY-SA require it. Anything that fails
(no network, no free photo) returns None and the caller keeps its old art, so a post never breaks over a photo.
"""
import json, pathlib, re, urllib.parse, urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "daybrief-pipeline/1.0 (https://github.com/dkhello777-wq/morning-brief-pipeline)"}
FREE = re.compile(r"^(cc0|cc[ -]by(-sa)?([ -]\d\.\d)?|public domain|pd\b)", re.I)

def _get(url, timeout=25):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r: return r.read()
    except Exception as e:
        print("photo fetch failed", url[:90], e, flush=True); return None

def _commons(params):
    q = {"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url|mime|size|extmetadata", "iiurlwidth": 1400}
    r = _get(API + "?" + urllib.parse.urlencode({**q, **params}))
    try: pages = json.loads(r)["query"]["pages"].values()
    except Exception: return None
    for p in sorted(pages, key=lambda p: p.get("index", 99)):
        ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "").strip()
        if ii.get("mime") not in ("image/jpeg", "image/png") or min(ii.get("width", 0), ii.get("height", 0)) < 700: continue
        if not FREE.match(lic): continue
        artist = re.sub(r"<[^>]+>", "", md.get("Artist", {}).get("value", "")).strip()
        artist = re.sub(r"\s+", " ", artist)[:40] or "Wikimedia Commons"
        img = _get(ii.get("thumburl") or ii["url"], timeout=40)
        if img: return img, f"사진 {artist} · {lic} · Wikimedia Commons"
    return None

def get(spec, base="."):
    """(image bytes, mime, credit) for a photo spec, or None."""
    if not spec: return None
    if isinstance(spec, str): spec = {"path": spec} if (pathlib.Path(base) / spec).is_file() else {"query": spec}
    got = None
    if spec.get("path"):
        f = pathlib.Path(base) / spec["path"]
        if f.is_file(): got = (f.read_bytes(), spec.get("credit", ""))
    elif spec.get("file"):
        got = _commons({"titles": spec["file"] if spec["file"].startswith("File:") else "File:" + spec["file"]})
    elif spec.get("query"):
        got = _commons({"generator": "search", "gsrsearch": spec["query"] + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 12})
    if not got: return None
    img, credit = got
    mime = "image/png" if img[:4] == b"\x89PNG" else "image/jpeg"
    return img, mime, spec.get("credit") or credit
