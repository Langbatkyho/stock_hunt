# Stock Hunt - Data Contract v1.0 (Bản đặc tả cấu trúc Scorecard)

Tài liệu này định nghĩa cấu trúc dữ liệu chính thức cho đối tượng `scorecard` (bảng chỉ số kỹ thuật của cổ phiếu) được truyền tải giữa các thành phần trong hệ thống:
**Scanner (`scanner.py`)** -> **AI Analyzer (`ai_analyzer.py`)** -> **Telegram Bot (`telegram_bot.py`)**

> [!IMPORTANT]
> **Quy tắc vàng:** Tất cả các keys trong dictionary `scorecard` bắt buộc phải sử dụng **tiếng Anh nguyên bản** (English keys) kế thừa trực tiếp từ đầu ra của `bot_app/indicators.py::build_scorecard`. Việc dịch thuật hoặc hiển thị tiếng Việt chỉ được phép thực hiện ở **lớp hiển thị cuối cùng** (phần tạo message HTML của Telegram Bot).

---

## 1. Cấu trúc trường dữ liệu Scorecard (English Keys)

Dưới đây là danh sách đầy đủ các trường dữ liệu và kiểu dữ liệu chuẩn của chúng:

| Key trong Scorecard | Ý nghĩa kỹ thuật | Kiểu dữ liệu | Ví dụ giá trị |
|---|---|---|---|
| `symbol` | Mã cổ phiếu | `str` | `"VCB"` |
| `current_price` | Thị giá hiện tại (nghìn đồng) | `float` | `92.5` |
| `1D_pct` | Biến động giá 1 ngày gần nhất (%) | `float` | `1.5` |
| `1M_pct` | Biến động giá 1 tháng gần nhất (%) | `float` | `-3.2` |
| `1Y_pct` | Biến động giá 1 năm gần nhất (%) | `float` | `12.8` |
| `5Y_pct` | Biến động giá 5 năm gần nhất (%) | `float` | `45.6` |
| `consecutive_up` | Số phiên tăng giá liên tiếp | `int` | `3` |
| `vol_vs_sma10_pct` | Khối lượng giao dịch so với SMA10 (%) | `float` | `125.4` (125.4%) |
| `vol_vs_sma20_pct` | Khối lượng giao dịch so với SMA20 (%) | `float` | `98.2` (98.2%) |
| `active_buy_pct` | Tỷ lệ mua chủ động (%) | `float` | `51.5` (51.5%) |
| `rsi_14` | Chỉ số RSI 14 phiên | `float` | `48.5` |
| `rsi_status` | Trạng thái RSI | `str` | `"Trung tính"` / `"Quá bán"` |
| `macd_hist` | Giá trị cột MACD Histogram | `float` | `0.15` |
| `macd_status` | Trạng thái MACD so với Signal line | `str` | `"Cắt lên"` / `"Cắt xuống"` |
| `price_vs_ma10_pct` | Khoảng cách giá hiện tại so với MA10 (%) | `float` | `0.8` (cao hơn MA10 0.8%) |
| `price_vs_ma20_pct` | Khoảng cách giá hiện tại so với MA20 (%) | `float` | `-1.1` (thấp hơn MA20 1.1%) |
| `price_vs_ma50_pct` | Khoảng cách giá hiện tại so với MA50 (%) | `float` | `2.5` (cao hơn MA50 2.5%) |
| `rs_3D` | Chỉ số Sức mạnh giá (RS) ngắn hạn 3 ngày | `float` | `58.2` |
| `rs_1M` | Chỉ số RS trung hạn 1 tháng | `float` | `62.1` |
| `rs_avg` | Điểm RS Percentile trung bình (ghi đè bằng stock_strength từ Screener VCI) | `float` | `60.5` |
| `foreign_net_vol_20d`| Khối lượng giao dịch ròng khối ngoại 20 phiên | `float` hoặc `int` | `-250000` (bán ròng) |
| `beta` | Hệ số Beta so với thị trường | `float` | `1.15` |
| `pe` | Hệ số P/E | `float` | `14.2` |
| `pb` | Hệ số P/B | `float` | `1.85` |
| `market_cap` | Vốn hóa thị trường (tỷ đồng) | `float` | `320500.0` |

---

## 2. Quy chuẩn Dữ liệu nguyên bản (Data Serialization)

Để tránh lỗi crash JSON hoặc lỗi định dạng khi gửi dữ liệu sang API Gemini hoặc qua Telegram, toàn bộ các giá trị trong `scorecard` bắt buộc phải đi qua hàm chuyển đổi về kiểu dữ liệu thuần Python (native types):
- **Numpy/Pandas types** (`np.float64`, `np.int64`, v.v.) -> Chuyển sang `float`, `int`.
- **NaN / Inf / None** -> Chuyển sang `None` hoặc `0` tùy ngữ cảnh hiển thị.
- **Datetime/Timestamp** -> Chuyển sang chuỗi `str` (Y-m-d).

Hàm chuyển đổi chuẩn được tập trung tại tệp tiện ích `stock_hunt/utils.py` và import trực tiếp vào cả `scanner.py` và `ai_analyzer.py` trước khi xử lý dữ liệu.

---

## 3. Bản đồ ánh xạ Việt hóa cuối cùng (Telegram Format Layer)

Bản đồ dưới đây được sử dụng để hiển thị tin nhắn Telegram và phân tích AI, tuyệt đối không dùng làm key trong bộ nhớ hay file lưu trữ tạm:

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
    'rs_avg': 'Chỉ số RS trung bình',
    'foreign_net_vol_20d': 'Giao dịch khối ngoại 20 phiên (khối lượng)',
    'beta': 'Hệ số Beta',
    'pe': 'Định giá P/E',
    'pb': 'Định giá P/B',
    'market_cap': 'Vốn hóa thị trường'
}
```

---
*Cập nhật lần cuối: 27/05/2026 bởi Antigravity (Phase 3)*
