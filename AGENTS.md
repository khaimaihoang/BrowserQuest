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
- **TỐI ĐA 10 LẦN VIEW TRÊN 1 TỆP TRONG MỘT LƯỢT CHAT (Single-Read Enforcement)**:
  - Agent CHỈ ĐƯỢC PHÉP gọi `view_file` đúng 10 lần duy nhất cho mỗi file trong cùng 1 turn. Nếu cần xem nhiều đoạn, hãy đọc toàn bộ hàm/khối từ MCP `get_code_snippet` hoặc chọn khoảng dòng lớn bao quát (`EndLine - StartLine <= 800`).
  - **CẤM TUYỆT ĐỐI**: Không bao giờ gọi `view_file` lần thứ 11 trên cùng một đường dẫn trong cùng một lượt phản hồi. Lần thứ 11 trở đi bị coi là vi phạm nghiêm trọng và sẽ kích hoạt ngắt lệnh ngay lập tức.
- **DỪNG VÒNG LẶP SUY NGHĨ (Break Thought Loop)**:
  - Khi đã xác định được file lỗi và logic, Agent PHẢI dừng gọi công cụ đọc file ngay lập tức để chuyển sang công cụ chỉnh sửa (`replace_file_content`) hoặc trả lời trực tiếp cho người dùng.
  - Tuyệt đối không vừa suy nghĩ vừa gọi tiếp công cụ thăm dò nếu thông tin đã đủ để kết luận.

## 10. Tiêu Chuẩn Chất Lượng Thương Mại Hóa (Production-Ready Standard)
Mọi kết quả do Agent tạo ra **BẮT BUỘC** phải đạt chuẩn sẵn sàng thương mại hóa trước khi bàn giao:
- **Tự kiểm thử tối thiểu 10 vòng**: Agent phải tự chạy lại, đọc lại, và xác minh logic của mọi thay đổi ít nhất 10 lần trước khi kết luận xong. Không được dừng sau lần kiểm tra đầu tiên.
- **Sửa lỗi đến khi sạch hoàn toàn**: Không bàn giao kết quả còn lỗi đã biết, cảnh báo chưa xử lý, hoặc logic chưa hoàn chỉnh. Nếu phát hiện lỗi trong lần kiểm tra thứ N, phải sửa và bắt đầu lại vòng kiểm tra từ đầu.
- **Sẵn sàng ra mắt ngày mai**: Mọi tính năng, tài liệu, và mã nguồn phải đạt mức có thể ship lên production ngay lập tức — không có "TODO", không có "placeholder", không có code debug còn sót lại.
- **Không bao giờ đổ lỗi cho môi trường**: Nếu có vấn đề, Agent phải tìm ra và xử lý triệt để thay vì giải thích rằng "có thể do môi trường" hoặc "cần kiểm tra thêm".

## 11. Hồ Sơ Thực Thi Nghiêm Ngặt & Giảm Token (Strict Execution Profile)
- **Định Hướng Đường Dẫn Trực Tiếp (Zero Broad Searches)**: TUYỆT ĐỐI KHÔNG chạy tìm kiếm đệ quy (`grep_search`, `find_by_name`) trên thư mục gốc `F:\GihOt\BrowserQuest`. Mở trực tiếp đường dẫn đã biết (`client/`, `server/`, `shared/`, `config/`, `docs/`, `tools/`).
- **Sửa File Trực Tiếp (No Scratch Script Overkill)**: Đọc và sửa file trực tiếp bằng `view_file` / `replace_file_content`. KHÔNG tạo hoặc chạy script Python/batch tạm cho việc đọc file, diff, hay validate văn bản cơ bản.
- **Bảo Toàn Ngân Sách Token**: Giữ số lần gọi công cụ ở mức tối thiểu (1–3 lần có chủ đích mỗi lượt). Tránh gọi chuỗi công cụ dây chuyền hoặc thăm dò suy đoán.
- **Codebase Memory MCP & unity-synaptic First**: Luôn ưu tiên `codebase-memory-mcp` (`search_graph`, `trace_path`, `get_code_snippet`, `query_graph`, `get_architecture`) để khám phá mã nguồn. Dùng `unity-synaptic` MCP cho kiểm tra runtime Unity khi cần. Chỉ fallback sang grep/đọc file cho cấu hình tĩnh (JSON/config) hoặc khi MCP không hỗ trợ.
- **Đọc Có Chủ Đích (Targeted Reading)**: Khi đọc mã, chọn khoảng dòng cụ thể (span <= 800 dòng) hoặc dùng `get_code_snippet`. KHÔNG đọc từng lát 10–30 dòng liên tục trên cùng một file (tối đa 2–3 lần đọc có chủ đích mỗi file mỗi lượt).
- **Không Rà Quét File Suy Đoán**: KHÔNG quét `node_modules/`, `dist/`, `sessions/`, `logs/`, `maps/`, `sprites/`, `audio/`, `img/`. Chỉ dựa vào tên class/hàm rõ ràng hoặc quy ước đường dẫn đã biết.
- **Không Đoán Lặp (No Iterative Guessing)**: Nếu một lệnh hoặc thao tác sửa file thất bại 2 lần, DỪNG ngay và yêu cầu làm rõ. Không brute-force lặp lại.
- **Mặc Định Sửa Đơn File**: Mỗi lượt chỉ sửa 1 file đích trừ khi người dùng yêu cầu rõ ràng thay đổi nhiều file.
- **Zero Log Dumps**: KHÔNG trả về toàn bộ output build/console. Chỉ trích xuất đúng tên file, số dòng, và mã lỗi.
- **Trình Bày Diff**: Đưa thay đổi mã dạng unified diff với ±5 dòng ngữ cảnh.
- **Tóm Tắt Thực Thi**: Kết thúc bằng 1 câu tóm tắt ngắn gọn việc đã làm.
- **Link Clickable**: Mọi tham chiếu file/ký hiệu phải dùng markdown link (`[tên](file:///đường/dẫn)`).
