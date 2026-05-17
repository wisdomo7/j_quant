"""
Data Collector v5.0 — yfinance + FDR 기반
============================================================
pykrx 의존 제거, Python 3.14 호환, KRX 인증 불필요
당일 장 마감 데이터를 곧바로 가져올 수 있음
============================================================
"""

from datetime import datetime, timedelta
import time
import pandas as pd
import numpy as np

try:
    import yfinance as yf
    import FinanceDataReader as fdr
except ImportError:
    print("⚠ 필수 라이브러리 미설치. 다음 명령으로 설치하세요:")
    print("    pip install yfinance FinanceDataReader")
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


def code_to_yf_ticker(code, master=None):
    """종목코드 → yfinance ticker (코스피=.KS, 코스닥=.KQ)"""
    if master is None:
        master = {}
    market = ""
    if code in master:
        info = master[code]
        if isinstance(info, dict):
            market = info.get("market", "")
    
    if market == "KOSDAQ":
        return f"{code}.KQ"
    return f"{code}.KS"


# ============================================================
# 거래일 (yfinance 기반)
# ============================================================
def get_safe_trading_days(days_back=30):
    """yfinance로 거래일 추출 (삼성전자 차트 기준)"""
    try:
        df = yf.Ticker("005930.KS").history(
            period=f"{days_back + 20}d", 
            auto_adjust=False
        )
        if df is None or len(df) == 0:
            raise ValueError("거래일 조회 결과 없음")
        
        days = [d.strftime("%Y%m%d") for d in df.index[-days_back:]]
        if days:
            return days
        raise ValueError("거래일 추출 실패")
    
    except Exception as e:
        print(f"  ⚠ 거래일 조회 실패, 폴백 모드: {e}")
        fallback = []
        current = datetime.now() - timedelta(days=1)
        while len(fallback) < days_back:
            if current.weekday() < 5:
                fallback.append(current.strftime("%Y%m%d"))
            current -= timedelta(days=1)
        return list(reversed(fallback))


# ============================================================
# 기술 지표 (v4 동일)
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
# yfinance Batch OHLCV (핵심)
# ============================================================
def batch_download_ohlcv(codes, days_back=30, master=None, chunk_size=50):
    """다수 종목 일괄 OHLCV - chunk 단위로 batch 다운로드"""
    if master is None:
        master = {}
    
    all_data = {}
    period = f"{days_back + 5}d"
    total_chunks = (len(codes) + chunk_size - 1) // chunk_size
    
    for chunk_idx, i in enumerate(range(0, len(codes), chunk_size)):
        chunk_codes = codes[i:i + chunk_size]
        tickers = [code_to_yf_ticker(c, master) for c in chunk_codes]
        
        print(f"    📥 Batch {chunk_idx+1}/{total_chunks} ({len(chunk_codes)}개)...")
        
        try:
            df = yf.download(
                tickers, 
                period=period, 
                group_by="ticker", 
                progress=False, 
                threads=True, 
                auto_adjust=False
            )
            
            for code, ticker in zip(chunk_codes, tickers):
                try:
                    if len(tickers) == 1:
                        sub_df = df.copy()
                    else:
                        if ticker not in df.columns.get_level_values(0):
                            continue
                        sub_df = df[ticker].copy()
                    
                    sub_df = sub_df.dropna(how='all')
                    if len(sub_df) < 5:
                        continue
                    
                    sub_df = sub_df.rename(columns={
                        "Open": "시가",
                        "High": "고가",
                        "Low": "저가",
                        "Close": "종가",
                        "Volume": "거래량",
                    })
                    sub_df["거래대금"] = sub_df["종가"] * sub_df["거래량"]
                    all_data[code] = sub_df
                except Exception:
                    continue
        
        except Exception as e:
            print(f"    ⚠ Batch {chunk_idx+1} 실패: {type(e).__name__}: {str(e)[:60]}")
        
        # Rate limit 방지
        if chunk_idx + 1 < total_chunks:
            time.sleep(0.5)
    
    return all_data


