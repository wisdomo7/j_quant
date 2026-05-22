"""
Data Collector — pykrx 기반 자동 데이터 수집기
코스피·코스닥 전체 종목의 가격·RSI·거래량·ATR을 자동으로 가져옴
"""

from datetime import datetime, timedelta
import pandas as pd
import numpy as np

try:
    from pykrx import stock
except ImportError:
    print("⚠ pykrx가 설치되지 않았습니다. 다음 명령으로 설치하세요:")
    print("    pip install pykrx")
    raise


def get_trading_days(days_back: int = 30) -> list:
    """최근 거래일 리스트"""
    today = datetime.now()
    start = today - timedelta(days=days_back + 10)
    days = stock.get_previous_business_days(
        fromdate=start.strftime("%Y%m%d"),
        todate=today.strftime("%Y%m%d")
    )
    return days[-days_back:]


def calc_rsi(prices: pd.Series, period: int = 14) -> float:
    """RSI(14) 계산"""
    if len(prices) < period + 1:
        return 50.0
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(period).mean()
    loss = -delta.where(delta < 0, 0).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 1) if not pd.isna(rsi.iloc[-1]) else 50.0


def calc_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
    """ATR(%) 계산"""
    if len(close) < period + 1:
        return 5.0
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(period).mean().iloc[-1]
    last_close = close.iloc[-1]
    if last_close == 0 or pd.isna(atr):
        return 5.0
    return round(float(atr / last_close * 100), 2)


def calc_volume_ratio(volumes: pd.Series, period: int = 20) -> float:
    """20일 평균 대비 거래량 배수"""
    if len(volumes) < period:
        return 1.0
    avg = volumes.iloc[-period:-1].mean()
    today_vol = volumes.iloc[-1]
    if avg == 0:
        return 1.0
    return round(float(today_vol / avg), 2)


def collect_stock_data(ticker: str, days: list) -> dict | None:
    """단일 종목 데이터 수집"""
    try:
        fromdate = days[0]
        todate = days[-1]

        # 가격 데이터 (OHLCV)
        df = stock.get_market_ohlcv(fromdate, todate, ticker)
        if df.empty or len(df) < 20:
            return None

        # 종목명
        name = stock.get_market_ticker_name(ticker)

        # 현재가 (최근일 종가)
        price = int(df["종가"].iloc[-1])

        # RSI, ATR, 거래량 비율
        rsi = calc_rsi(df["종가"])
        atr = calc_atr(df["고가"], df["저가"], df["종가"])
        vol_ratio = calc_volume_ratio(df["거래량"])

        # 거래대금 (억원)
        deal_vol = int(df["거래대금"].iloc[-1] / 1e8)

        return {
            "code": ticker,
            "name": name,
            "price": price,
            "rsi": rsi,
            "volume": vol_ratio,
            "deal_vol": deal_vol,
            "atr_pct": atr,
            "margin_pct": 0,        # 외부 API 또는 수동 입력 필요
            "yoy_pct": 0,           # 외부 API 또는 수동 입력 필요
            "foreign_buy_3d": False,  # 외국인 수급 별도 조회 필요
        }
    except Exception as e:
        print(f"  ⚠ {ticker} 수집 실패: {e}")
        return None


def collect_all_stocks(max_count: int = None, market: str = "ALL") -> list:
    """
    코스피·코스닥 전체 종목 데이터 수집
    
    Args:
        max_count: 수집 종목 수 제한 (테스트용). None이면 전체
        market: "KOSPI", "KOSDAQ", "ALL"
    """
    print(f"📊 {market} 종목 데이터 수집 시작...")
    
    # 거래일 리스트
    days = get_trading_days(30)
    if not days:
        print("⚠ 거래일 정보를 가져올 수 없습니다")
        return []

    # 종목 코드 리스트
    tickers = []
    if market in ["KOSPI", "ALL"]:
        tickers.extend(stock.get_market_ticker_list(days[-1], market="KOSPI"))
    if market in ["KOSDAQ", "ALL"]:
        tickers.extend(stock.get_market_ticker_list(days[-1], market="KOSDAQ"))

    if max_count:
        tickers = tickers[:max_count]

    print(f"  전체 {len(tickers)}개 종목 스캔")

    results = []
    for i, ticker in enumerate(tickers):
        if i % 100 == 0:
            print(f"  진행: {i}/{len(tickers)} ({i*100//len(tickers)}%)")

        data = collect_stock_data(ticker, days)
        if data:
            results.append(data)

    print(f"✓ 수집 완료: {len(results)}개")
    return results


