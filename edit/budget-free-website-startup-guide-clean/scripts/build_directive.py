import json, hashlib
SRC="/home/dev/videos/budget-free-website-startup-guide-clean.mp4"
SHA="ea8bfd2eec998ef7393aac1695fb664b7b4fde70e56676f8b19530be5212617c"
DUR=729.367
W=json.load(open("transcripts/budget-free-website-startup-guide-clean.json"))["words"]
W=[w for w in W if w["type"]=="word"]
def said(a,b): return " ".join(w["text"] for w in W if w["start"]>=a-0.05 and w["end"]<=b+0.05)

SCREENS=[(78.2,94.6),(123.8,290.0),(370.0,697.4)]
COLUMN={"x":32,"y":32,"width":368,"height":656}          # side-column presenter (crop src x408-812 full height, scale 0.911)
COLUMN_GFX={"x":440,"y":56,"width":808,"height":608}
RIGHT_CARD={"x":976,"y":150,"width":280,"height":420}     # right of presenter corridor (x260-960)
CHIP={"x":976,"y":40,"width":272,"height":44}             # top-right chip, over the browser tab bar of a framed screen
FULL={"x":0,"y":0,"width":1280,"height":720}
WINDOW={"x":48,"y":120,"width":768,"height":432}
WINDOW_GFX={"x":860,"y":120,"width":380,"height":480}

beats=[]
def B(id,s,e,role,tr,purpose,copy,sync=(),tin="cut",tout="cut",rat="",**kw):
    b={"id":id,"start":s,"end":e,"spoken_text":said(s,e),"role":role,"treatment":tr,"purpose":purpose,
       "on_screen_copy":list(copy),"reveal_sync":[{"element":el,"time":t} for el,t in sync],
       "transition_in":tin,"transition_out":tout,"audio_continuity":"continuous","rationale":rat,"review_status":"approved"}
    b.update(kw); beats.append(b)

ROAD=["Prep","Build","Go static","Mobile check","Go live","Speed check"]
def road(id,s,e,node,cue,rat,tin="slide-from-right",tout="slide-out-right"):
    B(id,s,e,"roadmap","FULLSCREEN_MOTION","Roadmap marker: show where we are in the build",
      ROAD,[(ROAD[node-1] if node else "all steps lit",cue)],tin,tout,rat,layout=FULL,
      roadmap={"nodes":ROAD,"active":node or "all","done":list(range(1,node)) if node else list(range(1,7))})

# ---------- A. camera 0-78.2 : hook + promise + story ----------
B("b01",0.0,7.3,"hook","CLEAN_PRESENTER","Live site on the phone in her hand; the face sells it",[],
  rat="Opening proof shot. Her phone already shows the site; nothing should compete.")
B("b02",7.4,23.6,"proof","OVERLAY_CARD","Glass stat card: what the site does and what it costs",
  ["Instant on mobile","Book on WhatsApp","$0 hosting","Domain under $10 / year"],
  [("Instant on mobile",7.72),("Book on WhatsApp",10.12),("$0 hosting",12.22),("Domain under $10 / year",18.28)],
  "glass-slide-from-right","glass-slide-out-right",
  "Four short facts the hook says aloud, one per spoken word. Lives right of the presenter corridor. WhatsApp icon (official) next to its line.",
  layout=RIGHT_CARD,brand_icons=[{"brand":"WhatsApp","time":10.12}])
B("b03",23.6,44.1,"problem","CLEAN_PRESENTER","Her four-hour story and the promise: trust moment",[],
  rat="Story + promise stay clean. Attention toolkit: punch-in 1.10x on the jump at 23.92 (new sentence), back to 1.0 at 34.80 ('In this video').",
  punch_ins=[{"in":23.92,"out":34.80,"scale":1.10}])
B("b04",44.1,47.9,"promise","SELECTIVE_TEXT","Kinetic keyword on the payoff",
  ["under **2 hours**"],[("under **2 hours**",44.32)],"scale-90-100","fade",
  "One keyword beside her head, right column, 90%->100% spring then fade.",layout={"x":976,"y":250,"width":280,"height":90})
