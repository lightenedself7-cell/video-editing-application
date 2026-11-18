import json
d = json.load(open('/home/dev/video-editing-application/edit/hiringcafe-hidden-job-board/transcripts/hiringcafe-hidden-job-board.json'))
with open('/home/dev/video-editing-application/edit/hiringcafe-hidden-job-board/transcripts/segments.txt', 'w') as f:
    for s in d['segments']:
        f.write(f"{s['start']:6.1f}-{s['end']:6.1f} {s['text']}\n")
