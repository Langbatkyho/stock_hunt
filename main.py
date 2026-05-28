import os
import sys
import time
import argparse
import logging
import signal
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone, timedelta
import schedule

# Cấu hình đường dẫn thư mục gốc để import bot_app và các modules khác dễ dàng
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'bot_app'))

import stock_hunt.config as config
from stock_hunt.scanner import run_scan
from stock_hunt.ai_analyzer import analyze_candidate
from stock_hunt.telegram_bot import send_hunt_report

# Tạo thư mục chứa log nếu chưa tồn tại
logs_dir = os.path.join(project_root, 'stock_hunt', 'logs')
os.makedirs(logs_dir, exist_ok=True)
log_file_path = os.path.join(logs_dir, 'stock_hunt.log')

# Thiết lập hệ thống ghi log (RotatingFileHandler tối đa 5MB, giữ 3 bản backup, mã hóa UTF-8)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(
    log_file_path,
    maxBytes=5 * 1024 * 1024,
    backupCount=3,
    encoding='utf-8'
)
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] (%(name)s) %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Ghi log ra Console để theo dõi trực tiếp
console_handler = logging.StreamHandler(sys.stdout)
console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# Ghi nhận log khởi động
logger.info("Khởi động hệ thống theo dõi cổ phiếu Stock Hunt...")

# Import reset_market từ bot_app.data_fetcher một cách an toàn
try:
    from bot_app.data_fetcher import reset_market
    logger.info("Import reset_market thành công từ bot_app.data_fetcher.")
except ImportError:
    logger.warning("Không thể import reset_market từ bot_app.data_fetcher. Sử dụng hàm fallback mặc định.")
    def reset_market():
        logger.info("Đang thực hiện làm sạch phiên và cache dữ liệu thị trường...")


def job():
    """Hàm xử lý công việc chính được kích hoạt theo lịch trình hoặc qua tham số --now"""
    logger.info("==================================================================")
    logger.info("=== BẮT ĐẦU CHU KỲ QUÉT VÀ PHÂN TÍCH CỔ PHIẾU ===")
    logger.info("==================================================================")
    
    try:
        # Ghi nhận thời gian bắt đầu
        start_time = time.time()
        
        # 1. Khởi tạo lại phiên kết nối và xóa cache cũ
        logger.info("Bước 1: Khởi tạo lại kết nối thị trường (fresh session/invalidate cache)...")
        reset_market()
        
        # 2. Chạy Scanner tìm kiếm các mã cổ phiếu thỏa mãn các bộ lọc kỹ thuật
        logger.info("Bước 2: Tiến hành chạy Scanner cho các sàn HOSE và HNX...")
        candidates_by_filter = run_scan()
        logger.info(f"Quét hoàn tất. Số lượng ứng viên tìm thấy: "
                    f"[{config.FILTER_1}: {len(candidates_by_filter.get(config.FILTER_1, []))}], "
                    f"[{config.FILTER_2}: {len(candidates_by_filter.get(config.FILTER_2, []))}], "
                    f"[{config.FILTER_3}: {len(candidates_by_filter.get(config.FILTER_3, []))}]")
        
        # 3. Với mỗi bộ lọc, tiến hành gọi AI phân tích chi tiết từng cổ phiếu
        filters = [config.FILTER_1, config.FILTER_2, config.FILTER_3]
        
        for filter_name in filters:
            logger.info(f"Đang xử lý báo cáo cho bộ lọc: {filter_name}")
            candidates = candidates_by_filter.get(filter_name, [])
            
            report_candidates = []
            for symbol, scorecard_dict in candidates:
                logger.info(f"Đang phân tích AI cho mã cổ phiếu {symbol} thuộc bộ lọc {filter_name}...")
                
                # Gọi AI Analyzer để tạo báo cáo
                ai_report_text = analyze_candidate(symbol, scorecard_dict, filter_name)
                report_candidates.append((symbol, scorecard_dict, ai_report_text))
                
                # Tránh gọi Gemini dồn dập (rate limit)
                time.sleep(2)
                
            # 4. Gửi báo cáo kết quả qua Telegram
            logger.info(f"Gửi báo cáo của bộ lọc '{filter_name}' qua Telegram...")
            send_hunt_report(filter_name, report_candidates)
            
            # Giãn cách giữa các lần gửi báo cáo bộ lọc
            time.sleep(2)
            
        elapsed_time = time.time() - start_time
        logger.info("==================================================================")
        logger.info(f"=== CHU KỲ QUÉT HOÀN TẤT THÀNH CÔNG TRONG {elapsed_time:.1f} GIÂY ===")
        logger.info("==================================================================")
        
    except Exception as e:
        logger.error(f"Lỗi nghiêm trọng trong chu kỳ quét cổ phiếu: {e}", exc_info=True)


def sigterm_handler(signum, frame):
    logger.info("Nhận tín hiệu tắt hệ thống. Đang thoát an toàn (graceful shutdown)...")
    sys.exit(0)

# Đăng ký signal handler cho SIGTERM (Windows và Linux)
try:
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)
except Exception as e:
    logger.warning(f"Không thể đăng ký signal handler: {e}")

def get_system_time_for_gmt7(gmt7_time_str):
    """
    Chuyển đổi một chuỗi giờ 'HH:MM' định dạng GMT+7 sang giờ hệ thống tương ứng 'HH:MM'.
    Giúp scheduler kích hoạt đúng giờ bất kể múi giờ của máy chủ chạy bot.
    """
    try:
        now = datetime.now()
        h, m = map(int, gmt7_time_str.split(':'))
        tz_gmt7 = timezone(timedelta(hours=7))
        dt_gmt7 = datetime(now.year, now.month, now.day, h, m, tzinfo=tz_gmt7)
        dt_local = dt_gmt7.astimezone()
        return dt_local.strftime("%H:%M")
    except Exception as e:
        logger.error(f"Lỗi khi chuyển đổi múi giờ cho {gmt7_time_str}: {e}")
        return gmt7_time_str


def main():
    parser = argparse.ArgumentParser(description="Stock Hunt Scanner & AI Pipeline CLI Tool")
    parser.add_argument('--now', action='store_true', help="Chạy chu kỳ quét ngay lập tức để debug/kiểm thử và thoát.")
    args = parser.parse_args()
    
    if args.now:
        logger.info("Nhận diện tham số --now. Đang kích hoạt quét khẩn cấp ngay lập tức...")
        job()
        logger.info("Quét khẩn cấp hoàn tất. Chương trình sẽ tự động đóng.")
        sys.exit(0)
        
    # Thiết lập chạy định kỳ
    gmt7_times = getattr(config, 'SCHEDULE_TIMES', ["10:15", "14:05"])
    logger.info(f"Thiết lập lịch quét tự động tại các mốc (giờ Việt Nam GMT+7): {gmt7_times}")
    
    times = [get_system_time_for_gmt7(t) for t in gmt7_times]
    logger.info(f"Mốc giờ hệ thống tương ứng được cài đặt: {times}")
    
    for t in times:
        schedule.every().day.at(t).do(job)
        
    logger.info("Vòng lặp Scheduler đang hoạt động. Chương trình sẽ chạy vô hạn để quét tự động...")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
