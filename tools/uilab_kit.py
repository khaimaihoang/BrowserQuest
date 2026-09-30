"""uilab_kit.py — interactive UI-kit demo injected into the generated client/ui-lab.html.

DEV ONLY. Nothing here ships in the game CSS: the markup/styles/JS are inlined into the
lab page (client/ui-lab.html), a dev page. Every component is rendered by the real asset
pipeline — the `.ui-*` classes produced by tools/ui-pack.py — at the same 1x/2x/3x `--s`
scale the lab page uses. Item icons come from client/img/1/item-*.png (6-frame 96x16
sheets; frame 0 is shown with background-size:600%).

Groups rendered by kit_markup(): button · switch · checkbox/radio · tabs (ngang / dọc /
icon vuông) · slider · input field · progress bars · inventory + hotbar · panel/list-row/
dialog · gauge · toast · HUD mock.

Wiring (tools/ui-pack.py):
    from uilab_kit import kit_style, kit_markup, kit_script
"""
from __future__ import annotations

# 96x16 = 6 frame item sheets. item-cake is 72x24, so it is excluded on purpose.
ITEMS = [
    "item-sword1", "item-redsword", "item-bluesword", "item-axe", "item-morningstar",
    "item-leatherarmor", "item-platearmor", "item-goldenarmor", "item-firepotion", "item-flask",
]


# ---------------------------------------------------------------- markup helpers


def _tab(prefix: str, key: str, label: str, active: bool = False) -> str:
    """Một tab = 4 mảnh viền (tab-top/bottom/left/right) + ô giữa chứa nhãn."""
    a = " active" if active else ""
    e = f"{prefix}-tab-"
    return (f'<button class="kit-tab{a}" data-tab="{key}" type="button">'
            f'<i class="{e}top e top{a}"></i><i class="{e}left e left{a}"></i>'
            f'<i class="{e}right e right{a}"></i><i class="{e}bottom e bottom{a}"></i>'
            f'<span class="mid">{label}</span></button>')


def _icon_tab(prefix: str, key: str, n: int, active: bool = False) -> str:
    a = " active" if active else ""
    return (f'<button class="kit-itab" data-tab="{key}" type="button" aria-label="tab {n}">'
            f'<i class="{prefix}-tab-icon-{n}{a}"></i></button>')


def _slot(prefix: str, item: str, count: int | None = None, kind: str = "md",
          active: bool = False, key: str | None = None) -> str:
    cls = f"{prefix}-slot" + ("" if kind == "md" else f"-{kind}")
    a = " active" if active else ""
    badge = f"<b>{count}</b>" if count is not None else ""
    hot = f"<u>{key}</u>" if key else ""
    return (f'<button class="kit-slot {cls}{a}" data-slot type="button" title="{item}">'
            f'<i class="kit-item" style="background-image:url(\'img/1/{item}.png\')"></i>'
            f'{badge}{hot}</button>')


def _switch(prefix: str, label: str, checked: bool = False, cls: str = "toggle-h",
            disabled: bool = False) -> str:
    c = " checked" if checked else ""
    lbl = f'<span class="lbl">{label}</span>' if label else ""
    return (f'<button class="kit-switch{" disabled" if disabled else ""}" data-switch type="button" '
            f'role="switch" aria-checked="{"true" if checked else "false"}"'
            f'{" disabled" if disabled else ""}>'
            f'<i class="{prefix}-{cls}{c}{" disabled" if disabled else ""}"></i>{lbl}</button>')


def _check(prefix: str, label: str, cls: str, state: str = "") -> str:
    """state: '' | checked | pressed | checked-pressed"""
    s = f" {state}" if state else ""
    on = "checked" in state
    extra = " data-radio" if cls.endswith("radio") else " data-check"
    return (f'<button class="kit-check" type="button"{extra} aria-checked="{"true" if on else "false"}">'
            f'<i class="{prefix}-{cls}{s}"></i><span class="lbl">{label}</span></button>')


def _bar(prefix: str, key: str, label: str, color: str, pct: int, vertical: bool = False) -> str:
    """Thanh tiến trình: fill nằm TRONG khung (z-index thấp hơn ::before = hoạ tiết tâm),
    nhờ vậy fill đè lên nền khung nhưng vẫn nằm dưới hoạ tiết + chữ."""
    v = vertical
    cap = f'<span class="cap">{label}</span>' if label else ""
    return (f'<div class="kit-bar {"v" if v else "h"}" data-bar="{key}" data-pct="{pct}">'
            f'{cap}<div class="{prefix}-bar{"-v" if v else "-h"} frame">'
            f'<div class="{prefix}-bar-fill{"-v" if v else ""}-{color} fill"></div>'
            f'</div></div>')


# ---------------------------------------------------------------- style