# ============================================================
# 펀더멘털 (yfinance.info)
# ============================================================
def fetch_fundamentals(code, master=None):
    """yfinance.info에서 PER/PBR/EPS (한국 종목은 제한적)"""
    ticker = code_to_yf_ticker(code, master)
    try:
        info = yf.Ticker(ticker).info
        per = info.get("trailingPE", 0) or 0
        pbr = info.get("priceToBook", 0) or 0
        eps = info.get("trailingEps", 0) or 0
        
        per = validate_number(per, 0, 0, 1000)
        pbr = validate_number(pbr, 0, 0, 100)
        eps = validate_int(eps, 0)
        
        return {"per": per, "pbr": pbr, "eps": eps}
    except Exception:
        return {"per": 0, "pbr": 0, "eps": 0}


def fetch_supply(code, today):
    """외국인/기관 수급 - yfinance 미지원, v6에서 네이버금융 크롤링 추가 예정"""
    return {"foreign_buy_3d": False, "inst_buy_3d": False}


# ============================================================
# Layer 1: 캐시 기반 시가총액 필터
# ============================================================
def layer1_market_filter(date_str, master, min_market_cap=500, min_deal_vol=10):
    print(f"📡 Layer 1: 캐시 기반 광역 스캔 (시총 {min_market_cap}억+)")
    
    candidates = []
    big_codes = get_codes_by_marcap(min_market_cap, master)
    
    if not big_codes:
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
# Layer 2: yfinance Batch OHLCV + 신호 감지
# ============================================================
def layer2_signal_detect(candidates, days, master, min_volume_ratio=1.5, min_deal_vol=10):
    print(f"🔍 Layer 2: yfinance Batch + 거래대금({min_deal_vol}억+) + 신호 감지")
    
    if not candidates:
        return []
    
    codes = [c["code"] for c in candidates]
    
    print(f"  📥 OHLCV 배치 다운로드 ({len(codes)}개)...")
    start_time = time.time()
    all_ohlcv = batch_download_ohlcv(codes, days_back=30, master=master, chunk_size=50)
    elapsed = time.time() - start_time
    print(f"  ✓ 다운로드 완료: {len(all_ohlcv)}개 ({elapsed:.1f}초)")
    
    signals = []
    total = len(candidates)
    failed = 0
    
    for i, cand in enumerate(candidates):
        if i % 100 == 0 and i > 0:
            print(f"  분석: {i}/{total} ({i*100//max(total,1)}%) · 통과 {len(signals)}개")
        
        try:
            code = cand["code"]
            ohlcv = all_ohlcv.get(code)
            
            if not is_valid_ohlcv(ohlcv):
                failed += 1
                continue
            
            today_close = validate_int(safe_get_col(ohlcv, "종가", -1, 0), 0, 1)
            if today_close == 0:
                continue
            
            deal_vol_raw = safe_get_col(ohlcv, "거래대금", -1, 0)
            if deal_vol_raw == 0:
                vol_today = safe_get_col(ohlcv, "거래량", -1, 0)
                deal_vol_raw = vol_today * today_close
            
            deal_vol_eok = deal_vol_raw / 1e8
            
            if deal_vol_eok < min_deal_vol:
                continue
            
            vol_ratio = calc_volume_ratio(ohlcv["거래량"])
            yest_close = validate_number(safe_get_col(ohlcv, "종가", -2, today_close), today_close, 0)
            change_pct = round((today_close - yest_close) / yest_close * 100, 2) if yest_close > 0 else 0.0
            
            high_30d = float(ohlcv["고가"].max()) if "고가" in ohlcv.columns else today_close
            near_high = today_close >= high_30d * 0.97 if high_30d > 0 else False
            
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
# Layer 3: 펀더멘털 (yfinance.info)
# ============================================================
def layer3_enrich(signals, today, master=None):
    print(f"📊 Layer 3: 펀더멘털 보강 (yfinance.info)")
    
    enriched = []
    total = len(signals)
    
    for i, s in enumerate(signals):
        if i % 30 == 0:
            print(f"  진행: {i}/{total} ({i*100//max(total,1)}%)")
        
        try:
            code = s["code"]
            
            fund = fetch_fundamentals(code, master)
            s["per"] = fund["per"]
            s["pbr"] = fund["pbr"]
            s["eps"] = fund["eps"]
            
            if 0 < s["per"] < 30:
                s["margin_pct"] = round(100 / s["per"], 1)
                s["yoy_pct"] = 20
            else:
                s["margin_pct"] = 0
                s["yoy_pct"] = 0
            
            # 수급은 v5에서 일단 False (v6에서 네이버금융 크롤링 추가 예정)
            s["foreign_buy_3d"] = False
            s["inst_buy_3d"] = False
            
            enriched.append(s)
            time.sleep(0.05)  # Rate limit 완화
        except Exception:
            continue
    
    print(f"  ✓ Layer 3 통과: {len(enriched)}개")
    return enriched


