"""Local word-level transcription with faster-whisper (no upload). Writes Scribe-shaped JSON."""
import json, subprocess, sys, tempfile, os
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
if os.path.exists(out):
    print("cached", out); sys.exit(0)
with tempfile.TemporaryDirectory() as td:
    wav = os.path.join(td, "a.wav")
    subprocess.run(["ffmpeg","-v","error","-i",src,"-vn","-ac","1","-ar","16000","-f","s16le",wav],check=True)
    import numpy as np
    audio = np.frombuffer(open(wav,"rb").read(), dtype=np.int16).astype(np.float32)/32768.0
    m = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=12)
    segs, info = m.transcribe(audio, language="en", word_timestamps=True, vad_filter=False, beam_size=5, condition_on_previous_text=False)
    words=[]; prev=None
    for s in segs:
        for w in s.words:
            if prev is not None and w.start>prev:
                words.append({"type":"spacing","text":" ","start":prev,"end":w.start,"speaker_id":"S0"})
            words.append({"type":"word","text":w.word.strip(),"start":round(w.start,3),"end":round(w.end,3),"speaker_id":"S0","probability":round(w.probability,3)})
            prev=w.end
        print(f"{s.end:.1f}s", flush=True)
json.dump({"engine":"faster-whisper small int8 (local)","language":"en","words":words}, open(out,"w"), indent=1)
print("done", len(words))
