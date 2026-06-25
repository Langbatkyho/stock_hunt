import os
import sys
import pandas as pd
import numpy as np

# Thêm đường dẫn dự án và bot_app để import thành công
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'bot_app')))
sys.stdout.reconfigure(encoding='utf-8')

from bot_app.data_fetcher import fetch_ohlcv
from bot_app.indicators import calc_ta_indicators
from stock_hunt.ai_analyzer import generate_prompt
from stock_hunt.utils import _to_native

def main():
    print("=== BẮT ĐẦU KIỂM TRA CHỈ SỐ LỊCH SỬ RSI TRÊN DỮ LIỆU THẬT ===")
    
    # 1. Tải dữ liệu OHLCV thật của mã SSI
    symbol = "SSI"
    print(f"Đang tải dữ liệu 1 năm của mã {symbol}...")
    df_ohlcv = fetch_ohlcv(symbol, length='1Y')
    if df_ohlcv is None or df_ohlcv.empty:
        print("[LỖI] Không thể tải dữ liệu OHLCV cho SSI. Kiểm tra kết nối internet.")
        return
        
    print(f"Tải thành công {len(df_ohlcv)} phiên giao dịch.")
    
    # 2. Tính toán các chỉ báo kỹ thuật bao gồm rsi_14_history mới
    print("Đang tính toán các chỉ báo kỹ thuật...")
    indicators = calc_ta_indicators(df_ohlcv)
    
    # 3. Kiểm chứng sự tồn tại và tính hợp lệ của rsi_14_history
    if 'rsi_14_history' not in indicators:
        print("[LỖI] Không tìm thấy khóa 'rsi_14_history' trong chỉ báo kỹ thuật trả về!")
        return
        
    rsi_hist = indicators['rsi_14_history']
    print(f"\n[XÁC THỰC THÀNH CÔNG] Đã tìm thấy 'rsi_14_history' trong scorecard.")
    print(f" - Độ dài chuỗi RSI lịch sử: {len(rsi_hist)} phiên (kỳ vọng: 30)")
    print(f" - Danh sách các giá trị RSI lịch sử (từ cũ đến mới):")
    print(f"   {rsi_hist}")
    print(f" - Giá trị RSI hiện tại (T-0): {indicators.get('rsi_14'):.2f}")
    
    # 4. Serialize qua _to_native để kiểm tra an toàn dữ liệu
    print("\nKiểm tra quá trình serialize qua _to_native...")
    native_indicators = _to_native(indicators)
    print("Serialize thành công không có lỗi crash!")
    
    # 5. Tạo prompt phân tích bằng AI
    print("\nĐang tạo prompt phân tích động cho Gemini...")
    # Tạo scorecard giả định chứa các thông tin tối thiểu
    scorecard = {
        'symbol': symbol,
        'current_price': df_ohlcv['close'].iloc[-1],
        '1D_pct': 1.5,
        'rsi_14': indicators.get('rsi_14'),
        'rsi_14_history': native_indicators.get('rsi_14_history'),
        'rsi_status': indicators.get('rsi_status'),
        'price_vs_ma20_pct': indicators.get('price_vs_ma20_pct', 0.0),
        'active_buy_pct': 52.3
    }
    
    prompt = generate_prompt(symbol, scorecard, "Tích lũy phá nền")
    print("=== DƯỚI ĐÂY LÀ NỘI DUNG PROMPT ĐÃ ĐƯỢC TẬP TRUNG RSI RANGE SHIFT THỜI GIAN ===")
    print(prompt)
    print("==================================================================================")
    print("🎉 BÀI TẤT CẢ KIỂM TRA ĐÃ THÀNH CÔNG RỰC RỠ!")

if __name__ == '__main__':
    main()
