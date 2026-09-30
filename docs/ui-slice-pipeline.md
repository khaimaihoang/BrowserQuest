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
            ├─► tools/ui-pack.py ──┬─► client/img/{1,2,3}/ui/<name>.png   (NEAREST, ×1/×2/×3)
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
| RESOURCE'S BARS & CONTAINERS | 635–856 | 756–988 |
| PUSH BUTTONS | 4 cỡ (16×16 / 48×16 / 16×48 / 48×48) | y≈1040 / 1088 |

> **Bài học:** tên slice phải bám **nhóm trong guideline**, không đoán theo hình
> dạng. (Đã từng đặt sai: `divider-fancy-*` thực ra thuộc SLIDERS; các thanh
> `x416–592` thực ra thuộc TABS chứ không phải resource bars.)

---

## 3. Manifest — schema

File: [`tools/ui/slices.json`](../tools/ui/slices.json)

### 3.1 Cấp cao (top-level)

| Khoá | Ý nghĩa |
|---|---|
| `source` | đường dẫn atlas (tương đối repo root) |
| `grid` | kích thước ô lưới (16) |
| `themes.default` / `themes.offsets` | theme mặc định + offset x từng cột |
| `scales` | `[1,2,3]` — các hệ số upscale NEAREST |
| `output.image/css/lab/preview` | đường dẫn output (`{scale}` được thay) |
| `css.prefix` | tiền tố class (`ui` → `.ui-panel`) |

### 3.2 Mỗi slice

