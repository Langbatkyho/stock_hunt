import os
import sys
import time
import logging
import numpy as np
import instructor
from google import genai
from pydantic import BaseModel, Field
from typing import Literal

# Thiết lập logger cho module
logger = logging.getLogger(__name__)

# Đảm bảo đường dẫn import hoạt động tốt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import config một cách an toàn và linh hoạt
try:
    from stock_hunt import config
except ImportError:
    try:
        from . import config
    except ImportError:
        import config

from stock_hunt.utils import _to_native

# Khai báo Data Contract bằng Pydantic cho AI đầu ra
class AIAnalysis(BaseModel):
    strength_comparison: str = Field(description="Đánh giá sức mạnh kỹ thuật của cổ phiếu (dựa trên RS, tỷ lệ mua chủ động, hoặc biến động giá so với thị trường/các chỉ số hỗ trợ).")
    short_term_trend: str = Field(description="Dự báo xu hướng giá ngắn hạn (Tăng, Giảm, hay Tích lũy) dựa trên các đường MA, RSI, MACD và giao dịch khối ngoại.")
    recommendation: Literal["MUA", "BÁN", "QUAN SÁT"] = Field(description="Khuyến nghị hành động rõ ràng: MUA, BÁN hoặc QUAN SÁT.")
    quantitative_reason: str = Field(description="Một lý do định lượng quan trọng nhất rút ra trực tiếp từ các dữ liệu kỹ thuật.")

# Quản lý danh sách API Keys để xoay vòng
api_keys_pool = []
current_key_idx = 0
client = None

def init_client(api_key: str):
    """Khởi tạo Gemini Client với Instructor patch"""
    try:
        raw_client = genai.Client(api_key=api_key)
        return instructor.from_genai(raw_client, mode=instructor.Mode.TOOLS)
    except Exception as e:
        logger.error(f"Lỗi khởi tạo Gemini Client: {e}")
        return None

# Nạp danh sách API keys từ config hoặc biến môi trường
if hasattr(config, 'GEMINI_API_KEYS') and config.GEMINI_API_KEYS:
    api_keys_pool = config.GEMINI_API_KEYS
elif hasattr(config, 'GEMINI_API_KEY') and config.GEMINI_API_KEY and "YOUR_" not in config.GEMINI_API_KEY:
    api_keys_pool = [config.GEMINI_API_KEY]
