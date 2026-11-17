"""Round-3 edits to build_directive.py: layouts away from the corners, strike-through, focus-points, pipeline beats (run once)."""
import re
from pathlib import Path

D = Path(r"\\wsl$\Ubuntu-24.04\home\dev\video-editing-application\edit\automated-job-search-spreadsheet-demo\scripts\build_directive.py")
s = D.read_text(encoding="utf-8").replace("\r\n", "\n")
if "PIPE_STEPS" in s:
    raise SystemExit("already patched")


def rep(old, new, count=1):
    global s
    assert old in s, old[:60]
    s = s.replace(old, new, count)


def to_cardr(start_marker):
    global s
    i = s.index(start_marker)
    j = s.index("layout=CARD4", i)
    s = s[:j] + "layout=CARDR" + s[j + len("layout=CARD4"):]


# layouts: room 1 (pink wall) -> left-centre; room 2 and screen overlays -> right-centre; tags above the player bar
rep('CARD = {"x": 976, "y": 200, "width": 280, "height": 20}', 'CARD = {"x": 12, "y": 360, "width": 280, "height": 20}  # left-centre (room 1)')
rep('CARD4 = {"x": 976, "y": 320, "width": 280, "height": 20}  # cards are centred on layout y; 4 rows need to sit lower',
    'CARD4 = {"x": 12, "y": 360, "width": 280, "height": 20}  # cards are centred on layout y\nCARDR = {"x": 984, "y": 360, "width": 280, "height": 20}  # right-centre (second room, screen stretches)')
rep('TAG = {"x": 40, "y": 616, "width": 400, "height": 90}', 'TAG = {"x": 24, "y": 452, "width": 400, "height": 90}  # left-centre, below the face region, clear of the player bar')
rep('"protected_regions": [{"name": "presenter", "x": 260, "y": 0, "width": 700, "height": 600}]',
    '"protected_regions": [{"name": "presenter", "x": 300, "y": 0, "width": 660, "height": 440}]')
for m in ("add(260.4", "add(395.3", "add(412.5", "add(420.4"):
    to_cardr(m)

# hands-off card with strike-through
i = s.index("add(31.2, 36.6")
j = s.index("add(39.6")
s = s[:i] + '''add(31.2, 37.4, "OVERLAY_CARD", "proof", ["no job board", "no prompt", "no cell"], 31.3, layout=CARD, component="explainer-card",
    props={"title": "Skipped", "rows": [{"text": "Open a **job board**", "cue": 31.3, "strike": 31.95},
                                        {"text": "Type a **prompt**", "cue": 32.5, "strike": 33.3},
                                        {"text": "Type a **cell**", "cue": 35.0, "strike": 36.15}]},
    purpose="Each skipped chore gets struck through as it is named")
''' + s[j:]

# not just Claude -> focus-points
i = s.index("add(43.3, 52.0")
j = s.index("add(55.1")
s = s[:i] + '''add(43.3, 52.0, "FULLSCREEN_MOTION", "context", ["tested in Claude", "not locked to Claude", "any AI app with connectors"], 43.5, component="focus-points",
    props={"title": "Works beyond Claude",
           "points": [{"text": "Tested in **Claude**", "cue": 43.5, "icon": "brand/claude.png"},
                      {"text": "Connector is **not locked** to Claude", "cue": 45.6},
                      {"text": "Any AI app with **connectors**", "cue": 48.0}]},
    purpose="Blurs the presenter and brings the three points to the centre")
''' + s[j:]

rep('"title": "When your search changes"', '"title": "Search changed?"')

# pipeline definitions
rep("# ---- 0 - 31: hook", '''PIPE_STEPS = [{"label": "Blank sheet", "sub": "in Google Drive"}, {"label": "Setup prompt", "sub": "in Claude"},
              {"label": "Check Config", "sub": "tabs fill in"}, {"label": "Nightly prompt", "sub": "runs every night"},
              {"label": "Read the sheet", "sub": "Jobs, Rejected, Log"}, {"label": "Schedule it", "sub": "check in the morning"}]


def pipe(a, b, active, cue_):
    add(a, b, "FULLSCREEN_MOTION", "process", ["PIPELINE", PIPE_STEPS[active]["label"].upper()], cue_, component="pipeline",
        props={"title": "The pipeline", "steps": PIPE_STEPS, "active": active, "cue": cue_},
        purpose="Shows where we are in the pipeline and lights the step as it is discussed")


# ---- 0 - 31: hook''')

# Step 1 title -> pipeline step 1, split the screen shares around the pipeline beats
i = s.index("add(163.95, 166.9")
j = s.index("add(186.8, 203.6")
s = s[:i] + '''pipe(163.95, 168.9, 0, 166.0)
add(169.0, 172.5, "FULLSCREEN_MOTION", "process", ["Drive sheet link"], 169.2, component="screen-share", props={"screen": FULLSCR},
    purpose="Teal window for copying the sheet link")
pipe(172.6, 176.6, 1, 173.1)
add(176.7, 186.7, "FULLSCREEN_MOTION", "process", ["Claude setup prompt"], 176.9, component="screen-share", props={"screen": FULLSCR},
    purpose="Teal window for the Claude setup prompt")
''' + s[j:]

i = s.index("add(204.4, 236.5")
j = s.index("add(236.7")
s = s[:i] + '''add(204.4, 210.3, "FULLSCREEN_MOTION", "process", ["Config tab"], 204.8, component="screen-share", props={"screen": FULLSCR},
    purpose="Teal window while the sheet fills in")
pipe(210.4, 214.4, 2, 210.7)
add(214.5, 236.5, "FULLSCREEN_MOTION", "process", ["Config tab"], 214.7, component="screen-share", props={"screen": FULLSCR},
    purpose="Teal window while the Config tab is explained")
''' + s[j:]

# Step 2 title -> pipeline step 4
i = s.index("add(281.45, 285.2")
j = s.index("add(285.3, 313.9")
s = s[:i] + "pipe(281.45, 285.2, 3, 281.9)\n" + s[j:]

# step 5 before the Jobs spotlight
rep("add(314.0, 322.4", "pipe(313.95, 317.2, 4, 314.3)\nadd(317.3, 322.4")
rep('"cue": 316.9, "marker": ROW3}', '"cue": 317.9, "marker": ROW3}')
rep('"tab_marks": [tab("Jobs", 314.4, 8.0)]', '"tab_marks": [tab("Jobs", 317.5, 5.0)]')

# step 6: schedule
rep('add(322.6, 377.3, "FULLSCREEN_MOTION", "process", ["Jobs, Rejected, Log, scheduling"], 323, component="screen-share",',
    'add(322.6, 364.6, "FULLSCREEN_MOTION", "process", ["Jobs, Rejected, Log"], 323, component="screen-share",')
i = s.index("add(377.5, 384.7")
s = s[:i] + '''pipe(364.7, 368.9, 5, 365.0)
add(369.0, 377.3, "FULLSCREEN_MOTION", "process", ["Scheduled task"], 369.2, component="screen-share", props={"screen": FULL720},
    purpose="Teal window for the scheduled-task page")
''' + s[i:]

D.write_text(s, encoding="utf-8")
print("directive patched")