B("b05",47.9,60.4,"context","CLEAN_PRESENTER","Setup and the start of the dad story",[],
  rat="Punch-in at 50.46 (\"You can tweak\"), out at 58.16 (\"he didn't need anything fancy\").",
  punch_ins=[{"in":50.46,"out":58.16,"scale":1.10}])
B("b06",60.4,70.9,"definition","OVERLAY_CARD","Glass card: what Dad actually needed",
  ["Rooms","Rates","WhatsApp or call"],[("Rooms",62.74),("Rates",63.84),("WhatsApp or call",65.74)],
  "glass-slide-from-right","glass-slide-out-right","The brief that 'decided everything that followed'; three items on their words.",layout=RIGHT_CARD)
road("b07",71.0,77.5,1,73.96,"First roadmap appearance: path draws, six nodes appear left to right, node 1 lights on 'get these together'. Exits before the prep-doc screen at 78.2.")
# ---------- B. screen 78.2-94.6 ----------
B("b08",77.5,94.6,"process","CLEAN_PRESENTER","Prep doc screen recording, framed",[],
  rat="Creator's own screen share. Shown in the floating rounded frame (see screen_framing), no overlays.",screen=True)
# ---------- C. camera 94.6-123.8 ----------
B("b09",94.8,120.5,"process","PRESENTER_INSET","Side-column: the prep checklist",
  ["Real photos","About 2 hours","Domain price","Missing info? Leave it out","The prep is the work"],
  [("Real photos",95.74),("About 2 hours",101.30),("Domain price",102.20),("Missing info? Leave it out",110.98),("The prep is the work",117.40)],
  "column-move-in","column-move-out",
  "Presenter moves into a full-height left column (crop x408-812, scale 0.911, eyes upper third); checklist cards build on the right, each with a rose check. Last line is the payoff, bold.",
  presenter_layout=COLUMN,layout=COLUMN_GFX)
road("b10",120.6,123.7,2,121.32,"Node 2 'Build' lights on 'jump straight into the tool'; exits right as the AI Studio screen begins (123.8).")
# ---------- D. screen 123.8-290 ----------
B("b11",123.8,124.5,"process","CLEAN_PRESENTER","AI Studio screen",[],rat="Framed screen.",screen=True)
B("b12",124.5,129.5,"process","OVERLAY_CARD","Brand chip on the tool name",["Google AI Studio"],[("Google AI Studio",124.60)],
  "chip-fade-slide","fade","Official AI Studio icon + label chip on the word, top-right over the browser tab bar.",layout=CHIP,brand_icons=[{"brand":"Google AI Studio","time":124.60}],screen=True)
B("b13",129.5,191.0,"process","CLEAN_PRESENTER","Build walkthrough on screen",[],rat="Screen carries it; framed only.",screen=True)
B("b14",191.0,196.0,"process","OVERLAY_CARD","Chip: reality check",["Reality check"],[("Reality check",192.52)],"chip-fade-slide","fade",
  "Marks the sub-step without a full roadmap stop.",layout=CHIP,screen=True)
