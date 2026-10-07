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
import hashlib
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

# Touch-first state model: `pressed` = finger/mouse down, `disabled` = LOCKED (dark sprite,
# sprite không đổi dù có nhấn — "khoá cứng", xem `pointer-events:none` bên dưới),
# `active`/`checked` = selected/on (LIGHTER sprite). `hover` is desktop-only.
# Thứ tự emit = thứ tự cascade: state sau ghi đè state trước khi specificity bằng nhau
# ⇒ `disabled`/`checked-disabled` để CUỐI để mọi tổ hợp nhấn đều giữ sprite tối.
STATE_ORDER = [
    "active", "active-pressed", "pressed",
    "checked", "checked-pressed",
    "disabled", "checked-disabled",
    "hover",
]

# Element đang disabled là "khoá cứng": loại hẳn khỏi mọi selector nhấn
# (kể cả khi JS tự thêm .pressed) — nhờ vậy sprite không bao giờ đổi khi bị khoá.
NOT_DISABLED = (":not(:disabled):not([disabled])"
                ":not(.disabled):not([aria-disabled='true'])")

STATE_SELECTORS = {
    "hover": ["{c}:hover", "{c}.hover"],
    "pressed": [f"{{c}}{NOT_DISABLED}:active", f"{{c}}{NOT_DISABLED}.pressed"],
    "active": ["{c}.active", "{c}[aria-selected='true']", "{c}[aria-pressed='true']"],
    "disabled": ["{c}:disabled", "{c}.disabled", "{c}[aria-disabled='true']"],
    # chỉ các tổ hợp disabled + nhấn (không có :active/.pressed trần — nút enabled nhấn dùng
    # state `pressed` = sprite sáng-nhấn, xem STATE_ORDER)
    # `[disabled]` = DOM attribute trên div giả lập (game dùng attribute + MutationObserver,
    # xem .agents/skills/game_state_testing) — phải khớp cùng :disabled/.disabled/[aria-disabled].
    # KHÔNG còn state `disabled-pressed`: nút disabled là khoá cứng (sprite không đổi khi nhấn).
    "active-pressed": [f"{{c}}{NOT_DISABLED}.active.pressed",
                       f"{{c}}{NOT_DISABLED}.active:active",
                       f"{{c}}{NOT_DISABLED}[aria-pressed='true']:active"],
    "checked": ["{c}:checked", "{c}.checked", "{c}[aria-checked='true']"],
    "checked-pressed": [f"{{c}}{NOT_DISABLED}:checked:active",
                        f"{{c}}{NOT_DISABLED}.checked.pressed"],
    "checked-disabled": ["{c}:checked:disabled", "{c}.checked.disabled", "{c}.checked[disabled]",
                         "{c}[aria-checked='true'][disabled]", "{c}.checked[aria-disabled='true']",
                         "{c}[aria-checked='true'][aria-disabled='true']"],
    "disabled": ["{c}:disabled", "{c}[disabled]", "{c}.disabled", "{c}[aria-disabled='true']"],
}
# Media-query scale mapping — mirrors client/css/panel.css.
SCALE_MEDIA = {
    3: [("screen and (min-width: 1501px)",)],
    2: [("screen and (max-width: 1500px)",), ("screen and (max-height: 870px)",)],
    1: [("screen and (max-width: 1000px)",), ("screen and (max-width: 800px)",)],
}

# cache-bust token for generated CSS + sprite urls (set in run() from the manifest hash)
ASSET_VERSION = "0"


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

def overlay_for(ov: dict, spec: dict, mf: dict, set_name: str) -> dict:
    """Rect hoạ tiết tâm của slice, dời theo bộ (giống rect)."""
    out = dict(ov)
    out["rect"] = rect_for({"rect": ov["rect"],
                            "setRect": ov.get("setRect")}, mf, set_name, ov["rect"])
    return out


def overlay_list(spec: dict, set_name: str = "") -> list:
    """Overlay của slice theo bộ. `setOverlays` thắng `overlays` khi có khai báo."""
    so = (spec.get("setOverlays") or {}).get(set_name)
    if so is not None:
        return list(so)
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

