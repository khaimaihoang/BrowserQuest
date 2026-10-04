# UI Slice Pipeline (Minifantasy → game)

> **Trạng thái:** Chuẩn bắt buộc (MUST-FOLLOW) khi thêm/sửa UI từ atlas Minifantasy.
>
> **Tài liệu liên quan:**
> - [ui-pixel-perfect-9slice.md](./ui-pixel-perfect-9slice.md) — quy tắc 9-slice pixel-perfect
> - [ui-hud-ux-process.md](./ui-hud-ux-process.md) — quy trình & kiến trúc UI/HUD
> - [ui-hud-architecture-guide.md](./ui-hud-architecture-guide.md) — kiến trúc UI hiện tại
> - [`tools/ui/README.md`](../tools/ui/README.md) — bản tóm tắt thao tác nhanh
> - `AGENTS.md` §2, §10, §11

---

## 1. Mục đích

Atlas Minifantasy là **một tấm PNG lớn không có tên từng phần**, nên trước đây mỗi
asset phải cắt tay, upscale tay, viết CSS tay — không lặp lại được, dễ lệch pixel.

Pipeline này biến atlas thành **asset + CSS dùng được ngay** thông qua một
**manifest có tên gọi rõ ràng**, để artist chỉ cần khai báo "slice nào là gì" rồi
chạy 1 lệnh.

```
atlas PNG ──┐
            ├─► tools/ui-pack.py ──┬─► client/img/{1,2,3}/ui-kit/<name>.png   (NEAREST, ×1/×2/×3)
slices.json ┘                     ├─► client/css/ui-slices.generated.css  (border-image + states)
                                  ├─► client/ui-lab.html                  (preview dev)
                                  └─► tools/ui/out/preview.png            (self-test 9-slice/state)
```

---

## 2. Nguồn: cấu trúc atlas

| Thuộc tính | Giá trị |
|---|---|
| File | `client/Minifantasy/Minifantasy_UI _Overhaul_v1.0/_Minifantasy_UI_Overhaul_Assets/Grim_Minifantasy_UI/_grim_ui.png` |
| Kích thước | **4528 × 1984** |
| Lưới | **16 × 16 px** (`_Info.txt`: "16x16px sliced to facilitate the creation of panels of any size") |
| Theme | **5 cột màu**, stride **912px**: `dark (0)`, `green (912)`, `blue (1824)`, `red (2736)`, `white (3648)` |
| Layer `.aseprite` | 6 layer phẳng: `Bg, Shadow, UI_Bg, Grim_UI, Outline, Guidelines` — **không có tên element** |
| Block "UI" | Bản có màu/fill thật: **y ≥ 544**. Hàng phía trên (y < 544) là bản **outline** |
| Resource fills | Đáy atlas (`y≈1747` dọc, `y≈1821` ngang), **màu khác nhau theo từng cột** |

Vì `.aseprite` không có metadata tên, **manifest là nguồn sự thật duy nhất** cho
việc "vùng nào là gì".

### 2.0 Mỗi theme có **3 BỘ** (set) — không phải 1

Mỗi cột theme (912px) chứa **3 bộ asset xếp dọc**, cùng nhóm nhưng **hoa văn khác**:

| Bộ | Hoạ tiết | Y-offset so với bộ 2 |
|---|---|---|
| **set1** *(mặc định)* | **trơn** — khung chữ nhật, không góc, thanh mảnh, không boss | **−540 / −544** |
| **set2** | **hoa thị (fan)** — nút ở 4 góc, hoa thị trên/dưới panel-textured, boss ở tâm thanh | 0 |
| **set3** | **gai (spike)** — gai ở góc, hoa văn chữ thập ở giữa | **+540 / +544** |

⇒ **5 theme × 3 bộ = 15 bộ**. Toạ độ nhóm **giống hệt nhau về x**; chỉ khác y.

Offset chính xác **đo từ `use_guideline_layer.png`** (khung nhóm tô màu riêng cho từng bộ
— đọc bbox theo màu) rồi đo lại trên art thật:

| Nhóm | set2→set1 | set2→set3 |
|---|---|---|
| PANELS · TABS | −540 | +540 |
| DIVIDERS · SLIDERS · RESOURCES | −544 | +544 |
| CHECK_BOXES | −544 | +542 |
| TOGGLE_BUTTONS · SLOTS | −544 | +543 |
| PUSH_BUTTONS | −544 | +540 |

> **Bài học 3:** trước đây manifest chỉ cắt **bộ 2**, mà `button`/`button-slim` lại lấy
> từ **bộ 1** ⇒ asset bị **lẫn hai bộ hoa văn**. Hiện đã **rebase toàn bộ về bộ 1**
> (bộ mặc định) và siết `rect` về đúng bao nội dung (42/42 slice khít 0px).
>
> Bộ 1 **thiếu hoạ tiết so với bộ 2/3** ⇒ thanh bar thấp/mảnh hơn hẳn (vd `bar-h`
> 48×12 thay vì 48×20) nên **`overlays` bị bỏ khỏi bộ mặc định** — cơ chế neo hoạ tiết
> tâm chỉ cần cho bộ 2/3.

