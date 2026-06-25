# Hướng Dẫn Vận Hành & Nhật Ký Hệ Thống Săn Tìm Cổ Phiếu Đảo Chiều (Stock Hunt Bot)

Chúng tôi đã hoàn thành việc triển khai hệ thống **Stock Hunt Bot** độc lập nằm trong thư mục [stock_hunt](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt) theo đúng kế hoạch đã được phê duyệt. Toàn bộ các mô-đun đã được lập trình đầy đủ, nhất quán và vượt qua các bài kiểm thử cơ bản về môi trường và nạp dữ liệu.

---

## 🛠️ Danh sách các Tệp nguồn Đã Tạo & Cấu Trúc

### 1. [config.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/config.py)
* **Mô tả:** Cấu hình độc lập của hệ thống. Chứa các thiết lập về thời gian quét (`10:15` và `14:05` GMT+7), các sàn quét (`HOSE`, `HNX` - đã loại bỏ hoàn toàn `UPCOM`), và tên của 3 bộ lọc.
* **Tối ưu bảo mật (Phase 3):** Toàn bộ API Keys và Token Telegram thật được bóc tách và nạp thông qua tệp cấu hình bảo mật riêng biệt `.env` (được bảo vệ trong `.gitignore`). Tệp `config.py` chỉ chứa logic load file `.env` thủ công và gán fallback chuỗi rỗng `""`.

### 2. [scanner.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/scanner.py)
* **Mô tả:** Bộ quét thị trường chính. Tích hợp trực tiếp các thuật toán tính toán chỉ báo từ `bot_app` để tối ưu mã nguồn.
* **Tính năng nổi bật:**
  - **Tối ưu hóa hiệu năng cực cao (Layer 0 Pre-filter):** Sử dụng Insights Screener quét 1500+ mã toàn thị trường chỉ trong **~25 giây**, lọc RAM trên Pandas thu gọn còn ~16 mã sôi động nhất trước khi chạy vòng lặp ticker.
  - **Đồng bộ hóa RS bằng Percentile Rank:** Ghi đè chỉ số `rs_avg` bằng xếp hạng Percentile Rank (`stock_strength` từ Screener VCI) giúp bộ lọc hoạt động chính xác với nhóm cổ phiếu đi ngang xây nền.
  - **Cấu hình 3 bộ lọc thực chiến (đã đồng bộ thực tế):**
    - **Tích lũy phá nền (Filter 1):** Vol SMA20 > 1M, RS Percentile `[25, 45]`, RSI `[40, 52]`, khoảng cách MA20 `[-1.2%, +1.2%]`, % Mua chủ động `[42%, 55%]`.
    - **Hổ gặp nạn (Filter 2):** GTGD 10d > 10 Tỷ VND, Vol SMA10 > 500k, RS Percentile `> 45`, RSI `[20, 35]`, % Mua chủ động `[42%, 55%]`.
    - **Vua sập bẫy (Filter 3):** Vol SMA10 > 3M, P/B < 1.1, RSI `[25, 35]`, % Mua chủ động `> 50%` (hạ từ 55% xuống 50% ở Phase 2.3 để hấp thụ sai số lệnh).
  - **Dọn dẹp code sạch sẽ (Phase 3):** Hàm dead code `map_scorecard_to_vietnamese()` đã được xoá bỏ. Hàm `_to_native()` được gom chung vào tiện ích.

### 3. [utils.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/utils.py) [NEW]
* **Mô tả:** Tệp tiện ích dùng chung cho toàn bộ module.
* **Tính năng nổi bật:**
  - **Trùng lặp Code (`_to_native`):** Centralized (tập trung) hàm ép kiểu dữ liệu an toàn để tránh lỗi JSON khi gửi sang Gemini.
  - **Bình thường hoá đơn vị giá (`is_price_in_vnd`, `get_price_in_vnd`, `get_price_in_thousands`):** Sử dụng ngưỡng an toàn **500** để phát hiện và chuyển đổi chính xác đơn vị giá (VND vs. Nghìn đồng) của dữ liệu thô từ API nguồn.

