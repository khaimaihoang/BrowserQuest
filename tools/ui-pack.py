#!/usr/bin/env python3
"""ui-pack.py — BrowserQuest UI slice packer.

Reads a UI slice manifest (tools/ui/slices.json), slices named components out of
the Minifantasy "Grim" 16px atlas, exports them at 1x/2x/3x (NEAREST, integer
scale) into client/img/{1,2,3}/ui/, then generates:

  * client/css/ui-slices.generated.css  (border-image classes, 3 scales, themes,
                                         hover/active/disabled states)
  * client/ui-lab.html                  (dev preview page)
  * tools/ui/out/preview.png            (offline 9-slice assembly self-test)

Why: the atlas is one 4528x1984 sheet with no per-element names. This tool makes
the *slice contract* explicit and reproducible so artists can design once and
have the game consume the assets immediately.

Usage:
    python tools/ui-pack.py                     # write everything
    python tools/ui-pack.py --themes dark       # only the default theme
    python tools/ui-pack.py --no-write          # validate + build in-memory only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required: pip install Pillow")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from uilab_kit import kit_markup, kit_script, kit_style  # noqa: E402  (dev-only UI kit demo)

ROOT = Path(__file__).resolve().parents[1]

# Touch-first state model: `active`/`checked` = selected/on (LIGHTER sprite),
# `pressed` = finger/mouse down, `disabled` = darker/dimmed. `hover` is desktop-only
# and emitted inside @media (hover: hover). Order controls CSS fallbacks.
STATE_ORDER = [
    "active", "disabled", "disabled-pressed", "active-pressed", "pressed",
    "checked", "checked-pressed", "checked-disabled", "hover",
]

STATE_SELECTORS = {
    "hover": ["{c}:hover", "{c}.hover"],
    "pressed": ["{c}:active", "{c}.pressed"],
    "active": ["{c}.active", "{c}[aria-selected='true']", "{c}[aria-pressed='true']"],
    "disabled": ["{c}:disabled", "{c}.disabled", "{c}[aria-disabled='true']"],
    "disabled-pressed": ["{c}:active", "{c}.pressed", "{c}.disabled.pressed",
                          "{c}.disabled:active", "{c}:disabled:active"],
    "active-pressed": ["{c}.active.pressed", "{c}.active:active",
                       "{c}[aria-pressed='true']:active"],
    "checked": ["{c}:checked", "{c}.checked", "{c}[aria-checked='true']"],
    "checked-pressed": ["{c}:checked:active", "{c}.checked.pressed"],
    "checked-disabled": ["{c}:checked:disabled", "{c}.checked.disabled"],
    "disabled": ["{c}:disabled", "{c}.disabled", "{c}[aria-disabled='true']"],
}
# Media-query scale mapping — mirrors client/css/panel.css.
SCALE_MEDIA = {
    3: [("screen and (min-width: 1501px)",)],
    2: [("screen and (max-width: 1500px)",), ("screen and (max-height: 870px)",)],
    1: [("screen and (max-width: 1000px)",), ("screen and (max-width: 800px)",)],
}


# --------------------------------------------------------------------------- #
# image helpers
# --------------------------------------------------------------------------- #
def tile_to(src: Image.Image, tw: int, th: int) -> Image.Image:
    """Tile `src` to (tw, th), cropping overflow — emulates CSS repeat."""
    out = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    sw, sh = src.size
    if sw <= 0 or sh <= 0:
        return out
    for y in range(0, th, sh):
        for x in range(0, tw, sw):
            out.paste(src, (x, y))
    return out




def flatten_middle(crop: Image.Image, sl, axis: str) -> Image.Image:
    """Fill the 9-slice middle band from its own centre line so it tiles with no
    visible seam (bars have a dashed edge that would otherwise repeat).
    axis='y' (vertical bar): replicate the middle ROW across the band.
    axis='x' (horizontal bar): replicate the middle COLUMN across the band."""
    t, r, b, l = sl
    w, h = crop.size
    if w - l - r <= 0 or h - t - b <= 0:
        return crop
    out = crop.copy()
    px = out.load()
    if axis == "y":
        cy = t + (h - t - b) // 2
        row = [px[i, cy] for i in range(w)]
        for j in range(t, h - b):
            for i in range(w):
                px[i, j] = row[i]
    else:
        cx = l + (w - l - r) // 2
        for j in range(t, h - b):
            src = px[cx, j]
            for i in range(l, w - r):
                px[i, j] = src
    return out

def overlay_list(spec: dict) -> list:
    return list(spec.get("overlays") or [])


def clean_overlays(crop: Image.Image, rect, ovs: list) -> Image.Image:
    """Copy of `crop` with every overlay region filled from the pixel just left
    of it (per row). Makes the 9-slice middle uniform so it tiles cleanly; the
    ornament itself is re-drawn on top by a pseudo-element."""
    out = crop.copy()
    px = out.load()
    W, H = out.size
    ox0, oy0, sw, sh = rect[0], rect[1], rect[2], rect[3]
    for ov in ovs:
        ox, oy, ow, oh = ov["rect"]
        rx, ry = ox - ox0, oy - oy0
        if ow >= sw:
            # ornament spans the full width -> bar tiles vertically: fill each
            # column from the pixel just ABOVE the ornament.
            for i in range(ow):
                x = min(max(rx + i, 0), W - 1)
                src = px[x, min(max(ry - 1, 0), H - 1)]
                for j in range(oh):
                    y = ry + j
                    if 0 <= y < H:
                        px[x, y] = src
        else:
            # horizontal bar -> fill each row from the pixel just LEFT.
            for j in range(oh):
                sy = min(max(ry + j, 0), H - 1)
                src = px[min(max(rx - 1, 0), W - 1), sy]
                for i in range(ow):
                    x = rx + i
                    if 0 <= x < W:
                        px[x, sy] = src
    return out


def overlay_pos(anchor: str, w: int, h: int, scale: int, sl) -> str:
    """Absolute children are positioned against the PADDING box (inside the
    border), so shift by the border width to land on the border-box edge/centre."""
    t, r, b, l = sl
    W, H = w * scale, h * scale
    dx = (l - r) * scale // 2          # padding-centre vs border-centre
    dy = (t - b) * scale // 2
    if anchor == "tc":
        return f"left:50%;top:{-t * scale}px;margin-left:{dx - W // 2}px;"
    if anchor == "bc":
        return f"left:50%;bottom:{-b * scale}px;margin-left:{dx - W // 2}px;"
    if anchor == "lc":
        return f"left:{-l * scale}px;top:50%;margin-top:{dy - H // 2}px;"
    if anchor == "rc":
        return f"right:{-r * scale}px;top:50%;margin-top:{dy - H // 2}px;"
    return f"left:50%;top:50%;margin:{dy - H // 2}px 0 0 {dx - W // 2}px;"

def parse_slice(spec: dict) -> tuple[int, int, int, int]:
    """Slice width as (top, right, bottom, left). Accepts an int or a 1-4 list."""
    s = spec.get("slice", 0)
    if isinstance(s, (list, tuple)):
        vals = [int(v) for v in s][:4]
        vals += [0] * (4 - len(vals))
        return tuple(vals)  # type: ignore[return-value]
    v = int(s)
    return (v, v, v, v)


def compose9(im: Image.Image, rect, sl, ow: int, oh: int) -> Image.Image:
    """Assemble a 9-slice from a sprite — the same result CSS border-image
    produces with `repeat` edges. `sl` = (top, right, bottom, left)."""
    x, y, w, h = rect
    t, r, b, l = sl
    ow, oh = max(ow, l + r), max(oh, t + b)
    out = Image.new("RGBA", (ow, oh), (0, 0, 0, 0))
    if not (t or r or b or l):
        out.paste(im.crop((x, y, x + w, y + h)), (0, 0))
        return out
    # corners
    out.paste(im.crop((x, y, x + l, y + t)), (0, 0))
    out.paste(im.crop((x + w - r, y, x + w, y + t)), (ow - r, 0))
    out.paste(im.crop((x, y + h - b, x + l, y + h)), (0, oh - b))
    out.paste(im.crop((x + w - r, y + h - b, x + w, y + h)), (ow - r, oh - b))
    # edges
    out.paste(tile_to(im.crop((x + l, y, x + w - r, y + t)), ow - l - r, t), (l, 0))
    out.paste(tile_to(im.crop((x + l, y + h - b, x + w - r, y + h)), ow - l - r, b), (l, oh - b))
    out.paste(tile_to(im.crop((x, y + t, x + l, y + h - b)), l, oh - t - b), (0, t))
    out.paste(tile_to(im.crop((x + w - r, y + t, x + w, y + h - b)), r, oh - t - b), (ow - r, t))
    # center
    out.paste(tile_to(im.crop((x + l, y + t, x + w - r, y + h - b)), ow - l - r, oh - t - b), (l, t))
    return out


def nearest_scale(im: Image.Image, n: int) -> Image.Image:
    return im.resize((im.width * n, im.height * n), Image.NEAREST)


# --------------------------------------------------------------------------- #
# manifest
# --------------------------------------------------------------------------- #
def load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if "source" not in data or "slices" not in data:
        raise ValueError("manifest must define 'source' and 'slices'")
    data.setdefault("grid", 16)
    data.setdefault("scales", [1, 2, 3])
    data.setdefault("themes", {"default": "dark", "offsets": {"dark": 0}})
    data.setdefault("css", {"prefix": "ui", "pixelated": True})
    return data


def iter_slices(mf: dict):
    """Manifest slices, skipping `_comment_*` / other underscore keys."""
    return [(k, v) for k, v in mf["slices"].items() if not k.startswith("_")]


def asset_filename(name: str, state: str, theme: str, default_theme: str) -> str:
    parts = [name]
    if state:
        parts.append(state)
    if theme != default_theme:
        parts.append(theme)
    return "--".join(parts) + ".png"


def slice_themes(spec: dict, themes: list[str], default_theme: str) -> list[str]:
    """Slices may opt out of theming (e.g. coloured resource fills)."""
    return themes if spec.get("themed", True) else [default_theme]


def ordered_states(spec: dict) -> list[str]:
    states = spec.get("states") or {}
    known = [s for s in STATE_ORDER if s in states]
    extra = [s for s in states if s not in STATE_ORDER]
    return known + extra


def variants(spec: dict, default_theme: bool = True):
    """Yield (state, rect); state '' is the base variant."""
    yield "", spec["rect"]
    for state in ordered_states(spec):
        yield state, spec["states"][state]


def state_selectors(cls: str, state: str) -> list[str]:
    tpl = STATE_SELECTORS.get(state)
    if tpl is None:
        tpl = [f"{{c}}:{state}", f"{{c}}.{state}"]
    return [t.format(c=cls) for t in tpl]


def validate(mf: dict, sheet_size) -> list[str]:
    """Return a list of human-readable validation problems (empty = OK)."""
    problems: list[str] = []
    offsets = mf["themes"]["offsets"]
    sw, sh = sheet_size
    for name, spec in iter_slices(mf):
        nine = spec.get("nine", True)
        t, r, b, l = parse_slice(spec)
        for state, rect in variants(spec):
            if len(rect) != 4:
                problems.append(f"{name}[{state or 'base'}]: rect must be [x,y,w,h]")
                continue
            x, y, w, h = rect
            dt = mf["themes"]["default"]
            check = offsets.items() if spec.get("themed", True) else [(dt, offsets[dt])]
            for theme, off in check:
                if x + off < 0 or x + off + w > sw or y < 0 or y + h > sh:
                    problems.append(f"{name}[{state or 'base'}][{theme}]: rect out of bounds")
            if nine and state == "":
                if max(t, r, b, l) <= 0:
                    problems.append(f"{name}: nine-slice needs a slice > 0")
                elif t + b >= h or l + r >= w:
                    problems.append(
                        f"{name}: slice ({t},{r},{b},{l}) too large for {w}x{h}")
    return problems


def source_decl(rel: str, indent: str) -> str:
    return f"{indent}border-image-source: url('{rel}');"


def url_for(rel: str) -> str:
    return "../" + rel.replace("client/", "", 1)


def write_images(mf: dict, im: Image.Image, themes: list[str], write: bool) -> dict:
    """Slice + upscale + export. Returns assets[theme][name][state][scale] = rel."""
    offsets = mf["themes"]["offsets"]
    default_theme = mf["themes"]["default"]
    scales = mf["scales"]
    out_tpl = mf["output"]["image"]
    result: dict = {}

    for theme in themes:
        off = offsets[theme]
        result[theme] = {}
        for name, spec in iter_slices(mf):
            if theme not in slice_themes(spec, themes, default_theme):
                continue
            result[theme][name] = {}
            for state, rect in variants(spec):
                x, y, w, h = rect
                crop = im.crop((x + off, y, x + off + w, y + h))
                fname = asset_filename(name, state, theme, default_theme)
                result[theme][name][state] = {}
                for scale in scales:
                    rel = out_tpl.format(scale=scale) + "/" + fname
                    result[theme][name][state][scale] = rel
                    if write:
                        dest = ROOT / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        nearest_scale(crop, scale).save(dest)
            # 9-slice with an anchored centre ornament: export a cleaned base
            # (ornament removed) + the ornament itself as `--ovN` sprites.
            ovs = overlay_list(spec)
            if ovs:
                rect = spec["rect"]
                x, y, w, h = rect
                src_base = im.crop((x + off, y, x + off + w, y + h))
                cleaned = clean_overlays(src_base, rect, ovs)
                if spec.get("flatten", False):
                    cleaned = flatten_middle(cleaned, parse_slice(spec), spec.get("stretch", "x"))
                result[theme][name]["@base"] = {}
                for scale in scales:
                    rel = out_tpl.format(scale=scale) + "/" + asset_filename(
                        name + "--base", "", theme, default_theme)
                    result[theme][name]["@base"][scale] = rel
                    if write:
                        dest = ROOT / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        nearest_scale(cleaned, scale).save(dest)
                for i, ov in enumerate(ovs, 1):
                    ox, oy, ow, oh = ov["rect"]
                    ocrop = im.crop((ox + off, oy, ox + off + ow, oy + oh))
                    key = f"@ov{i}"
                    result[theme][name][key] = {}
                    for scale in scales:
                        rel = out_tpl.format(scale=scale) + "/" + asset_filename(
                            f"{name}--ov{i}", "", theme, default_theme)
                        result[theme][name][key][scale] = rel
                        if write:
                            dest = ROOT / rel
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            nearest_scale(ocrop, scale).save(dest)
    return result


def collect_rels(assets: dict) -> set[str]:
    """Every output path referenced by the current manifest."""
    return {
        assets[t][n][s][sc]
        for t in assets
        for n in assets[t]
        for s in assets[t][n]
        for sc in assets[t][n][s]
    }


def clean_stale(index_path: Path, new_rels: set[str]) -> list[str]:
    """Delete files generated by a previous run that are no longer produced."""
    if not index_path.exists():
        return []
    old = set(json.loads(index_path.read_text(encoding="utf-8")))
    removed = []
    for rel in sorted(old - new_rels):
        path = ROOT / rel
        if path.exists():
            path.unlink()
            removed.append(rel)
    return removed


def pixelated_decls(indent: str = "  ") -> str:
    return (
        f"{indent}image-rendering: -moz-crisp-edges;\n"
        f"{indent}image-rendering: -webkit-optimize-contrast;\n"
        f"{indent}image-rendering: pixelated;"
    )


def css_for_scale(mf: dict, assets: dict, scale: int, themes: list[str]) -> str:
    prefix = mf["css"]["prefix"]
    default_theme = mf["themes"]["default"]
    out: list[str] = []
    hover: list[str] = []

    for name, spec in iter_slices(mf):
        cls = f".{prefix}-{name}"
        nine = spec.get("nine", True)
        t, r, b, l = (v * scale for v in parse_slice(spec))
        prop = "border-image-source" if nine else "background-image"

        ovs = overlay_list(spec)
        # 1. base rule (cleaned image when an anchored ornament is present)
        base_key = "@base" if (ovs and "@base" in assets[default_theme][name]) else ""
        base_rel = url_for(assets[default_theme][name][base_key][scale])
        out.append(f"{cls} {{")
        if ovs:
            out.append("  position: relative;")
        if nine:
            out.append("  box-sizing: border-box;")
            out.append(f"  border-width: {t}px {r}px {b}px {l}px;")
            out.append("  border-style: solid;")
            out.append("  border-color: transparent;")
            out.append(f"  border-image: url('{base_rel}') {t} {r} {b} {l} fill "
                       f"{spec.get('repeat', 'repeat')};")
        else:
            rep = spec.get("repeat", "no-repeat")
            out.append("  display: inline-block;")
            out.append(f"  background-image: url('{base_rel}');")
            out.append(f"  background-repeat: {rep};")
            if rep.startswith("repeat-x"):
                out.append("  background-position: left center;")
                out.append("  background-size: auto 100%;")
            elif rep.startswith("repeat-y"):
                out.append("  background-position: center top;")
                out.append("  background-size: 100% auto;")
            else:
                out.append("  background-position: center;")
                out.append("  background-size: contain;")
        out.append(pixelated_decls())
        out.append("}")

        # 2. theme base overrides
        for theme in slice_themes(spec, themes, default_theme):
            if theme == default_theme:
                continue
            tkey = "@base" if (ovs and "@base" in assets[theme][name]) else ""
            turl = url_for(assets[theme][name][tkey][scale])
            out.append(f".theme-{theme} {cls} {{ {prop}: url('{turl}'); }}")

        # 3+4. state + theme-state overrides (hover is deferred to a media block)
        for state in ordered_states(spec):
            target = hover if state == "hover" else out
            srel = url_for(assets[default_theme][name][state][scale])
            sel = ", ".join(state_selectors(cls, state))
            target.append(f"{sel} {{ {prop}: url('{srel}'); }}")
            for theme in slice_themes(spec, themes, default_theme):
                if theme == default_theme:
                    continue
                turl = url_for(assets[theme][name][state][scale])
                tsel = ", ".join(f".theme-{theme} {x}" for x in state_selectors(cls, state))
                target.append(f"{tsel} {{ {prop}: url('{turl}'); }}")

        # 4b. aliases: expose an existing state sprite under extra selectors
        for alias_state, target in (spec.get("alias") or {}).items():
            if target not in (spec.get("states") or {}):
                continue
            arel = url_for(assets[default_theme][name][target][scale])
            sel = ", ".join(state_selectors(cls, alias_state))
            out.append(f"{sel} {{ {prop}: url('{arel}'); }}")
            for theme in slice_themes(spec, themes, default_theme):
                if theme == default_theme:
                    continue
                turl = url_for(assets[theme][name][target][scale])
                tsel = ", ".join(f".theme-{theme} {x}"
                                 for x in state_selectors(cls, alias_state))
                out.append(f"{tsel} {{ {prop}: url('{turl}'); }}")

        # 5. optional desktop hover reusing an existing state sprite (no extra file)
        hover_ref = spec.get("hoverUses")
        if hover_ref and hover_ref in (spec.get("states") or {}):
            hrel = url_for(assets[default_theme][name][hover_ref][scale])
            hover.append(f"{cls}:hover, {cls}.hover {{ {prop}: url('{hrel}'); }}")
            for theme in slice_themes(spec, themes, default_theme):
                if theme == default_theme:
                    continue
                turl = url_for(assets[theme][name][hover_ref][scale])
                hover.append(f".theme-{theme} {cls}:hover, .theme-{theme} {cls}.hover "
                             f"{{ {prop}: url('{turl}'); }}")

        # 4c. anchored centre ornaments as pseudo-elements (never tiled)
        for i, ov in enumerate(ovs):
            pseudo = "::before" if i == 0 else "::after"
            ow, oh = ov["rect"][2], ov["rect"][3]
            pos = overlay_pos(ov.get("anchor", "center"), ow, oh, scale, parse_slice(spec))
            rel = url_for(assets[default_theme][name][f"@ov{i + 1}"][scale])
            out.append(
                f"{cls}{pseudo} {{ content:''; position:absolute; {pos} "
                f"width:{ow * scale}px; height:{oh * scale}px; "
                f"background:url('{rel}') no-repeat; image-rendering:pixelated; "
                f"pointer-events:none; }}")
            for theme in slice_themes(spec, themes, default_theme):
                if theme == default_theme:
                    continue
                turl = url_for(assets[theme][name][f"@ov{i + 1}"][scale])
                out.append(f".theme-{theme} {cls}{pseudo} {{ background-image: url('{turl}'); }}")

    if hover:
        out.append("@media (hover: hover) {")
        out.extend("  " + line for line in hover)
        out.append("}")
    return "\n".join(out) + "\n"


def generate_css(mf: dict, assets: dict, themes: list[str]) -> str:
    header = (
        "/* AUTO-GENERATED by tools/ui-pack.py — DO NOT EDIT.\n"
        "   Manifest: tools/ui/slices.json\n"
        "   Regenerate: npm run ui:pack */\n\n"
    )
    parts = [header, css_for_scale(mf, assets, 1, themes)]
    for scale in (2, 3):
        for (media,) in SCALE_MEDIA[scale]:
            parts.append(f"@media {media} {{\n")
            for line in css_for_scale(mf, assets, scale, themes).splitlines():
                parts.append(("  " + line) if line else line)
            parts.append("}\n")
    for (media,) in SCALE_MEDIA[1]:
        parts.append(f"@media {media} {{\n")
        for line in css_for_scale(mf, assets, 1, themes).splitlines():
            parts.append(("  " + line) if line else line)
        parts.append("}\n")
    return "\n".join(parts)


def demo_sizes(spec: dict) -> list[tuple[int, int]]:
    """Preview sizes anchored on the sprite's NATIVE size, then stretched ×2/×3 and
    a LONG case (360px+ along the long axis) to reveal tiling seams.
    Native first so the real sprite is visible; bars stretch only along their long axis."""
    w, h = spec["rect"][2], spec["rect"][3]
    st = spec.get("stretch")
    if st == "x":                 # horizontal-only stretch
        return [(w, h), (w * 2, h), (w * 3, h), (max(360, w * 6), h)]
    if st == "y":                 # vertical-only stretch
        return [(w, h), (w, h * 2), (w, h * 3), (w, max(360, h * 6))]
    stretchable = spec.get("nine", True) or spec.get("repeat", "no-repeat").startswith("repeat")
    if w / h >= 2:                 # horizontal bar / edge
        sizes = [(w, h), (w * 2, h), (w * 3, h)]
        if stretchable:
            sizes.append((max(360, w * 6), h))
        return sizes
    if h / w >= 2:                 # vertical bar / edge
        sizes = [(w, h), (w, h * 2), (w, h * 3)]
        if stretchable:
            sizes.append((w, max(360, h * 6)))
        return sizes
    sizes = [(w, h), (w * 2, h * 2), (w * 3, h * 3)]
    if spec.get("nine", True):
        sizes += [(w * 5, h * 2), (w * 2, h * 5)]   # wide + tall
    return sizes


def generate_lab(mf: dict, themes: list[str]) -> str:
    prefix = mf["css"]["prefix"]
    default_theme = mf["themes"]["default"]
    rows = []
    for name, spec in iter_slices(mf):
        nine = spec.get("nine", True)
        cls = f"{prefix}-{name}"
        sizes_l = demo_sizes(spec)
        demos = []
        for i, (dw, dh) in enumerate(sizes_l):
            flag = "" if i else " base"
            demos.append(f'<i class="{cls}{flag}" style="width:calc({dw}px * var(--s));'
                         f'height:calc({dh}px * var(--s))"></i>')
        size = sizes_l[1]
        for state in ordered_states(spec):
            state_classes = state.replace("-", " ")
            demos.append(
                f'<i class="{cls} {state_classes}" '
                f'style="width:calc({size[0]}px * var(--s));height:calc({size[1]}px * var(--s))" '
                f'title="{state}"></i>'
            )
        sl = spec.get("slice", 0)
        sl = str(sl) if not isinstance(sl, list) else ",".join(map(str, sl))
        rows.append(
            f'<section class="row"><header>{name} '
            f'<em>{"9-slice " + sl if nine else "sprite"}'
            f'{" · +" + "/".join(ordered_states(spec)) if spec.get("states") else ""}</em></header>'
            f'<div class="demos">{"".join(demos)}</div></section>'
        )

    theme_buttons = "".join(f'<button data-theme="{t}">{t}</button>' for t in themes)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BrowserQuest UI Lab — {mf["name"]}</title>
<link rel="stylesheet" href="css/ui-slices.generated.css">
<style>
  :root {{ color-scheme: dark; --s: 1; }}
  /* --s mirrors the generated CSS scale so demos are not cropped at 2x/3x */
  @media screen and (max-width: 1500px) {{ :root {{ --s: 2; }} }}
  @media screen and (max-height: 870px) {{ :root {{ --s: 2; }} }}
  @media screen and (min-width: 1501px) {{ :root {{ --s: 3; }} }}
  @media screen and (max-width: 1000px) {{ :root {{ --s: 1; }} }}
  @media screen and (max-width: 800px) {{ :root {{ --s: 1; }} }}
  body {{ margin: 0; padding: 16px; background: #1c1c22; color: #dfe3ea;
         font: 13px/1.4 system-ui, sans-serif; }}
  h1 {{ font-size: 18px; margin: 0 0 4px; }}
  .hint {{ color: #9aa3b2; margin-bottom: 12px; }}
  .toolbar {{ position: sticky; top: 0; z-index: 5; display: flex; gap: 8px;
             flex-wrap: wrap; padding: 8px 0; background: #1c1c22; }}
  .toolbar button {{ padding: 4px 10px; }}
  #stage {{ display: flex; flex-direction: column; gap: 10px; }}
  #stage.checker {{ background-color: #26262e;
      background-image: linear-gradient(45deg, #333 25%, transparent 25%),
        linear-gradient(-45deg, #333 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, #333 75%),
        linear-gradient(-45deg, transparent 75%, #333 75%);
      background-size: 16px 16px;
      background-position: 0 0, 0 8px, 8px -8px, -8px 0; }}
  .row {{ display: flex; align-items: center; gap: 16px; padding: 8px;
         border-bottom: 1px solid #2e2e38; }}
  .row header {{ width: 220px; flex: none; }}
  .row em {{ color: #8b93a3; font-style: normal; font-size: 11px; display: block; }}
  .demos {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
  .demos i {{ display: block; }}
  .demo-panel {{ width: 240px; height: 120px; }}
  .demo-icon {{ width: 20px; height: 20px; }}
</style>
{kit_style()}
</head>
<body class="theme-{default_theme}">
<h1>BrowserQuest UI Lab</h1>
<div class="hint">
  Auto-generated from <code>tools/ui/slices.json</code>. Resize the window to
  exercise 1x / 2x / 3x. State samples use <code>.hover/.active/.disabled</code>
  (and <code>:hover/:active/:disabled</code> in real use). Toggle checkerboard.
</div>
<div class="toolbar">
  <button id="checkerBtn">Toggle checkerboard</button>
  {theme_buttons}
</div>
<div id="stage">
{"".join(rows)}
</div>
{kit_markup(prefix)}
<script>
  const stage = document.getElementById('stage');
  document.getElementById('checkerBtn').onclick = () => stage.classList.toggle('checker');
  document.querySelectorAll('[data-theme]').forEach(b => b.onclick = () => {{
    document.body.className = b.dataset.theme === '{default_theme}' ? '' : 'theme-' + b.dataset.theme;
  }});
{kit_script()}
</script>
</body>
</html>
"""


