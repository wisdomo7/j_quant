"""
Mailer — Gmail 자동 발송 모듈
매일 J 엔진 결과를 HTML 리포트로 이메일 발송
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

try:
    from config import EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO
except ImportError:
    print("⚠ config.py 파일이 없습니다. config.py를 생성하고 Gmail 설정을 입력하세요.")
    EMAIL_FROM = EMAIL_PASSWORD = EMAIL_TO = None


def build_html_report(results: dict) -> str:
    """J 엔진 결과를 HTML 이메일 본문으로 변환"""
    now = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

    def render_section(title, stocks, color):
        if not stocks:
            return f"<h3 style='color:{color}'>{title}</h3><p style='color:#94a3b8'>통과 종목 없음</p>"
        rows = ""
        for s in stocks:
            rows += f"""
            <tr>
                <td><b>{s['name']}</b><br><small>{s['code']}</small></td>
                <td style='text-align:center;background:{'#065f46' if s['adjusted_score']>=70 else '#854d0e' if s['adjusted_score']>=50 else '#7f1d1d'};color:white;font-weight:700'>{s['adjusted_score']}</td>
                <td style='text-align:right'>{s['price']:,}</td>
                <td style='text-align:center'>{s['rsi']}</td>
                <td style='text-align:right;color:#60a5fa'>{s['targets']['entry']:,}</td>
                <td style='text-align:right;color:#34d399'>{s['targets']['target1']:,}</td>
                <td style='text-align:right;color:#f87171'>{s['targets']['stop']:,}</td>
                <td style='text-align:center;font-weight:700'>{s['targets']['rr']}:1</td>
                <td style='text-align:center;font-size:11px'>{s['suggest_size']}</td>
            </tr>"""
        return f"""
        <h3 style='color:{color}'>{title} ({len(stocks)}종목)</h3>
        <table style='width:100%;border-collapse:collapse;font-size:12px;margin-bottom:20px'>
            <thead>
                <tr style='background:#0f172a;color:#94a3b8'>
                    <th style='padding:8px'>종목</th>
                    <th style='padding:8px'>점수</th>
                    <th style='padding:8px'>현재가</th>
                    <th style='padding:8px'>RSI</th>
                    <th style='padding:8px'>진입가</th>
                    <th style='padding:8px'>1차 목표</th>
                    <th style='padding:8px'>손절가</th>
                    <th style='padding:8px'>손익비</th>
                    <th style='padding:8px'>비중</th>
                </tr>
            </thead>
            <tbody style='background:#1e293b;color:#e2e8f0'>{rows}</tbody>
        </table>
        """

    blocked_html = ""
    if results["blocked"]:
        rows = ""
        for s in results["blocked"][:10]:
            rows += f"<li style='color:#f87171;font-size:12px'><b>{s['name']}</b> ({s['code']}): {s['block_reason']}</li>"
        blocked_html = f"""
        <h3 style='color:#f87171'>🚫 필터 차단 종목 ({len(results['blocked'])}개)</h3>
        <ul style='background:#1e293b;padding:16px;border-radius:6px'>{rows}</ul>
        """

    return f"""
    <!DOCTYPE html>
    <html><head><meta charset='UTF-8'></head>
    <body style='font-family:Malgun Gothic,sans-serif;background:#0a0e1a;color:#e2e8f0;padding:24px;max-width:900px;margin:auto'>
        <div style='background:linear-gradient(135deg,#1e3a5f,#0f172a);padding:24px;border-radius:8px;margin-bottom:20px'>
            <h1 style='color:#60a5fa;margin:0'>📊 J Partner Daily Report</h1>
            <p style='color:#94a3b8;margin-top:8px'>v3.0 · {now} KST</p>
        </div>
        
        <div style='background:#1e293b;padding:16px;border-radius:8px;margin-bottom:20px'>
            <h3 style='color:#818cf8;margin-top:0'>📈 오늘의 시그널 요약</h3>
            <p>🏆 장기 {len(results['long'])}종목 | 📈 스윙 {len(results['swing'])}종목 | ⚡ 단타 {len(results['day'])}종목 | 🚫 차단 {len(results['blocked'])}종목</p>
        </div>

        {render_section('🏆 장기 후보 (Long-term)', results['long'], '#fbbf24')}
        {render_section('📈 스윙 후보 (Swing 2~4주)', results['swing'], '#34d399')}
        {render_section('⚡ 단타 후보 (Day Trading)', results['day'], '#60a5fa')}
        
        {blocked_html}
        
        <div style='background:linear-gradient(135deg,#1e293b,#1e1b4b);padding:16px;border-radius:8px;margin-top:20px;border-left:4px solid #ec4899'>
            <h3 style='color:#f472b6;margin-top:0'>🎯 핵심 액션</h3>
            <p>관망 + 우선순위 실행 · 481만원의 30%(약 144만)만 1차 진입 · 현대차 절대 매도 금지</p>
        </div>
        
        <hr style='border-color:#334155;margin:24px 0'>
        <p style='color:#475569;font-size:10px;text-align:center'>
            J Partner Quant v3.0 · 모든 매매 전 HTS 실시간 가격 직접 확인 필수<br>
            본 리포트는 의사결정 보조용이며 최종 책임은 사용자 본인에게 있습니다
        </p>
    </body></html>
    """


def send_daily_report(results: dict, subject: str = None) -> bool:
    """일일 리포트 이메일 발송"""
    if not all([EMAIL_FROM, EMAIL_PASSWORD, EMAIL_TO]):
        print("⚠ config.py 설정이 완료되지 않았습니다.")
        return False

    if subject is None:
        subject = f"📊 J Partner Daily Report — {datetime.now().strftime('%Y-%m-%d')}"

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject

    html_body = build_html_report(results)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"✓ 이메일 발송 완료 → {EMAIL_TO}")
        return True
    except Exception as e:
        print(f"⚠ 이메일 발송 실패: {e}")
        return False


if __name__ == "__main__":
    # 테스트 발송
    from j_engine import analyze_results

    test_data = [
        {"code": "005380", "name": "현대차", "price": 661000, "rsi": 62, "volume": 3.2, "deal_vol": 850, "margin_pct": 8.5, "yoy_pct": 25, "foreign_buy_3d": True, "atr_pct": 4.5, "track": "long"},
        {"code": "036570", "name": "NC소프트", "price": 255000, "rsi": 51, "volume": 2.5, "deal_vol": 200, "margin_pct": 18, "yoy_pct": 2856, "foreign_buy_3d": False, "atr_pct": 5.2, "track": "long"},
    ]
    results = analyze_results(test_data)
    send_daily_report(results)
