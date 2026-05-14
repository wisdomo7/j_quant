"""
J Partner Quant Screener v4.0.2 — Streamlit Cloud Web App
HTML 직접 렌더링으로 pyarrow 호환성 문제 완전 해결
모바일 최적화 + 비밀번호 보호 추가
"""

import streamlit as st
import json
import os
from datetime import datetime

# ============================================================
# 페이지 설정 (모바일 최적화)
# ============================================================
st.set_page_config(
    page_title="J Partner Quant v4.0.2",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",  # 모바일에서 사이드바 자동 접힘
)

# ============================================================
# 비밀번호 보호 (정재영님만 접속 가능)
# ============================================================
def check_password():
    """Streamlit Cloud Secrets에서 비밀번호 가져와서 검증"""
    def password_entered():
        # Streamlit Cloud의 Secrets에서 비밀번호 읽기
        correct_password = st.secrets.get("APP_PASSWORD", "jung2026")
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("""
        <div style="text-align:center; padding:50px 20px;">
            <h1 style="color:#60a5fa;">🎯 J Partner Quant</h1>
            <p style="color:#94a3b8; font-size:14px;">정재영님 전용 시스템</p>
        </div>
        """, unsafe_allow_html=True)
        st.text_input("🔐 비밀번호 입력", type="password", on_change=password_entered, key="password")
        st.stop()
    elif not st.session_state["password_correct"]:
        st.markdown("""
        <div style="text-align:center; padding:50px 20px;">
            <h1 style="color:#60a5fa;">🎯 J Partner Quant</h1>
        </div>
        """, unsafe_allow_html=True)
        st.text_input("🔐 비밀번호 입력", type="password", on_change=password_entered, key="password")
        st.error("❌ 비밀번호가 틀렸습니다")
        st.stop()

# 비밀번호 검증 실행
check_password()

# 비밀번호 통과 후 엔진 import
from j_engine_v4 import analyze_dual_mode, WHITELIST, HOLDINGS, BLACKLIST

