"""
Data Collector v4.0.6 — 마스터 캐시 기반 Layer 1
KRX 추가 접근 없이 캐시된 시가총액으로 필터링
"""

from datetime import datetime, timedelta
import time
import pandas as pd
import numpy as np

try:
    from pykrx import stock
except ImportError:
    print("⚠ pykrx 미설치")
    raise

from master_data_manager import (
    get_stock_name, get_stock_market, get_stock_marcap,
    get_master_data, get_codes_by_marcap, get_all_codes,
    validate_number, validate_int, validate_bool
)


# ============================================================
# 안전 헬퍼
# ============================================================
def safe_get_col(df, col_name, idx=-1, default=0):
    try:
        if df is None or len(df) == 0:
            return default
        if col_name not in df.columns:
            return default
        val = df[col_name].iloc[idx]
        if pd.isna(val):
            return default
        return float(val)
    except Exception:
        return default


def is_valid_ohlcv(df, min_rows=5):
    if df is None:
        return False
    if len(df) < min_rows:
        return False
    if "종가" not in df.columns:
        return False
    last_close = df["종가"].iloc[-1] if len(df) > 0 else 0
    if pd.isna(last_close) or last_close <= 0:
        return False
    return True


# ============================================================
# 거래일
# ============================================================
def get_safe_trading_days(days_back=30):
    today = datetime.now()
    
    for attempt in range(5):
        try:
            start = today - timedelta(days=days_back + 20)
            days = stock.get_previous_business_days(
                fromdate=start.strftime("%Y%m%d"),
                todate=today.strftime("%Y%m%d")
            )
            if days and len(days) > 0:
                if hasattr(days[0], 'strftime'):
                    days = [d.strftime("%Y%m%d") for d in days]
                return days[-days_back:]
        except Exception as e:
            print(f"  거래일 재시도 {attempt+1}/5: {e}")
            time.sleep(1)
            today = today - timedelta(days=1)
    
    fallback = []
    current = datetime.now() - timedelta(days=1)
    while len(fallback) < days_back:
        if current.weekday() < 5:
            fallback.append(current.strftime("%Y%m%d"))
        current -= timedelta(days=1)
    return list(reversed(fallback))


# ============================================================
# 기술 지표
# ============================================================
def calc_rsi(prices, period=14):
    try:
        if prices is None or len(prices) < period + 1:
            return 50.0
        prices = prices.dropna()
        if len(prices) < period + 1:
            return 50.0
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = -delta.where(delta < 0, 0).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        val = rsi.iloc[-1]
        if pd.isna(val):
            return 50.0
        return round(max(0, min(100, float(val))), 1)
    except Exception:
        return 50.0


def calc_atr(high, low, close, period=14):
    try:
        if close is None or len(close) < period + 1:
            return 5.0
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        atr = tr.rolling(period).mean().iloc[-1]
        last_close = close.iloc[-1]
        if last_close == 0 or pd.isna(atr) or pd.isna(last_close):
            return 5.0
        result = float(atr / last_close * 100)
        return round(max(0.1, min(50, result)), 2)
    except Exception:
        return 5.0


def calc_volume_ratio(volumes, period=20):
    try:
        if volumes is None or len(volumes) < period:
            return 1.0
        avg = volumes.iloc[-period:-1].mean()
        today = volumes.iloc[-1]
        if avg == 0 or pd.isna(avg) or pd.isna(today):
            return 1.0
        result = float(today / avg)
        return round(max(0, min(100, result)), 2)
    except Exception:
        return 1.0


# ============================================================
# 펀더멘털·수급
# ============================================================
def fetch_fundamentals(ticker, today):
    try:
        fund_df = stock.get_market_fundamental(today, today, ticker)
        if fund_df is None or fund_df.empty:
            return {"per": 0, "pbr": 0, "eps": 0}
        per = validate_number(safe_get_col(fund_df, "PER", 0, 0), 0, 0, 1000)
        pbr = validate_number(safe_get_col(fund_df, "PBR", 0, 0), 0, 0, 100)
        eps = validate_int(safe_get_col(fund_df, "EPS", 0, 0), 0)
        return {"per": per, "pbr": pbr, "eps": eps}
    except Exception:
        return {"per": 0, "pbr": 0, "eps": 0}


