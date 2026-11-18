"""Single source of truth for the 35 approved beats (director-treatment.md) and spoken-word cues.

compose.py renders from this table; build_directive.py turns it into editorial-directive.json.
Times are source seconds. Boundaries that overlapped in the treatment table are nudged by <=0.5 s
(b10/b11, b26/camera cut) so beats never stack; nothing else is changed.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
NFR = 19920                      # 664.0 s
SRC = "/home/dev/videos/hiringcafe-hidden-job-board.mp4"

_W = [w for w in json.load(open(os.path.join(ROOT, "transcripts/hiringcafe-hidden-job-board.json")))["words"] if w["type"] == "word"]
_norm = lambda s: re.sub(r"[^a-z0-9$%]", "", s.lower())
_T = [_norm(w["text"]) for w in _W]

def cue(phrase, nth=0, after=0.0, end=False):
    """Start (or end) time of the nth match of `phrase` at or after `after` seconds."""
    qs = [_norm(x) for x in phrase.split()]
    hits = [i for i in range(len(_W) - len(qs) + 1)
            if _W[i]["start"] >= after - 1e-6 and all(_T[i + k] == qs[k] for k in range(len(qs)))]
    if len(hits) <= nth:
        raise KeyError(f"cue not found: {phrase!r} (nth={nth}, after={after})")
    i = hits[nth]
    return round(_W[i + len(qs) - 1]["end"] if end else _W[i]["start"], 2)

def words_between(a, b):
    return [(w["text"], w["start"], w["end"]) for w in _W if a <= w["start"] < b]

def gaps(a, b, min_gap=0.22):
    """Pauses (start, end) between spoken words inside [a, b), for jump-cut punch-ins."""
    out = []
    for w0, w1 in zip(_W, _W[1:]):
        if a <= w0["end"] < b and w1["start"] - w0["end"] >= min_gap:
            out.append((w0["end"], w1["start"]))
    return out

def sentence_breaks(a, b, marks=".?!,"):
    """Cut points at sentence/clause ends inside [a, b): midway between the closing word's end and the next word's start."""
    out = []
    for w0, w1 in zip(_W, _W[1:]):
        if a <= w0["end"] < b and w0["text"].rstrip()[-1:] in marks:
            out.append(round((w0["end"] + w1["start"]) / 2, 3))
    return out

# Source structure (frames): camera / screen
CAMERA_FR = [(0, 2664), (5284, 6128), (15259, 15473), (17467, 19920)]
def is_camera(n): return any(a <= n < b for a, b in CAMERA_FR)
def is_screen(n): return not is_camera(n)

# id, start, end, treatment, role, spoken excerpt, on-screen copy
B = lambda *a: dict(zip(("id", "start", "end", "treatment", "role", "spoken_text", "on_screen_copy"), a))
BEATS = [
    B("b01", 0.0, 4.6, "SELECTIVE_TEXT", "hook", "AI just killed LinkedIn and Indeed.", ["LinkedIn", "Indeed"]),
    B("b02", 4.6, 10.5, "SELECTIVE_TEXT", "hook", "There's a free site that is 10x better than both and almost nobody knows about it.", ["10x", "BETTER"]),
    B("b03", 14.8, 22.1, "OVERLAY_CARD", "promise", "It is called HiringCafe, hiringcafe.com. It is free. You don't even need an account.", ["HiringCafe", "hiringcafe.com", "Free", "No account needed"]),
    B("b04", 23.1, 35.5, "SELECTIVE_TEXT", "problem", "You're fighting hundreds of people for the same job. Your applicant number 400. Nobody is reading number 400.", ["APPLICANT #", "400"]),
    B("b05", 36.2, 64.0, "FULLSCREEN_MOTION", "process", "A job doesn't start on LinkedIn. It starts on the company's own careers page... three times a day.", ["Company careers page", "Recruiter", "Delay", "LinkedIn", "Indeed", "HiringCafe", "3x a day"]),
    B("b06", 64.4, 79.0, "SELECTIVE_TEXT", "reveal", "You see the job before it shows up on LinkedIn and you apply before the crowd. You are early.", ["YOU ARE", "EARLY"]),
    B("b07", 79.0, 88.8, "PRESENTER_INSET", "proof", "The big job boards only show you 20% of the jobs companies pay to promote. The other 80% are here.", ["20%", "paid to promote", "80%", "everything else"]),
    B("b08", 88.8, 95.0, "OVERLAY_CARD", "demo", "Go to hiringcafe.com. That's the site and this is how it looks.", ["hiringcafe.com"]),
    B("b09", 95.0, 176.13, "OVERLAY_CARD", "demo", "Filters, account executive, past 24 hours, Atacama seen by five, posted 13 hours ago; LinkedIn shows only three.", ["Posted 13 h ago · 0 applied", "Not on LinkedIn yet"]),
    B("b10", 176.6, 186.0, "OVERLAY_CARD", "reveal", "That's the gap. The job is live on company site. It is on HiringCafe. It hasn't reached LinkedIn.", ["Company site", "HiringCafe", "LinkedIn (not yet)"]),
    B("b11", 186.0, 191.4, "SELECTIVE_TEXT", "promise", "Time is your leverage. Early applicants get the call.", ["Time is your leverage", "Early applicants get the call"]),
    B("b12", 191.4, 197.5, "OVERLAY_CARD", "context", "Stay with me, I'll show how to use Claude to search and update your tracker overnight.", ["Claude", "Google Sheets", "Coming up"]),
    B("b13", 198.6, 203.8, "OVERLAY_CARD", "cta", "Please like, comment and subscribe to my channel.", ["Like", "Comment", "Subscribe"]),
    B("b14", 204.27, 231.0, "OVERLAY_CARD", "context", "It started as a spreadsheet; ex-Meta engineer; 10,000 jobs; Reddit; 2 million users; no money spent on ads.", ["Ex-Meta engineer", "10,000 jobs", "Reddit", "2 million users"]),
    B("b15", 231.0, 238.3, "OVERLAY_CARD", "definition", "There are two ways to search here. Classic search and AI search.", ["Classic search", "AI search"]),
    B("b16", 238.3, 270.4, "OVERLAY_CARD", "process", "Registered nurse, the filters, date posted set to 24 hours. That one filter is the whole strategy.", ["Date posted: 24 h", "One filter = the whole strategy"]),
    B("b17", 270.4, 326.8, "OVERLAY_CARD", "process", "Apply now, save the job, the tracker, statuses, follow-up notes.", ["Save", "Applied", "Interviewing", "Notes"]),
    B("b18", 326.8, 354.6, "OVERLAY_CARD", "definition", "Network: recruiters reach out to you. Add jobs is only for recruiters.", ["Network: recruiters come to you", "Add jobs: recruiters only"]),
    B("b19", 354.6, 373.2, "FULLSCREEN_MOTION", "problem", "The mistake: one title. 10 companies will call the same job 10 different things.", ["1 title", "10 names"]),
    B("b20", 373.8, 396.5, "FULLSCREEN_MOTION", "process", "Open Claude or ChatGPT, upload your resume and give this prompt.", ["Claude", "ChatGPT", "prompt"]),
    B("b21", 401.8, 425.2, "OVERLAY_CARD", "proof", "On September 28th... launching its AI talent agent allowing anyone to create AI agents to search across millions of jobs.", ["September 28", "AI talent agent"]),
    B("b22", 425.2, 473.0, "OVERLAY_CARD", "demo", "Upload my resume... almost 33 jobs, seven matching and 15 related... schedule an email alert.", ["33 jobs", "7 matching", "15 related", "Email alerts"]),
    B("b23", 473.0, 508.6, "OVERLAY_CARD", "reassurance", "On the free plan you can have only one chat per account... the free plan covers everything.", ["Free plan: 1 agent chat", "Everything shown = free"]),
    B("b24", 508.63, 515.8, "OVERLAY_CARD", "cta", "Please consider to like and subscribe.", ["Subscribe"]),
    B("b25", 518.0, 555.0, "OVERLAY_CARD", "demo", "HiringCafe connects to Claude, also ChatGPT... pink funnel... scheduled task... Google Sheet.", ["Claude", "ChatGPT", "Google Sheets"]),
    B("b26", 555.0, 582.2, "FULLSCREEN_MOTION", "process", "Why midnight? Claude usage works in five-hour sessions; search runs while I'm asleep.", ["24 h", "5-hour windows", "Used while you sleep"]),
    B("b27", 582.3, 595.8, "PRESENTER_INSET", "recap", "The whole thing in one breath: careers page, HiringCafe three times a day, ghost jobs and scams filtered, you apply early.", ["Careers page", "HiringCafe 3x a day", "Ghost jobs & scams filtered", "You apply early"]),
    B("b28", 597.1, 610.8, "SELECTIVE_TEXT", "promise", "An agent searching over 5 million jobs for you all day for free.", ["5,000,000+", "jobs"]),
    B("b29", 610.8, 617.6, "OVERLAY_CARD", "reveal", "Keep LinkedIn for networking and posting. But for finding a job, use HiringCafe.", ["LinkedIn: Networking, Posting", "HiringCafe: Finding"]),
    B("b30", 617.6, 623.4, "FULLSCREEN_MOTION", "reveal", "LinkedIn is for being found. HiringCafe is for finding.", ["LinkedIn is for being found.", "HiringCafe is for finding."]),
    B("b31", 623.4, 634.9, "OVERLAY_CARD", "cta", "Bookmark hiringcafe.com, search your title, last 24 hours, apply for one job. 5 minutes.", ["Bookmark hiringcafe.com", "Search your title", "Last 24 hours", "Apply to one"]),
    B("b32", 634.9, 640.2, "OVERLAY_CARD", "cta", "If you get stuck, tell me in the comments.", ["Comment below"]),
    B("b33", 640.2, 645.9, "OVERLAY_CARD", "cta", "If you got something out of this, consider subscribing. Hit like.", ["Subscribe", "Like"]),
    B("b34", 645.9, 652.3, "OVERLAY_CARD", "cta", "Know someone who is job hunting right now. Send them this video.", ["Share"]),
]
BY_ID = {b["id"]: b for b in BEATS}

def beat_at(t):
    for b in BEATS:
        if b["start"] <= t < b["end"]:
            return b
    return None
