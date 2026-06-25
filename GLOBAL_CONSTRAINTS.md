# GLOBAL CONSTRAINTS - Stock Hunt

Tài liệu này định nghĩa các ràng buộc kiến trúc và quy chuẩn lập trình bất biến đối với dự án Stock Hunt. Toàn bộ các thay đổi mã nguồn trong tương lai bắt buộc phải tuân thủ nghiêm ngặt các quy tắc này.

---

## 1. Kiến Trúc Hệ Thống & Tách Biệt Trách Nhiệm (Separation of Concerns)

- **Orchestrator (`main.py`)**: 
  - Chỉ làm nhiệm vụ điều phối lịch trình thời gian (Scheduler), khởi chạy tiến trình quét và gọi phân phối.
  - **TUYỆT ĐỐI KHÔNG** được chứa logic nghiệp vụ, tính toán chỉ báo, lọc cổ phiếu, bóc tách chuỗi HTML, hay prompt LLM.
  - Tổng số dòng không vượt quá 150 dòng.
- **Scanner (`scanner.py`)**:
  - Đảm nhiệm việc tải dữ liệu thô (OHLCV, Screener, Foreign flows) và thực hiện các bộ lọc kỹ thuật.
  - Đảm bảo cơ chế Layer 0 Pre-filter hoạt động ổn định để tối ưu hóa hiệu năng, giảm số lượng request.
- **AI Analyzer (`ai_analyzer.py`)**:
  - Đảm nhiệm toàn bộ việc cấu hình prompt, tương tác với LLM và ép kiểu dữ liệu đầu ra.
- **Telegram Bot (`telegram_bot.py`)**:
  - Đảm nhiệm vai trò phân phối tin nhắn, kiểm soát độ dài tin nhắn (chunking), và xử lý format hiển thị (HTML/Markdown/Plain text).

---

## 2. Giao Tiếp LLM & Ràng Buộc Dữ Liệu Đầu Ra (Pydantic & Instructor)

- **Không sử dụng Regex**: Tuyệt đối nghiêm cấm việc sử dụng biểu thức chính quy (Regex) để trích xuất hoặc parse JSON từ chuỗi kết quả trả về của LLM.
- **Bắt buộc dùng Pydantic**: Mọi dữ liệu có cấu trúc cần thu thập từ LLM bắt buộc phải được khai báo thông qua Pydantic Schema (`BaseModel`).
- **Instructor Integration**: Bắt buộc sử dụng thư viện `instructor` để bọc Client LLM (`instructor.from_genai()`) nhằm kích hoạt cơ chế ép kiểu tự động và tự động sửa lỗi cú pháp (`max_retries=3`).
- **Rate Limit & Anti-Spam**:
  - Các cuộc gọi LLM trong vòng lặp phải chèn `time.sleep(2)` để tránh spam và vi phạm Rate Limit.
  - Phải có cơ chế retry-backoff động đối với lỗi `429` (Resource Exhausted) với thời gian chờ tối thiểu 65 giây.

---

## 3. Atomic Caching & Ghi Trạng Thái

- Việc lưu trạng thái, bộ đệm (cache), hoặc nhật ký chạy (nếu có) xuống đĩa cứng hoặc cơ sở dữ liệu chỉ được thực hiện **một lần duy nhất** tại khối `finally` ở cuối vòng lặp chính.
- Nghiêm cấm đặt lệnh ghi đĩa (I/O) dở dang bên trong vòng lặp duyệt phần tử (ví dụ duyệt qua từng cổ phiếu ứng viên) để đề phòng hỏng dữ liệu khi tiến trình bị ngắt đột ngột.

---

## 4. Dọn Dẹp Sau Lập Trình (Cleanup Amnesia)

- Mọi thay đổi code sau khi hoàn tất thành công bắt buộc phải đi kèm thao tác dọn dẹp:
  - Loại bỏ hoàn toàn các `import` thừa không sử dụng.
  - Comment hoặc xóa bỏ các đoạn code/hàm đã bị thay thế (dead code).
  - Không để lại các file rác sinh ra trong quá trình test/debug (như file `.csv`, `.txt` tạm thời).
