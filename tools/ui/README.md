# UI Slice Pipeline (Minifantasy)

Biến atlas UI (một tấm PNG lớn, không có tên từng phần) thành **asset + CSS dùng
được ngay** trong game, theo một manifest có tên gọi rõ ràng.

- 📖 **Tài liệu đầy đủ: [`docs/ui-slice-pipeline.md`](../../docs/ui-slice-pipeline.md)**
- **Kit component tương tác: [`client/ui-lab.html`](../../client/ui-lab.html)** (§ *UI kit*)
  — sinh từ [`tools/uilab_kit.py`](../uilab_kit.py): button, switch/toggle, checkbox & radio,
  tab (ngang / dọc / vuông-icon), slider (kéo được, ngang + dọc), input field (focus ring +
  stepper + chat bar), thanh HP/MP/XP/Stamina (ngang + dọc), inventory 5×2 + hotbar (phím `1-6`),
  panel + list row + dialog + toast, gauge tròn, HUD mock. Nút **Components only** ở toolbar
  để ẩn gallery slice. Dev-only: CSS/JS nằm inline trong lab, không nằm trong CSS ship game.
- Manifest: [`tools/ui/slices.json`](./slices.json)
- Packer: [`tools/ui-pack.py`](../ui-pack.py)
- Preview dev: [`client/ui-lab.html`](../../client/ui-lab.html)
- **Editor kéo slice: [`client/ui-slice-editor.html`](../../client/ui-slice-editor.html)** (`python tools/make-slice-editor.py`)
  — kéo 4 đường slice, thêm hoạ tiết tâm, **chọn theme màu** (`dark/green/blue/red/white`,
  phím `1`-`5`) và **so sánh 5 theme cạnh nhau** cùng một `rect`; JSON copy ra ở toạ độ
  base (dark) đúng như `slices.json`
- ⚠️ **Quy tắc `slice` chống sọc:** `slice` phải phủ hết bề dày hoạ tiết viền và bước lặp
  (`w-l-r` / `h-t-b`) phải chia hết chu kỳ hoạ tiết atlas (32px) — thiếu 1px ⇒ sọc đậm lặp lại,
  chỉ thấy ở theme sáng. Chi tiết: [`docs/ui-slice-pipeline.md` §8](../../docs/ui-slice-pipeline.md)
- CSS sinh ra: `client/css/ui-slices.generated.css` (đã `@import` trong `main.css`)

> Trang này là bản tóm tắt thao tác nhanh; chi tiết schema/state/nhóm nằm trong
tài liệu ở `docs/`.

## Pipeline

```
atlas PNG ──┐
            ├─► tools/ui-pack.py ──┬─► client/img/{1,2,3}/ui/<name>.png   (NEAREST, ×1/×2/×3)
slices.json ┘                     ├─► client/css/ui-slices.generated.css  (border-image + states)
                                  ├─► client/ui-lab.html                  (preview dev + UI kit)
                                  └─► tools/ui/out/preview.png            (self-test 9-slice/state)

tools/uilab_kit.py  ──► nhúng kit component tương tác vào client/ui-lab.html
```

## Lệnh

```bash
npm run ui:pack                         # validate + xuất tất cả
python tools/ui-pack.py --themes dark   # chỉ 1 theme
python tools/ui-pack.py --no-write      # chỉ validate, không ghi file
```

Yêu cầu: Python 3 + `Pillow`. Sau khi chạy, `npm run watch:client` → mở
`http://localhost:8008/ui-lab.html`.

> Packer tự dọn file cũ (index `tools/ui/out/generated.json`); file của lần chạy
> trước không còn trong manifest sẽ bị xoá, không đụng asset thủ công.

## Mô hình STATE — touch-first

Mobile **không có hover** (button/switch không khai báo `hoverUses` ⇒ không sinh rule
`:hover`); state lấy `pressed`/`active`/`checked`/`disabled` làm gốc. Quy ước:
**sprite sáng = dùng được (enabled / on), sprite tối = `disabled`**.

