import os
import sys
import time
import logging
import numpy as np
import pandas as pd
from google import genai

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

# Khởi tạo Gemini Client dùng SDK mới (google-genai)
client = None
try:
    if hasattr(config, 'GEMINI_API_KEY') and config.GEMINI_API_KEY and "YOUR_" not in config.GEMINI_API_KEY:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        logger.info("Khởi tạo thành công Gemini Client từ config.GEMINI_API_KEY.")
    else:
        # Thử lấy từ biến môi trường làm dự phòng
        env_key = os.environ.get("STOCKHUNT_GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if env_key:
            client = genai.Client(api_key=env_key)
            logger.info("Khởi tạo thành công Gemini Client từ biến môi trường.")
        else:
            logger.warning("Cảnh báo: Chưa tìm thấy GEMINI_API_KEY hợp lệ trong config hoặc biến môi trường!")
except Exception as e:
    logger.error(f"Lỗi khi khởi tạo Gemini Client: {e}")


from stock_hunt.utils import _to_native



def generate_prompt(symbol, scorecard, filter_name):
    """
    Tạo prompt động bằng tiếng Việt cho Gemini 3.5 Flash, tập trung hoàn toàn vào dữ liệu kỹ thuật
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

    indicators_str = "\n".join(available_data)

    prompt = f"""Bạn là một chuyên gia phân tích kỹ thuật chứng khoán Việt Nam cao cấp.
Hãy đưa ra nhận định ngắn gọn về cổ phiếu mục tiêu {symbol} dựa trên các tiêu chí kỹ thuật cụ thể.

THÔNG TIN BỐI CẢNH BỘ LỌC:
- Cổ phiếu {symbol} đã được hệ thống phát hiện qua bộ lọc: "{filter_name}".
- Ý nghĩa bộ lọc kỹ thuật này: {filter_context}

DỮ LIỆU ĐẦU VÀO ĐỊNH LƯỢNG CHO {symbol}:
{indicators_str}

YÊU CẦU PHÂN TÍCH:
Hãy viết một bản phân tích ngắn gọn, cô đọng (dưới 150-200 từ), sử dụng ngôn từ chuyên nghiệp, tập trung hoàn toàn vào dữ liệu định lượng kỹ thuật và dòng tiền ở trên (không dùng các câu cảnh báo chung chung hay sáo rỗng).

Báo cáo phân tích phải tuân thủ CHÍNH XÁC cấu trúc 3 phần sau bằng tiếng Việt:

1. So sánh Sức mạnh: Đánh giá sức mạnh kỹ thuật của {symbol} (dựa trên RS 3D/1M/average, tỷ lệ mua chủ động, hoặc sự biến động giá so với thị trường/các chỉ số hỗ trợ).
2. Xu hướng Ngắn hạn: Dự báo xu hướng giá ngắn hạn (Tăng, Giảm, hay Tích lũy) dựa trên vị thế giá so với các đường MA10/MA20/MA50, chỉ báo RSI, trạng thái MACD và giao dịch khối ngoại.
3. Khuyến nghị: Đưa ra khuyến nghị rõ ràng (MUA, BÁN hoặc QUAN SÁT) kèm theo một lý do định lượng quan trọng nhất rút ra trực tiếp từ các dữ liệu kỹ thuật ở trên.
"""
    return prompt


def analyze_candidate(symbol, scorecard, filter_name):
    """
    Phân tích cổ phiếu ứng viên tìm được từ scanner bằng Gemini 3.5 Flash.
    Hàm này có tích hợp vòng lặp retry 3 lần thông minh để chống lỗi nghẽn hoặc vượt hạn mức (Rate Limit 429).
    """
    if client is None:
        logger.error("Gemini client chưa được khởi tạo. Không thể thực hiện phân tích AI.")
        return "⚠️ Lỗi: Chưa cấu hình GEMINI_API_KEY hoặc khởi tạo Client thất bại."

    # 1. Chuyển đổi dữ liệu về dạng nguyên bản của Python để tránh lỗi truyền/tuần tự hóa
    native_scorecard = _to_native(scorecard)

    # 2. Xây dựng prompt động bằng tiếng Việt
    prompt = generate_prompt(symbol, native_scorecard, filter_name)

    # 3. Lấy model name từ config
    model_name = getattr(config, 'GEMINI_MODEL', 'gemini-3.5-flash')
    logger.info(f"Đang gửi prompt phân tích AI cho mã {symbol} qua bộ lọc '{filter_name}'...")

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            # Gọi API
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            if response and response.text:
                logger.info(f"Giao tiếp Gemini thành công cho {symbol} ở lần thử {attempt}.")
                return response.text
            else:
                logger.warning(f"Gemini trả về kết quả rỗng cho {symbol} (Lần thử {attempt}/{max_retries})")
                if attempt == max_retries:
                    return "⚠️ Lỗi phân tích AI: Nhận phản hồi rỗng từ Gemini API."
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
                sleep_time = 65
                logger.warning(f"Bị giới hạn tần suất API (429/ResourceExhausted). Chờ {sleep_time} giây trước khi thử lại...")
                time.sleep(sleep_time)
            else:
                # Lỗi thường gặp khác, nghỉ ngắn 2 giây trước khi thử lại
                if attempt == max_retries:
                    logger.error(f"Đã thử {max_retries} lần gọi Gemini API cho mã {symbol} nhưng đều thất bại.")
                    return f"⚠️ Lỗi phân tích AI: {err_str}"
                time.sleep(2)

    # Dự phòng cuối cùng
    return f"⚠️ Lỗi phân tích AI: Đã thử tối đa {max_retries} lần nhưng không thành công."
