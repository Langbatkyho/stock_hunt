# Stock Hunt Bot - Hướng dẫn sử dụng và Cấu trúc dự án

Stock Hunt là một hệ thống bot tự động quét thị trường chứng khoán Việt Nam, ứng dụng AI (Google Gemini) để phân tích kỹ thuật và gửi tín hiệu giao dịch trực tiếp qua Telegram.

## 🚀 Tính năng nổi bật
- **Quét kỹ thuật tự động:** Dựa trên các bộ lọc chuyên sâu (Tích lũy phá nền, Hổ gặp nạn, Vua sập bẫy).
- **Phân tích bằng AI:** Tự động xây dựng prompt và gọi Gemini API để lấy nhận định (MUA/BÁN/QUAN SÁT) dựa trên các chỉ báo như RSI Range Shift, MA, MACD.
- **Báo cáo Telegram:** Tổng hợp scorecard và lời khuyên định lượng bằng HTML gửi qua Telegram.
- **Enterprise-Grade Resiliency:** Chống Rate Limit (API Key Rotation), Tự động Fallback sang model nhẹ hơn khi quá tải (503 Service Unavailable), và Exponential Backoff an toàn.

## 📁 Cấu trúc thư mục

- `main.py`: Orchestrator điều phối lịch trình quét.
- `scanner.py`: Tải dữ liệu thị trường và lọc ra ứng viên tiềm năng (Layer 0).
- `ai_analyzer.py`: Nhận diện mẫu hình, giao tiếp với LLM qua Instructor/Pydantic.
- `telegram_bot.py`: Quản lý tin nhắn và phân mảnh nội dung an toàn.
- `config.py`: Tệp cấu hình tập trung (API Keys, Token, Filters).
- `docs/`: Tài liệu dự án.
- `session_records/`: Bản lưu trữ các quyết định hệ thống của Multi-Agent.

## ⚙️ Cài đặt & Sử dụng

1. **Yêu cầu:** Môi trường ảo Python (`~/.venv`).
2. **Cấu hình `.env`:**
   ```env
   STOCKHUNT_TELEGRAM_BOT_TOKEN="your-bot-token"
   STOCKHUNT_TELEGRAM_CHAT_ID="your-chat-id"
   # Hỗ trợ cấu hình nhiều API key dự phòng để chống Rate Limit:
   STOCKHUNT_GEMINI_API_KEYS="key1,key2,key3"
   ```
3. **Chạy thử nghiệm ngay lập tức:**
   ```bash
   python -m stock_hunt.main --now
   ```
4. **Chạy tự động (Scheduler):**
   ```bash
   python -m stock_hunt.main
   ```
