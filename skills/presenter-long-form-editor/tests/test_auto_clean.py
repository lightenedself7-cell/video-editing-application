import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import auto_clean as ac  # noqa: E402


def mk(text, start=0.0, step=0.3, gaps=None):
    """Build a word list; gaps = {index: extra silence before that word}."""
    gaps, t, out = gaps or {}, start, []
    for i, w in enumerate(text.split()):
        t += gaps.get(i, 0.0)
        out.append({"w": w, "start": round(t, 3), "end": round(t + 0.25, 3)})
        t += step
    return out


class DetectTests(unittest.TestCase):
    def test_filler_removed(self):
        w = mk("So um we start here now.")
        cuts = ac.detect(w, 3.0)
        self.assertTrue(any("filler" in c["types"] and "um" in c["removed_text"] for c in cuts))

    def test_long_pause_shortened_keeps_gap(self):
        w = mk("first part here second part there", gaps={3: 2.0})
        cuts = ac.detect(w, 6.0)
        c = [x for x in cuts if x["types"] == ["pause"]][0]
        self.assertGreater(c["len"], 1.3)
        self.assertLess(c["len"], 2.0)

    def test_stutter_and_false_start(self):
        w = mk("that is why the prompt only looks that is why the prompt only looks at new jobs", gaps={7: 0.6})
        cuts = ac.detect(w, 8.0)
        self.assertTrue(any(c["types"] and ("false-start" in c["types"] or "repeat" in c["types"]) for c in cuts))
        self.assertTrue(cuts[0]["start"] < 0.1)  # the first attempt (starts at word 0) is the one removed

    def test_cut_cut_marker(self):
        w = mk("this take is bad cut cut", gaps={}) + mk("this take is good", start=6.0)
        cuts = ac.detect(w, 8.0)
        self.assertIn("cut-cut", cuts[0]["types"])
        self.assertAlmostEqual(cuts[0]["start"], 0.0, places=1)

    def test_plain_repeat_word_kept(self):
        w = mk("that was very very good indeed my friend")
        self.assertEqual([c for c in ac.detect(w, 4.0) if "repeat" in c["types"]], [])

    def test_script_retake_keeps_last(self):
        script = "The spreadsheet fills itself every single night."
        w = mk("The spreadsheet fills itself every single night.") + mk("chatter here", start=3.0) + mk("The spreadsheet fills itself every single night.", start=4.5)
        cuts = ac.detect(w, 8.0, script=script)
        self.assertTrue(any("retake" in c["types"] for c in cuts))
        self.assertTrue(cuts[0]["start"] < 0.1)


class ShiftTests(unittest.TestCase):
    def test_time_map(self):
        T = ac.make_T([[10, 12], [20, 21]])
        self.assertEqual(T(5), 5)
        self.assertEqual(T(11), 10)
        self.assertEqual(T(15), 13)
        self.assertEqual(T(25), 22)

    def test_transcript_shift_drops_cut_words(self):
        raw = {"duration": 30, "words": mk("a b c d e f g h", step=1.0), "phrases": [{"start": 0, "end": 8, "text": "a b c d e f g h"}]}
        out = ac.shift_transcript(raw, [[2.0, 4.0]])
        self.assertEqual([w["w"] for w in out["words"]], ["a", "b", "e", "f", "g", "h"])
        self.assertEqual(out["duration"], 28)


if __name__ == "__main__":
    unittest.main()
