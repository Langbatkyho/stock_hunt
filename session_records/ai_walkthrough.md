# Hướng Dẫn Vận Hành AI: Cấu Trúc Và Hoạt Động Của `stock_hunt/ai_analyzer.py`

Tài liệu này chi tiết hóa kiến trúc, quyết định thiết kế và các chi tiết cài đặt của bộ phân tích AI sử dụng Gemini 3.5 Flash (`stock_hunt/ai_analyzer.py`), được thiết kế để đánh giá định lượng các cổ phiếu ứng viên tìm được từ scanner.

---

## 🛠️ Tổng Quan Các Tính Năng Cốt Lõi

Module `stock_hunt/ai_analyzer.py` được xây dựng với các thành phần cốt lõi sau:

1. **Giao tiếp SDK & Quản lý API Key (`google-genai`)**:
   - Sử dụng thư viện SDK `google-genai` chính thức và mới nhất (`from google import genai`).
   - Tự động nạp cấu hình từ `stock_hunt.config.GEMINI_API_KEY`.
   - Hỗ trợ cơ chế dự phòng tự động đọc từ biến môi trường hệ thống (`STOCKHUNT_GEMINI_API_KEY` và `GEMINI_API_KEY`) giúp tăng tính cơ động khi triển khai.

2. **Làm sạch Kiểu dữ liệu Numpy/Pandas (`_to_native`)**:
   - Tự động lọc và chuyển đổi đệ quy các giá trị trong scorecard sang kiểu dữ liệu nguyên bản (native types) của Python trước khi nạp vào AI.
   - Loại bỏ hoàn toàn các lỗi tuần tự hóa JSON và lỗi truyền tải dữ liệu khi gửi các định dạng float/int đặc thù của Pandas/Numpy trực tiếp sang API.
   - Centralized (tập trung) tại `stock_hunt/utils.py` và import trực tiếp vào `ai_analyzer.py` để tối ưu cấu trúc mã nguồn.

3. **Bộ tạo Prompt Kỹ thuật Động (`generate_prompt`)**:
   - Được viết hoàn toàn bằng **Tiếng Việt**.
   - Cung cấp bối cảnh kỹ thuật riêng biệt cho AI tùy theo mẫu hình bộ lọc phát hiện ra cổ phiếu (e.g., *Tích lũy phá nền*, *Hổ gặp nạn*, *Vua sập bẫy*).
   - Lọc động các chỉ số: Chỉ đưa vào prompt các chỉ số kỹ thuật thực tế có sẵn và khả dụng trong scorecard, ngăn chặn AI bị "ảo giác" tự bịa dữ liệu.
   - Khống chế kết quả phân tích cô đọng dưới **150–200 từ** với cấu trúc 3 phần bắt buộc:
     1. **So sánh Sức mạnh**: So sánh kỹ thuật và dòng tiền của cổ phiếu.
     2. **Xu hướng Ngắn hạn**: Dự báo xu hướng giá ngắn hạn (Tăng, Giảm, hay Tích lũy).
     3. **Khuyến nghị**: Đưa ra hành động rõ ràng (MUA, BÁN hoặc QUAN SÁT) kèm theo một lý do định lượng then chốt nhất.

4. **Vòng lặp Retry 3 lần Siêu bền bỉ (`analyze_candidate`)**:
   - Bắt chính xác lỗi vượt hạn mức / nghẽn mạng **429 (ResourceExhausted / Rate Limit)**.
   - Tự động đưa tiến trình vào giấc ngủ **65 giây** khi gặp lỗi 429 trước khi thử lại.
   - Ngủ **2 giây** đối với các lỗi tạm thời khác.
   - Trả về thông tin báo lỗi sạch sẽ thay vì làm sập toàn bộ chu kỳ quét của bot nếu cả 3 lần thử đều thất bại.

---

## 📁 Cấu Trúc Tệp Tin

Tệp nguồn được lưu trữ tại:
- **Đường dẫn**: `d:\Nghiên cứu AI\vnstock-agent-guide\stock_hunt\ai_analyzer.py`

---

## 🔍 Chi Tiết Hoạt Động Của Mã Nguồn

### 1. Bản Đồ Ánh Xạ Chỉ Số Động
Để đảm bảo prompt gửi cho Gemini trực quan và sạch sẽ, các khoá tiếng Anh chuẩn hóa của scorecard được dịch sang nhãn Tiếng Việt tương ứng:
```python
INDICATOR_LABELS = {
    'current_price': 'Thị giá',
    '1D_pct': 'Biến động 1D (%)',
    '1M_pct': 'Biến động 1M (%)',
    '1Y_pct': 'Biến động 1Y (%)',
    '5Y_pct': 'Biến động 5Y (%)',
    'consecutive_up': 'Số phiên tăng liên tiếp',
    'vol_vs_sma10_pct': 'Khối lượng so với SMA10 (%)',
    'vol_vs_sma20_pct': 'Khối lượng so với SMA20 (%)',
    'active_buy_pct': 'Tỷ lệ mua chủ động (%)',
    'rsi_14': 'RSI(14)',
    'rsi_status': 'Trạng thái RSI',
    'macd_hist': 'MACD Histogram',
    'macd_status': 'Trạng thái MACD',
    'price_vs_ma10_pct': '% giá so với MA10',
    'price_vs_ma20_pct': '% giá so với MA20',
    'price_vs_ma50_pct': '% giá so với MA50',
    'rs_3D': 'Chỉ số RS 3 ngày',
    'rs_1M': 'Chỉ số RS 1 tháng',
    'rs_avg': 'Chỉ số RS trung bình (Percentile Rank)',
    'foreign_net_vol_20d': 'Giao dịch khối ngoại 20 phiên (khối lượng)',
    'beta': 'Hệ số Beta',
    'pe': 'Định giá P/E',
    'pb': 'Định giá P/B',
    'market_cap': 'Vốn hóa thị trường'
}
```

### 2. Thích Ứng Bối Cảnh Chiến Lược
Prompt động thay đổi định hướng chuyên môn sâu dựa theo từng chiến lược:
- **Tích lũy phá nền**: Tập trung vào điểm bùng nổ (breakout) vượt nền kháng cự và thanh khoản xác nhận.
- **Hổ gặp nạn**: Tập trung vào nhịp điều chỉnh ngắn hạn lành mạnh trong xu hướng tăng mạnh để tìm điểm đảo chiều dòng tiền (reversal).
- **Vua sập bẫy**: Tập trung vào mô hình bẫy giảm giá (Bear Trap), dụ lực bán tháo ở hỗ trợ rồi nhanh chóng kéo ngược hấp thụ mạnh.

### 3. Thiết Kế Cơ Chế Tự Phục Hồi (Auto-Recovery)
Đoạn mã xử lý lỗi tần suất gọi API (Rate Limit) hoạt động ổn định:
```python
max_retries = 3
for attempt in range(1, max_retries + 1):
    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text
    except Exception as e:
        err_str = str(e)
        # Kiểm tra lỗi Rate Limit 429 / Hết hạn ngạch
        if "429" in err_str or "ResourceExhausted" in err_str or "quota" in err_str.lower():
            time.sleep(65)
        else:
            time.sleep(2)
```