KIT_STYLE = r"""
/* ============ UI KIT (dev demo — inlined on purpose, không nằm trong CSS ship) ============ */
@font-face { font-family:'GraphicPixel'; src:url('fonts/graphicpixel-webfont.woff') format('woff'); font-display:swap; }
:root { --u: calc(1px * var(--s)); --kitink:#dfe3ea; --kitdim:#8b93a3; --kitaccent:#8fd0ff;
        --kitcard:#22222a; --kitline:#2e2e38; }
body.components-only #stage { display:none; }
#kit { display:grid; gap:calc(12 * var(--u));
  grid-template-columns:repeat(auto-fill, minmax(calc(300 * var(--u)), 1fr));
  margin-top:calc(6 * var(--u)); padding-bottom:calc(40 * var(--u)); }
#kit *, #kit *::before, #kit *::after { box-sizing:border-box; }
#kit h2 { grid-column:1/-1; margin:calc(10 * var(--u)) 0 0; font-size:calc(15 * var(--u)); }
.kit-intro { grid-column:1/-1; color:var(--kitdim); font-size:calc(11 * var(--u)); line-height:1.6; }
.kit-intro code { color:#cfe6ff; }
.kit-nav { grid-column:1/-1; display:flex; gap:calc(6 * var(--u)); flex-wrap:wrap; }
.kit-nav a { color:#9fd7ff; text-decoration:none; border:1px solid #2f3b4a; border-radius:3px;
  padding:calc(2 * var(--u)) calc(8 * var(--u)); font:calc(11 * var(--u))/1 monospace; }
.kit-nav a:hover { background:#26303c; }
#kit button { appearance:none; -webkit-appearance:none; background:none; margin:0; padding:0;
  color:inherit; font:inherit; cursor:pointer; -webkit-tap-highlight-color:transparent; }
/* chỉ xoá viền của nút KHÔNG dùng border-image (nút .ui-button* giữ border của 9-slice) */
#kit button:not([class*="ui-"]), #kit .kit-slot { border:0; }
#kit button:disabled { cursor:not-allowed; }
/* nút bị khoá: sprite tối + pointer-events:none (không nhấn được) — wrapper để vẫn hiện cursor */
.kit-lockwrap { display:inline-flex; cursor:not-allowed; }
.card { background:var(--kitcard); border:1px solid var(--kitline); border-radius:6px;
  padding:calc(10 * var(--u)) calc(12 * var(--u)); min-width:0; }
.card > h3 { margin:0; font:600 calc(11 * var(--u))/1.3 system-ui; color:var(--kitaccent);
  letter-spacing:.4px; text-transform:uppercase; }
.card > em { display:block; font-style:normal; color:var(--kitdim); font:calc(10 * var(--u))/1.6 monospace;
  margin:calc(3 * var(--u)) 0 calc(10 * var(--u)); }
.row { display:flex; align-items:center; gap:calc(10 * var(--u)); flex-wrap:wrap; margin-bottom:calc(10 * var(--u)); }
.row:last-child { margin-bottom:0; }
.col { display:flex; flex-direction:column; gap:calc(8 * var(--u)); align-items:flex-start; }
.lbl { color:#cdd6e2; font:calc(11 * var(--u))/1.2 'GraphicPixel', monospace; letter-spacing:.5px; }
.log { margin:calc(8 * var(--u)) 0 0; color:#9fd7ff; font:calc(10 * var(--u))/1.6 monospace; }

/* ---- buttons ---- */
.ktxt { display:flex; align-items:center; justify-content:center; width:100%; height:100%;
  font-family:'GraphicPixel', monospace; font-size:calc(9 * var(--u)); letter-spacing:.5px;
  color:#f1e7cd; text-shadow:0 calc(1 * var(--u)) 0 rgba(0,0,0,.8); text-transform:uppercase; white-space:nowrap; }
.btn { min-width:calc(78 * var(--u)); height:calc(38 * var(--u)); padding:0 calc(6 * var(--u)); }
.btn-slim { width:calc(36 * var(--u)); height:calc(38 * var(--u)); }
.btn-thin { width:calc(112 * var(--u)); height:calc(20 * var(--u)); }
.btn-tiny { width:calc(26 * var(--u)); height:calc(26 * var(--u)); }
.btn-ico { width:calc(32 * var(--u)); height:calc(32 * var(--u)); display:inline-flex;
  align-items:center; justify-content:center; }
.kit-ico { display:block; width:calc(16 * var(--u)); height:calc(16 * var(--u));
  background-repeat:no-repeat; background-size:contain; background-position:center; image-rendering:pixelated; }
.badge { display:inline-block; margin-left:calc(4 * var(--u)); padding:0 calc(3 * var(--u));
  background:#000a; border-radius:calc(2 * var(--u)); color:#ffe08a; font-size:calc(9 * var(--u)); font-style:normal; }

/* ---- switch / checkbox / radio ---- */
.kit-switch { display:inline-flex; align-items:center; gap:calc(6 * var(--u)); padding:calc(3 * var(--u)); }
.kit-switch i { display:block; width:calc(16 * var(--u)); height:calc(8 * var(--u)); }
.kit-switch i.ui-toggle-v { width:calc(8 * var(--u)); height:calc(16 * var(--u)); }
.kit-check { display:inline-flex; align-items:center; gap:calc(6 * var(--u)); padding:calc(4 * var(--u)); }
.kit-check i { display:block; width:calc(12 * var(--u)); height:calc(12 * var(--u)); }

/* ---- tabs ---- */
.kit-tabbar { display:flex; align-items:flex-end; gap:calc(4 * var(--u)); flex-wrap:wrap; }
.kit-tabbar.rail { flex-direction:column; align-items:flex-start; }
/* tab dùng đúng bề dày sprite theo state (12px inactive / 16px active) để 4 mảnh khớp 1:1,
   không bị hở góc; tab active sẽ to ra 4px mỗi chiều (giống tab được nâng lên) */
.kit-tab { display:grid;
  grid-template-columns:calc(12 * var(--u)) calc(48 * var(--u)) calc(12 * var(--u));
  grid-template-rows:calc(12 * var(--u)) calc(48 * var(--u)) calc(12 * var(--u)); }
.kit-tab.active { grid-template-columns:calc(16 * var(--u)) calc(48 * var(--u)) calc(16 * var(--u));
  grid-template-rows:calc(16 * var(--u)) calc(48 * var(--u)) calc(16 * var(--u)); }
.kit-tab .e { display:block; background-size:contain; }
.kit-tab .top { grid-area:1/2/2/3; } .kit-tab .bottom { grid-area:3/2/4/3; }
.kit-tab .left { grid-area:2/1/3/2; } .kit-tab .right { grid-area:2/3/3/4; }
.kit-tab .mid { grid-area:2/2/3/3; display:flex; align-items:center; justify-content:center;
  background:#171720; color:#9aa3b2; font-family:'GraphicPixel', monospace;
  font-size:calc(10 * var(--u)); letter-spacing:.5px; }
.kit-tab.active .mid { background:#232334; color:#ffe9b8; }
.kit-itab { width:calc(16 * var(--u)); height:calc(16 * var(--u)); }
.kit-itab i { display:block; width:100%; height:100%; }
.kit-square { display:grid; grid-template-columns:repeat(2, calc(28 * var(--u)));
  grid-template-rows:repeat(2, calc(28 * var(--u))); gap:calc(2 * var(--u)); }
.kit-square .kit-itab { width:calc(28 * var(--u)); height:calc(28 * var(--u)); }
.tabpanel { border:1px solid var(--kitline); background:#1b1b22; padding:calc(8 * var(--u));
  min-height:calc(26 * var(--u)); color:#c6cfdb; font:calc(10 * var(--u))/1.6 monospace; }
.tabpanel[hidden] { display:none; }

/* ---- slider ---- */
.kit-slider { position:relative; height:calc(24 * var(--u)); touch-action:none; cursor:pointer; }
.kit-slider.v { width:calc(24 * var(--u)); height:calc(120 * var(--u)); }
.kit-slider .track { position:absolute; inset:0; pointer-events:none; }
.kit-slider .fill { position:absolute; pointer-events:none; }
.kit-slider.h .fill { left:calc(8 * var(--u)); top:50%; height:calc(6 * var(--u)); transform:translateY(-50%); }
.kit-slider.v .fill { bottom:calc(8 * var(--u)); left:50%; width:calc(6 * var(--u)); transform:translateX(-50%); }
.kit-slider .thumb { position:absolute; pointer-events:none; }
.kit-slider.h .thumb { width:calc(6 * var(--u)); height:calc(7 * var(--u)); }
.kit-slider.v .thumb { width:calc(7 * var(--u)); height:calc(6 * var(--u)); }
.out { min-width:calc(42 * var(--u)); color:#ffe08a; font:calc(11 * var(--u))/1 monospace; }

/* ---- input field ---- */
.kit-input { display:flex; align-items:center; width:calc(190 * var(--u)); height:calc(38 * var(--u));
  padding:0 calc(9 * var(--u)); }
.kit-input input { flex:1; min-width:0; background:none; border:0; outline:0; color:#f2ecdc;
  font:calc(11 * var(--u))/1 'GraphicPixel', monospace; letter-spacing:.5px; }
.kit-input input::placeholder { color:#7d8797; }
.kit-input:focus-within { filter:brightness(1.2) drop-shadow(0 0 calc(3 * var(--u)) #8fd0ffaa); }
.kit-stepper { display:inline-flex; align-items:center; gap:calc(5 * var(--u)); }
.kit-stepper .out { min-width:calc(36 * var(--u)); text-align:center; }
.kit-chat { display:flex; align-items:center; gap:calc(6 * var(--u)); width:100%; padding:calc(5 * var(--u)); }
.kit-chat input { flex:1; min-width:0; background:none; border:0; outline:0; color:#eee;
  font:calc(11 * var(--u))/1 'GraphicPixel', monospace; }
.kit-msgs { margin:calc(8 * var(--u)) 0 0; padding:0; list-style:none; color:#c6cfdb;
  font:calc(10 * var(--u))/1.7 monospace; }
.kit-msgs li { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

/* ---- progress bars ---- */
.kit-bar { position:relative; display:flex; flex-direction:column; gap:calc(2 * var(--u));
  width:calc(180 * var(--u)); }
.kit-bar .frame { position:relative; z-index:0; height:calc(24 * var(--u)); width:100%; }
.kit-bar.v { width:auto; align-items:flex-start; }
.kit-bar.v .frame { width:calc(24 * var(--u)); height:calc(130 * var(--u)); }
/* khung tạo stacking context: nền (border-image) < fill < hoạ tiết tâm (::before) */
.kit-bar .frame::before { z-index:2; }
.kit-bar .fill { position:absolute; z-index:1; }
.kit-bar.h .fill { left:calc(15 * var(--u)); top:50%; height:calc(6 * var(--u)); transform:translateY(-50%); }
.kit-bar.v .fill { bottom:calc(15 * var(--u)); left:50%; width:calc(6 * var(--u)); transform:translateX(-50%); }
.kit-bar .cap { color:#e8ddc6; font:calc(9 * var(--u))/1 'GraphicPixel', monospace;
  text-shadow:0 calc(1 * var(--u)) 0 #000; white-space:nowrap; }
.kit-legend { color:var(--kitdim); font:calc(10 * var(--u))/1.6 monospace; }

/* ---- slots / inventory ---- */
.kit-slots { display:grid; grid-template-columns:repeat(5, auto); gap:calc(6 * var(--u)); justify-content:start; }
.kit-hotbar { display:flex; gap:calc(6 * var(--u)); flex-wrap:wrap; }
.kit-slot { position:relative; display:block; }
.kit-slot.ui-slot-md { width:calc(22 * var(--u)); height:calc(22 * var(--u)); }
.kit-slot.ui-slot-lg { width:calc(54 * var(--u)); height:calc(54 * var(--u)); }
.kit-item { position:absolute; left:50%; top:50%; width:calc(16 * var(--u)); height:calc(16 * var(--u));
  margin:calc(-8 * var(--u)) 0 0 calc(-8 * var(--u)); background-repeat:no-repeat;
  background-size:600% auto; background-position:0 0; image-rendering:pixelated; }
.kit-slot.ui-slot-lg .kit-item { width:calc(32 * var(--u)); height:calc(32 * var(--u));
  margin:calc(-16 * var(--u)) 0 0 calc(-16 * var(--u)); }
.kit-slot b, .kit-slot u { position:absolute; font:calc(9 * var(--u))/1 monospace;
  text-shadow:0 0 calc(2 * var(--u)) #000; font-style:normal; text-decoration:none; }
.kit-slot b { right:calc(1 * var(--u)); bottom:calc(1 * var(--u)); color:#ffe08a; }
.kit-slot u { left:calc(2 * var(--u)); top:calc(1 * var(--u)); color:#9fd7ff; }
.kit-slot.active { filter:drop-shadow(0 0 calc(3 * var(--u)) #ffd479cc); }

/* ---- panel / list rows / dialog / toast ---- */
.kit-list { display:flex; flex-direction:column; gap:calc(2 * var(--u)); }
.kit-lrow { display:flex; align-items:center; gap:calc(8 * var(--u)); padding:calc(4 * var(--u)) calc(6 * var(--u)); }
.kit-lrow .grow { flex:1; min-width:0; color:#dfe3ea; font:calc(11 * var(--u))/1.4 'GraphicPixel', monospace; }
.kit-lrow .val { color:#ffe08a; font:calc(10 * var(--u))/1 monospace; }
.kit-div { width:100%; height:calc(3 * var(--u)); }
.kit-dialog { position:fixed; inset:0; z-index:50; display:flex; align-items:center; justify-content:center;
  background:#000a; }
.kit-dialog[hidden] { display:none; }
.kit-dialog .win { position:relative; width:min(92vw, calc(300 * var(--u)));
  padding:calc(14 * var(--u)) calc(16 * var(--u)) calc(12 * var(--u)); }
.kit-dialog h4 { margin:calc(2 * var(--u)) 0 calc(6 * var(--u)); color:#ffe9b8;
  font:calc(12 * var(--u))/1.3 'GraphicPixel', monospace; text-align:center; }
.kit-dialog p { margin:0; color:#cfd7e2; font:calc(10 * var(--u))/1.6 monospace; }
.kit-close { position:absolute; top:calc(-6 * var(--u)); right:calc(-6 * var(--u));
  width:calc(12 * var(--u)); height:calc(12 * var(--u));
  background:url('img/1/ui/close.png') no-repeat center/contain; image-rendering:pixelated; }
.kit-close:hover, .kit-close:active { background-image:url('img/1/ui/close_pressed.png'); }
.kit-toast { position:fixed; left:50%; bottom:calc(20 * var(--u)); transform:translateX(-50%); z-index:60;
  padding:calc(7 * var(--u)) calc(16 * var(--u)); color:#f2ecdc;
  font:calc(10 * var(--u))/1 'GraphicPixel', monospace; opacity:0; transition:opacity .18s;
  pointer-events:none; }
.kit-toast.on { opacity:1; }

/* ---- gauge + HUD mock ---- */
.kit-gauges { display:flex; gap:calc(14 * var(--u)); align-items:center; flex-wrap:wrap; }
.kit-gauge { position:relative; display:inline-flex; align-items:center; justify-content:center; }
.kit-gauge i { display:block; width:100%; height:100%; }
.kit-gauge span { position:absolute; font:calc(9 * var(--u))/1 'GraphicPixel', monospace; color:#ffe9b8; }
.kit-hud { position:relative; width:100%; height:calc(160 * var(--u)); background:#12121a;
  border:1px solid var(--kitline); overflow:hidden; }
.kit-hud .abs { position:absolute; }
.kit-hud .bars { left:calc(10 * var(--u)); top:calc(10 * var(--u)); display:flex; flex-direction:column; gap:calc(6 * var(--u)); }
.kit-hud .bars .kit-bar { width:calc(150 * var(--u)); }
.kit-hud .bars .kit-bar .frame { height:calc(20 * var(--u)); }
.kit-hud .top { right:calc(10 * var(--u)); top:calc(10 * var(--u)); display:flex; gap:calc(4 * var(--u)); }
.kit-hud .bottom { left:50%; bottom:calc(10 * var(--u)); transform:translateX(-50%); }
.kit-hud .side { right:calc(10 * var(--u)); bottom:calc(10 * var(--u)); }
"""


