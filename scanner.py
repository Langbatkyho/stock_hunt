import sys
import os
import time
import logging
import pandas as pd
from stock_hunt import config

# ─────────────────────────────────────────────────────────────────────────────
# 1. PATH RESOLUTION & DYNAMIC IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
# Set encoding for safe console output
sys.stdout.reconfigure(encoding='utf-8')

# Dynamic project root resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # parent of stock_hunt
if project_root not in sys.path:
    sys.path.insert(0, project_root)



# ─────────────────────────────────────────────────────────────────────────────
# 2. LOGGING CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
logger = logging.getLogger("stock_hunt.scanner")

# ─────────────────────────────────────────────────────────────────────────────
# 3. SINGLETON MARKET INSTANCE
# ─────────────────────────────────────────────────────────────────────────────
_market_instance = None

def get_market():
    """Get or create a reusable Market instance."""
    global _market_instance
    if _market_instance is None:
        try:
            from vnstock_data import Market
            _market_instance = Market(random_agent=True)
            logger.info("Created reusable vnstock_data.Market instance.")
        except Exception as e:
            logger.error(f"Failed to initialize Market instance: {e}")
    return _market_instance

# ─────────────────────────────────────────────────────────────────────────────
# 4. HOSE & HNX SYMBOL RETRIEVER (UPCOM Excluded)
# ─────────────────────────────────────────────────────────────────────────────
def get_exchange_symbols(exchange="HOSE"):
    """Retrieve symbols from a specific exchange (HOSE or HNX) using multiple APIs to ensure high robustness."""
    exchange = exchange.upper()
    
    # Try 1: Reference.equity.list_by_group (Unified UI)
    try:
        from vnstock_data import Reference
        ref = Reference()
        df = ref.equity.list_by_group(exchange)
        if df is not None and not df.empty and 'symbol' in df.columns:
            logger.info(f"Retrieved symbols for {exchange} using Reference.equity.list_by_group")
            return df['symbol'].tolist()
    except Exception as e:
        logger.warning(f"Failed to get symbols using Reference.equity.list_by_group for {exchange}: {e}")
        
    # Try 2: Reference.equity.list_by_exchange (Unified UI)
    try:
        from vnstock_data import Reference
        ref = Reference()
        df = ref.equity.list_by_exchange()
        if df is not None and not df.empty:
            if isinstance(df, dict):
                if exchange in df:
                    df_ex = df[exchange]
                    if 'symbol' in df_ex.columns:
                        return df_ex['symbol'].tolist()
            elif hasattr(df, 'columns') and 'exchange' in df.columns:
                filtered = df[df['exchange'].str.upper() == exchange]
                if not filtered.empty and 'symbol' in filtered.columns:
                    return filtered['symbol'].tolist()
    except Exception as e:
        logger.warning(f"Failed to get symbols using Reference.equity.list_by_exchange: {e}")

    # Try 3: Listing(source='VCI').symbols_by_exchange
    for source in ['VCI', 'KBS', 'VND']:
        try:
            from vnstock_data import Listing
            listing = Listing(source=source)
            if source == 'KBS':
                df = listing.symbols_by_exchange(get_all=True)
            else:
                df = listing.symbols_by_exchange()
            if df is not None and not df.empty and 'exchange' in df.columns:
                filtered = df[df['exchange'].str.upper() == exchange]
                if not filtered.empty and 'symbol' in filtered.columns:
                    logger.info(f"Retrieved symbols for {exchange} using Listing(source='{source}').symbols_by_exchange")
                    return filtered['symbol'].tolist()
        except Exception as e:
            logger.warning(f"Failed to get symbols using Listing(source='{source}').symbols_by_exchange: {e}")

    # Try 4: Listing(source='VND').all_symbols()
    try:
        from vnstock_data import Listing
        listing = Listing(source='VND')
        df = listing.all_symbols()
        if df is not None and not df.empty and 'exchange' in df.columns:
            filtered = df[df['exchange'].str.upper() == exchange]
            if not filtered.empty and 'symbol' in filtered.columns:
                logger.info(f"Retrieved symbols for {exchange} using Listing(source='VND').all_symbols")
                return filtered['symbol'].tolist()
    except Exception as e:
        logger.warning(f"Failed to get symbols using Listing(source='VND').all_symbols: {e}")
        
    return []