def parse_slice(spec: dict, set_name: str = "") -> tuple[int, int, int, int]:
    """Slice width as (top, right, bottom, left). Accepts an int or a 1-4 list.
    `setSlice: {set2: N|[t,r,b,l]}` overrides per bộ — ornament set2/set3 dày hơn,
    slice phải phủ hết hoa văn viền nếu không góc sẽ bị cắt/lặp."""
    s = (spec.get("setSlice") or {}).get(set_name, spec.get("slice", 0))
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
    # Multi-sheet: `source` stays the themed main atlas. Extra sheets are opt-in
    # per slice with `"sheet": "<name>"`. A sheet with `themed:false` has no
    # per-theme x-offset, so its slices are exported once, absolute rects.
    sheets = data.setdefault("sheets", {})
    for name, meta in list(sheets.items()):
        if isinstance(meta, str):
            sheets[name] = {"source": meta, "themed": name == "main"}
    sheets.setdefault("main", {"source": data["source"], "themed": True})
    # Trục BỘ (set) — giống trục theme nhưng theo trục y: mỗi theme có nhiều bộ asset
    # cùng nhóm, khác hoạ tiết. `rect` luôn ghi ở bộ mặc định; bộ khác = rect + offset
    # (+ setDelta riêng nếu nhóm lệch vài px), hoặc setRect khi khác cả kích thước.
    data.setdefault("sets", {"default": "set1", "offsets": {"set1": 0}})
    data["sets"].setdefault("default", list(data["sets"]["offsets"])[0])
    return data


def iter_slices(mf: dict):
    """Manifest slices, skipping `_comment_*` / other underscore keys."""
    return [(k, v) for k, v in mf["slices"].items() if not k.startswith("_")]


def sheet_name(spec: dict) -> str:
    return spec.get("sheet", "main")


def sheet_themed(mf: dict, name: str) -> bool:
    """True when this sheet repeats horizontally once per theme."""
    return bool(mf["sheets"][name].get("themed", name == "main"))


def set_names(mf: dict) -> list[str]:
    """Các bộ ĐƯỢC XUẤT. `sets.export` giới hạn (vd mới có toạ độ cho set1);
    bỏ trống = xuất hết. Các bộ vẫn phải khai trong `offsets`."""
    every = list(mf["sets"]["offsets"])
    exp = mf["sets"].get("export")
    return [s for s in every if exp is None or s in exp]


def default_set(mf: dict) -> str:
    return mf["sets"]["default"]


def slice_sets(mf: dict, spec: dict) -> list[str]:
    """Các bộ mà slice này CÓ mặt.

    Chỉ sprite trên sheet theo-theme (atlas chính) và có `themed` mới lặp theo bộ —
    sheet tĩnh (`icons`, `grids`) và slice `themed:false` (resource fills) chỉ có 1 bản.
    """
    if spec.get("sets", True) is False:
        return [default_set(mf)]
    if not sheet_themed(mf, sheet_name(spec)) or not spec.get("themed", True):
        return [default_set(mf)]
    return set_names(mf)


def rect_for(spec: dict, mf: dict | None, set_name: str, rect: list) -> list:
    """Rect của slice ở một bộ. Không truyền `mf` ⇒ trả nguyên rect."""
    if mf is None or set_name == default_set(mf):
        return rect
    override = (spec.get("setRect") or {}).get(set_name)
    if override:
        # Apply the bộ's delta (dx,dy,dw,dh) to ANY rect — base OR state — so a
        # state sprite keeps its own position/size instead of collapsing to base.
        b = spec["rect"]
        return [rect[0] + override[0] - b[0], rect[1] + override[1] - b[1],
                rect[2] + override[2] - b[2], rect[3] + override[3] - b[3]]
    dy = mf["sets"]["offsets"][set_name] + (spec.get("setDelta") or {}).get(set_name, 0)
    return [rect[0], rect[1] + dy, rect[2], rect[3]]


def load_sheets(mf: dict, root: Path) -> dict:
    """Open every declared sheet once: {name: RGBA image}."""
    out = {}
    for name, meta in mf["sheets"].items():
        path = root / meta["source"]
        if not path.exists():
            raise FileNotFoundError(f"sheet '{name}' not found: {path}")
        out[name] = Image.open(path).convert("RGBA")
    return out


def asset_filename(name: str, state: str, theme: str, default_theme: str,
                   set_name: str = "", default_s: str = "") -> str:
    parts = [name]
    if state:
        parts.append(state)
    if set_name and set_name != default_s:
        parts.append(set_name)
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


def variants(spec: dict, default_theme: bool = True,
             mf: dict | None = None, set_name: str = ""):
    """Yield (state, rect); state '' is the base variant.
    Truyền `mf` + `set_name` để rect được dời theo bộ (setRect/setDelta/offsets)."""
    yield "", rect_for(spec, mf, set_name, spec["rect"])
    for state in ordered_states(spec):
        # per-state, per-set absolute rect wins (ornament của state KHÁC vị trí/kích thước
        # giữa các bộ, không suy ra được bằng delta của base)
        ov = ((spec.get("stateSetRect") or {}).get(state) or {}).get(set_name)
        yield state, (list(ov) if ov is not None
                      else rect_for(spec, mf, set_name, spec["states"][state]))


