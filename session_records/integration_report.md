# Báo cáo Tích hợp Hệ thống Tự động Quét Cổ phiếu (Stock Hunt Pipeline)

Hệ thống **Stock Hunt** đã được xây dựng và tích hợp thành công hai thành phần cốt lõi điều phối: `stock_hunt/telegram_bot.py` và `stock_hunt/main.py`. Kiến trúc đảm bảo tính liền mạch giữa quy trình: **Quét định lượng (Scanner) ➔ Phân tích Trí tuệ Nhân tạo (Gemini AI) ➔ Báo cáo Tin nhắn (Telegram Bot)**.

Tài liệu này đã được cập nhật đầy đủ các cấu trúc tích hợp chuyên nghiệp sau Phase 2, 2.1 (Performance Tuning), Phase 2.2 (Verification Alignment) và Phase 3 (Audit Remediation).

---

## 1. Thành phần 1: `stock_hunt/telegram_bot.py`

Thành phần này chịu trách nhiệm định dạng dữ liệu kỹ thuật và gửi tin nhắn HTML tới Telegram.

### Điểm nổi bật trong thiết kế:
1. **Scorecard Contract Alignment**:
   - Nhận trực tiếp đối tượng scorecard tiếng Anh nguyên bản từ `scanner.py` theo đúng hợp đồng dữ liệu **English Keys**.
   - Đọc trực tiếp các khóa chuẩn như `current_price`, `1D_pct`, `active_buy_pct`, `rsi_14`, `rs_avg`, `price_vs_ma20_pct`.
   - Giúp loại bỏ hoàn toàn lỗi hiển thị cột 0 do Mismatch khóa tiếng Việt/tiếng Anh ở các phiên bản trước.
2. **Bình thường hoá hiển thị Giá (`utils.py` synced)**:
   - Sử dụng hàm tiện ích dùng chung `get_price_in_thousands` từ `utils.py` để định dạng giá đóng cửa luôn ở dạng nghìn đồng (e.g., 17100đ thành 17.1), triệt tiêu hoàn toàn sự nhập nhằng đơn vị giá giữa lớp quét và lớp hiển thị.
3. **Bảng Scorecard Kỹ thuật Monospaced**:
   - Sử dụng thẻ `<code>` của Telegram để hiển thị một bảng định dạng hoàn hảo với khoảng cách cột đồng đều.
   - Dịch các khóa hiển thị sang tiếng Việt thân thiện ở lớp định dạng tin nhắn cuối cùng (Telegram Format Layer) thay vì đổi khóa từ trong bộ nhớ.
4. **Cơ chế Xử lý Chuỗi & HTML An toàn**:
   - Tự động thay thế các ký tự HTML nguy hiểm (`<`, `>`, `&`) từ phản hồi AI của Gemini thông qua hàm `html.escape()` trước khi chèn vào tin nhắn.
   - Chuyển đổi cú pháp in đậm Markdown thông dụng `**text**` từ AI thành tag HTML `<b>text</b>` để giữ nguyên tính nhấn mạnh trực quan trên Telegram.
5. **Phân mảnh Tin nhắn Thông minh (Chunking)**:
   - Tự động chia nhỏ tin nhắn dài vượt giới hạn 4096 ký tự của Telegram bằng thuật toán tách theo dòng văn bản (giới hạn an toàn `< 4000` ký tự mỗi tin) để không bị lỗi `400 Bad Request`.
6. **Chế độ Fallback Plain Text Khẩn cấp**:
   - Nếu Telegram từ chối định dạng HTML do lỗi cú pháp sinh ra từ AI, Bot sẽ tự động loại bỏ các thẻ HTML và thử gửi lại dưới dạng văn bản thuần túy (Plain Text), đảm bảo tin nhắn báo cáo không bao giờ bị nghẽn hay thất lạc.

---

## 2. Thành phần 2: `stock_hunt/main.py`

Thành phần điều phối toàn bộ quy trình, chạy định kỳ và ghi log chi tiết.

