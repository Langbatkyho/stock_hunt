# Hướng dẫn thiết lập chạy stock_hunt trên Windows 11 Task Scheduler

Tài liệu này hướng dẫn cách cấu hình bộ lập lịch tự động của Windows (Task Scheduler) để chạy `stock_hunt` định kỳ vào lúc 10:15 và 14:05 (Giờ Việt Nam GMT+7). Việc này giúp tối ưu hóa tài nguyên RAM thay vì phải duy trì vòng lặp Python liên tục.

---

## 1. Cơ chế hoạt động
Hệ thống sử dụng tệp lệnh `run_hunt_task.bat` đã được cấu hình sẵn. Khi Task Scheduler kích hoạt tệp này:
1. Nó kích hoạt biến môi trường `set PYTHONUTF8=1` để tránh lỗi font chữ tiếng Việt trên Windows.
2. Di chuyển chính xác vào thư mục làm việc của dự án.
3. Kích hoạt môi trường ảo Python (`.venv`) của người dùng.
4. Chạy `python -m stock_hunt.main --now`.
5. Cờ `--now` thông báo cho hệ thống quét đúng 1 lần duy nhất trên thị trường thực tế rồi tự thoát an toàn, giải phóng hoàn toàn bộ nhớ RAM.

---

## 2. Các bước cấu hình chi tiết

### Bước 1: Mở Task Scheduler
1. Nhấn phím `Windows` trên bàn phím.
2. Tìm kiếm cụm từ **Task Scheduler**.
3. Nhấp chuột phải vào ứng dụng và chọn **Run as administrator** (Chạy dưới quyền quản trị).

### Bước 2: Tạo Tác vụ (Create Task)
1. Ở bảng điều hướng bên phải (Actions panel), nhấn chọn **Create Task...** (Không chọn *Create Basic Task*).
2. **Tại tab General (Chung):**
   - **Name:** Nhập tên tác vụ, ví dụ: `Stock Hunt Bot`
   - **Security options:** Chọn **Run whether user is logged on or not** (Để tác vụ tự động kích hoạt ngay cả khi bạn khóa máy hoặc không đăng nhập).
   - Đánh dấu chọn vào ô **Hidden** (Để tiến hành chạy ẩn, không làm hiện cửa sổ CMD màu đen cản trở công việc).

### Bước 3: Thiết lập Lịch trình kích hoạt (Triggers)
1. Chuyển sang tab **Triggers**, nhấn nút **New...**
2. Chọn tần suất chạy là **Daily** (Hàng ngày).
3. Tại ô thời gian `Start:`, nhập mốc đầu tiên là **10:15:00**, nhấn **OK**.
4. Nhấn **New...** lần nữa.
5. Chọn **Daily**, nhập mốc thời gian thứ hai là **14:05:00**, nhấn **OK**.

### Bước 4: Thiết lập Hành động (Actions)
1. Chuyển sang tab **Actions**, nhấn nút **New...**
2. **Action:** Chọn `Start a program`.
3. **Program/script:** Nhấp `Browse...` và tìm tới tệp:
   `D:\Nghiên cứu AI\vnstock-agent-guide\stock_hunt\run_hunt_task.bat`
4. **Bắt buộc:** Tại ô **Start in (optional):**, bạn phải khai báo thư mục làm việc để Batch chạy đúng vị trí tương đối:
   `D:\Nghiên cứu AI\vnstock-agent-guide\stock_hunt\`
5. Nhấn **OK**.

### Bước 5: Cấu hình Khắc phục Sự cố (Settings)
1. Chuyển sang tab **Settings**.
2. Đánh dấu tích vào ô: **Run task as soon as possible after a scheduled start is missed** (Giúp chạy bù tác vụ ngay khi máy tính được đánh thức từ chế độ Sleep/Hibernate).
3. Đánh dấu chọn ô: **If the task fails, restart every:** `1 minute` và đặt giá trị lần thử lại là `3 times`.
4. Nhấn **OK** để lưu toàn bộ cấu hình. 
5. Hệ thống sẽ hiển thị một hộp thoại yêu cầu bạn nhập mật khẩu tài khoản Windows đang đăng nhập trên thiết bị để phân quyền chạy ngầm.

---

## 3. Cách nghiệm thu hệ thống
1. Tại danh mục `Task Scheduler Library` ở giữa màn hình, tìm tác vụ `Stock Hunt Bot`.
2. Nhấp chuột phải vào dòng đó và chọn **Run**.
3. Sau khoảng 1-2 phút, kiểm tra tin nhắn Telegram của bạn để xác minh bot đã gửi báo cáo đầy đủ.
4. Mọi lỗi phát sinh trong lúc Task Scheduler chạy ngầm sẽ được ghi nhận tại log file: `stock_hunt/logs/stock_hunt.log`.
