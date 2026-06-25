# Nhật ký thay đổi (Changelog & Activity Log)

Tài liệu này lưu trữ lịch sử các giai đoạn phát triển, các bản vá lỗi (hotfix), và các tinh chỉnh kỹ thuật (performance tuning) đã áp dụng vào dự án `stock_hunt`.

## Enterprise-Grade Resiliency & System Polish (Tháng 6/2026)
- **API Key Rotation & Fallback Model:** Nhằm khắc phục lỗi `429 Resource Exhausted` và `503 Service Unavailable` từ phía máy chủ Google Gemini, hệ thống đã được trang bị cơ chế tự động xoay vòng nhiều API keys dự phòng và cơ chế Fallback thông minh sang model `gemini-2.5-flash` khi model chính bị quá tải.
- **Exponential Backoff:** Bổ sung cơ chế chống spam/tự động nghỉ lũy tiến để giảm tải máy chủ và duy trì luồng tự động vĩnh viễn.
- **Cleanup Amnesia (Quy tắc dọn dẹp):** Khởi tạo `GLOBAL_CONSTRAINTS.md`, dọn dẹp các thư viện và hàm bị bỏ quên trong toàn bộ source code (như `_to_native` trong scanner).

## Tích hợp Tự động hóa qua Windows Task Scheduler (Tháng 5/2026)
- **Tạo Script tối ưu (`run_hunt_task.bat`):** Loại bỏ lệnh `pause` ở cuối tệp để tránh làm kẹt các tiến trình ngầm (zombie processes) khi Task Scheduler chạy tự động. Tự động áp dụng tham số `--now` để tắt bot ngay sau khi hoàn thành 1 chu kỳ quét.
- **Tài liệu hóa quy trình cấu hình:** Soạn thảo tệp `task_scheduler_guide.md` hướng dẫn chi tiết các bước thiết lập cấu hình trên giao diện đồ họa của Windows 11 Task Scheduler (bao gồm quyền admin, trigger Daily 10:15/14:05, chạy ẩn Hidden, tự động chạy bù nếu bị lỡ mốc giờ).

## Phase 3: Final Audit & Polish (Tháng 5/2026)
- **Tách cấu hình nhạy cảm:** Chuyển đổi mã nguồn sang sử dụng `python-dotenv` để ẩn các API Keys.
- **Cải thiện Logging:** Đồng bộ hóa logging utf-8 với cấu hình chuẩn. Thêm tính năng Graceful Shutdown cho luồng lập lịch.
- **Kiểm thử tự động (Unit Test):** Thiết lập `test_scan.py` sử dụng Mock Data (hàm drift phi tuyến và hàm sin) để chuẩn hóa độ chính xác toán học của các bộ lọc.

## Phase 2.2: Đồng bộ RS Metric & Tinh chỉnh quy trình lọc chặt (Tháng 5/2026)
- **Vấn đề:** Các mã đi ngang có RS thô quá thấp nên bị rớt từ bộ lọc thô trước khi nạp điểm Percentile Rank.
- **Khắc phục:** 
  - Sửa đổi hàm `check_pre_filters` để nới lỏng hoặc loại bỏ bộ lọc RS thô sớm.
  - Sửa vòng lặp quét chặt chẽ (`run_scan`) để dựa hoàn toàn vào điểm Percentile Rank (stock_strength) để đối chiếu điều kiện RS.
- **Hệ điều hành Windows:** Cập nhật script `run_hunt_bot.bat` kích hoạt môi trường ảo tại `C:\Users\Langbatkyho\.venv`.

## Phase 2.1: Performance Tuning & Data Sanitation (Tháng 5/2026)
- **Tối ưu tốc độ:** Nhận thấy danh sách quét 2 sàn chứa 955 mã làm quá trình kéo dài 20 phút. Đã áp dụng `Insights().screener` tại Layer 0 để thu gọn các mã 3 ký tự thoả mãn khối lượng/giá trị thô, giảm thời gian thực thi xuống dưới 7 phút (~16 mã).
- **An toàn ép kiểu:** Bọc logic P/B trong vòng `try-except` ép kiểu Float do API trả về None hoặc String ở một số mã (e.g., HAG) làm vỡ luồng phân tích.
- **Đồng bộ Indicator:** Chuyển đổi benchmark từ Custom Index sang `VNINDEX` chuẩn, và sử dụng trường `stock_strength` từ screener để ghi đè `rs_avg`.

## Phase 1 & 2: Khởi tạo và Hotfix Hợp đồng dữ liệu (Tháng 5/2026)
- **Khởi tạo:** Thiết lập khung 3 module: `scanner.py`, `ai_analyzer.py`, `telegram_bot.py`.
- **Lỗi giao tiếp (Data Contract Failure):** Module scanner trả về dict bằng tiếng Việt khiến bot và AI analyzer đọc lỗi. Đã thực hiện hotfix chuyển chuẩn giao tiếp sang tiếng Anh giữa các hàm (English Keys) để khắc phục lỗi JSON Serialization.
