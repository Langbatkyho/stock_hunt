# Stock Hunt - Tiến độ thực hiện (Task Tracker)

## Phase 1: Tạo Nền Tảng (Đã hoàn thành)
- [x] Create `stock_hunt` directory
- [x] Create `stock_hunt/config.py` with API key placeholders and settings.
- [x] Create `stock_hunt/scanner.py` with logic to fetch list of symbols and evaluate the 3 filters from `Stock_filters.md`.
- [x] Create `stock_hunt/ai_analyzer.py` to prepare the prompt containing the data columns specified in `chi_so.md` and call Gemini.
- [x] Create `stock_hunt/telegram_bot.py` to format the HTML message and send via Telegram.
- [x] Create `stock_hunt/main.py` with `schedule` to run at 10:15 and 14:05.
- [x] Create `stock_hunt/test_scan.py` to test the performance of scanning HOSE/HNX exchanges.
- [x] Create `stock_hunt/run_hunt_bot.bat` for easy startup.

## Phase 2: Audit Hotfix (Đã hoàn thành)
- [x] Phase 2: Audit Hotfix (Main Agent & Subagents)
  - [x] Main Agent: Tạo file `stock_hunt/__init__.py` (Fix #2)
  - [x] Main Agent: Sửa `run_hunt_bot.bat` hoạt động tại project root (Fix #7)
  - [x] Data Engineer: Sửa `scanner.py` bỏ convert VN key, dùng config exchanges, loại bỏ trùng reset_market, sửa logging (Fix #3a, #4, #5, #6a)
  - [x] AI Engineer: Sửa `ai_analyzer.py` loại bỏ root logging `basicConfig` (Fix #6b)
  - [x] System Integrator: Sửa `main.py` đổi tên hàm `run_scan`, đưa import lên top-level (Fix #1, #8)
  - [x] System Integrator: Sửa `telegram_bot.py` đọc trực tiếp English keys (Fix #3b)
  - [x] Integration Smoke Test: Chạy chạy kiểm thử `python -m stock_hunt.main --now` để nghiệm thu cuối cùng.

## Phase 2.1: Performance Tuning & Hybrid RS (Đã hoàn thành)
- [x] Tích hợp Layer 0 Pre-filter via `Insights.screener` để tăng tốc độ quét gấp 25 làm (dưới 50 giây).
- [x] Lọc chặt chẽ các mã 3 ký tự (Equity symbols) loại bỏ chứng quyền & ETF.
- [x] Bảo vệ kiểu dữ liệu định giá P/B tránh lỗi so sánh string/float.
- [x] Chuyển đổi sang VN-Index Benchmark thông thường thay thế Custom Benchmark.
- [x] Tích hợp điểm Percentile Rank (`stock_strength` từ Screener) ghi đè lên `rs_avg`.

## Phase 2.2: Strict Verification Alignment (Đã hoàn thành)
- [x] Giải phóng bộ lọc thô `check_pre_filters` khỏi điều kiện RS tuyệt đối hẹp.
- [x] Di chuyển điều kiện lọc RS Percentile `[40, 60]` chặt chẽ xuống vòng xác minh cuối cùng (Strict Verification) trong `run_scan`.
- [x] Chạy kiểm thử khẩn cấp và kiểm chứng dữ liệu thực tế với 5 mã mục tiêu thành công tốt đẹp.

## Phase 2.3: Cross-Verification & Audit (BVB, VC3, KHG) (Đã hoàn thành)
- [x] Lập trình kịch bản test case định lượng `verify_3_symbols.py` trong thư mục `session_records/scratch/`.
- [x] Chạy kiểm thử thực tế trên môi trường ảo `.venv` đối chiếu với các bộ lọc tương đương của TCBS.
- [x] Giải thích định lượng chi tiết lý do BVB (UPCOM), VC3 (RS thấp), KHG (Mua CĐ yếu) bị loại trừ bởi hệ thống.
- [x] Tạo tệp báo cáo kiểm chứng chi tiết `audit_report.md` và lưu trữ hoạt động trong nhật ký hệ thống.

## Phase 3: Audit Remediation (Kế Hoạch Khắc Phục Sau Kiểm Toán - Đã hoàn thành)
- [x] **Ưu tiên 1: Bảo mật API Keys**
  - [x] Sửa `stock_hunt/config.py` để loại bỏ API keys thật (thay bằng `""`)
  - [x] Tạo tệp `stock_hunt/.env` chứa các API keys thật
  - [x] Cập nhật `.gitignore` để bỏ qua tệp `.env`
- [x] **Ưu tiên 2: Đồng bộ Tài liệu**
  - [x] Cập nhật ngưỡng bộ lọc thực tế (`[25, 45]` cho F1 RS, `[42%, 55%]` cho F1/F2 Active Buy, `> 50%` cho F3 Active Buy) trong các tài liệu:
    - [x] `walkthrough.md`
    - [x] `scanner_walkthrough.md`
    - [x] `implementation_plan.md`
    - [x] `data_contract.md` (cập nhật cả mô tả `rs_avg`)
    - [x] `agent_activity_log.md`
    - [x] `audit_report.md`
  - [x] Sửa lỗi mâu thuẫn nội bộ trong `walkthrough.md` (giữa dòng 21 và dòng 125)
  - [x] Dịch sang Tiếng Việt (Việt hóa):
    - [x] `scanner_walkthrough.md`
    - [x] `ai_walkthrough.md`
  - [x] Bổ sung thông tin Phase 2.3 và Phase 3 vào các tài liệu bị thiếu:
    - [x] `walkthrough.md`
    - [x] `scanner_walkthrough.md`
    - [x] `integration_report.md`
    - [x] `user_prompts.md`
- [x] **Ưu tiên 3: Dọn dẹp Code**
  - [x] Xóa bỏ hoặc chuyển hàm dead code `map_scorecard_to_vietnamese()` ra khỏi `scanner.py`
  - [x] Tạo tệp tiện ích `stock_hunt/utils.py` và chuyển hàm `_to_native()` dùng chung vào đây
  - [x] Xóa bỏ biến rác `hardcoded_path` tại `scanner.py:21-23`
  - [x] Cập nhật `run_hunt_bot.bat` dòng 12 (thêm `%*`) và thay user path bằng `%USERPROFILE%`
- [x] **Ưu tiên 4: Cải tiến Kỹ thuật**
  - [x] Thêm SIGTERM signal handler trong `main.py` để graceful shutdown
  - [x] Xây dựng unit tests cơ bản cho logic lọc trong `test_scan.py` sử dụng mock data
  - [x] Tối ưu hóa cuộc gọi API trong `scanner.py` (tải EOD 5Y ngay khi qua Layer 0 Pre-filter)
  - [x] Xóa bỏ các cấu hình rác không sử dụng trong `config.py`
  - [x] Bổ sung xử lý Timezone GMT+7 cho bộ scheduler trong `main.py`
  - [x] Chuẩn hóa đơn vị giá (is_in_thousands) trong `scanner.py` và `telegram_bot.py`
  - [x] Chạy nghiệm thu liên hợp `python -m stock_hunt.main --now` và chụp ảnh/lưu log báo cáo

## Tích hợp Tự động hóa qua Windows Task Scheduler (Đã hoàn thành)
- [x] Tạo tệp khởi chạy chuyên dụng `run_hunt_task.bat` loại bỏ pause.
- [x] Soạn thảo hướng dẫn cấu hình chi tiết `task_scheduler_guide.md`.
- [x] Kiểm tra tích hợp và cập nhật đồng bộ các tài liệu trong `session_records/`.