def state_selectors(cls: str, state: str) -> list[str]:
    tpl = STATE_SELECTORS.get(state)
    if tpl is None:
        tpl = [f"{{c}}:{state}", f"{{c}}.{state}"]
    return [t.format(c=cls) for t in tpl]


def validate(mf: dict, sheet_sizes: dict) -> list[str]:
    """Return a list of human-readable validation problems (empty = OK)."""
    problems: list[str] = []
    offsets = mf["themes"]["offsets"]
    for name, spec in iter_slices(mf):
        nine = spec.get("nine", True)
        sheet = sheet_name(spec)
        if sheet not in sheet_sizes:
            problems.append(f"{name}: unknown sheet '{sheet}'")
            continue
        sw, sh = sheet_sizes[sheet]
        themed = sheet_themed(mf, sheet) and spec.get("themed", True)
        for set_name in slice_sets(mf, spec):
            t, r, b, l = parse_slice(spec, set_name)
            for state, rect in variants(spec, mf=mf, set_name=set_name):
                where = f"{name}[{state or 'base'}][{set_name}]"
                if len(rect) != 4:
                    problems.append(f"{where}: rect must be [x,y,w,h]")
                    continue
                x, y, w, h = rect
                dt = mf["themes"]["default"]
                check = offsets.items() if themed else [(dt, offsets[dt])]
                for theme, off in check:
                    if x + off < 0 or x + off + w > sw or y < 0 or y + h > sh:
                        problems.append(f"{where}[{theme}]: rect out of bounds")
                if nine and state == "":
                    if max(t, r, b, l) <= 0:
                        problems.append(f"{name}[{set_name}]: nine-slice needs a slice > 0")
                    elif t + b >= h or l + r >= w:
                        problems.append(
                            f"{name}[{set_name}]: slice ({t},{r},{b},{l}) too large for {w}x{h}")
    return problems


def source_decl(rel: str, indent: str) -> str:
    return f"{indent}border-image-source: url('{rel}');"


def url_for(rel: str) -> str:
    return "../" + rel.replace("client/", "", 1) + f"?v={ASSET_VERSION}"


def write_images(mf: dict, ims: dict, themes: list[str], write: bool) -> dict:
    """Slice + upscale + export → assets[set][theme][name][key][scale] = rel."""
    offsets = mf["themes"]["offsets"]
    default_theme = mf["themes"]["default"]
    dset = default_set(mf)
    scales = mf["scales"]
    out_tpl = mf["output"]["image"]
    result: dict = {}

    def emit(crop, stem: str, theme: str, set_name: str, bucket: dict) -> None:
        """Ghi 1 sprite ở mọi scale; đổ rel vào bucket[scale]."""
        fname = asset_filename(stem, "", theme, default_theme, set_name, dset)
        for scale in scales:
            rel = out_tpl.format(scale=scale) + "/" + fname
            bucket[scale] = rel
            if write:
                dest = ROOT / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                nearest_scale(crop, scale).save(dest)

    for set_name in set_names(mf):
        result[set_name] = {}
        for theme in themes:
            result[set_name][theme] = {}
            for name, spec in iter_slices(mf):
                if set_name not in slice_sets(mf, spec):
                    continue
                sheet = sheet_name(spec)
                s_themed = sheet_themed(mf, sheet)
                allowed = (slice_themes(spec, themes, default_theme) if s_themed
                           else [default_theme])
                if theme not in allowed:
                    continue
                # the theme x-offset only applies to a themed slice on a themed sheet
                off = offsets[theme] if (s_themed and spec.get("themed", True)) else 0
                im = ims[sheet]
                rec: dict = {}
                result[set_name][theme][name] = rec
                for state, rect in variants(spec, mf=mf, set_name=set_name):
                    x, y, w, h = rect
                    crop = im.crop((x + off, y, x + off + w, y + h))
                    key = state
                    rec[key] = {}
                    fname = asset_filename(name, state, theme, default_theme, set_name, dset)
                    for scale in scales:
                        rel = out_tpl.format(scale=scale) + "/" + fname
                        rec[key][scale] = rel
                        if write:
                            dest = ROOT / rel
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            nearest_scale(crop, scale).save(dest)
                # 9-slice with an anchored centre ornament: export a cleaned base
                # (ornament removed) + the ornament itself as `--ovN` sprites.
                ovs = overlay_list(spec, set_name)
                if ovs:
                    x, y, w, h = rect_for(spec, mf, set_name, spec["rect"])
                    src_base = im.crop((x + off, y, x + off + w, y + h))
                    cleaned = clean_overlays(src_base, [x, y, w, h],
                                             [overlay_for(o, spec, mf, set_name) for o in ovs])
                    if spec.get("flatten", False):
                        cleaned = flatten_middle(cleaned, parse_slice(spec, set_name),
                                                 spec.get("stretch", "x"))
                    rec["@base"] = {}
                    emit(cleaned, name + "--base", theme, set_name, rec["@base"])
                    for i, ov in enumerate(ovs, 1):
                        ovr = overlay_for(ov, spec, mf, set_name)
                        ox, oy, ow, oh = ovr["rect"]
                        ocrop = im.crop((ox + off, oy, ox + off + ow, oy + oh))
                        rec[f"@ov{i}"] = {}
                        emit(ocrop, f"{name}--ov{i}", theme, set_name, rec[f"@ov{i}"])
    return result


