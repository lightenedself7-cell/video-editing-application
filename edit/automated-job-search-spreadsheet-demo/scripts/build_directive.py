"""Builds editorial-directive.json on the CUT timeline. Beat times below are ORIGINAL source seconds;
everything after each removed cut is shifted back (see CUTS). Cues snap to transcript words."""
import json, re, sys
from pathlib import Path

P = Path("/home/dev/video-editing-application/edit/automated-job-search-spreadsheet-demo")
CUTS = [(384.8, 391.7), (405.0, 406.59)]  # ORIGINAL seconds removed from the edit source
words = json.load(open(P / "prepared/transcripts/section-1.json"))["words"]
sha = open(P / "reports/source-cut.sha256").read().split()[0]


def T(x):
    return round(x - sum(min(x, b) - a for a, b in CUTS if x > a), 3)


def norm(s):
    return re.sub(r"[^a-z0-9$]", "", s.lower())


def cue(word, near):
    c = [w for w in words if norm(w["w"]) == norm(word)]
    if not c:
        raise SystemExit(f"no word {word!r}")
    return min(c, key=lambda w: abs(w["start"] - near))["start"]


def beat(i, a, b, treatment, role, copy_, first_cue, **extra):
    d = {"id": f"b{i:02d}", "start": T(a), "end": T(b), "spoken_text": " ".join(copy_), "role": role, "treatment": treatment,
         "purpose": extra.pop("purpose"), "on_screen_copy": copy_, "reveal_sync": [{"element": copy_[0], "time": T(first_cue)}],
         "transition_in": "wipe-from-right" if treatment == "FULLSCREEN_MOTION" else "fade",
         "transition_out": "wipe-from-right" if treatment == "FULLSCREEN_MOTION" else "fade",
         "audio_continuity": "continuous", "rationale": extra.pop("rationale", "Planned in director-treatment.md"), "review_status": "approved"}
    if "props" in extra:
        extra["props"] = shift_props(extra["props"])
    d.update(extra)
    return d


