"""
Daily Scheduler v4.0 — 자동 스캔 + 이메일 + 캐시
매일 평일 15:30 자동 실행
"""

import json
import os
import sys
from datetime import datetime

from data_collector_v4 import smart_scan_all, quick_collect_watchlist
from j_engine_v4 import analyze_dual_mode

CACHE_DIR = "cache"
REPORTS_DIR = "reports"
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def save_cache(results, stocks):
    """캐시 파일 저장"""
    cache_path = os.path.join(CACHE_DIR, "latest_scan.json")
    
    cache_data = {
        "timestamp": datetime.now().isoformat(),
        "stocks": stocks,
        "summary": {
            "input": results["total_input"],
            "conservative_pass": results["conservative"]["total"],
            "aggressive_pass": results["aggressive"]["total"],
            "blocked": len(results["blocked"]),
        }
    }
    
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"  ✓ 캐시 저장: {cache_path}")


def build_html_report(results):
    """HTML 리포트 생성"""
    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
    
    def render_block(stocks_list, color, title):
        if not stocks_list:
            return f"<h3 style='color:{color}'>{title}</h3><p>통과 종목 없음</p>"
        rows = ""
        for s in stocks_list[:10]:
            rows += f"""
            <tr>
                <td><b>{s['name']}</b><br><small>{s['code']}</small></td>
                <td style='text-align:center;background:#065f46;color:white;font-weight:700'>{s['score']}</td>
                <td style='text-align:right'>{s['price']:,}</td>
                <td style='text-align:right;color:#60a5fa'>{s['targets']['entry']:,}</td>
                <td style='text-align:right;color:#34d399'>{s['targets']['target1']:,}</td>
                <td style='text-align:right;color:#f87171'>{s['targets']['stop']:,}</td>
                <td style='text-align:center'>{s['targets']['rr']}:1</td>
                <td style='font-size:11px'>{s['suggest_size']}</td>
            </tr>"""
        return f"""
        <h3 style='color:{color}'>{title} ({len(stocks_list)}종목)</h3>
        <table style='width:100%;border-collapse:collapse;font-size:12px;margin-bottom:20px'>
            <thead><tr style='background:#0f172a;color:#94a3b8'>
                <th style='padding:8px'>종목</th><th>점수</th><th>현재가</th>
                <th>진입가</th><th>1차</th><th>손절</th><th>RR</th><th>비중</th>
            </tr></thead>
            <tbody style='background:#1e293b;color:#e2e8f0'>{rows}</tbody>
        </table>
        """
    
    return f"""
    <!DOCTYPE html><html><head><meta charset='UTF-8'></head>
    <body style='font-family:Malgun Gothic,sans-serif;background:#0a0e1a;color:#e2e8f0;padding:24px;max-width:900px;margin:auto'>
        <div style='background:linear-gradient(135deg,#1e3a5f,#0f172a);padding:24px;border-radius:8px;margin-bottom:20px'>
            <h1 style='color:#60a5fa'>🎯 J Partner Daily Report v4.0</h1>
            <p style='color:#94a3b8'>{now} KST · 듀얼 모드 분석</p>
        </div>
        
        <div style='background:#1e293b;padding:16px;border-radius:8px;margin-bottom:20px'>
            <p>📊 입력: {results['total_input']}개 · 보수형 통과: {results['conservative']['total']}개 · 공격형 통과: {results['aggressive']['total']}개 · 차단: {len(results['blocked'])}개</p>
        </div>
        
        <h2 style='color:#34d399'>🛡 보수형 (Conservative)</h2>
        {render_block(results['conservative']['long'], '#fbbf24', '🏆 장기')}
        {render_block(results['conservative']['swing'], '#34d399', '📈 스윙')}
        {render_block(results['conservative']['day'], '#60a5fa', '⚡ 단타')}
        
        <h2 style='color:#f87171'>⚔ 공격형 (Aggressive)</h2>
        {render_block(results['aggressive']['long'], '#fbbf24', '🏆 장기')}
        {render_block(results['aggressive']['swing'], '#34d399', '📈 스윙')}
        {render_block(results['aggressive']['day'], '#60a5fa', '⚡ 단타')}
        
        <div style='background:linear-gradient(135deg,#1e293b,#1e1b4b);padding:16px;border-radius:8px;margin-top:20px;border-left:4px solid #ec4899'>
            <h3 style='color:#f472b6'>🎯 핵심 액션</h3>
            <p>관망 + 우선순위 실행 · 481만원의 30%만 1차 진입 · 현대차 절대 매도 금지</p>
        </div>
        
        <p style='color:#475569;font-size:10px;text-align:center;margin-top:24px'>
            J Partner Quant v4.0 · 모든 매매 전 HTS 가격 직접 확인 필수
        </p>
    </body></html>
    """


def send_email_report(results):
    """이메일 발송 (config.py 사용)"""
    try:
        from config import EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        if EMAIL_FROM in ["본인gmail@gmail.com", ""]:
            print("  ⚠ config.py에 Gmail 정보를 입력하지 않아 이메일을 건너뜁니다.")
            return False
        
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_FROM
        msg["To"] = EMAIL_TO
        msg["Subject"] = f"🎯 J Partner Daily v4.0 — {datetime.now().strftime('%Y-%m-%d')}"
        
        html = build_html_report(results)
        msg.attach(MIMEText(html, "html", "utf-8"))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        
        print(f"  ✓ 이메일 발송 → {EMAIL_TO}")
        return True
    except Exception as e:
        print(f"  ⚠ 이메일 발송 실패: {e}")
        return False


def run_daily_cycle(mode="full"):
    """
    일일 자동 실행 사이클
    mode: "full" (전체 스마트 스캔) 또는 "quick" (관심 종목만)
    """
    print("=" * 60)
    print(f"  J Partner Daily Cycle v4.0")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  모드: {mode}")
    print("=" * 60)
    
    # 1. 데이터 수집
    if mode == "full":
        stocks = smart_scan_all(min_market_cap=500, min_deal_vol=10, min_volume_ratio=1.5)
    else:
        watchlist = [
            "005380", "000660", "005930", "034020", "012450",
            "141080", "277810", "138080", "083650", "272210",
            "099320", "012330", "319400", "454910", "079550",
            "064350", "010120", "267260", "010140", "009540",
        ]
        stocks = quick_collect_watchlist(watchlist)
    
    if not stocks:
        print("⚠ 수집된 데이터가 없습니다.")
        return
    
    # 2. 듀얼 모드 분석
    print(f"\n🧠 듀얼 모드 분석 ({len(stocks)}개)...")
    results = analyze_dual_mode(stocks)
    print(f"  ✓ 보수형 {results['conservative']['total']}개 · 공격형 {results['aggressive']['total']}개 통과")
    
    # 3. 캐시 저장
    save_cache(results, stocks)
    
    # 4. HTML 리포트
    today = datetime.now().strftime("%Y%m%d")
    html_path = os.path.join(REPORTS_DIR, f"report_{today}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(build_html_report(results))
    print(f"  ✓ HTML 저장: {html_path}")
    
    # 5. 이메일 발송
    print(f"\n📧 이메일 발송 시도...")
    send_email_report(results)
    
    print("\n" + "=" * 60)
    print(f"  ✅ Daily Cycle 완료")
    print("=" * 60)


if __name__ == "__main__":
    # 명령행 인수로 모드 선택 가능
    mode = "full"
    if len(sys.argv) > 1 and sys.argv[1] in ["quick", "full"]:
        mode = sys.argv[1]
    
    run_daily_cycle(mode)