# ---------------------------------------------------------------- markup


def kit_markup(prefix: str = "ui") -> str:
    p = prefix

    buttons = f"""<section id="k-button" class="card"><h3>Button</h3>
<em>base (sáng) = enabled · <b>.pressed</b> = sáng+nhấn · <b>disabled</b> (`[disabled]` /
`.disabled` / `[aria-disabled]`) = tối, **KHOÁ CỨNG**: nhấn không đổi sprite +
`pointer-events:none` · KHÔNG hover</em>
<div class="row">
  <button class="{p}-button btn" data-count type="button"><span class="ktxt">Play <i class="badge" data-badge>0</i></span></button>
  <button class="{p}-button btn" type="button"><span class="ktxt">Giữ để nhấn</span></button>
  <button class="{p}-button btn" type="button" disabled><span class="ktxt">Locked (native)</span></button>
  <span class="kit-lockwrap" title="div[disabled] — khoá cứng"><span class="{p}-button btn" disabled aria-disabled="true" role="button"><span class="ktxt">Locked (div)</span></span></span>
</div>
<div class="row">
  <button class="{p}-button-slim btn-slim" type="button" aria-label="minus"><span class="ktxt">&ndash;</span></button>
  <button class="{p}-button-slim btn-slim" type="button" aria-label="plus" disabled><span class="ktxt">+</span></button>
  <button class="{p}-button-thin btn-thin" type="button"><span class="ktxt">Level up</span></button>
  <button class="{p}-button-thin btn-thin" type="button" disabled><span class="ktxt">Locked</span></button>
  <span class="kit-lockwrap"><span class="{p}-button-tiny btn-tiny" disabled aria-disabled="true" role="button"><i class="kit-item" style="background-image:url('img/1/item-sword1.png')"></i></span></span>
  <button class="{p}-button btn-ico" type="button" aria-label="settings"><i class="{p}-tab-icon-1 kit-ico"></i></button>
</div>
<p class="log" data-log>button clicks: 0 · giữ chuột để xem .pressed (sáng+nhấn); nút khoá: ấn không ăn, sprite đứng yên</p></section>"""

    switches = f"""<section id="k-switch" class="card"><h3>Switch / Toggle</h3>
<em>OFF/ON × enabled/disabled: enabled luôn dùng sprite <b>sáng</b>, disabled luôn dùng sprite
<b>tối</b> (atlas có 2 bản cho mỗi vị trí núm) + dim nhẹ <code>brightness(.72)</code> để 2 mức
phân biệt rõ ngay ở theme tối (~8 luma là quá ít nếu chỉ đổi sprite).
Khoá cứng: `[disabled]`/`:disabled`/`.disabled`/`[aria-disabled]` (+ `.checked` = tối on).</em>
<div class="row">
  {_switch(p, "Sound", True)}
  {_switch(p, "Music")}
  {_switch(p, "Effects (on + khoá)", True, disabled=True)}
  {_switch(p, "Vibration (off + khoá)", disabled=True)}
</div>
<div class="row">
  <span class="lbl">Vertical</span>
  <span class="kit-switch" data-switch-v><i class="{p}-toggle-v checked"></i><span class="lbl">ON</span></span>
  <span class="kit-switch" data-switch-v><i class="{p}-toggle-v"></i><span class="lbl">OFF</span></span>
  <span class="kit-switch"><i class="{p}-toggle-v checked disabled"></i><span class="lbl">khoá + ON</span></span>
  <span class="kit-switch"><i class="{p}-toggle-v disabled"></i><span class="lbl">khoá + OFF</span></span>
</div>
<p class="log" data-switchlog>switch: Sound=on, Music=off</p></section>"""

    checks = f"""<section id="k-check" class="card"><h3>Checkbox &amp; Radio</h3>
<em>enabled dùng sprite <b>sáng</b> (checked &amp; unchecked), disabled dùng sprite <b>tối</b>
(cả checked &amp; unchecked) + dim nhẹ — khoá cứng, không nhấn được</em>
<div class="row">
  {_check(p, "Fullscreen", "checkbox", "checked")}
  {_check(p, "Vibration", "checkbox")}
  {_check(p, "Auto-save (khoá)", "checkbox", "disabled")}
  {_check(p, "Cloud save (khoá + on)", "checkbox", "checked disabled")}
</div>
<div class="row" data-radio-group="quality">
  <span class="lbl">Quality</span>
  {_check(p, "Low", "radio", "checked")}
  {_check(p, "Medium", "radio")}
  {_check(p, "High", "radio")}
  {_check(p, "Ultra (khoá)", "radio", "disabled")}
</div>
<p class="log" data-checklog>checkbox: Fullscreen=on · radio: Low</p></section>"""

    tabs = f"""<section id="k-tabs" class="card"><h3>Tabs — ngang / dọc / vuông</h3>
<em>{p}-tab-top/bottom/left/right ghép khung tab · {p}-tab-icon-1..4 cho tab vuông (icon)</em>
<div class="kit-tabbar" data-tabbar="h">
  {_tab(p, "h1", "Inventory", True)}{_tab(p, "h2", "Skills")}{_tab(p, "h3", "Quests")}
</div>
<div class="tabpanel" data-tabpanel="h1">TAB NGANG · Inventory — 12/20 ô (khung 4 mảnh, tab active sáng)</div>
<div class="tabpanel" data-tabpanel="h2" hidden>TAB NGANG · Skills — 3 điểm chưa dùng</div>
<div class="tabpanel" data-tabpanel="h3" hidden>TAB NGANG · Quests — 2 nhiệm vụ đang làm</div>
<div class="row" style="margin-top:calc(12 * var(--u)); align-items:flex-start">
  <div class="kit-tabbar rail" data-tabbar="v">
    {_tab(p, "v1", "Map", True)}{_tab(p, "v2", "Party")}
  </div>
  <div style="flex:1; min-width:calc(140 * var(--u))">
    <div class="tabpanel" data-tabpanel="v1">TAB DỌC · Map — rail bên trái</div>
    <div class="tabpanel" data-tabpanel="v2" hidden>TAB DỌC · Party — rail bên trái</div>
  </div>
  <div class="col">
    <span class="lbl">ngang (icon)</span>
    <div class="kit-tabbar" data-tabbar="i">
      {_icon_tab(p, "i1", 1, True)}{_icon_tab(p, "i2", 2)}{_icon_tab(p, "i3", 3)}{_icon_tab(p, "i4", 4)}
    </div>
    <span class="lbl">dọc (icon)</span>
    <div class="kit-tabbar rail" data-tabbar="j">
      {_icon_tab(p, "j1", 1, True)}{_icon_tab(p, "j2", 2)}{_icon_tab(p, "j3", 3)}
    </div>
    <span class="lbl">vuông 2x2</span>
    <div class="kit-square" data-tabbar="k">
      {_icon_tab(p, "k1", 1, True)}{_icon_tab(p, "k2", 2)}{_icon_tab(p, "k3", 3)}{_icon_tab(p, "k4", 4)}
    </div>
  </div>
</div>
<p class="log" data-tablog>tab: ngang=h1 · dọc=v1 · vuông=k1</p></section>"""

    slider = f"""<section id="k-slider" class="card"><h3>Slider</h3>
<em>{p}-slider-track-h/v + {p}-slider-thumb-h/v + {p}-bar-fill-* — kéo bằng chuột / chạm</em>
<div class="row">
  <div class="kit-slider h" data-slider="h" style="width:calc(220 * var(--u))">
    <div class="{p}-slider-track-h track"></div>
    <div class="{p}-bar-fill-green kit-fill"></div>
    <div class="{p}-slider-thumb-h thumb"></div>
  </div>
  <output class="out" data-out="h">40%</output>
</div>
<div class="row" style="align-items:flex-end">
  <div class="kit-slider v" data-slider="v">
    <div class="{p}-slider-track-v track"></div>
    <div class="{p}-bar-fill-v-gold kit-fill"></div>
    <div class="{p}-slider-thumb-v thumb"></div>
  </div>
  <output class="out" data-out="v">75%</output>
  <div class="col">
    <span class="lbl">Volume (bar-fill-blue)</span>
    <div class="kit-slider h" data-slider="vol" style="width:calc(140 * var(--u))">
      <div class="{p}-slider-track-h track"></div>
      <div class="{p}-bar-fill-blue kit-fill"></div>
      <div class="{p}-slider-thumb-h thumb"></div>
    </div>
  </div>
</div></section>"""

    inputs = f"""<section id="k-input" class="card"><h3>Input field</h3>
<em>input thật + khung {p}-panel-slim / {p}-panel — focus ring, placeholder, stepper, chat bar</em>
<div class="row">
  <label class="{p}-panel-slim kit-input"><input type="text" value="Hero" maxlength="16" placeholder="Player name"></label>
  <label class="{p}-panel-slim kit-input" style="width:calc(110 * var(--u))"><input type="number" value="20" min="1" max="99" step="1"></label>
</div>
<div class="row">
  <div class="kit-stepper">
    <button class="{p}-button-tiny btn-tiny" type="button" data-step="-1"><span class="ktxt">&ndash;</span></button>
    <output class="out" data-step-out>5</output>
    <button class="{p}-button-tiny btn-tiny" type="button" data-step="1"><span class="ktxt">+</span></button>
    <span class="lbl">skill points</span>
  </div>
</div>
<div class="{p}-panel kit-chat">
  <input type="text" placeholder="Say something…" maxlength="40" data-chat>
  <button class="{p}-button-tiny btn-tiny" type="button" data-send><span class="ktxt">&#9166;</span></button>
</div>
<ul class="kit-msgs" data-chatlog><li>system: welcome to UI lab</li></ul></section>"""

    bars = f"""<section id="k-bars" class="card"><h3>Progress bars</h3>
<em>{p}-bar-h/-v + {p}-bar-fill-{{red,blue,gold,green,purple}} (hoạ tiết tâm neo giữa)</em>
<div class="row" style="gap:calc(14 * var(--u))">
  {_bar(p, "hp", "HP 100/100", "red", 100)}
  {_bar(p, "mp", "MP 60/80", "blue", 75)}
</div>
<div class="row" style="gap:calc(14 * var(--u)); align-items:flex-end">
  {_bar(p, "xp", "XP 42/120", "gold", 35)}
  {_bar(p, "st", "STAM", "green", 55)}
  {_bar(p, "stv", "V", "purple", 70, vertical=True)}
</div>
<div class="row">
  <button class="{p}-button-thin btn-thin" type="button" data-hp="-15"><span class="ktxt">-15 HP</span></button>
  <button class="{p}-button-thin btn-thin" type="button" data-hp="15"><span class="ktxt">+15 HP</span></button>
  <span class="kit-legend">bar dọc = {p}-bar-v + {p}-bar-fill-v-*</span>
</div></section>"""

    inv_slots = "".join(_slot(p, it, c, "md", i == 4)
                        for i, (it, c) in enumerate(zip(ITEMS, [1, 2, 1, 3, 12, 1, 1, 1, 5, 8])))
    hot_slots = "".join(_slot(p, it, c, "lg", i == 0, key=str(i + 1))
                        for i, (it, c) in enumerate(zip(ITEMS[:6], [3, 1, 12, 1, 2, 1])))
    slots = f"""<section id="k-slots" class="card"><h3>Inventory &amp; hotbar</h3>
<em>{p}-slot-md / {p}-slot-lg + .active — click chọn ô, hotbar nhận phím 1..6</em>
<div class="kit-slots">{inv_slots}</div>
<div class="kit-hotbar" style="margin-top:calc(12 * var(--u))">{hot_slots}</div>
<p class="log" data-slotlog>slot: item-morningstar (phím 5)</p></section>"""

    list_rows = f"""<div class="kit-lrow"><span class="grow">Master volume</span><span class="val">80%</span></div>
<i class="{p}-divider-h kit-div"></i>
<div class="kit-lrow"><span class="grow">Graphics</span><span class="val">High</span></div>
<i class="{p}-divider-h kit-div"></i>
<div class="kit-lrow"><span class="grow">Language</span><span class="val">Tiếng Việt</span></div>
<i class="{p}-divider-h kit-div"></i>
<div class="kit-lrow"><span class="grow">Sound</span>{_switch(p, "Effects", True)}</div>"""
    panel = f"""<section id="k-panel" class="card"><h3>Panel · list row · dialog</h3>
<em>{p}-panel-textured + {p}-panel-header + {p}-panel-title + {p}-divider-h + close.png</em>
<div class="{p}-panel" style="padding:calc(8 * var(--u))">
  <i class="{p}-panel-title" style="display:block;margin:0 auto calc(4 * var(--u))"></i>
  <div class="kit-list">{list_rows}</div>
</div>
<div class="row" style="margin-top:calc(10 * var(--u))">
  <button class="{p}-button btn" type="button" data-dialog="d1"><span class="ktxt">Open dialog</span></button>
  <button class="{p}-button-thin btn-thin" type="button" data-toast><span class="ktxt">Toast</span></button>
</div></section>"""

    gauges = f"""<section id="k-gauge" class="card"><h3>Gauge (container)</h3>
<em>{p}-container · -md · -sm — sprite tròn + nhãn %</em>
<div class="kit-gauges">
  <span class="kit-gauge" style="width:calc(40 * var(--u));height:calc(32 * var(--u))"><i class="{p}-container"></i><span>68%</span></span>
  <span class="kit-gauge" style="width:calc(32 * var(--u));height:calc(24 * var(--u))"><i class="{p}-container-md"></i><span>32%</span></span>
  <span class="kit-gauge" style="width:calc(22 * var(--u));height:calc(16 * var(--u))"><i class="{p}-container-sm"></i><span>7</span></span>
</div>
<div class="row" style="margin-top:calc(10 * var(--u))">
  <button class="{p}-button-thin btn-thin" type="button" data-gauge><span class="ktxt">+ charge</span></button>
  <span class="lbl">cooldown / charge</span>
</div></section>"""

    hud = f"""<section class="card" style="grid-column:1/-1"><h3>HUD mock (ghép nhiều component)</h3>
<em>thanh máu + slot góc phải + bar dọc + hotbar — kiểm tra tổng thể trên nền tối</em>
<div class="kit-hud">
  <div class="abs bars">{_bar(p, "hud-hp", "", "red", 100)}{_bar(p, "hud-mp", "", "blue", 70)}</div>
  <div class="abs top">
    {_slot(p, ITEMS[6], 1, "md", True)}{_slot(p, ITEMS[7], 1, "md")}{_slot(p, ITEMS[8], 4, "md")}
  </div>
  <div class="abs side">{_bar(p, "hud-st", "", "green", 60, vertical=True)}</div>
  <div class="abs bottom"><div class="kit-hotbar">{''.join(_slot(p, it, None, 'lg', i == 0, key=str(i + 1)) for i, it in enumerate(ITEMS[:4]))}</div></div>
</div></section>"""

    dialog = f"""<div class="kit-dialog" data-dlg="d1" hidden>
  <div class="{p}-panel-textured win">
    <button class="kit-close" type="button" data-dlg-close aria-label="close"></button>
    <i class="{p}-panel-header" style="display:block;margin:0 auto calc(4 * var(--u))"></i>
    <h4>Bán vật phẩm?</h4>
    <p>Golden armor &mdash; nhận 120 gold. Bạn có chắc không?</p>
    <div class="row" style="justify-content:center;margin-top:calc(10 * var(--u))">
      <button class="{p}-button btn" type="button" data-dlg-close><span class="ktxt">Cancel</span></button>
      <button class="{p}-button btn active" type="button" data-dlg-ok><span class="ktxt">Sell</span></button>
    </div>
  </div>
</div>
<div class="{p}-panel-slim kit-toast" data-toastbox><span data-toasttext>Saved!</span></div>"""

    head = f"""<h2 id="kit-title">UI kit tương tác — component của game mobile</h2>
<p class="kit-intro">Dev-only: mọi component dùng đúng class <code>.ui-*</code> do
<code>tools/ui-pack.py</code> sinh ra (border-image + sprite, scale theo <code>--s</code>).
Thử click / kéo / gõ phím: switch, checkbox, radio, tab (ngang-dọc-vuông), slider, input,
dialog, hotbar (phím <b>1..6</b>). Icon vật phẩm lấy từ <code>img/1/item-*.png</code>.</p>
<div class="kit-nav">
  <a href="#k-button">Buttons</a><a href="#k-switch">Switch</a><a href="#k-check">Checkbox/Radio</a>
  <a href="#k-tabs">Tabs</a><a href="#k-slider">Slider</a><a href="#k-input">Input</a>
  <a href="#k-bars">Bars</a><a href="#k-slots">Inventory</a><a href="#k-panel">Panel/Dialog</a>
  <a href="#k-gauge">Gauge</a><a href="#k-hud">HUD</a>
</div>"""

    body = "\n  ".join([buttons, switches, checks, tabs, slider, inputs, bars,
                        slots, panel, gauges, hud])
    return f'<div id="kit">\n{head}\n  {body}\n  {dialog}\n</div>'


