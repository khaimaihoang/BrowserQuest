# Quy Tắc Đọc & Khám Phá Mã Nguồn (Codebase Reading & Discovery Rules)

Nhằm tối ưu hóa hiệu suất, tránh lãng phí context token và ngăn chặn hành vi đọc lặp (looping/spamming file read), mọi Agent hoạt động trong dự án này BẮT BUỘC tuân thủ các quy định sau:

---

## 1. Nghiêm Cấm Đọc Lặp Lại Một File (`Anti-File-Spamming`)
- **Giới hạn số lần đọc**: Không được gọi `view_file` trên cùng một tệp quá **2 lần** trong suốt một phiên/lượt phản hồi.
- **Không đọc vụn vặt**: Nghiêm cấm việc đọc 10-30 dòng rồi lại đọc tiếp đoạn kế tiếp liên tục. Phải đọc trọn vẹn khối hàm/class cần xử lý trong 1 lần gọi duy nhất.

---

## 2. Bắt Buộc Ưu Tiên Knowledge Graph (`codebase-memory-mcp`)
Trước khi mở bất kỳ file mã nguồn nào (`.ts`, `.js`, v.v.), BẮT BUỘC phải dùng MCP tools:

1. **Tìm kiếm hàm / class / symbol**:
   - Dùng `search_graph(name_pattern="...")` để xác định ngay vị trí định nghĩa.
2. **Đọc chi tiết code của hàm / method**:
   - Dùng `get_code_snippet(qualified_name="...")` để lấy chính xác code của hàm mà không cần mở cả file lớn.
3. **Lần vết luồng gọi hàm (`call graph` / dependencies)**:
   - Dùng `trace_path(function_name="...", direction="inbound" | "outbound")` để xem luồng gọi thay vì đọc thủ công chuỗi file liên quan.
4. **Cấu trúc tổng quan**:
   - Dùng `get_architecture()` để nắm module trước khi đi vào chi tiết.

---

## 3. Quy Trình Khi Buộc Phải Dùng Công Cụ File Truyền Thống
Chỉ được phép sử dụng `grep_search` hoặc `view_file` khi:
- Tìm chuỗi ký tự thô (string literals), cấu hình JSON, tài liệu Markdown, css/html.
- MCP chưa đánh chỉ mục (index) hoặc không tìm thấy symbol.

Khi đó:
- Dùng `grep_search` để tìm chính xác số dòng cần đọc trước.
- Chỉ gọi `view_file` **đúng 1 lần** với `StartLine` và `EndLine` bao trọn ngữ cảnh cần thiết.
