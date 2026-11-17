import json
d=json.load(open('/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo/editorial-directive.json'))
b=sorted(d['beats'],key=lambda x:x['start']); dur=d['source']['duration_s']
cut=384.8
# camera shots on the CUT timeline (orig times; after cut shift -6.9)
cam=[(0,98.7),(107.43,130.7),(144.93,163.9),(253.0,281.37),(411.6,454.77)]
s=lambda x: x if x<=cut else x-6.9
cam=[(s(a),s(c)) for a,c in cam]
gaps=[];t=0
for x in b:
    gaps.append((t,x['start'])); t=x['end']
gaps.append((t,dur))
out=[]
for a,c in gaps:
    for ca,cc in cam:
        lo,hi=max(a,ca),min(c,cc)
        if hi-lo>1: out.append((hi-lo,lo,hi))
for L,lo,hi in sorted(out,reverse=True): print(f"{L:5.1f}s  {int(lo//60)}:{lo%60:04.1f} - {int(hi//60)}:{hi%60:04.1f}")
