"""
Daily Scheduler — 매일 장 마감 후 자동 실행
1. pykrx로 데이터 수집
2. J 엔진 분석
3. 이메일 발송
4. HTML 리포트 저장

실행 방법:
- 수동: python scheduler.py
- 자동: crontab 또는 Windows 작업 스케줄러 등록
"""

import json
import os
from datetime import datetime

from data_collector import collect_watchlist, enrich_fundamentals, auto_classify_tracks
from j_engine import analyze_results
from mailer import send_daily_report, build_html_report


# ============================================================
# 사용자 관심 종목 (필요 시 수정)
# ============================================================
WATCHLIST = [
    # 보유 종목
    "005380",  # 현대차
    "036570",  # NC소프트

    # 메가트렌드 매수 후보
    "000660",  # SK하이닉스
    "005930",  # 삼성전자
    "034020",  # 두산에너빌리티
    "012450",  # 한화에어로스페이스
    "141080",  # 리가켐바이오
    "277810",  # 레인보우로보틱스
    "138080",  # 오이솔루션
    "083650",  # 비에이치아이
    "272210",  # 한화시스템
    "099320",  # 쎄트렉아이
    "012330",  # 현대모비스
    "319400",  # 현대무벡스
    "454910",  # 두산로보틱스
    "259960",  # 크래프톤
]

# ============================================================
# 펀더멘털 수동 데이터 (분기 실적 발표 후 업데이트 필요)
# ============================================================
MANUAL_FUNDAMENTALS = {
    "005380": {"margin_pct": 8.5, "yoy_pct": 25, "foreign_buy_3d": True},
    "000660": {"margin_pct": 42, "yoy_pct": 180, "foreign_buy_3d": False},
    "005930": {"margin_pct": 12, "yoy_pct": 95, "foreign_buy_3d": False},
    "034020": {"margin_pct": 9.2, "yoy_pct": 45, "foreign_buy_3d": True},
    "012450": {"margin_pct": 13.5, "yoy_pct": 65, "foreign_buy_3d": True},
    "141080": {"margin_pct": 18, "yoy_pct": 120, "foreign_buy_3d": True},
    "277810": {"margin_pct": 8, "yoy_pct": 38, "foreign_buy_3d": False},
    "138080": {"margin_pct": 6.5, "yoy_pct": 35, "foreign_buy_3d": True},
    "083650": {"margin_pct": 7, "yoy_pct": 28, "foreign_buy_3d": False},
    "272210": {"margin_pct": 7, "yoy_pct": 28, "foreign_buy_3d": False},
    "099320": {"margin_pct": 5, "yoy_pct": 18, "foreign_buy_3d": False},
    "012330": {"margin_pct": 5.5, "yoy_pct": 22, "foreign_buy_3d": True},
    "319400": {"margin_pct": 8, "yoy_pct": 75, "foreign_buy_3d": False},
    "454910": {"margin_pct": 6, "yoy_pct": 30, "foreign_buy_3d": False},
    "259960": {"margin_pct": 34, "yoy_pct": 1697, "foreign_buy_3d": True},
    "036570": {"margin_pct": 18, "yoy_pct": 2856, "foreign_buy_3d": False},  # 블랙리스트 차단됨
}


def run_daily_cycle():
    """일일 자동 실행 사이클"""
    print("=" * 60)
    print(f"  J Partner Daily Cycle — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # 1. 데이터 수집
    print("\n📊 [1/4] 데이터 수집...")
    stocks = collect_watchlist(WATCHLIST)
    if not stocks:
        print("⚠ 수집된 데이터가 없습니다. 종료.")
        return

    # 2. 펀더멘털 보강
    print("\n📈 [2/4] 펀더멘털 보강...")
    stocks = enrich_fundamentals(stocks, MANUAL_FUNDAMENTALS)
    stocks = auto_classify_tracks(stocks)

    # 3. J 엔진 분석
    print("\n🧠 [3/4] J 엔진 분석...")
    results = analyze_results(stocks)
    print(f"  ✓ 장기 {len(results['long'])}종목 · 스윙 {len(results['swing'])}종목 · "
          f"단타 {len(results['day'])}종목 · 차단 {len(results['blocked'])}종목")

    # 4. HTML 리포트 저장
    html = build_html_report(results)
    today = datetime.now().strftime("%Y%m%d")
    report_path = f"reports/daily_{today}.html"
    os.makedirs("reports", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ HTML 리포트 저장: {report_path}")

    # 5. 이메일 발송
    print("\n📧 [4/4] 이메일 발송...")
    send_daily_report(results)

    # 6. JSON 백업
    json_path = f"reports/daily_{today}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "long_count": len(results["long"]),
            "swing_count": len(results["swing"]),
            "day_count": len(results["day"]),
            "blocked_count": len(results["blocked"]),
            "results": {
                k: [{kk: vv for kk, vv in s.items() if kk != "reasons"} for s in results[k]]
                for k in ["long", "swing", "day", "blocked"]
            },
        }, f, ensure_ascii=False, indent=2, default=str)
    print(f"  ✓ JSON 백업 저장: {json_path}")

    print("\n" + "=" * 60)
    print("  ✅ Daily Cycle 완료")
    print("=" * 60)


if __name__ == "__main__":
    run_daily_cycle()