**Cơ chế đã sẵn sàng** (trục `sets` trong manifest + `.set2`/`.set3` trong CSS), nhưng
`sets.export` hiện chỉ bật `set1`. Lý do **đo được**, không phải bỏ dở:

- Nhiều sprite **khác cả kích thước** giữa các bộ (không chỉ dịch y): `bar-h` 48×12 ↔ 48×20,
  `divider-h` 3px ↔ 7px, `panel` 44 ↔ 48. Dời thuần offset ⇒ **cắt cụt** sprite
  (đã thử bật `set2`: `bar-h--set2.png` ra 48×12 thay vì 48×20 ⇒ sai).
- Hoạ tiết tâm (boss/fan) **chỉ có ở bộ 2/3** ⇒ phải khai `overlays` riêng cho từng bộ,
  nếu không boss bị kéo giãn thành vệt khi 9-slice stretch.
- Offset **lệch theo từng nhóm** (set1↔set2 = 540 hoặc 544; set1↔set3 = 1080/1084/1086/1087/1088)
  ⇒ phải khai `setDelta` cho mỗi nhóm.

⇒ Mở bộ 2/3 = khai `setRect` + `setDelta` + overlay-theo-bộ cho ~40 sprite, rồi thêm tên bộ
vào `sets.export`. Nên làm bằng **slice editor** (kéo tay, mắt người soát) rồi dán vào manifest.

### 2.1 Nhóm theo guideline

File `_Use_Guidelines/set_use_guidelines.png` (1:1 với atlas) ghi nhãn nhóm. Toạ độ
nhóm ở block "UI" (= block gốc + 544):

| Nhóm | x | y (block UI) |
|---|---|---|
| PANELS | 54–266 | 646–762 |
| DIVIDERS | 298–375 | 652–708 |
| SLIDERS | 287–383 | 715–770 |
| CHECK BOXES | 205–370 | 807–866 |
| TOGGLE BUTTONS | 205–370 | 884–943 |
| SLOTS | 29–184 | 765–985 |
| TABS | 154–618 | 631–1019 |  
| _(cùng nhóm TABS)_ NẮP tab nhỏ | 404–480 | 660–732 |
| RESOURCE'S BARS & CONTAINERS | 635–856 | 756–988 |
| PUSH BUTTONS | 4 cỡ (16×16 / 48×16 / 16×48 / 48×48) | y≈1040 / 1088 |

> **Bài học:** tên slice phải bám **nhóm trong guideline**, không đoán theo hình
> dạng. (Đã từng đặt sai: `divider-fancy-*` thực ra thuộc SLIDERS; các thanh
> `x416–592` thực ra thuộc TABS chứ không phải resource bars.)

### 2.2 NẮP tab ≠ icon (sửa tên sai `tab-icon-*`)

Nhóm TABS chứa **hai** loại mảnh, cả hai đều có bản `--active`:

| Vai trò | Rect (theme dark) | Kích thước | Tên đúng |
|---|---|---|---|
| CẠNH khung tab lớn | `[416,756]` / `[416,848]` / `[404,784]` / `[464,784]` | 48×12 / 12×48 | `tab-top` `tab-bottom` `tab-left` `tab-right` |
| **NẮP** tab nhỏ (gắn vào mép panel) | `[432,660]` / `[404,688]` / `[464,688]` / `[432,720]` | 16×12 / 12×16 | `tab-cap-top` `tab-cap-left` `tab-cap-right` `tab-cap-bottom` |

Bản `--active` của nắp là **khung nâng 16×16** (tab đang chọn cao hơn 4px) — đúng
kiểu tab trong `mock_up_1.png`.

> **Bài học 2:** tên cũ `tab-icon-1..4` là **SAI** — chúng là *nắp khung*, không phải
> icon. **Icon** trong mockup đến từ **sheet khác** (mục 2.3), không nằm trong
> `_grim_ui.png`. Đã đổi tên thành `tab-cap-<side>`.

### 2.3 Hai sheet phụ mà mockup dùng

`_grim_ui.png` **không** chứa icon lẫn ô lưới item. Mockup lấy chúng từ
`_General_UI_Resources/`:

| Sheet | Kích thước | Nội dung | Slice |
|---|---|---|---|
| `Icons/_icons.png` | **576×432** | lưới icon **16px, sprite 8×8**. Block phổ thông ở `x≈376–560`: hàng `y=24` (chest, barrel, pickaxe, bottle, hammer…) và hàng `y=40` (**person**, swords, shield, **craft** = búa+đe, **orb**, heart, plus, bolt, boot, pan, drop) + block icon social | `icon-*` (22) |
| `Grids/grids.png` | **1360×496** | ô lưới item: **5 style** × 5 tông màu (block stride **272px**). Mỗi style: 1 ô đơn, 1 khối **4 gạch góc**, mảnh chữ T, ô nhỏ, lưới 3×3, lưới 6×6 | `grid-*` (9) |

Toạ độ đã **đo bằng connected-component** (scipy), không đoán:

