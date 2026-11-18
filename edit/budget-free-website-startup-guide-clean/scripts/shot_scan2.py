import subprocess, numpy as np, json, sys
src=sys.argv[1]; W,H=64,36; fps=5
raw=subprocess.run(["ffmpeg","-v","error","-i",src,"-vf",f"fps={fps},scale={W}:{H}","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
fr=np.frombuffer(raw,np.uint8).reshape(-1,H,W,3).astype(int)
r,g,b=fr[...,0],fr[...,1],fr[...,2]
# camera: pink wall over most of frame; check upper band (rows 0-12) magenta fraction
mag=((r-g>50)&(b-g>20))[:,0:14,:].mean((1,2))
cls=np.where(mag>0.5,"camera","screen")
segs=[];cur=cls[0];st=0
for i,c in enumerate(cls):
    if c!=cur: segs.append([cur,st/fps,i/fps]);cur=c;st=i
segs.append([cur,st/fps,len(cls)/fps])
out=[]
for s in segs:
    if out and s[2]-s[1]<1.0: out[-1][2]=s[2]
    elif out and out[-1][0]==s[0]: out[-1][2]=s[2]
    else: out.append(s)
json.dump(out,open("reports/shots.json","w"))
for s in out: print(f"{s[0]:7s} {s[1]:7.1f} {s[2]:7.1f} ({s[2]-s[1]:.1f})")
