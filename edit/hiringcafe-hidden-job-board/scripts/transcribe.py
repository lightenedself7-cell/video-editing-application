import json, sys
from faster_whisper import WhisperModel

import wave
import numpy as np

src, out = sys.argv[1], sys.argv[2]
with wave.open(src) as w:  # 16 kHz mono s16; bypasses PyAV (version mismatch with faster-whisper)
    audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=12)
segs, info = model.transcribe(audio, language="en", word_timestamps=True, vad_filter=False,
                              initial_prompt="HiringCafe, LinkedIn, Indeed, job board, hiring.cafe")
words, lines = [], []
for s in segs:
    print(f"{s.end:.1f}s", flush=True)
    lines.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
    for w in s.words:
        words.append({"type": "word", "text": w.word.strip(), "start": round(w.start, 2),
                      "end": round(w.end, 2), "speaker_id": "S0", "probability": round(w.probability, 3)})
json.dump({"engine": "faster-whisper small int8 (local)", "language": "en", "words": words,
           "segments": lines}, open(out, "w"), indent=1)
print("done", len(words))
