#!/usr/bin/env python3
"""Option A: on-brand thumbnail from a theme + a photo of the creator.

Pipeline: rembg cutout -> theme ground (glow orbs from tokens.json) -> big headline
(words wrapped in *asterisks* use the theme highlight colour) -> optional accent chip.
Output is 1280x720 PNG. Free, local, deterministic, matches the channel's themes.

Usage (from repo root, with .venv active):
  python skills/thumbnail-maker/make_thumbnail.py --photo me.jpg \
      --text "JOBS WITH *0* APPLICANTS" --theme teal-spotlight --out thumb.png
  python skills/thumbnail-maker/make_thumbnail.py --photo me.jpg --text "FREE *AI* SITE" \
      --chip "FREE" --side left --variants 3 --out thumb.png   # 3 layout variants
"""
import argparse
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1] / "theme-renderer" / "themes"
W, H = 1280, 720


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def load_theme(name):
    d = ROOT / name
    tokens = json.loads((d / "tokens.json").read_text())
    return d, tokens


def make_ground(tokens):
    c = tokens["colors"]
    img = np.zeros((H, W, 3), dtype=np.float32)
    img[:] = hex_rgb(c["ground"])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # theme orbs are authored for 1920x1080; scale to 1280x720
    s = W / 1920
    for o in tokens.get("ground", {}).get("orbs", []):
        d = np.sqrt((xx - o["cx"] * s) ** 2 + (yy - o["cy"] * s) ** 2) / (o["radius"] * s)
        a = np.clip(1 - d, 0, 1) ** o.get("power", 2) * o.get("strength", 0.5)
        col = np.array(hex_rgb(o["from"]), dtype=np.float32)
        img = img * (1 - a[..., None]) + col * a[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert("RGBA")


def cutout(photo_path):
    # small person-specific model (~170MB); rembg's default model is ~1GB and OOMs in WSL
    from rembg import new_session, remove
    im = Image.open(photo_path).convert("RGBA")
    im.thumbnail((1400, 1400))
    out = remove(im, session=new_session("u2net_human_seg"))
    bbox = out.getchannel("A").getbbox()
    return out.crop(bbox) if bbox else out


def sticker_edge(im, color=(255, 255, 255), width=10):
    a = im.getchannel("A").filter(ImageFilter.MaxFilter(width * 2 + 1)).filter(ImageFilter.GaussianBlur(1.5))
    edge = Image.new("RGBA", im.size, color + (255,))
    edge.putalpha(a)
    pad = width * 2
    canvas = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    canvas.paste(edge, (pad, pad), edge)
    canvas.alpha_composite(im, (pad, pad))
    return canvas


def load_font(theme_dir, tokens, size):
    # Montserrat Black for every theme: thumbnails need maximum weight at small sizes
    font = ImageFont.truetype(str(theme_dir / tokens["fonts"]["regular"]), size)
    try:
        font.set_variation_by_axes([900])
    except Exception:
        pass
    return font


def parse_runs(text):
    """'JOBS WITH *0* APPLICANTS' -> [(word, highlighted)] per line."""
    lines = []
    for raw in text.split("|"):
        words = []
        for tok in re.findall(r"\*[^*]+\*|\S+", raw.strip()):
            hl = tok.startswith("*") and tok.endswith("*")
            words.append((tok.strip("*"), hl))
        lines.append(words)
    return lines


def draw_text(img, lines, theme_dir, tokens, box, size):
    c = tokens["colors"]
    base, hi = hex_rgb(c["text"]), hex_rgb(c.get("pop", c["highlight"]))
    x0, y0, x1, y1 = box
    # shrink until the widest line fits and the block fits vertically
    while size > 40:
        font = load_font(theme_dir, tokens, size)
        d = ImageDraw.Draw(img)
        widths = [sum(d.textlength(w + " ", font=font) for w, _ in ln) for ln in lines]
        if max(widths) <= (x1 - x0) and len(lines) * size * 1.02 <= (y1 - y0):
            break
        size -= 4
    lh = int(size * 1.02)
    y = y0 + ((y1 - y0) - lh * len(lines)) // 2
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    d = ImageDraw.Draw(img)
    for ln in lines:
        x = x0
        for word, hl in ln:
            col = hi if hl else base
            sd.text((x + 6, y + 8), word, font=font, fill=(0, 0, 0, 200))
            d.text((x, y), word, font=font, fill=col, stroke_width=3, stroke_fill=hex_rgb(c["ground"]))
            x += d.textlength(word + " ", font=font)
        y += lh
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)))
    # redraw crisp text over its soft shadow
    y = y0 + ((y1 - y0) - lh * len(lines)) // 2
    d = ImageDraw.Draw(img)
    for ln in lines:
        x = x0
        for word, hl in ln:
            d.text((x, y), word, font=font, fill=hi if hl else base, stroke_width=3, stroke_fill=hex_rgb(c["ground"]))
            x += d.textlength(word + " ", font=font)
        y += lh


def build(photo, text, theme, side, chip, out, person_scale=1.0):
    theme_dir, tokens = load_theme(theme)
    c = tokens["colors"]
    img = make_ground(tokens)
    person = sticker_edge(cutout(photo), width=9)
    ph = int(H * 1.02 * person_scale)
    person = person.resize((int(person.width * ph / person.height), ph), Image.LANCZOS)
    px = W - person.width + 30 if side == "right" else -30
    text_box = (60, 70, W - person.width - 20, H - 70) if side == "right" else (person.width - 10, 70, W - 60, H - 70)
    # text first, person on top so the face is never covered
    draw_text(img, parse_runs(text), theme_dir, tokens, text_box, 190)
    img.alpha_composite(person, (max(px, -person.width // 3), H - person.height + 20))
    if chip:
        d = ImageDraw.Draw(img)
        f = load_font(theme_dir, tokens, 64)
        tw = d.textlength(chip, font=f)
        cx = 60 if side == "right" else W - tw - 120
        d.rounded_rectangle((cx, 36, cx + tw + 56, 120), 18, fill=hex_rgb(c.get("pop", c["highlight"])))
        d.text((cx + 28, 44), chip, font=f, fill=hex_rgb(c["ground"]))
    img.convert("RGB").save(out, quality=95)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--photo", required=True)
    ap.add_argument("--text", required=True, help="3-4 words; *word* = highlight; | = line break")
    ap.add_argument("--theme", default="teal-spotlight")
    ap.add_argument("--side", choices=["left", "right"], default="right", help="side the person stands on")
    ap.add_argument("--chip", default="", help="optional small badge, e.g. FREE")
    ap.add_argument("--variants", type=int, default=1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    for i in range(a.variants):
        side = a.side if i % 2 == 0 else ("left" if a.side == "right" else "right")
        scale = 1.0 if i < 2 else 1.12
        p = out if a.variants == 1 else out.with_name(f"{out.stem}_{i + 1}{out.suffix}")
        build(a.photo, a.text, a.theme, side, a.chip, p, scale)
        print("wrote", p)


if __name__ == "__main__":
    main()