```
grid-cell           [26,  26, 28, 28]   ô đơn (solid)
grid-cell-bracket   [16,  64, 32, 32]   4 gạch góc trong 1 ô 32×32  ← mockup dùng cái này
grid-3x3            [138, 42, 48, 48]
grid-6x6            [196, 36, 56, 56]
grid-cell-ornate    [26, 410, 28, 28]   bản hoa văn (style 5)
```

---

## 3. Manifest — schema

File: [`tools/ui/slices.json`](../tools/ui/slices.json)

### 3.1 Cấp cao (top-level)

| Khoá | Ý nghĩa |
|---|---|
| `source` | đường dẫn atlas **chính** (tương đối repo root) — tương đương `sheets.main.source` |
| `sheets` | map `{tên: {source, themed}}`. `themed:true` = ảnh lặp ngang theo từng theme (nhận `offsets`); `themed:false` = rect tuyệt đối, xuất **1 lần** |
| `sets` | trục **BỘ** (hoa văn) theo y: `{default, offsets: {set1:0, set2:544, set3:1088}, export: ["set1"]}`. Bộ mặc định → class `.ui-*` trần; bộ khác → `.set2 .ui-*` / `.set3 .ui-*` (gộp được với theme: `.set2.theme-green`). `export` giới hạn bộ nào được sinh (chỉ bật bộ nào đã có toạ độ chuẩn) |
| `grid` | kích thước ô lưới (16) |
| `themes.default` / `themes.offsets` | theme mặc định + offset x từng cột |
| `scales` | `[1,2,3]` — các hệ số upscale NEAREST |
| `output.image/css/lab/preview` | đường dẫn output (`{scale}` được thay) |
| `css.prefix` | tiền tố class (`ui` → `.ui-panel`) |

### 3.2 Mỗi slice

```jsonc
// Trục BỘ: rect ghi ở BỘ MẶC ĐỊNH (set1). Bộ khác = rect + offsets + setDelta,
// hoặc setRect khi sprite khác CẢ kích thước; "sets": false = chỉ có 1 bộ.
"bar-h": {
  "rect": [672, 314, 48, 12],                 // bộ mặc định: thanh mảnh, không boss
  "setRect": { "set2": [672, 854, 48, 20] },  // bộ 2: dày hơn (có boss) — khi mở set2
  "setDelta": { "set2": -4, "set3": -8 }      // lệch vài px so với offsets chung
},
"bar-fill-red": { "sets": false, "themed": false },
"icon-person": {
  "sheet": "icons",            // tuỳ chọn — sheet chứa slice (mặc định "main")
  "themed": false,             // sheet tĩnh ⇒ không cộng offsets theo theme
  "rect": [376, 40, 8, 8],
  "nine": false
},
"button": {
  "rect": [208, 544, 48, 48], // [x, y, w, h] theo pixel atlas (theme dark) — base = look enabled
  "nine": true,                // true = 9-slice; false = sprite rời
  "slice": 8,                  // bề dày viền: int (4 cạnh bằng nhau) HOẶC [t,r,b,l]
  "repeat": "repeat",          // CSS border-image-repeat ('repeat' = pixel-perfect)
  "states": {                  // tuỳ chọn — sinh sprite + selector cho từng state
    "pressed":  [464, 544, 48, 48],     // enabled + đang nhấn (sáng nhấn)
    "disabled": [ 80, 544, 48, 48]      // vô hiệu = khoá cứng (tối, không đổi sprite khi nhấn)
  },
  "alias": { "x": "y" },              // tuỳ chọn — map thêm selector sang sprite có sẵn
  "hoverUses": "active",              // tuỳ chọn — desktop hover (bọc @media hover); KHÔNG dùng cho button
  "disabledFilter": "brightness(.62) saturate(.75)",  // tuỳ chọn — filter cho state disabled
                                                     // (dùng khi atlas không có sprite tối, vd toggle)
  "stretch": "x",                     // tuỳ chọn — 'x' chỉ kéo ngang / 'y' chỉ kéo dọc
  "overlays": [                       // tuỳ chọn — neo hoạ tiết tâm (KHÔNG tile)
    { "rect": [688,864,16,20], "anchor": "center" }
  ],
  "flatten": true,                    // tuỳ chọn — làm phẳng dải giữa để tile sạch
  "themed": false                     // tuỳ chọn — chỉ xuất 1 bản, không theo theme
}
```

- `disabledFilter` = CSS `filter` áp cho `:disabled/[disabled]/.disabled/[aria-disabled='true']`
  (kèm `cursor:default`), dùng để **đủ tương phản disabled** — vd toggle dùng bản tối
  trong atlas rồi dim thêm `brightness(.72) saturate(.8)` (2 bản sáng/tối chỉ lệch ~8 luma).

- `overlays` = sprite có **hoạ tiết ở tâm** mà 9-slice không neo được (sprite có boss,
  hoa văn giữa). Packer sẽ:
  1. xuất `X--base.png` = sprite đã **xoá hoạ tiết tâm** (để ruột 9-slice tile sạch),
  2. xuất `X--ovN.png` = từng hoạ tiết,
  3. sinh `.ui-X { position:relative }` + `.ui-X::before/::after` neo hoạ tiết
     (`anchor`: `center` / `tc` / `bc` / `lc` / `rc`). Vị trí neo được **bù theo
  `border-width`** (absolute neo vào padding box, không phải border box) nên hoạ tiết
  khớp đúng mép panel.
  Tối đa **2 overlay** (2 pseudo-element). Sprite dùng: `bar-h` (và `-md/-sm/-xs`),
  `bar-v` (và `-md/-sm/-xs`), `panel-textured`.
