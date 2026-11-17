import json
w=json.load(open("/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo/prepared/transcripts/section-1.json"))["words"]
for a,b in [(0,31),(31,55.2),(59,75),(85,99),(107,125),(256,282),(414,426)]:
    print(f"--- {a}-{b}")
    print(" ".join(f"{x['w']}@{x['start']:.1f}" for x in w if a<=x["start"]<b))