B("b15",196.0,215.8,"process","CLEAN_PRESENTER","Screen",[],rat="Framed screen.",screen=True)
B("b16",215.8,220.6,"process","OVERLAY_CARD","Numbered chip 1",["1  Real photos"],[("1  Real photos",215.88)],"chip-fade-slide","fade","Spoken list item, numbered badge.",layout=CHIP,screen=True)
B("b17",220.6,225.8,"process","CLEAN_PRESENTER","Screen",[],rat="Framed screen.",screen=True)
B("b18",225.8,230.8,"process","OVERLAY_CARD","Numbered chip 2",["2  Distances"],[("2  Distances",227.62)],"chip-fade-slide","fade","Spoken list item.",layout=CHIP,screen=True)
B("b19",230.8,248.6,"process","CLEAN_PRESENTER","Screen",[],rat="Framed screen.",screen=True)
B("b20",248.6,253.6,"process","OVERLAY_CARD","Numbered chip 3",["3  Booking button"],[("3  Booking button",249.68)],"chip-fade-slide","fade","Spoken list item.",layout=CHIP,screen=True)
B("b21",253.6,289.8,"process","CLEAN_PRESENTER","Booking demo on screen",[],rat="Framed screen.",screen=True)
# ---------- E. camera 290-370 ----------
road("b22",289.8,292.6,3,291.52,"Node 3 'Go static' lights on 'where I got stuck'. Enters as the camera returns (290.0).")
B("b23",292.7,302.4,"question","SELECTIVE_TEXT","Question beat",
  ["No limits: what kind of site does AI **build**?"],[("No limits: what kind of site does AI **build**?",294.42)],
  "darken-blur-in","darken-blur-out","Turn in the argument: footage dims + soft blur, one thin centred line, one bold word; holds through 'Hold that guess'.",
  layout={"x":160,"y":616,"width":960,"height":56},footage_treatment="dim 45% + 6px blur")
B("b24",302.6,349.8,"comparison","PRESENTER_INSET","Side-column: dynamic vs static",
  ["Dynamic","Static","Knows who you are","Server + database","A brochure: same page for everyone","Enough for a small hotel","No limits → a full React app"],
  [("Dynamic",305.14),("Static",306.06),("Knows who you are",307.20),("Server + database",323.0),("A brochure: same page for everyone",328.98),("Enough for a small hotel",335.42),("No limits → a full React app",344.66)],
  "column-move-in","column-move-out",
  "Two glass cards side by side. Amazon icon under Dynamic on 'Amazon' (311.10). Final line lights the Dynamic card rose: that's what AI built.",
  presenter_layout=COLUMN,layout=COLUMN_GFX,brand_icons=[{"brand":"Amazon","time":311.10}])
B("b25",349.8,357.6,"reveal","CLEAN_PRESENTER","Punchline: built like a banking app, Dad needed a brochure",[],
  rat="Full frame for the payoff line.")
B("b26",357.6,364.8,"proof","OVERLAY_CARD","Glass stat card: the failure",["25 MiB file limit","Upload failed"],
  [("25 MiB file limit",361.26),("Upload failed",363.30)],"glass-slide-from-right","glass-slide-out-right",
  "Cloudflare icon on 'Cloudflare' (heard as 'cloud player', 357.88). One fact card.",layout=RIGHT_CARD,brand_icons=[{"brand":"Cloudflare","time":357.88}])
B("b27",364.8,370.0,"story","CLEAN_PRESENTER","An hour to figure out",[],rat="Punch-in 1.10x at 364.66 to the cut at 370.0.",punch_ins=[{"in":364.9,"out":370.0,"scale":1.10}])
# ---------- F. screen 370-570.4 ----------
B("b28",370.0,386.6,"process","CLEAN_PRESENTER","The static-site prompt on screen",[],rat="Framed screen.",screen=True)
road("b29",386.6,389.6,4,387.62,"Node 4 'Mobile check' lights on 'Most of your guests'.")
B("b30",395.2,406.4,"process","FULLSCREEN_MOTION","Phone mockup: the live mobile preview",
  ["Look at it on a phone"],[("Look at it on a phone",395.7)],"slide-from-right","slide-out-right",
  "Attention toolkit phone mockup. The live mobile preview from the screen recording (crop x596-910 y180-680, scale 1.25) plays inside a 9:16 rounded phone frame with a raspberry glow; her baked bubble (crop x996-1262 y420-688) sits in a glowing portrait bubble bottom-right. Real footage, nothing faked. Starts at 395.2 s, the first settled frame after the preview switches to Mobile (395.1 s).",
  layout=FULL,footage_inserts=[{"name":"mobile-preview","crop":{"x":596,"y":180,"width":314,"height":500}},{"name":"bubble","crop":{"x":996,"y":420,"width":266,"height":268}}])
