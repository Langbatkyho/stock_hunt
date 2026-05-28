import os
import sys
import time
import html
import re
import logging
import requests
from datetime import datetime

# Thêm thư mục gốc vào path để có thể import từ stock_hunt hoặc bot_app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import stock_hunt.config as config

logger = logging.getLogger("stock_hunt_telegram")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


def escape_ai_text(text):
    """
    Escape special characters for Telegram HTML but preserve Markdown bold.
    This prevents Telegram's HTML parser from throwing Bad Request errors.
    """
    if not text:
        return ""
    # Tránh việc ký tự <, >, & gây lỗi parse HTML
    escaped = html.escape(text)
    # Chuyển đổi Markdown bold (**text**) thành HTML bold (<b>text</b>)
    escaped = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', escaped)
    return escaped


def format_scorecard_table(candidates):
    """
    Tạo bảng monospaced thể hiện Scorecard các chỉ số chính cho các cổ phiếu thỏa mãn bộ lọc.
    Các cột bao gồm: Mã, Thị giá (k), %1D, %Mua CĐ, RSI, RS TB, khoảng cách MA20 (%).
    """
    table = "<b>📊 BẢNG ĐIỂM THEO DÕI:</b>\n"
    table += "<code>"
    table += f"{'Mã':<4} | {'Giá':<5} | {'1D%':<6} | {'Mua%':<4} | {'RSI':<3} | {'RS':<3} | {'MA20':<5}\n"
    table += "-" * 45 + "\n"
    
    for symbol, sc, _ in candidates:
        # Lấy các chỉ số từ scorecard một cách an toàn theo đúng Data Contract
        price = sc.get('current_price', 0)
        change_1d = sc.get('1D_pct', 0)
        active_buy = sc.get('active_buy_pct', 0)
        rsi = sc.get('rsi_14', 0)
        rs_avg = sc.get('rs_avg', 0)
        ma20_dist = sc.get('price_vs_ma20_pct', 0)
        
        # Format Thị giá (luôn hiển thị ở đơn vị nghìn đồng, e.g. 17100đ -> 17.1, 17.1 -> 17.1)
        from stock_hunt.utils import get_price_in_thousands
        price_k = get_price_in_thousands(price)
        price_str = f"{price_k:.1f}"
            
        change_str = f"{change_1d:+.1f}%" if isinstance(change_1d, (int, float)) else str(change_1d)
        active_str = f"{active_buy:.0f}%" if isinstance(active_buy, (int, float)) else str(active_buy)
        rsi_str = f"{rsi:.0f}" if isinstance(rsi, (int, float)) else str(rsi)
        rs_str = f"{rs_avg:.0f}" if isinstance(rs_avg, (int, float)) else str(rs_avg)
        ma20_str = f"{ma20_dist:+.1f}%" if isinstance(ma20_dist, (int, float)) else str(ma20_dist)
        
        table += f"{symbol:<4} | {price_str:<5} | {change_str:<6} | {active_str:<4} | {rsi_str:<3} | {rs_str:<3} | {ma20_str:<5}\n"
        
    table += "</code>"
    return table


def send_telegram_message(text):
    """
    Gửi tin nhắn HTML tới Telegram với cơ chế retry 3 lần và tự động phân chia tin nhắn
    nếu độ dài vượt quá giới hạn 4096 ký tự của Telegram.
    """
    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID

    if not token or token == "YOUR_NEW_TELEGRAM_BOT_TOKEN" or not chat_id or chat_id == "YOUR_TELEGRAM_CHAT_ID":
        logger.warning("Telegram Bot Token hoặc Chat ID chưa được cấu hình. Chỉ hiển thị ra console.")
        print("\n=== MÔ PHỎNG TELEGRAM MESSAGE ===")
        print(text)
        print("=================================\n")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Chia nhỏ tin nhắn nếu vượt quá 4000 ký tự (để an toàn so với giới hạn 4096 của Telegram)
    max_length = 4000
    chunks = []
    
    if len(text) <= max_length:
        chunks.append(text)
    else:
        logger.info(f"Độ dài tin nhắn ({len(text)}) vượt quá giới hạn. Đang thực hiện phân mảnh...")
        lines = text.split("\n")
        current_chunk = ""
        for line in lines:
            if len(line) > max_length:
                # Nếu một dòng đơn quá dài (hiếm gặp), cắt nhỏ dòng đó ra
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                for idx in range(0, len(line), max_length):
                    chunks.append(line[idx:idx+max_length])
            elif len(current_chunk) + len(line) + 1 > max_length:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

    success = True
    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            logger.info(f"Đang gửi phần {i+1}/{len(chunks)}")
        
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "HTML"
        }

        chunk_success = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                logger.info(f"Gửi phần tin nhắn {i+1} thành công.")
                chunk_success = True
                break
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as ce:
                logger.warning(f"Lỗi mạng Telegram (lần thử {attempt}/{MAX_RETRIES}): {ce}")
            except Exception as e:
                # Fallback khẩn cấp nếu bị lỗi Parse HTML (ví dụ do tag HTML bị cắt ngang hoặc sai cấu trúc)
                if "can't parse entities" in str(e) or "bad request" in str(e).lower():
                    logger.error(f"Lỗi parse HTML Telegram. Đang gửi lại dạng plain text không định dạng... Lỗi: {e}")
                    clean_text = chunk.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", "").replace("<i>", "").replace("</i>", "").replace("<pre>", "").replace("</pre>", "")
                    payload["text"] = clean_text
                    payload.pop("parse_mode", None)
                    try:
                        response = requests.post(url, json=payload, timeout=10)
                        response.raise_for_status()
                        logger.info(f"Gửi phần tin nhắn {i+1} thành công bằng phương thức plain text fallback.")
                        chunk_success = True
                        break
                    except Exception as fallback_err:
                        logger.error(f"Fallback plain text thất bại: {fallback_err}")
                else:
                    logger.error(f"Lỗi gửi tin nhắn Telegram (lần thử {attempt}/{MAX_RETRIES}): {e}")

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

        if not chunk_success:
            success = False

    return success


def send_hunt_report(filter_name, candidates):
    """
    Gửi báo cáo kết quả quét cổ phiếu cho bộ lọc tương ứng.
    
    candidates: Danh sách các tuple (symbol, scorecard_dict, ai_report_text)
    """
    if not candidates:
        msg = f"<b>[{filter_name}]</b>: Không tìm thấy cổ phiếu thỏa mãn."
        return send_telegram_message(msg)
        
    # Tạo bảng scorecard
    table = format_scorecard_table(candidates)
    
    # Tạo nội dung báo cáo tổng thể
    report = f"<b>🔍 BỘ LỌC: {filter_name.upper()}</b>\n"
    report += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    report += table + "\n\n"
    
    for symbol, sc, ai_text in candidates:
        report += f"<b>📌 Cổ phiếu {symbol}:</b>\n"
        if ai_text:
            escaped_ai = escape_ai_text(ai_text)
            report += f"{escaped_ai}\n\n"
        else:
            report += "<i>Không có phân tích AI.</i>\n\n"
            
    return send_telegram_message(report)
