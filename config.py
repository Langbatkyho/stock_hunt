import os
import sys

# Thêm thư mục gốc vào path để có thể import từ bot_app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load .env file manually if it exists
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().strip('"').strip("'")
                    os.environ[key] = val

load_env()

# Cấu hình API Keys (Đọc từ biến môi trường hoặc file .env)
TELEGRAM_BOT_TOKEN = os.environ.get("STOCKHUNT_TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("STOCKHUNT_TELEGRAM_CHAT_ID", "")
GEMINI_API_KEY = os.environ.get("STOCKHUNT_GEMINI_API_KEY", "")

# Hỗ trợ nhiều API key cho Rotation, phân cách bằng dấu phẩy
raw_keys = os.environ.get("STOCKHUNT_GEMINI_API_KEYS", "")
if raw_keys:
    GEMINI_API_KEYS = [k.strip() for k in raw_keys.split(',') if k.strip()]
elif GEMINI_API_KEY:
    GEMINI_API_KEYS = [GEMINI_API_KEY]
else:
    GEMINI_API_KEYS = []


GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_FALLBACK_MODEL = "gemini-2.5-flash"

# Thời gian quét cố định (giờ Việt Nam GMT+7)
SCHEDULE_TIMES = ["10:15", "14:05"]

# Ưu tiên các sàn giao dịch (đã loại bỏ UPCOM theo yêu cầu)
EXCHANGES = ["HOSE", "HNX"]

# Filter Names
FILTER_1 = "Tích lũy phá nền"
FILTER_2 = "Hổ gặp nạn"
FILTER_3 = "Vua sập bẫy"
