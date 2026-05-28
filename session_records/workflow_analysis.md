# Phân tích Luồng công việc (Workflow Analysis) - Stock Hunt Bot

Tài liệu này tổng hợp các bài học rút ra từ quá trình phát triển hệ thống Stock Hunt Bot, đặc biệt tập trung vào việc quản trị dự án, điều phối tác vụ (delegation) và quản lý tài liệu trong một hệ thống Multi-agent.

## 1. Thiết lập Kiến trúc & Hợp đồng Dữ liệu (Data Contract)
* **Vấn đề đã gặp:** Ở giai đoạn đầu, các Subagents được phân công viết `scanner.py`, `ai_analyzer.py`, và `telegram_bot.py` song song nhưng không có thỏa thuận chung về định dạng dữ liệu truyền tải (Data Contract). Kết quả là sự bất đồng bộ giữa tiếng Việt/tiếng Anh ở các biến dict, dẫn đến lỗi tích hợp (Integration Error) toàn hệ thống.
* **Bài học (Best Practice):** Các Subagent không tự giao tiếp với nhau trong lúc lập trình. Do đó, **Hợp đồng dữ liệu (Data Contract)** quy định chính xác tên biến, schema I/O, và kiểu dữ liệu phải được thiết lập và phê duyệt **trước khi** khởi tạo bất kỳ Subagent nào.

## 2. Quản trị Tài liệu & Tinh chỉnh Logic (Iterative Prompting)
* **Vấn đề đã gặp:** Trong quá trình hiệu chỉnh tham số (chỉnh sửa ngưỡng RS, RSI, Volume), các thay đổi được cập nhật vào mã nguồn nhưng tài liệu gốc (như `implementation_plan.md` hay `Stock_filters.md`) bị bỏ quên. Điều này tạo ra khoản "nợ kỹ thuật" (technical debt) và gây ra cảnh báo đỏ (Critical) khi thực hiện System Audit.
* **Bài học (Best Practice):** 
  - **Single Source of Truth:** Tách các tham số thường xuyên thay đổi (thresholds) vào tệp cấu hình độc lập (`.env`, `config.py` hoặc `filters.yaml`) thay vì hard-code trong logic chính.
  - **Prompt Kép:** Khi ra lệnh thay đổi logic, luôn đính kèm chỉ thị đồng bộ tài liệu: *"Hãy cập nhật code VÀ cập nhật thay đổi này vào mọi tài liệu thiết kế liên quan"*.

## 3. Phân biệt Bản thiết kế (Living Plan) và Nhật ký (Changelog)
* **Vấn đề đã gặp:** Tài liệu `implementation_plan.md` phình to lên hơn 500 dòng do bị nhồi nhét nội dung của nhiều giai đoạn (Phase 2, Phase 3). AI phải tiêu tốn rất nhiều Token và thời gian để đọc lại các lịch sử lỗi thời.
* **Bài học (Best Practice):** Tách biệt rõ ràng:
  - `implementation_plan.md`: Chỉ chứa kiến trúc và quy trình hiện tại (Living Document).
  - `changelog.md`: Dành để ghi chép lịch sử phiên bản, các bản vá lỗi (hotfix), và quá trình tiến hóa của hệ thống.

## 4. Kiểm thử sớm (Shift-Left Testing)
* **Vấn đề đã gặp:** Ở giai đoạn cuối (Phase 3), khi áp dụng hệ thống trên dữ liệu thực tế, người dùng mới đặt câu hỏi về tính chính xác toán học của các bộ lọc.
* **Bài học (Best Practice):** Bắt buộc xây dựng script Mock Data (`test_scan.py` hoặc `scratch/test_logic.py`) để kiểm tra độ tin cậy của thuật toán (Indicator Engine) trước khi tích hợp vào luồng chính. Thực hiện kiểm thử (TDD) sớm giúp ngăn chặn lỗi rò rỉ dữ liệu.
