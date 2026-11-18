import json,sys,re
W=[w for w in json.load(open("transcripts/budget-free-website-startup-guide-clean.json"))["words"] if w["type"]=="word"]
norm=lambda s:re.sub(r"[^a-z0-9$]","",s.lower())
toks=[norm(w["text"]) for w in W]
for q in sys.argv[1:]:
    qs=[norm(x) for x in q.split()]
    hits=[i for i in range(len(W)-len(qs)+1) if all(toks[i+k]==qs[k] for k in range(len(qs)))]
    print(q, "->", ", ".join(f"{W[i]['start']:.2f}-{W[i+len(qs)-1]['end']:.2f}" for i in hits) or "NONE")
