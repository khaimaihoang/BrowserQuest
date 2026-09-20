# Kiến Trúc Tích Hợp Paperdoll Minifantasy (Technical Specification)

Tài liệu kỹ thuật tổng hợp kiến trúc, đặc tả dữ liệu và lịch sử triển khai hệ thống **Paperdoll** sử dụng asset pack **Minifantasy** cho dự án **BrowserQuest**.

---

## 1. Tổng Quan Kiến Trúc & Yêu Cầu Kỹ Thuật

### 1.1. Mục Tiêu
- Chuyển đổi mô hình sprite nguyên khối (monolithic sprite) của nhân vật Player sang cơ chế **Paperdoll**:
  - Tách lớp cơ thể cơ bản (`Base Human`) riêng biệt.
  - Tách trang phục / giáp (`Armor/Shirt`) thành lớp layer phủ lên cơ thể.
  - Tách vũ khí (`Weapon`) thành lớp render độc lập.
- Giữ nguyên cấu trúc thư mục gốc của asset pack `Minifantasy` trong `client/Minifantasy/`, tuyệt đối **không đổi tên / di chuyển** file asset Minifantasy nhằm thuận tiện cho việc cập nhật sau này.
- Cung cấp cơ chế tương thích ngược (backwards compatibility) cho các sprite BrowserQuest nguyên bản.

### 1.2. Thứ Tự Vẽ Lớp (Render Layer Order)
Quy trình composite sprite của Player trên Canvas 2D tuân theo thứ tự phân tầng từ dưới lên:
```text
1. Shadow (Bóng nhân vật)
   └── 2. Base Body (base_human)
        └── 3. Armor / Paperdoll (clotharmor, platearmor, leatherarmor, ...)
             └── 4. Weapon (sword1, axe, morningstar, ...)
```

---

## 2. Định Dạng Cấu Hình Sprite Mở Rộng (`is_multi`)

Để hỗ trợ sprite tổng hợp từ nhiều file rời rạc của Minifantasy mà không phá vỡ engine BrowserQuest, cấu hình JSON của sprite được mở rộng với cờ `is_multi: true`.

### 2.1. Cấu Trúc JSON Schema Mở Rộng
```json
{
  "id": "<sprite_id>",
  "width": 32,
  "height": 32,
  "offset_x": -8,
  "offset_y": -7,
  "is_multi": true,
  "base_path": "<relative_path_to_assets>/",
  "animations": {
    "<anim_name>": {
      "length": <number_of_frames>,
      "row": <row_index>,
      "file": "<relative_filename_to_base_path>",
      "offset_x": <optional_override_offset_x>,
      "offset_y": <optional_override_offset_y>
    }
  }
}
```

### 2.2. Chi Tiết Thuộc Tính
- `is_multi` (*boolean*): Khi `true`, sprite sẽ chuyển sang cơ chế tải nhiều ảnh qua `loadMulti()` thay vì `load()` một ảnh duy nhất từ `img/<scale>/<id>.png`.
- `base_path` (*string*): Thư mục gốc chứa các frame ảnh của sprite này.
- `animations.<anim_name>.file` (*string*): File ảnh tương ứng với hành động. Nếu chuỗi rỗng `""`, engine coi như trạng thái này tàng hình / transparent (không render).
- `animations.<anim_name>.row` (*number*): Chỉ số hàng cần cắt trong sheet ảnh:
  - **Hàng 0**: Hướng Xuống / Phải (Front-facing: `idle_down`, `idle_right`, `walk_down`, `walk_right`, `atk_down`, `atk_right`).
  - **Hàng 3**: Hướng Lên (Back-facing: `idle_up`, `walk_up`, `atk_up`).
- `animations.<anim_name>.length` (*number*): Số lượng frame thực tế của animation:
  - `idle`: 14 frames.
  - `walk`: 4 frames.
  - `atk`: 4 frames.
  - `death`: 12 frames (sử dụng `humansouldie.png`).
- `offset_x`, `offset_y` (*number*): Tọa độ căn chỉnh điểm gốc (anchor) hiển thị. Chuẩn của Minifantasy 32x32 trên lưới BrowserQuest là `offset_x: -8`, `offset_y: -7` (thay thế mức mặc định `-16, -16`). Cấu hình animation riêng có thể ghi đè nếu cần thiết.

---

## 3. Thiết Kế & Thay Đổi Trong Source Code

