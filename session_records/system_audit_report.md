# 🔍 Báo Cáo Kiểm Toán Toàn Diện Hệ Thống Stock Hunt Bot

**Ngày kiểm toán:** 27/05/2026  
**Kiểm toán viên:** Antigravity (Claude Opus 4.6 — Thinking)  
**Phương pháp:** Song song 2 subagent chuyên biệt (Code Quality Auditor + Documentation Compliance Auditor) kết hợp xác minh thủ công bởi Main Agent.  
**Phạm vi:** Toàn bộ 8 tệp mã nguồn + 10 tệp tài liệu session_records

---

## 📋 Tóm Tắt Điều Hành (Executive Summary)

Hệ thống Stock Hunt Bot hiện tại **hoạt động ổn định và đã qua kiểm thử thực tế thành công** (5 mã mục tiêu DPM/OIL/SSI/TPB/VC3 + 3 mã kiểm chứng chéo BVB/VC3/KHG). Tuy nhiên, quá trình **12 lượt subagent chỉnh sửa liên tiếp** qua 5 giai đoạn (Phase 1 → 2 → 2.1 → 2.2 → 2.3) đã tạo ra một khoảng cách đáng kể giữa **code thực tế** và **tài liệu ghi chép**.

### Bảng Điểm Tổng Quan

| Tiêu chí | Điểm | Nhận định |
|:---|:---:|:---|
| **Tính ổn định vận hành** | 🟢 9/10 | Bot chạy ổn định, gửi Telegram thành công, xử lý lỗi tốt |
| **Tuân thủ Implementation Plan** | 🟡 6/10 | Code đã vượt ra ngoài kế hoạch gốc do điều chỉnh ngưỡng nhiều lần |
| **Đồng bộ tài liệu** | 🔴 3/10 | **Nghiêm trọng** — Code và tài liệu lệch nhau ở các thông số then chốt |
| **Chất lượng code** | 🟡 7/10 | Tốt về tổng thể, nhưng có dead code và vấn đề bảo mật |
| **Bảo mật** | 🔴 4/10 | API keys thật hardcode trong config.py |

---

## 🔴 PHÁT HIỆN MỨC CRITICAL (Yêu cầu xử lý ngay)

### C1. Ngưỡng Bộ Lọc Trong Code Lệch Hoàn Toàn So Với Tài Liệu

> [!CAUTION]
> Đây là phát hiện nghiêm trọng nhất. Ngưỡng strict filter trong code đã được điều chỉnh nhiều lần nhưng **KHÔNG có tài liệu nào được cập nhật** theo, tạo ra rủi ro lớn về khả năng bảo trì và hiểu nhầm khi người dùng đọc tài liệu.

#### Bảng đối chiếu Code vs. Tài liệu