B("b31",406.4,430.0,"process","CLEAN_PRESENTER","Screenshot-and-fix on screen",[],rat="Framed screen; she points at UI, so it stays visible.",screen=True)
B("b32",430.0,447.6,"proof","FULLSCREEN_MOTION","Phone mockup: after the fix",
  ["After the fix"],[("After the fix",430.04)],"slide-from-right","slide-out-right",
  "Same phone mockup, same geometry, showing the fixed mobile view while she says the phone interface must be smooth.",
  layout=FULL,footage_inserts=[{"name":"mobile-preview","crop":{"x":596,"y":180,"width":314,"height":500}},{"name":"bubble","crop":{"x":996,"y":420,"width":266,"height":268}}])
B("b33",447.6,481.8,"process","CLEAN_PRESENTER","Restore versions on screen",[],rat="Framed screen.",screen=True)
road("b34",481.8,484.6,5,481.94,"Node 5 'Go live' lights on 'once we are happy'.")
B("b35",484.6,528.0,"process","CLEAN_PRESENTER","Export and unzip on screen",[],rat="Framed screen.",screen=True)
B("b36",528.0,533.0,"process","OVERLAY_CARD","Brand chip",["Cloudflare Drop"],[("Cloudflare Drop",528.10)],"chip-fade-slide","fade",
  "Official Cloudflare icon chip on the word.",layout=CHIP,brand_icons=[{"brand":"Cloudflare","time":528.10}],screen=True)
B("b37",533.0,570.4,"process","CLEAN_PRESENTER","Upload, claim",[],rat="Framed screen.",screen=True)
# ---------- G. (screen continues) 570.4-597: live site ----------
B("b38",570.4,573.7,"process","CLEAN_PRESENTER","Live site on screen",[],rat="Framed screen.",screen=True)
B("b39",573.7,579.2,"process","OVERLAY_CARD","Chip: launch check",["Open on your phone, tap every button"],[("Open on your phone, tap every button",573.88)],"chip-fade-slide","fade",
  "The live site is on screen (desktop view), so a phone mockup would need invented UI; a single chip carries the instruction.",layout={"x":968,"y":36,"width":280,"height":68},screen=True)
B("b39b",579.2,591.0,"process","CLEAN_PRESENTER","Live site on screen",[],rat="Framed screen.",screen=True)
B("b39c",591.0,596.4,"process","OVERLAY_CARD","Chip: Dad's check",["Check every room, rate, number"],[("Check every room, rate, number",591.12)],"chip-fade-slide","fade",
  "Her dad's review, the human check before buying a domain.",layout={"x":968,"y":36,"width":280,"height":68},screen=True)
B("b39d",596.4,597.0,"process","CLEAN_PRESENTER","Screen",[],rat="Framed screen.",screen=True)
# ---------- H. screen 597-697.4 (continued) ----------
B("b40",597.0,612.0,"process","CLEAN_PRESENTER","Domain purchase",[],rat="Framed screen.",screen=True)
B("b41",612.0,617.0,"proof","OVERLAY_CARD","Stat chip",["Under $10 / year"],[("Under $10 / year",613.52)],"chip-fade-slide","fade","Price chip on the spoken figure.",layout=CHIP,screen=True)
B("b42",617.0,631.2,"process","CLEAN_PRESENTER","Renewal, HTTPS",[],rat="Framed screen.",screen=True)
B("b43",631.2,636.0,"proof","OVERLAY_CARD","Stat chip",["Wholesale, zero markup"],[("Wholesale, zero markup",631.32)],"chip-fade-slide","fade","",layout=CHIP,screen=True)
B("b44",636.0,647.6,"process","CLEAN_PRESENTER","Link and go live",[],rat="Framed screen.",screen=True)
road("b45",647.6,650.4,6,648.54,"Node 6 'Speed check' lights on 'speed check'.")
B("b46",650.4,697.4,"process","CLEAN_PRESENTER","PageSpeed walkthrough",[],rat="Framed screen; scores are already legible.",screen=True)
# ---------- I. camera 697.4-729.4 ----------
road("b47",697.5,700.6,0,698.12,"Final roadmap return: all six nodes lit on 'That's the entire process'.")
B("b48",700.6,712.4,"recap","PRESENTER_INSET","Recap window with check-mark cards",
  ["$0 hosting fees","Built for under $10","Prompts in the pinned comment"],
  [("$0 hosting fees",702.58),("Built for under $10",705.34),("Prompts in the pinned comment",711.02)],
  "window-move-in","window-move-out",
  "Recap layout: presenter in a 768x432 rounded window with a thin glowing border, italic caption under it ('A budget-free website, start to finish'); three cards right, rose checks pop on the words.",
  presenter_layout=WINDOW,layout=WINDOW_GFX)
