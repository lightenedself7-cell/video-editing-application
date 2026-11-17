#!/usr/bin/env bash
rm -rf /tmp/tb; mkdir /tmp/tb; cd /tmp/tb
ffmpeg -hide_banner -nostdin -loglevel error -ss 312 -t 68 -i /home/dev/videos/automated-job-search-spreadsheet-demo.mp4 -vf "fps=4,crop=520:40:0:680" t_%04d.png
/home/dev/video-editing-application/.venv/bin/python - <<'PY'
import glob, numpy as np
from PIL import Image
tabs={"Config":118,"Jobs":198,"Rej":265,"Log":358}
prev=None
for i,f in enumerate(sorted(glob.glob("/tmp/tb/t_*.png"))):
    a=np.asarray(Image.open(f).convert("RGB")).astype(int)
    # find tab bar row: row where x=198..258 looks like a tab; try rows 10..30
    best=None
    for y in range(8,38):
        res=[k for k,x in tabs.items() if a[y,x,2]-a[y,x,0]>=12 and a[y,x].sum()>600]
        if res: best=(y,res[0]); break
    cur=best[1] if best else "-"
    if cur!=prev: print(round(312+i/4,2), cur, best[0]+680 if best else ""); prev=cur
PY