# ─────────────────────────────────────────────────────────────────────────────
# 5. LIGHTWEIGHT OHLCV PRE-FILTERING (Huge Optimization)
# ─────────────────────────────────────────────────────────────────────────────
def check_pre_filters(symbol, df_ohlcv, df_benchmark):
    """
    Apply pre-filters using only OHLCV and daily benchmark to minimize heavy API calls.
    Returns: (bool passed_any, dict details)
    """
    from bot_app.indicators import calc_ta_indicators, calc_rs
    
    if df_ohlcv is None or len(df_ohlcv) < 50:
        return False, {}
        
    try:
        # Calculate moving averages of volume
        volumes = df_ohlcv['volume']
        vol_sma20 = volumes.rolling(20).mean().iloc[-1]
        vol_sma10 = volumes.rolling(10).mean().iloc[-1]
        
        # Calculate RSI(14) and MA distances
        ta_ind = calc_ta_indicators(df_ohlcv)
        rsi_14 = ta_ind.get('rsi_14')
        price_vs_ma20_pct = ta_ind.get('price_vs_ma20_pct')
        
        # Calculate Relative Strength average
        rs_ind = calc_rs(df_ohlcv, df_benchmark)
        rs_avg = rs_ind.get('rs_avg')
        
        # Calculate 10-day Average Trading Value using centralized price normalizer
        from stock_hunt.utils import get_price_in_vnd
        last_close = df_ohlcv['close'].iloc[-1]
        close_prices_vnd = df_ohlcv['close'].apply(get_price_in_vnd)
        trading_val = df_ohlcv['volume'] * close_prices_vnd
        avg_trading_val_10d = trading_val.rolling(10).mean().iloc[-1]
        
        # Save calculations for final scorecard use
        pre_calc = {
            'vol_sma20': vol_sma20,
            'vol_sma10': vol_sma10,
            'rsi_14': rsi_14,
            'price_vs_ma20_pct': price_vs_ma20_pct,
            'rs_avg': rs_avg,
            'avg_trading_val_10d': avg_trading_val_10d,
            'ta_ind': ta_ind,
            'rs_ind': rs_ind,
            'trading_value_billion': (volumes.iloc[-1] * get_price_in_vnd(last_close)) / 1_000_000_000
        }
        
        # Check Pre-Filter 1: Tích lũy phá nền (Excluding Volume Profile check for now)
        pass_pre_f1 = False
        if (vol_sma20 is not None and vol_sma20 > 1_000_000 and
            rs_avg is not None and -15 <= rs_avg <= 35 and
            rsi_14 is not None and 40 <= rsi_14 <= 52 and
            price_vs_ma20_pct is not None and -1.2 <= price_vs_ma20_pct <= 1.2):
            pass_pre_f1 = True
            
        # Check Pre-Filter 2: Hổ gặp nạn (Excluding Volume Profile check for now)
        pass_pre_f2 = False
        if (avg_trading_val_10d is not None and avg_trading_val_10d > 10_000_000_000 and
            vol_sma10 is not None and vol_sma10 > 500_000 and
            rs_avg is not None and rs_avg > -15 and
            rsi_14 is not None and 20 <= rsi_14 <= 35):
            pass_pre_f2 = True
            
        # Check Pre-Filter 3: Vua sập bẫy (Excluding P/B and Volume Profile check for now)
        pass_pre_f3 = False
        if (vol_sma10 is not None and vol_sma10 > 3_000_000 and
            rsi_14 is not None and 25 <= rsi_14 <= 35):
            pass_pre_f3 = True
            
        passed_any = pass_pre_f1 or pass_pre_f2 or pass_pre_f3
        
        return passed_any, {
            'pass_pre_f1': pass_pre_f1,
            'pass_pre_f2': pass_pre_f2,
            'pass_pre_f3': pass_pre_f3,
            'pre_calc': pre_calc
        }
    except Exception as e:
        logger.error(f"Error checking pre-filters for {symbol}: {e}")
        return False, {}

