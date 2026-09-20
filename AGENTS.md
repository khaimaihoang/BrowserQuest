# Hướng Dẫn Hoạt Động (AGENTS.md)

Dự án này sử dụng hệ thống **Game Studio Framework** kết hợp với **Impeccable Design**. Là một AI Agent (Antigravity), bạn có trách nhiệm tuân thủ các quy tắc sau:

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

## 6. Khám Phá Mã Nguồn & Knowledge Graph (codebase-memory-mcp)
**TUYỆT ĐỐI TUÂN THỦ NGUYÊN TẮC TIẾT KIỆM TOKEN VÀ TỐI ƯU CÔNG CỤ:**
- **Ưu tiên số 1**: PHẢI luôn gọi các công cụ của `codebase-memory-mcp` (`search_graph`, `trace_path`, `get_code_snippet`, `query_graph`, `get_architecture`) để tra cứu cấu trúc, hàm, class.
- **Nghiêm cấm lạm dụng**: TUYỆT ĐỐI KHÔNG gọi `view_file`, `grep_search`, `find_by_name`, `run_command` tràn lan để dò code khi chưa dùng knowledge graph. Chỉ dùng grep/file khi đọc cấu hình tĩnh (JSON, config) hoặc khi MCP không hỗ trợ.
- **Phong cách trả lời (Concise & Token-efficient)**: Trả lời ngắn gọn, trực diện, đi thẳng vào nguyên nhân và giải pháp kỹ thuật. Không giải thích dài dòng hoặc lặp lại code không cần thiết nhằm tiết kiệm tối đa token.

## 7. Nghiêm Cấm Đọc Lặp Lại Một Tệp (Anti-File-Spamming)
- Tuyệt đối không gọi `view_file` trên cùng một tệp quá 10 lần trong 1 phiên làm việc.
- Khi cần đọc file, phải xác định trước phạm vi dòng cần thiết (`StartLine`, `EndLine`) và đọc trọn vẹn 1 lần thay vì đọc từng đoạn 10-30 dòng liên tục.
- Luôn đọc theo quy định chi tiết tại `.agents/rules/codebase-reading.md`.

## 8. Định Dạng Header Bắt Buộc Trong Mọi Câu Trả Lời
Mọi câu trả lời của Agent BẮT BUỘC phải gắn dòng thông tin sau lên ngay đầu câu trả lời:
`Token used: <ước lượng hoặc số token> | Rules read: <danh sách rule áp dụng> | Tools used: <danh sách công cụ đã gọi>`

## 9. Cơ Chế Ngắt Khẩn Cấp (Circuit Breaker) & Ràng Buộc Tiêu Cực (Negative Constraints)
- **TỐI ĐA 1 LẦN VIEW TRÊN 1 TỆP TRONG MỘT LƯỢT CHAT (Single-Read Enforcement)**:
  - Agent CHỈ ĐƯỢC PHÉP gọi `view_file` đúng 1 lần duy nhất cho mỗi file trong cùng 1 turn. Nếu cần xem nhiều đoạn, hãy đọc toàn bộ hàm/khối từ MCP `get_code_snippet` hoặc chọn khoảng dòng lớn bao quát (`EndLine - StartLine <= 800`).
  - **CẤM TUYỆT ĐỐI**: Không bao giờ gọi `view_file` lần thứ 2 trên cùng một đường dẫn trong cùng một lượt phản hồi. Lần thứ 2 trở đi bị coi là vi phạm nghiêm trọng và sẽ kích hoạt ngắt lệnh ngay lập tức.
- **DỪNG VÒNG LẶP SUY NGHĨ (Break Thought Loop)**:
  - Khi đã xác định được file lỗi và logic, Agent PHẢI dừng gọi công cụ đọc file ngay lập tức để chuyển sang công cụ chỉnh sửa (`replace_file_content`) hoặc trả lời trực tiếp cho người dùng.
  - Tuyệt đối không vừa suy nghĩ vừa gọi tiếp công cụ thăm dò nếu thông tin đã đủ để kết luận.
