#!/usr/bin/env python3
"""Sinh `client/ui-mockup.html` — trang để ARTIST tự xếp UI bằng sprite đã cắt.

Ý tưởng (theo yêu cầu): lấy 1 sprite làm **base của một bảng**, rescale, rồi tạo
col/row ở trong. Trang này cho phép:

  * chọn theme + scale (1x/2x/3x) — đúng bội số nguyên, không nội suy
  * đặt kích thước lưới (cols x rows, cell px), bật/tắt lưới toạ độ
  * kéo sprite từ palette vào ô, hoặc click để thả vào ô trống đầu tiên
  * chỉnh từng món: cột/hàng, colspan/rowspan, scale riêng, mode
    (fit / stretch / tile / 9-slice), state (active/disabled/...), nhãn, icon vật phẩm
  * thêm **BẢNG**: 1 sprite làm base + lưới ô bên trong (sprite ô, cell size, gap)
  * Export / Copy JSON — agent đọc file đó để dựng component thật

CSS scale: trang nạp `ui-slices.generated.css` đã sinh, **lọc lấy đúng khối 1x** rồi
scope vào `.mk-canvas`, nên canvas luôn là 1:1 pixel; việc phóng to do `zoom` đảm nhiệm
(integer + `image-rendering:pixelated` ⇒ sắc nét).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

# --------------------------------------------------------------------------- #
# sprite index
# --------------------------------------------------------------------------- #

ITEM_GLOB = "client/img/1/item-*.png"


def sprite_index(mf: dict, assets: dict, root: Path) -> dict:
    """{tên: {w, h, group, sheet, nine, states, themed}} theo thứ tự khai báo."""
    group = "OTHER"
    out: dict = {}
    for key, spec in mf["slices"].items():
        if key.startswith("_comment"):
            group = str(spec).split(" - ")[0].split(" -")[0].strip() or group
            continue
        if key.startswith("_"):
            continue
        x, y, w, h = spec["rect"]
        out[key] = {
            "w": w,
            "h": h,
            "group": group,
            "sheet": spec.get("sheet", "main"),
            "nine": bool(spec.get("nine", True)),
            "themed": bool(spec.get("themed", True)),
            "states": list((spec.get("states") or {}).keys()),
        }
    items = sorted(p.stem for p in (root / "client" / "img" / "1").glob("item-*.png"))
    out["@items"] = {"w": 16, "h": 16, "group": "ITEM (img/1/item-*)",
                     "sheet": "items", "nine": False, "themed": False, "states": []}
    return out, items


# --------------------------------------------------------------------------- #
# css: chỉ lấy khối 1x, scope vào .mk-canvas
# --------------------------------------------------------------------------- #

_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.S)


def scope_css(css: str, scope: str) -> str:
    """Thêm `scope ` vào trước mọi selector (bỏ comment + @rule)."""
    body = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = []
    for sel, decl in _RULE.findall(body):
        s = sel.strip()
        if not s or s.startswith("@"):
            continue
        parts = [f"{scope} {p.strip()}" for p in s.split(",") if p.strip()]
        out.append(", ".join(parts) + " {" + decl.rstrip() + "}")
    return "\n".join(out)


# --------------------------------------------------------------------------- #

PAGE_CSS = r"""
:root { color-scheme: dark; }
* { box-sizing: border-box; }
html, body { height: 100%; }
body { margin: 0; display: flex; flex-direction: column; height: 100vh;
  background: #14141a; color: #dfe3ea; font: 12px/1.45 system-ui, sans-serif; }

/* ---- top bar ---- */
.mk-top { display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  padding: 8px 12px; background: #1c1c24; border-bottom: 1px solid #2c2c38; }
.mk-top h1 { font: 600 14px/1 system-ui; margin: 0 8px 0 0; color: #8fd0ff; }
.mk-f { display: flex; align-items: center; gap: 4px; color: #8b93a3; }
.mk-f input[type=number] { width: 58px; }
.mk-f input[type=text] { width: 130px; }
input, select, button { font: inherit; color: #dfe3ea; background: #23232e;
  border: 1px solid #3a3a48; border-radius: 5px; padding: 3px 6px; }
input[type=text], input[type=number] { padding: 3px 6px; }
button { cursor: pointer; }
button:hover { background: #2c2c3a; }
button.pri { background: #2b6cb0; border-color: #3b82d6; color: #fff; font-weight: 600; }
button.pri:hover { background: #3182ce; }
.mk-sep { width: 1px; height: 22px; background: #33333f; }
.mk-sp { flex: 1; }

/* ---- body ---- */
.mk-body { flex: 1; display: grid; grid-template-columns: 232px 1fr 262px;
  min-height: 0; }
.mk-col { overflow: auto; }
.mk-left { background: #17171e; border-right: 1px solid #2c2c38; padding: 8px; }
.mk-right { background: #17171e; border-left: 1px solid #2c2c38; padding: 8px; }
.mk-center { overflow: auto; padding: 16px; background:
  linear-gradient(45deg, #16161c 25%, transparent 25%),
  linear-gradient(-45deg, #16161c 25%, transparent 25%),
  linear-gradient(45deg, transparent 75%, #16161c 75%),
  linear-gradient(-45deg, transparent 75%, #16161c 75%);
  background-color: #101015; background-size: 16px 16px;
  background-position: 0 0, 0 8px, 8px -8px, -8px 0; }

/* ---- palette ---- */
.mk-search { width: 100%; margin-bottom: 8px; }
.mk-grp { margin: 0 0 4px; }
.mk-grp > summary { cursor: pointer; padding: 4px 6px; border-radius: 5px;
  background: #1f1f29; color: #9aa3b2; font: 600 10px/1.6 system-ui;
  letter-spacing: .4px; text-transform: uppercase; user-select: none; }
.mk-grp[open] > summary { color: #8fd0ff; }
.mk-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 4px;
  padding: 6px 0; }
.mk-pal { display: flex; flex-direction: column; align-items: center; gap: 3px;
  padding: 5px 3px; background: #1d1d26; border: 1px solid #2e2e3a; border-radius: 5px;
  cursor: grab; user-select: none; }
.mk-pal:hover { border-color: #4a4a5e; background: #24242f; }
.mk-pal.sel { border-color: #3b82d6; box-shadow: 0 0 0 1px #3b82d6 inset; }
.mk-pal .th { height: 34px; display: flex; align-items: center; justify-content: center; }
.mk-pal .th > i { display: block; }
.mk-pal span { font: 9px/1.2 monospace; color: #9aa3b2; text-align: center;
  word-break: break-all; }

/* ---- canvas ---- */
.mk-canvas { position: relative; transform-origin: top left;
  outline: 1px solid #3a3a48; }
.mk-canvas.bg { background-color: #0d0d12; }
.mk-guide { position: absolute; inset: 0; pointer-events: none; }
.mk-guide i { position: absolute; }
.mk-guide .v { top: 0; bottom: 0; width: 1px; background: #ffffff14; }
.mk-guide .h { left: 0; right: 0; height: 1px; background: #ffffff14; }
.mk-guide b { position: absolute; font: 8px/1 monospace; color: #ffffff2e;
  padding: 1px 2px; }
.mk-item { position: absolute; cursor: move; outline: 1px dashed #4a4a5e00; }
.mk-item:hover { outline-color: #4a4a5e; }
.mk-item.sel { outline: 1px solid #3b82d6; }
.mk-item.lock { pointer-events: none; }
.mk-item > .bg { position: absolute; inset: 0; }
.mk-item > .lbl { position: absolute; inset: 0; display: flex; align-items: center;
  justify-content: center; font-family: 'GraphicPixel', monospace; color: #e8ddc6;
  text-shadow: 0 1px 0 #000; pointer-events: none; }
.mk-item > .ico { position: absolute; left: 50%; top: 50%; transform: translate(-50%,-50%);
  width: 16px; height: 16px; background-repeat: no-repeat; background-position: center;
  background-size: 100% 100%; image-rendering: pixelated; pointer-events: none; }
.mk-tbl { position: absolute; }
.mk-tbl > .cells { position: absolute; display: grid; }
.mk-tbl > .cells > i { background-repeat: no-repeat; background-position: center;
  background-size: 100% 100%; image-rendering: pixelated; }
.mk-drop { position: absolute; border: 2px solid #3b82d6; background: #3b82d622;
  pointer-events: none; }

/* ---- inspector ---- */
.mk-sec { margin-bottom: 12px; }
.mk-sec > h4 { margin: 0 0 6px; font: 600 10px/1.4 system-ui; color: #8fd0ff;
  letter-spacing: .4px; text-transform: uppercase; }
.mk-r { display: flex; align-items: center; gap: 6px; margin-bottom: 5px; }
.mk-r > label { flex: none; width: 74px; color: #8b93a3; font-size: 11px; }
.mk-r > input, .mk-r > select { flex: 1; min-width: 0; }
.mk-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; }
.mk-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; }
.mk-list { max-height: 220px; overflow: auto; border: 1px solid #2e2e3a;
  border-radius: 5px; }
.mk-li { display: flex; align-items: center; gap: 6px; padding: 4px 6px; cursor: pointer;
  border-bottom: 1px solid #22222c; font-size: 11px; }
.mk-li:last-child { border-bottom: 0; }
.mk-li:hover { background: #1f1f29; }
.mk-li.sel { background: #22384f; }
.mk-li .n { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mk-li .p { color: #8b93a3; font: 9px monospace; }
.mk-hint { color: #8b93a3; font-size: 11px; line-height: 1.5; }
.mk-hint code { background: #23232e; padding: 0 3px; border-radius: 3px; }
.mk-json { width: 100%; height: 150px; font: 10px/1.4 monospace; white-space: pre;
  overflow: auto; resize: vertical; }
.mk-toast { position: fixed; left: 50%; bottom: 18px; transform: translateX(-50%);
  background: #2b6cb0; color: #fff; padding: 6px 14px; border-radius: 6px;
  opacity: 0; transition: opacity .18s; pointer-events: none; z-index: 99; }
.mk-toast.on { opacity: 1; }
"""  # noqa: E501


PAGE_JS = r"""
const SPRITES = __SPRITES__;
const ITEMS = __ITEMS__;
const PREFIX = __PREFIX__;
const STATE_LIST = ['', 'active', 'pressed', 'disabled', 'checked', 'checked-disabled'];

let doc = {
  name: 'mockup-1', theme: 'dark', scale: 1,
  cols: 6, rows: 6, cell: 32, bg: true,
  items: []
};
let selId = null, uid = 1, thumbMode = false;

/* ------------------------------------------------------------------ utils */
const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
function toast(msg) {
  const t = $('#toast'); t.textContent = msg; t.classList.add('on');
  clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove('on'), 1400);
}
function spriteOf(n) { return n === '@items' || n.startsWith('item-') ? null : SPRITES[n]; }
function nativeSize(n) {
  if (n && n.startsWith('item-')) return { w: 16, h: 16 };
  const s = SPRITES[n]; return s ? { w: s.w, h: s.h } : { w: 16, h: 16 };
}
/* class .ui-<name> cho sprite trên atlas; icon vật phẩm là ảnh rời */
function cssClass(n) {
  if (!n) return '';
  if (n.startsWith('item-')) return '';
  return PREFIX + '-' + n;
}
function imgUrl(n) {
  return n && n.startsWith('item-') ? 'img/1/' + n + '.png' : '';
}
function itemBg(el, it) {
  const n = it.name; el.className = it.kind === 'table' ? '' : 'bg';
  el.style.backgroundImage = '';
  if (it.kind === 'table') return;
  const cls = cssClass(n);
  el.className = 'bg' + (cls ? ' ' + cls : '');
  STATE_LIST.forEach(s => s && el.classList.remove(s));
  if (it.state) it.state.split(' ').forEach(s => s && el.classList.add(s));
  const url = imgUrl(n);
  if (url) { el.style.backgroundImage = `url('${url}')`; }
  /* mode chỉ áp cho sprite KHÔNG 9-slice; 9-slice để border-image tự lo */
  const sp = spriteOf(n);
  const nine = sp ? sp.nine : false;
  if (!nine) {
    const sz = nativeSize(n);
    if (it.mode === 'tile') {
      el.style.backgroundSize = `${sz.w}px ${sz.h}px`;
      el.style.backgroundRepeat = 'repeat';
    } else if (it.mode === 'stretch') {
      el.style.backgroundSize = '100% 100%'; el.style.backgroundRepeat = 'no-repeat';
    } else {
      el.style.backgroundSize = 'auto'; el.style.backgroundRepeat = 'no-repeat';
      el.style.backgroundPosition = 'center';
    }
  } else {
    el.style.backgroundSize = ''; el.style.backgroundRepeat = '';
  }
}

/* ------------------------------------------------------------------ render */
function rect(it) {
  const g = doc.cell;
  return {
    left: it.c * g, top: it.r * g,
    width: it.cs * g, height: it.rs * g
  };
}
function render() {
  const cv = $('#canvas');
  const g = doc.cell;
  cv.style.width = doc.cols * g + 'px';
  cv.style.height = doc.rows * g + 'px';
  cv.style.zoom = doc.scale;
  cv.className = 'mk-canvas' + (doc.bg ? ' bg' : '');
  cv.setAttribute('data-theme-slot', '1');
  $$('.theme-slot').forEach(e => e.remove());
  applyTheme(cv);

  $('#items').innerHTML = '';
  doc.items.forEach(it => {
    const d = document.createElement('div');
    const r = rect(it);
    d.className = 'mk-item' + (it.id === selId ? ' sel' : '');
    d.style.left = r.left + 'px'; d.style.top = r.top + 'px';
    d.style.width = r.width + 'px'; d.style.height = r.height + 'px';
    d.dataset.id = it.id;
    if (it.kind === 'table') {
      d.classList.add('mk-tbl');
      const bg = document.createElement('i');
      bg.className = 'bg' + (cssClass(it.name) ? ' ' + cssClass(it.name) : '');
      d.appendChild(bg);
      if (it.cell) {
        const cells = document.createElement('i');
        cells.className = 'cells';
        const cs = it.cellSize || 32, gap = it.gap || 0;
        const n = Math.max(1, Math.floor((r.width - gap) / (cs + gap)));
        const m = Math.max(1, Math.floor((r.height - gap) / (cs + gap)));
        cells.style.gridTemplateColumns = `repeat(${n}, ${cs}px)`;
        cells.style.gridTemplateRows = `repeat(${m}, ${cs}px)`;
        cells.style.gap = gap + 'px';
        cells.style.left = '50%'; cells.style.top = '50%';
        cells.style.transform = 'translate(-50%,-50%)';
        for (let k = 0; k < n * m; k++) {
          const c = document.createElement('i');
          c.className = cssClass(it.cell);
          cells.appendChild(c);
        }
        d.appendChild(cells);
      }
    } else {
      const bg = document.createElement('i');
      itemBg(bg, it);
      d.appendChild(bg);
      if (it.label) {
        const l = document.createElement('span');
        l.className = 'lbl'; l.textContent = it.label; d.appendChild(l);
      }
      if (it.icon) {
        const ic = document.createElement('i');
        ic.className = 'ico';
        ic.style.backgroundImage = `url('${imgUrl(it.icon)}')`;
        d.appendChild(ic);
      }
    }
    d.addEventListener('mousedown', ev => { ev.stopPropagation(); select(it.id); });
    $('#items').appendChild(d);
  });
  drawGuides();
  renderInspector();
  renderList();
}
function applyTheme(el) {
  el.classList.remove('theme-green', 'theme-blue', 'theme-red', 'theme-white');
  if (doc.theme !== 'dark') el.classList.add('theme-' + doc.theme);
}
function drawGuides() {
  const cv = $('#guide'); cv.innerHTML = '';
  if (!$('#guides').checked) return;
  const g = doc.cell;
  for (let c = 0; c <= doc.cols; c++) {
    const i = document.createElement('i');
    i.className = 'v'; i.style.left = c * g + 'px'; cv.appendChild(i);
  }
  for (let r = 0; r <= doc.rows; r++) {
    const i = document.createElement('i');
    i.className = 'h'; i.style.top = r * g + 'px'; cv.appendChild(i);
  }
  if (g >= 20) for (let r = 0; r < doc.rows; r++) for (let c = 0; c < doc.cols; c++) {
    const b = document.createElement('b');
    b.textContent = c + ',' + r; b.style.left = (c * g + 2) + 'px';
    b.style.top = (r * g + 1) + 'px'; cv.appendChild(b);
  }
}

/* ------------------------------------------------------------------ palette */
function buildPalette() {
  const box = $('#palette'); box.innerHTML = '';
  const groups = {};
  Object.entries(SPRITES).forEach(([n, s]) => {
    if (n === '@items') return;
    (groups[s.group] = groups[s.group] || []).push(n);
  });
  groups['ITEM (img/1/item-*)'] = ITEMS;
  Object.entries(groups).forEach(([g, names]) => {
    const det = document.createElement('details');
    det.className = 'mk-grp'; det.open = ['PANELS', 'TABS', 'GRIDS', 'ICONS', 'SLOTS']
      .some(k => g.toUpperCase().includes(k));
    const sum = document.createElement('summary');
    sum.textContent = g + ' (' + names.length + ')'; det.appendChild(sum);
    const grid = document.createElement('div'); grid.className = 'mk-grid';
    names.forEach(n => {
      const b = document.createElement('div');
      b.className = 'mk-pal'; b.title = n; b.dataset.name = n;
      const th = document.createElement('div'); th.className = 'th';
      const s = nativeSize(n);
      if (n.startsWith('item-')) {
        const i = document.createElement('i');
        i.style.cssText = `width:${s.w}px;height:${s.h}px;background:url('${imgUrl(n)}') center/100% 100% no-repeat;image-rendering:pixelated`;
        th.appendChild(i);
      } else {
        const i = document.createElement('i');
        i.className = cssClass(n);
        const k = Math.min(3, Math.max(1, Math.floor(34 / Math.max(s.w, s.h))));
        i.style.cssText = `width:${s.w * k}px;height:${s.h * k}px`;
        th.appendChild(i);
      }
      const sp = document.createElement('span'); sp.textContent = n;
      b.appendChild(th); b.appendChild(sp);
      b.addEventListener('click', () => addSprite(n));
      b.draggable = true;
      b.addEventListener('dragstart', e => e.dataTransfer.setData('text/plain', n));
      grid.appendChild(b);
    });
    det.appendChild(grid); box.appendChild(det);
  });
}

/* ------------------------------------------------------------------ actions */
function firstFree(cs, rs) {
  for (let r = 0; r <= doc.rows - rs; r++)
    for (let c = 0; c <= doc.cols - cs; c++) {
      const bad = doc.items.some(o => !(o.c + o.cs <= c || c + cs <= o.c ||
                                        o.r + o.rs <= r || r + rs <= o.r));
      if (!bad) return { c, r };
    }
  return { c: 0, r: 0 };
}
function addSprite(name) {
  const s = nativeSize(name);
  const cs = Math.max(1, Math.ceil(s.w / doc.cell)), rs = Math.max(1, Math.ceil(s.h / doc.cell));
  const p = firstFree(cs, rs);
  doc.items.push({ id: uid++, kind: 'sprite', name, c: p.c, r: p.r, cs, rs,
                   scale: 1, mode: 'fit', state: '', label: '', icon: '' });
  selId = uid - 1; render();
}
function addTable() {
  const p = firstFree(doc.cols, doc.rows);
  doc.items.push({ id: uid++, kind: 'table', name: 'panel', cell: 'grid-cell-bracket',
                   cellSize: doc.cell, gap: 2, c: p.c, r: p.r, cs: doc.cols, rs: doc.rows });
  selId = uid - 1; render();
}
function select(id) { selId = id; render(); }
function cur() { return doc.items.find(o => o.id === selId) || null; }
function sorted(by) {
  const it = cur(); if (!it) return;
  const i = doc.items.indexOf(it), j = i + by;
  if (j < 0 || j >= doc.items.length) return;
  doc.items.splice(j, 0, doc.items.splice(i, 1)[0]); render();
}
function del() {
  const it = cur(); if (!it) return;
  doc.items.splice(doc.items.indexOf(it), 1); selId = null; render();
}
function clone() {
  const it = cur(); if (!it) return;
  const c = JSON.parse(JSON.stringify(it)); c.id = uid++; c.c = Math.min(c.c + c.cs, doc.cols - c.cs);
  doc.items.push(c); selId = c.id; render();
}

/* ------------------------------------------------------------------ inspector */
function renderInspector() {
  const box = $('#insp'); box.innerHTML = '';
  const it = cur();
  if (!it) {
    box.innerHTML = '<p class="mk-hint">Chọn một món trên canvas, hoặc click sprite ở palette trái để thêm.</p>';
    return;
  }
  const sec = (title, rows) => {
    const d = document.createElement('div'); d.className = 'mk-sec';
    d.innerHTML = '<h4>' + title + '</h4>'; rows.forEach(r => d.appendChild(r));
    box.appendChild(d);
  };
  const row = (label, el) => {
    const d = document.createElement('div'); d.className = 'mk-r';
    const l = document.createElement('label'); l.textContent = label;
    d.appendChild(l); d.appendChild(el); return d;
  };
  const num = (label, key, min, max) => {
    const i = document.createElement('input');
    i.type = 'number'; i.min = min; i.max = max; i.value = it[key];
    i.oninput = () => { it[key] = Math.max(min, Math.min(max, +i.value || min)); render(); };
    return row(label, i);
  };
  const sel = (label, key, opts) => {
    const s = document.createElement('select');
    s.innerHTML = opts.map(o => `<option value="${o[0]}"${it[key] === o[0] ? ' selected' : ''}>${o[1]}</option>`).join('');
    s.onchange = () => { it[key] = s.value; render(); };
    return row(label, s);
  };

  const nameRow = document.createElement('div'); nameRow.className = 'mk-r';
  nameRow.innerHTML = `<label>sprite</label><b style="flex:1;font:11px monospace">${it.name}</b>`;
  sec(it.kind === 'table' ? 'Bảng (table)' : 'Sprite', [nameRow,
    num('cột (c)', 'c', 0, doc.cols - 1), num('hàng (r)', 'r', 0, doc.rows - 1),
    num('colspan', 'cs', 1, doc.cols), num('rowspan', 'rs', 1, doc.rows)]);

  if (it.kind === 'table') {
    const cellSel = document.createElement('select');
    const opts = [''].concat(Object.keys(SPRITES).filter(n => n.startsWith('grid-') || n.startsWith('slot')));
    cellSel.innerHTML = opts.map(o => `<option value="${o}"${it.cell === o ? ' selected' : ''}>${o || '— không có ô —'}</option>`).join('');
    cellSel.onchange = () => { it.cell = cellSel.value; render(); };
    sec('Ô bên trong', [row('sprite ô', cellSel), num('cell px', 'cellSize', 4, 96),
                        num('gap px', 'gap', 0, 16)]);
  } else {
    sec('Hiển thị', [
      sel('mode', 'mode', [['fit', 'fit (đúng cỡ)'], ['stretch', 'stretch (kéo)'],
                           ['tile', 'tile (lặp)']]),
      sel('state', 'state', [['', '—'], ['active', 'active'], ['pressed', 'pressed'],
                             ['disabled', 'disabled'], ['checked', 'checked'],
                             ['checked-disabled', 'checked-disabled']]),
      (() => { const i = document.createElement('input'); i.type = 'text';
        i.placeholder = 'nhãn…'; i.value = it.label || '';
        i.oninput = () => { it.label = i.value; render(); }; return row('nhãn', i); })(),
      (() => { const s = document.createElement('select');
        s.innerHTML = ['<option value="">— icon —</option>']
          .concat(ITEMS.map(n => `<option value="${n}"${it.icon === n ? ' selected' : ''}>${n}</option>`)).join('');
        s.onchange = () => { it.icon = s.value; render(); }; return row('icon', s); })(),
    ]);
  }

  const acts = document.createElement('div'); acts.className = 'mk-3';
  [['◀ trước', () => sorted(-1)], ['▶ sau', () => sorted(1)],
   ['⧉ nhân bản', clone], ['✕ xoá', del]].forEach(([t, f]) => {
    const b = document.createElement('button'); b.textContent = t; b.onclick = f;
    acts.appendChild(b);
  });
  const d = document.createElement('div'); d.className = 'mk-sec';
  d.appendChild(acts); box.appendChild(d);
}
function renderList() {
  const box = $('#list'); box.innerHTML = '';
  doc.items.forEach(it => {
    const d = document.createElement('div');
    d.className = 'mk-li' + (it.id === selId ? ' sel' : '');
    d.innerHTML = `<span class="n">${it.name}</span><span class="p">${it.c},${it.r}</span>`;
    d.onclick = () => select(it.id);
    box.appendChild(d);
  });
}

/* ------------------------------------------------------------------ io */
function exportDoc() { return JSON.parse(JSON.stringify(doc)); }
function setDoc(o) {
  doc = Object.assign({ name: 'mockup-1', theme: 'dark', scale: 1, cols: 6, rows: 6,
                        cell: 32, bg: true, items: [] }, o);
  uid = 1 + doc.items.reduce((m, i) => Math.max(m, i.id || 0), 0);
  selId = null; syncTop(); render();
}
function syncTop() {
  $('#name').value = doc.name; $('#theme').value = doc.theme; $('#scale').value = doc.scale;
  $('#cols').value = doc.cols; $('#rows').value = doc.rows; $('#cell').value = doc.cell;
  $('#bgc').checked = doc.bg;
}
function toastJson() {
  $('#json').value = JSON.stringify(exportDoc(), null, 1);
  toast('Đã xuất JSON — copy dán cho agent');
}

/* ------------------------------------------------------------------ wire */
function wire() {
  $('#name').oninput = e => { doc.name = e.target.value; };
  $('#theme').onchange = e => { doc.theme = e.target.value; render(); };
  $('#scale').onchange = e => { doc.scale = +e.target.value; render(); };
  $('#cols').oninput = e => { doc.cols = Math.max(1, +e.target.value || 1); render(); };
  $('#rows').oninput = e => { doc.rows = Math.max(1, +e.target.value || 1); render(); };
  $('#cell').oninput = e => { doc.cell = Math.max(4, +e.target.value || 32); render(); };
  $('#bgc').onchange = e => { doc.bg = e.target.checked; render(); };
  $('#guides').onchange = drawGuides;
  $('#addTable').onclick = addTable;
  $('#del').onclick = del;
  $('#export').onclick = toastJson;
  $('#copy').onclick = () => { toastJson();
    navigator.clipboard && navigator.clipboard.writeText($('#json').value); };
  $('#load').onclick = () => { try { setDoc(JSON.parse($('#json').value)); toast('Đã nạp JSON'); }
    catch (e) { toast('JSON lỗi: ' + e.message); } };
  $('#clear').onclick = () => { doc.items = []; selId = null; render(); toastJson(); };

  $('#search').oninput = e => {
    const q = e.target.value.toLowerCase();
    $$('.mk-pal').forEach(b => {
      const on = !q || b.dataset.name.toLowerCase().includes(q);
      b.style.display = on ? '' : 'none';
    });
    $$('.mk-grp').forEach(g => { if (q) g.open = true; });
  };

  const cv = $('#canvas');
  cv.addEventListener('dragover', e => { e.preventDefault(); });
  cv.addEventListener('drop', e => {
    e.preventDefault();
    const name = e.dataTransfer.getData('text/plain'); if (!name) return;
    const s = nativeSize(name);
    const cs = Math.max(1, Math.ceil(s.w / doc.cell)), rs = Math.max(1, Math.ceil(s.h / doc.cell));
    const b = cv.getBoundingClientRect();
    const c = Math.max(0, Math.min(doc.cols - cs,
      Math.floor((e.clientX - b.left) / doc.scale / doc.cell)));
    const r = Math.max(0, Math.min(doc.rows - rs,
      Math.floor((e.clientY - b.top) / doc.scale / doc.cell)));
    doc.items.push({ id: uid++, kind: 'sprite', name, c, r, cs, rs, scale: 1,
                     mode: 'fit', state: '', label: '', icon: '' });
    selId = uid - 1; render();
  });

  /* kéo món trên canvas */
  let drag = null;
  $('#items').addEventListener('mousedown', e => {
    const el = e.target.closest('.mk-item'); if (!el) return;
    const it = cur(); if (!it) return;
    drag = { it, x: e.clientX, y: e.clientY, c: it.c, r: it.r };
    e.preventDefault();
  });
  window.addEventListener('mousemove', e => {
    if (!drag) return;
    const dc = Math.round((e.clientX - drag.x) / doc.scale / doc.cell);
    const dr = Math.round((e.clientY - drag.y) / doc.scale / doc.cell);
    const it = drag.it;
    const c = Math.max(0, Math.min(doc.cols - it.cs, drag.c + dc));
    const r = Math.max(0, Math.min(doc.rows - it.rs, drag.r + dr));
    if (c !== it.c || r !== it.r) { it.c = c; it.r = r; render(); }
  });
  window.addEventListener('mouseup', () => { drag = null; });

  cv.addEventListener('mousedown', e => { if (e.target === cv) { selId = null; render(); } });
  window.addEventListener('keydown', e => {
    const it = cur(); if (!it) return;
    if (e.key === 'Delete' || e.key === 'Backspace') { if (e.target.tagName !== 'INPUT') { del(); e.preventDefault(); } }
    if (e.key === 'Escape') { selId = null; render(); }
    const step = e.shiftKey ? 1 : 1;
    if (e.key === 'ArrowLeft' && it.c > 0) { it.c -= step; render(); }
    if (e.key === 'ArrowRight' && it.c < doc.cols - it.cs) { it.c += step; render(); }
    if (e.key === 'ArrowUp' && it.r > 0) { it.r -= step; render(); }
    if (e.key === 'ArrowDown' && it.r < doc.rows - it.rs) { it.r += step; render(); }
  });

  /* nháp mẫu = đúng kiểu trong ed.png: 3 nắp tab, thanh ngang, rail dọc, lưới ô */
  const DEMO = {
    name: 'inventory-window', theme: 'dark', scale: 2,
    cols: 6, rows: 8, cell: 32, bg: true,
    items: [
      { id: 1, kind: 'sprite', name: 'tab-cap-top', c: 2, r: 0, cs: 1, rs: 1, mode: 'fit', state: '', label: '', icon: '' },
      { id: 2, kind: 'sprite', name: 'tab-cap-top', c: 3, r: 0, cs: 1, rs: 1, mode: 'fit', state: '', label: '', icon: '' },
      { id: 3, kind: 'sprite', name: 'tab-cap-top', c: 4, r: 0, cs: 1, rs: 1, mode: 'fit', state: 'active', label: '', icon: '' },
      { id: 4, kind: 'sprite', name: 'slider-track-h', c: 1, r: 1, cs: 5, rs: 1, mode: 'stretch', state: '', label: '', icon: '' },
      { id: 5, kind: 'sprite', name: 'slider-track-v', c: 0, r: 2, cs: 1, rs: 6, mode: 'stretch', state: '', label: '', icon: '' },
      { id: 6, kind: 'table', name: 'panel', cell: 'grid-cell-bracket', cellSize: 32, gap: 2, c: 1, r: 2, cs: 5, rs: 6 }
    ]
  };
  $('#demo').onclick = () => { setDoc(DEMO); toastJson(); };
}

buildPalette(); syncTop(); wire(); $('#demo').click();  /* mở trang là có sẵn mẫu */
"""


def generate(mf: dict, assets: dict, root: Path, css_1x: str) -> str:
    """`css_1x` là khối 1x của BỘ MẶC ĐỊNH (trang chỉ dựng ở bộ đó)."""
    sprites, items = sprite_index(mf, assets, root)
    prefix = mf["css"]["prefix"]
    # CSS sinh ra dùng url('../img/...') vì nằm ở client/css/. Nhúng inline vào
    # client/ui-mockup.html thì phải bỏ '../'. Scope 2 lần: palette (ngoài canvas)
    # và canvas — để preview trong palette cũng có background/border-image.
    scoped_pal = scope_css(css_1x, ".mk-pal").replace("../img/", "img/")
    scoped = scope_css(css_1x, ".mk-canvas").replace("../img/", "img/")
    js = (PAGE_JS
          .replace("__SPRITES__", json.dumps(sprites, ensure_ascii=False))
          .replace("__ITEMS__", json.dumps(items, ensure_ascii=False))
          .replace("__PREFIX__", json.dumps(prefix)))
    themes = "".join(f'<option value="{t}">{t}</option>'
                     for t in mf["themes"]["offsets"])
    return f"""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UI Mockup — {mf["name"]}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<style>
/* CSS sinh ra, ép về đúng khối 1x và scope vào .mk-canvas ⇒ canvas luôn 1:1 pixel,
   phóng to bằng `zoom` (bội số nguyên + pixelated ⇒ không nội suy). */
{scoped}
/* bản scope cho palette (preview sprite ngoài canvas) */
{scoped_pal}
</style>
<style>{PAGE_CSS}</style>
</head>
<body>
<div class="mk-top">
  <h1>UI Mockup</h1>
  <div class="mk-f"><label>tên</label><input id="name" type="text"></div>
  <div class="mk-f"><label>theme</label><select id="theme">{themes}</select></div>
  <div class="mk-f"><label>scale</label>
    <select id="scale"><option>1</option><option>2</option><option>3</option></select></div>
  <span class="mk-sep"></span>
  <div class="mk-f"><label>cols</label><input id="cols" type="number" min="1" max="40"></div>
  <div class="mk-f"><label>rows</label><input id="rows" type="number" min="1" max="40"></div>
  <div class="mk-f"><label>cell</label><input id="cell" type="number" min="4" max="128"></div>
  <span class="mk-f"><input id="guides" type="checkbox" checked><label>lưới</label></span>
  <span class="mk-f"><input id="bgc" type="checkbox" checked><label>nền</label></span>
  <span class="mk-sep"></span>
  <button id="addTable">+ Bảng</button>
  <button id="demo">Mẫu (như ed.png)</button>
  <button id="del">Xoá món</button>
  <span class="mk-sp"></span>
  <button id="export">Xuất</button>
  <button class="pri" id="copy">Copy JSON</button>
  <button id="load">Nạp</button>
  <button id="clear">Trắng</button>
</div>

<div class="mk-body">
  <div class="mk-col mk-left">
    <input id="search" class="mk-search" type="text" placeholder="tìm sprite…">
    <div id="palette"></div>
  </div>

  <div class="mk-col mk-center">
    <div class="mk-canvas" id="canvas">
      <div class="mk-guide" id="guide"></div>
      <div id="items"></div>
    </div>
  </div>

  <div class="mk-col mk-right">
    <div class="mk-sec">
      <h4>Món đang chọn</h4>
      <div id="insp"></div>
    </div>
    <div class="mk-sec">
      <h4>Danh sách ({len(sprites)} sprite)</h4>
      <div class="mk-list" id="list"></div>
    </div>
    <div class="mk-sec">
      <h4>JSON (agent đọc file này)</h4>
      <textarea id="json" class="mk-json" spellcheck="false"></textarea>
      <p class="mk-hint"><code>kind:"table"</code> = 1 sprite làm base + lưới ô bên trong
      (<code>cellSize</code>, <code>gap</code>). <code>kind:"sprite"</code> = 1 sprite đặt
      vào ô, có <code>mode</code> fit/stretch/tile + <code>state</code>.</p>
    </div>
  </div>
</div>
<div class="mk-toast" id="toast"></div>
<script>{js}</script>
</body>
</html>
"""