# ---------------------------------------------------------------- script

KIT_SCRIPT = r"""
/* ---------------- UI KIT demo behaviour (dev only) ---------------- */
(function () {
  const $$ = (s, r = document) => Array.from((r || document).querySelectorAll(s));
  const $ = (s, r = document) => (r || document).querySelector(s);
  const scale = () => parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--s')) || 1;
  const setLog = (sel, txt) => { const el = $(sel); if (el) el.textContent = txt; };

  /* toast */
  const toast = txt => {
    const box = $('[data-toastbox]'); if (!box) return;
    const t = $('[data-toasttext]', box); if (t) t.textContent = txt;
    box.classList.add('on'); clearTimeout(box._t);
    box._t = setTimeout(() => box.classList.remove('on'), 1600);
  };

  /* buttons */
  $$('[data-count]').forEach(b => b.addEventListener('click', () => {
    const n = parseInt(b.dataset.count || '0', 10) + 1; b.dataset.count = n;
    const badge = $('[data-badge]', b); if (badge) badge.textContent = n;
    setLog('[data-log]', 'button clicks: ' + n);
  }));
  /* nút bị khoá: pipeline đã set pointer-events:none ⇒ không cần JS chặn ở đây */

  /* switches */
  const reportSwitch = () => {
    const parts = $$('[data-switch]').map(s => {
      const l = $('.lbl', s), i = $('i', s);
      return (l ? l.textContent : '?') + '=' + (i.classList.contains('checked') ? 'on' : 'off');
    });
    if (parts.length) setLog('[data-switchlog]', 'switch: ' + parts.join(', '));
  };
  $$('[data-switch], [data-switch-v]').forEach(sw => sw.addEventListener('click', () => {
    if (sw.hasAttribute('disabled')) return;
    const knob = $('i', sw); if (!knob) return;
    knob.classList.toggle('checked');
    sw.setAttribute('aria-checked', knob.classList.contains('checked') ? 'true' : 'false');
    if (!sw.hasAttribute('data-switch-v')) reportSwitch();
    else setLog('[data-switchlog]', 'switch dọc (toggle-v): ' + (knob.classList.contains('checked') ? 'on' : 'off'));
  }));

  /* checkbox + radio */
  const reportChecks = () => setLog('[data-checklog]',
    'checkbox: ' + $$('[data-check]').map(c => $('.lbl', c).textContent + '=' +
      ($('i', c).classList.contains('checked') ? 'on' : 'off')).join(' · '));
  $$('[data-check]').forEach(c => c.addEventListener('click', () => {
    const i = $('i', c); i.classList.toggle('checked');
    c.setAttribute('aria-checked', i.classList.contains('checked') ? 'true' : 'false');
    reportChecks();
  }));
  $$('[data-radio-group]').forEach(g => $$('[data-radio]', g).forEach(r => r.addEventListener('click', () => {
    $$('[data-radio]', g).forEach(o => { $('i', o).classList.remove('checked'); o.setAttribute('aria-checked', 'false'); });
    $('i', r).classList.add('checked'); r.setAttribute('aria-checked', 'true');
    setLog('[data-checklog]', 'radio ' + g.dataset.radioGroup + ': ' + $('.lbl', r).textContent);
  })));

  /* tabs (ngang / dọc / icon) */
  $$('[data-tabbar] [data-tab]').forEach(tab => tab.addEventListener('click', () => {
    const bar = tab.closest('[data-tabbar]');
    $$('[data-tab]', bar).forEach(o => {
      const on = o === tab;
      o.classList.toggle('active', on);
      $$('.e', o).forEach(e => e.classList.toggle('active', on));
      $$('i', o).forEach(i => i.classList.toggle('active', on));
      o.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    const key = tab.dataset.tab;
    $$('[data-tabpanel]').forEach(pnl => { pnl.hidden = pnl.dataset.tabpanel !== key; });
    setLog('[data-tablog]', 'tab active: ' + key + ' (' + (bar.dataset.tabbar === 'h' ? 'ngang'
      : bar.dataset.tabbar === 'v' ? 'dọc' : 'icon') + ')');
  }));

  /* sliders (kéo chuột / chạm) */
  const PAD = 8;                                  /* bề dày mũi tên của sprite track */
  $$('[data-slider]').forEach(sl => {
    const vertical = sl.classList.contains('v');
    const fill = $('.kit-fill', sl), thumb = $('.thumb', sl);
    const out = document.querySelector('[data-out="' + sl.dataset.slider + '"]');
    let v = sl.dataset.slider === 'v' ? 0.75 : sl.dataset.slider === 'h' ? 0.4 : 0.6;
    let dragging = false;
    const paint = () => {
      const span = 'calc(100% - ' + (2 * PAD) + ' * var(--u))';
      const at = 'calc(' + PAD + ' * var(--u) + ' + span + ' * ' + v + ')';
      if (!vertical) {
        fill.style.width = 'calc(' + span + ' * ' + v + ')';
        thumb.style.left = at; thumb.style.top = '50%'; thumb.style.transform = 'translate(-50%,-50%)';
      } else {
        fill.style.height = 'calc(' + span + ' * ' + v + ')';
        thumb.style.top = 'calc(100% - ' + at + ')'; thumb.style.left = '50%';
        thumb.style.transform = 'translate(-50%,-50%)';
      }
      if (out) out.textContent = Math.round(v * 100) + '%';
    };
    const fromEvent = e => {
      const r = sl.getBoundingClientRect(), s = scale();
      const p = (vertical ? (r.bottom - e.clientY) : (e.clientX - r.left)) - PAD * s;
      const len = (vertical ? r.height : r.width) - 2 * PAD * s;
      v = len > 0 ? Math.max(0, Math.min(1, p / len)) : 0;
      paint();
    };
    sl.addEventListener('pointerdown', e => { dragging = true; try { sl.setPointerCapture(e.pointerId); } catch (_) { /* synthetic */ } fromEvent(e); });
    sl.addEventListener('pointermove', e => { if (dragging) fromEvent(e); });
    sl.addEventListener('pointerup', () => { dragging = false; setLog('[data-log]', 'slider ' + sl.dataset.slider + ' = ' + Math.round(v * 100) + '%'); });
    sl.addEventListener('lostpointercapture', () => { dragging = false; });
    paint();
  });

  /* stepper */
  let step = 5;
  $$('[data-step]').forEach(b => b.addEventListener('click', () => {
    step = Math.max(0, Math.min(99, step + parseInt(b.dataset.step, 10)));
    const o = $('[data-step-out]'); if (o) o.textContent = step;
  }));

  /* chat bar */
  const chat = $('[data-chat]');
  const send = () => {
    if (!chat || !chat.value.trim()) return;
    const list = $('[data-chatlog]'); if (!list) return;
    const li = document.createElement('li'); li.textContent = 'you: ' + chat.value.trim();
    list.appendChild(li); chat.value = '';
    while (list.children.length > 4) list.removeChild(list.firstChild);
  };
  if (chat) chat.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
  const sendBtn = $('[data-send]'); if (sendBtn) sendBtn.addEventListener('click', send);

  /* progress bars */
  const setBar = (key, pct) => {
    const bar = document.querySelector('[data-bar="' + key + '"]'); if (!bar) return;
    pct = Math.max(0, Math.min(100, pct));
    bar.dataset.pct = pct;
    const vertical = bar.classList.contains('v');
    const fill = $('.fill', bar);
    if (fill) {
      if (vertical) fill.style.height = 'calc((100% - 30 * var(--u)) * ' + (pct / 100) + ')';
      else fill.style.width = 'calc((100% - 30 * var(--u)) * ' + (pct / 100) + ')';
    }
    const cap = $('.cap', bar);
    if (cap && bar.dataset.bar === 'hp' && !cap.dataset.base) cap.dataset.base = cap.textContent.replace(/\s*\d+%?\/?\d*$/, '');
    if (cap && bar.dataset.bar === 'hp') cap.textContent = 'HP ' + pct + '/100';
  };
  $$('[data-bar]').forEach(b => setBar(b.dataset.bar, parseInt(b.dataset.pct || '0', 10)));
  $$('[data-hp]').forEach(b => b.addEventListener('click', () => {
    const bar = $('[data-bar="hp"]'); if (!bar) return;
    const next = Math.max(0, Math.min(100, parseInt(bar.dataset.pct || '100', 10) + parseInt(b.dataset.hp, 10)));
    setBar('hp', next); toast('HP ' + next + '/100');
  }));

  /* gauge */
  $$('[data-gauge]').forEach(b => b.addEventListener('click', () => {
    const g = $('[data-gauge]') && $('.kit-gauge span'); if (!g) return;
    const cur = Math.max(0, Math.min(100, (parseInt(g.textContent, 10) || 0) + 17));
    g.textContent = cur + '%'; toast('charge ' + cur + '%');
  }));

  /* inventory + hotbar */
  const selectSlot = el => {
    const group = el.closest('.kit-slots, .kit-hotbar') || el.parentElement;
    $$('[data-slot]', group).forEach(o => o.classList.toggle('active', o === el));
    const hot = el.querySelector('u');
    setLog('[data-slotlog]', 'slot: ' + (el.title || '?') + (hot ? ' (phím ' + hot.textContent + ')' : ''));
  };
  $$('[data-slot]').forEach(s => s.addEventListener('click', () => selectSlot(s)));
  document.addEventListener('keydown', e => {
    const i = '123456'.indexOf(e.key);
    if (i < 0) return;
    const ae = document.activeElement;
    if (ae && /INPUT|TEXTAREA/.test(ae.tagName)) return;
    const slots = $$('.kit-hotbar [data-slot]');
    if (slots[i] && slots[i].offsetParent) { selectSlot(slots[i]); toast('hotbar ' + (i + 1) + ': ' + slots[i].title); }
  });

  /* dialog */
  const closeDlg = d => { if (d) d.hidden = true; };
  $$('[data-dialog]').forEach(b => b.addEventListener('click', () => {
    const d = document.querySelector('[data-dlg="' + b.dataset.dialog + '"]'); if (d) d.hidden = false;
  }));
  $$('[data-dlg-close]').forEach(b => b.addEventListener('click', () => closeDlg(b.closest('[data-dlg]'))));
  $$('[data-dlg-ok]').forEach(b => b.addEventListener('click', () => {
    closeDlg(b.closest('[data-dlg]')); toast('sold golden armor +120g');
  }));
  $$('[data-toast]').forEach(b => b.addEventListener('click', () => toast('Settings saved')));

  /* toolbar: chỉ hiện components */
  const bar = document.querySelector('.toolbar');
  if (bar && !document.getElementById('kitOnly')) {
    const btn = document.createElement('button');
    btn.id = 'kitOnly'; btn.textContent = 'Components only';
    btn.onclick = () => {
      const on = document.body.classList.toggle('components-only');
      btn.textContent = on ? 'Show slice gallery' : 'Components only';
      if (on) document.getElementById('kit').scrollIntoView();
    };
    bar.appendChild(btn);
  }
})();
"""


def kit_style() -> str:
    """CSS block for the lab page (inlined right after the lab's own <style>)."""
    return f"<style>{KIT_STYLE}</style>"


def kit_script() -> str:
    """Behaviour block appended to the lab page's <script>."""
    return KIT_SCRIPT