### Điểm nổi bật trong thiết kế:
1. **Top-Level Imports**:
   - Đưa tất cả các lệnh import của các mô-đun (`run_scan` từ `scanner`, `analyze_candidate` từ `ai_analyzer`, `send_hunt_report` từ `telegram_bot`) lên đầu tệp `main.py` (top-level imports).
   - Xóa bỏ các khối `try-except import` rườm rà trong thân hàm giúp hệ thống phản hồi lỗi nhập khẩu ngay lập tức khi khởi động, tăng tính minh bạch và dễ bảo trì.
2. **Hệ thống Ghi log Chuyên nghiệp**:
   - Sử dụng `logging.handlers.RotatingFileHandler` ghi log vào `stock_hunt/logs/stock_hunt.log` với dung lượng tối đa **5MB** và tự động giữ **3 bản backup**.
   - Hỗ trợ mã hóa **UTF-8** đầy đủ để hiển thị chuẩn xác tiếng Việt có dấu trong log.
   - Đồng thời xuất ra màn hình (Console) để theo dõi thời gian thực.
   - Xóa bỏ việc cấu hình log module-level trùng lặp trong `scanner.py` và `ai_analyzer.py` để tránh hiện tượng log in 2 lần.
3. **Lập lịch Định kỳ Múi giờ Động (Timezone GMT+7 Aware)**:
   - Nhận cấu hình `SCHEDULE_TIMES` (ví dụ: `["10:15", "14:05"]` theo giờ Việt Nam GMT+7).
   - Tự động tính toán độ chênh lệch thời gian giữa múi giờ hệ thống của máy chủ chạy bot (dù chạy trên UTC, PST...) để quy đổi chính xác giờ kích hoạt tương ứng. Kích hoạt đúng thời điểm thị trường giao dịch.
4. **Graceful Shutdown (Tắt máy An toàn)**:
   - Đăng ký signal handler cho các tín hiệu hệ thống `SIGTERM` và `SIGINT` (Ctrl+C). Khi nhận tín hiệu, bot tiến hành ghi log thông báo tắt máy và đóng các luồng một cách an toàn thay vì crash chương trình.
5. **Chế độ Vận hành Tối ưu**:
   - Kích hoạt làm sạch phiên kết nối thị trường `reset_market()` duy nhất **1 lần** tại `main.py` trước khi gọi `run_scan()` để loại bỏ lãng phí hiệu năng.
6. **Tham số CLI `--now` Tiện dụng**:
   - Tích hợp cờ `--now` cho phép người dùng chạy quét ngay lập tức thông qua tệp `.bat` để phục vụ việc kiểm tra dòng dữ liệu, kiểm thử kết nối Telegram và AI mà không cần chờ tới lịch hẹn giờ.

---

## 3. Bản đồ Luồng Dữ liệu (Workflow Data Map)

```mermaid
graph TD
    A[Scheduler / --now] -->|Kích hoạt| B[Reset Market Cache]
    B -->|Xóa phiên cũ| C[Chạy main.py]
    C -->|Gọi top-level import| D[scanner.py: run_scan]
    D -->|Layer 0 Pre-filter| E[Tải 1500 mã giá trị toàn sàn]
    E -->|RAM filtering| F[Thu hẹp còn 16 mã ứng viên]
    F -->|Vòng 1: EOD check & Price Normalization| G{Thỏa mãn bộ lọc thô?}
    G -- Không --> H[Bỏ qua mã, giảm 95% API calls]
    G -- Có --> I[Tải Volume Profile & PB]
    I --> J[Ghi đè rs_avg = stock_strength Percentile]
    J --> K{Vòng 3: Strict verification RS [25, 45]?}
    K -- Không --> L[Loại bỏ mã]
    K -- Có --> M[Tải full EOD 5Y & Foreign Flow]
    M --> N[Tạo scorecard English keys]
    N --> O[ai_analyzer: Gemini 3.5 Flash]
    O -->|Nhận định tiếng Việt| P[telegram_bot: Định dạng scorecard]
    P --> Q{Có ứng viên thỏa mãn?}
    Q -- Không --> R[Gửi tin nhắn Không tìm thấy]
    Q -- Có --> S[Gửi báo cáo HTML chi tiết]
    S -->|Lỗi HTML parse| T[Fallback gửi plain text]
```