def generate_preview(mf: dict, im: Image.Image, default_theme: str) -> Image.Image:
    """Offline self-test: base 9-slice at 3 sizes plus every state, dark theme.
    Preview sizes respect each sprite's aspect so bars stay bars."""
    pad, label_h = 12, 16
    offsets = mf["themes"]["offsets"]
    off = offsets[default_theme]
    rows = []
    for name, spec in iter_slices(mf):
        nine = spec.get("nine", True)
        w0, h0 = spec["rect"][2], spec["rect"][3]
        dims = [(w0, h0)] if not nine else demo_sizes(spec)
        state_dim = dims[min(1, len(dims) - 1)]
        tiles = [("", d) for d in dims] + [(st, state_dim) for st in ordered_states(spec)]
        rows.append((name, spec, nine, tiles))

    def row_h(tiles):
        return label_h + 4 + max(dh for _, (_, dh) in tiles) + 10

    W = max(1280, max(pad + sum(dw + pad for _, (dw, _) in t) for _, _, _, t in rows))
    H = sum(row_h(t) for _, _, _, t in rows) + 40
    sheet = Image.new("RGB", (W, H), (38, 38, 46))
    d = ImageDraw.Draw(sheet)
    d.text((8, 8), f"{mf['name']} — 9-slice/state self-test ({default_theme})", fill=(240, 240, 240))
    y = 40
    for name, spec, nine, tiles in rows:
        d.text((8, y), name, fill=(200, 200, 120))
        cx = pad
        sl = parse_slice(spec)
        for state, (dw, dh) in tiles:
            rect = spec["rect"] if not state else spec["states"][state]
            x, yy, rw, rh = rect
            rect_t = (x + off, yy, rw, rh)
            d.text((cx, y + 12), f"{state or 'base'} {dw}x{dh}", fill=(150, 150, 160))
            if nine:
                demo = compose9(im, rect_t, sl, dw, dh)
            else:
                demo = im.crop((rect_t[0], rect_t[1], rect_t[0] + rw, rect_t[1] + rh))
            sheet.paste(demo, (cx, y + label_h + 4), demo)
            cx += demo.width + pad
        y += row_h(tiles)
    return sheet


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="BrowserQuest UI slice packer")
    ap.add_argument("--manifest", default=str(ROOT / "tools" / "ui" / "slices.json"))
    ap.add_argument("--themes", nargs="*", default=None,
                    help="themes to export (default: all)")
    ap.add_argument("--no-write", action="store_true", help="validate only, no files")
    args = ap.parse_args()

    mf = load_manifest(Path(args.manifest))
    src = ROOT / mf["source"]
    if not src.exists():
        sys.exit(f"atlas not found: {src}")

    im = Image.open(src).convert("RGBA")
    all_themes = list(mf["themes"]["offsets"].keys())
    themes = all_themes if not args.themes else args.themes
    for t in themes:
        if t not in mf["themes"]["offsets"]:
            sys.exit(f"unknown theme '{t}' (have: {all_themes})")

    problems = validate(mf, im.size)
    n_states = sum(len(spec.get("states") or {}) for _, spec in iter_slices(mf))
    print(f"atlas: {src.relative_to(ROOT)}  {im.width}x{im.height}")
    print(f"themes: {themes}  scales: {mf['scales']}  "
          f"slices: {len(iter_slices(mf))} (+{n_states} states)")
    if problems:
        print("VALIDATION FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print("validation: OK")

    assets = write_images(mf, im, themes, write=not args.no_write)

    if not args.no_write:
        css = generate_css(mf, assets, themes)
        css_path = ROOT / mf["output"]["css"]
        css_path.parent.mkdir(parents=True, exist_ok=True)
        css_path.write_text(css, encoding="utf-8")
        print(f"wrote {css_path.relative_to(ROOT)}  ({len(css.splitlines())} lines)")

        lab_path = ROOT / mf["output"]["lab"]
        lab_path.write_text(generate_lab(mf, themes), encoding="utf-8")
        print(f"wrote {lab_path.relative_to(ROOT)}")

        # refresh the interactive slice editor (embeds the current manifest)
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "make_slice_editor", ROOT / "tools" / "make-slice-editor.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            ed = ROOT / "client" / "ui-slice-editor.html"
            html = mod.generate(mf)
            ed.write_text(html, encoding="utf-8")
            print(f"wrote {ed.relative_to(ROOT)}")
            # also drop it in dist/client (webpack-dev-server serves that dir first)
            dist = ROOT / "dist" / "client"
            if dist.is_dir():
                (dist / "ui-slice-editor.html").write_text(html, encoding="utf-8")
                print("wrote dist/client/ui-slice-editor.html")
        except Exception as exc:  # non-fatal
            print(f"slice editor skipped: {exc}")

        preview = generate_preview(mf, im, mf["themes"]["default"])
        prev_path = ROOT / mf["output"]["preview"]
        prev_path.parent.mkdir(parents=True, exist_ok=True)
        preview.save(prev_path)
        print(f"wrote {prev_path.relative_to(ROOT)}")

        index_path = ROOT / "tools" / "ui" / "out" / "generated.json"
        new_rels = collect_rels(assets)
        removed = clean_stale(index_path, new_rels)
        if removed:
            print(f"removed {len(removed)} stale file(s)")
        index_path.write_text(json.dumps(sorted(new_rels), indent=0), encoding="utf-8")

        generated = ROOT / assets[mf["themes"]["default"]]["panel"][""][1]
        legacy = ROOT / "client/img/1/ui/panel.png"
        if generated.exists() and legacy.exists():
            same = generated.read_bytes() == legacy.read_bytes()
            print(f"panel 1x vs legacy panel.png: {'MATCH' if same else 'DIFFERS'}")

    print(f"done: {len(collect_rels(assets))} images "
          f"({len(iter_slices(mf))} slices + {n_states} states, {len(themes)} themes, "
          f"{len(mf['scales'])} scales)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
