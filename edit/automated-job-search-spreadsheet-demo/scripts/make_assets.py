"""Builds the extra brand tiles for round 2 (run with the project venv)."""
import glob, os, shutil
from PIL import Image, ImageDraw, ImageFont

E = "/home/dev/video-editing-application/edit"
B = f"{E}/automated-job-search-spreadsheet-demo/brand"
for f in sorted(glob.glob(f"{B}/*.png") + glob.glob(f"{B}/user/*.png")):
    print(f, Image.open(f).size)
fonts = glob.glob(f"{E}/hiringcafe-hidden-job-board/brand/fonts/*")
print(fonts)

shutil.copy(f"{E}/hiringcafe-hidden-job-board/brand/chatgpt.png", f"{B}/chatgpt.png")


def font(size):
    f = ImageFont.truetype(f"{E}/hiringcafe-hidden-job-board/brand/fonts/Montserrat.ttf", size)
    try:
        f.set_variation_by_name("Bold")
    except Exception:
        pass
    return f


# Google Sheets icon, drawn at 4x and reduced
S = 1024
im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
GREEN, DARK = (15, 157, 88, 255), (11, 128, 67, 255)
x0, y0, x1, y1 = 200, 90, 824, 934
fold = 190
d.polygon([(x0 + 30, y0), (x1 - fold, y0), (x1, y0 + fold), (x1, y1 - 30), (x1 - 30, y1), (x0 + 30, y1), (x0, y1 - 30), (x0, y0 + 30)], fill=GREEN)
d.rounded_rectangle([x0, y0, x0 + 90, y0 + 90], 30, fill=GREEN)
d.polygon([(x1 - fold, y0), (x1, y0 + fold), (x1 - fold, y0 + fold)], fill=DARK)
gx0, gy0, gx1, gy1 = 290, 430, 734, 760
d.rounded_rectangle([gx0, gy0, gx1, gy1], 14, fill=(255, 255, 255, 255))
cw = (gx1 - gx0) / 3
rh = (gy1 - gy0) / 3
for i in (1, 2):
    d.rectangle([gx0 + cw * i - 7, gy0, gx0 + cw * i + 7, gy1], fill=GREEN)
    d.rectangle([gx0, gy0 + rh * i - 7, gx1, gy0 + rh * i + 7], fill=GREEN)
im.resize((512, 512), Image.LANCZOS).save(f"{B}/sheets_icon.png")

# hiringcafe.com tile: logo on top, domain below, on a white card
logo = Image.open(f"{B}/hiringcafe.png").convert("RGBA")
W, H = 760, 380
t = Image.new("RGBA", (W, H), (255, 255, 255, 255))
logo.thumbnail((200, 200), Image.LANCZOS)
t.paste(logo, ((W - logo.width) // 2, 28), logo)
dd = ImageDraw.Draw(t)
f = font(76)
txt = "hiringcafe.com"
w = dd.textlength(txt, font=f)
dd.text(((W - w) / 2, 262), txt, font=f, fill=(33, 10, 18, 255))
t.save(f"{B}/hiringcafe_com.png")
print("assets done")