def shift_props(o):
    if isinstance(o, dict):
        return {k: (T(v) if k == "cue" else shift_props(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [shift_props(x) for x in o]
    return o


CARD = {"x": 976, "y": 200, "width": 280, "height": 20}
CARD4 = {"x": 976, "y": 320, "width": 280, "height": 20}  # cards are centred on layout y; 4 rows need to sit lower
TAG = {"x": 40, "y": 616, "width": 400, "height": 90}
FULLSCR = {"x": 0, "y": 20, "width": 1280, "height": 680}
b = []
n = [0]


def add(*a, **k):
    n[0] += 1
    b.append(beat(n[0], *a, **k))


TAG2 = {"x": 972, "y": 112, "width": 300, "height": 90}  # top right, under the YouTube card teaser; outside the protected region
FULL720 = {"x": 0, "y": 0, "width": 1280, "height": 720}  # full height so the sheet tab bar stays visible
TABS = {"Config": {"x": 113, "width": 73}, "Jobs": {"x": 193, "width": 68}, "Rejected": {"x": 262, "width": 85}, "Log": {"x": 352, "width": 62}}


def tab(name, cue_, dur=2.8):
    return {"cue": cue_, "dur": dur, "active": {"x": TABS[name]["x"], "y": 688, "width": TABS[name]["width"], "height": 32}}


# ---- 0 - 31: hook (round 2: graphics from the first second)
add(0.3, 2.7, "OVERLAY_CARD", "context", ["THE BORING PART", "NOT APPLYING"], 0.4, layout=TAG, component="lower-third-tag",
    props={"text": "The boring part", "sub": "not applying", "cue": 0.4}, purpose="Names the pain in the first seconds")
add(2.8, 7.7, "OVERLAY_CARD", "process", ["filtering", "matching to your CV", "shortlisting"], 2.9, layout=CARD, component="explainer-card",
    props={"title": "The boring part", "rows": [{"text": "**Filtering**", "cue": 2.9, "icon": "brand/user/img25.png"},
                                                 {"text": "Matching every job to your **CV**", "cue": 3.5},
                                                 {"text": "Shortlisting the few **worth your time**", "cue": 5.2}]},
    purpose="Lists the three chores that get automated")
add(7.8, 10.0, "OVERLAY_CARD", "promise", ["AUTOMATE IT TODAY"], 8.3, layout=TAG, component="lower-third-tag",
    props={"text": "Automate it today", "cue": 8.3}, purpose="States the promise")
add(10.1, 19.2, "FULLSCREEN_MOTION", "process", ["CLAUDE DOES IT", "WHILE YOU SLEEP", "hiringcafe.com"], 10.2, component="section-title",
    props={"title": "Claude does it", "key": "while you sleep", "cue": 10.2,
           "tiles": [{"icon": "brand/claude.png", "cue": cue("claude", 10.2)}, {"icon": "brand/hiringcafe_com.png", "cue": 12.9, "scale": 2.4}]},
    purpose="Shows Claude and the hiringcafe.com site name the moment they are said")
add(19.4, 23.5, "OVERLAY_CARD", "context", ["LINK UP HERE", "TAP THE CARD"], cue("link", 20.7), layout=TAG2, component="lower-third-tag",
    props={"text": "Link up here", "sub": "tap the card", "cue": cue("link", 20.7), "size": 30, "align": "right"}, purpose="Points at the YouTube card, which is the clickable link")
add(23.9, 31.0, "OVERLAY_CARD", "proof", ["36 searches", "15 jobs read", "1 in my sheet"], cue("36", 25), layout=CARD, component="explainer-card",
    props={"title": "One night", "rows": [{"text": "**36** searches", "cue": cue("36", 25)}, {"text": "**15** jobs read", "cue": cue("15", 26.4)},
                                           {"text": "**1** in my sheet", "cue": cue("one", 28.3)}]}, purpose="Makes the result concrete")
# ---- 31 - 55: promise
add(31.2, 36.6, "OVERLAY_CARD", "proof", ["no job board", "no prompt", "no cell"], 31.5, layout=CARD, component="explainer-card",
    props={"title": "Hands off", "rows": [{"text": "No **job board** opened", "cue": 31.5}, {"text": "No **prompt** typed", "cue": 32.9},
                                          {"text": "No **cell** typed", "cue": 35.2}]}, purpose="Shows how little effort it takes")
add(39.6, 42.9, "OVERLAY_CARD", "context", ["NO BORED SEARCHING"], 40.2, layout=TAG, component="lower-third-tag",
    props={"text": "No bored searching", "cue": 40.2}, purpose="Names what the viewer skips")
add(43.3, 52.0, "OVERLAY_CARD", "context", ["tested in Claude", "not locked to Claude", "any AI app with connectors"], 43.5, layout=CARD,
    component="explainer-card",
    props={"title": "Not just Claude", "rows": [{"text": "Tested in **Claude**", "cue": 43.5, "icon": "brand/claude.png"},
                                                {"text": "Connector is **not locked** to Claude", "cue": 45.6},
                                                {"text": "Any AI app with **connectors**", "cue": 48.0}]},
    purpose="Says the idea works beyond Claude")
add(55.1, 59.2, "OVERLAY_CARD", "promise", ["1 SHEET + 2 PROMPTS"], cue("one", 55.3), layout=TAG, component="lower-third-tag",
    props={"text": "1 sheet + 2 prompts", "cue": cue("one", 55.3)}, purpose="States the deliverables")
add(59.3, 72.3, "FULLSCREEN_MOTION", "process", ["WHAT YOU NEED", "3 THINGS"], cue("claude", 60.6), component="section-title",
    props={"title": "What you\nneed", "key": "3 things", "cue": 59.6,
           "tiles": [{"icon": "brand/claude.png", "cue": 60.66}, {"icon": "brand/hiringcafe.png", "cue": 64.18},
                     {"icon": "brand/sheets_icon.png", "cue": 68.74}]},
    purpose="Opens the requirements section with the three apps shown as they are named")
add(72.4, 75.8, "OVERLAY_CARD", "reassurance", ["NO CODE, NO API KEYS"], cue("code", 73.4), layout=TAG, component="lower-third-tag",
    props={"text": "No code, no API keys", "cue": cue("no", 72.5)}, purpose="Reassurance")
add(81.8, 85.9, "OVERLAY_CARD", "context", ["LAUNCHED LATE OCTOBER"], cue("launched", 82), layout=TAG, component="lower-third-tag",
    props={"text": "Launched late October", "cue": cue("launched", 82)}, purpose="Dates the connector")
add(86.0, 98.6, "FULLSCREEN_MOTION", "process", ["THE HARD WAY", "A SCRAPER"], 86.1, component="section-title",
    props={"title": "The hard way", "key": "a scraper", "cue": 86.1,
           "tiles": [{"icon": "brand/user/img27.png", "cue": 88.4, "scale": 1.2}, {"icon": "brand/user/img29.png", "cue": 89.4, "scale": 1.7},
                     {"icon": "brand/hiringcafe.png", "cue": 90.3}]},
    purpose="Shows the Apify scraper story instead of a face-only stretch")
add(98.8, 107.3, "FULLSCREEN_MOTION", "proof", ["Disallow: /*?searchState=*"], 99.3, component="spotlight-box",
    props={"boxes": [{"x": 0, "y": 420, "width": 440, "height": 100, "cue": 99.3, "marker": {"x": 4, "y": 470, "width": 162, "height": 16}}]},
    purpose="Zoom on the robots.txt rule being discussed")
add(107.7, 122.4, "OVERLAY_CARD", "process", ["the front door", "built for Claude", "and ChatGPT", "scrapers can get blocked"], cue("front", 108.3), layout=CARD4,
    component="explainer-card",
    props={"title": "The front door", "rows": [{"text": "Connector is the **front door**", "cue": cue("front", 108.3)},
                                               {"text": "Built for **Claude**", "cue": 109.9, "icon": "brand/claude.png"},
                                               {"text": "And **ChatGPT**", "cue": 110.84, "icon": "brand/chatgpt.png"},
                                               {"text": "Scrapers: cheaper, can get **blocked**", "cue": 112.3, "icon": "brand/user/img26.png"}]},
    purpose="Connector vs scraper, with the apps shown")
add(123.0, 127.5, "OVERLAY_CARD", "context", ["BUILT FOR THIS", "THE CONNECTOR"], 123.2, layout=TAG, component="lower-third-tag",
    props={"text": "Built for this", "sub": "the connector", "cue": 123.2}, purpose="Lands the point")
add(130.8, 144.8, "FULLSCREEN_MOTION", "proof", ["connector docs"], 131.0, component="screen-share", props={"screen": FULLSCR},
    purpose="Frames the docs page while read-only and filters are explained")
add(149.9, 162.9, "OVERLAY_CARD", "process", ["alert vs this"], cue("matches", 151), layout=CARD4, component="explainer-card",
    props={"title": "Alert vs this", "rows": [{"text": "Alert sends **matches**", "cue": cue("matches", 151)},
                                               {"text": "Applies your **rules**", "cue": cue("rules", 152.9)},
                                               {"text": "Says **why** kept or out", "cue": cue("why", 154)},
                                               {"text": "Keeps a **record**", "cue": cue("record", 156.6)}]}, purpose="Answers the alerts question")
add(163.95, 166.9, "FULLSCREEN_MOTION", "context", ["STEP 1", "BUILD THE SHEET"], 164.2, component="section-title",
    props={"title": "Step 1", "key": "Build the sheet", "cue": 164.3}, purpose="Section title",
    rationale="Short title card over 'Step one'")
add(167.0, 186.7, "FULLSCREEN_MOTION", "process", ["Drive, sheet link, Claude prompt"], 167.2, component="screen-share", props={"screen": FULLSCR},
    purpose="Teal window for the Drive and Claude setup steps")
add(186.8, 203.6, "FULLSCREEN_MOTION", "proof", ["deal-breakers"], cue("deal", 187), component="spotlight-box",
    props={"boxes": [{"x": 495, "y": 470, "width": 530, "height": 80, "cue": cue("deal", 187)}]}, purpose="Zoom on the deal-breakers text")
add(204.4, 236.5, "FULLSCREEN_MOTION", "process", ["Config tab"], 204.8, component="screen-share", props={"screen": FULLSCR},
    purpose="Teal window while the Config tab fills in")
add(236.7, 252.9, "FULLSCREEN_MOTION", "proof", ["Gap: no people management"], cue("line", 237.4), component="spotlight-box",
    props={"boxes": [{"x": 545, "y": 392, "width": 700, "height": 52, "cue": cue("line", 237.4), "marker": {"x": 545, "y": 408, "width": 685, "height": 17}}]},
    purpose="Zoom on the gap line")
add(254.6, 257.0, "OVERLAY_CARD", "cta", ["LIKE, COMMENT, SUBSCRIBE"], 254.8, layout=TAG, component="lower-third-tag",
    props={"text": "Like, comment, subscribe", "cue": cue("like", 254.8)}, purpose="Mid-roll call to action")
add(260.4, 278.4, "OVERLAY_CARD", "context", ["sound familiar", "40 minutes later", "same posting 3 times", "months old"], 260.6, layout=CARD4,
    component="explainer-card",
    props={"title": "Sound familiar?", "rows": [{"text": "Squeezing in **job hunting**", "cue": 260.8, "icon": "brand/user/img28.png"},
                                                {"text": "**40 minutes** later...", "cue": 268.0},
                                                {"text": "Same posting **3 times**", "cue": 270.4},
                                                {"text": "Some are **months old**", "cue": 272.2}]},
    purpose="Fills the longest face-only stretch with the problem the viewer recognises")
add(278.6, 281.3, "OVERLAY_CARD", "context", ["THAT'S SCROLLING", "NOT A JOB"], 278.7, layout=TAG, component="lower-third-tag",
    props={"text": "That's scrolling", "sub": "not a job", "cue": 278.7}, purpose="Punchline")
add(281.45, 285.2, "FULLSCREEN_MOTION", "context", ["STEP 2", "THE NIGHTLY PROMPT"], 281.8, component="section-title",
    props={"title": "Step 2", "key": "The nightly prompt", "cue": 281.9}, purpose="Section title")
add(285.3, 313.9, "FULLSCREEN_MOTION", "process", ["nightly prompt, 3 things"], 285.6, component="screen-share",
    props={"screen": {"x": 641, "y": 191, "width": 638, "height": 338}, "presenter": {"x": 110, "y": 190, "width": 400, "height": 350}},
    purpose="The split-screen source is re-framed: screen in the teal window, presenter in the card",
    rationale="Replaces the planned explainer card: the source is already split screen, so the card would cover content")
# whole Customer Success Manager row, then the Technical PM row; the tab bar stays sharp with the Jobs tab glowing
ROW3 = {"x": 2, "y": 282, "width": 1195, "height": 18}
ROW2 = {"x": 2, "y": 264, "width": 1195, "height": 18}
add(314.0, 322.4, "FULLSCREEN_MOTION", "proof", ["Medium", "High"], cue("medium", 319), component="spotlight-box",
    props={"boxes": [{"x": 0, "y": 240, "width": 1280, "height": 100, "cue": 316.9, "marker": ROW3},
                     {"x": 0, "y": 240, "width": 1280, "height": 100, "cue": 320.3, "marker": ROW2}],
           "keep": [{"x": 100, "y": 684, "width": 330, "height": 36}], "tab_marks": [tab("Jobs", 314.4, 8.0)]},
    purpose="Highlights the whole Customer Success Manager row (Medium), then Technical PM (High)")
add(322.6, 377.3, "FULLSCREEN_MOTION", "process", ["Jobs, Rejected, Log, scheduling"], 323, component="screen-share",
    props={"screen": FULL720, "tab_marks": [tab("Rejected", 328.75), tab("Log", 333.75), tab("Jobs", 337.75), tab("Rejected", 349.0),
                                            tab("Config", 361.25)]},
    purpose="Full-height teal window so the sheet tab names show, with the active tab glowing at each switch")
add(377.5, 384.7, "FULLSCREEN_MOTION", "context", ["WHY MIDNIGHT?", "5-HOUR SESSIONS"], 378, component="section-title",
    props={"kicker": "Why midnight?", "title": "Usage works in", "key": "5-hour sessions", "cue": 377.8}, purpose="Section title")
add(395.3, 411.4, "OVERLAY_CARD", "process", ["midnight", "5 AM", "weekly limit", "24 hours"], cue("midnight", 396), layout=CARD4,
    component="explainer-card",
    props={"title": "Why it works", "rows": [{"text": "Runs at **midnight**", "cue": cue("midnight", 396)},
                                              {"text": "Session ends by **5 AM**", "cue": cue("five", 398.2)},
                                              {"text": "Still counts toward your **weekly limit**", "cue": cue("weekly", 404.3)},
                                              {"text": "Last **24 hours**, max 25", "cue": cue("hours", 408.4)}]},
    purpose="Summarises the session and limit explanation")
add(412.5, 417.2, "OVERLAY_CARD", "recap", ["blank sheet", "builds", "runs", "sleep"], cue("blank", 412.6), layout=CARD4, component="explainer-card",
    props={"title": "Recap", "rows": [{"text": "A **blank** sheet", "cue": cue("blank", 412.6)}, {"text": "One prompt **builds** it", "cue": cue("builds", 414.9)},
                                      {"text": "One prompt **runs** it", "cue": cue("runs", 415.8)}, {"text": "Works while you **sleep**", "cue": cue("sleep", 416.4)}]},
    purpose="Recap")
add(417.3, 420.2, "OVERLAY_CARD", "cta", ["BOTH PROMPTS IN THE DESCRIPTION"], cue("both", 417.4) + 0.05, layout=TAG, component="lower-third-tag",
    props={"text": "Both prompts in the description", "cue": cue("both", 417.4) + 0.05}, purpose="Points to the prompts")
add(420.4, 427.5, "OVERLAY_CARD", "process", ["search changes", "tell Claude", "add product manager", "it updates the sheet"], 420.5, layout=CARD4,
    component="explainer-card",
    props={"title": "When your search changes", "rows": [{"text": "Don't touch the **prompt**", "cue": 420.5},
                                                          {"text": "Tell **Claude** what changed", "cue": 421.6, "icon": "brand/claude.png"},
                                                          {"text": "\"Add **product manager** to my titles\"", "cue": 423.0},
                                                          {"text": "It **updates** the sheet", "cue": 424.8}]},
    purpose="Fills the face-only stretch with how to change the search")
add(436.5, 440.3, "OVERLAY_CARD", "cta", ["LIKE, COMMENT, SHARE"], cue("like", 436.7), layout=TAG, component="lower-third-tag",
    props={"text": "Like, comment, share", "cue": cue("like", 436.7)}, purpose="Closing call to action")
add(449.4, 453.4, "OVERLAY_CARD", "cta", ["STUCK? ASK IN THE COMMENTS"], cue("stuck", 450.7), layout=TAG, component="lower-third-tag",
    props={"text": "Stuck? Ask in the comments", "cue": cue("stuck", 450.7)}, purpose="Invites questions")

d = {"version": 1, "project": "automated-job-search-spreadsheet-demo", "theme": "teal-spotlight",
     "source": {"path": "/home/dev/videos/automated-job-search-spreadsheet-demo-cut.mp4", "sha256": sha, "width": 1280, "height": 720,
                "fps": "30/1", "duration_s": 446.273},
     "approval": {"status": "approved", "approved_scope": "Teal Spotlight plan in director-treatment.md, round 2: repeated 'five-hour sessions' take (384.8-391.7 s) and the false start 'that's why the prompt only look' (405.0-406.59 s) cut; extra graphics",
                  "ambiguities": []},
     "protected_regions": [{"name": "presenter", "x": 260, "y": 0, "width": 700, "height": 600}],
     "beats": b}
json.dump(d, open(P / "editorial-directive.json", "w"), indent=1)
print(len(b), "beats")