def fetch_supply(ticker, today):
    try:
        fromdate = (datetime.strptime(today, "%Y%m%d") - timedelta(days=10)).strftime("%Y%m%d")
        trading = stock.get_market_trading_value_by_date(fromdate, today, ticker)
        if trading is None or len(trading) < 3:
            return {"foreign_buy_3d": False, "inst_buy_3d": False}
        
        foreign_3d = False
        inst_3d = False
        
        if "외국인합계" in trading.columns:
            try:
                val = trading["외국인합계"].iloc[-3:].sum()
                foreign_3d = bool(val > 0) if not pd.isna(val) else False
            except Exception:
                foreign_3d = False
        
        if "기관합계" in trading.columns:
            try:
                val = trading["기관합계"].iloc[-3:].sum()
                inst_3d = bool(val > 0) if not pd.isna(val) else False
            except Exception:
                inst_3d = False
        
        return {"foreign_buy_3d": foreign_3d, "inst_buy_3d": inst_3d}
    except Exception:
        return {"foreign_buy_3d": False, "inst_buy_3d": False}


# ============================================================
# Layer 1: 캐시 기반 (KRX 접근 없음)
# ============================================================
def layer1_market_filter(date_str, master, min_market_cap=500, min_deal_vol=10):
    """
    캐시된 시가총액 사용 - KRX 추가 접근 없음
    """
    print(f"📡 Layer 1: 캐시 기반 광역 스캔 (시총 {min_market_cap}억+)")
    
    candidates = []
    
    # 캐시된 시가총액으로 1차 필터
    big_codes = get_codes_by_marcap(min_market_cap, master)
    
    if not big_codes:
        # 시가총액 정보가 캐시에 없으면 전체 종목 사용
        print("  ⚠ 캐시에 시가총액 없음 - 전체 종목으로 진행")
        all_codes = get_all_codes(master)
        for code in all_codes:
            market = get_stock_market(code, master)
            if market in ["KOSPI", "KOSDAQ"]:
                candidates.append({
                    "code": code,
                    "name": get_stock_name(code, master),
                    "market_cap": 0,
                    "deal_vol": 0,
                    "market": market,
                })
    else:
        for code in big_codes:
            info = master.get(code, {})
            cap_eok = info.get("marcap", 0) / 1e8 if info.get("marcap", 0) > 0 else 0
            candidates.append({
                "code": code,
                "name": info.get("name", code),
                "market_cap": round(cap_eok, 0),
                "deal_vol": 0,
                "market": info.get("market", ""),
            })
    
    print(f"  ✓ Layer 1 통과: {len(candidates)}개")
    return candidates