- `flatten: true` = **làm phẳng dải giữa** của 9-slice (theo trục `stretch`) để tile
  không lộ mối. Cần cho các bar vì thân bar có viền nét đứt → nếu tile nguyên sẽ thấy
  "đốm sáng" ở ranh tile. Dùng cùng 8 bar trên.
- `stretch: "x"` = **chỉ kéo ngang** → slice `[0,c,0,c]` (t=b=0, giữ nguyên chiều cao
  sprite). `stretch: "y"` = chỉ kéo dọc → `[c,0,c,0]`. Dùng cho `bar-h`/`bar-v`.
- `slice` dạng **`[t,r,b,l]`** dùng cho các **thanh mỏng** (slider track,
  resource bar): chỉ giữ hoạ tiết ở 2 đầu **theo trục dài**, tile phần giữa, và
  **không cắt theo trục ngắn** (nếu không sẽ bị chia thành dải ngang → trông kì lạ):
  - thanh **ngang** (rộng ≫ cao): `[0, c, 0, c]` — vd `bar-fill-red`, `slider-track-h`
  - thanh **dọc** (cao ≫ rộng): `[c, 0, c, 0]` — vd `bar-fill-v-red`, `slider-track-v`
  - sprite có **boss/hoa tiết nhô ra ngoài thân** (`bar-h`, `bar-v`) → vẫn 9-slice
    được, nhưng phải kèm `overlays` (neo hoạ tiết tâm) + `flatten` (làm phẳng ruột),
    nếu không boss sẽ bị tile lặp hoặc đốm sáng ở ranh tile.
  - sprite **cố định** (tab-*, panel-header/title, slot, check/toggle, divider,
    container): `nine:false`, dùng ở kích thước gốc.
  - slider track: `c=8` để giữ 2 mũi tên.
- Lab preview & `preview.png` tự chọn kích thước: **native ×1 → ×2 → ×3**, rồi thêm
  case **DÀI** (≥360px theo trục dài cho thanh; wide 5w×2h + tall 2w×5h cho panel)
  để lộ đường tile/góc. Không ép mọi 9-slice về cùng một ô demo.
- `alias`/`hoverUses` **không sinh file** — chúng trỏ selector khác về sprite có sẵn.
- `themed:false` dùng cho các **bar-fill màu** (màu nằm ở từng cột) → chỉ xuất 1 bản.
- `sheet: "<tên>"` chọn sheet chứa `rect` đó (mặc định `"main"`). Packer cộng
  `themes.offsets[theme]` vào `x` **chỉ khi cả sheet lẫn slice đều `themed`** — nên
  slice trên sheet tĩnh luôn khớp toạ độ tuyệt đối.
- Khoá `_comment_*` trong `slices` được packer bỏ qua (dùng để chia nhóm cho dễ đọc).

---

## 4. Mô hình STATE — touch-first

Mobile **không có hover** (button/switch **không khai báo `hoverUses`** ⇒ không sinh
rule `:hover`); state gốc là `pressed`/`active`/`checked`/`disabled`. Quy ước:
**sprite sáng = dùng được (enabled / on), sprite tối = `disabled`**.

| State | Ý nghĩa | Selector sinh ra |
|---|---|---|
| `pressed` | enabled + đang nhấn (sáng nhấn) | `:active`, `.pressed` — kèm `:not(:disabled):not([disabled]):not(.disabled):not([aria-disabled])` |
| `disabled` | vô hiệu = **KHOÁ CỨNG** (sprite tối, nhấn không đổi sprite) | `:disabled`, `[disabled]`, `.disabled`, `[aria-disabled='true']` + `cursor:default` (NUỐT click) |
| `active` | bật / đang chọn | `.active`, `[aria-selected='true']`, `[aria-pressed='true']` |
| `active-pressed` | `active` + đang nhấn | `.active.pressed`, `.active:active`, `[aria-pressed='true']:active` |
| `checked` | on (checkbox/switch) | `:checked`, `.checked`, `[aria-checked='true']` |
| `checked-pressed` | on + đang nhấn | `:checked:active`, `.checked.pressed` |
| `checked-disabled` | on + vô hiệu (sprite tối, khoá cứng) | `:checked:disabled`, `.checked.disabled`, `.checked[disabled]`, `[aria-checked='true'][disabled]`, `.checked[aria-disabled='true']`, `[aria-checked='true'][aria-disabled='true']` |
| `hover` | chỉ desktop | `:hover`, `.hover` — **bọc trong `@media (hover: hover)`** |

