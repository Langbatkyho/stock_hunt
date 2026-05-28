import os
import sys
import pandas as pd
import numpy as np

# Add project root and bot_app to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'bot_app')))
sys.stdout.reconfigure(encoding='utf-8')

from stock_hunt import config
from stock_hunt.scanner import check_pre_filters
from bot_app.data_fetcher import fetch_ohlcv, fetch_volume_profile, fetch_summary
from bot_app.indicators import calc_ta_indicators, calc_rs, calc_active_buy_pct
from vnstock_data import Insights, Reference

def main():
    print("=== START QUANTITATIVE AUDIT FOR BVB, VC3, KHG ===")
    symbols = ['BVB', 'VC3', 'KHG']
    
    # Initialize benchmark
    print("Fetching VNINDEX Benchmark...")
    df_benchmark = fetch_ohlcv("VNINDEX", length='1Y', is_index=True)
    if df_benchmark is None or df_benchmark.empty:
        print("[ERROR] Failed to fetch VNINDEX benchmark.")
        return
        
    # Initialize Screener data to get stock_strength (percentile rank) and exchange info
    print("Fetching Insights Screener for global details...")
    ins = Insights()
    broad_filter = [{"name": "marketPrice", "conditionOptions": [{"from": 0, "to": 1000000}]}]
    df_screener = ins.screener.filter(filters=broad_filter, limit=2000)
    
    # Try fetching exchange via Reference.equity.list_by_exchange()
    df_exchange_info = None
    try:
        ref = Reference()
        df_exchange_info = ref.equity.list_by_exchange()
    except Exception as e:
        print(f"[WARN] Failed to fetch exchange info via Reference: {e}")
        
    for symbol in symbols:
        print(f"\n==================================================")
        print(f"AUDITING SYMBOL: {symbol}")
        
        # 0. Find Exchange
        exchange = "Unknown"
        if df_screener is not None and not df_screener.empty:
            sym_screen = df_screener[df_screener['symbol'] == symbol]
            if not sym_screen.empty and 'exchange' in sym_screen.columns:
                exchange = sym_screen['exchange'].iloc[0]
        
        if exchange == "Unknown" and df_exchange_info is not None:
            if isinstance(df_exchange_info, dict):
                for ex_name, df_ex in df_exchange_info.items():
                    if 'symbol' in df_ex.columns and symbol in df_ex['symbol'].values:
                        exchange = ex_name
                        break
            elif hasattr(df_exchange_info, 'columns') and 'exchange' in df_exchange_info.columns:
                sym_ex = df_exchange_info[df_exchange_info['symbol'] == symbol]
                if not sym_ex.empty:
                    exchange = sym_ex['exchange'].iloc[0]
                    
        print(f"Exchange: {exchange}")
        
        # 1. Fetch EOD OHLCV
        df_ohlcv = fetch_ohlcv(symbol, length='1Y')
        if df_ohlcv is None or df_ohlcv.empty:
            print(f"[FAIL] Could not fetch OHLCV for {symbol}")
            continue
            
        print(f"OHLCV data points: {len(df_ohlcv)}")
        
        # 2. Extract basic TA metrics
        volumes = df_ohlcv['volume']
        vol_sma20 = volumes.rolling(20).mean().iloc[-1]
        vol_sma10 = volumes.rolling(10).mean().iloc[-1]
        
        ta_ind = calc_ta_indicators(df_ohlcv)
        rsi_14 = ta_ind.get('rsi_14')
        price_vs_ma20_pct = ta_ind.get('price_vs_ma20_pct')
        
        rs_ind = calc_rs(df_ohlcv, df_benchmark)
        rs_avg = rs_ind.get('rs_avg')
        
        # 3. Pull stock_strength (Percentile rank) from Screener
        stock_strength = None
        if df_screener is not None and not df_screener.empty:
            sym_screen = df_screener[df_screener['symbol'] == symbol]
            if not sym_screen.empty and 'stock_strength' in sym_screen.columns:
                stock_strength = sym_screen['stock_strength'].iloc[0]
                
        # 4. Fetch volume profile for active buy pct
        df_vol_profile = fetch_volume_profile(symbol)
        active_buy_pct = calc_active_buy_pct(df_vol_profile)
        
        # 5. Fetch P/B ratio from summary
        summary = fetch_summary(symbol)
        pb = None
        if summary is not None and not summary.empty and 'pb' in summary.columns:
            pb = summary['pb'].iloc[-1]
            
        # Calculate 10-day Average Trading Value
        last_close = df_ohlcv['close'].iloc[-1]
        is_in_thousands = last_close < 1000
        multiplier = 1000 if is_in_thousands else 1
        trading_val = df_ohlcv['volume'] * (df_ohlcv['close'] * multiplier)
        avg_trading_val_10d = trading_val.rolling(10).mean().iloc[-1]
        
        print(f"\n--- METRICS REPORT FOR {symbol} ---")
        print(f" - Exchange: {exchange}")
        print(f" - Last Close: {last_close * multiplier:,.0f} VND")
        print(f" - Vol SMA20: {vol_sma20:,.0f} shares")
        print(f" - Vol SMA10: {vol_sma10:,.0f} shares")
        print(f" - RSI(14): {rsi_14:.2f}" if rsi_14 is not None else " - RSI(14): None")
        print(f" - Price vs MA20 Distance: {price_vs_ma20_pct:.2f}%" if price_vs_ma20_pct is not None else " - Price vs MA20 Distance: None")
        print(f" - RS Absolute (vs VNINDEX EOD): {rs_avg:.2f}" if rs_avg is not None else " - RS Absolute: None")
        print(f" - RS Percentile Rank (stock_strength from Screener): {stock_strength}" if stock_strength is not None else " - RS Percentile Rank: None")
        print(f" - Active Buy %: {active_buy_pct:.2f}%" if active_buy_pct is not None else " - Active Buy %: None")
        print(f" - 10-day Avg Trading Value: {avg_trading_val_10d:,.0f} VND")
        print(f" - P/B: {pb}" if pb is not None else " - P/B: None")
        
        # 6. Pre-filter evaluation
        passed_pre, pre_details = check_pre_filters(symbol, df_ohlcv, df_benchmark)
        print(f"\n--- PRE-FILTER EVALUATION ---")
        print(f" - Overall Pre-filter Passed: {passed_pre}")
        if passed_pre:
            print(f"   - Match Pre-F1 (Tích lũy phá nền): {pre_details.get('pass_pre_f1')}")
            print(f"   - Match Pre-F2 (Hổ gặp nạn): {pre_details.get('pass_pre_f2')}")
            print(f"   - Match Pre-F3 (Vua sập bẫy): {pre_details.get('pass_pre_f3')}")
        else:
            print(f"   - Details: {pre_details}")
            
        # 7. Strict Filter evaluation
        # Resolve RS percentile rank (stock_strength) or fallback to rs_avg
        rs_val = stock_strength if stock_strength is not None else (rs_avg if rs_avg is not None else 0)
        
        pass_pre_f1 = pre_details.get('pass_pre_f1', False)
        pass_pre_f2 = pre_details.get('pass_pre_f2', False)
        pass_pre_f3 = pre_details.get('pass_pre_f3', False)
        
        is_f1 = pass_pre_f1 and (active_buy_pct is not None and 42 <= active_buy_pct <= 55) and (40 <= rs_val <= 60)
        is_f2 = pass_pre_f2 and (active_buy_pct is not None and 42 <= active_buy_pct <= 55) and (rs_val > 65)
        
        pb_float = 999.0
        if pb is not None:
            try:
                pb_float = float(pb)
            except:
                pass
        is_f3 = pass_pre_f3 and (pb_float < 1.1) and (active_buy_pct is not None and active_buy_pct > 50)
        
        print(f"\n--- STRICT FILTER EVALUATION ---")
        print(f" - Filter 1 (Tích lũy phá nền) strictly matched? {is_f1}")
        if not is_f1 and pass_pre_f1:
            reasons = []
            if active_buy_pct is None or not (42 <= active_buy_pct <= 55):
                reasons.append(f"Active Buy % ({active_buy_pct:.2f}%) out of [42%, 55%]")
            if not (40 <= rs_val <= 60):
                reasons.append(f"RS Percentile Rank ({rs_val:.2f}) out of [40, 60]")
            print(f"   -> Reason for strict failure: {', '.join(reasons)}")
            
        print(f" - Filter 2 (Hổ gặp nạn) strictly matched? {is_f2}")
        if not is_f2 and pass_pre_f2:
            reasons = []
            if active_buy_pct is None or not (42 <= active_buy_pct <= 55):
                reasons.append(f"Active Buy % ({active_buy_pct:.2f}%) out of [42%, 55%]")
            if not (rs_val > 65):
                reasons.append(f"RS Percentile Rank ({rs_val:.2f}) not > 65")
            print(f"   -> Reason for strict failure: {', '.join(reasons)}")
            
        print(f" - Filter 3 (Vua sập bẫy) strictly matched? {is_f3}")
        if not is_f3 and pass_pre_f3:
            reasons = []
            if pb_float is None or pb_float >= 1.1:
                reasons.append(f"P/B ratio ({pb_float}) not < 1.1")
            if active_buy_pct is None or active_buy_pct <= 50:
                reasons.append(f"Active Buy % ({active_buy_pct:.2f}%) not > 50%")
            print(f"   -> Reason for strict failure: {', '.join(reasons)}")
            
        # Check system config criteria
        exchanges_lower = [e.lower() for e in config.EXCHANGES]
        is_exchange_allowed = exchange.lower() in exchanges_lower or (exchange.lower() == 'hsx' and 'hose' in exchanges_lower)
        print(f" - System allowed exchange? {is_exchange_allowed} (System config: {config.EXCHANGES}, Symbol exchange: {exchange})")

if __name__ == '__main__':
    main()