### 3.1. Sprite Loader & Multi-Image Management ([sprite.ts](file:///F:/GihOt/BrowserQuest/client/ts/renderer/sprite.ts))
- **Thuộc tính mới**:
  - `isMulti: boolean`: Cờ nhận diện sprite dạng đa file.
  - `basePath: string`: Đường dẫn cơ sở.
  - `multiImages: { [key: string]: HTMLImageElement }`: Bộ nhớ cache lưu các đối tượng `Image` theo tên file.
  - `imagesLoaded / totalImages`: Quản lý tiến trình tải bất đồng bộ tất cả unique image files.
- **Phương thức mới**:
  - `loadMulti()`: Trích xuất danh sách file duy nhất từ `animationData`, tải song song tất cả các ảnh và kích hoạt `onload_func` khi toàn bộ ảnh đã nạp xong.
  - `getImage(animName?: string)`: Trả về `HTMLImageElement` tương ứng với animation cụ thể nếu là `isMulti`, ngược lại trả về `this.image` nguyên bản.
  - `getOffset(animName?: string)`: Lấy tọa độ offset riêng của từng animation (nếu có định nghĩa) hoặc fallback về `offsetX` / `offsetY` toàn cục của sprite.
- **Xử lý An Toàn (Crash Prevention)**:
  - Chặn `createHurtSprite()` và `createSilhouette()` đối với `isMulti` để tránh crash khi `this.image` không tồn tại ở sprite đa file.

### 3.2. Renderer Engine ([renderer.ts](file:///F:/GihOt/BrowserQuest/client/ts/renderer/renderer.ts))
- **Render Entity / Player Layering**:
  - Tại `drawCharacter` / `drawEntity`, tính toán lại `srcScale` (với sprite thông thường là `os`, với `isMulti` lấy trực tiếp `1` do asset Minifantasy nguyên bản không có tiền tố folder tỷ lệ scale).
  - Tích hợp vẽ tuần tự: `baseSprite` -> `armorSprite` -> `weaponSprite`.
- **Pixel-Perfect Rendering & Anti-Aliasing Fix**:
  - Khắc phục hiện tượng mờ nhòe pixel trên sprite `Base_Human` và các asset 1x khi upscale:
    - Bổ sung `disableImageSmoothing()` vô hiệu hóa làm mịn (`imageSmoothingEnabled = false`, `webkitImageSmoothingEnabled = false`, `mozImageSmoothingEnabled = false`, `msImageSmoothingEnabled = false`) trên cả 3 ngữ cảnh Canvas 2D (`context`, `background`, `foreground`) sau mỗi lần resize/rescale màn hình (`createCamera`).
    - Cập nhật nhận diện `upscaledRendering` hỗ trợ chuẩn HTML5 Canvas hiện đại (`imageSmoothingEnabled !== undefined`).
    - Khai báo CSS `image-rendering: pixelated`, `image-rendering: -moz-crisp-edges`, `image-rendering: crisp-edges` trên toàn bộ thẻ `canvas`.

### 3.3. Tối Ưu Hóa Build & Static Serving ([webpack.config.js](file:///D:/Develop/Projects/BrowserQuest/webpack.config.js))
- Xử lý vấn đề cạn kiệt file descriptors trên hệ điều hành (**EMFILE errors**) do lượng asset Minifantasy rất lớn:
  - Trong môi trường phát triển (`development`), cấu hình `devServer.static` trỏ thẳng tới thư mục `client/` thay vì copy hàng ngàn file qua `CopyWebpackPlugin`.
  - Cấu hình file watcher bỏ qua thư mục `Minifantasy/`: `watch: { ignored: /Minifantasy/ }`.
  - Giới hạn `concurrency: 50` khi build production.

---

## 4. Bảng Ánh Xạ Dữ Liệu Minifantasy (Asset Mapping Matrix)

### 4.1. Base Human (`client/sprites/base_human.json`)
- **Asset Dir**: `Minifantasy/Minifantasy_Creatures_v3.3_Commercial_Version/Minifantasy_Creatures_Assets/Base_Humanoids/Human/Base_Human/`

