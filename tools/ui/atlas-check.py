#!/usr/bin/env python3
"""Reconstruct the dark-theme (3-set) atlas from the EXPORTED kit sprites and
compare component-by-component with the source atlas.

For every atlas component it reports:
  full  = fully covered by an exported rect
  CUT   = partially covered  (rect too small / wrong -> a real bug)
  unused= not covered by any rect (atlas art the manifest doesn't export)

Usage: python tools/ui/atlas-check.py
Also writes tools/ui/out/atlas-check.png  (dim = covered, magenta = unused).
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
mf = json.loads((ROOT / "tools/ui/slices.json").read_text(encoding="utf-8"))
OFF, DEFAULT, SETS = mf["sets"]["offsets"], mf["sets"]["default"], ["set1", "set2", "set3"]
atlas = Image.open(ROOT / mf["sheets"]["main"]["source"]).convert("RGBA")
W, H = atlas.size
mask = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(mask)


def rf(spec, s, rect):
    if s == DEFAULT:
        return list(rect)
    ov = (spec.get("setRect") or {}).get(s)
    if ov:
        b = spec["rect"]
        return [rect[0] + ov[0] - b[0], rect[1] + ov[1] - b[1],
                rect[2] + ov[2] - b[2], rect[3] + ov[3] - b[3]]
    return [rect[0], rect[1] + OFF[s] + (spec.get("setDelta") or {}).get(s, 0), rect[2], rect[3]]


for name, spec in mf["slices"].items():
    if name.startswith("_") or not isinstance(spec, dict) or spec.get("sheet", "main") != "main":
        continue
    for s in ([DEFAULT] if (spec.get("sets") is False or spec.get("themed") is False) else SETS):
        for st, r0 in [("", spec["rect"])] + list((spec.get("states") or {}).items()):
            ov = ((spec.get("stateSetRect") or {}).get(st) or {}).get(s) if st else None
            x, y, w, h = list(ov) if ov else rf(spec, s, r0)
            d.rectangle([x, y, x + w - 1, y + h - 1], fill=255)

pa, pm = atlas.load(), mask.load()
seen, cut, unused, full = set(), [], [], 0
for y in range(H):
    for x in range(912):                       # dark = x 0..911
        if (x, y) in seen or pa[x, y][3] == 0:
            continue
        st = [(x, y)]; seen.add((x, y)); X0 = X1 = x; Y0 = Y1 = y; n = cov = 0
        while st:
            cx, cy = st.pop(); n += 1
            if pm[cx, cy]:
                cov += 1
            X0, X1 = min(X0, cx), max(X1, cx); Y0, Y1 = min(Y0, cy), max(Y1, cy)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < 912 and 0 <= ny < H and (nx, ny) not in seen and pa[nx, ny][3] > 0:
                        seen.add((nx, ny)); st.append((nx, ny))
        if n < 8:
            continue
        if cov == 0:
            unused.append((X0, Y0, X1 - X0 + 1, Y1 - Y0 + 1))
        elif cov < n:
            cut.append((X0, Y0, X1 - X0 + 1, Y1 - Y0 + 1, cov, n))
        else:
            full += 1

print(f"full={full}  CUT={len(cut)}  unused={len(unused)}")
for b in sorted(cut, key=lambda z: -(z[5] - z[4])):
    print("  CUT x=%d y=%d %dx%d  covered %d/%d" % b)
vis = atlas.crop((0, 0, 912, H)).copy(); pv = vis.load()
for y in range(H):
    for x in range(912):
        if pa[x, y][3] == 0:
            continue
        if pm[x, y]:
            r, g, b, a = pv[x, y]; pv[x, y] = (r // 3, g // 3, b // 3, 255)
        else:
            pv[x, y] = (255, 0, 255, 255)
vis.save(ROOT / "tools/ui/out/atlas-check.png")
print("wrote tools/ui/out/atlas-check.png")