def collect_rels(assets: dict) -> set[str]:
    """Every output path referenced by the current manifest (assets[set][theme]...)."""
    return {
        assets[st][t][n][s][sc]
        for st in assets
        for t in assets[st]
        for n in assets[st][t]
        for s in assets[st][t][n]
        for sc in assets[st][t][n][s]
    }


def scan_output_dirs(mf: dict) -> set[str]:
    """Every .png currently in the generated image dirs (they hold ONLY
    generated UI sprites, so scanning is a safe fallback for the index)."""
    found: set[str] = set()
    for scale in mf["scales"]:
        d = ROOT / mf["output"]["image"].format(scale=scale)
        if d.is_dir():
            for p in d.glob("*.png"):
                found.add(p.relative_to(ROOT).as_posix())
    return found


def clean_stale(mf: dict, index_path: Path, new_rels: set[str]) -> list[str]:
    """Delete files generated by a previous run that are no longer produced.

    The index lives under a gitignored dir, so on a fresh clone it is missing and
    deleted slices would survive forever. Scanning the output dirs closes that gap.
    """
    old: set[str] = set()
    if index_path.exists():
        old = set(json.loads(index_path.read_text(encoding="utf-8")))
    old |= scan_output_dirs(mf)
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


def css_for_scale(mf: dict, view: dict, scale: int, themes: list[str],
                  set_name: str = "") -> str:
    """CSS cho MỘT bộ. `view` = view[set_name] (view[theme][name][key][scale]).

    Bộ mặc định xuất rule đầy đủ (border-width + hình + state + theme...).
    Bộ khác CHỈ xuất override đường dẫn ảnh — border-width/repeat/stretch y hệt
    nên không cần lặp lại, CSS không phình 3 lần.
    """
    prefix = mf["css"]["prefix"]
    default_theme = mf["themes"]["default"]
    sc = f".{set_name}" if set_name and set_name != default_set(mf) else ""
    full = not sc                      # bộ mặc định ⇒ rule đầy đủ
    out: list[str] = []
    hover: list[str] = []

    def scoped(sel: str) -> str:
        """Thêm tiền tố bộ vào từng selector trong chuỗi đã nối bằng dấu phẩy."""
        if not sc:
            return sel
        return ", ".join(f"{sc} {part.strip()}" for part in sel.split(","))

    def themed(sel: str, theme: str) -> str:
        """Selector cho theme, gộp luôn tiền tố bộ (cả 2 class trên <body>)."""
        base = ".theme-" + theme
        if not sc:
            return ", ".join(f"{base} {part.strip()}" for part in sel.split(","))
        return ", ".join(f"{sc}{base} {part.strip()}" for part in sel.split(","))

    for name, spec in iter_slices(mf):
        # bộ này không có slice đó (sheet tĩnh, themed:false, sets:false) → bỏ qua
        if name not in view.get(default_theme, {}):
            continue
        cls = f".{prefix}-{name}"
        nine = spec.get("nine", True)
        t, r, b, l = (v * scale for v in parse_slice(spec))
        prop = "border-image-source" if nine else "background-image"

        ovs = overlay_list(spec, set_name)
        # 1. base rule (cleaned image when an anchored ornament is present)
        base_key = "@base" if (ovs and "@base" in view[default_theme][name]) else ""
        base_rel = url_for(view[default_theme][name][base_key][scale])
        if not full:
            st, sr, sb, sl = (v * scale for v in parse_slice(spec, set_name))
            if nine and (st, sr, sb, sl) != (t, r, b, l):
                out.append(f"{sc} {cls} {{")
                out.append("  box-sizing: border-box;")
                out.append(f"  border-width: {st}px {sr}px {sb}px {sl}px;")
                out.append("  border-style: solid;")
                out.append("  border-color: transparent;")
                out.append(f"  border-image: url('{base_rel}') {st} {sr} {sb} {sl} fill "
                           f"{spec.get('repeat', 'repeat')}; }}")
            else:
                out.append(f"{sc} {cls} {{ {prop}: url('{base_rel}'); }}")
            if ovs:
                out.append(f"{sc} {cls} {{ position: relative; }}")
        else:
            out.append(f"{cls} {{")
        if full and ovs:
            out.append("  position: relative;")
        if full and nine:
            out.append("  box-sizing: border-box;")
            out.append(f"  border-width: {t}px {r}px {b}px {l}px;")
            out.append("  border-style: solid;")
            out.append("  border-color: transparent;")
            out.append(f"  border-image: url('{base_rel}') {t} {r} {b} {l} fill "
                       f"{spec.get('repeat', 'repeat')};")
        elif full:
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
        if full:
            out.append(pixelated_decls())
            out.append("}")

        # 2. theme base overrides
        for theme in slice_themes(spec, themes, default_theme):
            if theme == default_theme:
                continue
            tkey = "@base" if (ovs and "@base" in view[theme][name]) else ""
            turl = url_for(view[theme][name][tkey][scale])
            out.append(f"{themed(cls, theme)} {{ {prop}: url('{turl}'); }}")

        # 3+4. state + theme-state overrides (hover is deferred to a media block)
        for state in ordered_states(spec):
            target = hover if state == "hover" else out
            srel = url_for(view[default_theme][name][state][scale])
            sel = scoped(", ".join(state_selectors(cls, state)))
            # disabled = khoá cứng NHƯNG vẫn nuốt click: giữ pointer-events:auto để
            # control hứng cú click (không xuyên xuống canvas/cha phía sau) + cursor:default.
            # Không có phản hồi nhấn vì selector pressed/active-pressed đã loại disabled.
            extra = "; cursor: default" if state == "disabled" else ""
            target.append(f"{sel} {{ {prop}: url('{srel}'){extra}; }}")
            for theme in slice_themes(spec, themes, default_theme):
                if theme == default_theme:
                    continue
                turl = url_for(view[theme][name][state][scale])
                tsel = themed(", ".join(state_selectors(cls, state)), theme)
                target.append(f"{tsel} {{ {prop}: url('{turl}'); }}")

        # 4b. aliases: expose an existing state sprite under extra selectors
        for alias_state, target in (spec.get("alias") or {}).items():
            if target not in (spec.get("states") or {}):
                continue
            arel = url_for(view[default_theme][name][target][scale])
            sel = scoped(", ".join(state_selectors(cls, alias_state)))
            out.append(f"{sel} {{ {prop}: url('{arel}'); }}")
            for theme in slice_themes(spec, themes, default_theme):
                if theme == default_theme:
                    continue
                turl = url_for(view[theme][name][target][scale])
                tsel = themed(", ".join(state_selectors(cls, alias_state)), theme)
                out.append(f"{tsel} {{ {prop}: url('{turl}'); }}")

        # 4d. optional dimming filter for sprites without a disabled variant
        #     (atlas has no dark sprite for toggles/checkboxes — see docs/ui-slice-pipeline.md §8)
        dim = spec.get("disabledFilter")
        if dim:
            sel = ", ".join(state_selectors(cls, "disabled"))
            out.append(f"{sel} {{ filter: {dim}; cursor: default; }}")

        # 5. optional desktop hover reusing an existing state sprite (no extra file)
        hover_ref = spec.get("hoverUses")
        if hover_ref and hover_ref in (spec.get("states") or {}):
            hrel = url_for(view[default_theme][name][hover_ref][scale])
            hover.append(f"{scoped(cls + ':hover, ' + cls + '.hover')} {{ {prop}: url('{hrel}'); }}")
            for theme in slice_themes(spec, themes, default_theme):
                if theme == default_theme:
                    continue
                turl = url_for(view[theme][name][hover_ref][scale])
                hover.append(f"{themed(cls + ':hover, ' + cls + '.hover', theme)} "
                             f"{{ {prop}: url('{turl}'); }}")

        # 4c. anchored centre ornaments as pseudo-elements (never tiled)
        for i, ov in enumerate(ovs):
            pseudo = "::before" if i == 0 else "::after"
            ow, oh = ov["rect"][2], ov["rect"][3]
            pos = overlay_pos(ov.get("anchor", "center"), ow, oh, scale, parse_slice(spec, set_name))
            rel = url_for(view[default_theme][name][f"@ov{i + 1}"][scale])
            out.append(
                f"{scoped(cls + pseudo)} {{ content:''; position:absolute; {pos} "
                f"width:{ow * scale}px; height:{oh * scale}px; "
                f"background:url('{rel}') no-repeat; image-rendering:pixelated; "
                f"pointer-events:none; }}")
            for theme in slice_themes(spec, themes, default_theme):
                if theme == default_theme:
                    continue
                turl = url_for(view[theme][name][f"@ov{i + 1}"][scale])
                out.append(f"{themed(cls + pseudo, theme)} {{ background-image: url('{turl}'); }}")

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
    def every_set(scale: int) -> str:
        """Nối CSS của mọi bộ được xuất: bộ mặc định (rule đầy đủ) trước, rồi
        các bộ khác chỉ override đường dẫn ảnh → CSS không phình theo số bộ."""
        return "\n".join(css_for_scale(mf, assets[st], scale, themes, st)
                          for st in set_names(mf))

    parts = [header, every_set(1)]
    for scale in (2, 3):
        for (media,) in SCALE_MEDIA[scale]:
            parts.append(f"@media {media} {{\n")
            for line in every_set(scale).splitlines():
                parts.append(("  " + line) if line else line)
            parts.append("}\n")
    for (media,) in SCALE_MEDIA[1]:
        parts.append(f"@media {media} {{\n")
        for line in every_set(1).splitlines():
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
    default_s = default_set(mf)
    for name, spec in iter_slices(mf):
        nine = spec.get("nine", True)
        cls = f"{prefix}-{name}"
        cells = []
        for s in slice_sets(mf, spec):
            sc = "" if s == default_s else " " + s
            variants = [("", spec["rect"])]
            variants += list((spec.get("states") or {}).items())
            for st, r0 in variants:
                r = rect_for(spec, mf, s, r0)
                dw, dh = r[2], r[3]          # native sprite size → render 1:1
                label = st or "base"
                cells.append(
                    f'<span class="cell{sc}" data-cell title="{name} · {s} · {label} · {dw}×{dh}">'
                    f'<i class="{cls} {st.replace("-", " ")}" style="width:calc({dw}px * var(--s));'
                    f'height:calc({dh}px * var(--s))"></i></span>'
                )
        sl = spec.get("slice", 0)
        sl = str(sl) if not isinstance(sl, list) else ",".join(map(str, sl))
        rows.append(
            f'<section class="row"><header>{name} '
            f'<em>{"9-slice " + sl if nine else "sprite"}'
            f'{" · +" + "/".join(ordered_states(spec)) if spec.get("states") else ""}</em></header>'
            f'<div class="demos">{"".join(cells)}</div></section>'
        )

    # anim: container + fill (gauge) đặt lên nhau, 3 bộ
    orb_rows = []
    for cbase, fbase, nstage in [("container", "container-fill", 14),
                                 ("container-md", "container-md-fill", 10),
                                 ("container-sm", "container-sm-fill", 6)]:
        cspec = mf["slices"].get(cbase)
        if not cspec:
            continue
        group = []
        for s in slice_sets(mf, cspec):
            r = rect_for(cspec, mf, s, cspec["rect"])
            sc = "" if s == default_s else " " + s
            group.append(
                f'<span class="orb{sc}" data-fill="{prefix}-{fbase}" data-n="{nstage}" '
                f'title="{cbase} · {s} · {r[2]}x{r[3]}">'
                f'<i class="{prefix}-{cbase}" style="width:{r[2]}px;height:{r[3]}px"></i>'
                f'<i class="{prefix}-{fbase}-1 gfill" style="width:{r[2]}px;height:{r[3]}px"></i></span>'
            )
        orb_rows.append(f'<div class="orbrow"><em>{cbase} · {nstage} stage</em>{"".join(group)}</div>')
    fill_sec = ('<section class="row"><header>ANIM fill &#8594; container'
                '<em>base 3 bộ · gauge chạy</em></header>'
                f'<div class="orbs">{"".join(orb_rows)}</div></section>')

    theme_buttons = "".join(f'<button data-theme="{t}">{t}</button>' for t in themes)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="cache-control" content="no-store, must-revalidate">
