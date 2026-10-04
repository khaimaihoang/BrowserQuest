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
| **`set1`** *(mặc định)* | **trơn** — khung chữ nhật, không góc, thanh mảnh, không boss | `bar-h` 48×**12**, `panel` 48×**48**, `divider` 3px |
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
| `sets` | `{default, offsets: {set1:0,set2:544,set3:1088}, export: ["set1","set2","set3"]}` |
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
  "setSlice": { "set3": 12 }, // (tuỳ chọn) slice riêng theo bộ khi ornament set2/3 dày hơn
  "repeat": "repeat",           // border-image-repeat
  "stretch": "x",               // 'x' chỉ kéo ngang / 'y' chỉ kéo dọc
  "states": { "pressed": [...], "disabled": [...] },
  "alias": { "hover": "active" },        // map selector sang sprite có sẵn
  "hoverUses": "active",                 // hover desktop, bọc @media (hover:hover)
  "disabledFilter": "brightness(.72) saturate(.8)",
  "overlays": [{ "rect": [...], "anchor": "center" }],   // hoạ tiết tâm (mọi bộ)
  "setOverlays": { "set2": [ ... ], "set3": [ ... ] },   // overlay riêng từng bộ (kèm ov.setRect)
  "flatten": true,              // làm phẳng dải giữa cho tile sạch
  "themed": false,              // 1 bản, không theo theme (resource fills)
  "sets": false,                // 1 bản, không theo bộ (sheet tĩnh, decoration…)
  "setDelta": { "set2": -4 },   // lệch thêm so với offsets chung
  "setRect": { "set2": [...] }, // khác CẢ kích thước → khai rect đầy đủ
  "stateSetRect": { "active": { "set2": [...] } } // rect tuyệt đối theo bộ cho từng STATE
}
```

Khoá `_comment_*` bị packer bỏ qua (chia nhóm cho dễ đọc + làm nhãn nhóm cho palette).

---

## 4. Sản phẩm hiện có

```
204 slice (+36 state) × 5 theme × 3 scale  →  5418 ảnh  (set1/set2/set3; 108 slice `-extraN` là sets:false)
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
| [`tools/ui/qa.py`](file:///D:/Develop/Projects/BrowserQuest/tools/ui/qa.py) | **QA sheet 1 ảnh**: mọi bộ × native + kéo dài → `tools/ui/out/qa.png` (soi nhanh, 1 screenshot) |
| [`tools/ui/atlas-check.py`](file:///D:/Develop/Projects/BrowserQuest/tools/ui/atlas-check.py) | **reconstruct atlas 1 theme × 3 bộ** từ sprite đã xuất → so với gốc: full / **CUT** / unused |
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
| Gallery slice + UI kit (mỗi tên: base + **mọi state** × 3 bộ) | `ui-lab.html` (`?only=1` = chỉ kit, `#k-mock` = mockup 1) |
| Editor kéo slice | `ui-slice-editor.html` |
| **Mockup cho artist** | `ui-mockup.html` |

### 5.2 Output

```
client/img/{1,2,3}/ui-kit/*.png          sprite theo scale (NEAREST ×1/×2/×3)
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
| `7aa83398` | **feat/fix**: hoàn thiện kit 3 bộ — fix rect thiếu mép trên · state khai sai bộ · `setRect/setSlice/setOverlays/stateSetRect` · tách `ui-kit` + guard + khôi phục asset HUD · cache-bust `?v=` · `qa.py`/`atlas-check.py` · xuất đủ atlas (**CUT=0 unused=0**, 204 slice) |

### 8.1 Bug đã sửa trong phiên

- **Disabled xuyên click** — `pointer-events:none` → `cursor:default` + JS guard.
- **Dọn rác không chạy sau clone** — index dọn rác nằm ở `tools/ui/out/` (**gitignored**) ⇒
  135 file của manifest cũ sống mãi. Nay packer **quét luôn** `client/img/{1,2,3}/ui-kit/*.png`.
- **Lẫn bộ hoa văn** — rebase về `set1` + siết rect.
- **Mockup page không render** — nút `#shades` không tồn tại làm `wire()` ném lỗi.
- **Palette vô hình** — CSS scope thiếu; inline CSS phải bỏ `../` trong `url()`.
- **Cụt border top (11 slice PANELS/TABS)** — `panel` `panel-slim` `panel-title`
  `tab-cap-*` `tab-*` khai `rect` thiếu **3–4px** ở mép trên (crop bắt đầu dưới đường
  viền) ⇒ 9-slice mất hẳn cạnh trên. Đã nới `rect.y`/`+h` cho đủ bbox và dịch
  `setDelta` đúng bằng phần nới để **giữ nguyên** toạ độ set2/set3.
- **State của control ở SAI BỘ (set2)** — `radio`/`checkbox`/`toggle-v`/`toggle-h`/
  `button-thin`/`button-tiny` khai `states` ở `base_y + 544` (toạ độ set2) trong khi base
  ở set1 ⇒ bật/tắt control thì sprite **đổi kiểu** (mảnh ↔ dày). Đã chuyển hết state về set1.
- **CSS bộ không được scope** — rule override ảnh của `.set2`/`.set3` thiếu tiền tố bộ
  (`css_for_scale` dòng base) ⇒ bộ cuối đè bộ mặc định. Đã thêm `.set2`/`.set3`.
- **set2/set3 bị cắt cụt** — do thiếu `setRect`; đã auto-đo 43 slice khác kích thước
  (xem §9 P0) + audit "art vượt rect" = NONE.
- **Sprite cũ còn cache (nghi can chính của "sọc/cụt")** — sprite set2/set3 sinh lại
  nhưng **URL không đổi** ⇒ trình duyệt dùng bản cũ, CSS mới + sprite cũ = 9-slice sai.
  Đã thêm token `?v=<md5(manifest + source packer)>` vào **mọi** `url()` và `<link>` CSS (`ASSET_VERSION`).
  (Băm cả `ui-pack.py` để sửa packer cũng bust cache — nếu chỉ băm manifest thì lần sửa
  code trước vẫn dùng sprite cũ → set3 chỉ hiện base.)
- **TRÙNG THƯ MỤC với asset HUD gốc (bug gốc rễ của "cụt")** — packer xuất vào
  `client/img/{1,2,3}/ui/` là **đúng thư mục** game dùng (`main.css` → `ui/bar_body.png`,
  `panel.css` → `ui/panel.png`). `clean_stale` đã **xoá** `bar_body/left/right`, `close*`
  và **ghi đè** `panel.png`; dev-server lại serve `dist/client` **trước** `client` nên
  `.ui-panel` (set1) lấy `dist/.../ui/panel.png` (bản game, khác) còn set2/set3 lấy kit ⇒
  lệch/cụt. **Fix:** đổi `output.image` → `client/img/{scale}/ui-kit`, khôi phục asset game,
  thêm guard trong packer chặn ghi vào `img/<n>/ui/`.
- **Dev-server phục vụ bản CŨ ở `dist/client`** — serve `dist/client` trước `client`, mà
  packer chỉ ghi CSS/lab vào `client/` ⇒ `dist/client/css/ui-slices.generated.css` cũ
  shadow. **Fix:** packer **mirror CSS + ui-lab.html sang `dist/client`** + in **build
  stamp** (`ASSET_VERSION`) trên header lab để biết đang xem bản nào.
- **Overlay pseudo bị lệch/clipped** — `position: relative` chỉ phát ở rule bộ mặc định
  (set1); set2/set3 mới có overlay nhưng thiếu `position:relative` ⇒ `::before/::after`
  neo vào tổ tiên sai ⇒ crown bị cắt. Fix: phát `position: relative` cho mọi bộ có overlay.
- **State set2/set3 trùng base** — `rect_for` trả thẳng `setRect` của slice cho MỌI rect ⇒
  state (pressed/checked/…) ở set3 đè lên base set3. Fix: áp **delta** `setRect − rect`
  lên rect bất kỳ (base hoặc state) ⇒ state giữ đúng vị trí/kích thước riêng.
- **Atlas 1 theme 3 bộ giờ phủ 100%** — 108 component art còn thiếu được xuất thêm,
  tên tạm `<slice gần nhất>-extraN` (sets:false, rect tuyệt đối). `atlas-check.py`:
  full=347 · CUT=0 · unused=0. **Cần artist đổi tên chuẩn** cho 108 slice extra.
- **State `active` của TAB khai sai bộ (set2)** — `tab-*` khai `states.active` tại toạ độ
  **set2** (y~660-844) ⇒ set1 lấy art set2, set2/set3 bị cộng delta ⇒ set3 rơi vào vùng
  **trống** (vd `[558,1743]`). Fix: khai `active` về **set1** + thêm **`stateSetRect`**
  (rect tuyệt đối theo bộ cho từng state — ornament state khác vị trí/kích thước giữa bộ,
  không suy ra được bằng delta của base).

---

## 9. TODO

### P0 — Mở bộ `set2` / `set3` ✅ ĐÃ XONG

> `sets.export = ["set1","set2","set3"]`. `rect` vẫn ghi ở set1; khác kích thước →
> `setRect`, chỉ lệch vài px → `setDelta`. Auto-đo bằng packer (mở mép chịu 1px hở) →
> audit "art vượt rect" = **NONE** ở cả set2/set3.

- [x] **`setSlice` theo bộ** — ornament set2/set3 dày hơn nên `slice` cũ bị cắt/lặp góc:
      `panel` set3=12, `panel-slim` set3=[12,11,12,11], `panel-textured` set2=[12,15,12,15]/set3=[16,15,16,15],
      `button*` set3 (+4).
- [x] **`setRect` cho 43 sprite khác kích thước** — `bar-h/-v[-md/-sm/-xs]`, `container*`,
      `divider-h/v`, `panel-textured`, `panel-header`, `tab-*`, `slot*`, `radio`,
      `checkbox`, `toggle-*` (set3), `button*`/`panel` (set3)…
- [x] **`setDelta`** — chỉ còn 3 slice lệch y (đã chuẩn hoá).
- [x] Bật `set2`/`set3` vào `sets.export` + soát render.
- [x] **Fix scope CSS**: rule override ảnh của bộ khác trước đây **thiếu tiền tố**
      `.set2`/`.set3` ⇒ bộ cuối (set3) đè luôn bộ mặc định ở theme dark. Nay là
      `.set2 .ui-x` / `.set3 .ui-x` (kèm theme: `.set2.theme-green .ui-x`).
- [x] **ui-lab gọn + 3 bộ**: base + **mọi state** (checked/disabled/…) native, 3 nhóm set1/set2/set3,
      theme switcher
      áp theme lên chính phần tử cell (để selector `.set2.theme-*` khớp).
- [~] **`overlays` theo bộ** — đã thêm hỗ trợ `setOverlays` (dict theo bộ) + `overlay.setRect`;
      khai crown trên/dưới cho `panel-textured` set2/set3. Native render vẫn **pixel-exact**,
      kéo dài hết lặp crown. Còn: `panel-header` (nên chuyển `nine:true` + overlay crown),
      crown/hoa văn tâm của `bar-*`.
- [x] **Xuất đủ atlas 1 theme × 3 bộ** — reconstruct (`tools/ui/atlas-check.py`): **full=347 · CUT=0 · unused=0**. Thêm **108 slice `-extraN`** cho phần art chưa xuất (sets:false, rect tuyệt đối).
- [ ] **Đổi tên 108 slice `-extraN`** sang tên chuẩn (suy ra từ nhóm: cột nút thứ 4 = `button-hover`, hàng slot/tab variant…).
- [ ] Thêm dropdown **bộ 1/2/3** vào trang mockup.

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
