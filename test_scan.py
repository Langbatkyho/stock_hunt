import os
import sys
import logging
import pandas as pd
import numpy as np

# Thêm đường dẫn dự án
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Thiết lập log cho test
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("stock_hunt_test")

def create_mock_ohlcv(price_trend="flat", vol_level=1200000):
    """
    Tạo DataFrame OHLCV giả lập cho mục đích unit test.
    Chiều dài: 60 phiên để đảm bảo tính toán rolling MA20 và RSI14.
    """
    dates = pd.date_range(end=pd.Timestamp.now(), periods=60)
    
    # Sử dụng normalize=True để làm tròn Timestamp về 00:00:00, giúp so khớp index thời gian hoàn hảo với Benchmark
    dates = pd.date_range(end=pd.Timestamp.now(), periods=60, normalize=True)
    
    # Tạo giá đóng cửa giả lập với dao động tự nhiên để chỉ báo kỹ thuật tính toán chuẩn xác
    if price_trend == "flat":
        # Dao động hình sin nhẹ kết hợp tăng trưởng cực nhỏ để tạo RSI ~45-48 và giữ giá sát MA20
        closes = [20.0 + 0.18 * np.sin(i * 0.5) + 0.008 * i for i in range(60)]
    elif price_trend == "dip":
        closes = list(np.linspace(25, 15, 60))
    elif price_trend == "oversold":
        # Giảm dần kết hợp sóng dao động lớn đan xen để tạo các phiên hồi kỹ thuật, giúp RSI giữ vững trong dải [25, 35]
        closes = [30.0 + 0.1 * np.sin(i) for i in range(40)] + [30.0 - 0.2 * (i - 40) + 0.6 * np.sin(i) for i in range(40, 60)]
    else:
        # Tăng dần từ 15 lên 25
        closes = list(np.linspace(15, 25, 60))
        
    volumes = [vol_level] * 60
    
    df = pd.DataFrame({
        'time': dates,
        'open': closes,
        'high': [c * 1.01 for c in closes],
        'low': [c * 0.99 for c in closes],
        'close': closes,
        'volume': volumes
    })
    return df

def create_mock_benchmark():
    """Tạo DataFrame Benchmark giả lập (VNINDEX)."""
    # Sử dụng normalize=True để đồng bộ hoàn chỉnh Timestamp
    dates = pd.date_range(end=pd.Timestamp.now(), periods=60, normalize=True)
    closes = list(np.linspace(1100, 1150, 60))
    df = pd.DataFrame({
        'time': dates,
        'open': closes,
        'high': closes,
        'low': closes,
        'close': closes,
        'volume': [10000000] * 60
    })
    return df

def run_mock_unit_tests():
    """Chạy các kịch bản kiểm thử giả định trên logic lọc kỹ thuật check_pre_filters."""
    logger.info("4. Khởi chạy bộ kiểm thử định lượng giả lập (Mock Unit Tests)...")
    
    from stock_hunt.scanner import check_pre_filters
    
    df_benchmark = create_mock_benchmark()
    
    # Kịch bản A: Cổ phiếu đi ngang tích lũy chặt chẽ (sử dụng mã VCB thật để lấy được RS)
    logger.info(" -> Chạy Kịch bản A: Cổ phiếu tích lũy nền phẳng (Mã: AAA)...")
    df_f1 = create_mock_ohlcv(price_trend="flat", vol_level=1200000)
    passed_a, details_a = check_pre_filters("AAA", df_f1, df_benchmark)
    
    # Kịch bản B: Cổ phiếu giảm sâu quá bán (Mã: DPM)
    logger.info(" -> Chạy Kịch bản B: Cổ phiếu sập bẫy quá bán (Mã: DPM)...")
    df_f3 = create_mock_ohlcv(price_trend="oversold", vol_level=3500000)
    passed_b, details_b = check_pre_filters("DPM", df_f3, df_benchmark)
    
    # Kịch bản C: Cổ phiếu thanh khoản quá yếu (Mã: AAA)
    logger.info(" -> Chạy Kịch bản C: Cổ phiếu không có thanh khoản (Mã: AAA)...")
    df_low = create_mock_ohlcv(price_trend="flat", vol_level=50000)
    passed_c, details_c = check_pre_filters("AAA", df_low, df_benchmark)
    
    logger.info("=== KẾT QUẢ KIỂM THỬ ĐỊNH LƯỢNG MOCK DATA ===")
    logger.info(f" - Kịch bản A (Tích lũy): passed={passed_a}, Khớp Pre-F1={details_a.get('pass_pre_f1')}")
    logger.info(f" - Kịch bản B (Quá bán/Sập bẫy): passed={passed_b}, Khớp Pre-F3={details_b.get('pass_pre_f3')}")
    logger.info(f" - Kịch bản C (Yếu thanh khoản): passed={passed_c} (Kỳ vọng: False)")
    
    assert passed_a == True, "Lỗi: Kịch bản tích lũy nền phẳng bắt buộc phải khớp bộ lọc thô 1!"
    assert passed_b == True, "Lỗi: Kịch bản quá bán sâu bắt buộc phải khớp bộ lọc thô 3!"
    assert passed_c == False, "Lỗi: Cổ phiếu thanh khoản quá thấp phải bị loại bỏ ngay lập tức!"
    
    logger.info("🎉 TẤT CẢ CÁC BÀI KIỂM THỬ UNIT TEST MOCK ĐÃ VƯỢT QUA THÀNH CÔNG!")


def main():
    logger.info("=== BẮT ĐẦU CHẠY KIỂM THỬ KHỞI ĐỘNG MODULE SCANNER ===")
    
    try:
        from stock_hunt.scanner import get_exchange_symbols
        
        # 1. Test lấy danh sách sàn
        logger.info("1. Kiểm tra tải danh sách mã HOSE...")
        hose_symbols = get_exchange_symbols("HOSE")
        logger.info(f"Lấy thành công {len(hose_symbols)} mã từ sàn HOSE.")
        if hose_symbols:
            logger.info(f"Ví dụ 5 mã đầu tiên: {hose_symbols[:5]}")
            
        logger.info("2. Kiểm tra tải danh sách mã HNX...")
        hnx_symbols = get_exchange_symbols("HNX")
        logger.info(f"Lấy thành công {len(hnx_symbols)} mã từ sàn HNX.")
        if hnx_symbols:
            logger.info(f"Ví dụ 5 mã đầu tiên: {hnx_symbols[:5]}")
            
        # 2. Nhập và import các hàm chính của hệ thống
        logger.info("3. Nhập và import các hàm chính của hệ thống...")
        from stock_hunt.scanner import run_scan
        logger.info("Hệ thống đã sẵn sàng để quét.")
        
        # 3. Kích hoạt Unit Test
        run_mock_unit_tests()
        
        print("\n[OK] Module scanner tải thành công và kiểm tra cơ bản hoạt động tốt!")
        print("Để chạy quét thực tế kèm AI và Telegram, vui lòng chạy file run_hunt_bot.bat --now hoặc python -m stock_hunt.main --now\n")
        
    except Exception as e:
        logger.error(f"Gặp lỗi khi kiểm tra module scanner: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