| Animation Name | Frames | Row Index | Source File |
| :--- | :--- | :--- | :--- |
| `idle_down` | 14 | 0 | `humanidle.png` |
| `idle_right`| 14 | 0 | `humanidle.png` |
| `idle_up`   | 14 | 3 | `humanidle.png` |
| `walk_down` | 4  | 0 | `humanwalk.png` |
| `walk_right`| 4  | 0 | `humanwalk.png` |
| `walk_up`   | 4  | 3 | `humanwalk.png` |
| `atk_down`  | 4  | 0 | `humanattack.png` |
| `atk_right` | 4  | 0 | `humanattack.png` |
| `atk_up`    | 4  | 3 | `humanattack.png` |
| `death`     | 12 | 0 | `humansouldie.png` |

### 4.2. Armors & Paperdolls (`clotharmor`, `leatherarmor`, `mailarmor`, `platearmor`, `redarmor`, `goldenarmor`)
- **Asset Dir**: `Minifantasy/Minifantasy_AMyriadOfNPCs_v.1.0/Minifantasy_NPCs_Assets/Generic_NPCs/`

| Sprite ID | Texture Color | Idle Subpath | Walk Subpath | Die Subpath |
| :--- | :--- | :--- | :--- | :--- |
| `clotharmor` | `white` | `Idle/Body/Shirt/minifantasy_npcsidle_shirt_white.png` | `Walk/Body/Shirt/minifantasy_npcswalk_shirt_white.png` | `Die/Body/Shirt/minifantasy_npcsdie_shirt_white.png` |
| `leatherarmor` | `brownleather` | `Idle/Body/Shirt/minifantasy_npcsidle_shirt_brownleather.png` | `Walk/Body/Shirt/minifantasy_npcswalk_shirt_brownleather.png` | `Die/Body/Shirt/minifantasy_npcsdie_shirt_brownleather.png` |
| `mailarmor` | `grey` | `Idle/Body/Shirt/minifantasy_npcsidle_shirt_grey.png` | `Walk/Body/Shirt/minifantasy_npcswalk_shirt_grey.png` | `Die/Body/Shirt/minifantasy_npcsdie_shirt_grey.png` |
| `platearmor` | `blackleather` | `Idle/Body/Shirt/minifantasy_npcsidle_shirt_blackleather.png` | `Walk/Body/Shirt/minifantasy_npcswalk_shirt_blackleather.png` | `Die/Body/Shirt/minifantasy_npcsdie_shirt_blackleather.png` |
| `redarmor` | `red` | `Idle/Body/Shirt/minifantasy_npcsidle_shirt_red.png` | `Walk/Body/Shirt/minifantasy_npcswalk_shirt_red.png` | `Die/Body/Shirt/minifantasy_npcsdie_shirt_red.png` |
| `goldenarmor` | `yellow` | `Idle/Body/Shirt/minifantasy_npcsidle_shirt_yellow.png` | `Walk/Body/Shirt/minifantasy_npcswalk_shirt_yellow.png` | `Die/Body/Shirt/minifantasy_npcsdie_shirt_yellow.png` |

*Ghi chú hành vi*:
- `idle_*`: 14 frames, Row 0 (Down/Right), Row 3 (Up).
- `walk_*`: 4 frames, Row 0 (Down/Right), Row 3 (Up).
- `atk_*`: `""` (transparent/không che khuất base human).
- `death`: 12 frames, Row 0.

### 4.3. Weapons (`sword1`, `sword2`, `redsword`, `goldensword`, `axe`, `morningstar`)

| Sprite ID | Weapon Type / Origin | Base Path | Front Attack File (`atk_down`, `atk_right`) | Back Attack File (`atk_up`) | Frames |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `sword1` | Sword | `Minifantasy/Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Slash_Attacks/` | `Sword/slash_sword_f.png` | `Sword/slash_sword_b.png` | 4 |
| `sword2` | Dagger | `Minifantasy/Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Slash_Attacks/` | `Dagger/slash_dagger_f.png` | `Dagger/slash_dagger_b.png` | 4 |
| `redsword` | Bleeding Magic Sword | `Minifantasy/Minifantasy_Magic_Weapons_And_Effects_v1.0/.../Magic Weapons/Sword/` | `Front Layer/sword_bleeding_f.png` | `Back Layer/sword_bleeding_b.png` | 4 |
| `goldensword`| Stun Magic Sword | `Minifantasy/Minifantasy_Magic_Weapons_And_Effects_v1.0/.../Magic Weapons/Sword/` | `Front Layer/sword_stun_f_.png` | `Back Layer/sword_stun_b.png` | 4 |
| `axe` | Axe | `Minifantasy/Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Slash_Attacks/` | `Axe/slash_axe_f.png` | `Axe/slash_axe_b.png` | 4 |
| `morningstar`| Flail Swing | `Minifantasy/Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Swing_Attacks/` | `swing_flail.png` | `swing_flail.png` | 3 |

