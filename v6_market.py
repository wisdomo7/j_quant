"""
v6_market.py - 실시간 시장 지수 수집 (코스피 / 코스닥 / 원·달러)
FinanceDataReader 우선 + yfinance 폴백 (이중 안전망)
app_v6.py의 MarketIndexCollector().get_realtime_index() 호환
"""
from datetime import datetime, timedelta


def _kst_now():
    return datetime.utcnow() + timedelta(hours=9)


class MarketIndexCollector:
    # key: (FinanceDataReader 심볼, yfinance 심볼)
    TARGETS = {
        "kospi":   ("KS11", "^KS11"),
        "kosdaq":  ("KQ11", "^KQ11"),
        "usd_krw": ("USD/KRW", "KRW=X"),
    }

    def get_realtime_index(self):
        """앱이 기대하는 형식으로 반환:
        {'collection_time': '...', 'kospi': {...}, 'kosdaq': {...}, 'usd_krw': {...}}"""
        result = {"collection_time": _kst_now().strftime("%Y-%m-%d %H:%M:%S")}
        for key, (fdr_sym, yf_sym) in self.TARGETS.items():
            data = self._fetch_fdr(fdr_sym)
            if data.get("status") != "success":      # FDR 실패 시 yfinance로 재시도
                data = self._fetch_yf(yf_sym)
            result[key] = data
        return result

    def _fmt(self, last, prev):
        change = (last - prev) / prev * 100 if prev else 0.0
        return {
            "price": f"{last:,.2f}",
            "change": f"{change:+.2f}%",
            "status": "success",
        }

    def _fetch_fdr(self, symbol):
        try:
            import FinanceDataReader as fdr
            start = (_kst_now() - timedelta(days=10)).strftime("%Y-%m-%d")
            df = fdr.DataReader(symbol, start)
            if df is None or len(df) < 2 or "Close" not in df:
                return {"status": "fail"}
            last = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2])
            return self._fmt(last, prev)
        except Exception as e:
            print(f"[FDR 실패] {symbol}: {e}")
            return {"status": "fail"}

    def _fetch_yf(self, symbol):
        try:
            import yfinance as yf
            df = yf.Ticker(symbol).history(period="5d")
            if df is None or len(df) < 2 or "Close" not in df:
                return {"status": "fail"}
            last = float(df["Close"].iloc[-1])
            prev = float(df["Close"].iloc[-2])
            return self._fmt(last, prev)
        except Exception as e:
            print(f"[yfinance 실패] {symbol}: {e}")
            return {"status": "fail"}


# 단독 실행 테스트용
if __name__ == "__main__":
    import json
    print(json.dumps(MarketIndexCollector().get_realtime_index(), ensure_ascii=False, indent=2))
