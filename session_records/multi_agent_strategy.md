# Chiến lược Phân công AI & Mẫu Prompt Đa Tác Vụ (Model Routing & Multi-Agent Strategy)

Tài liệu này đóng vai trò như một "Playbook" hướng dẫn cách điều phối và phân công công việc cho các mô hình AI khác nhau (Gemini, Claude) nhằm tối ưu hóa thời gian, chi phí (Token), và độ chính xác trong các dự án phát triển phần mềm bằng AI Agent.

---

## 1. Phân loại và Vai trò của các Model AI

### 1.1 Dòng Heavyweight (Hạng Nặng)
*Ví dụ: Claude 4.6 Opus, Gemini Pro 3.1 High*
* **Đặc điểm:** Suy luận đỉnh cao, hiểu ngữ cảnh phức tạp, tuân thủ nghiêm ngặt chỉ thị kiến trúc lớn. Chậm hơn và chi phí cao.
* **Vai trò chính: Kiến trúc sư Hệ thống (Architect) / Kiểm toán viên (Auditor)**
  - Phân tích yêu cầu nghiệp vụ phức tạp ở đầu dự án.
  - Phác thảo `implementation_plan.md` và Hợp đồng Dữ liệu (Data Contract).
  - Thực hiện System Audit, chẩn đoán lỗi logic chéo giữa nhiều module phức tạp.

### 1.2 Dòng Mid-weight (Hạng Trung)
*Ví dụ: Claude 4.6 Sonnet, Gemini Pro 3.1 Low/Medium*
* **Đặc điểm:** Cân bằng hoàn hảo giữa thông minh, tốc độ và chi phí. Khả năng lập trình xuất sắc, làm theo mẫu nhanh chóng.
* **Vai trò chính: Lập trình viên Chủ chốt (Senior Dev) / System Integrator**
  - Viết các module cốt lõi (như `scanner.py`, `ai_analyzer.py`).
  - Đóng vai trò Main Agent (người điều phối hàng ngày) để ra quyết định chia nhỏ task cho Subagents.
  - Xử lý các thư viện, framework, và logic hệ thống (như async, API request).

### 1.3 Dòng Lightweight (Hạng Nhẹ)
*Ví dụ: Gemini Flash 3.5*
* **Đặc điểm:** Tốc độ phản hồi chớp nhoáng, chi phí cực rẻ, bộ nhớ (Context Window) khổng lồ. Yếu hơn về mặt toán học hoặc suy luận hệ thống.
* **Vai trò chính: QA Tester / Data Parser / Vibe Coder / Subagent Chuyên biệt**
  - Đọc log, tóm tắt tài liệu lớn, chuyển đổi định dạng (JSON).
  - Thực thi các công việc cơ bắp lặp đi lặp lại (thêm logging, đổi tên biến hàng loạt).
  - Hoạt động ngầm làm Subagent liên tục chạy lệnh kiểm thử (QA Tester).

---

## 2. Chiến lược Điều phối Phễu (The Orchestration Strategy)

1. **Khởi tạo (High-tier):** Dùng Heavyweight để phác thảo Kiến trúc và Data Contract.
2. **Triển khai (Mid-tier):** Dùng Mid-weight (làm Main Agent) khởi tạo các Subagents (cũng Mid-weight) để code song song các module độc lập.
3. **Tinh chỉnh & Fix Bug (Low/Mid-tier):** Dùng Main Agent hoặc Lightweight để thực hiện các hotfix nhanh chóng bằng tool chỉnh sửa file trực tiếp thay vì khởi tạo Subagent (tránh lãng phí overhead context).
4. **Nghiệm thu (High-tier):** Bật lại Heavyweight để tiến hành Audit và đồng bộ tài liệu trước khi đóng gói Release.

---

## 3. Mẫu Prompt Quy Trình Chuẩn (Standard Prompt Template)

Sử dụng chuỗi lệnh (Prompt Chain) này cho bất kỳ dự án Agentic nào trong tương lai:

### Bước 1: Khởi tạo Kiến trúc
> *"Dưới đây là yêu cầu nghiệp vụ cho dự án [TÊN DỰ ÁN]. Đừng code vội. Hãy phác thảo Kiến trúc (Architecture) và Hợp đồng Dữ liệu (Data Contract: I/O, Data Types, Keys) vào `implementation_plan.md`. Ask for my approval."*

### Bước 2: Giao việc & Tích hợp (Sau khi duyệt)
> *"Kế hoạch đã duyệt. Hãy gọi các Subagents (Agent A viết [Module 1], Agent B viết [Module 2]). Yêu cầu chúng bám sát chặt chẽ Data Contract đã chốt ở Bước 1."*

### Bước 3: Kiểm thử Sớm (Shift-Left)
> *"Trước khi tích hợp vào luồng chính, hãy dùng công cụ tạo một kịch bản Mock Data ảo trong `scratch/test_logic.py` để tôi nghiệm thu logic tính toán của [Core Engine]."*

### Bước 4: Tinh chỉnh & Đồng bộ (Bảo trì)
> *"Tôi muốn đổi thông số [Tham số]. Hãy trực tiếp cập nhật code trong tệp liên quan, VÀ đồng thời cập nhật thay đổi này vào mọi tệp tài liệu thiết kế để đảm bảo không có sự trôi dạt kỹ thuật."*