B("b49",712.4,729.367,"cta","CLEAN_PRESENTER","CTA and sign-off, untouched",[],
  rat="The ending is fixed by the creator: no graphics, no zoom, no change.")

d={"version":1,"project":"budget-free-website-startup-guide-clean","theme":"clean-creator",
 "source":{"path":SRC,"sha256":SHA,"width":1280,"height":720,"fps":"30/1","duration_s":DUR},
 "delivery":{"width":1280,"height":720,"fps":"30/1","codec":"h264 yuv420p","audio":"source AAC 48 kHz stereo, stream-copied"},
 "approval":{"status":"approved","approved_scope":"Creator approved director-treatment.md as planned (2026-11-07). Screens framed 1152x648 with glowing border; the baked presenter bubble stays round with a thin raspberry glow around the circle only, no rectangle or box around it. No wordmark.",
   "ambiguities":[]},
 "audio":{"policy":"unchanged; source audio stream-copied","measured_integrated_lufs":-14.1,"measured_true_peak_dbtp":-1.1,"lra_lu":3.5},
 "captions":None,
 "palette":{"ground":"#210A12","orb":["#92205A","#8C3D5D"],"accent":"#92205A","highlight":"#E25C8E","text":"#FAF9F8"},
 "type":{"family":"Montserrat","titles":"800 uppercase, soft warm-white glow","body":"300 sentence case"},
 "screen_framing":{"approved":True,"bubble":"kept round; thin raspberry glow ring on the circle only; no rectangle/box around it","wordmark":None,"intervals":SCREENS,"window":{"x":64,"y":36,"width":1152,"height":648,"radius":22,"border":"1.5px #92205A glow"},
   "ground":"#210A12 with raspberry orb","protected_during_screens":[{"name":"baked-bubble-bottom-left","x":0,"y":440,"width":300,"height":280},{"name":"baked-bubble-bottom-right","x":990,"y":410,"width":290,"height":310}],"note":"The presenter bubble baked into the screen recordings stays inside the frame."},
 "protected_regions":[{"name":"presenter-camera-head-shoulders","x":260,"y":0,"width":700,"height":600}],
 "beats":beats}
json.dump(d,open("editorial-directive.json","w"),indent=1,ensure_ascii=False)

# shares
cam=DUR-sum(b-a for a,b in SCREENS)
tot={}
for b in beats:
    k=b["treatment"]+(" (over screen)" if b.get("screen") else "")
    tot[k]=tot.get(k,0)+b["end"]-b["start"]
cov=sum(b["end"]-b["start"] for b in beats)
tot["CLEAN_PRESENTER"]=tot.get("CLEAN_PRESENTER",0)+DUR-cov
json.dump({"durations":tot,"camera_s":cam,"screen_s":DUR-cam},open("reports/shares.json","w"),indent=1)
for k,v in sorted(tot.items()): print(f"{k:34s} {v:7.1f}s {100*v/DUR:5.1f}%")
print("camera",cam,"screen",DUR-cam)