---

## 5. Lịch Sử Phân Tích & Tiến Trình Commit (Từ `34c134d8`)

| Commit ID | Tiêu Đề / Thay Đổi | Phân Tích Kỹ Thuật |
| :--- | :--- | :--- |
| [`34c134d8`](file:///D:/Develop/Projects/BrowserQuest/SESSION.md#L1) | `temp: restore minifantasy paperdoll logic` | - Tái thiết lập kiến trúc paperdoll cơ bản: thêm `is_multi`, `loadMulti()`, `getImage()`, `getOffset()` vào [sprite.ts](file:///D:/Develop/Projects/BrowserQuest/client/ts/renderer/sprite.ts).<br>- Bổ sung cấu hình [base_human.json](file:///D:/Develop/Projects/BrowserQuest/client/sprites/base_human.json), cập nhật [clotharmor.json](file:///D:/Develop/Projects/BrowserQuest/client/sprites/clotharmor.json) và [sword1.json](file:///D:/Develop/Projects/BrowserQuest/client/sprites/sword1.json).<br>- Tích hợp các bước render xếp chồng Base -> Armor -> Weapon trong [renderer.ts](file:///D:/Develop/Projects/BrowserQuest/client/ts/renderer/renderer.ts).<br>- Ghi nhận cấu hình initial Q&A trong `SESSION.md`. |
| [`25e70ec4`](file:///D:/Develop/Projects/BrowserQuest/webpack.config.js#L50-L75) | `fix: resolve EMFILE errors by optimizing webpack devServer and CopyWebpackPlugin for Minifantasy assets` | - Khắc phục crash `EMFILE: too many open files` do Webpack cố gắng copy hàng ngàn file asset Minifantasy khi dev.<br>- Chuyển sang phục vụ tĩnh trực tiếp từ `client/` qua `devServer.static` và bỏ qua watch thư mục `Minifantasy`. |
| [`7be6ffff`](file:///D:/Develop/Projects/BrowserQuest/client/ts/renderer/renderer.ts#L370-L480) | `fix(sprites): fix base_human visibility, rendering offsets, walk animation frames, and orientation facing` | - Sửa lỗi nhân vật tàng hình: đưa `base_human` vào mảng danh sách khởi tạo `spriteNames` của [game.ts](file:///D:/Develop/Projects/BrowserQuest/client/ts/game.ts).<br>- Chuẩn hóa offset: cập nhật từ `-16, -16` thành `offset_x: -8`, `offset_y: -7` giúp nhân vật đứng chuẩn trên ô gạch.<br>- Điều chỉnh số frame animation bước đi `walk` từ 6 xuống 4 frame theo đúng texture Minifantasy.<br>- Chuẩn hóa hướng hàng (Row mapping): hàng 0 cho Hướng Xuống/Phải, hàng 3 cho Hướng Lên.<br>- Đồng bộ định dạng `is_multi` cho toàn bộ danh mục giáp (`leatherarmor`, `mailarmor`, `platearmor`, `redarmor`, `goldenarmor`) và vũ khí (`sword2`, `redsword`, `goldensword`, `axe`, `morningstar`).<br>- Sửa tên file chữ hoa -> chữ thường (`humanidle.png`, `humanwalk.png`, `humanattack.png`, `humansouldie.png`) phù hợp case-sensitivity môi trường build. |
| `Uncommitted` | `fix(renderer): enable modern imageSmoothingEnabled disabling for pixel-perfect rendering` | - Khắc phục tình trạng làm mịn (anti-aliasing bilinear) gây nhòe mờ sprite `Base_Human` và các sprite 1x khi upscale.<br>- Bổ sung hàm `disableImageSmoothing()` cho 3 contexts canvas (`context`, `background`, `foreground`) mỗi khi `rescale()` và `createCamera()`.<br>- Cập nhật CSS thẻ `canvas` áp dụng `image-rendering: pixelated` và `crisp-edges`. |

---

## 6. Kế Hoạch Mở Rộng Tiếp Theo (Future Roadmap)
1. **Custom Action States**: Hỗ trợ bổ sung các animation đặc thù của Minifantasy chưa có trong BrowserQuest như `jump`, `chargedattack`, `dmg` khi phát triển thêm cơ chế gameplay mới.
2. **Idle/Walk Weapon Sprites**: Bổ sung asset tư thế cầm vũ khí ở trạng thái đứng im/di chuyển (nếu có asset phù hợp) để loại bỏ hiện tượng vũ khí tàng hình ngoài lúc chém.
3. **Automated Sprite Validation**: Triển khai script CI/test để kiểm tra kích thước ảnh, số frame thực tế và đối chiếu schema JSON tránh lỗi cấu hình sai lệch.

---

## 7. Ánh Xạ Dữ Liệu Item Sang Sprite Minifantasy (Đã Hoàn Thành)

Hệ thống đã chuẩn hóa toàn diện 6 bộ giáp và 6 loại vũ khí từ sprite nguyên bản của BrowserQuest sang sprite ghép đa file (`is_multi: true`) của Minifantasy:

### 7.1. Bảng Ánh Xạ Giáp (Armors - Generic NPCs Shirts)
Toàn bộ sprite giáp sử dụng texture từ gói `Minifantasy/Minifantasy_AMyriadOfNPCs_v.1.0/Minifantasy_NPCs_Assets/Generic_NPCs/`. Mỗi loại giáp được chọn một màu sắc đặc trưng để phân biệt rõ ràng:

1. **`clotharmor`** -> **`white`**: Áo vải mộc màu trắng ngà truyền thống.
2. **`leatherarmor`** -> **`brownleather`**: Giáp da thuộc nâu tự nhiên.
3. **`mailarmor`** -> **`grey`**: Áo giáp xích kim loại ánh xám bạc.
4. **`platearmor`** -> **`blackleather`**: Giáp đen đanh thép tạo cảm giác cứng cáp, vượt trội so với da và xích.
5. **`redarmor`** -> **`red`**: Giáp chiến binh màu đỏ thẫm rực rỡ.
6. **`goldenarmor`** -> **`yellow`**: Hoàng kim giáp rực sáng quyền quý.

*Quy cách frame*: `idle`: 14 frames, `walk`: 4 frames, `atk`: transparent (không có sheet riêng), `death`: 12 frames. `offset_x: -8`, `offset_y: -7`.

### 7.2. Bảng Ánh Xạ Vũ Khí (Weapons)
1. **`sword1` (Basic Sword)**:
   - Thư mục: `Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Slash_Attacks/`
   - File: `Sword/slash_sword_f.png` (Down/Right, Row 0) & `Sword/slash_sword_b.png` (Up, Row 3). 4 frames.
2. **`sword2` (Dagger)**:
   - Thư mục: `Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Slash_Attacks/`
   - File: `Dagger/slash_dagger_f.png` (Down/Right, Row 0) & `Dagger/slash_dagger_b.png` (Up, Row 3). 4 frames.
3. **`redsword` (Huyết Kiếm - Bleeding Sword)**:
   - Thư mục: `Minifantasy_Magic_Weapons_And_Effects_v1.0/Minifantasy_Magic_Weapons_And_Effects_Assets/Addon Effects (Minifantasy - Weapons)/Magic Weapons/Sword/`
   - File: `Front Layer/sword_bleeding_f.png` (Down/Right, Row 0) & `Back Layer/sword_bleeding_b.png` (Up, Row 3). 4 frames hiệu ứng máu đỏ.
4. **`goldensword` (Lôi Kiếm / Hoàng Kim - Stun Sword)**:
   - Thư mục: `Minifantasy_Magic_Weapons_And_Effects_v1.0/Minifantasy_Magic_Weapons_And_Effects_Assets/Addon Effects (Minifantasy - Weapons)/Magic Weapons/Sword/`
   - File: `Front Layer/sword_stun_f_.png` (Down/Right, Row 0) & `Back Layer/sword_stun_b.png` (Up, Row 3). 4 frames tia chớp hoàng kim.
5. **`axe` (Battle Axe)**:
   - Thư mục: `Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Slash_Attacks/`
   - File: `Axe/slash_axe_f.png` (Down/Right, Row 0) & `Axe/slash_axe_b.png` (Up, Row 3). 4 frames rìu chiến.
6. **`morningstar` (Chùy Xích - Flail)**:
   - Thư mục: `Minifantasy_Weapons_v3.0/Minifantasy_Weapons_Assets/Swing_Attacks/`
   - File: `swing_flail.png` (Front & Back, 3 frames ở kích thước 96x128 chia lưới 3 cột x 4 hàng).