> **Disabled nuốt click, KHÔNG xuyên qua** (bug đã gặp): dùng `cursor:default` +
> giữ `pointer-events:auto` để control hứng cú click, không cho nó rơi xuống canvas/cha
> phía sau (nếu dùng `pointer-events:none` thì `elementFromPoint` trả về phần tử CHA ⇒
> click vào nhân vật/canvas vẫn kích hoạt). Không có phản hồi nhấn vì selector
> `pressed`/`active-pressed` đã loại disabled.
> **Hệ quả cho JS**: handler gắn trực tiếp lên control PHẢI tự bỏ qua khi
> `el.hasAttribute('disabled')` hoặc `el.classList.contains('disabled')` — CSS
> không chặn được bubbling lên cha.

**Button = enabled {chưa nhấn, đã nhấn} + disabled (KHOÁ CỨNG)**; **base = look enabled
(sáng)**; nút disabled **giữ nguyên sprite tối dù có nhấn** (selector nhấn đã loại hẳn
element disabled, và control vẫn giữ `cursor:default` + `pointer-events:auto` để **nuốt** cú click):

```jsonc
"button": {
  "rect": [208, 544, 48, 48],          // enabled (sáng, chưa nhấn) = base
  "states": {
    "pressed":  [464, 544, …],         // sáng, đã nhấn
    "disabled": [ 80, 544, …]          // tối — khoá cứng, không có state *-pressed
  }
  // KHÔNG hoverUses ⇒ không có trạng thái hover
}
```

CSS sinh ra (thứ tự cascade: base → theme base → state → theme state → alias →
``disabledFilter`` → hover; `disabled` để **cuối** để luôn thắng khi specificity bằng nhau):

```css
.ui-button { /* base = enabled (sáng) */ }
.ui-button:not(:disabled):not([disabled]):not(.disabled):not([aria-disabled='true']):active,
.ui-button:not(…):not(…).pressed   { border-image-source: url('…--pressed.png'); }
.ui-button:disabled, .ui-button[disabled], .ui-button.disabled, .ui-button[aria-disabled='true']
  { border-image-source: url('…--disabled.png'); pointer-events: none; }
```

> `[disabled]` (attribute trên div giả lập) **bắt buộc có** — game set/remove attribute này
> để MutationObserver cập nhật sprite; thiếu nó thì nút disabled vẫn hiện look enabled
> (nhấn xuống nhưng không khoá).

> **Toggle/checkbox có 2 bản sprite cho mỗi vị trí (sáng/tối)** — vd `toggle-h`:
> `base` = off-tối, `pressed` = off-**sáng**, `checked` = on-**sáng**, `checked-pressed` = on-tối.
> Sprite cho 2 cặp on/off luôn đồng bộ: enabled lấy bản sáng cho cả
> off & on, disabled lấy bản tối cho cả off & on — **cộng thêm `disabledFilter:
> "brightness(.72) saturate(.8)"`** vì 2 bản chỉ lệch ~8 luma (ở theme tối là quá ít để
> phân biệt “disabled”; filter chỉ làm tối thêm, không đổi màu / không đổi vị trí núm):
>
> ```jsonc
> "toggle-h": {
>   "rect":   [256, 932, 16, 8],                      // ENABLED + OFF (sáng)
>   "states": {
>     "checked":          [304, 932, 16, 8],          // ENABLED + ON  (sáng)
>     "disabled":         [208, 932, 16, 8],          // DISABLED + OFF (tối)
>     "checked-disabled": [352, 932, 16, 8]           // DISABLED + ON  (tối)
>   }
> }
> ```
>
> `disabledFilter` (filter cho team `disabled`, kèm `cursor:default` + `pointer-events:auto`)
> dim thêm bản tối để đủ tương phản ở theme tối.
>
> **Checkbox/radio áp cùng công thức** (atlas cũng có bản sáng/tối cho mỗi on/off):
>
> ```jsonc
> "checkbox": {
>   "rect":   [258, 850, 12, 12],                 // ENABLED + unchecked (sáng)
>   "states": {
>     "checked":          [354, 850, 12, 12],     // ENABLED + checked   (sáng, có dấu)
>     "disabled":         [210, 850, 12, 12],     // DISABLED + unchecked (tối)
>     "checked-disabled": [306, 850, 12, 12]      // DISABLED + checked   (tối, có dấu)
>   }
> }
> ```
>
> Kết hợp với việc selector `pressed`/`checked-pressed` loại hẳn element disabled ⇒
> toggle bị khoá **cũng không đổi sprite** dù JS có thêm `.pressed`.

---

## 5. Bộ component hiện có (96 slice + 36 state → 1488 ảnh, bộ `set1`)

