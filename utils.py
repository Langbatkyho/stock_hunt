# Utility functions for Stock Hunt Bot
import numpy as np
import pandas as pd

def _to_native(value):
    """
    Chuyển đổi các định dạng số, kiểu dữ liệu đặc thù của numpy/pandas sang các kiểu dữ liệu
    nguyên bản (native types) của Python để tránh lỗi tương thích hoặc lỗi tuần tự hóa JSON.
    """
    if isinstance(value, dict):
        return {k: _to_native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_native(x) for x in value]
    if hasattr(value, 'item'):
        return value.item()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, (pd.Timestamp, pd.DatetimeIndex)):
        return str(value)
    if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
        return None
    return value

def is_price_in_vnd(price):
    """
    Xác định xem giá cổ phiếu có đang ở đơn vị VND gốc hay không.
    Ngưỡng 500 là ngưỡng an toàn tuyệt đối (không có cổ phiếu nào giá dưới 500đ, 
    và cũng không có cổ phiếu nào ở đơn vị nghìn đồng mà giá > 500).
    """
    if price is None:
        return False
    return price >= 500

def get_price_in_vnd(price):
    """Đảm bảo trả về giá ở đơn vị VND gốc."""
    if price is None:
        return 0.0
    return float(price) if is_price_in_vnd(price) else float(price) * 1000.0

def get_price_in_thousands(price):
    """Đảm bảo trả về giá ở đơn vị nghìn đồng (thousands)."""
    if price is None:
        return 0.0
    return float(price) / 1000.0 if is_price_in_vnd(price) else float(price)

