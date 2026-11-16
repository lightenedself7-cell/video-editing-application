"""Run: .venv/bin/python -m unittest discover -s skills/theme-renderer/tests -v

Builds a synthetic 18 s clip and a component-based directive, then checks the validator, the registry,
single frames, a chunk render and the full parallel CLI.
"""
import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from renderer import engine, registry  # noqa: E402

VALIDATOR = SKILL.parent / "presenter-long-form-editor" / "scripts" / "validate_directive.py"
CLI = SKILL / "render_directive.py"
DUR = 18.0
GLOW_TAIL = 3.0  # max pixel change (of 255) allowed inside the protected region from a card's soft glow


def beat(i, start, end, treatment, role, copy_, **extra):
    b = {"id": f"b{i:02d}", "start": start, "end": end, "spoken_text": "test", "role": role, "treatment": treatment,
         "purpose": "test", "on_screen_copy": copy_, "reveal_sync": [{"element": copy_[0], "time": start + 0.3}],
         "transition_in": "fade", "transition_out": "fade", "audio_continuity": "continuous", "rationale": "test", "review_status": "approved"}
    b.update(extra)
    return b


def make_directive(src: Path, sha: str) -> dict:
    return {
        "version": 1, "project": "tr-test", "theme": "clean-creator",
        "source": {"path": str(src), "sha256": sha, "width": 1280, "height": 720, "fps": "30/1", "duration_s": DUR},
        "approval": {"status": "approved", "approved_scope": "test", "ambiguities": []},
        "protected_regions": [{"name": "presenter", "x": 260, "y": 0, "width": 700, "height": 600}],
        "beats": [
            beat(1, 0.5, 3.0, "OVERLAY_CARD", "proof", ["One", "Two"], layout={"x": 976, "y": 330, "width": 280, "height": 20},
                 component="glass-card", props={"rows": [{"text": "Instant on **mobile**", "cue": 0.8}, {"text": "**$0** hosting", "cue": 1.6}]}),
            beat(2, 3.2, 4.5, "SELECTIVE_TEXT", "promise", ["2 hours"], layout={"x": 976, "y": 250, "width": 280, "height": 90},
                 component="kinetic-keyword", props={"lead": "under", "word": "2 HOURS", "cue": 3.4}),
            beat(3, 4.7, 6.5, "SELECTIVE_TEXT", "question", ["Q"], layout={"x": 160, "y": 616, "width": 960, "height": 56},
                 component="question-beat", props={"text": "What kind of site does AI **build**?", "cue": 4.9}),
            beat(4, 6.8, 11.0, "PRESENTER_INSET", "process", ["a"], presenter_layout={"x": 32, "y": 32, "width": 368, "height": 656},
                 component="side-column-list", props={"title": "PREP", "source_cx": 610, "rows": [{"text": "Real photos", "cue": 8.2}, {"text": "The prep is the **work**", "cue": 9.6}]}),
            beat(5, 12.0, 17.5, "PRESENTER_INSET", "recap", ["a"], presenter_layout={"x": 48, "y": 120, "width": 768, "height": 432},
                 component="recap-window", props={"title": "RECAP", "caption": "A test, start to finish", "rows": [{"text": "**$0** hosting", "cue": 14.0}, {"text": "Done", "cue": 15.5}]}),
        ],
    }


class RendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.src = cls.dir / "source.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size=1280x720:rate=30:duration={DUR}",
                        "-f", "lavfi", "-i", f"sine=frequency=440:duration={DUR}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(cls.src)], check=True)
        cls.sha = hashlib.sha256(cls.src.read_bytes()).hexdigest()
        cls.directive = make_directive(cls.src, cls.sha)
        cls.dpath = cls.dir / "editorial-directive.json"
        cls.dpath.write_text(json.dumps(cls.directive))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def validate(self, directive):
        p = self.dir / "d.json"
        p.write_text(json.dumps(directive))
        r = subprocess.run([sys.executable, str(VALIDATOR), str(p)], capture_output=True, text=True)
        return r.returncode, r.stderr

    # ----- validator + registry -----
    def test_validator_accepts_component_directive(self):
        code, err = self.validate(self.directive)
        self.assertEqual(code, 0, err)

    def test_custom_graphics_warns_and_needs_reason(self):
        d = copy.deepcopy(self.directive)
        b = d["beats"][0]
        b.pop("component"); b.pop("props")
        b["custom_graphics"] = "needs a map"
        code, err = self.validate(d)
        self.assertEqual(code, 0, err)
        self.assertIn("needs a map", err)
        b["custom_graphics"] = " "
        self.assertEqual(self.validate(d)[0], 1)

    def test_validator_rejects_unknown_component(self):
        d = copy.deepcopy(self.directive)
        d["beats"][0]["component"] = "confetti-burst"
        code, err = self.validate(d)
        self.assertEqual(code, 1)
        self.assertIn("confetti-burst", err)
        self.assertIn("glass-card", err)  # lists what is available

    def test_validator_rejects_bad_props(self):
        d = copy.deepcopy(self.directive)
        del d["beats"][0]["props"]["rows"]
        d["beats"][1]["props"]["cue"] = "soon"
        d["beats"][2]["props"]["colour"] = "red"
        d["beats"][3]["props"]["rows"][0]["cue"] = 99.0
        code, err = self.validate(d)
        self.assertEqual(code, 1)
        for needle in ("props.rows is required", "props.cue must be a number", "props.colour is not a known prop", "outside the beat"):
            self.assertIn(needle, err)

    def test_validator_rejects_wrong_treatment(self):
        d = copy.deepcopy(self.directive)
        d["beats"][1]["component"] = "glass-card"
        code, err = self.validate(d)
        self.assertEqual(code, 1)
        self.assertIn("is for OVERLAY_CARD", err)

    def test_validator_rejects_component_on_theme_without_templates(self):
        d = copy.deepcopy(self.directive)
        d["theme"] = "warm-paper"
        code, err = self.validate(d)
        self.assertEqual(code, 1)
        self.assertIn("has no templates yet", err)

    def test_registry_and_components_agree(self):
        ctx = engine.Context(self.directive, str(self.dir))
        self.assertEqual(set(ctx.registry["components"]), set(ctx.components))

    # ----- rendering -----
    def test_frames_draw_only_where_they_should(self):
        ctx = engine.Context(self.directive, str(self.dir))
        frames = [20, 100, 140, 250, 330, 470]  # card, keyword, question, column list, recap, recap rows
        paths = engine.render_pngs(ctx, frames, str(self.dir / "frames"))
        for n, p in zip(frames, paths):
            out = cv2.imread(p)
            self.assertEqual(out.shape, (720, 1280, 3))
        # glass card at 1.6 s: changed at the right, untouched in the protected presenter region
        n = 60
        src = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{n / 30:.4f}", "-i", str(self.src), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                           capture_output=True).stdout, np.uint8).reshape(720, 1280, 3).astype(np.float32)
        out, ref = engine.render_frame(ctx, n, src)
        self.assertIsNotNone(ref)  # card must not touch the presenter
        self.assertGreater(float(np.abs(out[250:450, 976:1256] - src[250:450, 976:1256]).max()), 20)
        # only the card's faint glow tail may reach the region (the old pipeline measured 0.4 on real footage)
        self.assertLess(float(np.abs(out[0:600, 260:960] - src[0:600, 260:960]).max()), GLOW_TAIL)
        # outside every beat the frame is the source, untouched
        out, ref = engine.render_frame(ctx, int(12 * 30 - 5), src)
        self.assertTrue(np.array_equal(out, src))

    def test_chunk_render_frame_count_and_safety(self):
        ctx = engine.Context(self.directive, str(self.dir))
        out = self.dir / "chunk.mp4"
        safe = engine.render_chunk(ctx, 0, 90, str(out), crf=28)
        self.assertEqual(safe["frames_written"], 90)
        self.assertLess(safe["max_overlay_delta_in_protected"], GLOW_TAIL)
        n =subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries", "stream=nb_read_frames",
                            "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip()
        self.assertEqual(int(n), 90)

    def test_full_cli_render_keeps_audio_and_length(self):
        proj = self.dir / "proj"
        proj.mkdir()
        (proj / "editorial-directive.json").write_text(json.dumps(self.directive))
        out = proj / "master.mp4"
        r = subprocess.run([sys.executable, str(CLI), str(proj), "--workers", "3", "--out", str(out)], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        probe = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,nb_frames:format=duration", "-of", "json", str(out)],
                                          capture_output=True, text=True).stdout)
        kinds = {s["codec_type"] for s in probe["streams"]}
        self.assertEqual(kinds, {"video", "audio"})
        self.assertAlmostEqual(float(probe["format"]["duration"]), DUR, delta=0.1)
        self.assertLess(json.loads((proj / "render" / "safe.json").read_text())["max_overlay_delta_in_protected"], GLOW_TAIL)
        self.assertTrue((proj / "ui-progress.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
