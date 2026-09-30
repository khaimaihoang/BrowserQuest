# SESSION: UI Slice Pipeline (Minifantasy → game) · Mockup cho artist · Trục BỘ

Tóm tắt kiến trúc, quy chuẩn dữ liệu và tiến trình của **pipeline cắt UI Minifantasy** cho
**BrowserQuest**. Phiên trước (Paperdoll Minifantasy) đã được lưu ở
[`sessions/1_KIẾN_TRÚC_TÍCH_HỢP_PAPERDOLL_MINIFANTASY_TECHNICAL_SPECIFICATION.md`](file:///D:/Develop/Projects/BrowserQuest/sessions/1_KI%E1%BA%BEN_TR%C3%9AC_T%C3%8DCH_H%E1%BB%A2P_PAPERDOLL_MINIFANTASY_TECHNICAL_SPECIFICATION.md).

Tài liệu chuẩn (canonical) của pipeline: [`docs/ui-slice-pipeline.md`](file:///D:/Develop/Projects/BrowserQuest/docs/ui-slice-pipeline.md).

---

## 1. Mục tiêu & phạm vi

Cho **artist 2D** thiết kế UI từ atlas Minifantasy rồi dùng thẳng trong game:

1. Manifest khai vùng atlas → packer cắt thành sprite có tên + sinh CSS.
2. Artist tự xếp UI trong **trang mockup** → export JSON → agent dựng component thật.
3. Pixel-perfect, touch-first, không phụ thuộc công cụ ngoài (Python + Pillow).

---

## 2. Nguồn dữ liệu

### 2.1 Ba sheet

| Sheet | File | Kích thước | Vai trò |
|---|---|---|---|
| `main` | `Grim_Minifantasy_UI/_grim_ui.png` | 4528×1984 | khung/panel/button/tab/slot/bar/divider/decoration |
| `icons` | `_General_UI_Resources/Icons/_icons.png` | 576×432 | icon 8×8 trên lưới 16px (person, craft, orb, heart, bolt…) |
| `grids` | `_General_UI_Resources/Grids/grids.png` | 1360×496 | ô lưới item (5 style × 5 tông màu, stride 272) |

`sheets` khai trong manifest; slice chọn sheet bằng `"sheet": "<tên>"`. Sheet `themed:false`
= rect tuyệt đối, xuất 1 lần, **không** cộng `themes.offsets`.

### 2.2 Trục THEME (x) — 5 màu

`_grim_ui.png` lặp ngang **5 cột**, stride **912px**: `dark(0)` `green(912)` `blue(1824)`
`red(2736)` `white(3648)`. CSS: `.theme-green .ui-panel { … }`.

### 2.3 Trục BỘ / SET (y) — **3 bộ mỗi theme**

Mỗi cột theme chứa **3 bộ asset xếp dọc**, cùng nhóm nhưng **hoạ tiết khác**:

| Bộ | Hoạ tiết | Ghi chú |
|---|---|---|
| **`set1`** *(mặc định)* | **trơn** — khung chữ nhật, không góc, thanh mảnh, không boss | `bar-h` 48×**12**, `panel` 48×**44**, `divider` 3px |
| **`set2`** | **hoa thị (fan)** — nút 4 góc, hoa thị trên/dưới, boss ở tâm thanh | `bar-h` 48×**20** |
| **`set3`** | **gai (spike)** — gai góc, hoa văn chữ thập giữa | `divider` **7px** |

**5 theme × 3 bộ = 15 bộ.** Toạ độ nhóm **giống hệt nhau về x**; chỉ khác y.

Offset đo từ `_Use_Guidelines/use_guideline_layer.png` (khung nhóm **tô màu riêng cho từng
bộ** → đọc bbox theo màu) rồi đo lại trên art thật:

| Nhóm | set1↔set2 | set1↔set3 |
|---|---|---|
| PANELS · TABS | 540 | 1080 |
| DIVIDERS · SLIDERS · RESOURCES | 544 | 1088 |
| CHECK_BOXES | 544 | 1086 |
| TOGGLE_BUTTONS · SLOTS | 544 | 1087 |
| PUSH_BUTTONS | 544 | 1084 |

> **Bài học lớn:** manifest ban đầu chỉ cắt **bộ 2**, nhưng `button`/`button-slim` lại lấy từ
> **bộ 1** ⇒ asset lẫn hai bộ hoa văn. Đã **rebase toàn bộ về `set1`**.

### 2.4 Nhóm trong `set_use_guidelines.png`

`PANELS` · `DIVIDERS` · `SLIDERS` · `CHECK BOXES` · `TOGGLE BUTTONS` · `SLOTS` · `TABS` ·
`RESOURCE'S BARS & CONTAINERS` · `PUSH BUTTONS` · `DECORATION` · `WINDOW BUTTONS`.
Bản art thật ở **y ≥ 544** trong block gốc (phần trên là bản outline).

**Bài học:** tên slice phải bám **nhãn nhóm trong guideline**, không đoán theo hình dạng.
Đã từng đặt sai: `divider-fancy-*` (thật ra thuộc SLIDERS), `tab-icon-1..4` (thật ra là
**4 NẮP khung tab**, đã đổi thành `tab-cap-top/left/right/bottom`).

---

## 3. Manifest — [`tools/ui/slices.json`](file:///D:/Develop/Projects/BrowserQuest/tools/ui/slices.json)

### 3.1 Top-level

| Khoá | Ý nghĩa |
|---|---|
| `source` | atlas chính (= `sheets.main.source`) |
| `sheets` | `{tên: {source, themed}}` — sheet phụ |
| `sets` | `{default, offsets: {set1:0,set2:544,set3:1088}, export: ["set1"]}` |
| `themes` | `{default: dark, offsets: {…}}` |
| `scales` | `[1,2,3]` — upscale NEAREST |
| `output` | `image` / `css` / `lab` / `mockup` / `preview` |
| `css.prefix` | tiền tố class (`ui`) |

### 3.2 Mỗi slice

```jsonc
"button": {
  "sheet": "main",              // sheet chứa rect (mặc định "main")
  "rect": [208, 108, 48, 48],   // [x,y,w,h] ở BỘ MẶC ĐỊNH (set1), theme mặc định
  "nine": true,                 // true = 9-slice (border-image), false = sprite rời
  "slice": 8,                   // bề dày viền: int, hoặc [t,r,b,l] cho thanh mỏng
  "repeat": "repeat",           // border-image-repeat
  "stretch": "x",               // 'x' chỉ kéo ngang / 'y' chỉ kéo dọc
  "states": { "pressed": [...], "disabled": [...] },
  "alias": { "hover": "active" },        // map selector sang sprite có sẵn
  "hoverUses": "active",                 // hover desktop, bọc @media (hover:hover)
  "disabledFilter": "brightness(.72) saturate(.8)",
  "overlays": [{ "rect": [...], "anchor": "center" }],   // hoạ tiết tâm (chỉ bộ 2/3)
  "flatten": true,              // làm phẳng dải giữa cho tile sạch
  "themed": false,              // 1 bản, không theo theme (resource fills)
  "sets": false,                // 1 bản, không theo bộ (sheet tĩnh, decoration…)
  "setDelta": { "set2": -4 },   // lệch thêm so với offsets chung
  "setRect": { "set2": [...] }  // khác CẢ kích thước → khai rect đầy đủ
}
```

Khoá `_comment_*` bị packer bỏ qua (chia nhóm cho dễ đọc + làm nhãn nhóm cho palette).

---

## 4. Sản phẩm hiện có

```
96 slice (+36 state) × 5 theme × 3 scale  →  1488 ảnh   (đang xuất bộ set1)
```

| Nhóm | Slice tiêu biểu |
|---|---|
| PANELS | `panel` `panel-slim` `panel-textured` `panel-header` `panel-title` |
| PUSH BUTTONS | `button` `button-slim` `button-thin` `button-tiny` (+pressed/disabled) |
| SLIDERS | `slider-track-h/v` `slider-thumb-h/v` |
| DIVIDERS | `divider-h` `divider-v` |
| SLOTS | `slot` `slot-sm` `slot-md` `slot-wide` `slot-pill` `slot-lg` |
| CHECK BOXES | `radio` `checkbox` (+pressed/checked/checked-pressed) |
| TOGGLE BUTTONS | `toggle-h` `toggle-v` (+pressed/checked/checked-pressed) |
| TABS | `tab-cap-top/left/right/bottom` (**nắp** 16×12 / 12×16, +active) · `tab-top/bottom/left/right` (**cạnh** 48×12 / 12×48) |
| RESOURCES | `bar-h[-md/-sm/-xs]` `bar-v[-md/-sm/-xs]` `container[-md/-sm]` |
| RESOURCE FILLS | `bar-fill-{red,blue,gold,green,purple}` `bar-fill-v-{…}` *(themed:false)* |
| DECORATION | `decoration-top-arch/-bar` `-bottom-arch/-bar` `decoration-side-1..4` |
| WINDOW BUTTONS | `window-btn-min/-max/-close` (+hover/pressed) |
| ICONS *(sheet `icons`)* | 22 icon: `icon-person` `icon-craft` `icon-orb` `icon-heart` `icon-bolt` `icon-shield` `icon-swords` `icon-plus` `icon-drop` `icon-chest` `icon-pickaxe` … |
| GRIDS *(sheet `grids`)* | `grid-cell` `grid-cell-sm` `grid-cell-bracket` `grid-3x3` `grid-6x6` (+`-ornate`) |

> `bar-fill-*` và 2 sheet phụ **không** thuộc bộ nào (`sets:false` / sheet tĩnh).

---

## 5. Công cụ

| File | Vai trò |
|---|---|
| [`tools/ui-pack.py`](file:///D:/Develop/Projects/BrowserQuest/tools/ui-pack.py) | packer: validate → cắt ảnh → sinh CSS → sinh lab/editor/mockup → dọn file rác |
| [`tools/uilab_kit.py`](file:///D:/Develop/Projects/BrowserQuest/tools/uilab_kit.py) | UI kit tương tác nhúng vào lab (button/switch/check/tab/slider/bar/slot/panel/gauge/HUD + section **Mockup 1**) |
| [`tools/ui-mockup.py`](file:///D:/Develop/Projects/BrowserQuest/tools/ui-mockup.py) | sinh **trang mockup cho artist** |
| [`tools/make-slice-editor.py`](file:///D:/Develop/Projects/BrowserQuest/tools/make-slice-editor.py) | sinh **editor kéo slice** (theme + overlays) |
| [`tools/ui/probe-disabled.html`](file:///D:/Develop/Projects/BrowserQuest/tools/ui/probe-disabled.html) | probe hồi quy: control disabled phải **nuốt** click |

### 5.1 Lệnh

```bash
npm run ui:pack                        # validate + xuất tất cả
python tools/ui-pack.py --no-write     # chỉ validate
python tools/ui-pack.py --themes dark  # 1 theme
npm run watch:client                   # http://localhost:8008/
```

| Trang | URL |
|---|---|
| Gallery slice + UI kit | `ui-lab.html` (`?only=1` = chỉ kit, `#k-mock` = mockup 1) |
| Editor kéo slice | `ui-slice-editor.html` |
| **Mockup cho artist** | `ui-mockup.html` |

### 5.2 Output

```
client/img/{1,2,3}/ui/*.png          sprite theo scale (NEAREST ×1/×2/×3)
client/css/ui-slices.generated.css   class .ui-* + state + theme + set + 3 scale
client/ui-lab.html                   gallery + UI kit (dev-only)
client/ui-slice-editor.html          editor kéo slice
client/ui-mockup.html                trang mockup cho artist
tools/ui/out/{preview.png,generated.json}
```

`client/css/main.css` đã `@import 'ui-slices.generated.css'` ⇒ class dùng được ngay.

---

## 6. Mô hình STATE — touch-first

**Nguyên tắc: sprite SÁNG = `active`/enabled, sprite TỐI = `disabled`.** Không có hover trên mobile.

| State | Nghĩa | Selector |
|---|---|---|
| `pressed` | enabled + đang nhấn | `:active`, `.pressed` — **kèm `:not(:disabled):not([disabled]):not(.disabled):not([aria-disabled])`** |
| `disabled` | vô hiệu = **KHOÁ CỨNG** (sprite tối, nhấn không đổi) | `:disabled`, `[disabled]`, `.disabled`, `[aria-disabled='true']` + `cursor:default` |
| `active` | bật / đang chọn | `.active`, `[aria-selected]`, `[aria-pressed]` |
| `active-pressed` | active + đang nhấn | `.active.pressed`, `.active:active` |
| `checked` | on | `:checked`, `.checked`, `[aria-checked='true']` |
| `checked-disabled` | on + vô hiệu | `:checked:disabled`, `.checked.disabled`, … |
| `hover` | **chỉ desktop** | `:hover`, `.hover` — **bọc `@media (hover: hover)`** |

### 6.1 Disabled phải NUỐT click (bug đã gặp, đã sửa)

`pointer-events:none` làm control trong suốt với chuột ⇒ cú click **xuyên qua**, rơi vào
canvas/cha phía sau (nhân vật vẫn di chuyển, hàng cha vẫn toggle). Probe headless xác nhận:
`elementFromPoint` trên ô disabled trả về **phần tử CHA**.

**Chuẩn:** giữ `pointer-events:auto` + `cursor:default` (nuốt click) **và** guard ở JS —
CSS không chặn được bubbling. Module dùng chung cho repo khác:
`T004/Assets/JavaScript/modules/DisabledGuard.js` (xem `.agents/rules/ui-code.md` của T004).

---

## 7. Quy tắc pixel-perfect (bắt buộc)

1. Scale **nguyên** ×1/×2/×3, `image-rendering: pixelated` — không nội suy.
2. `border-image-repeat: repeat` (không `stretch`) cho 9-slice.
3. `border-image-slice` **bằng đúng** `border-width` (theo ×scale).
4. `rect` phải **khít bao nội dung** — lệch vài px là xêng khung 9-slice. (Đã siết 42/42
   slice main về **khít 0px**.)
5. **`slice` chống sọc:** `slice` phải phủ hết bề dày hoạ tiết viền; bước lặp
   (`w-l-r` / `h-t-b`) phải chia hết chu kỳ hoạ tiết atlas (**32px**). Sprite 48px dùng
   `slice: 8`; `7` cho 34px ⇒ lệch pha 2px ⇒ **sọc đậm lặp lại** (chỉ thấy ở theme sáng).
6. Sprite **cố định** (`nine:false`) dùng ở kích thước gốc, không kéo giãn.

---

## 8. Nhật ký commit (phiên này)

| Commit | Nội dung |
|---|---|
| `0713ade2` | **fix**: disabled nuốt click (bỏ `pointer-events:none`) + lab/preview scale đúng media query (hết crop ở 2x/3x) + probe hồi quy |
| `e8547115` | **feat**: pipeline **đa sheet** (`icons` + `grids`) · đổi tên `tab-icon-*` → `tab-cap-*` · dọn **135 file rác** |
| `1f77baef` | **feat**: **trang mockup cho artist** (`ui-mockup.html`) + fix `#shades`/palette scope |
| `8af4be8c` | **fix**: phát hiện **3 BỘ/theme**, rebase về **bộ 1** (mặc định) → hết lẫn hoa văn; siết rect khít 0px; bỏ overlays sai |
| `07edfef5` | **feat**: **trục `sets`** trong packer + 2 nhóm còn thiếu (`DECORATION`, `WINDOW BUTTONS`) → 96 slice |

### 8.1 Bug đã sửa trong phiên

- **Disabled xuyên click** — `pointer-events:none` → `cursor:default` + JS guard.
- **Dọn rác không chạy sau clone** — index dọn rác nằm ở `tools/ui/out/` (**gitignored**) ⇒
  135 file của manifest cũ sống mãi. Nay packer **quét luôn** `client/img/{1,2,3}/ui/*.png`.
- **Lẫn bộ hoa văn** — rebase về `set1` + siết rect.
- **Mockup page không render** — nút `#shades` không tồn tại làm `wire()` ném lỗi.
- **Palette vô hình** — CSS scope thiếu; inline CSS phải bỏ `../` trong `url()`.

---

## 9. TODO

### P0 — Mở bộ `set2` / `set3` (đang chặn)

> Cơ chế **đã xong**: `sets.export` bật là chạy. Đã bật thử `set2` để kiểm: sinh đúng
> 370 file + 326 rule `.set2`. **Nhưng phải tắt lại** vì sprite bị **CẮT CỤT**.

- [ ] **`setRect` cho ~9 sprite khác kích thước** — `bar-h[-md/-sm/-xs]` (48×12 ↔ 48×20),
      `bar-v[-md/-sm/-xs]` (12 ↔ 20 rộng), `panel-textured` (48 ↔ 56 cao), `panel`
      (44 ↔ 48), `divider-h/v` (3 ↔ 7 ở set3).
- [ ] **`setDelta` đúng cho từng nhóm** — đã gán cho 9 slice, cần soát lại đủ 42 slice main.
- [ ] **`overlays` theo bộ** — hoạ tiết tâm (boss/fan) **chỉ có ở set2/set3**; cần hỗ trợ
      `setOverlays` (hoặc `ov.setRect`) trong packer + khai rect boss cho từng bộ, nếu không
      boss bị **kéo giãn thành vệt** khi 9-slice stretch.
- [ ] Thêm `"set2"`, `"set3"` vào `sets.export` sau khi 3 việc trên xong + **soát ảnh render**.
- [ ] Thêm dropdown **bộ 1/2/3** vào trang mockup.
- [ ] *Cách làm khuyến nghị:* dùng `ui-slice-editor.html` kéo tay cho ~10 sprite khác kích
      thước; phần chỉ lệch offset thì map tự động rồi soát.

### P1 — Mở rộng nguồn asset

- [ ] `_icons.png`: còn **~150 icon** ở block màu khác chưa cắt (hiện chỉ 22 icon block phổ thông).
- [ ] `grids.png`: **5 style × 5 tông màu** — manifest mới dùng **block 0** (tông đồng).
      Muốn map theo theme cần thêm `sheet offsets`.
- [ ] Sheet chưa đưa vào pipeline: `Selectors/`, `Labels_And_Tags/`, `Character_Emotions/`,
      `Cursors/` (+ `Click_Effects`), `Controls/Controller`, `Controls/Keyboard_Mouse`.
- [ ] `classic` + `stylized` UI version (2 thư mục còn lại trong pack) — hiện chỉ dùng `grim`.

### P1 — Đưa UI vào game thật

- [ ] **Chưa màn hình nào dùng `.ui-*`** — mới có lab/mockup. Cần thay HUD hiện tại
      (xem [`docs/ui-hud-architecture-guide.md`](file:///D:/Develop/Projects/BrowserQuest/docs/ui-hud-architecture-guide.md)).
- [ ] Wire `DisabledGuard` vào `game-world-ui-manager.js` / `ui-manager.js` / `sprite-ui-manager.js`
      của T004 (đang để rời cho an toàn, xem `.agents/rules/ui-code.md`).
- [ ] Nút **Components only** + deep-link `?only=1` đã có ở lab; xét thêm cho mockup page.

### P2 — Chuẩn UI (theo `.agents/rules/ui-code.md`)

- [ ] Localization — hiện chuỗi trong lab/mockup hardcode tiếng Việt/Anh.
- [ ] Gamepad + keyboard cho mọi control (hiện chỉ chuột/chạm).
- [ ] Colorblind mode + scalable text.
- [ ] Test ở độ phân giải min/max.

### P2 — Chất lượng pipeline

- [ ] Script CI validate schema + kiểm `rect` khít + `slice` chia hết chu kỳ.
- [ ] Test tự động cho packer (idempotent, dọn rác, đa sheet, đa bộ).
- [ ] Cảnh báo khi `setRect`/`setDelta` thiếu cho một bộ đang `export`.

### P3 — Tài liệu

- [ ] Ảnh so sánh 3 bộ (plain/fan/spike) cạnh nhau trong `docs/`.
- [ ] Sơ đồ cách thêm 1 nhóm mới (đo rect → khai manifest → chạy packer → soát preview).
- [ ] Bổ sung mục "3 bộ" vào `docs/ui-pixel-perfect-9slice.md` nếu liên quan.

---

## 10. Ghi chú kỹ thuật đáng nhớ

- **Guideline layer là dữ liệu**: `use_guideline_layer.png` có khung nhóm **tô màu riêng
  cho từng bộ** → đọc bbox theo màu ra toạ độ chuẩn, không phải đoán.
- **`.aseprite` không có metadata tên** → manifest là nguồn sự thật duy nhất.
- **Sprite sheet gốc có layer**: `Bg, Shadow, UI_Bg, Grim_UI, Outline, Guidelines`; bản
  `grim_ui_only.png` = chỉ art, `grim_ui_outline.png` = outline.
- **CSS cho bộ khác chỉ override đường dẫn ảnh** (border-width/repeat y hệt) ⇒ CSS **không
  phình** theo số bộ (8221 dòng cho cả set1; nếu lặp rule đầy đủ sẽ ~22k dòng).
- **Trang mockup** ép CSS sinh ra về **đúng khối 1x** rồi scope vào `.mk-canvas` / `.mk-pal`
  ⇒ canvas luôn 1:1 pixel; phóng to bằng `zoom` bội số nguyên.
- **`clean_stale` phải quét thư mục output**, không chỉ dựa vào index (index nằm trong
  thư mục gitignored ⇒ sau clone nó rỗng).
