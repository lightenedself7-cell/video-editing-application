"""Flat light themes (personal, navy-amber, lime-tech) share renderer/flat.py; tokens set the look."""
import copy
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

from renderer import engine  # noqa: E402
from test_renderer import VALIDATOR, beat  # noqa: E402

THEMES = ("personal", "navy-amber", "lime-tech")
DUR = 20.0


def make_directive(theme, src):
    return {
        "version": 1, "project": "flat-test", "theme": theme,
        "source": {"path": str(src), "sha256": "0" * 64, "width": 1280, "height": 720, "fps": "30/1", "duration_s": DUR},
        "approval": {"status": "approved", "approved_scope": "test", "ambiguities": []},
        "protected_regions": [{"name": "presenter", "x": 260, "y": 0, "width": 700, "height": 600}],
        "beats": [
            beat(1, 0.5, 4.5, "FULLSCREEN_MOTION", "hook", ["T"], component="title-scene",
                 props={"title": "Build your\nwebsite", "subtitle": "A guide", "key": "in one hour", "cue": 0.9}),
            beat(2, 5.0, 9.0, "FULLSCREEN_MOTION", "process", ["T"], component="checklist-scene",
                 props={"title": "The plan", "rows": [{"text": "Describe the site", "cue": 5.6}, {"text": "Let AI build it", "cue": 6.6}]}),
            beat(3, 10.0, 13.5, "OVERLAY_CARD", "proof", ["T"], layout={"x": 996, "y": 200, "width": 270, "height": 20}, component="card-overlay",
                 props={"title": "WHAT YOU NEED", "rows": [{"text": "A **laptop**", "cue": 10.5}, {"text": "An idea", "cue": 11.5}]}),
            beat(4, 14.0, 17.0, "SELECTIVE_TEXT", "promise", ["T"], layout={"x": 996, "y": 300, "width": 270, "height": 90}, component="keyword-pill",
                 props={"lead": "all for", "word": "$0", "cue": 14.4}),
            beat(5, 17.4, 19.9, "PRESENTER_INSET", "recap", ["T"], presenter_layout={"x": 32, "y": 32, "width": 368, "height": 656}, component="inset-checklist",
                 props={"title": "RECAP", "source_cx": 640, "rows": [{"text": "Describe", "cue": 18.4}, {"text": "Build", "cue": 18.9}]}),
        ],
    }


class FlatThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.src = cls.dir / "source.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size=1280x720:rate=30:duration={DUR}", "-f", "lavfi", "-i",
                        f"sine=frequency=440:duration={DUR}", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(cls.src)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def validate(self, directive):
        p = self.dir / "d.json"
        p.write_text(json.dumps(directive))
        r = subprocess.run([sys.executable, str(VALIDATOR), str(p)], capture_output=True, text=True)
        return r.returncode, r.stderr

    def test_validator_and_registry(self):
        for theme in THEMES:
            d = make_directive(theme, self.src)
            self.assertEqual(self.validate(d)[0], 0, theme)
            ctx = engine.Context(d, str(self.dir))
            self.assertEqual(set(ctx.registry["components"]), set(ctx.components), theme)
            bad = copy.deepcopy(d)
            bad["beats"][1]["props"]["rows"] = []
            self.assertEqual(self.validate(bad)[0], 1, theme)

    def test_every_frame_renders_and_overlays_stay_off_the_presenter(self):
        S = np.full((720, 1280, 3), 90.0, np.float32)
        for theme in THEMES:
            ctx = engine.Context(make_directive(theme, self.src), str(self.dir))
            for b in ctx.beats:
                for n in range(int(b["start"] * 30) - 1, int(b["end"] * 30) + 2, 3):
                    out, ref = engine.render_frame(ctx, n, S)
                    self.assertTrue(np.isfinite(out).all(), (theme, n))
                    if ref is not None:
                        self.assertLess(np.abs(out[0:600, 260:960] - S[0:600, 260:960]).max(), 4.0, (theme, b["component"], n))

    def test_ground_is_not_mutated_between_frames(self):
        S = np.full((720, 1280, 3), 90.0, np.float32)
        ctx = engine.Context(make_directive("lime-tech", self.src), str(self.dir))
        before = ctx.ground().copy()
        engine.render_frame(ctx, 60, S)  # title scene draws text and ornaments on its own copy
        self.assertEqual(float(np.abs(ctx.ground() - before).max()), 0.0)


if __name__ == "__main__":
    unittest.main()
