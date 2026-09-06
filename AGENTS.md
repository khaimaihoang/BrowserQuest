# Hướng Dẫn Hoạt Động (AGENTS.md)

Dự án này (`TwoKone Word Chain`) sử dụng hệ thống **Game Studio Framework** kết hợp với **Impeccable Design**. Là một AI Agent (Antigravity), bạn có trách nhiệm tuân thủ các quy tắc sau:

## 1. Cơ Cấu Tổ Chức & Subagents
Dự án có một Plugin nội bộ cung cấp các Subagents chuyên biệt:
- **`game-designer`**: Thiết kế cơ chế, GDD, Game Loop. Hãy dùng `invoke_subagent` gọi agent này khi bạn cần tư vấn hoặc viết Game Design Document.
- **`unity-specialist`**: Tối ưu hoá Unity, kiến trúc mã nguồn.
- **`qa-tester`**: Lên kịch bản kiểm thử, soát lỗi logic.

Bất cứ khi nào người dùng giao một tác vụ phức tạp (như thiết kế tính năng mới, hoặc kiểm tra lỗi), hãy tự động ủy quyền (delegate) cho subagent phù hợp thay vì tự làm một mình nếu tác vụ đó nằm ngoài chuyên môn chung.

## 2. Hệ Thống Tài Liệu Thiết Kế (Document Templates)
Mọi tài liệu thiết kế phải được lưu tại `docs/` hoặc `design/` (sử dụng thư mục `docs/templates/` làm mẫu).

## 3. Mã Nguồn và Quy Tắc
Hệ thống Antigravity sẽ tự động nạp các tệp `.md` từ `.agents/rules/` tùy theo tệp bạn đang chỉnh sửa (VD: `gameplay-code.md`, `ui-code.md`). Bạn bắt buộc phải đọc và làm theo các ràng buộc đó khi sửa mã nguồn.

## 4. Thiết Kế UX/UI (Impeccable)
Khi làm việc với các thành phần giao diện người dùng (UI), hãy kết hợp sử dụng skill `impeccable` (đã được cài đặt mức Global). Ví dụ, bạn có thể tự gọi lệnh `/impeccable critique <file-name>` để nhận đánh giá chi tiết về UI trước khi bắt tay lập trình. Luôn bám sát `PRODUCT.md` ở thư mục gốc.

## 5. Quy Trình Phối Hợp
- **Question -> Options -> Decision -> Draft -> Approval**: Luôn hỏi và đề xuất 2-4 lựa chọn trước khi chốt giải pháp.
- Đừng tự động ghi đè file lớn nếu chưa báo cáo cho người dùng.