<meta http-equiv="pragma" content="no-cache">
<title>BrowserQuest UI Lab — {mf["name"]}</title>
<link rel="stylesheet" href="css/ui-slices.generated.css?v={ASSET_VERSION}">
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
  #stage {{ display: flex; flex-direction: column; gap: 4px; }}
  #stage.checker {{ background-color: #26262e;
      background-image: linear-gradient(45deg, #333 25%, transparent 25%),
        linear-gradient(-45deg, #333 25%, transparent 25%),
        linear-gradient(45deg, transparent 75%, #333 75%),
        linear-gradient(-45deg, transparent 75%, #333 75%);
      background-size: 16px 16px;
      background-position: 0 0, 0 8px, 8px -8px, -8px 0; }}
  .row {{ display: flex; align-items: center; gap: 12px; padding: 3px 6px;
         border-bottom: 1px solid #2e2e38; }}
  .row header {{ width: 190px; flex: none; font-size: 11px; }}
  .row em {{ color: #8b93a3; font-style: normal; font-size: 10px; display: block; }}
  .demos {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
  .demos .cell {{ display: inline-flex; align-items: center; justify-content: center;
      min-width: 46px; min-height: 20px; padding: 3px;
      border: 1px solid #33334a; border-radius: 2px; }}
  .demos i {{ display: block; }}
  .orbs {{ display: flex; flex-direction: column; gap: 10px; }}
  .orbrow {{ display: flex; align-items: flex-end; gap: 18px; }}
  .orbrow em {{ width: 130px; color: #8b93a3; font-style: normal; font-size: 11px; }}
  .orb {{ position: relative; display: inline-block; }}
  .orb .gfill {{ position: absolute; left: 0; top: 0; image-rendering: pixelated; }}
  .orb i {{ display: block; }}
</style>
{kit_style()}
</head>
<body class="theme-{default_theme}">
<h1>BrowserQuest UI Lab</h1>
<div class="hint">
  Auto-generated from <code>tools/ui/slices.json</code> — mỗi tên: base + mọi state, 3 bộ
  (<code>.set1</code> mặc định · <code>.set2</code> · <code>.set3</code>) xếp cạnh nhau.
  Resize the window to exercise 1x / 2x / 3x. Toggle checkerboard.
  <b style="color:#ffe08a">build {ASSET_VERSION}</b>
</div>
<div class="toolbar">
  <button id="checkerBtn">Toggle checkerboard</button>
  {theme_buttons}
</div>
<div id="stage">
{fill_sec}
{"".join(rows)}
</div>
{kit_markup(prefix)}
<script>
  const stage = document.getElementById('stage');
  document.getElementById('checkerBtn').onclick = () => stage.classList.toggle('checker');
  document.querySelectorAll('[data-theme]').forEach(b => b.onclick = () => {{
    const t = b.dataset.theme, dft = t === '{default_theme}';
    document.body.className = dft ? '' : 'theme-' + t;
    // bộ + theme phải cùng một phần tử cha (selector .set2.theme-green .ui-*)
    document.querySelectorAll('[data-cell]').forEach(c => {{
      for (const cl of [...c.classList]) if (cl.startsWith('theme-')) c.classList.remove(cl);
      if (!dft) c.classList.add('theme-' + t);
    }});
  }});
  document.querySelectorAll('.orb[data-fill]').forEach(o => {{
    const base = o.dataset.fill, n = +o.dataset.n, el = o.querySelector('.gfill');
    let i = 1;
    setInterval(() => {{ el.className = 'gfill ' + base + '-' + i; i = i % n + 1; }}, 130);
  }});
{kit_script()}
</script>
</body>
</html>
"""


def generate_preview(mf: dict, ims: dict, default_theme: str) -> Image.Image:
    """Offline self-test: base 9-slice at 3 sizes plus every state, default theme.
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
        d.text((8, y), f"{name}  [{sheet_name(spec)}]", fill=(200, 200, 120))
        cx = pad
        sl = parse_slice(spec)
        im = ims[sheet_name(spec)]
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
    global ASSET_VERSION
    h = hashlib.md5()
    h.update(json.dumps(mf["slices"], sort_keys=True, ensure_ascii=False).encode())
    h.update(Path(__file__).read_bytes())          # packer code cũng đổi output → phải bust
    ASSET_VERSION = h.hexdigest()[:8]
    try:
        ims = load_sheets(mf, ROOT)
    except FileNotFoundError as exc:
        sys.exit(str(exc))
    im = ims["main"]
    all_themes = list(mf["themes"]["offsets"].keys())
    themes = all_themes if not args.themes else args.themes
    for t in themes:
        if t not in mf["themes"]["offsets"]:
            sys.exit(f"unknown theme '{t}' (have: {all_themes})")

    problems = validate(mf, {n: i.size for n, i in ims.items()})
    n_states = sum(len(spec.get("states") or {}) for _, spec in iter_slices(mf))
    for name, meta in mf["sheets"].items():
        i = ims[name]
        kind = "themed" if sheet_themed(mf, name) else "static"
        n = sum(1 for _, s in iter_slices(mf) if sheet_name(s) == name)
        print(f"sheet {name:6s} {kind:6s} {i.width:>5}x{i.height:<5} "
              f"{Path(meta['source']).name}  ({n} slices)")
    print(f"themes: {themes}  scales: {mf['scales']}  "
          f"slices: {len(iter_slices(mf))} (+{n_states} states)")
    print(f"sets: {set_names(mf)}  default: '{default_set(mf)}' "
          f"(default = no class suffix, others = .<set> like .theme-*)")
    if problems:
        print("VALIDATION FAILED:")
        for p in problems:
            print("  -", p)
        return 1
    print("validation: OK")

    assets = write_images(mf, ims, themes, write=not args.no_write)

    if not args.no_write:
        css = generate_css(mf, assets, themes)
        css_path = ROOT / mf["output"]["css"]
        css_path.parent.mkdir(parents=True, exist_ok=True)
        css_path.write_text(css, encoding="utf-8")
        print(f"wrote {css_path.relative_to(ROOT)}  ({len(css.splitlines())} lines)")

        lab_path = ROOT / mf["output"]["lab"]
        lab_html = generate_lab(mf, themes)
        lab_path.write_text(lab_html, encoding="utf-8")
        print(f"wrote {lab_path.relative_to(ROOT)}")
        # mirror CSS + lab into dist/client too (webpack-dev-server serves dist first,
        # and a stale copy there shadows client/ → user sees old sprites/CSS)
        dist = ROOT / "dist" / "client"
        if dist.is_dir():
            (dist / "css").mkdir(parents=True, exist_ok=True)
            (dist / "css" / "ui-slices.generated.css").write_text(css, encoding="utf-8")
            (dist / "ui-lab.html").write_text(lab_html, encoding="utf-8")
            print("wrote dist/client/css/ui-slices.generated.css + dist/client/ui-lab.html")

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

        # mockup composer (artist xếp sprite thành module rồi export JSON)
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "ui_mockup", ROOT / "tools" / "ui-mockup.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mk = ROOT / mf["output"].get("mockup", "client/ui-mockup.html")
            mk.write_text(
                mod.generate(mf, assets, ROOT,
                             css_for_scale(mf, assets[default_set(mf)], 1, themes)),
                encoding="utf-8")
            print(f"wrote {mk.relative_to(ROOT)}")
            dist = ROOT / "dist" / "client"
            if dist.is_dir():
                (dist / "ui-mockup.html").write_text(mk.read_text(encoding="utf-8"),
                                                     encoding="utf-8")
                print("wrote dist/client/ui-mockup.html")
        except Exception as exc:  # non-fatal
            print(f"mockup page skipped: {exc}")

        preview = generate_preview(mf, ims, mf["themes"]["default"])
        prev_path = ROOT / mf["output"]["preview"]
        prev_path.parent.mkdir(parents=True, exist_ok=True)
        preview.save(prev_path)
        print(f"wrote {prev_path.relative_to(ROOT)}")

        index_path = ROOT / "tools" / "ui" / "out" / "generated.json"
        new_rels = collect_rels(assets)
        removed = clean_stale(mf, index_path, new_rels)
        if removed:
            print(f"removed {len(removed)} stale file(s)")
        index_path.write_text(json.dumps(sorted(new_rels), indent=0), encoding="utf-8")

    # guard: the UI kit must NEVER write into the game's own img/<n>/ui/ dir
    game_ui = ROOT / "client/img/1/ui"
    if (ROOT / mf["output"]["image"].format(scale=1)).resolve() == game_ui.resolve():
        print("ERROR: kit output collides with the game's client/img/1/ui — change output.image")
        return 1

    print(f"done: {len(collect_rels(assets))} images "
          f"({len(iter_slices(mf))} slices + {n_states} states, {len(themes)} themes, "
          f"{len(mf['scales'])} scales)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