| State | Ý nghĩa | Selector sinh ra |
|---|---|---|
| `pressed` | enabled + đang nhấn (sáng nhấn) | `:active`, `.pressed` — có `:not(:disabled):not([disabled]):not(.disabled):not([aria-disabled])` |
| `disabled` | vô hiệu = **KHOÁ CỨNG** (sprite tối, nhấn không đổi sprite) | `:disabled`, `[disabled]`, `.disabled`, `[aria-disabled='true']` + `pointer-events:none` |
| `active` | bật / đang chọn | `.active`, `[aria-selected='true']`, `[aria-pressed='true']` |
| `active-pressed` | `active` + đang nhấn | `.active.pressed`, `.active:active` |
| `checked` | on (checkbox/switch) | `:checked`, `.checked`, `[aria-checked='true']` |
| `checked-pressed` | on + đang nhấn | `:checked:active`, `.checked.pressed` |
| `hover` | chỉ desktop | `:hover`, `.hover` — bọc trong `@media (hover: hover)` |

`hoverUses: "<state>"` (tuỳ chọn) → map `:hover` sang sprite của state có sẵn (không
sinh thêm file), bọc trong `@media (hover: hover)`.

Button = **enabled {chưa nhấn, đã nhấn} + disabled (khoá cứng)**; **base = look enabled
(sáng)**; nút disabled giữ nguyên sprite tối dù có nhấn (selector `pressed`/`checked-pressed`
đã loại hẳn element disabled, cộng thêm `pointer-events:none`):

```jsonc
"button": {
  "rect": [208, 544, 48, 48],          // enabled (sáng, chưa nhấn) = base
  "states": {
    "pressed":  [464, 544, …],         // sáng, đã nhấn
    "disabled": [ 80, 544, …]          // tối — khoá cứng (không có state *-pressed)
  }
  // KHÔNG khai báo hoverUses ⇒ không có trạng thái hover
}
```

`alias: { "x": "y" }` (tuỳ chọn) → map thêm selector của state `x` sang sprite
của state `y`, không sinh file.

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
> `disabledFilter` (filter cho team `disabled` + `pointer-events:none`) vẫn có sẵn cho slice
> nào *không* có bản tối trong atlas.
>
> ⚠️ Game dùng **div giả lập + attribute `disabled`** (MutationObserver) — nên `[disabled]`
> là selector chính, đứng ngang hàng `:disabled`/`.disabled`/`[aria-disabled]`.
>
> ⚠️ Game dùng **div giả lập + attribute `disabled`** (MutationObserver) — nên `[disabled]`
> là selector chính, đứng ngang hàng `:disabled`/`.disabled`/`[aria-disabled]`.

## Manifest — schema

```jsonc
"button": {
  "rect": [80, 544, 48, 48],   // [x, y, w, h] theo pixel atlas (theme dark)
  "nine": true,                // true = 9-slice, false = sprite rời
  "slice": 7,                  // bề dày viền nguồn (px) — phải < min(w,h)/2
  "repeat": "repeat",          // CSS border-image-repeat
  "states": {
    "active":  [208, 544, 48, 48],
    "pressed": [336, 544, 48, 48]
  },
  "hoverUses": "active"        // tuỳ chọn — desktop hover tái dùng sprite active
}
```

`"themed": false` → slice chỉ xuất **1 bản** (không theo theme), dùng cho các
**bar-fill màu** (đỏ/xanh/vàng/lục/tím) vì màu nằm ở từng cột atlas chứ không
phải theo theme.

## Bộ component (54 slice + 34 state)

Tên slice nay bám đúng **nhóm trong `set_use_guidelines.png`** (không đoán theo hình
 dạng nữa). Toạ độ nhóm (block "UI", = block gốc + 544):