# ============================================================
# Layer 2: 거래대금 + 신호 감지
# ============================================================
def layer2_signal_detect(candidates, days, master, min_volume_ratio=1.5, min_deal_vol=10):
    """OHLCV로 거래대금 + 신호 동시 확인"""
    print(f"🔍 Layer 2: 거래대금({min_deal_vol}억+) + 신호 감지")
    
    today = days[-1]
    signals = []
    total = len(candidates)
    failed = 0
    
    for i, cand in enumerate(candidates):
        if i % 100 == 0:
            print(f"  진행: {i}/{total} ({i*100//max(total,1)}%) · 통과 {len(signals)}개")
        
        try:
            ticker = cand["code"]
            ohlcv = stock.get_market_ohlcv(days[0], today, ticker)
            
            if not is_valid_ohlcv(ohlcv):
                failed += 1
                continue
            
            today_close = validate_int(safe_get_col(ohlcv, "종가", -1, 0), 0, 1)
            if today_close == 0:
                continue
            
            # 거래대금
            deal_vol_raw = safe_get_col(ohlcv, "거래대금", -1, 0)
            if deal_vol_raw == 0:
                vol_today = safe_get_col(ohlcv, "거래량", -1, 0)
                deal_vol_raw = vol_today * today_close
            
            deal_vol_eok = deal_vol_raw / 1e8
            
            if deal_vol_eok < min_deal_vol:
                continue
            
            # 거래량 비율
            vol_ratio = calc_volume_ratio(ohlcv["거래량"])
            
            # 전일 대비
            yest_close = validate_number(safe_get_col(ohlcv, "종가", -2, today_close), today_close, 0)
            change_pct = round((today_close - yest_close) / yest_close * 100, 2) if yest_close > 0 else 0.0
            
            # 신고가
            high_30d = float(ohlcv["고가"].max()) if "고가" in ohlcv.columns else today_close
            near_high = today_close >= high_30d * 0.97 if high_30d > 0 else False
            
            # 신호
            has_signal = (
                vol_ratio >= min_volume_ratio or
                abs(change_pct) >= 5 or
                near_high
            )
            
            if has_signal:
                cand["deal_vol"] = int(deal_vol_eok)
                cand.update({
                    "price": today_close,
                    "volume": vol_ratio,
                    "rsi": calc_rsi(ohlcv["종가"]),
                    "atr_pct": calc_atr(ohlcv["고가"], ohlcv["저가"], ohlcv["종가"]),
                    "change_pct": change_pct,
                    "near_52w_high": near_high,
                })
                signals.append(cand)
        except Exception:
            failed += 1
            continue
    
    print(f"  ✓ Layer 2 통과: {len(signals)}개 (실패 {failed}개)")
    return signals


# ============================================================
# Layer 3: 펀더멘털·수급
# ============================================================
def layer3_enrich(signals, today):
    print(f"📊 Layer 3: 펀더멘털·수급 보강")
    
    enriched = []
    total = len(signals)
    
    for i, s in enumerate(signals):
        if i % 30 == 0:
            print(f"  진행: {i}/{total} ({i*100//max(total,1)}%)")
        
        try:
            ticker = s["code"]
            
            fund = fetch_fundamentals(ticker, today)
            s["per"] = fund["per"]
            s["pbr"] = fund["pbr"]
            s["eps"] = fund["eps"]
            
            if 0 < s["per"] < 30:
                s["margin_pct"] = round(100 / s["per"], 1)
                s["yoy_pct"] = 20
            else:
                s["margin_pct"] = 0
                s["yoy_pct"] = 0
            
            supply = fetch_supply(ticker, today)
            s["foreign_buy_3d"] = supply["foreign_buy_3d"]
            s["inst_buy_3d"] = supply["inst_buy_3d"]
            
            enriched.append(s)
        except Exception:
            continue
    
    print(f"  ✓ Layer 3 통과: {len(enriched)}개")
    return enriched


# ============================================================
# 전체 스마트 스캔
# ============================================================
def smart_scan_all(min_market_cap=500, min_deal_vol=10, min_volume_ratio=1.5):
    """4단계 스마트 스캐닝 - 캐시 기반"""
    print("=" * 60)
    print(f"  J Quant System v4.0.6 — Smart Scanning")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    master = get_master_data()
    print(f"📚 종목 마스터: {len(master)}개")
    
    # 시가총액 캐시 확인
    with_cap = sum(1 for v in master.values() if isinstance(v, dict) and v.get("marcap", 0) > 0)
    print(f"   시가총액 포함: {with_cap}개")
    
    days = get_safe_trading_days(30)
    if not days:
        print("⚠ 거래일 없음")
        return []
    
    today = days[-1]
    print(f"기준일: {today}\n")
    
    # Layer 1
    candidates = layer1_market_filter(today, master, min_market_cap, min_deal_vol)
    if not candidates:
        return []
    
    # Layer 2
    signals = layer2_signal_detect(candidates, days, master, min_volume_ratio, min_deal_vol)
    if not signals:
        print("⚠ 신호 종목 없음")
        return []
    
    # Layer 3
    enriched = layer3_enrich(signals, today)
    
    print("\n" + "=" * 60)
    print(f"  ✅ Smart Scanning 완료: {len(enriched)}개")
    print("=" * 60)
    
    return enriched


