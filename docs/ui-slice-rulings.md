# UI Slice — Rulings (tổng hợp từ phiên hoàn thiện kit 3 bộ)

> File này chốt **toàn bộ quy tắc (ruling)** rút ra từ phiên sửa pipeline + ui-lab.
> Nguồn kỹ thuật chi tiết: [`ui-slice-pipeline.md`](file:///D:/Develop/Projects/BrowserQuest/docs/ui-slice-pipeline.md),
> [`ui-pixel-perfect-9slice.md`](file:///D:/Develop/Projects/BrowserQuest/docs/ui-pixel-perfect-9slice.md).
> Trạng thái công việc: [`SESSION.md`](file:///D:/Develop/Projects/BrowserQuest/SESSION.md).

---

## 0. TL;DR — checklist trước khi chốt một slice

1. **Namespace**: kit xuất vào `client/img/{scale}/ui-kit/` — **KHÔNG BAO GIỜ** ghi vào `img/<n>/ui/` (asset HUD game).
2. **`rect` luôn ở set1** (bộ mặc định) + theme dark. Bộ khác = `setRect` (khác kích thước) / `setDelta` (chỉ lệch y).
3. **`states` cũng ở set1**. State khác vị trí/kích thước giữa bộ ⇒ khai `stateSetRect`.
4. **`slice` phải phủ hết hoa văn viền**; ornament set2/set3 dày hơn ⇒ `setSlice`.
5. **Thanh kéo 1 chiều** (bar/fill/track/slider) ⇒ `stretch: x|y` ⇒ CSS `border-image-repeat: stretch`.
6. **Fill khít lòng**: cross = **native 6u** (sprite 42×6 / 6×42); `top/left = calc((100% - 6u)/2)`; neo đúng lòng (-11u / +22u); snap integer pixel grid.
7. **Overlay** (`::before/::after`) cần `position: relative` trên **mọi bộ** có overlay.
8. Soát bằng `tools/ui/atlas-check.py` → phải `CUT=0`.
9. Xem bằng `tools/ui/qa.py` / `ui-lab.html` (1 bộ, native + kéo dài).
10. Sinh lại → cache tự bust (`?v=` băm cả manifest + source packer).

---

## 1. Namespace & an toàn tài sản game

| Quy tắc | Chi tiết |
|---|---|
| **Output kit** | `client/img/{1,2,3}/ui-kit/*.png` (manifest `output.image`) |
| **Cấm** | ghi/xoá `client/img/{1,2,3}/ui/` — đó là asset **HUD gốc của game** (`panel.png`, `bar_body/left/right.png`, `close*.png` dùng bởi `main.css`/`panel.css`) |
| **Guard** | packer báo lỗi + dừng nếu `output.image` trỏ lại `img/<n>/ui/` |
| **Dev-server** | serve `dist/client` **TRƯỚC** `client` ⇒ mirror CSS + `ui-lab.html` sang `dist/client` để không bị bản cũ shadow |

> **Bài học**: pipeline từng ghi đè/xoá asset HUD game vì trùng thư mục ⇒ dev-server trả bản cũ từ `dist` ⇒ set1 là art sai, set2/set3 là kit ⇒ "cụt/lệch".

---

## 2. Trục BỘ (set) & THEME

- Theme = trục **x** (5 màu, stride 912). Set = trục **y** (3 bộ, offsets `set2=544`, `set3=1088`).
- **`rect` luôn ghi ở set1**; class set khác = `.set2` / `.set3` (scope CSS, như `.theme-*`).
- CSS: rule bộ mặc định đầy đủ; bộ khác **chỉ override ảnh** — **BẮT BUỘC có tiền tố bộ**:
  ```
  .set2 .ui-panel { … }            ✅
  .ui-panel { … set2 … }           ❌ (đè bộ mặc định)
  ```
- Theme + bộ phải cùng **một** phần tử cha: `.set2.theme-green .ui-x` (runtime: `<body class="set2 theme-green">`; lab: gán class lên chính cell).

---

## 3. `rect` / `setRect` / `setDelta` / `stateSetRect`

| Khoá | Khi nào dùng | Ý nghĩa |
|---|---|---|
| `rect` | luôn có | `[x,y,w,h]` ở **set1**, theme mặc định |
| `setDelta: {set2: n}` | cùng kích thước, **chỉ lệch y** | `y + offsets[set] + n` |
| `setRect: {set2: […]}` | **khác cả kích thước** | rect đầy đủ của bộ đó |
| `stateSetRect: {state: {set2: […]}}` | state khác vị trí/kích thước giữa bộ | rect đầy đủ cho từng state × bộ |

**Ruling quan trọng**: khi có `setRect`, packer **áp DELTA** (`setRect − rect`) lên **mọi** rect (base **hoặc** state) — KHÔNG trả thẳng `setRect` (nếu trả thẳng, mọi state ở set2/3 bị đè về base).

> Bug đã gặp: `rect_for` trả `setRect` cho mọi rect ⇒ state set3 = base set3.

---

## 4. STATE (checkbox/radio/toggle/tab/slot/button…)

- **Mọi `states` phải ghi ở set1.** Nếu bộ khác lệch vị trí/kích thước ⇒ `stateSetRect`.
- Bug điển hình: state khai **ở toạ độ set2** ⇒ set1 lấy art set2, set2/set3 bị cộng delta ⇒ set3 rơi vào **vùng trống**.
- Nhóm có "hàng base + hàng active liền kề" (vd SLOTS/SWITCH): **active = base + offset cố định trong lòng bộ** ⇒ ghi `states.active` = set1, delta tự ra set2/set3.

---

## 5. 9-slice: `slice`, `setSlice`, `repeat` vs `stretch`

- `slice` (t,r,b,l) phải **phủ hết bề dày hoa văn viền**; nếu không, góc/viền bị cắt hoặc lặp.
- `setSlice: {set3: 12}` cho ornament dày hơn ở bộ khác. Khi slice khác bộ mặc định, CSS **phải phát lại `border-width` + `border-image`** (không chỉ đổi source).
- **`border-image-repeat`**:
  - **Thanh kéo 1 chiều** (`stretch: x|y` trong manifest) → **`stretch`** (dải giữa kéo giãn, KHÔNG lặp → hết "sandwich"/nửa sprite).
  - **Hoạ tiết** (panel/button…) → **`repeat`** (hoa văn lặp đều).
  - Packer: hàm `rep_for(spec)` quyết định; **KHÔNG hardcode `repeat`**.
- Sprite **cố định** (`nine:false`) dùng ở size gốc. `stretch`/`repeat` không áp dụng.

---

## 6. FILL — quy tắc khít lòng (pixel-perfect)

### 6.1 Nguyên tắc chung
- **Trục vuông góc (cross) = native** của sprite — nếu element lớn hơn, **viền hai đầu tile** và trông như nhiều thanh ("5 thanh").
- **Trục chính = `pct%`** của **lòng** khung (không phải của padding-box thô).
- **2 mode neo**: ngang `left|right`, dọc `top|bottom`.
- `background`/`border-image` phải khớp lòng; mép fill **chạm đúng pixel lòng**, không đè viền/shadow.

### 6.2 Fill tròn (gauge `container-fill`)
- Sprite = **đúng size khung** (`container` 32 / `md` 24 / `sm` 16), gauge canh giữa.
- Element chồng tại `(0,0)` (cùng size) ⇒ pixel-perfect by construction.
- Nhiều **stage** (14/10/6) = các sprite riêng, đổi class để chạy anim.

### 6.3 Fill thanh (`bar-fill-*` / `bar-fill-v-*`)
- Sprite cắt **TIGHT = art** (42×6 / 6×42), `slice: 7`.
- Element = **lòng đen thật** của bar, neo bằng offset âm vào vùng viền:
  ```
  bar-h: top: calc((100% - 6u)/2) [=3u ở set1]; height: 6u (native);  left/right: -11u;  span = (100% + 22u) * pct
  bar-v: left: calc((100% - 6u)/2) [=3u ở set1]; width: 6u (native);  top/bottom: -11u;  span = (100% + 22u) * pct
  ```
- **Vì sao `height/width: 6u` (cross = native) và `top/left: 3u`**:
  - Sprite fill native dày **6px** (`42×6` / `6×42`), slice cross = 0. Nếu đặt `8u`, CSS `border-image` sẽ kéo giãn 6px lên 8px gây **pixel bleed** (nhoè hàng pixel, vỡ pixel art).
  - Khung `bar-h` (48×12) chừa **3px mỗi mép**: 1px viền đen ngoài + 1px viền highlight + 1px shadow đen lòng ⇒ lòng fill chiếm đúng 6px (y=3..8), chừa đúng 3px trên và 3px dưới (`3 + 6 + 3 = 12px`).
  - Dùng công thức canh giữa `top/left: calc((100% - 6 * var(--u)) / 2)` sẽ tự khớp hoàn hảo cho cả 3 bộ: set1 (12u ⇒ top 3u), set2 (20u ⇒ top 7u), set3 (28u ⇒ top 11u).
- **Vì sao `-11` / `+22`**: bar-h border `14`, lòng thật chừa **3px mỗi đầu** (1 viền + 2 shadow)
  ⇒ offset = `-(14 − 3) = -11`, span = `100% + 2*(14 − 3) = +22`.
- **Công thức tổng quát**: `offset = -(border − pad)`, `span = 100% + 2*(border − pad)`, với `pad` = khoảng chừa mỗi đầu trong sprite bar.
- **Tránh pixel bleed trục chính**: JS tính chiều dài fill snap theo đơn vị pixel sprite `units * u`:
  `units = Math.round(((frameLen / u - 6) * pct) / 100); span = units * u + 'px'`.
  Tránh subpixel floating-point (như 60.9px) làm mép bo 7px của `border-image` bị nhoè pixel. Khi `pct === 0`, ẩn fill (`display: none`).

> Bug điển hình: `height: 8u` kéo giãn sprite 6px ⇒ pixel bleed; `border-image: repeat` ⇒ sandwich; sprite 44×8 có đệm ⇒ lệch 1px; `left:14` tính theo padding-box ⇒ lệch +14; `width: 100% − 30u` ⇒ sai bề rộng; frame bị ép `height: 20u` ở set1 làm méo khung 12px.

---

## 7. OVERLAY (hoạ tiết tâm: crown/boss)

- Dùng cho ornament ở **tâm cạnh** (không nằm trong `slice`).
- `overlays` (mọi bộ) / `setOverlays` (theo bộ) + **`overlay.setRect`** (tránh cộng offset 2 lần).
- Sprite base được **clean** (`--ovN` tách riêng); CSS vẽ lại bằng `::before/::after` neo `top/bottom/left/right-center`.
- **BẮT BUỘC**: element có overlay phải được phát `position: relative` ở **mọi bộ** (không chỉ bộ mặc định) — nếu thiếu, pseudo neo sai tổ tiên ⇒ ornament bị cắt.

---

## 8. UI-LAB (dev preview)

- **1 tên = base + mọi state**, 3 bộ cạnh nhau, render ở **native size**.
- Cờ **`demo:false`** ⇒ ẩn slice khỏi gallery (vẫn giữ manifest/CSS). Dùng cho slice "extra" đã soát xong.
- Theme switcher gán theme lên **chính cell** (`[data-cell]`) để selector `.set2.theme-*` khớp.
- **Section ANIM**: container + fill, 3 size × 3 bộ, JS đổi class stage mỗi ~130ms.
- **Build stamp** trên header (`ASSET_VERSION`) để biết đang xem bản nào.
- **Box-sizing/định vị**: element 9-slice thanh phải đặt **cross = native** (nếu không → tile dọc → "5 thanh").

---

## 9. CACHE & BUILD

- **`?v=<md5(manifest + source packer)>`** gắn vào **mọi** `url()` + `<link>` CSS (`ASSET_VERSION`).
  - Băm **cả `ui-pack.py`** — nếu chỉ băm manifest, sửa code packer sẽ **không** bust cache ⇒ vẫn xem sprite cũ.
- Mirror `ui-slices.generated.css` + `ui-lab.html` sang `dist/client` (dev-server serve `dist` trước).
- `<meta http-equiv="cache-control" content="no-store">` trong lab.
- Sinh lại: `npm run ui:pack` (validate → cắt ảnh → CSS → lab/mockup).

---

## 10. CÔNG CỤ SOÁT (bắt buộc trước khi chốt)

| Tool | Việc |
|---|---|
| `python tools/ui/atlas-check.py` | Ghép lại atlas 1 theme × 3 bộ từ sprite đã xuất, so với gốc: `full / CUT / unused` — **CUT phải = 0** |
| `python tools/ui/qa.py <slice…>` | Ảnh QA 1 phát: mọi bộ × native + kéo dài |
| `python tools/ui-pack.py --no-write` | Validate schema + bounds + slice |
| `ui-lab.html` / `ui-lab.html?only=1` | Xem gallery + kit (kéo chuột/chạm) |

---

## 11. NGUỒN CHUẨN (đo từ đâu)

- **`Grim_UI.aseprite`** (Aseprite): mở bằng CLI
  ```
  Aseprite.exe -b Grim_UI.aseprite --split-layers --save-as L_{layer}.png
  → 6 layer: Bg · Grim_UI (art) · Guidelines (khung+nhãn nhóm) · Outline · Shadow · UI_Bg
  ```
  **Không có `--list-slices`/tags** ⇒ aseprite **không** có metadata tên từng sprite → phải **đo từ art**.
- **`_Use_Guidelines/set_use_guidelines.png`**: khung + **nhãn NHÓM** (PANELS, SLOTS, RESOURCE METERS, TOGGLE BUTTONS…) — dùng để đặt tên/ phân nhóm, không có tên từng sprite.
- **`_grim_ui.png`**: atlas gốc để đo/verify.
- **Studio's Shadow layer** = lớp bóng; fill phải chừa **1px shadow** ở hai đầu lòng.

---

## 12. ANTI-PATTERN (đừng lặp lại)

| ❌ Sai | ✅ Đúng |
|---|---|
| Ghi kit vào `img/<n>/ui/` | `img/<n>/ui-kit/` |
| `setRect` trả thẳng cho mọi rect | áp **delta** lên rect base/state |
| State khai ở set2 | state ở set1 + `stateSetRect` |
| CSS bộ thiếu tiền tố `.set2/.set3` | `.set2 .ui-x` |
| `border-image-repeat: repeat` cho thanh kéo | `stretch` (theo `stretch: x|y`) |
| Element thanh cao hơn native | cross = native |
| Fill cross != native (vd: `height: 8u` trên sprite 6px) | cross = native 6u (`top: calc((100% - 6u)/2)`) |
| Frame bar-h set1 bị ép `height: 20u` | height = native 12u (20u chỉ cho set2) |
| Chiều dài fill subpixel (vd: 60.9px) gây nhoè mép | JS snap `units * u`; `pct === 0` ẩn fill |
| `?v=` chỉ băm manifest | băm manifest **+ source packer** |
| Sửa file rồi chỉ tin test `file://` | kiểm cả **URL dev-server** + mirror `dist` |
| Overlay thiếu `position:relative` ở bộ khác | phát `position:relative` mọi bộ |

---

## 13. Quy trình chuẩn 1 vòng sửa

```
1. Đo rect/slice/lòng từ _grim_ui.png (hoặc aseprite layer)
2. Sửa manifest (tools/ui/slices.json) +/hoặc packer (tools/ui-pack.py)
3. python tools/ui-pack.py            # validate + xuất
4. python tools/ui/atlas-check.py     # CUT phải = 0
5. python tools/ui/qa.py <slice>      # 1 ảnh soi mọi bộ, native + kéo dài
6. Mở ui-lab.html?x=1 (build stamp mới) để xem thực tế
7. Commit
```
