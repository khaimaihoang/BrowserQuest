# Pixel-Perfect cho UI 9-slice (BrowserQuest)

> Tài liệu ghi lại vấn đề pixel bị kéo giãn khi dựng panel 9-slice bằng
> `border-image`, cách khắc phục, và quy tắc chung để UI/HUD luôn sắc nét.
>
> Áp dụng cho: MiniFantasy UI panel (`client/css/panel.css`,
> `client/img/{1,2,3}/ui/*`) và mọi UI pixel-art thêm sau này.
>
> Liên quan: [ui-hud-ux-process.md](./ui-hud-ux-process.md) ·
> [ui-hud-architecture-guide.md](./ui-hud-architecture-guide.md) ·
> [kaetram-ui-review.md](./kaetram-ui-review.md)

---

## 1. Vấn đề

Panel MiniFantasy dùng `border-image` để bo viền 9-slice:

```css
border: 7px solid transparent;
border-image: url('../img/1/ui/panel.png') 7 fill stretch;  /* ❌ */
```

`stretch` **kéo giãn edge slice** (cạnh) theo chiều dài panel. Sprite panel có
cạnh là **nét đứt trang trí, không tile đều**, nên khi kéo giãn:

- khoảng cách các dash méo (dày/mỏng bất thường),
- pixel bị scale phi nguyên → vỡ hình.

→ **Không pixel-perfect.**

---

## 2. Phân tích sprite panel (`grim_panel_2`)

Crop từ `_grim_ui.png` (Minifantasy UI Overhaul):

| Thuộc tính | Giá trị |
|---|---|
| `rect` | `[112, 704, 48, 48]` |
| `margins` | `[7, 7, 7, 7]` |
| Center | **đen đặc** `(0,0,0,255)` |
| Cạnh trên/dưới | dải 34×7 có nét đứt, **dày ở 2 đầu, thưa ở giữa** → không tile đều |
| Cạnh trái/phải | nét 1px dọc, thưa |
| Góc | 4 góc 7×7 hoa văn |

Vì cạnh **không phải tile đều**, việc lặp/kéo giãn đều dễ méo. Đây là
frame trang trí thiết kế cho một kích thước nhất định, không phải 9-slice
"công nghiệp" có cạnh tileable.

---

## 3. So sánh `border-image-repeat`

Render thật bằng Chrome headless, zoom NEAREST để kiểm tra:

| Giá trị | Hành vi | Pixel-perfect? |
|---|---|---|
| `stretch` | kéo giãn 1 edge slice cho vừa | ❌ méo dash, scale phi nguyên |
| `round` | scale đều để vừa **số nguyên** ô | ⚠️ scale vẫn phi nguyên (VD 0.95×) |
| `space` | tile native + chèn khoảng trống | ⚠️ tạo lỗ hổng ở viền |
| **`repeat`** | **tile ở kích thước native** | ✅ **đúng** |

---

## 4. Giải pháp đã chọn

```css
border: 7px solid transparent;
border-image: url('../img/1/ui/panel.png') 7 fill repeat;   /* ✅ */
```

- **Cạnh**: tile ở native → mỗi pixel nguồn = khối nguyên (1x→1px, 3x→3px).
- **Góc**: giữ nguyên native.
- **Center**: `fill` — nhưng là **màu đặc** nên kéo giãn không gây méo.
- **Đánh đổi**: tile cuối có thể bị cắt nhẹ (không scale pixel, chỉ crop).
  Nếu cần tuyệt đối không cắt → chỉnh kích thước panel thành **bội số của
  kích thước tile** (cạnh 34px ở 1x).

Đã áp dụng cho **13 chỗ** trong `client/css/panel.css` (base + mọi media
block + `.upscaled` + trigger `#ui-panel-trigger`).

---

## 5. Pixel-scale phải nhất quán giữa các sprite

**Lỗi đã gặp ở nút close:** sprite gốc 6×6 nhưng tạo ở `12/24/36`
(scale 2/4/6×) trong khi panel chỉ `1/2/3×` → pixel close to gấp đôi panel,
trông "chunky" và quá to.

Sửa: mọi sprite con phải dùng **cùng hệ scale** với panel.

| Scale | Panel (48 gốc) | Close (6 gốc) |
|---|---|---|
| 1x | 48 (×1) | **6 (×1)** |
| 2x | 96 (×2) | **12 (×2)** |
| 3x | 144 (×3) | **18 (×3)** |

Quy tắc: một panel ở scale `N` thì mọi sprite đi kèm cũng ở scale `N`
(upscale bằng **NEAREST**, không nội suy).

---

## 6. Quy tắc chung cho UI pixel-art

1. **Sprite theo scale**: đặt ở `client/img/1|2|3/...` tương ứng 1x/2x/3x,
   dùng đúng breakpoint của BrowserQuest:
   - `@media (min-width: 1501px)` → 3x
   - `@media (max-width: 1500px)` và `(max-height: 870px)` → 2x
   - `@media (max-width: 1000px)` → 1x
   - `@media (max-width: 800px)` → mobile
2. **9-slice**: dùng `border-image-slice` == `border-width` (tỉ lệ 1:1) và
   `border-image-repeat: repeat` (KHÔNG `stretch`).
3. **Upscale sprite bằng NEAREST** theo bội số nguyên; không để trình duyệt
   tự scale (trừ khi `image-rendering: pixelated` + bội nguyên).
4. **`image-rendering`**: dùng cặp chuẩn của BrowserQuest
   `-moz-crisp-edges` + `-webkit-optimize-contrast`.
5. **Center của 9-slice** nên là **màu đặc** để `fill` không lộ méo.
6. **Kích thước nên là bội số của tile** nếu muốn không cắt tile cuối.

---

## 7. Checklist kiểm tra pixel-perfect

- [ ] `border-image-repeat` là `repeat` (không `stretch`).
- [ ] `border-image-slice` == `border-width`.
- [ ] Sprite có đủ bản `1x/2x/3x` và media query trỏ đúng.
- [ ] Mọi sprite con (close, icon…) cùng pixel-scale với panel mẹ.
- [ ] Upscale NEAREST theo bội số nguyên.
- [ ] Render + zoom NEAREST ở **1x và 3x** để xác nhận không vỡ pixel.
- [ ] Center fill là màu đặc (không dùng texture cho vùng stretch).

---

## 8. Cách kiểm chứng nhanh (Chrome headless)

```bash
# render panel ở từng scale rồi crop + zoom NEAREST
chrome --headless=new --disable-gpu --hide-scrollbars \
  --window-size=900,700 --screenshot=out.png file:///.../test.html
```

So sánh `stretch` vs `round` vs `repeat` bằng cách đổi
`border-image-repeat` và render lại — chọn `repeat` nếu muốn pixel-perfect.
