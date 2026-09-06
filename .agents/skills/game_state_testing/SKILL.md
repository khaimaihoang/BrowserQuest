---
name: game-state-testing
description: Hệ thống kiểm thử chuẩn hóa (E2E CDP) để tự động hóa việc kiểm tra trạng thái game, giao diện và logic.
---

# Game State Testing System

Mỗi khi cần kiểm tra trạng thái game, xác minh giao diện (UI) hoặc test một chức năng mới, hãy sử dụng hệ thống test chuẩn hóa này thay vì tạo các script test một lần (ad-hoc).

## 1. Công cụ Cốt lõi
Hệ thống test được tập trung tại `tests/run_full_e2e_tests.py`. Script này sử dụng Chrome DevTools Protocol (CDP) không giao diện (headless) để kết nối trực tiếp vào luồng chạy của game, giúp test với tốc độ cực nhanh và xuất log cực ngắn (tiết kiệm token cho AI).

### Cách sử dụng qua `run_command`:
- **Chạy toàn bộ test:** `python tests/run_full_e2e_tests.py` (In ra kết quả PASS/FAIL rút gọn gọn gàng nhất).
- **Chạy một suite cụ thể:** `python tests/run_full_e2e_tests.py -s <tên_hoặc_số_suite>` (Ví dụ: `-s boot`, `-s 4`).
- **Lấy output dạng JSON (để dễ parse):** `python tests/run_full_e2e_tests.py --json`
- **Chụp ảnh màn hình (Visual Testing):** `python tests/run_full_e2e_tests.py --screenshot` (Ảnh sẽ được lưu tự động vào `tests/test_results/`). Bạn có thể đọc ảnh bằng tool `view_file` để tự mình nhìn và xác minh.

## 2. Tiêu chuẩn khi Thêm Test Mới
Nếu bạn cần kiểm tra một logic mới, hãy mở rộng `tests/run_full_e2e_tests.py` bằng cách thêm một block `if run_all or args.suite in ('...',):` thay vì tạo file mới.
Khi viết test, phải tuân thủ:
1. **Dùng CDP thuần:** Sử dụng `await eval_js("...")` để thực thi JS lấy trạng thái DOM hoặc trigger sự kiện.
2. **Đánh giá tự động:** Luôn dùng hàm `report("SuiteName", "Tên Test", điều_kiện)` để ghi nhận kết quả. 
3. **Tuyệt đối không dump dữ liệu lớn:** Không in ra màn hình nguyên HTML hay base64. Xử lý trực tiếp trong script Python và chỉ trả về trạng thái Đúng/Sai (True/False).

## 3. Quy trình Kiểm tra (Workflow)
Khi User yêu cầu "kiểm tra trạng thái game":
1. Chạy lệnh: `python tests/run_full_e2e_tests.py` (có thể kèm `-s` nếu chỉ cần check một phần).
2. Xem số lượng PASS/FAIL.
3. Nếu có lỗi (FAIL), chạy lại với cờ `--verbose` để xem chi tiết thông báo lỗi cụ thể ở bước nào.
4. Nếu kiểm tra giao diện (UI/Pixel), chạy với cờ `--screenshot`, sau đó dùng tool `view_file` đọc ảnh PNG trong `tests/test_results/` để xác nhận bố cục.

## 4. Các Rule Kiểm Thử Tính Năng UI (UI Features Testing Rules)
Khi phát triển hoặc sửa đổi các tính năng UI, phải tuân thủ và kiểm thử các quy tắc sau:

1. **Test Hover/Active States (Hiệu ứng tương tác):** 
   - Tuyệt đối không dùng `transform: scale(số thập phân)` (ví dụ 1.1) vì sẽ làm vỡ lưới pixel (pixel grid). Chỉ được phép dùng đổi màu (`filter`, sprite class) hoặc tịnh tiến nguyên khối theo bội số của pixel-scale (ví dụ: `transform: translateY(calc(-1px * var(--pixel-scale, 3)))`).
   - **CẤM DÙNG `transition: all` trên các phần tử Sprite:** Khi một thẻ HTML thay đổi CSS Class Sprite (ví dụ từ `ui-sprite-..._1` sang `ui-sprite-..._2`), trình duyệt sẽ thay đổi thuộc tính `border-image`. Việc dùng `transition: all` sẽ vô tình ép trình duyệt nội suy (animate) toàn bộ lưới 9-slice `border-image`, gây ra tình trạng treo/lag cục bộ kinh khủng (có thể lên tới hàng giây). Chỉ được phép transition đích danh các thuộc tính an toàn như `transform`, `filter`, `opacity`, `background-color`.
2. **Test Prefab Injection (Gắn thẻ động):** Khi instantiate một UI Component (ví dụ 
ace_card) vào bên trong một vùng chứa đã có sẵn, bắt buộc phải có cờ isWidget: true trong file YAML. Nếu thiếu, PrefabManager sẽ tự gán class .prefab-root (position: absolute) làm vỡ layout của thẻ cha.
3. **Test Button/Checkbox (Trạng thái Sprite):** Các nút bấm và checkbox của game là các thẻ div giả lập. Thay vì dùng property el.disabled = false, bắt buộc phải dùng DOM Attribute el.removeAttribute('disabled') hoặc el.setAttribute('disabled', 'true') để kích hoạt MutationObserver cập nhật đồ họa Sprite.
4. **Test Scrollbar & Kéo Thả (Drag/Drop Performance):** Tính năng kéo thả phải hoạt động ở tốc độ 60fps mà không bị khựng hoặc trễ.
   - **Chống Layout Thrashing ở sự kiện `pointerdown`:** Bắt buộc phải thực hiện mọi lệnh đo đạc DOM (như `getBoundingClientRect()`, `clientWidth`, `scrollWidth`) TRƯỚC khi thay đổi bất kỳ style nào có khả năng làm mất hiệu lực layout toàn cục (ví dụ `document.body.style.userSelect = "none"`). Nếu thay đổi style trước rồi mới đo đạc, trình duyệt sẽ bị ép phải render lại toàn trang đồng bộ, gây khựng/lag nghiêm trọng (delay) ngay khoảnh khắc click chuột.
5. **Test Template ID (Binding Dữ liệu):** Các Prefab sử dụng cú pháp {{ var }} trong id phải được kiểm tra sau khi spawn xem đã render đúng ID thực tế chưa (VD: render ra 
ace-card-human chứ không được phép để nguyên chữ 
ace-card-{{ id }}).