| Nhóm (guideline) | Slice |
|---|---|
| PANELS | `panel`, `panel-slim` *(9-slice 2 chiều)*; `panel-textured` *(9-slice, **chỉ kéo dọc**)*; `panel-header`, `panel-title` *(cố định)* |
| PUSH BUTTONS | `button`, `button-slim`, `button-thin`, `button-tiny` *(base sáng = enabled / `pressed` / `disabled` tối — khoá cứng)* |
| SLIDERS | `slider-track-v`, `slider-track-h` *(slice `[t,r,b,l]` giữ 2 mũi tên)*, `slider-thumb-v`, `slider-thumb-h` |
| DIVIDERS | `divider-v`, `divider-h` |
| SLOTS | `slot` *(+active)*, `slot-sm`, `slot-md` *(+active)*, `slot-wide`, `slot-pill`, `slot-lg` — **tất cả `nine:false`** (ô túi đồ cố định) |
| CHECK BOXES | `radio`, `checkbox` *(+pressed/checked/checked-pressed)* |
| TOGGLE BUTTONS | `toggle-v`, `toggle-h` *(+pressed/checked/checked-pressed)* |
| TABS | `tab-cap-top/left/right/bottom` *(**NẮP** tab nhỏ 16×12 / 12×16, +active = khung nâng 16×16)*; `tab-top`, `tab-bottom`, `tab-left`, `tab-right` *(**CẠNH** khung tab lớn 48×12 / 12×48, +active)* |
| ICONS *(sheet `icons`)* | `icon-person`, `icon-craft` (búa+đe), `icon-orb`, `icon-heart`, `icon-bolt`, `icon-shield`, `icon-shield-2`, `icon-swords`, `icon-plus`, `icon-drop`, `icon-boot`, `icon-pan`, `icon-chest`, `icon-chest-gem`, `icon-bricks`, `icon-barrel`, `icon-pickaxe`, `icon-bottle`, `icon-bottle-blue`, `icon-hammer`, `icon-water`, `icon-face` — sprite 8×8, `themed:false` |
| GRIDS *(sheet `grids`)* | `grid-cell`, `grid-cell-sm`, `grid-cell-bracket`, `grid-3x3`, `grid-6x6` (+ bản `-ornate`) — ô lưới item, `themed:false` |
| DECORATION | `decoration-top-arch`, `decoration-top-bar`, `decoration-bottom-arch`, `decoration-bottom-bar`, `decoration-side-1..4` — móc/hoa văn viền panel (`side-1/2` rộng 10px, `side-3/4` hẹp 6px) |
| WINDOW BUTTONS | `window-btn-min`, `window-btn-max`, `window-btn-close` — 6×6, state `hover` (trong `@media (hover:hover)`) + `pressed` |
| RESOURCES BARS & CONTAINERS | `bar-h`/`bar-h-md`/`bar-h-sm`/`bar-h-xs` *(4 cỡ ngang)*, `bar-v`/`bar-v-md`/`bar-v-sm`/`bar-v-xs` *(4 cỡ dọc)* — có `overlays` neo hoạ tiết tâm; `container`, `container-md`, `container-sm` |
| RESOURCE FILLS | `bar-fill-{red,blue,gold,green,purple}`, `bar-fill-v-{…}` *(themed:false)* |

Ghi chú ngữ nghĩa:
- `panel-header`/`panel-title` = thanh header ngắn gắn trên panel.
- **TABS = sprite cố định** (`nine:false`) — dùng ở kích thước gốc, không kéo giãn.
  `tab-cap-<side>` = **nắp** tab (chọn `side` theo mép panel mà tab gắn vào); icon của
  tab dán **đè lên nắp** bằng một sprite từ sheet `icons` (xem mục 2.2 / 2.3).
- **ICONS** = sprite 8×8 native ⇒ muốn khớp ô 16px thì vẽ ở **2×** (vẫn là bội số nguyên).
- **GRIDS** = `grid-cell-bracket` (1 ô 32×32, 4 gạch ở 4 góc) lặp lại thành lưới item;
  đúng kiểu ô rỗng trong `mock_up_1.png`. 5 style × 5 tông màu, manifest dùng block 0.
- `panel-header`, `panel-title` = header cố định (`nine:false`) — hoạ tiết ở giữa sprite
  nên **không kéo dài** (nếu kéo sẽ lặp hoạ tiết).
- **SLOTS = ô túi đồ (item cell)** — sprite cố định, **KHÔNG 9-slice** (`nine:false`);
  dùng làm background của từng ô, đổi `active` khi ô được chọn.
- `bar-h`/`bar-v` = thanh resource (ngang/dọc); `container*` = gauge tròn.
- `bar-fill-*` = phần đầy (màu theo cột atlas → `themed:false`).

---

## 6. Quy tắc pixel-perfect (bắt buộc)

1. **Scale nguyên**: ảnh 2x/3x là bội nguyên của 1x, upscale **NEAREST** (không nội suy).
2. **`repeat`, không `stretch`** — cạnh tile ở kích thước native (xem
   [ui-pixel-perfect-9slice.md](./ui-pixel-perfect-9slice.md)).
   Chỉ dùng 9-slice cho **panel / button / slider-track / bar / bar-fill**; các sprite
   còn lại (tab, header, slot, check/toggle, divider, container, tab-icon) là **cố định**.
3. **`border-image-slice` == `border-width`**, nhân theo scale.
4. **Center của 9-slice nên là màu đặc** để `fill` không lộ méo.
5. **Cùng hệ scale** giữa sprite mẹ và sprite con.
6. **`slice [t,r,b,l]`** khi sprite chỉ có hoạ tiết ở 2 đầu (giữ đầu, tile giữa).

Packer **validate** và fail nếu: rect ngoài biên, `slice*2 >= min(w,h)`, hoặc
theme/state không hợp lệ.