```jsonc
"button": {
  "rect": [208, 544, 48, 48], // [x, y, w, h] theo pixel atlas (theme dark) — base = look enabled
  "nine": true,                // true = 9-slice; false = sprite rời
  "slice": 8,                  // bề dày viền: int (4 cạnh bằng nhau) HOẶC [t,r,b,l]
  "repeat": "repeat",          // CSS border-image-repeat ('repeat' = pixel-perfect)
  "states": {                  // tuỳ chọn — sinh sprite + selector cho từng state
    "pressed":          [464, 544, 48, 48],
    "disabled":         [ 80, 544, 48, 48],
    "disabled-pressed": [336, 544, 48, 48]
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

- `disabledFilter` = CSS `filter` áp cho `:disabled/.disabled/[aria-disabled='true']`
  (thêm dòng `filter:` sau state), dùng cho sprite mà atlas **không có bản tối**
  (`toggle-h`, `toggle-v`; xem §4).

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
- Khoá `_comment_*` trong `slices` được packer bỏ qua (dùng để chia nhóm cho dễ đọc).

---

## 4. Mô hình STATE — touch-first

Mobile **không có hover** (button/switch **không khai báo `hoverUses`** ⇒ không sinh
rule `:hover`); state gốc là `pressed`/`active`/`checked`/`disabled`. Quy ước:
**sprite sáng = dùng được (enabled / on), sprite tối = `disabled`**.

| State | Ý nghĩa | Selector sinh ra |
|---|---|---|
| `pressed` | enabled + đang nhấn (sáng nhấn) | `:active`, `.pressed` |
| `disabled` | vô hiệu (sprite tối) | `:disabled`, `[disabled]`, `.disabled`, `[aria-disabled='true']` |
| `disabled-pressed` | vô hiệu + đang nhấn (tối nhấn) | `.disabled.pressed`, `.disabled:active`, `[disabled].pressed`, `[disabled]:active`, `:disabled.pressed`, `:disabled:active`, `[aria-disabled='true'].pressed`, `[aria-disabled='true']:active` |
| `active` | bật / đang chọn | `.active`, `[aria-selected='true']`, `[aria-pressed='true']` |
| `active-pressed` | `active` + đang nhấn | `.active.pressed`, `.active:active`, `[aria-pressed='true']:active` |
| `checked` | on (checkbox/switch) | `:checked`, `.checked`, `[aria-checked='true']` |
| `checked-pressed` | on + đang nhấn | `:checked:active`, `.checked.pressed` |
| `checked-disabled` | on + vô hiệu | `:checked:disabled`, `.checked.disabled` |
| `hover` | chỉ desktop | `:hover`, `.hover` — **bọc trong `@media (hover: hover)`** |

**Button là ma trận 2×2** `{enabled, disabled} × {chưa nhấn, đã nhấn}`; **base = look
enabled (sáng)**; nhấn nút disabled → tối-nhấn, thả ra → tối thường:

```jsonc
"button": {
  "rect": [208, 544, 48, 48],             // enabled (sáng, chưa nhấn) = base
  "states": {
    "pressed":          [464, 544, …],   // sáng, đã nhấn
    "disabled":         [ 80, 544, …],   // tối
    "disabled-pressed": [336, 544, …]    // tối, đã nhấn
  }
  // KHÔNG hoverUses ⇒ không có trạng thái hover
}
```

CSS sinh ra (thứ tự cascade: base → theme base → state → theme state → alias →
``disabledFilter`` → hover):

```css
.ui-button { /* base = enabled (sáng) */ }
.ui-button:disabled, .ui-button[disabled], .ui-button.disabled, .ui-button[aria-disabled='true']  { border-image-source: url('…--disabled.png'); }
.ui-button[disabled].pressed, .ui-button[aria-disabled='true'].pressed, …                        { border-image-source: url('…--disabled-pressed.png'); }
.ui-button:active, .ui-button.pressed                                                            { border-image-source: url('…--pressed.png'); }
```

> `[disabled]` (attribute trên div giả lập) **bắt buộc có** — game set/remove attribute này
> để MutationObserver cập nhật sprite; thiếu nó thì nút disabled vẫn hiện look enabled
> (nhấn xuống nhưng không khoá).

> **Toggle/checkbox/radio không có sprite tối trong atlas** (4 sprite = {off,on} ×
> {chưa nhấn, nhấn}) → dùng khoá `disabledFilter`, packer emit filter cho team
> `disabled`, nhờ vậy **on & off đều thành tối khi vô hiệu**:
>
> ```jsonc
> "toggle-h": { "disabledFilter": "brightness(.62) saturate(.75)", … }
> ```
>
> ```css
> .ui-toggle-h:disabled, .ui-toggle-h.disabled, .ui-toggle-h[aria-disabled='true'] { filter: brightness(.62) saturate(.75); }
> ```

---

## 5. Bộ component hiện có (54 slice + 34 state)

| Nhóm (guideline) | Slice |
|---|---|
| PANELS | `panel`, `panel-slim` *(9-slice 2 chiều)*; `panel-textured` *(9-slice, **chỉ kéo dọc**)*; `panel-header`, `panel-title` *(cố định)* |
| PUSH BUTTONS | `button`, `button-slim`, `button-thin`, `button-tiny` *(2×2 state)* |
| SLIDERS | `slider-track-v`, `slider-track-h` *(slice `[t,r,b,l]` giữ 2 mũi tên)*, `slider-thumb-v`, `slider-thumb-h` |
| DIVIDERS | `divider-v`, `divider-h` |
| SLOTS | `slot` *(+active)*, `slot-sm`, `slot-md` *(+active)*, `slot-wide`, `slot-pill`, `slot-lg` — **tất cả `nine:false`** (ô túi đồ cố định) |
| CHECK BOXES | `radio`, `checkbox` *(+pressed/checked/checked-pressed)* |
| TOGGLE BUTTONS | `toggle-v`, `toggle-h` *(+pressed/checked/checked-pressed)* |
| TABS | `tab-icon-1..4` *(tab icon, +active)*; `tab-top`, `tab-bottom`, `tab-left`, `tab-right` *(sprite cố định, +active)* |
| RESOURCES BARS & CONTAINERS | `bar-h`/`bar-h-md`/`bar-h-sm`/`bar-h-xs` *(4 cỡ ngang)*, `bar-v`/`bar-v-md`/`bar-v-sm`/`bar-v-xs` *(4 cỡ dọc)* — có `overlays` neo hoạ tiết tâm; `container`, `container-md`, `container-sm` |
| RESOURCE FILLS | `bar-fill-{red,blue,gold,green,purple}`, `bar-fill-v-{…}` *(themed:false)* |

Ghi chú ngữ nghĩa:
- `panel-header`/`panel-title` = thanh header ngắn gắn trên panel.
- **TABS = sprite cố định** (`nine:false`) — thanh mảnh 1-đường-kẻ; dùng ở kích
  thước gốc, không kéo giãn. `tab-icon-*` = tab nhỏ cho icon (normal/active).
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
| `client/img/{1,2,3}/ui/<name>.png` | sprite theme mặc định (dark) |
| `client/img/{1,2,3}/ui/<name>--<state>--<theme>.png` | state / theme khác |
| `client/css/ui-slices.generated.css` | class `.ui-*` + state + theme + 3 scale |
| `client/ui-lab.html` | trang preview dev — gallery slice **+ UI kit component tương tác** (sinh từ `tools/uilab_kit.py`) |
| `client/ui-slice-editor.html` | **editor kéo slice bằng tay** (sinh bởi `tools/make-slice-editor.py`), có chọn theme + dải so sánh 5 theme |
| `tools/ui/out/preview.png` | ảnh self-test 9-slice/state |
| `tools/ui/out/generated.json` | index file đã sinh (để **tự dọn file cũ**) |

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

---

## 9. Checklist trước khi bàn giao

- [ ] `python tools/ui-pack.py --no-write` → `validation: OK`.
- [ ] Không có sọc lặp ở theme sáng (green/blue/red/white): `slice` ≥ bề dày hoạ tiết viền và
      bước lặp `w-l-r` / `h-t-b` chia hết chu kỳ hoạ tiết (32px) — xem mục 8.
- [ ] Mọi `url()` trong CSS sinh ra đều tồn tại (packer tự đảm bảo).
- [ ] `ui-lab.html` render đủ component ở 1x/2x/3x, state nhìn đúng.
- [ ] `panel.png` sinh ra **bit-identical** với asset thủ công cũ.
- [ ] Không còn file cũ/tên sai trong `client/img/*/ui/`.
- [ ] Asset thủ công (`bar_body`, `bar_left`, `bar_right`, `close`, `close_pressed`) còn nguyên.
- [ ] `game.ts` không đụng DOM; UI module nằm trong `client/ts/ui/`.

---

## 10. Hạn chế & roadmap

- **~1485 ảnh** (54 slice + 34 state, 5 theme × 3 scale) — có thể gộp atlas / tint runtime để giảm.
- **Disabled không có sprite riêng** — dùng CSS filter nếu cần.
- **Editor (`client/ui-slice-editor.html`)**: sửa `slices.json` bằng tay hoặc copy JSON
  slice từ editor (editor sinh từ manifest: `python tools/make-slice-editor.py`;
  nhớ chạy lại sau khi thêm slice mới).