# ============================================================
# 전체 스마트 스캔
# ============================================================
def smart_scan_all(min_market_cap=500, min_deal_vol=10, min_volume_ratio=1.5):
    """4단계 스마트 스캐닝 - v5.0 (yfinance + FDR)"""
    print("=" * 60)
    print(f"  J Quant System v5.0 — yfinance + FDR")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    master = get_master_data()
    print(f"📚 종목 마스터: {len(master)}개")
    
    with_cap = sum(1 for v in master.values() if isinstance(v, dict) and v.get("marcap", 0) > 0)
    print(f"   시가총액 포함: {with_cap}개")
    
    days = get_safe_trading_days(30)
    if not days:
        print("⚠ 거래일 없음")
        return []
    
    today = days[-1]
    print(f"기준일: {today}\n")
    
    # Layer 1: 시총 필터
    candidates = layer1_market_filter(today, master, min_market_cap, min_deal_vol)
    if not candidates:
        return []
    
    # Layer 2: OHLCV + 신호
    signals = layer2_signal_detect(candidates, days, master, min_volume_ratio, min_deal_vol)
    if not signals:
        print("⚠ 신호 종목 없음")
        return []
    
    # Layer 3: 펀더멘털
    enriched = layer3_enrich(signals, today, master)
    
    print("\n" + "=" * 60)
    print(f"  ✅ Smart Scanning 완료: {len(enriched)}개")
    print("=" * 60)
    
    return enriched


# ============================================================
# 빠른 모드 (관심 종목)
# ============================================================
def quick_collect_watchlist(codes):
    """관심 종목 빠르게 수집 - yfinance batch"""
    master = get_master_data()
    print(f"📚 종목 마스터: {len(master)}개")
    
    days = get_safe_trading_days(30)
    if not days:
        return []
    
    today = days[-1]
    results = []
    
    print(f"📊 빠른 수집: {len(codes)}개 종목 (기준일: {today})")
    
    # Batch download
    all_ohlcv = batch_download_ohlcv(codes, days_back=30, master=master, chunk_size=50)
    
    for code in codes:
        try:
            name = get_stock_name(code, master)
            if not name or name == code:
                name = code  # 마스터에 없으면 코드로 대체
            
            ohlcv = all_ohlcv.get(code)
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
            
            fund = fetch_fundamentals(code, master)
            
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
                "foreign_buy_3d": False,
                "inst_buy_3d": False,
                "near_52w_high": near_high,
            })
            print(f"  ✓ {name}({code}): {price:,}원 RSI {rsi}")
            
        except Exception as e:
            err_type = type(e).__name__
            err_msg = str(e)[:60]
            print(f"  ⚠ {code} 실패 [{err_type}]: {err_msg}")
            continue
    
    print(f"\n수집 완료: {len(results)}/{len(codes)}개")
    return results


# ============================================================
# 단독 실행 테스트
# ============================================================
if __name__ == "__main__":
    print("=== v5.0 빠른 수집 테스트 ===\n")
    test_codes = [
        "005930",  # 삼성전자
        "000660",  # SK하이닉스
        "005380",  # 현대차
        "034020",  # 두산에너빌리티
        "042660",  # 한화오션
    ]
    results = quick_collect_watchlist(test_codes)
    print(f"\n--- 최종 결과 ({len(results)}개) ---")
    for r in results:
        print(f"  {r['name']:15s} 가격{r['price']:>10,}원 RSI{r['rsi']:5.1f} 거래대금{r['deal_vol']:>5,}억")
