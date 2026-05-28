# Nhật Ký Yêu Cầu Của Người Dùng (User Prompts Log)

Dưới đây là lưu trữ toàn bộ các yêu cầu của người dùng trong quá trình thiết kế, kiểm thử hiệu năng và triển khai thực tế tiểu dự án **Stock Hunt Bot**:

---

## 📅 Yêu cầu 1: Đề xuất Ý tưởng & Thiết kế Ban đầu
> **Nội dung:**
> "Tôi muốn tạo một Telegram chatbot mới (độc lập với bot_app trong project hiện tại) nhằm mục tiêu săn tìm các cổ phiếu có dấu hiệu đảo chiều kỹ thuật từ giảm sang tăng vào khung giờ 10:15 và 14:05 (GMT+7) để trading. 
> 
> Tôi đã đặt file stock_filters.md trong thư mục dự án chứa các bộ lọc với tiêu chí cụ thể để sàng lọc cổ phiếu. 
> 
> Tôi muốn hệ thống sử dụng các API mới nhất của Vnstock để quét ra các ứng viên cổ phiếu theo từng bộ lọc. Sau đó, dữ liệu từ bộ lọc nói trên được kết hợp với bộ chỉ số từ file chi_so.md trong thư mục dự án để gửi cho Gemini 3.5 Flash đánh giá phân tích và trả kết quả vào Telegram bot.
> 
> Tôi đã có cấu hình Telegram chatbot mới + Gemini 3.5 API Key mới để sử dụng cho dự án này, độc lập với bot_app.
> 
> Bạn hãy tạo một thư mục con tên là stock_hunt..."

---

## 📅 Yêu cầu 2: Trả lời Câu hỏi Khảo sát & Định hướng Chạy thử nghiệm
> **Nội dung:**
> "Tôi trả lời các câu hỏi như sau:
> 
> 2. Tôi muốn bot nhắn tin Không tìm thấy với từng bộ lọc.
> 1. Tôi muốn chạy 1 test để đánh giá thực tế mức độ nặng nhẹ của việc quét toàn bộ ba sàn. Tôi sẽ ưu tiên HSX hơn HNX và UPCOM là ưu tiên thấp nhất."

---

## 📅 Yêu cầu 3: Yêu cầu Chạy Thử nghiệm Đo lường Hiệu năng trước khi Viết mã
> **Nội dung:**
> "Tôi trả lời các câu hỏi như sau:
> 2. Tôi muốn bot nhắn tin Không tìm thấy với từng bộ lọc.
> 1. Tôi muốn chạy 1 test để đánh giá thực tế mức độ nặng nhẹ của việc quét toàn bộ ba sàn. Tôi sẽ ưu tiên HSX hơn HNX và UPCOM là ưu tiên thấp nhất.
> 
> Bạn hãy chỉ chạy test như tôi đang yêu cầu. Chưa thực hiện code hệ thống cho đến khi tôi chấp thuận toàn bộ Implementation Plan."

---

## 📅 Yêu cầu 4: Loại bỏ UPCOM ra khỏi Hệ thống
> **Nội dung:**
> "Vậy hãy loại trừ UPCOM ra khỏi hệ thống. Bạn cập nhật lại Implementation Plan để tôi duyệt."

---

## 📅 Yêu cầu 5: Tích hợp các Bài học Kinh nghiệm từ Workflow cũ
> **Nội dung:**
> "Bạn hãy rà soát lại các bài học trong Workflow Analysis của bot_app trong thư mục docs/session_records và cập nhật, bổ sung vào Implementation Plan nếu thấy cần thiết."

---

## 📅 Yêu cầu 6: Làm rõ việc Phân chia Subagent cho từng Công việc
> **Nội dung:**
> "Tôi muốn bạn làm rõ thêm trong Implementation Plan việc chia ra từng task nhỏ và chỉ định các subagent để thực hiện các task này."

---

## 📅 Yêu cầu 7: Phê duyệt Implementation Plan & Chỉ thị Code
> **Nội dung:**
> "Tôi đồng ý Implementation Plan của Gemini 3.1 Pro đề xuất, bạn hãy tiến hành kích hoạt các Subagent và bắt đầu viết code."

---

## 📅 Yêu cầu 8: Lưu trữ Hồ sơ Phiên làm việc (Session Records)
> **Nội dung:**
> "Bạn hãy tạo folder session_records trong thư mục stock_hunt. Sau đó bạn lưu toàn bộ các tài liệu cho tiểu dự án stock_hunt này, bao gồm các artifacts và cả prompts của tôi vào đó."

---

## 📅 Yêu cầu 9: Phản hồi về thời gian chạy lâu
> **Nội dung:**
> "Dừng lại, tôi thấy đã chạy gần 20 phút rồi không ra kết quả. Hãy dừng và phân tích lỗi"

---

## 📅 Yêu cầu 10: Yêu cầu rà soát lại từng cấu phần
> **Nội dung:**
> "Hãy dừng lại, 15 phút rồi vẫn không ra kết quả. Bạn phải thay đổi cách tiếp cận. Hãy rà soát chạy test lại từng task, từng cấu phần."

---

