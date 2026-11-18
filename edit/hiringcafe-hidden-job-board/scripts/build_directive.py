"""Builds editorial-directive.json from beats.py (the table compose.py renders from)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from beats import *

SHA = open(os.path.join(ROOT, "reports/source.sha256")).read().split()[0]
TR = lambda x, y, w, h: {"x": x, "y": y, "width": w, "height": h}
TOPRIGHT = TR(870, 48, 330, 150)       # chips inside the framed screen window
LAYOUT = {
    "b01": TR(960, 290, 210, 100), "b02": TR(900, 200, 330, 230), "b03": TR(884, 176, 372, 296), "b04": TR(900, 200, 330, 280),
    "b06": TR(900, 210, 330, 230), "b08": TOPRIGHT, "b09": TOPRIGHT, "b10": TR(20, 170, 300, 340), "b11": TR(340, 610, 600, 100),
    "b12": TR(28, 300, 264, 124), "b13": TR(28, 240, 264, 140), "b14": TOPRIGHT, "b15": TOPRIGHT, "b16": TR(440, 600, 400, 60),
    "b17": TR(330, 44, 620, 56), "b18": TOPRIGHT, "b21": TOPRIGHT, "b22": TR(900, 48, 300, 150), "b23": TOPRIGHT, "b24": TR(28, 270, 232, 100),
    "b25": TOPRIGHT, "b28": TR(28, 250, 320, 170), "b29": TR(28, 210, 320, 290), "b31": TR(18, 100, 340, 500), "b32": TR(28, 290, 200, 60),
    "b33": TR(28, 260, 260, 130), "b34": TR(28, 290, 160, 60),
    "b07": TR(840, 100, 400, 520), "b27": TR(840, 100, 410, 520),
}
FULL = {"b05": ("slide-from-right", "slide-to-right"), "b19": ("slide-from-bottom", "slide-to-bottom"),
        "b20": ("slide-from-right", "slide-to-right"), "b26": ("slide-from-top", "slide-to-top"), "b30": ("dim-blur-fade", "dim-blur-fade")}
PURPOSE = {
    "b01": "Cross out both big boards on the hook line", "b02": "Land the 10x claim beside the presenter", "b03": "Name the site, its address and the two promises",
    "b04": "Make applicant 400 feel hopeless", "b05": "Show why the job reaches HiringCafe first (flow diagram)", "b06": "Land 'You are early'",
    "b07": "Show 20 % promoted vs 80 % everything else", "b08": "Zoom the address bar and show a crisp URL pill", "b09": "Walk the demo with zooms: filters, 24 h, Atacama, LinkedIn",
    "b10": "Check-list of the gap: company site, HiringCafe, not LinkedIn", "b11": "Named-rule line: time is your leverage", "b12": "Tease the Claude and Google Sheets tracker",
    "b13": "Like / comment / subscribe animation", "b14": "Highlight the founder story and numbers in the article", "b15": "Name the two search modes",
    "b16": "Zoom the Date posted filter and name the rule", "b17": "Follow the controls: save, applied, interviewing, notes", "b18": "Explain Network vs Add jobs",
    "b19": "One title splits into ten names", "b20": "Type the prompt exactly as spoken", "b21": "Highlight the AI talent agent launch line",
    "b22": "Counters for 33 / 7 / 15 and the email alert", "b23": "Free plan facts", "b24": "Short subscribe reminder", "b25": "Connector, funnel, schedule and Sheets icons",
    "b26": "Explain why midnight with a 24 h timeline", "b27": "Recap rail beside the presenter", "b28": "Count up to 5,000,000+ jobs", "b29": "LinkedIn for networking and posting, HiringCafe for finding",
    "b30": "Centre quote of the closing line", "b31": "Four-step action list with URL pill", "b32": "Invite comments", "b33": "Subscribe and like", "b34": "Share button click",
}
REVEALS = {
    "b01": [("LinkedIn", 2.48), ("Indeed", 3.08)], "b02": [("10x", 5.74), ("BETTER", 6.62)], "b03": [("HiringCafe", 15.34), ("hiringcafe.com", 17.9), ("Free", 19.54), ("No account needed", 20.88)],
    "b04": [("APPLICANT #", 23.76), ("400", 29.5), ("nobody is reading", 30.6)], "b05": [("Company careers page", 39.4), ("LinkedIn", 42.12), ("Indeed", 42.9), ("Recruiter", 49.4), ("DELAY", 53.86), ("HiringCafe", 56.3), ("3x a day", 62.78)],
    "b06": [("YOU ARE", 75.72), ("EARLY", 76.1)], "b07": [("20%", 81.54), ("80%", 85.36)], "b08": [("hiringcafe.com", 91.3)],
    "b09": [("Posted 13 h ago", 144.0), ("Not on LinkedIn yet", 164.0)], "b10": [("Company site", 178.68), ("HiringCafe", 180.14), ("LinkedIn", 181.72)],
    "b11": [("Time is your leverage", 186.16), ("Early applicants get the call", 186.52)], "b12": [("Claude", 192.3), ("Google Sheets", 195.4)],
    "b13": [("Like", 199.0), ("Comment", 199.25), ("Subscribe", 199.5)], "b14": [("Ex-Meta engineer", 209.9), ("10,000 jobs", 212.04), ("Reddit", 217.05), ("2 million", 219.72)],
    "b15": [("Classic search", 233.64), ("AI search", 235.14)], "b16": [("Date posted: 24 h", 260.06), ("One filter = the whole strategy", 267.9)],
    "b17": [("Save", 283.2), ("Applied", 293.84), ("Interviewing", 295.2), ("Notes", 318.66)], "b18": [("Network", 339.34), ("Add jobs", 350.04)],
    "b19": [("1 title", 357.2), ("10 names", 363.1)], "b20": [("Claude", 374.6), ("ChatGPT", 375.18), ("prompt", 380.38)], "b21": [("September 28", 409.38), ("AI talent agent", 413.76)],
    "b22": [("33 jobs", 447.26), ("7 matching", 449.3), ("15 related", 450.64), ("Email alerts", 468.64)], "b23": [("Free plan", 476.94), ("Everything free", 502.86)],
    "b24": [("Subscribe", 510.6)], "b25": [("Claude", 521.72), ("ChatGPT", 525.64), ("Google Sheets", 547.54)], "b26": [("24 h", 557.6), ("Used while you sleep", 559.22)],
    "b27": [("Careers page", 583.0), ("HiringCafe", 587.2), ("Ghost jobs", 591.18)], "b28": [("5,000,000+", 606.02)], "b29": [("Networking", 612.74), ("Finding", 615.44)],
    "b30": [("LinkedIn is for being found.", 619.4), ("HiringCafe is for finding.", 621.55)], "b31": [("Bookmark", 624.4), ("Last 24 hours", 627.8)],
    "b32": [("Comment below", 634.94)], "b33": [("Subscribe", 640.5), ("Like", 643.16)], "b34": [("Share", 648.62)],
}
ROLE_HOLD = {"hook": "continuous"}

def build():
    beats = []
    for b in BEATS:
        bid = b["id"]; tr = b["treatment"]
        d = dict(b)
        d["purpose"] = PURPOSE[bid]
        d["layout"] = LAYOUT.get(bid, TR(0, 0, 1280, 720))
        d["reveal_sync"] = [{"element": e, "time": t} for e, t in REVEALS.get(bid, []) if b["start"] <= t <= b["end"]]
        if tr == "FULLSCREEN_MOTION":
            d["transition_in"], d["transition_out"] = FULL[bid]; d["layout"] = TR(0, 0, 1280, 720)
        elif tr == "PRESENTER_INSET":
            d["presenter_layout"] = TR(48, 120, 768, 432); d["transition_in"] = "scale-move-to-window"; d["transition_out"] = "scale-move-to-full-frame"
        else:
            d["transition_in"] = "fade-slide-12f"; d["transition_out"] = "fade-10f"
        d["audio_continuity"] = "continuous"
        d["rationale"] = {"SELECTIVE_TEXT": "One short phrase whose timing is the effect; presenter untouched.",
                          "OVERLAY_CARD": "Small supporting element in a side margin (camera) or inside the framed screen; presenter face clear.",
                          "FULLSCREEN_MOTION": "Process or comparison that needs the whole canvas; narration continues underneath.",
                          "PRESENTER_INSET": "Presenter moves into a rounded window while graphics use the remaining space."}[tr]
        d["review_status"] = "approved"
        beats.append(d)
    return {
        "version": 1, "project": "hiringcafe-hidden-job-board", "theme": "clean-creator",
        "source": {"path": SRC, "sha256": SHA, "width": 1280, "height": 720, "fps": "30/1", "duration_s": 664.0},
        "approval": {"status": "approved", "approved_scope": "Full plan in director-treatment.md (all 35 beats) approved by the creator on 2026-11-14/15, including real brand logos "
                     "(LinkedIn, Indeed, HiringCafe, Claude, Google Sheets) and YouTube-style subscribe / like / share buttons in theme colours. "
                     "Execution notes: b30 is classified FULLSCREEN_MOTION (footage blurs in place); ChatGPT icon added because the narration names it.",
                     "ambiguities": []},
        "protected_regions": [{"name": "presenter-face-core", "x": 580, "y": 150, "width": 160, "height": 410}],
        "beats": beats,
    }

if __name__ == "__main__":
    out = os.path.join(ROOT, "editorial-directive.json")
    json.dump(build(), open(out, "w"), indent=1, ensure_ascii=False)
    print("wrote", out)