| Tham số | Code thực tế ([scanner.py:440-442](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/scanner.py#L440-L442)) | Tất cả tài liệu ghi chép | Mức lệch |
|:---|:---:|:---:|:---:|
| **F1 RS Percentile** | `[25, 45]` | `[40, 60]` | 🔴 Lệch hoàn toàn |
| **F1 Active Buy** | `[42%, 55%]` | `[45%, 52%]` | 🔴 Lệch biên rộng |
| **F2 RS Percentile** | `> 45` | `> 65` | 🔴 Lệch 20 điểm |
| **F2 Active Buy** | `[42%, 55%]` | `[45%, 52%]` | 🔴 Lệch biên rộng |
| **F3 Active Buy** | `> 50%` | `> 55%` | 🟡 Lệch 5% (đã ghi nhận ở Phase 2.3) |

**Nguyên nhân gốc:** Người dùng đã yêu cầu điều chỉnh ngưỡng RS và Active Buy qua nhiều phiên tương tác (yêu cầu số 2, 3, 9 trong compaction summary: "*đề xuất điều chỉnh mức % Mua chủ động*", "*hiệu chỉnh lại mục tiêu RS Trung bình*"). Code được cập nhật trực tiếp nhưng tài liệu session_records không được đồng bộ hóa.

**Các tài liệu bị ảnh hưởng (tất cả đều hiển thị ngưỡng cũ):**
- [walkthrough.md:21-23](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/session_records/walkthrough.md#L21-L23)
- [scanner_walkthrough.md:54-56](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/session_records/scanner_walkthrough.md#L54-L56)
- [implementation_plan.md:452-454](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/session_records/implementation_plan.md#L452-L454) (Phase 2.2)
- [data_contract.md](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/session_records/data_contract.md) (không đề cập ngưỡng nhưng mô tả rs_avg chưa đúng)
- [agent_activity_log.md:98, 111](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/session_records/agent_activity_log.md#L98)
- [audit_report.md:27-28, 47-48, 51](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/session_records/audit_report.md#L27-L28)

---

### C2. API Keys Thật Lộ Trong Code

> [!CAUTION]
> Tệp [config.py:8-10](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/config.py#L8-L10) chứa **API keys thực tế** của Telegram Bot, Chat ID và Gemini API Key dưới dạng giá trị mặc định (fallback) của `os.environ.get()`. Nếu thư mục `stock_hunt` được commit lên Git public repository, các keys này sẽ bị lộ.

```python
# config.py:8-10 — Keys thật đang nằm trong plaintext
TELEGRAM_BOT_TOKEN = os.environ.get("STOCKHUNT_TELEGRAM_BOT_TOKEN", "8858104222:AAHl...")
TELEGRAM_CHAT_ID = os.environ.get("STOCKHUNT_TELEGRAM_CHAT_ID", "5942808899")
GEMINI_API_KEY = os.environ.get("STOCKHUNT_GEMINI_API_KEY", "AIzaSyDq...")
```

**Khuyến nghị:** Thay fallback bằng placeholder rỗng `""` hoặc `"YOUR_KEY_HERE"` và tạo file `.env` riêng (đã được `.gitignore`).

---

### C3. Mâu Thuẫn Nội Bộ Trong Cùng 1 Tệp

Tệp [walkthrough.md](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/session_records/walkthrough.md) tự mâu thuẫn:
- **Dòng 21** (mô tả bộ lọc): Active Buy `[45%, 52%]`
- **Dòng 125** (bảng audit): Active Buy `(42-55%)`

Đây là dấu hiệu của việc cập nhật bảng audit mà quên cập nhật phần mô tả bộ lọc.

---

## 🟡 PHÁT HIỆN MỨC WARNING (Nên xử lý sớm)

### W1. Dead Code — Hàm `map_scorecard_to_vietnamese()` (81 dòng)

[scanner.py:210-280](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/scanner.py#L210-L280) — Hàm `map_scorecard_to_vietnamese()` dài 71 dòng **không được gọi từ bất kỳ module nào**. Hàm `_to_native()` tại dòng 200-208 cũng chỉ được dùng bên trong hàm chết này.

- Theo Implementation Plan Fix #3a, hàm này được giữ lại để "telegram_bot.py gọi khi cần format hiển thị"
- Thực tế: `telegram_bot.py` có logic format riêng inline, **không import hàm này**

**Khuyến nghị:** Xóa bỏ hoặc chuyển sang file riêng `utils.py` nếu dự kiến dùng trong tương lai.

### W2. Trùng lặp Code — Hàm `_to_native()` 

Hàm `_to_native()` tồn tại ở **2 nơi**:
- [scanner.py:200-208](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/scanner.py#L200-L208) — Phiên bản đơn giản (dead code)
- [ai_analyzer.py:42-59](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/ai_analyzer.py#L42-L59) — Phiên bản đầy đủ hơn (đệ quy, xử lý dict/list/set)

**Khuyến nghị:** Tách ra `stock_hunt/utils.py` và import từ một nguồn duy nhất.

### W3. Hardcoded Path Không Cần Thiết

[scanner.py:21-23](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/scanner.py#L21-L23):
```python
hardcoded_path = r"d:\Nghiên cứu AI\vnstock-agent-guide"
```
Dòng 15-18 đã có logic dynamic path resolution. Hardcoded path này là dư thừa và phá tính di động (portability).

### W4. Batch File Thiếu Hỗ Trợ `--now`

[run_hunt_bot.bat:12](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/run_hunt_bot.bat#L12) chỉ gọi `python -m stock_hunt.main` mà **không truyền `%*`** (tham số dòng lệnh). Tài liệu [walkthrough.md:96](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/session_records/walkthrough.md#L96) ghi nhận `run_hunt_bot.bat --now` hoạt động, nhưng thực tế tham số `--now` sẽ bị **bỏ qua**.

**Fix đề xuất:** Sửa dòng 12 thành `python -m stock_hunt.main %*`

### W5. Batch File Hardcoded User Path

[run_hunt_bot.bat:6](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/run_hunt_bot.bat#L6):
```batch
call "C:\Users\Langbatkyho\.venv\Scripts\activate.bat"
```
Nên thay bằng `call "%USERPROFILE%\.venv\Scripts\activate.bat"` để tăng tính di động.

### W6. Tài Liệu Bằng Tiếng Anh Không Nhất Quán

2 tệp tài liệu viết hoàn toàn bằng tiếng Anh trong khi toàn bộ dự án và yêu cầu người dùng là tiếng Việt:
- [scanner_walkthrough.md](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/session_records/scanner_walkthrough.md) — 89 dòng tiếng Anh
- [ai_walkthrough.md](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/session_records/ai_walkthrough.md) — 101 dòng tiếng Anh

### W7. Phase 2.3 Không Được Phản Ánh Trong Nhiều Tài Liệu

| Tài liệu | Phase 2.3 |
|:---|:---:|
| implementation_plan.md | ✅ Có |
| task.md | ✅ Có |
| agent_activity_log.md | ✅ Có |
| audit_report.md | ✅ Có |
| walkthrough.md | ❌ Thiếu |
| scanner_walkthrough.md | ❌ Thiếu |
| integration_report.md | ❌ Thiếu |
| data_contract.md | ❌ Thiếu |
| user_prompts.md | ❌ Thiếu (prompts 19+ không được ghi) |

### W8. Biến Config Không Được Sử Dụng

- [config.py:18](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/config.py#L18): `DATA_SOURCE = "KBS"` — không được tham chiếu bởi scanner.py
- [config.py:24-26](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/config.py#L24-L26): `FILTER_1`, `FILTER_2`, `FILTER_3` — đã được main.py sử dụng ✅, nhưng `FILTER_NAMES` (nếu có) không tồn tại

### W9. Thiếu Xử Lý Timezone Cho Schedule

[main.py:129](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/main.py#L129): Thư viện `schedule` sử dụng đồng hồ hệ thống. Config ghi `SCHEDULE_TIMES` là giờ GMT+7 nhưng không có cơ chế ép timezone. Nếu hệ thống chạy trên máy chủ ở timezone khác (VD: UTC trên cloud), bot sẽ quét sai giờ.

### W10. Nhập Nhằng Đơn Vị Giá Cổ Phiếu

[telegram_bot.py:54-57](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/telegram_bot.py#L54-L57) và [scanner.py:144-146](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/scanner.py#L144-L146): Cả hai nơi đều có logic phát hiện đơn vị giá (`is_in_thousands = last_close < 1000`) dựa trên ngưỡng cố định. Nếu nguồn API thay đổi format trả về (VND gốc vs. nghìn đồng), logic này sẽ tính sai giá trị giao dịch và hiển thị sai giá trên Telegram.

---

## 🟢 PHÁT HIỆN MỨC GHI NHẬN (Đề xuất cải tiến)

### E1. Thiếu Graceful Shutdown

[main.py:132-138](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/main.py#L132-L138) chỉ bắt `KeyboardInterrupt`. Nên bổ sung xử lý `SIGTERM` cho triển khai production (Windows Service / Docker).

### E2. Dữ Liệu VC3 Khác Nhau Giữa Các Tài Liệu

Các tài liệu ghi nhận dữ liệu VC3 từ các ngày chạy khác nhau mà không ghi rõ timestamp:
- walkthrough.md: RSI = 40.37, RS = 28.0, Active Buy = 48.53%
- audit_report.md: RSI = 43.85, RS = 30.0, Active Buy = 48.13%

**Khuyến nghị:** Mỗi bảng audit nên ghi rõ ngày lấy dữ liệu.

### E3. Thiếu Unit Tests Cho Logic Bộ Lọc

[test_scan.py](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/test_scan.py) chỉ kiểm tra smoke test (nạp danh sách mã). Không có unit test nào kiểm tra:
- Logic `check_pre_filters()` với dữ liệu mock
- Logic strict verification tại dòng 440-442
- Cơ chế chunking tin nhắn Telegram

### E4. Tái Sử Dụng Dữ Liệu EOD 1Y

[scanner.py:398, 448](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/scanner.py#L398): `fetch_ohlcv(symbol, length='1Y')` được gọi ở Vòng 1, sau đó `fetch_ohlcv_long(symbol)` (5Y) được gọi lại ở Vòng 3.5 cho mã đã match. Dữ liệu 1Y là tập con của 5Y — có thể tối ưu bằng cách gọi 5Y ngay từ đầu cho các mã qua Vòng 1, tiết kiệm 1 API call/mã.

### E5. Data Contract Chưa Cập Nhật Mô Tả `rs_avg`

[data_contract.md:36](file:///d:/Nghiên cứu AI/vnstock-agent-guide/stock_hunt/session_records/data_contract.md#L36) mô tả `rs_avg` là "*Chỉ số RS trung bình trọng số*" nhưng thực tế giá trị này đã bị **ghi đè bằng `stock_strength` Percentile Rank từ VCI Screener** (Phase 2.1). Mô tả nên phản ánh đúng nguồn gốc dữ liệu.

---

## 📊 Tuân Thủ Implementation Plan — Đánh Giá Chi Tiết

### Phase 1 (Foundation) — ✅ 100% Tuân Thủ
Tất cả 8 tệp nguồn được tạo đúng theo kế hoạch. Kiến trúc 5 module hoạt động như thiết kế.

### Phase 2 (Audit Hotfix) — ✅ 100% Tuân Thủ
Tất cả 8 Fix (#1-#8) được thực hiện chính xác bởi các subagent phân công.

### Phase 2.1 (Performance Tuning) — ✅ 100% Tuân Thủ
Layer 0 Pre-filter, VN-Index Benchmark, RS Percentile override — tất cả hoạt động đúng.

### Phase 2.2 (Strict Verification) — ⚠️ 80% Tuân Thủ
Phân tầng RS relaxed → strict hoạt động đúng. Tuy nhiên, **ngưỡng cuối cùng trong code đã vượt ra ngoài spec ban đầu** do điều chỉnh liên tiếp ở Phase 2.3.

### Phase 2.3 (Cross-Verification) — ⚠️ 70% Tuân Thủ
Kết quả kiểm chứng chéo chính xác. Nhưng các điều chỉnh ngưỡng (Active Buy từ `[45,52]` → `[42,55]`, RS từ `[40,60]` → `[25,45]`) được thực hiện trực tiếp trên code **mà không cập nhật Implementation Plan** tương ứng, vi phạm quy trình "*nếu phát hiện issues cần thay đổi đáng kể, cập nhật implementation_plan.md và xin review lại*".

---

## 🧑‍💻 Đánh Giá Hiệu Năng Subagent

Hệ thống đã triển khai tổng cộng **12 lượt subagent** qua 5 giai đoạn:

| Giai đoạn | Số Subagent | Chất lượng code output | Ghi chú |
|:---|:---:|:---:|:---|
| Phase 1 | 3 | 🟡 Trung bình | Tạo ra 3 lỗi Critical do thiếu Data Contract |
| Phase 2 | 3 | 🟢 Tốt | Sửa đúng theo spec, không tạo thêm lỗi |
| Phase 2.1 | 5 | 🟢 Xuất sắc | Layer 0 Pre-filter giảm 25x thời gian quét |
| Phase 2.2 | 1 | 🟢 Tốt | Phân tầng RS chính xác |
| Phase 2.3 | 0 | N/A | Main Agent thực hiện trực tiếp |

> [!TIP]
> **Bài học rút ra:** Phase 1 chứng minh rằng khi 3 subagent code song song mà không có Data Contract chung, tỷ lệ lỗi tích hợp rất cao. Từ Phase 2 trở đi, việc thiết lập Data Contract trước khi phân chia task đã loại bỏ hoàn toàn lỗi tương tự.

---

## 🎯 Kế Hoạch Khắc Phục Được Đề Xuất (Theo Thứ Tự Ưu Tiên)

### Ưu tiên 1 — Bảo mật (Ngay lập tức)
- [ ] **C2:** Thay API keys thật trong `config.py` bằng placeholder. Tạo `.env` file.
- [ ] Thêm `stock_hunt/config.py` hoặc `.env` vào `.gitignore` nếu chưa có.

### Ưu tiên 2 — Đồng bộ Tài liệu (Trong ngày)
- [ ] **C1:** Cập nhật ngưỡng bộ lọc trong 6 tệp tài liệu cho khớp với code thực tế.
- [ ] **C3:** Sửa mâu thuẫn nội bộ trong walkthrough.md (dòng 21 vs dòng 125).
- [ ] **W6:** Dịch `scanner_walkthrough.md` và `ai_walkthrough.md` sang tiếng Việt.
- [ ] **W7:** Bổ sung Phase 2.3 vào 5 tài liệu còn thiếu.
- [ ] **E5:** Cập nhật mô tả `rs_avg` trong data_contract.md.

### Ưu tiên 3 — Dọn dẹp Code (Trong tuần)
- [ ] **W1:** Xóa hoặc chuyển `map_scorecard_to_vietnamese()` ra khỏi scanner.py.
- [ ] **W2:** Gom `_to_native()` vào `stock_hunt/utils.py`.
- [ ] **W3:** Xóa hardcoded path fallback trong scanner.py.
- [ ] **W4:** Sửa `run_hunt_bot.bat` dòng 12 thành `python -m stock_hunt.main %*`.
- [ ] **W5:** Thay hardcoded user path bằng `%USERPROFILE%`.

### Ưu tiên 4 — Cải tiến Kỹ thuật (Khi có thời gian)
- [ ] **E1:** Thêm signal handler cho graceful shutdown.
- [ ] **E3:** Viết unit tests cho logic bộ lọc với dữ liệu mock.
- [ ] **E4:** Tối ưu hóa fetch EOD (gọi 5Y ngay từ đầu cho mã qua pre-filter).
- [ ] **W8:** Xóa biến config không sử dụng hoặc tích hợp vào scanner.

---

## 📝 Kết Luận

Hệ thống Stock Hunt Bot đã được xây dựng với kiến trúc vững chắc, hiệu năng xuất sắc (quét toàn thị trường < 50 giây), và quy trình tích hợp AI-Telegram hoàn chỉnh. Tuy nhiên, quá trình tinh chỉnh ngưỡng liên tục qua nhiều phiên đã tạo ra **nợ kỹ thuật về tài liệu** — đây là rủi ro lớn nhất hiện tại vì bất kỳ ai đọc tài liệu sẽ hiểu sai hoàn toàn cách hệ thống đang hoạt động.

**Khuyến nghị quan trọng nhất:** Ưu tiên tuyệt đối việc **đồng bộ tài liệu với code thực tế** trước khi thực hiện bất kỳ tính năng mới nào, và thiết lập quy ước rằng mỗi khi thay đổi ngưỡng bộ lọc, phải cập nhật tài liệu ngay trong cùng phiên làm việc.

---

*Báo cáo được tổng hợp từ kết quả audit của 2 subagent chuyên biệt và xác minh thủ công bởi Main Agent.*