st.markdown("""
<style>
.stApp { background-color: #0a0e1a; }
.main .block-container { padding-top: 2rem; max-width: 1600px; }
h1 { color: #60a5fa; }
h2 { color: #34d399; }
h3 { color: #fbbf24; }

.j-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    margin: 8px 0 20px 0;
    color: #e2e8f0;
}
.j-table thead tr {
    background: #1e293b;
    color: #94a3b8;
}
.j-table th {
    padding: 8px 6px;
    text-align: left;
    border-bottom: 2px solid #334155;
    font-weight: 600;
}
.j-table tbody tr {
    background: #0f172a;
    border-bottom: 1px solid #1e293b;
}
.j-table tbody tr:hover {
    background: #1e293b;
}
.j-table td {
    padding: 8px 6px;
}
.score-high {
    background: #065f46;
    color: #d1fae5;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 700;
    display: inline-block;
}
.score-mid {
    background: #854d0e;
    color: #fef3c7;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 700;
    display: inline-block;
}
.score-low {
    background: #7f1d1d;
    color: #fee2e2;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 700;
    display: inline-block;
}
.mode-conservative {
    background: linear-gradient(135deg, #065f46, #047857);
    padding: 14px;
    border-radius: 8px;
    color: white;
    font-weight: 700;
    text-align: center;
    margin-bottom: 12px;
    font-size: 16px;
}
.mode-aggressive {
    background: linear-gradient(135deg, #7c2d12, #c2410c);
    padding: 14px;
    border-radius: 8px;
    color: white;
    font-weight: 700;
    text-align: center;
    margin-bottom: 12px;
    font-size: 16px;
}
.empty-msg {
    color: #64748b;
    background: #1e293b;
    padding: 16px;
    border-radius: 6px;
    text-align: center;
    margin: 8px 0 20px 0;
}
.sector-tag {
    background: #1e40af;
    color: #dbeafe;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 10px;
    margin-left: 4px;
}
.holding-tag {
    background: #065f46;
    color: #d1fae5;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 10px;
    margin-left: 4px;
}
.price-target { color: #34d399; font-weight: 600; }
.price-stop { color: #f87171; font-weight: 600; }
.price-entry { color: #60a5fa; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 캐시 파일
# ============================================================
CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "latest_scan.json")

# ============================================================
# 헤더
# ============================================================
st.title("🎯 J Partner Quant Screener")
st.caption(f"v4.0.2 · 보수형/공격형 듀얼 분석 · {datetime.now().strftime('%Y-%m-%d %H:%M')} KST")

# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.header("시장 국면")
    st.metric("코스피", "7,844.01", "+2.63%")
    st.metric("코스피 RSI", "86.4", "과열")
    st.metric("원/달러", "1,491.10", "1,500선 근접")
    st.caption("외국인 5월 누적 -16조 매도")

    st.divider()
    st.subheader("내 포트폴리오")
    st.markdown("""
- **현대차** · 10주 · `+78%`
- **SPYM** · 2주 · `+105%`
- **NC** · 1주 · `-69.8%`
- **예수금** · 481만원
""")
    
    st.divider()
    st.subheader("Operation Recovery")
    st.progress(0.27, text="27% · 잔여 -102만")
    
    st.divider()
    st.subheader("자동 차단 종목")
    for code, reason in BLACKLIST.items():
        st.caption(f"`{code}` {reason}")

# ============================================================
# 스캐닝 모드 선택
# ============================================================
st.header("1. 데이터 입력 및 스캐닝")

scan_mode = st.radio(
    "스캐닝 방식 선택",
    [
        "전체 스마트 스캔 (코스피·코스닥 자동 발굴, 3~5분)",
        "관심 종목 빠른 수집 (1분 이내)",
        "샘플 데이터 즉시 분석 (0초)",
        "JSON 직접 입력",
        "마지막 스캔 결과 불러오기",
    ],
)

stocks = None
scan_executed = False

# ============================================================
# 샘플 데이터
# ============================================================
SAMPLE_DATA = [
    {"code": "005380", "name": "현대차", "price": 661000, "rsi": 62, "volume": 3.2, "deal_vol": 850, "margin_pct": 8.5, "yoy_pct": 25, "foreign_buy_3d": True, "inst_buy_3d": True, "atr_pct": 4.5, "near_52w_high": True},
    {"code": "000660", "name": "SK하이닉스", "price": 1804000, "rsi": 58, "volume": 2.1, "deal_vol": 2100, "margin_pct": 42, "yoy_pct": 180, "foreign_buy_3d": False, "inst_buy_3d": True, "atr_pct": 5.2, "near_52w_high": True},
    {"code": "005930", "name": "삼성전자", "price": 265250, "rsi": 54, "volume": 1.8, "deal_vol": 1400, "margin_pct": 12, "yoy_pct": 95, "foreign_buy_3d": False, "inst_buy_3d": False, "atr_pct": 4.0},
    {"code": "034020", "name": "두산에너빌리티", "price": 121100, "rsi": 48, "volume": 1.8, "deal_vol": 680, "margin_pct": 9.2, "yoy_pct": 45, "foreign_buy_3d": True, "inst_buy_3d": True, "atr_pct": 4.8},
    {"code": "012450", "name": "한화에어로스페이스", "price": 840000, "rsi": 55, "volume": 1.4, "deal_vol": 420, "margin_pct": 13.5, "yoy_pct": 65, "foreign_buy_3d": True, "inst_buy_3d": False, "atr_pct": 4.2},
    {"code": "141080", "name": "리가켐바이오", "price": 185000, "rsi": 60, "volume": 1.6, "deal_vol": 230, "margin_pct": 18, "yoy_pct": 120, "foreign_buy_3d": True, "inst_buy_3d": True, "atr_pct": 5.5},
    {"code": "277810", "name": "레인보우로보틱스", "price": 868000, "rsi": 52, "volume": 1.2, "deal_vol": 380, "margin_pct": 8, "yoy_pct": 38, "foreign_buy_3d": False, "inst_buy_3d": False, "atr_pct": 5.8},
    {"code": "138080", "name": "오이솔루션", "price": 32500, "rsi": 58, "volume": 2.0, "deal_vol": 95, "margin_pct": 6.5, "yoy_pct": 35, "foreign_buy_3d": True, "inst_buy_3d": False, "atr_pct": 4.5},
    {"code": "079550", "name": "LIG넥스원", "price": 285000, "rsi": 56, "volume": 1.7, "deal_vol": 280, "margin_pct": 11, "yoy_pct": 50, "foreign_buy_3d": True, "inst_buy_3d": True, "atr_pct": 4.5},
    {"code": "064350", "name": "현대로템", "price": 92000, "rsi": 62, "volume": 2.3, "deal_vol": 180, "margin_pct": 9, "yoy_pct": 80, "foreign_buy_3d": True, "inst_buy_3d": True, "atr_pct": 5.0, "near_52w_high": True},
    {"code": "010120", "name": "LS ELECTRIC", "price": 145000, "rsi": 65, "volume": 3.5, "deal_vol": 320, "margin_pct": 12, "yoy_pct": 110, "foreign_buy_3d": True, "inst_buy_3d": True, "atr_pct": 5.5, "near_52w_high": True},
    {"code": "036570", "name": "NC소프트", "price": 255000, "rsi": 51, "volume": 2.5, "deal_vol": 200, "margin_pct": 18, "yoy_pct": 2856, "foreign_buy_3d": False, "atr_pct": 5.2},
    {"code": "035720", "name": "카카오", "price": 43400, "rsi": 55, "volume": 2.1, "deal_vol": 500, "margin_pct": 5, "yoy_pct": 15, "foreign_buy_3d": False, "atr_pct": 4.0},
]

# ============================================================
# 스캐닝 실행
# ============================================================
if scan_mode.startswith("전체 스마트 스캔"):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("전체 스캔은 코스피·코스닥 약 2,400개 종목을 4단계로 분석합니다. 3~5분 소요됩니다.")
    with col2:
        if st.button("스캔 시작", type="primary", use_container_width=True):
            try:
                from data_collector_v4 import smart_scan_all
                with st.spinner("Layer 1~3 진행 중..."):
                    stocks = smart_scan_all(min_market_cap=500, min_deal_vol=10, min_volume_ratio=1.5)
                    with open(CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump({"timestamp": datetime.now().isoformat(), "stocks": stocks}, f, ensure_ascii=False, default=str)
                    scan_executed = True
                    st.success(f"스캔 완료: {len(stocks)}개")
            except Exception as e:
                st.error(f"스캔 실패: {e}")

elif scan_mode.startswith("관심 종목"):
    if st.button("관심 종목 수집 시작", type="primary"):
        try:
            from data_collector_v4 import quick_collect_watchlist
            watchlist = [
                "005380", "000660", "005930", "034020", "012450",
                "141080", "277810", "138080", "083650", "272210",
                "099320", "012330", "319400", "454910", "079550",
                "064350", "010120", "267260", "010140", "009540",
            ]
            with st.spinner("관심 종목 수집 중..."):
                stocks = quick_collect_watchlist(watchlist)
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump({"timestamp": datetime.now().isoformat(), "stocks": stocks}, f, ensure_ascii=False, default=str)
                scan_executed = True
                st.success(f"수집 완료: {len(stocks)}개")
        except Exception as e:
            st.error(f"수집 실패: {e}")

elif scan_mode.startswith("샘플 데이터"):
    stocks = SAMPLE_DATA
    scan_executed = True

elif scan_mode.startswith("JSON"):
    json_input = st.text_area("JSON 입력", height=200)
    if json_input:
        try:
            stocks = json.loads(json_input)
            scan_executed = True
        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 오류: {e}")

elif scan_mode.startswith("마지막 스캔"):
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
                stocks = cache["stocks"]
                scan_executed = True
                st.info(f"캐시 로드: {cache['timestamp']}")
        except Exception as e:
            st.error(f"캐시 로드 실패: {e}")
    else:
        st.warning("저장된 캐시가 없습니다.")


# ============================================================
# HTML 테이블 직접 생성 (pyarrow 완전 우회)
# ============================================================
def render_stocks_table(stocks_list):
    """HTML 테이블 직접 생성 - pyarrow 사용 안 함"""
    if not stocks_list or len(stocks_list) == 0:
        return '<div class="empty-msg">통과 종목 없음</div>'
    
    rows_html = ""
    for s in stocks_list:
        # 점수 색상 클래스
        score = int(s.get("score", 0))
        if score >= 70:
            score_class = "score-high"
        elif score >= 50:
            score_class = "score-mid"
        else:
            score_class = "score-low"
        
        # 종목명 + 태그
        name = str(s.get("name", "")).replace("<", "").replace(">", "")
        code = str(s.get("code", ""))
        
        # 섹터 태그
        sector_html = ""
        if code in WHITELIST:
            sector = WHITELIST[code]["sector"]
            sector_html = f'<span class="sector-tag">{sector}</span>'
        
        # 보유 태그
        holding_html = ""
        if code in HOLDINGS:
            holding_html = '<span class="holding-tag">보유</span>'
        
        # 가격 데이터 안전 변환
        price = int(s.get("price", 0))
        rsi = float(s.get("rsi", 0))
        volume = float(s.get("volume", 0))
        targets = s.get("targets", {})
        entry = int(targets.get("entry", 0))
        target1 = int(targets.get("target1", 0))
        target2 = int(targets.get("target2", 0))
        stop = int(targets.get("stop", 0))
        rr = float(targets.get("rr", 0))
        suggest = str(s.get("suggest_size", ""))
        
        rows_html += f"""
        <tr>
            <td><b>{name}</b><br><small style='color:#64748b'>{code}</small>{sector_html}{holding_html}</td>
            <td><span class="{score_class}">{score}</span></td>
            <td style='text-align:right'>{price:,}</td>
            <td style='text-align:center'>{rsi:.1f}</td>
            <td style='text-align:center'>{volume:.1f}x</td>
            <td class='price-entry' style='text-align:right'>{entry:,}</td>
            <td class='price-target' style='text-align:right'>{target1:,}</td>
            <td class='price-target' style='text-align:right'>{target2:,}</td>
            <td class='price-stop' style='text-align:right'>{stop:,}</td>
            <td style='text-align:center;font-weight:600'>{rr:.1f}:1</td>
            <td style='font-size:11px'>{suggest}</td>
        </tr>"""
    
    return f"""
    <table class="j-table">
        <thead>
            <tr>
                <th>종목</th>
                <th>점수</th>
                <th style='text-align:right'>현재가</th>
                <th style='text-align:center'>RSI</th>
                <th style='text-align:center'>거래량</th>
                <th style='text-align:right'>진입가</th>
                <th style='text-align:right'>1차목표</th>
                <th style='text-align:right'>2차목표</th>
                <th style='text-align:right'>손절가</th>
                <th style='text-align:center'>손익비</th>
                <th>비중</th>
            </tr>
        </thead>
        <tbody>{rows_html}</tbody>
    </table>
    """


# ============================================================
# 듀얼 모드 분석
# ============================================================
if stocks and scan_executed:
    st.header("2. J 엔진 듀얼 분석")
    
    results = analyze_dual_mode(stocks)
    
    # 요약 메트릭
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("입력 종목", f"{results['total_input']}개")
    col2.metric("보수형 통과", f"{results['conservative']['total']}개")
    col3.metric("공격형 통과", f"{results['aggressive']['total']}개")
    col4.metric("차단", f"{len(results['blocked'])}개")
    
    # 좌우 분할
    col_cons, col_agg = st.columns(2)
    
    with col_cons:
        st.markdown('<div class="mode-conservative">🛡 보수형 (Conservative)</div>', unsafe_allow_html=True)
        
        for track_key, track_label in [("long", "🏆 장기"), ("swing", "📈 스윙"), ("day", "⚡ 단타")]:
            st.subheader(track_label)
            html = render_stocks_table(results["conservative"][track_key])
            st.markdown(html, unsafe_allow_html=True)
    
    with col_agg:
        st.markdown('<div class="mode-aggressive">⚔ 공격형 (Aggressive)</div>', unsafe_allow_html=True)
        
        for track_key, track_label in [("long", "🏆 장기"), ("swing", "📈 스윙"), ("day", "⚡ 단타")]:
            st.subheader(track_label)
            html = render_stocks_table(results["aggressive"][track_key])
            st.markdown(html, unsafe_allow_html=True)
    
    # 차단 종목
    if results["blocked"]:
        with st.expander(f"차단 종목 {len(results['blocked'])}개 보기"):
            blocked_html = "<table class='j-table'><thead><tr><th>종목</th><th>코드</th><th>차단 사유</th><th style='text-align:right'>현재가</th></tr></thead><tbody>"
            for s in results["blocked"]:
                name = str(s.get("name", "")).replace("<", "").replace(">", "")
                blocked_html += f"<tr><td><b>{name}</b></td><td>{s.get('code', '')}</td><td style='color:#f87171'>{s.get('block_reason', '')}</td><td style='text-align:right'>{int(s.get('price', 0)):,}</td></tr>"
            blocked_html += "</tbody></table>"
            st.markdown(blocked_html, unsafe_allow_html=True)

# ============================================================
# 최종 액션
# ============================================================
if stocks and scan_executed:
    st.header("3. 오늘의 핵심 액션")
    
    action_html = """
    <table class="j-table">
        <thead><tr><th>시점</th><th>행동</th><th>조건</th></tr></thead>
        <tbody>
            <tr><td>오늘 21:30</td><td>미 4월 PPI 발표 확인</td><td>+0.4% 이하 → 매수 우호</td></tr>
            <tr><td>5/14 오전</td><td>NC 1주 매도 시도</td><td>시가 +2% 갭상승 시</td></tr>
            <tr><td>5/14 오전</td><td>미중 회담 보도 확인</td><td>관세 휴전 → SK하이닉스</td></tr>
            <tr><td>5/14 오후</td><td>두산E 매수 검토</td><td>12만원 초반 / 50만 1차</td></tr>
            <tr><td>5/15</td><td>회담 종합 판단</td><td>빅딜 → 추가 100만</td></tr>
            <tr><td>6월</td><td>BD IPO 결정 확인</td><td>현대차 보유 유지</td></tr>
        </tbody>
    </table>
    """
    st.markdown(action_html, unsafe_allow_html=True)
    
    st.success("핵심 결론: 관망 + 우선순위 실행 · 481만원의 30%만 1차 진입 · 현대차 절대 매도 금지")

st.divider()
st.caption("J Partner Quant v4.0.2 · 모든 매매 전 HTS 실시간 가격 직접 확인 필수")