# ─────────────────────────────────────────────────────────────────────────────
# 6. CENTRALIZED UTILITY IMPORTS
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# 7. SCANNER MAIN LOGIC
# ─────────────────────────────────────────────────────────────────────────────
def run_scan():
    """
    Scan both HOSE and HNX markets (excluding UPCOM) using the three designated filters:
    1. Tích lũy phá nền
    2. Hổ gặp nạn
    3. Vua sập bẫy
    
    Returns:
        dict: { 'Tích lũy phá nền': [(symbol, score_dict), ...],
                'Hổ gặp nạn': [(symbol, score_dict), ...],
                'Vua sập bẫy': [(symbol, score_dict), ...] }
    """
    logger.info("Initializing automated scan of HOSE and HNX exchanges...")
    
    # Import data_fetcher tools and initialize market
    from bot_app.data_fetcher import (
        fetch_ohlcv, fetch_ohlcv_long, fetch_quote,
        fetch_summary, fetch_volume_profile, fetch_foreign_flow
    )
    # from bot_app.custom_benchmark import get_custom_benchmark_ohlcv
    from bot_app.indicators import build_scorecard, calc_active_buy_pct
    from bot_app.strategy import evaluate_strategy
    
    get_market() # Force initialization
    
    # 1. Fetch benchmark once (VNINDEX Benchmark)
    logger.info("Fetching daily VNINDEX Benchmark...")
    df_benchmark = fetch_ohlcv("VNINDEX", length='1Y', is_index=True)
    if df_benchmark is None or df_benchmark.empty:
        logger.error("Failed to retrieve VNINDEX benchmark. Aborting scan.")
        return {'Tích lũy phá nền': [], 'Hổ gặp nạn': [], 'Vua sập bẫy': []}
        
    # 2. Retrieve exchange symbols from config and apply Layer 0 Pre-filter (Vnstock Solution Architect Optimized)
    logger.info("Retrieving symbols and applying Layer 0 Pre-filter via Insights.screener...")
    symbols = []
    df_screener = None
    try:
        from vnstock_data import Insights
        ins = Insights()
        broad_filter = [
            {
                "name": "marketPrice",
                "conditionOptions": [{"from": 0, "to": 1000000}]
            }
        ]
        
        # Gọi API lấy bảng giá 1500 mã toàn thị trường chỉ trong 1 request (~20s)
        df_screener = ins.screener.filter(filters=broad_filter, limit=2000)
        
        if df_screener is not None and not df_screener.empty:
            # Lọc sàn HOSE/HNX từ config.EXCHANGES
            exchanges_lower = [e.lower() for e in config.EXCHANGES]
            # Hỗ trợ cả định dạng 'hose' và 'hsx' để tương thích chéo với các nguồn API khác nhau
            mapped_exchanges = []
            for e in exchanges_lower:
                mapped_exchanges.append(e)
                if e == 'hose' and 'hsx' not in mapped_exchanges:
                    mapped_exchanges.append('hsx')
                elif e == 'hsx' and 'hose' not in mapped_exchanges:
                    mapped_exchanges.append('hose')
            
            df_filtered = df_screener[df_screener['exchange'].str.lower().isin(mapped_exchanges)]
            # Giới hạn mã 3 ký tự (loại bỏ Chứng quyền & ETF)
            df_filtered = df_filtered[df_filtered['symbol'].str.len() == 3]
            
            # Áp dụng Pandas OR để giữ lại các mã có thanh khoản đủ lớn, có hoạt động giao dịch
            # Bộ lọc 1 yêu cầu Vol MA20 > 1M -> Hôm nay accumulated_volume > 300k
            cond_f1 = df_filtered['accumulated_volume'] > 300000
            
            # Bộ lọc 2 yêu cầu Vol MA10 > 500k và Giá trị GD > 10 Tỷ -> Hôm nay accumulated_volume > 150k và Giá trị GD hôm nay > 3 Tỷ
            cond_f2 = (df_filtered['accumulated_volume'] > 150000) & (df_filtered['accumulated_value'] > 3000000000)
            
            # Bộ lọc 3 yêu cầu Vol MA10 > 3M -> Hôm nay accumulated_volume > 1M
            cond_f3 = df_filtered['accumulated_volume'] > 1000000
            
            df_candidates = df_filtered[cond_f1 | cond_f2 | cond_f3]
            symbols = df_candidates['symbol'].tolist()
            logger.info(f"Layer 0 Pre-filter completed. Successfully reduced from {len(df_filtered)} to {len(symbols)} active candidate symbols!")
        else:
            logger.warning("Screener returned empty DataFrame. Falling back to traditional listing...")
    except Exception as e:
        logger.error(f"Failed to run Layer 0 Pre-filter: {e}. Falling back to traditional listing...")
        symbols = []

    # Nếu pre-filter bị lỗi hoặc rỗng, kích hoạt fallback truyền thống
    if not symbols:
        logger.info("Executing traditional fallback symbol retrieval...")
        all_symbols = []
        for exchange in config.EXCHANGES:
            exchange_symbols = get_exchange_symbols(exchange)
            logger.info(f"Retrieved {len(exchange_symbols)} symbols from {exchange}")
            all_symbols.extend(exchange_symbols)
        symbols = [s for s in list(set(all_symbols)) if isinstance(s, str) and len(s) == 3]
        logger.info(f"Total fallback unique symbols: {len(symbols)}")
            
    if not symbols:
        logger.error("No symbols to scan. Aborting.")
        return {'Tích lũy phá nền': [], 'Hổ gặp nạn': [], 'Vua sập bẫy': []}
        
    # Candidates results mapping
    candidates = {
        'Tích lũy phá nền': [],
        'Hổ gặp nạn': [],
        'Vua sập bẫy': []
    }
    
    # 3. Main processing loop for symbols
    total = len(symbols)
    logger.info(f"Beginning scan on {total} symbols...")
    
    for idx, symbol in enumerate(symbols):
        try:
            # 3.1 Fetch lightweight 1Y OHLCV
            df_ohlcv = fetch_ohlcv(symbol, length='1Y')
            
            # 3.2 Pre-filtering
            passed_pre, pre_details = check_pre_filters(symbol, df_ohlcv, df_benchmark)
            if not passed_pre:
                # Silently skip, data_fetcher fetch_ohlcv has already slept for 0.3s internally.
                continue
                
            pre_calc = pre_details['pre_calc']
            pass_pre_f1 = pre_details['pass_pre_f1']
            pass_pre_f2 = pre_details['pass_pre_f2']
            pass_pre_f3 = pre_details['pass_pre_f3']
            
            logger.info(f"[{idx+1}/{total}] Symbol {symbol} passed pre-filtering! Detailed checks starting...")
            
            # 3.3 Fetch heavier properties only for pre-filtered targets to avoid rate limits
            df_vol_profile = fetch_volume_profile(symbol)
            active_buy_pct = calc_active_buy_pct(df_vol_profile)
            
            pb = 999.0
            summary = None
            if pass_pre_f3:
                summary = fetch_summary(symbol)
                if summary is not None and not summary.empty and 'pb' in summary.columns:
                    pb_val = summary['pb'].iloc[-1]
                    try:
                        pb = float(pb_val) if pb_val is not None else 999.0
                    except (ValueError, TypeError):
                        pb = 999.0
            
            # Khởi tạo scorecard tạm thời với rs_avg để tránh NameError và đồng bộ hóa chỉ số RS Percentile
            scorecard = {'rs_avg': pre_calc.get('rs_avg', 0)}
            if df_screener is not None and not df_screener.empty:
                symbol_screener = df_screener[df_screener['symbol'] == symbol]
                if not symbol_screener.empty and 'stock_strength' in symbol_screener.columns:
                    val = symbol_screener['stock_strength'].iloc[0]
                    if pd.notna(val):
                        scorecard['rs_avg'] = float(val)

            # 3.4 Strict Filters verification
            # Lấy điểm Percentile Rank (stock_strength) đã được ghi đè để lọc tinh chặt chẽ
            rs_val = scorecard.get('rs_avg', 0)
            is_f1 = pass_pre_f1 and (42 <= active_buy_pct <= 55) and (25 <= rs_val <= 45)
            is_f2 = pass_pre_f2 and (42 <= active_buy_pct <= 55) and (rs_val > 45)
            is_f3 = pass_pre_f3 and (pb < 1.1) and (active_buy_pct > 50)
            
            # 3.5 If strictly passed any filter, complete the full scorecard details
            if is_f1 or is_f2 or is_f3:
                logger.info(f"🎯 Symbol {symbol} MATCHED criteria. Filter 1: {is_f1}, Filter 2: {is_f2}, Filter 3: {is_f3}")
                
                df_ohlcv_long = fetch_ohlcv_long(symbol)
                df_foreign = fetch_foreign_flow(symbol, days=30)
                quote = fetch_quote(symbol)
                if summary is None:
                    summary = fetch_summary(symbol)
                    
                # Build unified scorecard
                scorecard = build_scorecard(
                    symbol, df_ohlcv, df_benchmark,
                    df_ohlcv_long=df_ohlcv_long,
                    df_vol_profile=df_vol_profile,
                    df_foreign=df_foreign,
                    quote=quote,
                    summary=summary
                )
                
                # Ghi đè rs_avg bằng điểm Percentile Rank (stock_strength) có sẵn từ Screener (TCBS/VCI Synced)
                if df_screener is not None and not df_screener.empty:
                    symbol_screener = df_screener[df_screener['symbol'] == symbol]
                    if not symbol_screener.empty and 'stock_strength' in symbol_screener.columns:
                        val = symbol_screener['stock_strength'].iloc[0]
                        if pd.notna(val):
                            scorecard['rs_avg'] = float(val)
                
                # Append pre-calculated fields
                scorecard['trading_value_billion'] = pre_calc['trading_value_billion']
                
                # Add rule-based buy signal mapping
                strat = evaluate_strategy(scorecard)
                scorecard['strategy_signal'] = strat.get('signal', 'Không có tín hiệu')
                
                # Format to Vietnamese scorecard dictionary (skipped to keep native english keys in raw candidate scorecards)
                
                # Append to corresponding candidates list
                if is_f1:
                    candidates['Tích lũy phá nền'].append((symbol, scorecard))
                if is_f2:
                    candidates['Hổ gặp nạn'].append((symbol, scorecard))
                if is_f3:
                    candidates['Vua sập bẫy'].append((symbol, scorecard))
                    
        except Exception as e:
            logger.error(f"Error scanning symbol {symbol}: {e}")
            time.sleep(0.3)  # Small safety sleep on error to protect rate limits
            
    logger.info("Scan completed successfully!")
    logger.info(f"Results summary:")
    for f_name, matches in candidates.items():
        logger.info(f" - {f_name}: {len(matches)} symbols matched.")
        
    return candidates

if __name__ == '__main__':
    # Test scan on execution
    print("Testing scanner run...")
    results = run_scan()
    print("Test finished. Results:")
    for k, v in results.items():
        print(f"Filter '{k}': {[sym for sym, _ in v]}")
