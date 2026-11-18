import subprocess, numpy as np, json, cv2
src="/home/dev/videos/budget-free-website-startup-guide-clean.mp4"
SCREENS=[(78.2,94.6),(123.8,290.0),(370.0,697.4)]
W,H=1280,720; fps=2
out=[]
for a,b in SCREENS:
    raw=subprocess.run(["ffmpeg","-v","error","-ss",str(a),"-t",str(b-a),"-i",src,"-vf",f"fps={fps}","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
    fr=np.frombuffer(raw,np.uint8).reshape(-1,H,W,3)
    for i,f in enumerate(fr):
        t=round(a+i/fps,2)
        r,g,bb=[f[...,k].astype(int) for k in range(3)]
        m=(((r-g>45)&(bb-g>15))|((r>110)&(r-g>60)&(r-bb>40))).astype(np.uint8)
        m[:260,:]=0; m[:,450:830]=0
        m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((15,15),np.uint8))
        n,lab,st,_=cv2.connectedComponentsWithStats(m)
        best=None
        if n>1:
            k=1+np.argmax(st[1:,cv2.CC_STAT_AREA])
            if st[k,cv2.CC_STAT_AREA]>3000:
                cnts,_=cv2.findContours((lab==k).astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)
                (cx,cy),rad=cv2.minEnclosingCircle(max(cnts,key=len))
                # circularity: fraction of circle area covered by filled component+holes
                filled=np.zeros((H,W),np.uint8); cv2.drawContours(filled,cnts,-1,1,-1)
                circ=np.zeros((H,W),np.uint8); cv2.circle(circ,(int(cx),int(cy)),int(rad),1,-1)
                cov=(filled&circ).sum()/max(circ.sum(),1)
                if cov>0.8 and 40<rad<200: best=[round(cx,1),round(cy,1),round(rad,1),round(cov,2)]
        out.append([t,best])
json.dump(out,open("reports/bubble_raw2.json","w"))
runs=[];cur=None
for t,g in out:
    same = cur is not None and ((g is None and cur["med"] is None) or (g is not None and cur["med"] is not None and max(abs(g[k]-cur["last"][k]) for k in range(3))<=6))
    if same:
        cur["end"]=t+1/fps; cur["s"].append(g); cur["last"]=g or cur["last"]
    else:
        cur={"start":t,"end":t+1/fps,"s":[g],"med":g,"last":g}; runs.append(cur)
res=[]
for r in runs:
    s=[x for x in r["s"] if x]
    med=np.median(np.array(s)[:,:3],0).round(1).tolist() if s else None
    res.append({"start":r["start"],"end":r["end"],"n":len(r["s"]),"circle":med})
    print(f'{r["start"]:7.1f}-{r["end"]:7.1f} n={len(r["s"]):4d} {med}')
json.dump(res,open("reports/bubble_runs2.json","w"),indent=0)