def collect_watchlist(codes: list) -> list:
    """관심 종목만 빠르게 수집"""
    days = get_trading_days(30)
    results = []
    print(f"📊 관심 종목 {len(codes)}개 수집...")
    for code in codes:
        data = collect_stock_data(code, days)
        if data:
            results.append(data)
            print(f"  ✓ {data['name']} ({code}): {data['price']:,}원, RSI {data['rsi']}")
    return results


# ============================================================
# 펀더멘털·외국인 수급 보강 (KRX 또는 수동 입력)
# ============================================================
def enrich_fundamentals(stocks: list, manual_data: dict = None) -> list:
    """
    펀더멘털·외국인 수급 데이터 보강
    
    manual_data 예시:
        {
            "005380": {"margin_pct": 8.5, "yoy_pct": 25, "foreign_buy_3d": True},
            "000660": {"margin_pct": 42, "yoy_pct": 180, "foreign_buy_3d": False},
        }
    """
    if not manual_data:
        manual_data = {}

    for s in stocks:
        if s["code"] in manual_data:
            s.update(manual_data[s["code"]])
    return stocks


def auto_classify_tracks(stocks: list) -> list:
    """RSI·거래량 기반 트랙 자동 분류 (J 엔진 호출)"""
    from j_engine import auto_classify_track
    for s in stocks:
        s["track"] = auto_classify_track(s)
    return stocks


# ============================================================
# 단독 실행 테스트
# ============================================================
if __name__ == "__main__":
    # 사용자 관심 종목 빠른 수집
    watchlist = [
        "005380",  # 현대차
        "000660",  # SK하이닉스
        "005930",  # 삼성전자
        "034020",  # 두산에너빌리티
        "012450",  # 한화에어로스페이스
        "141080",  # 리가켐바이오
        "277810",  # 레인보우로보틱스
        "319400",  # 현대무벡스
    ]

    stocks = collect_watchlist(watchlist)

    # 펀더멘털 수동 보강 (DART/증권사 리포트 기반)
    manual = {
        "005380": {"margin_pct": 8.5, "yoy_pct": 25, "foreign_buy_3d": True},
        "000660": {"margin_pct": 42, "yoy_pct": 180, "foreign_buy_3d": False},
        "005930": {"margin_pct": 12, "yoy_pct": 95, "foreign_buy_3d": False},
        "034020": {"margin_pct": 9.2, "yoy_pct": 45, "foreign_buy_3d": True},
        "012450": {"margin_pct": 13.5, "yoy_pct": 65, "foreign_buy_3d": True},
        "141080": {"margin_pct": 18, "yoy_pct": 120, "foreign_buy_3d": True},
        "277810": {"margin_pct": 8, "yoy_pct": 38, "foreign_buy_3d": False},
        "319400": {"margin_pct": 8, "yoy_pct": 75, "foreign_buy_3d": False},
    }

    stocks = enrich_fundamentals(stocks, manual)
    stocks = auto_classify_tracks(stocks)

    print("\n--- 수집 결과 ---")
    for s in stocks:
        print(f"{s['name']:20s} {s['price']:>10,}원 RSI {s['rsi']:5.1f} "
              f"마진 {s['margin_pct']:5.1f}% [{s['track']}]")
