import json, sys, os
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
model = WhisperModel(os.environ.get("VIDEO_WHISPER_MODEL", "small"), device="auto", compute_type="auto")
segments, info = model.transcribe(src, word_timestamps=True, vad_filter=True)
words, phrases = [], []
for s in segments:
    phrases.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
    for w in s.words or []:
        words.append({"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
json.dump({"language": info.language, "duration": round(info.duration, 2), "words": words, "phrases": phrases}, open(out, "w"), ensure_ascii=False)
with open(out.replace(".json", ".txt"), "w") as f:
    for p in phrases:
        f.write(f"[{p['start']:.2f}-{p['end']:.2f}] {p['text']}\n")
print("transcript", len(words), "words")