---

## 7. Lệnh & output

```bash
npm run ui:pack                         # validate + xuất tất cả (mặc định)
python tools/ui-pack.py --themes dark   # chỉ 1 theme
python tools/ui-pack.py --no-write      # chỉ validate, không ghi file
```

Yêu cầu: Python 3 + `Pillow` (`pip install Pillow`). Preview: `npm run watch:client`
→ `http://localhost:8008/ui-lab.html`.

| Output | Nội dung |
|---|---|
| `client/img/{1,2,3}/ui-kit/<name>.png` | sprite theme mặc định (dark) |
| `client/img/{1,2,3}/ui-kit/<name>--<state>--<theme>.png` | state / theme khác |
| `client/css/ui-slices.generated.css` | class `.ui-*` + state + theme + 3 scale |
| `client/ui-lab.html` | trang preview dev — gallery slice **+ UI kit component tương tác** (sinh từ `tools/uilab_kit.py`) |
| `client/ui-mockup.html` | **trang để artist tự xếp UI** (sinh từ `tools/ui-mockup.py`) — chọn sprite, đặt vào ô lưới, thêm BẢNG, chỉnh cột/hàng, export JSON |
| `client/ui-slice-editor.html` | **editor kéo slice bằng tay** (sinh bởi `tools/make-slice-editor.py`), có chọn theme + dải so sánh 5 theme |
| `tools/ui/out/preview.png` | ảnh self-test 9-slice/state |
| `tools/ui/out/generated.json` | index file đã sinh (dùng để **tự dọn file cũ**) |

Xem riêng gallery component (bỏ qua gallery slice) để chụp/soi nhanh:
`http://localhost:8008/ui-lab.html?only=1` — thêm `#k-mock` để nhảy thẳng tới mockup.
Trên trang có nút **Components only** đổi qua lại.

### 7.1 Trang mockup — artist tự xếp UI (`client/ui-mockup.html`)

```bash
npm run watch:client     # → http://localhost:8008/ui-mockup.html
```

Mở trang là có sẵn **mẫu giống `ed.png`** (3 nắp tab · thanh ngang · rail dọc · bảng).

| Vùng | Làm gì |
|---|---|
| **Trái** | Palette toàn bộ 85 sprite + icon vật phẩm, gom theo nhóm, có ô tìm. Kéo vào canvas hoặc click để thả vào ô trống đầu tiên. |
| **Giữa** | **Canvas** = lưới `cols × rows`, mỗi ô `cell` px. Bật/tắt lưới toạ độ. Kéo món để đổi ô. `arrows` / `Delete` / `Esc`. |
| **Phải** | Inspector món đang chọn + danh sách món + **JSON**. |

Hai loại món:

```jsonc
// 1 sprite đặt vào lưới
{ "kind":"sprite", "name":"tab-cap-top", "c":2, "r":0, "cs":1, "rs":1,
  "mode":"fit|stretch|tile", "state":"active", "label":"", "icon":"item-sword1" }

// 1 BẢNG: sprite làm base + lưới ô bên trong (ý tưởng "base rồi tạo col/row")
{ "kind":"table", "name":"panel", "cell":"grid-cell-bracket",
  "cellSize":32, "gap":2, "c":1, "r":2, "cs":5, "rs":6 }
```

Top-level doc:

```jsonc
{ "name":"inventory-window", "theme":"dark", "scale":2,
  "cols":6, "rows":8, "cell":32, "bg":true, "items":[ … ] }
```

Quy trình làm việc:

1. Artist mở trang, xếp UI, bấm **Copy JSON** → gửi JSON (hoặc file) cho agent.
2. Agent dựng component thật theo JSON: `kind:"table"` → `.ui-panel` + lưới
   `.ui-grid-cell-bracket`; `kind:"sprite"` → đúng class `.ui-<name>` + state.
3. `cell`, `gap`, `cellSize` trong JSON là **toạ độ ô lưới**, không phải pixel cuối —
   khi dựng thật thì nhân với scale (1x/2x/3x) theo quy tắc pixel-perfect (mục 6).

**Lưu ý kỹ thuật:** trang inline CSS nhưng **ép về đúng khối 1x** và `scope_css()`
thêm tiền tố `.mk-canvas` / `.mk-pal` vào mọi selector (đồng thời bỏ `../` trong
`url()` vì CSS nằm cùng cấp với `client/img`). Nhờ vậy canvas luôn **1:1 pixel** và
việc phóng to do `zoom` (bội số nguyên + `image-rendering:pixelated`) ⇒ không nội suy.

`client/css/main.css` đã `@import 'ui-slices.generated.css';` → class dùng được
ngay trong game. `client/img/` và `client/css/` được `copy-webpack-plugin` copy
sang `dist/` nên không cần đổi build.

---

## 8. Quy trình thêm/sửa một component

