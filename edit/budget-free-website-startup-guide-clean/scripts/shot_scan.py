import subprocess, numpy as np, json, sys
src=sys.argv[1]; W,H=64,36; fps=5
raw=subprocess.run(["ffmpeg","-v","error","-i",src,"-vf",f"fps={fps},scale={W}:{H}","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
fr=np.frombuffer(raw,np.uint8).reshape(-1,H,W,3).astype(float)
# camera: pink/magenta wall dominant -> R high, G low; screen: bright/white grey
r,g,b=fr[...,0].mean((1,2)),fr[...,1].mean((1,2)),fr[...,2].mean((1,2))
light=(fr.mean(3)>200).mean((1,2))
cls=np.where((light>0.35),"screen","camera")
# smooth: segments
segs=[];cur=cls[0];st=0
for i,c in enumerate(cls):
    if c!=cur:
        segs.append([cur,st/fps,i/fps]);cur=c;st=i
segs.append([cur,st/fps,len(cls)/fps])
# merge segments shorter than 1s
out=[]
for s in segs:
    if out and (s[2]-s[1]<1.0):
        out[-1][2]=s[2]
    elif out and out[-1][0]==s[0]:
        out[-1][2]=s[2]
    else: out.append(s)
json.dump(out,open("reports/shots.json","w"),indent=0)
for s in out: print(f"{s[0]:7s} {s[1]:7.1f} {s[2]:7.1f} ({s[2]-s[1]:.1f})")
