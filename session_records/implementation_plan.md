# Goal Description

Tạo một Telegram chatbot mới (độc lập với bot_app hiện tại) nằm trong thư mục `stock_hunt` để tự động săn tìm các cổ phiếu có dấu hiệu đảo chiều kỹ thuật. 
Bot sẽ hoạt động cố định vào hai khung giờ 10:15 và 14:05 (GMT+7). Quá trình quét sử dụng pre-filter qua API Insights để tối ưu tốc độ, sau đó lọc chuyên sâu dựa trên các bộ lọc (Tích lũy phá nền, Hổ gặp nạn, Vua sập bẫy) từ `Stock_filters.md`. Những cổ phiếu thoả mãn bộ lọc sẽ được gửi cho Gemini 3.5 Flash đánh giá và báo cáo kết quả qua Telegram.

## User Review Required

> [!IMPORTANT]
> **API Keys:** Bot yêu cầu cấu hình Telegram Token và Gemini API Key riêng. File config sẽ thiết lập thông qua biến môi trường tĩnh `.env`.

> [!NOTE]
> **Tái sử dụng code:** Thư mục `stock_hunt` import trực tiếp các hàm tiện ích tính toán và lấy dữ liệu từ `bot_app` thông qua việc trỏ đường dẫn (`sys.path`), tái sử dụng logic đã kiểm chứng.

## Current Architecture

Hệ thống được tổ chức thành các module tách biệt, hoạt động đồng bộ:

### [stock_hunt/config.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/stock_hunt/config.py)
Cấu hình độc lập với `bot_app/config.py`. Quản lý cấu hình thông qua `.env` (Telegram Token, Gemini API Key), thời gian chạy (`10:15` và `14:05`), và các ngưỡng thiết lập bộ lọc cơ bản. Không chứa hard-code nhạy cảm.

### [stock_hunt/scanner.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/stock_hunt/scanner.py)
Logic cốt lõi để lọc cổ phiếu. Hoạt động theo quy trình phân tầng:
- **Layer 0 (Pre-filter):** Gọi API `Insights().screener` để lọc thô khối lượng giao dịch và giá trị dòng tiền của mã 3 ký tự (chỉ quét HOSE/HNX), giảm số lượng quét từ 1500 xuống còn ~16 mã để tăng tốc. Lấy trực tiếp điểm Percentile Rank (stock_strength) để đại diện cho RS Trung bình.
- **Layer 1 (Verification):** Tính toán chi tiết các chỉ báo (RSI, RS, MA20, Active Buy) qua dữ liệu lịch sử OHLCV và chốt lọc chặt chẽ các điều kiện cuối cùng.

### [stock_hunt/ai_analyzer.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/stock_hunt/ai_analyzer.py)
Chịu trách nhiệm phân tích dữ liệu qua AI. Xây dựng Prompt động với các chỉ số kỹ thuật và gọi Gemini 3.5 Flash để đánh giá. Có cơ chế Retry tự động và bắt lỗi 429 (ngủ 65 giây chờ API phục hồi).

### [stock_hunt/telegram_bot.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/stock_hunt/telegram_bot.py)
Xử lý giao diện đầu ra bằng HTML chuẩn hóa. Nhận dữ liệu ứng viên và gửi báo cáo bao gồm Bảng điểm (Scorecard) + Kết luận AI vào nhóm Telegram.

### [stock_hunt/main.py](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/stock_hunt/main.py)
Orchestrator chính của ứng dụng. Sử dụng thư viện `schedule` cài đặt bộ lên lịch định kỳ (10:15, 14:05). Ghi log hệ thống qua `RotatingFileHandler`. Cung cấp cờ `--now` để chạy kiểm thử ngay lập tức.

### [stock_hunt/run_hunt_bot.bat](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/stock_hunt/run_hunt_bot.bat)
Script batch để khởi chạy bot thủ công trên Windows.

### [stock_hunt/run_hunt_task.bat](file:///d:/Nghi%C3%AAn%20c%E1%BB%A9u%20AI/vnstock-agent-guide/stock_hunt/run_hunt_task.bat)
Script batch tối ưu riêng cho Windows Task Scheduler (không lệnh pause) để chạy ẩn hoàn toàn.

## Verification Plan

### Automated Tests
- Kiểm tra tính toán toán học qua các Mock test (e.g. `test_scan.py`).
- Xác thực cơ chế phân tách Layer 0 và cấu trúc log.

### Manual Verification
- Chạy hệ thống trên thực tế với cờ `--now` để xác thực Telegram HTML render và kết nối API.
- Cấu hình và kiểm thử thành công qua Windows Task Scheduler.
