#!/usr/bin/env python3
"""Fast UI QA sheet (1 headless screenshot) — for verifying 9-slice + overlay.

Renders every requested slice in ALL exported sets, at its NATIVE size and at a
STRETCHED size, into a single PNG. One image shows everything, so a fix can be
validated in one round-trip instead of many ad-hoc probes.

Usage:
    python tools/ui/qa.py                       # default: panel-ish slices
    python tools/ui/qa.py panel panel-slim bar-h toggle-h
    python tools/ui/qa.py --all

Output: tools/ui/out/qa.png
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MF = json.loads((ROOT / "tools/ui/slices.json").read_text(encoding="utf-8"))
PREFIX = MF["css"]["prefix"]
DEFAULT_SET = MF["sets"]["default"]
SETS = list(MF["sets"]["offsets"])
OFF = MF["sets"]["offsets"]

CHROME = next((p for p in (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    shutil.which("chrome"), shutil.which("google-chrome"), shutil.which("chromium"),
) if p and Path(p).exists()), None)

DEFAULT_SLICES = ["panel", "panel-slim", "panel-textured", "panel-header", "panel-title",
                  "button", "bar-h", "bar-v", "divider-h", "slot-md", "toggle-h"]


def rect_for(spec: dict, set_name: str, rect: list) -> list:
    """Same rule as the packer: apply the set's delta to ANY rect (base or state)."""
    if set_name == DEFAULT_SET:
        return list(rect)
    ov = (spec.get("setRect") or {}).get(set_name)
    if ov:
        b = spec["rect"]
        return [rect[0] + ov[0] - b[0], rect[1] + ov[1] - b[1],
                rect[2] + ov[2] - b[2], rect[3] + ov[3] - b[3]]
    dy = OFF[set_name] + (spec.get("setDelta") or {}).get(set_name, 0)
    return [rect[0], rect[1] + dy, rect[2], rect[3]]


def stretch_size(spec: dict, w: int, h: int) -> tuple[int, int]:
    st = spec.get("stretch")
    if st == "x":
        return (max(w * 2, w + 48), h)
    if st == "y":
        return (w, max(h * 2, h + 48))
    if spec.get("nine", True):
        return (w + 64, h + 48)
    return (w, h)


def build_html(names: list[str]) -> str:
    rows = []
    for name in names:
        spec = MF["slices"].get(name)
        if not isinstance(spec, dict) or spec.get("sheet", "main") != "main":
            continue
        cells = []
        for s in SETS:
            if spec.get("sets") is False or spec.get("themed") is False:
                if s != DEFAULT_SET:
                    continue
            sc = "" if s == DEFAULT_SET else " " + s
            for st, r0 in [("", spec["rect"])] + list((spec.get("states") or {}).items()):
                ov = (((spec.get("stateSetRect") or {}).get(st) or {}).get(s)
                      if st else None)
                x, y, w, h = (list(ov) if ov else rect_for(spec, s, r0))
                sw, sh = stretch_size(spec, w, h)
                cls = f"{PREFIX}-{name} {st.replace('-', ' ')}".strip()
                cells.append(
                    f'<span class="cell{sc}" title="{s}/{st or "base"}">'
                    f'<i class="{cls}" style="width:{w}px;height:{h}px"></i></span>'
                    f'<span class="cell{sc}"><i class="{cls}" '
                    f'style="width:{sw}px;height:{sh}px"></i></span>'
                )
        rows.append(f'<div class="row"><b>{name}</b>{"".join(cells)}</div>')
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="../../../client/css/ui-slices.generated.css">
<style>
 body{{background:#1c1c22;margin:0;padding:6px;font:11px monospace;color:#cde}}
 .row{{display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid #2b2b38}}
 .row>b{{width:120px;flex:none}}
 .cell{{display:inline-flex;align-items:center;justify-content:center;min-width:24px;
        min-height:20px;padding:3px;border:1px solid #33334a}}
 i{{display:block}}
</style></head><body>
{"".join(rows)}
</body></html>"""


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    names = ([k for k, v in MF["slices"].items()
              if not k.startswith("_") and isinstance(v, dict) and v.get("sheet", "main") == "main"]
             if "--all" in argv else (args or DEFAULT_SLICES))
    out_html = ROOT / "tools/ui/out/qa.html"
    out_png = ROOT / "tools/ui/out/qa.png"
    out_html.write_text(build_html(names), encoding="utf-8")
    if not CHROME:
        print("chrome not found — wrote", out_html)
        return 1
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--window-size=1700,1000",
                    f"--screenshot={out_png}", out_html.as_uri()], check=False)
    print("wrote", out_png.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
