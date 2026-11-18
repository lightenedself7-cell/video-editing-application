#!/usr/bin/env python3
"""Option B: recreate a winning (outlier) thumbnail with YOUR face, via Gemini image editing.

Needs GEMINI_API_KEY in the environment or in <repo>/.env  (Google AI Studio key).
UNTESTED until a key is added. Cost is roughly $0.14-0.24 per image (Nano Banana Pro).

Lessons carried over from public notes on this technique:
  * 2 reference photos is the sweet spot (1 loses likeness, 3+ makes the model redraw everything)
  * say "16:9" explicitly or the model returns squares
  * label the images in the prompt ("IMAGE 1 = reference face, IMAGE 2 = thumbnail")
  * keep prompts short; use a second --edit pass for text/colour changes
  * a reference whose head angle matches the source face blends far better, so give --refs
    photos facing left, right and straight and pick per thumbnail

Usage:
  python skills/thumbnail-maker/recreate_thumbnail.py --youtube https://youtu.be/VIDEO_ID \
      --refs photos/me_left.jpg photos/me_front.jpg --out edit/thumbs/idea1
  python skills/thumbnail-maker/recreate_thumbnail.py --source thumb.jpg --refs a.jpg b.jpg -n 3
  python skills/thumbnail-maker/recreate_thumbnail.py --edit edit/thumbs/idea1_1.png \
      --prompt "Change the text to 'FREE AI SITE'. Make the background teal."
"""
import argparse
import io
import os
import re
import sys
import urllib.request
from pathlib import Path

MODEL = "gemini-3-pro-image-preview"
ROOT = Path(__file__).resolve().parents[2]


def api_key():
    key = os.environ.get("GEMINI_API_KEY")
    env = ROOT / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("GEMINI_API_KEY="):
                key = line.split("=", 1)[1].strip().strip("\"'")
    if not key:
        sys.exit("GEMINI_API_KEY not found. Add it to the environment or to .env in the repo root.")
    return key


def youtube_thumb(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", url)
    if not m:
        sys.exit(f"Could not find a video id in {url}")
    for name in ("maxresdefault", "hqdefault"):
        try:
            return urllib.request.urlopen(f"https://img.youtube.com/vi/{m.group(1)}/{name}.jpg", timeout=20).read()
        except Exception:
            continue
    sys.exit("Could not download that thumbnail")


def load_bytes(src):
    if str(src).startswith("http"):
        return urllib.request.urlopen(src, timeout=20).read()
    return Path(src).read_bytes()


def generate(parts, n, out):
    from google import genai
    from google.genai import types
    from PIL import Image

    client = genai.Client(api_key=api_key())
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    written = []
    for i in range(1, n + 1):
        resp = client.models.generate_content(
            model=MODEL,
            contents=parts,
            config=types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )
        img = None
        for cand in resp.candidates or []:
            for p in cand.content.parts:
                if getattr(p, "inline_data", None) and p.inline_data.data:
                    img = Image.open(io.BytesIO(p.inline_data.data))
        if img is None:
            print(f"variation {i}: no image returned", file=sys.stderr)
            continue
        path = out.with_name(f"{out.name}_{i}.png") if n > 1 or not out.suffix else out
        img.save(path)
        print("wrote", path)
        written.append(path)
    return written


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--youtube", help="video URL whose thumbnail to recreate")
    ap.add_argument("--source", help="thumbnail file or URL")
    ap.add_argument("--refs", nargs="+", help="1-2 photos of you (see notes on head angle)")
    ap.add_argument("--edit", help="existing image to refine (edit mode)")
    ap.add_argument("--prompt", default="", help="extra instructions (required for --edit)")
    ap.add_argument("-n", type=int, default=3, help="variations (default 3)")
    ap.add_argument("--out", default="edit/thumbnails/recreated")
    a = ap.parse_args()

    from google.genai import types

    def img(b):
        return types.Part.from_bytes(data=b, mime_type="image/png" if b[:4] == b"\x89PNG" else "image/jpeg")

    if a.edit:
        if not a.prompt:
            sys.exit("--edit needs --prompt")
        text = ("Edit this 16:9 YouTube thumbnail. Keep everything the same except the following change. "
                + a.prompt)
        generate([img(Path(a.edit).read_bytes()), text], 1, a.out)
        return

    if not (a.youtube or a.source) or not a.refs:
        sys.exit("Need --youtube or --source, plus --refs")
    source = youtube_thumb(a.youtube) if a.youtube else load_bytes(a.source)
    refs = [Path(r).read_bytes() for r in a.refs[:2]]
    labels = " ".join(f"IMAGE {i + 1} is a reference photo of the person." for i in range(len(refs)))
    text = (f"{labels} IMAGE {len(refs) + 1} is a YouTube thumbnail. Recreate the thumbnail as a 16:9 image, "
            "a 100% exact duplicate except replace the person's face and head with the person from the reference "
            "photos, matching the original head angle and lighting. Keep all text, layout and colours identical. "
            + a.prompt)
    generate([img(b) for b in refs] + [img(source), text], a.n, a.out)


if __name__ == "__main__":
    main()