# ============================================================
# 빠른 모드
# ============================================================
def quick_collect_watchlist(codes):
    master = get_master_data()
    print(f"📚 종목 마스터: {len(master)}개")
    
    days = get_safe_trading_days(30)
    if not days:
        return []
    
    today = days[-1]
    from_date = days[0]
    results = []
    
    print(f"📊 빠른 수집: {len(codes)}개 종목 (기준일: {today})")
    
    for code in codes:
        try:
            name = get_stock_name(code, master)
            
            ohlcv = stock.get_market_ohlcv(from_date, today, code)
            if not is_valid_ohlcv(ohlcv):
                print(f"  ⚠ {name}({code}) OHLCV 무효")
                continue
            
            price = validate_int(safe_get_col(ohlcv, "종가", -1, 0), 0, 1)
            if price == 0:
                print(f"  ⚠ {name}({code}) 가격 0")
                continue
            
            dv_raw = safe_get_col(ohlcv, "거래대금", -1, 0)
            if dv_raw == 0:
                vol_today = safe_get_col(ohlcv, "거래량", -1, 0)
                dv_raw = vol_today * price
            deal_vol = validate_int(dv_raw / 1e8, 0, 0)
            
            rsi = calc_rsi(ohlcv["종가"])
            vol_ratio = calc_volume_ratio(ohlcv["거래량"])
            
            high_col = ohlcv["고가"] if "고가" in ohlcv.columns else ohlcv["종가"]
            low_col = ohlcv["저가"] if "저가" in ohlcv.columns else ohlcv["종가"]
            atr = calc_atr(high_col, low_col, ohlcv["종가"])
            
            high_30d = float(ohlcv["고가"].max()) if "고가" in ohlcv.columns else price
            near_high = price >= high_30d * 0.97 if high_30d > 0 else False
            
            fund = fetch_fundamentals(code, today)
            supply = fetch_supply(code, today)
            
            results.append({
                "code": code,
                "name": name,
                "price": price,
                "rsi": rsi,
                "volume": vol_ratio,
                "atr_pct": atr,
                "deal_vol": deal_vol,
                "per": fund["per"],
                "pbr": fund["pbr"],
                "margin_pct": round(100 / fund["per"], 1) if 0 < fund["per"] < 30 else 10,
                "yoy_pct": 20,
                "foreign_buy_3d": supply["foreign_buy_3d"],
                "inst_buy_3d": supply["inst_buy_3d"],
                "near_52w_high": near_high,
            })
            print(f"  ✓ {name}({code}): {price:,}원 RSI {rsi} 외국인 {supply['foreign_buy_3d']}")
            
        except Exception as e:
            err_type = type(e).__name__
            err_msg = str(e)[:60]
            print(f"  ⚠ {code} 실패 [{err_type}]: {err_msg}")
            continue
    
    print(f"\n수집 완료: {len(results)}/{len(codes)}개")
    return results


if __name__ == "__main__":
    print("=== v4.0.6 전체 스마트 스캔 테스트 ===\n")
    results = smart_scan_all(min_market_cap=500, min_deal_vol=10, min_volume_ratio=1.5)
    print(f"\n최종: {len(results)}개")
    for r in results[:10]:
        print(f"  {r['name']:15s} 시총{r['market_cap']:>6,.0f}억 거래대금{r['deal_vol']:>4}억 RSI{r['rsi']}")
