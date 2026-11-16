"""Teal Spotlight: registry agreement, validator, and that each component draws only where it should."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import numpy as np  # noqa: E402
import cv2  # noqa: E402

from renderer import engine  # noqa: E402
from test_renderer import VALIDATOR, beat  # noqa: E402

DUR = 20.0


def make_directive(src: Path, sha: str) -> dict:
    return {
        "version": 1, "project": "ts-test", "theme": "teal-spotlight",
        "source": {"path": str(src), "sha256": sha, "width": 1280, "height": 720, "fps": "30/1", "duration_s": DUR},
        "approval": {"status": "approved", "approved_scope": "test", "ambiguities": []},
        "protected_regions": [{"name": "presenter", "x": 260, "y": 0, "width": 700, "height": 600}],
        "beats": [
            beat(1, 0.5, 4.5, "FULLSCREEN_MOTION", "hook", ["T"], component="section-title",
                 props={"kicker": "Part 2", "title": "Build your\nwebsite", "key": "in one hour", "cue": 0.9}),
            beat(2, 5.0, 10.0, "FULLSCREEN_MOTION", "proof", ["T"], component="spotlight-box",
                 props={"boxes": [{"x": 100, "y": 80, "width": 420, "height": 260, "cue": 5.6, "marker": {"x": 120, "y": 150, "width": 380, "height": 40}},
                                  {"x": 760, "y": 360, "width": 400, "height": 240, "cue": 7.6}]}),
            beat(3, 10.5, 14.0, "OVERLAY_CARD", "proof", ["T"], layout={"x": 976, "y": 200, "width": 280, "height": 20}, component="explainer-card",
                 props={"title": "How it works", "rows": [{"text": "Describe the **site**", "cue": 11.0}, {"text": "AI builds it", "cue": 12.0}, {"text": "You publish", "cue": 13.0}]}),
            beat(4, 14.5, 18.0, "OVERLAY_CARD", "cta", ["T"], layout={"x": 40, "y": 616, "width": 400, "height": 90}, component="lower-third-tag",
                 props={"text": "Link down below", "sub": "free template", "cue": 15.0}),
        ],
    }


class TealSpotlightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.src = cls.dir / "source.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size=1280x720:rate=30:duration={DUR}",
                        "-f", "lavfi", "-i", f"sine=frequency=440:duration={DUR}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(cls.src)], check=True)
        cls.directive = make_directive(cls.src, hashlib.sha256(cls.src.read_bytes()).hexdigest())

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def validate(self, directive):
        p = self.dir / "d.json"
        p.write_text(json.dumps(directive))
        r = subprocess.run([sys.executable, str(VALIDATOR), str(p)], capture_output=True, text=True)
        return r.returncode, r.stderr

    def test_validator_accepts_and_rejects(self):
        code, err = self.validate(self.directive)
        self.assertEqual(code, 0, err)
        d = copy.deepcopy(self.directive)
        d["beats"][1]["props"]["boxes"][0]["width"] = "wide"
        d["beats"][3]["component"] = "section-title"
        code, err = self.validate(d)
        self.assertEqual(code, 1)
        self.assertIn("must be a number", err)
        self.assertIn("is for FULLSCREEN_MOTION", err)

    def test_registry_and_components_agree(self):
        ctx = engine.Context(self.directive, str(self.dir))
        self.assertEqual(set(ctx.registry["components"]), set(ctx.components))

    def test_frames(self):
        ctx = engine.Context(self.directive, str(self.dir))
        frames = {"title": 60, "spot": 204, "spot2": 270, "card": 405, "tag": 480, "clean": 580}
        paths = engine.render_pngs(ctx, list(frames.values()), str(self.dir / "frames"))
        shots = {k: cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB).astype(np.float32) for k, p in zip(frames, paths)}
        ref = {}
        for k, n in frames.items():
            dec = engine._decode(ctx, n, n + 1)
            buf = dec.stdout.read(1280 * 720 * 3)
            dec.stdout.close(); dec.wait()
            ref[k] = np.frombuffer(buf, np.uint8).reshape(720, 1280, 3).astype(np.float32)
        self.assertLess(np.abs(shots["clean"] - ref["clean"]).max(), 2.0)  # no beat: untouched
        self.assertGreater(np.abs(shots["title"] - ref["title"]).mean(), 40)  # title card replaces the frame
        self.assertGreater(np.abs(shots["spot"] - ref["spot"]).mean(), 10)
        self.assertNotEqual(float(shots["spot"].sum()), float(shots["spot2"].sum()))  # the spotlight moved to the second box
        for key in ("card", "tag"):
            diff = np.abs(shots[key] - ref[key])
            self.assertGreater(diff.max(), 50, key)
            self.assertLess(diff[0:600, 260:960].max(), 4.0, f"{key} reaches into the protected region")

    def test_screen_share_card_hides_and_returns(self):
        d = copy.deepcopy(self.directive)
        d["beats"] = [beat(1, 0.5, 12.0, "FULLSCREEN_MOTION", "process", ["T"], component="screen-share",
                           props={"screen": {"x": 0, "y": 0, "width": 1280, "height": 720},
                                  "presenter": {"x": 880, "y": 400, "width": 360, "height": 280},
                                  "presenter_visibility": [{"cue": 6.0, "visible": False}, {"cue": 9.0, "visible": True}]})]
        self.assertEqual(self.validate(d)[0], 0)
        ctx = engine.Context(d, str(self.dir))
        paths = engine.render_pngs(ctx, [150, 240, 330], str(self.dir / "ss"))
        shown, hidden, back = [cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB).astype(np.float32) for p in paths]
        card = (slice(270, 450), slice(28, 260))  # where the presenter card sits
        strip = (slice(120, 220), slice(60, 200))  # above the card: bare ground while the card is out, screen once the window grows into the space
        ground = ctx.ground()
        self.assertGreater(np.abs(shown[card] - ground[card]).mean(), 40)    # card visible
        self.assertLess(np.abs(shown[strip] - ground[strip]).mean(), 12)     # window starts to the right of the card
        self.assertGreater(np.abs(hidden[strip] - ground[strip]).mean(), 40)  # card hidden: window fills the space
        self.assertGreater(np.abs(back[card] - ground[card]).mean(), 40)     # card returned
        self.assertLess(np.abs(back[strip] - ground[strip]).mean(), 12)
        bad = copy.deepcopy(d)
        bad["beats"][0]["props"]["presenter_visibility"] = [{"cue": 6.0}]
        self.assertEqual(self.validate(bad)[0], 1)


if __name__ == "__main__":
    unittest.main()
