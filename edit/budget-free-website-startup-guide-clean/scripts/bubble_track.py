import subprocess, numpy as np, json, cv2
src="/home/dev/videos/budget-free-website-startup-guide-clean.mp4"
SCREENS=[(78.2,94.6),(123.8,290.0),(370.0,697.4)]
W,H=640,360; fps=5
raw=subprocess.run(["ffmpeg","-v","error","-i",src,"-vf",f"fps={fps},scale={W}:{H}","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
fr=np.frombuffer(raw,np.uint8).reshape(-1,H,W,3)
out=[]
for i,f in enumerate(fr):
    t=i/fps
    if not any(a<=t<b for a,b in SCREENS): continue
    r,g,b=[f[...,k].astype(int) for k in range(3)]
    m=((r-g>45)&(b-g>15)).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    n,lab,st,_=cv2.connectedComponentsWithStats(m)
    if n<2: out.append([t,None]); continue
    k=1+np.argmax(st[1:,cv2.CC_STAT_AREA]); x,y,w,h,a=st[k]
    if a<800: out.append([t,None]); continue
    d=w; cx=x+w/2; cy=y+d/2
    out.append([t,[round(cx*2),round(cy*2),round(d)]])  # 1280 coords; d in 1280 = w*2 -> radius = w
json.dump(out,open("reports/bubble_raw.json","w"))
# runs
runs=[];cur=None
for t,g in out:
    key=None if g is None else tuple(int(round(v/12.0))*12 for v in g)
    if cur and ((key is None and cur["g"] is None) or (key and cur["g"] and max(abs(a-b) for a,b in zip(key,cur["g"]))<=24)):
        cur["end"]=t+1/fps; cur["n"]+=1
        if g: cur["samples"].append(g)
    else:
        cur={"start":t,"end":t+1/fps,"g":key,"n":1,"samples":[g] if g else []}; runs.append(cur)
for r in runs:
    med=np.median(np.array(r["samples"]),0).round().tolist() if r["samples"] else None
    r["median"]=med; del r["samples"]
    print(f'{r["start"]:7.1f}-{r["end"]:7.1f} n={r["n"]:4d} {med}')
json.dump(runs,open("reports/bubble_runs.json","w"),indent=0)
