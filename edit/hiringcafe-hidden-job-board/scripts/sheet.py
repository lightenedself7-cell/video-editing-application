import sys, glob, cv2, numpy as np
d = sys.argv[1]; out = sys.argv[2]; cols = int(sys.argv[3]); tw = int(sys.argv[4]) if len(sys.argv) > 4 else 480
files = sys.argv[5:] if len(sys.argv) > 5 else sorted(glob.glob(f"{d}/f*.png"))
th = tw * 9 // 16; tiles = []
for f in files:
    im = cv2.resize(cv2.imread(f), (tw, th), interpolation=cv2.INTER_AREA)
    n = int(f.split("/f")[-1][:5]); cv2.putText(im, f"{n/30:.1f}s", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, .55, (0, 255, 255), 2); tiles.append(im)
while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]))