## 📅 Yêu cầu 11: Truy vấn kỹ năng kiến trúc giải pháp
> **Nội dung:**
> "Dừng lại, tôi muốn truy vấn skill kiến trúc hệ thống vnstock để tìm giải pháp tốt nhất.
> /vnstock-solution-architect hãy đọc kỹ Implementation Plan, các tác vụ, hàm đang gặp lỗi ở trên và tư vấn giải pháp cho tôi."

---

## 📅 Yêu cầu 12: Chạy kiểm thử sau khi kích hoạt Bot Telegram
> **Nội dung:**
> "Tôi đã kích hoạt Telegram bot, hãy chạy test 1 lần nữa."

---

## 📅 Yêu cầu 13: Yêu cầu ghi nhận file log đối chiếu bộ lọc
> **Nội dung:**
> "Bạn hãy ghi nhận lại file log cho lần chạy gần nhất để tôi quick test xem thực sự kết quả chạy có đúng theo các bộ lọc không?"

---

## 📅 Yêu cầu 14: Nghi ngờ kết quả và chỉ thị tập trung vào 5 mã cổ phiếu
> **Nội dung:**
> "Tôi nghi ngờ kết quả chạy trên vì tôi dùng bộ lọc Tích lũy phá nền trên TCBS ra 5 mã DPM, OIL, SSI, TPB và VC3.
> Bạn hãy tập trung duy nhất vào 5 mã trên và chỉ test với bộ lọc Tích lũy phá nền. Lưu ý lưu lại tất cả các dữ liệu đã quét từ hệ thống vnstock để đối chiếu với bộ lọc."

---

## 📅 Yêu cầu 15: Phát hiện sự khác biệt RS Trung bình
> **Nội dung:**
> "Tôi đã phát hiện ra sự khác biệt nằm ở tiêu chí RS Trung bình. Bạn hãy mô tả lại cách hệ thống tính toán chỉ số này như thế nào."

---

## 📅 Yêu cầu 16: Chỉ thị đổi sang Benchmark thông thường & kiểm tra API
> **Nội dung:**
> "Tôi đã hiểu, bộ lọc này cần sử dụng RS Trung bình tính theo Benchmark thông thường của thị trường chứ không phải Custom Benchmark của tôi.
> /vnstock-solution-architect Bạn kiểm tra lại Vnstock có cung cấp sẵn dữ liệu Benchmark phục vụ tính toán RS (tất cả các dải 3 ngày, 1 tháng, 3 tháng và 1 năm) như thế nào. Sau đó báo lại cho tôi để quyết định giải pháp"

---

## 📅 Yêu cầu 17: Phê duyệt Giải pháp và bảo toàn logic bot_app
> **Nội dung:**
> "Đồng ý. Hãy đảm bảo tuyệt đối không xâm phạm tới Custom Benchmark và các logic đang chạy của bot_app."

---

## 📅 Yêu cầu 18: Lựa chọn Giải pháp 1 và Yêu cầu Cập nhật Nhật ký session_records
> **Nội dung:**
> "Tôi chọn giải pháp 1"
> "Hãy cập nhật toàn bộ nhật ký hoạt động của main agent và subagent cũng như các tài liệu khác trong thư mục session_records của tiểu dự án stock_hunt này."

---

## 📅 Yêu cầu 19: Hiệu chỉnh Chỉ số RS trung bình & Phân tích định lượng BVB/VC3/KHG
> **Nội dung:**
> "Tôi kiểm tra lại thì TCBS sử dụng RS trung bình dựa trên xếp hàng RS Percentile của 500 cổ phiếu vốn hóa lớn nhất. Trong giải pháp tôi đã chấp thuận của bạn thì chúng ta chỉ tính trên 300 cổ phiếu... Bạn hãy phản biện về tính toán RS Trung bình dựa trên những phân tích trên."
> "Tôi muốn tiếp tục hiệu chỉnh lại mục tiêu RS Trung bình cho các bộ lọc. Hiện tại tôi dùng bộ lọc Tích lũy phá nền trên TCBS ra 3 mã với RS Trung bình như sau: DPM: 60, MBB: 60, VC3: 56. Bạn hãy kiểm tra dữ liệu RS Trung bình chúng ta đang có với các mã này, phân tích và đánh giá đề xuất điều chỉnh mục tiêu RS Trung bình cho các bộ lọc đang sử dụng."

---

## 📅 Yêu cầu 20: Audit Toàn diện Hệ thống & Thực hiện Kế hoạch Khắc phục Kiểm toán (Phase 3)
> **Nội dung:**
> "Bạn hãy audit toàn bộ bản ghi hoạt động của các main agent, subagent và hệ thống code. Hãy xác minh tính tuân thủ với Implementation Plan..."
> "Tôi đồng ý với System Audit Report của Claude Opus 4.6. Bạn hãy lưu lại tài liệu này vào thư mục stock_hunt\session_records, cập nhật Kế hoạch khắc phục vào Implementation Plan. Sau đó bạn tiến hành thực hiện toàn bộ kế hoạch khắc phục đó. Bạn có thể giao việc và điều khiển các subagent thực hiện nếu thấy cần."