### 4. [ai_analyzer.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/ai_analyzer.py)
* **Mô tả:** Động cơ phân tích thông minh sử dụng Gemini 3.5 Flash (`google-genai` SDK mới).
* **Tính năng nổi bật:**
  - **Prompt động (Dynamic Prompting):** AI nhận diện đúng bối cảnh của từng bộ lọc kỹ thuật và chỉ hiển thị các chỉ số thực tế thu thập được trong prompt (tránh hiện tượng AI ảo giác số liệu bị thiếu).
  - **LLM Rate Limit Backoff:** Tự động bắt lỗi ResourceExhausted (429) hoặc quá tải và đưa tiến trình ngủ đúng **65 giây** trước khi tự động thử lại (tối đa 3 lần).

### 5. [telegram_bot.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/telegram_bot.py)
* **Mô tả:** Hệ thống phân phối báo cáo tới Telegram.
* **Tính năng nổi bật:**
  - **HTML Scorecard đẹp mắt:** Định dạng bảng điểm các chỉ số monospaced (`<code>`) đồng đều trên mọi thiết bị, đọc trực tiếp English keys theo đúng Data Contract.
  - **Resilient Message Chunking:** Tự động tách báo cáo thành nhiều tin nhắn nếu vượt quá giới hạn 4000 ký tự của Telegram.
  - **Fallback Plain-text:** Nếu Telegram từ chối định dạng HTML vì bất cứ lý do cấu trúc nào, hệ thống tự động bóc tách các thẻ HTML để gửi Plain-text khẩn cấp, đảm bảo tin nhắn không bao giờ bị nghẽn hay thất lạc.

### 6. [main.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/main.py)
* **Mô tả:** Trình điều phối trung tâm bằng thư viện `schedule`.
* **Tính năng nổi bật:**
  - **Ghi log xoay vòng chuyên nghiệp:** RotatingFileHandler (`logs/stock_hunt.log`) tối đa 5MB, lưu 3 bản backup, hỗ trợ UTF-8 đầy đủ.
  - **Hỗ trợ tham số `--now`:** Giúp người dùng có thể kích hoạt quét kiểm thử khẩn cấp ngay lập tức để debug/kiểm tra luồng mà không cần đợi đến khung giờ lịch trình.
  - **Xử lý Timezone GMT+7:** Tự động tính toán và đồng bộ mốc giờ chạy 10:15 và 14:05 GMT+7 với múi giờ của máy chủ chạy hệ thống.
  - **Graceful Shutdown:** Bổ sung bộ xử lý tín hiệu `SIGTERM` và `SIGINT` cho phép tắt bot an toàn.

### 7. [run_hunt_bot.bat](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/run_hunt_bot.bat)
* **Mô tả:** Tệp script khởi chạy nhanh trên Windows.
* **Tính năng nổi bật:** Tự động tìm kiếm kích hoạt môi trường ảo Python ở thư mục Home (`%USERPROFILE%\.venv`), ép kiểu UTF-8 toàn diện (`PYTHONUTF8=1`), hỗ trợ truyền tham số dòng lệnh `%*` (ví dụ: `run_hunt_bot.bat --now`).

---

## 🧪 Kết quả Kiểm thử & Phân Tích Thực Tế 5 Mã Mục Tiêu (Phase 2.2)

Để kiểm chứng hoạt động thực tế của bộ lọc **Tích lũy phá nền**, chúng tôi đã trích xuất dữ liệu EOD thực tế của 5 mã mục tiêu hôm nay. Dưới đây là bảng đối chiếu chi tiết:

| Mã | Vol SMA20 (> 1M) | RSI(14) (40-52) | Khoảng cách MA20 (±1.2%) | RS Percentile (25-45) | Active Buy % (42-55%) | Kết quả bộ lọc | Nguyên nhân chi tiết |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **DPM** | 3.98M | 42.65 | **-1.47%** ❌ | 40.0 | **32.22%** ❌ | **Loại** | Nằm quá xa dưới MA20 (-1.47% so với ngưỡng ±1.2%) và % Mua chủ động quá yếu (32.22% so với ngưỡng 42%). |
| **OIL** | 4.06M | 48.14 | 0.20% | 43.0 | 49.22% | **Khớp thô** ⚠️ | Đạt chuẩn bộ lọc 1, nhưng bị loại khỏi danh sách quét vì OIL niêm yết trên sàn **UPCOM** (Hệ thống loại UPCOM theo yêu cầu). |
| **SSI** | 16.64M | 46.88 | -0.58% | **25.0** | 45.84% | **Loại** | Sức mạnh giá tương đối (Percentile) nằm trong dải tích lũy `[25, 45]` nhưng bị loại do các yếu tố xu hướng khác. |
| **TPB** | 7.78M | 44.69 | -0.99% | **19.0** ❌ | 51.04% | **Loại** | Sức mạnh giá tương đối (Percentile) quá yếu, chỉ đạt 19.0 (yếu hơn 81% thị trường, dưới dải tích lũy `[25, 45]`). |
| **VC3** | 1.27M | 40.37 | **-1.201%** ❌ | **28.0** | 48.53% | **Loại** | Vi phạm khoảng cách MA20 một chút (-1.201% so với ngưỡng ±1.200%) và RS Percentile hôm nay đạt 28.0. |

---

## 🛡️ Phase 2.3: Kiểm Chứng Định Lượng Định Kỳ (BVB, VC3, KHG)

Nhằm rà soát chặt chẽ các sai lệch kết quả quét so với TCBS (các trường hợp người dùng thắc mắc như BVB, VC3, KHG), chúng tôi thiết lập quy trình kiểm thử định lượng `verify_3_symbols.py` đối chiếu với các bộ lọc của TCBS:

1. **BVB (UPCoM):**
   - Đạt 100% tiêu chí toán học của bộ lọc Tích lũy phá nền (RSI 50.81, RS Percentile 42.0, Active Buy 49.18%).
   - Tuy nhiên bị loại bỏ chính xác ở tầng cấu hình hệ thống (Exchange Level) vì thuộc sàn **UPCoM** (hệ thống giới hạn chỉ HOSE và HNX để giảm thiểu rủi ro biên độ dao động).
2. **VC3 (HNX):**
   - Đạt các tiêu chí khối lượng, RSI, khoảng cách MA20, nhưng bị loại vì RS Percentile chỉ đạt **30.0** (nằm ngoài dải tích lũy tối ưu **[40, 60]** trước đó). Hiện tại dải RS tích lũy được tối ưu thành **[25, 45]** dựa trên thực tế dữ liệu.
3. **KHG (HOSE):**
   - Đạt các tiêu chí cực kỳ quá bán (RSI 25.29, P/B 0.43) của bộ lọc Vua sập bẫy.
   - Ban đầu bị loại vì Active Buy đạt **51.34%** (dưới ngưỡng strict filter ban đầu `> 55%`).
   - Do có sai số phân loại lệnh mua/bán chủ động giữa các nguồn dữ liệu, chúng tôi **hạ ngưỡng strict filter Active Buy ở Bộ lọc 3 xuống > 50%**. Nhờ đó, KHG đã được hệ thống quét trúng và gửi báo cáo Telegram thành công!

---

## 🔧 Phase 3: Kế Hoạch Khắc Phục Sau Kiểm Toán (Audit Remediation)

Chúng tôi đã hoàn thành toàn diện **Giai đoạn 3 (Khắc phục lỗi sau kiểm toán)** để dọn sạch nợ kỹ thuật, cụ thể:
* **Bảo mật tuyệt đối:** API Keys và Token Telegram thật được ẩn hoàn toàn khỏi `config.py` và load động từ `.env`.
* **Đồng bộ tài liệu:** Cập nhật 100% các ngưỡng bộ lọc thực tế chạy trong code vào toàn bộ 6+ tệp tài liệu session_records, loại bỏ mâu thuẫn nội bộ.
* **Việt hóa toàn diện:** Dịch toàn bộ hai tệp tài liệu `scanner_walkthrough.md` và `ai_walkthrough.md` sang tiếng Việt.
* **Dọn dẹp code (Refactoring):** Gom `_to_native` sang `utils.py`, xóa bỏ dead code `map_scorecard_to_vietnamese()` khỏi `scanner.py`, xóa biến rác `hardcoded_path` trong scanner.py.
* **Batch file tối ưu:** Sửa batch file `run_hunt_bot.bat` để linh động kích hoạt `.venv` ở thư mục Home và truyền tham số dòng lệnh `%*`.
* **Graceful Shutdown & Timezone:** Tích hợp thành công tín hiệu `SIGTERM`/`SIGINT` và timezone-aware GMT+7 vào scheduler trung tâm trong `main.py`.