else:
    k = os.environ.get("STOCKHUNT_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""
    if k:
        api_keys_pool = [k]

if api_keys_pool:
    client = init_client(api_keys_pool[current_key_idx])
    logger.info(f"Khởi tạo thành công Gemini Client. Số lượng API key khả dụng: {len(api_keys_pool)}")
else:
    logger.warning("Cảnh báo: Chưa tìm thấy GEMINI_API_KEY(S) hợp lệ trong config hoặc biến môi trường!")

def rotate_api_key() -> bool:
    """Xoay vòng sang API Key tiếp theo trong pool (nếu có)."""
    global current_key_idx, client
    if not api_keys_pool or len(api_keys_pool) <= 1:
        return False
        
    old_idx = current_key_idx
    current_key_idx = (current_key_idx + 1) % len(api_keys_pool)
    
    logger.info(f"🔄 Đang xoay vòng API Key... Chuyển từ key index {old_idx} sang {current_key_idx}")
    client = init_client(api_keys_pool[current_key_idx])
    return True


def generate_prompt(symbol, scorecard, filter_name):
    """
    Tạo prompt động bằng tiếng Việt cho Gemini, tập trung hoàn toàn vào dữ liệu kỹ thuật
    của mã cổ phiếu mục tiêu tương ứng với chiến lược đảo chiều/bứt phá.
    """
    # Giải thích ý nghĩa của bộ lọc tương ứng để định hướng AI phân tích đúng trọng tâm kỹ thuật
    filter_context = ""
    if filter_name == "Tích lũy phá nền":
        filter_context = "Cổ phiếu tích lũy chặt chẽ trong nền giá phẳng sau đó bùng nổ (breakout) vượt kháng cự với khối lượng lớn, đánh dấu sự bắt đầu của xu hướng tăng mới."
    elif filter_name == "Hổ gặp nạn":
        filter_context = "Cổ phiếu trong xu hướng tăng mạnh nhưng gặp nhịp điều chỉnh ngắn hạn (hoặc sập bẫy giảm giá) tạo cơ hội mua giá tốt tại các vùng hỗ trợ quan trọng (reversal)."
    elif filter_name == "Vua sập bẫy":
        filter_context = "Mô hình đảo chiều tạo bẫy giảm giá (Bear Trap) dụ phe bán bán ra ở hỗ trợ cứng, sau đó nhanh chóng kéo ngược tăng mạnh và xác nhận dòng tiền lớn gia nhập (breakout/reversal)."
    else:
        filter_context = f"Bộ lọc phát hiện mẫu hình kỹ thuật đột biến: {filter_name}."

    # Bản đồ hiển thị thông tin rõ ràng cho AI
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

    # Lọc động: Chỉ đưa vào prompt các chỉ số thực tế đang khả dụng trong scorecard
    available_data = []
    for k, v in scorecard.items():
        if k in INDICATOR_LABELS and v is not None:
            native_val = _to_native(v)
            if isinstance(native_val, float):
                formatted_val = f"{native_val:.2f}"
            elif isinstance(native_val, (int, str)):
                formatted_val = str(native_val)
            else:
                formatted_val = str(native_val)
            available_data.append(f"- {INDICATOR_LABELS[k]}: {formatted_val}")

    # Xử lý chuỗi lịch sử RSI(14) 30 phiên để hỗ trợ phân tích xu hướng động (RSI Range Shift)
    rsi_history_str = ""
    if 'rsi_14_history' in scorecard and scorecard['rsi_14_history']:
        history = scorecard['rsi_14_history']
        valid_history = [float(x) for x in history if x is not None and not (isinstance(x, float) and np.isnan(x))]
        if valid_history:
            rsi_min = float(np.min(valid_history))
            rsi_max = float(np.max(valid_history))
            rsi_std = float(np.std(valid_history))
            rsi_curr = float(valid_history[-1])
            
            # Tạo chuỗi hiển thị dạng: [T-29: 45.10, T-28: 46.20, ..., T-0: 50.12]
            n = len(valid_history)
            time_series_items = []
            for i, val in enumerate(valid_history):
                t_label = f"T-{n - 1 - i}"
                time_series_items.append(f"{t_label}: {val:.2f}")
            ts_formatted = ", ".join(time_series_items)
            
            rsi_history_str = f"""- Chuỗi lịch sử RSI(14) {n} phiên gần nhất (từ cũ đến mới, T-0 là phiên hiện tại):
  [{ts_formatted}]
- Thống kê RSI(14) {n} phiên:
  + RSI Cao nhất (Max): {rsi_max:.2f}
  + RSI Thấp nhất (Min): {rsi_min:.2f}
  + Độ lệch chuẩn RSI (Std Dev): {rsi_std:.2f} (Biến động RSI thấp thể hiện tích lũy phẳng, biến động lớn thể hiện xu hướng mạnh hoặc giằng co)
  + RSI Hiện tại (T-0): {rsi_curr:.2f}"""

    indicators_str = "\n".join(available_data)
    if rsi_history_str:
        indicators_str += "\n" + rsi_history_str

    prompt = f"""Bạn là một chuyên gia phân tích kỹ thuật chứng khoán Việt Nam cao cấp.
Hãy đưa ra nhận định ngắn gọn về cổ phiếu mục tiêu {symbol} dựa trên các tiêu chí kỹ thuật cụ thể dưới đây.

THÔNG TIN BỐI CẢNH BỘ LỌC:
- Cổ phiếu {symbol} đã được hệ thống phát hiện qua bộ lọc: "{filter_name}".
- Ý nghĩa bộ lọc kỹ thuật này: {filter_context}

DỮ LIỆU ĐẦU VÀO ĐỊNH LƯỢNG CHO {symbol}:
{indicators_str}

YÊU CẦU PHÂN TÍCH:
Hãy viết một bản phân tích ngắn gọn, cô đọng, sử dụng ngôn từ chuyên nghiệp, tập trung hoàn toàn vào dữ liệu định lượng kỹ thuật và dòng tiền ở trên.
Hãy đặc biệt chú ý phân tích xu hướng động của RSI(14) qua chuỗi lịch sử 30 phiên được cung cấp ở trên (áp dụng lý thuyết RSI Range Shift dải sinh thái 40/60 để xác định xem cổ phiếu đang dịch chuyển xu hướng, tích lũy tạo nền phẳng vững chắc hay bứt phá mạnh mẽ).
"""
    return prompt


def format_analysis_to_markdown(analysis: AIAnalysis) -> str:
    """Format kết quả phân tích Pydantic thành chuỗi văn bản sử dụng Markdown bold (**)."""
    return (
        f"**1. So sánh Sức mạnh:** {analysis.strength_comparison.strip()}\n"
        f"**2. Xu hướng Ngắn hạn:** {analysis.short_term_trend.strip()}\n"
        f"**3. Khuyến nghị:** **{analysis.recommendation.strip()}** ({analysis.quantitative_reason.strip()})"
    )


def analyze_candidate(symbol, scorecard, filter_name):
    """
    Phân tích cổ phiếu ứng viên tìm được từ scanner bằng Gemini thông qua Instructor.
    Trả về chuỗi văn bản đã định dạng Markdown.
    Có tích hợp vòng lặp retry 3 lần thông minh để chống lỗi nghẽn hoặc vượt hạn mức (Rate Limit 429).
    """
    if client is None:
        logger.error("Gemini client chưa được khởi tạo. Không thể thực hiện phân tích AI.")
        return "⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEY hoặc khởi tạo Client thất bại."

    # 1. Chuyển đổi dữ liệu về dạng nguyên bản của Python để tránh lỗi truyền/tuần tự hóa
    native_scorecard = _to_native(scorecard)

    # 2. Xây dựng prompt động bằng tiếng Việt
    prompt = generate_prompt(symbol, native_scorecard, filter_name)

    # 3. Lấy model name từ config (bao gồm cả model dự phòng)
    current_model = getattr(config, 'GEMINI_MODEL', 'gemini-3.5-flash')
    fallback_model = getattr(config, 'GEMINI_FALLBACK_MODEL', 'gemini-2.5-flash')
    logger.info(f"Đang gửi prompt phân tích AI cho mã {symbol} qua bộ lọc '{filter_name}' bằng model {current_model}...")

    max_retries = 3
    attempt = 1
    rotations_tried = 0
    max_rotations = len(api_keys_pool)

    while attempt <= max_retries:
        try:
            # Gọi API qua Instructor
            response = client.chat.completions.create(
                model=current_model,
                messages=[{"role": "user", "content": prompt}],
                response_model=AIAnalysis,
                max_retries=3, # Số lần tự sửa lỗi cú pháp bên trong Instructor
            )

            if response:
                logger.info(f"Giao tiếp Gemini thành công cho {symbol} ở lần thử {attempt}.")
                # Chống spam nhẹ (sleep 2 giây) theo quy định resilient pipeline
                time.sleep(2)
                return format_analysis_to_markdown(response)
            else:
                logger.warning(f"Gemini trả về kết quả rỗng cho {symbol} (Lần thử {attempt}/{max_retries})")
                if attempt == max_retries:
                    return "⚠️ Lỗi phân tích AI: Nhận phản hồi rỗng từ Gemini API."
                attempt += 1
                time.sleep(2)

        except Exception as e:
            err_str = str(e)
            logger.warning(f"Lỗi gọi Gemini API (Lần thử {attempt}/{max_retries}) cho mã {symbol}: {e}")

            # Kiểm tra lỗi Rate Limit 429 / ResourceExhausted cụ thể
            is_rate_limit = (
                "429" in err_str or 
                "ResourceExhausted" in err_str or 
                "Resource exhausted" in err_str or 
                "quota" in err_str.lower()
            )

            if is_rate_limit:
                logger.warning(f"Bị giới hạn tần suất API (429/ResourceExhausted) hoặc hết Quota.")
                # Thử xoay vòng API key
                if rotations_tried < max_rotations:
                    rotated = rotate_api_key()
                    if rotated:
                        rotations_tried += 1
                        logger.info(f"Xoay vòng key thành công (Lần xoay {rotations_tried}/{max_rotations}), thử lại ngay lập tức...")
                        time.sleep(2)  # Nghỉ nhẹ trước khi thử lại với key mới
                        continue  # Thử lại ngay lập tức với key mới, giữ nguyên attempt
                
                # Nếu không có key dự phòng hoặc đã thử xoay hết tất cả các key
                sleep_time = 65
                logger.warning(f"Đã thử tất cả các API key hoặc không có key dự phòng. Chờ {sleep_time} giây trước khi thử lại...")
                time.sleep(sleep_time)
                attempt += 1
            else:
                is_server_error = "503" in err_str or "500" in err_str or "unavailable" in err_str.lower()
                
                # Nếu đã thử tối đa số lần cho model hiện tại
                if attempt == max_retries:
                    if current_model != fallback_model:
                        logger.warning(f"Model {current_model} thất bại {max_retries} lần. Chuyển sang model dự phòng {fallback_model}...")
                        current_model = fallback_model
                        attempt = 1 # Thử lại từ đầu với model dự phòng
                        continue
                    else:
                        logger.error(f"Đã thử {max_retries} lần gọi Gemini API cho mã {symbol} nhưng đều thất bại.")
                        return f"⚠️ Lỗi phân tích AI: {err_str}"
                
                # Tính năng thông minh: Nếu là lỗi quá tải server (503) và đã thử 1 lần thất bại, chuyển model sớm
                if is_server_error and attempt == 2 and current_model != fallback_model:
                    logger.warning(f"Model {current_model} đang quá tải (503). Chuyển sớm sang model dự phòng {fallback_model}...")
                    current_model = fallback_model
                    attempt = 1
                    continue
                
                sleep_time = 10 * attempt if is_server_error else 2
                logger.warning(f"Gặp lỗi hệ thống từ phía Google (503/500 hoặc khác). Chờ {sleep_time} giây trước khi thử lại...")
                attempt += 1
                time.sleep(sleep_time)

    return f"⚠️ Lỗi phân tích AI: Đã thử tối đa {max_retries} lần nhưng không thành công."