`PANELS x54-266 y646-762` · `DIVIDERS x298-375 y652-708` · `SLIDERS x287-383 y715-770` ·
`CHECK BOXES x205-370 y807-866` · `TOGGLE BUTTONS x205-370 y884-943` · `SLOTS x29-184 y765-985` ·
`TABS x154-618 y631-1019` · `RESOURCES BARS & CONTAINERS x635-856 y756-988`.

| Nhóm (guideline) | Slice |
|---|---|
| PANELS | `panel`, `panel-slim` *(9-slice 2 chiều)*; `panel-textured` *(9-slice, **chỉ kéo dọc**)*; `panel-header`, `panel-title` *(cố định)* |
| PUSH BUTTONS | `button`, `button-slim`, `button-thin`, `button-tiny` *(base sáng = enabled / `pressed` / `disabled` tối — khoá cứng)* |
| SLIDERS | `slider-track-v`, `slider-track-h` *(slice 4 cạnh, giữ 2 mũi tên)*, `slider-thumb-v`, `slider-thumb-h` |
| DIVIDERS | `divider-v`, `divider-h` |
| SLOTS | `slot` *(+active)*, `slot-sm`, `slot-md` *(+active)*, `slot-wide`, `slot-pill`, `slot-lg` — **ô túi đồ, `nine:false`** |
| CHECK BOXES | `radio`, `checkbox` *(+pressed/checked/checked-pressed)* |
| TOGGLE BUTTONS | `toggle-v`, `toggle-h` *(+pressed/checked/checked-pressed)* |
| TABS | `tab-icon-1..4` *(tab icon, +active)*; `tab-top`, `tab-bottom`, `tab-left`, `tab-right` *(cố định, +active)* |
| RESOURCES BARS & CONTAINERS | `bar-h`/`bar-h-md`/`bar-h-sm`/`bar-h-xs` *(4 cỡ ngang)*, `bar-v`/`bar-v-md`/`bar-v-sm`/`bar-v-xs` *(4 cỡ dọc)* — có `overlays` neo hoạ tiết tâm; `container`, `container-md`, `container-sm` |
| RESOURCE FILLS | `bar-fill-{red,blue,gold,green,purple}`, `bar-fill-v-{…}` *(themed:false)* |

Ghi chú:
- `panel-header`/`panel-title` = thanh header ngắn gắn trên panel.
- `tab-icon-*` = 4 tab-icon (normal/active = cặp trái/phải trong nhóm TABS);
  khung tab ghép từ `tab-top`+`tab-bottom`+`tab-left`+`tab-right` (mỗi cái có active).
- `slice` có thể là int (4 cạnh bằng nhau) hoặc `[t,r,b,l]` — dùng cho slider track
  để **giữ 2 mũi tên** ở hai đầu, chỉ tile phần giữa.
- `slot-lg` là khối nguyên (nine:false), kiểu ô item.
- `bar-h`/`bar-v` = thanh resource (ngang/dọc) — có **hoạ tiết tâm** nên dùng `overlays` (neo bằng pseudo-element).
- `container*` = gauge tròn.
- `bar-fill-*` = phần đầy (màu nằm ở từng cột atlas → `themed:false`).

## Ràng buộc đã đảm bảo

- **Scale nguyên** 1x/2x/3x, upscale NEAREST.
- **`repeat`, không `stretch`** (pixel-perfect, xem
  [`docs/ui-pixel-perfect-9slice.md`](../../docs/ui-pixel-perfect-9slice.md)).
- **`border-image-slice == border-width`**, đổi theo scale.
- **`panel.png` bit-identical** với asset thủ công cũ.

## Hạn chế / bước tiếp theo

- ~840 ảnh (do 5 theme × 3 scale); có thể gộp atlas hoặc tint runtime để giảm.
- Editor kéo slice có sẵn: chọn slice/theme rồi copy JSON (`slice`/`overlays`) dán vào
  `slices.json`, sau đó chạy lại packer. Editor sinh từ manifest nên sau khi thêm slice mới
  phải chạy `python tools/make-slice-editor.py`.
