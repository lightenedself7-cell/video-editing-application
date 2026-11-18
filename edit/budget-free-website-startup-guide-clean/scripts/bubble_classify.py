import subprocess, numpy as np, json
src="/home/dev/videos/budget-free-website-startup-guide-clean.mp4"
SCREENS=[(78.2,94.6),(123.8,290.0),(370.0,697.4)]
C={"A":(92.6,625.4,90.9),"B":(131.5,584.3,127.6),"C":(106.6,611.6,98.0),"D":(211.1,508.0,149.6),
   "E":(1135.0,459.0,107.8),"F":(1129.0,555.0,130.7),"G":(158.1,557.0,133.6),"H":(125.0,593.0,116.6),
   "I":(115.9,602.0,107.6),"J":(108.5,609.5,100.0)}
ang=np.linspace(0,2*np.pi,240,endpoint=False)
def pts(cx,cy,r):
    x=np.clip(np.round(cx+r*np.cos(ang)).astype(int),0,1279); y=np.round(cy+r*np.sin(ang)).astype(int)
    ok=(y>=0)&(y<720)&(cx+r*np.cos(ang)>=0)&(cx+r*np.cos(ang)<1280)
    return x,np.clip(y,0,719),ok
P={k:(pts(cx,cy,r-3.5),pts(cx,cy,r+3.5)) for k,(cx,cy,r) in C.items()}
res=[]
for a,b in SCREENS:
    p=subprocess.Popen(["ffmpeg","-v","error","-ss",str(a),"-t",str(b-a),"-i",src,"-f","rawvideo","-pix_fmt","rgb24","-"],stdout=subprocess.PIPE)
    i=0
    while True:
        buf=p.stdout.read(1280*720*3)
        if len(buf)<1280*720*3: break
        f=np.frombuffer(buf,np.uint8).reshape(720,1280,3).astype(int)
        sc={}
        for k,((xi,yi,oi),(xo,yo,oo)) in P.items():
            ok=oi&oo
            d=np.abs(f[yi,xi]-f[yo,xo]).sum(1)
            sc[k]=float((d[ok]>45).mean())
        k=max(sc,key=sc.get)
        res.append([round(a+i/30,4),k if sc[k]>0.55 else None,round(sc[k],2)])
        i+=1
json.dump(res,open("reports/bubble_frames.json","w"))
# runs
runs=[]
for t,k,s in res:
    if runs and runs[-1]["k"]==k and abs(t-runs[-1]["end"])<0.05: runs[-1]["end"]=round(t+1/30,4); runs[-1]["n"]+=1
    else: runs.append({"start":t,"end":round(t+1/30,4),"k":k,"n":1})
for r in runs:
    if r["n"]>=6: print(r)
print("runs",len(runs),"short",sum(1 for r in runs if r["n"]<6))
