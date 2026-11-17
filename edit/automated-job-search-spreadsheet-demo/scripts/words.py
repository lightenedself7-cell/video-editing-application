import json
w=json.load(open("/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo/prepared/transcripts/section-1.json"))["words"]
for a in range(160,385,15):
    print(f"--- {a}")
    print(" ".join(f"{x['w']}@{x['start']:.1f}" for x in w if a<=x["start"]<a+15))