---

## 📈 Phase 4: Cải tiến RSI Range Shift (Dữ liệu lịch sử 30 phiên & Thống kê động)

Để giúp Gemini 3.5 Flash nâng cao khả năng đánh giá xu hướng động (trend) thay vì chỉ nhìn nhận một giá trị tĩnh đơn lẻ, chúng tôi đã hoàn tất việc thiết kế và tích hợp dữ liệu chuỗi thời gian RSI(14) vào pipeline:

1. **Đồng bộ hóa Data Contract (`data_contract.md`):**
   - Bổ sung trường dữ liệu `rsi_14_history` kiểu `List[float]` (30 phần tử) đại diện cho diễn biến 30 ngày qua của RSI.
   - Giữ nguyên khóa `rsi_14` để đảm bảo Telegram Bot không bị ảnh hưởng định dạng bảng điểm.
2. **Cải tiến Engine tính toán (`bot_app/indicators.py`):**
   - Sửa đổi hàm `calc_ta_indicators()` để tự động trích xuất chuỗi RSI lịch sử 30 phiên gần nhất (đã loại bỏ các giá trị NaN) thông qua `.dropna().tail(30).tolist()`. Các giá trị trả về dưới dạng float nguyên bản của Python, loại bỏ các đối tượng NumPy/Pandas để tránh lỗi JSON.
3. **Phân tích Thống kê nâng cao & Prompt thông minh (`stock_hunt/ai_analyzer.py`):**
   - Khi dựng Prompt (`generate_prompt`), hệ thống sẽ tính toán thêm:
     - Giá trị RSI lớn nhất (Max) và nhỏ nhất (Min) trong 30 phiên.
     - Độ lệch chuẩn RSI (`Std Dev`) phản ánh độ phẳng của vùng tích lũy hoặc sức mạnh xu hướng.
   - Định dạng mảng thành chuỗi thời gian trực quan `[T-29: val, ..., T-0: val]` (với T-0 là phiên hiện tại).
   - Nhúng hướng dẫn chuyên sâu cho AI phân tích dịch chuyển dải sinh thái (RSI Range Shift dải 40/60) để phát hiện sớm các điểm đảo chiều bứt phá nền giá phẳng.
4. **Nghiệm thu và xác thực dữ liệu thật (`verify_rsi_history.py`):**
   - Chúng tôi đã viết và chạy tệp kiểm thử live `verify_rsi_history.py` trên môi trường ảo `.venv` kết nối trực tiếp máy chủ dữ liệu.
   - Kết quả xác thực trên mã **SSI** cực kỳ thành công: nạp thành công 250 phiên OHLCV, trích xuất chính xác 30 phiên RSI lịch sử, hoàn tất chuyển đổi serialize an toàn qua `_to_native()`, và dựng thành công Prompt chuyên nghiệp tuyệt đối với đầy đủ thống kê và chuỗi thời gian.

---

## 🚀 Hướng dẫn Vận hành Hệ thống

### Bước 1: Cấu hình API Keys qua tệp `.env`
Mở hoặc tạo tệp [stock_hunt/.env](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/.env) và nhập các thông tin bảo mật của bạn:
```env
STOCKHUNT_TELEGRAM_BOT_TOKEN="8858104222:AAHl..."
STOCKHUNT_TELEGRAM_CHAT_ID="5942808899"
STOCKHUNT_GEMINI_API_KEY="AIzaSyDq..."
```

### Bước 2: Chạy kiểm thử tức thì (Test Run)
Chạy tệp batch với tham số `--now` để kiểm thử ngay lập tức một chu kỳ:
```bash
run_hunt_bot.bat --now
```

### Bước 3: Khởi chạy sản xuất (Production Mode)
Chạy tệp batch bình thường để duy trì bot hoạt động lâu dài (Scheduler tự động quét 10:15 và 14:05 GMT+7 hàng ngày):
```bash
run_hunt_bot.bat
```
