# SESSION: Kiến Trúc & Tiến Trình Tích Hợp Paperdoll Minifantasy

Tóm tắt kiến trúc kỹ thuật, quy chuẩn dữ liệu và tiến trình triển khai hệ thống **Paperdoll Minifantasy** cho dự án **BrowserQuest** (cô đọng từ [1_KIẾN_TRÚC_TÍCH_HỢP_PAPERDOLL_MINIFANTASY_TECHNICAL_SPECIFICATION.md](file:///D:/Develop/Projects/BrowserQuest/sessions/1_KI%E1%BA%BEN_TR%C3%9AC_T%C3%8DCH_H%E1%BB%A2P_PAPERDOLL_MINIFANTASY_TECHNICAL_SPECIFICATION.md)).

---

## 1. Kiến Trúc Paperdoll & Thứ Tự Render
- **Mục tiêu**: Chuyển từ monolithic sprite sang cơ chế ghép lớp (Paperdoll), giữ nguyên cấu trúc thư mục gốc `client/Minifantasy/` (không đổi tên/di chuyển asset). Tương thích ngược với sprite nguyên bản.
- **Thứ tự layer (dưới lên trên)**:
  `Shadow` ➔ `Base Body (base_human)` ➔ `Armor (clotharmor, ...)` ➔ `Weapon (sword1, ...)`

---

## 2. Định Dạng Sprite Mở Rộng (`is_multi: true`)
- **Schema**:
  - `is_multi`: Chuyển cơ chế tải sang `loadMulti()`.
  - `base_path`: Thư mục gốc chứa asset sprite.
  - `animations.<anim_name>`:
    - `file`: Đường dẫn file tương đối so với `base_path` (`""` = tàng hình/transparent).
    - `row`: `0` (Hướng Down / Right - Front-facing), `3` (Hướng Up - Back-facing).
    - `length`: Số frame thực tế (`idle`: 14, `walk`: 4, `atk`: 4, `death`: 12).
    - `offset_x: -8`, `offset_y: -7`: Chuẩn anchor grid Minifantasy 32x32 trên BrowserQuest (thay thế mặc định `-16, -16`).

---

## 3. Thay Đổi Mã Nguồn Chính
1. **[sprite.ts](file:///D:/Develop/Projects/BrowserQuest/client/ts/renderer/sprite.ts)**:
   - Thêm `isMulti`, `basePath`, `multiImages`, `loadMulti()`, `getImage(animName)`, `getOffset(animName)`.
   - Bỏ qua `createHurtSprite()` / `createSilhouette()` khi `isMulti` để tránh crash do thiếu `this.image` đơn lẻ.
2. **[renderer.ts](file:///D:/Develop/Projects/BrowserQuest/client/ts/renderer/renderer.ts)**:
   - Render tuần tự `baseSprite` ➔ `armorSprite` ➔ `weaponSprite`; `srcScale = 1` cho `isMulti`.
   - **Pixel-Perfect**: Thêm `disableImageSmoothing()` cho 3 Canvas context (`context`, `background`, `foreground`) khi `rescale()` và `createCamera()`. CSS canvas: `image-rendering: pixelated; crisp-edges;`.
3. **[webpack.config.js](file:///D:/Develop/Projects/BrowserQuest/webpack.config.js)**:
   - Xử lý lỗi cạn kiệt file descriptors (**EMFILE**): Dev server phục vụ tĩnh từ `client/` qua `devServer.static`, bỏ qua watch `Minifantasy/`, build giới hạn `concurrency: 50`.
4. **[game.ts](file:///D:/Develop/Projects/BrowserQuest/client/ts/game.ts)**:
   - Đăng ký `base_human` vào mảng `spriteNames` để tải trước lúc khởi động game.

---

## 4. Bảng Ánh Xạ Asset Minifantasy

### Base Human (`base_human.json`)
- **Asset path**: `Minifantasy/Minifantasy_Creatures_v3.3_Commercial_Version/.../Base_Human/`
- **Files**: `humanidle.png` (14f), `humanwalk.png` (4f), `humanattack.png` (4f), `humansouldie.png` (12f). Row `0` (Down/Right), Row `3` (Up).

### Giáp / Paperdoll Shirts (`Minifantasy_AMyriadOfNPCs_v.1.0/.../Generic_NPCs/`)
*Cấu hình*: `idle` 14f, `walk` 4f, `atk` transparent, `death` 12f.
- `clotharmor`: `white`
- `leatherarmor`: `brownleather`
- `mailarmor`: `grey`
- `platearmor`: `blackleather`
- `redarmor`: `red`
- `goldenarmor`: `yellow`

### Vũ Khí / Weapons
- `sword1`: `Slash_Attacks/Sword/slash_sword_f.png` (Row 0) & `_b.png` (Row 3), 4f.
- `sword2`: `Slash_Attacks/Dagger/slash_dagger_f.png` (Row 0) & `_b.png` (Row 3), 4f.
- `redsword`: `Magic Weapons/Sword/Front Layer/sword_bleeding_f.png` & `Back Layer/..._b.png`, 4f.
- `goldensword`: `Magic Weapons/Sword/Front Layer/sword_stun_f_.png` & `Back Layer/..._b.png`, 4f.
- `axe`: `Slash_Attacks/Axe/slash_axe_f.png` & `_b.png`, 4f.
- `morningstar`: `Swing_Attacks/swing_flail.png`, 3f (Front & Back).

---

## 5. Tiến Trình Commit & Nhật Ký Sửa Lỗi
- `34c134d8`: Khôi phục logic paperdoll cơ bản (`is_multi`, `loadMulti`, `base_human.json`, `renderer.ts`).
- `25e70ec4`: Sửa lỗi EMFILE Webpack devServer cho asset Minifantasy.
- `7be6ffff`: Sửa base_human tàng hình (`spriteNames`), chuẩn hóa offset `-8, -7`, frame walk 4f, hướng hàng row 0/3, đồng bộ toàn bộ 6 giáp & 6 vũ khí.
- `Uncommitted`: 
  - Vô hiệu hóa image smoothing hiện đại (`imageSmoothingEnabled = false`) chống nhòe pixel khi upscale canvas.
  - Sửa dứt điểm lỗi giật/mất frame khi chuyển state `walk`/`idle` ➔ `attack`:
    - Loại bỏ switch kép `idle() ➔ hit()`: trong `Character.nextStep()`, chỉ gọi `idle()` khi kết thúc di chuyển nếu `!this.hasTarget()`. Trong `Character.lookAtTarget()`, chỉ cập nhật orientation nếu `this.isAttacking()`.
    - Thêm fallback render áo khi tấn công: Do giáp Minifantasy (`clotharmor`, ...) không có file sprite cho attack (`file: ""`), renderer fallback vẽ frame 0 của `idle_<orientation>` để nhân vật không bị mất áo đột ngột thành người trần.
    - Chuẩn hóa tính `row` cho các lớp con (`baseRow`, `weaponRow`) trong `renderer.ts` dựa theo `animationData` thay vì phụ thuộc vào `anim.row` của sprite chính.
    - Điều chỉnh `atkSpeed` từ `50ms` lên `90ms` trong `character.ts` để hiển thị rõ từng frame vung kiếm/chém.
    - Bổ sung `this.setDirty()` ngay khi gán animation mới trong `Entity.setAnimation()` ([entity.ts](file:///D:/Develop/Projects/BrowserQuest/client/ts/entity/entity.ts)).
    - Chạy Webpack compile và rebuild thành công `dist/client/main.js`.
  - Thiết lập quy tắc chống spam đọc file lặp lại (`codebase-reading.md`), cơ chế ngắt khẩn cấp (Circuit Breaker) trong `AGENTS.md`.

---

## 6. Định Hướng Tiếp Theo
1. Bổ sung animation trạng thái Minifantasy mới (`jump`, `chargedattack`, `dmg`).
2. Khảo sát sprite vũ khí ở trạng thái `idle`/`walk` (tránh vũ khí tàng hình khi không tấn công).
3. Viết script CI/test tự động validate schema sprite JSON và số frame ảnh thực tế.