1. Mở `set_use_guidelines.png`, xác định **nhóm** và toạ độ `[x,y,w,h]` (block UI, y≥544).
2. Thêm entry vào `slices.json` (đặt tên theo nhóm, không theo hình dạng).
3. Chạy `npm run ui:pack`.
4. **Chỉnh `slice` bằng editor**: `npm run watch:client` → mở
   `http://localhost:8008/ui-slice-editor.html` → chọn slice, **kéo 4 đường**
   (cam = trái/phải, đỏ = trên/dưới) → xem preview tile realtime → **Copy JSON slice**
   → dán vào `slices.json` → chạy lại packer.

   Editor hỗ trợ **theme**: chọn `dark/green/blue/red/white` ở thanh trên (hoặc bấm
   phím `1`-`5`) → mọi preview đổi cột atlas theo `themes.offsets`; dải **SO SÁNH THEME**
   render cùng slice ở cả 5 cột để đối chiếu. `rect`/`slice`/`overlays` luôn ở **toạ độ
   base (dark)** — đúng như `slices.json` lưu — nên JSON copy ra dán được ngay.
   Slice có `"themed": false` (bar-fill màu) không đổi theo theme.

   **Chọn `slice` để không bị sọc khi `repeat`** (lỗi đã gặp ở panel/panel-slim/panel-textured):
   `slice` phải phủ hết bề dày hoạ tiết viền (kể cả hàng dither/shadow nằm sát nền — thiếu 1px
   là tile nuốt hàng đó ⇒ **sọc đậm lặp lại**, chỉ thấy rõ ở theme sáng vì theme dark che mất);
   và bước lặp của dải viền (`w-l-r` theo ngang, `h-t-b` theo dọc) phải chia hết chu kỳ hoạ tiết
   của atlas (art panel/button vẽ theo chu kỳ **32px** ⇒ sprite 48px dùng `slice: 8`; `7` cho
   34px = lệch pha 2px ⇒ sọc). Sprite hẹp 16px (`panel-slim`, `button-slim`, `button-thin`)
   không thể đặt `8` cho cả 2 chiều (`l+r ≥ w` bị packer chặn) ⇒ dùng slice **theo từng cạnh**:
   `panel-slim`/`button-slim` = `[8, 7, 8, 7]`, `button-thin` = `[7, 8, 7, 8]`.
5. Kiểm tra `tools/ui/out/preview.png` (ghép 9-slice không méo) và `ui-lab.html`.

   `ui-lab.html` có 2 phần: **gallery slice** (mọi slice × size × state, resize cửa sổ để thử
   1x/2x/3x) và **UI kit** (component ghép sẵn, tương tác được: button, switch, checkbox/radio,
   tab ngang/dọc/vuông, slider, input field, thanh HP/MP, inventory + hotbar, panel/dialog,
   gauge, HUD mock). Kit do [`tools/uilab_kit.py`](../tools/uilab_kit.py) sinh và được packer
   nhúng inline vào lab ⇒ **dev-only**, không ảnh hưởng CSS/asset của game.
6. Dùng class `.ui-<tên>` trong markup.

> Editor sinh tự động bởi packer (nhúng manifest hiện tại) nên luôn đồng bộ.
> Chạy riêng: `python tools/make-slice-editor.py`.

Packer tự dọn file của lần chạy trước không còn trong manifest → **không để lại rác**.

Cơ chế: index `tools/ui/out/generated.json` **nằm trong thư mục đã gitignore**, nên sau khi
clone về nó rỗng ⇒ file rác của manifest cũ sẽ sống mãi (đã xảy ra: 5 tên
`bar_body` `bar_left` `bar_right` `close` `close_pressed` — 135 file, đã tracked trong git).
Nay packer **quét luôn** `client/img/{1,2,3}/ui-kit/*.png` — thư mục đó chỉ chứa sprite do
packer sinh — và xoá mọi file không nằm trong manifest hiện tại.

---

## 9. Checklist trước khi bàn giao

- [ ] `python tools/ui-pack.py --no-write` → `validation: OK`.
- [ ] Không có sọc lặp ở theme sáng (green/blue/red/white): `slice` ≥ bề dày hoạ tiết viền và
      bước lặp `w-l-r` / `h-t-b` chia hết chu kỳ hoạ tiết (32px) — xem mục 8.
- [ ] Mọi `url()` trong CSS sinh ra đều tồn tại (packer tự đảm bảo).
- [ ] `ui-lab.html` render đủ component ở 1x/2x/3x, state nhìn đúng.
- [ ] `panel.png` sinh ra **bit-identical** với asset thủ công cũ.
- [ ] Không còn file cũ/tên sai trong `client/img/*/ui-kit/`.
- [ ] Asset thủ công (`bar_body`, `bar_left`, `bar_right`, `close`, `close_pressed`) còn nguyên.
- [ ] `game.ts` không đụng DOM; UI module nằm trong `client/ts/ui/`.

---

## 10. Hạn chế & roadmap

- **~1485 ảnh** (54 slice + 34 state, 5 theme × 3 scale) — có thể gộp atlas / tint runtime để giảm.
- **Disabled không có sprite riêng** — dùng CSS filter nếu cần.
- **Editor (`client/ui-slice-editor.html`)**: sửa `slices.json` bằng tay hoặc copy JSON
  slice từ editor (editor sinh từ manifest: `python tools/make-slice-editor.py`;
  nhớ chạy lại sau khi thêm slice mới).
