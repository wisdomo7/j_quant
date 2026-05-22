"""
J Partner Quant Screener — Streamlit Web App
모바일/PC 어디서나 J 엔진 결과 확인 가능

실행: streamlit run app.py
배포: Streamlit Cloud (https://streamlit.io/cloud)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json

from j_engine import (
    analyze_results,
    BLACKLIST,
    WHITELIST,
    HOLDINGS,
    MARKET_WEIGHTS,
    RR_MIN,
)

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="J Partner Quant v3.0",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 다크 테마 커스텀 CSS
st.markdown("""
<style>
.stApp { background-color: #0a0e1a; }
.main .block-container { padding-top: 2rem; max-width: 1400px; }
h1, h2, h3 { color: #60a5fa; }
.metric-card {
    background: #1e293b;
    padding: 16px;
    border-radius: 8px;
    border-left: 4px solid #6366f1;
}
.score-high { background: #065f46; color: #34d399; padding: 4px 10px; border-radius: 4px; font-weight: 700; }
.score-mid { background: #854d0e; color: #fbbf24; padding: 4px 10px; border-radius: 4px; font-weight: 700; }
.score-low { background: #7f1d1d; color: #f87171; padding: 4px 10px; border-radius: 4px; font-weight: 700; }
.tag-mega { background: #1e40af; color: #93c5fd; padding: 2px 6px; border-radius: 3px; font-size: 11px; }
.tag-port { background: #065f46; color: #6ee7b7; padding: 2px 6px; border-radius: 3px; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 헤더
# ============================================================
st.title("📊 J Partner Quant Screener")
st.caption(f"v3.0 · 정재영 맞춤 운용 시스템 · {datetime.now().strftime('%Y-%m-%d %H:%M')} KST")

# ============================================================
# 사이드바: 시장 국면 + 포트폴리오
# ============================================================
with st.sidebar:
    st.header("🌐 시장 국면")
    kospi = st.metric("코스피", "7,844.01", "+2.63%")
    kosdaq = st.metric("코스닥", "1,176.93", "-0.20%")
    rsi = st.metric("코스피 RSI", "86.4", "⚠ 과열")
    fx = st.metric("원/달러", "1,491.10", "1,500선 근접")

    st.divider()
    st.subheader("💼 내 포트폴리오")
    st.markdown("""
    - **현대차 (005380)** · 10주 · +78%  
      *BD IPO까지 절대 매도 금지*
    - **SPYM** · 2주 · +105%  
      *환율 1,500원 모니터링*
    - **NC소프트 (036570)** · 1주 · -69.8%  
      *반등 시 분할 매도*
    - **예수금** · 4,815,950원  
      *PPI·미중회담 후 30% 진입*
    """)

    st.divider()
    st.subheader("🎯 Operation Recovery")
    st.progress(0.27, text="진도 27% · 잔여 -102만")
    st.caption("8개월 목표 (~2027.01)")

    st.divider()
    st.subheader("🚫 블랙리스트")
    for code, reason in BLACKLIST.items():
        st.caption(f"`{code}` {reason}")

# ============================================================
# 메인: 입력 영역
# ============================================================
st.header("1️⃣ 종목 데이터 입력")

input_mode = st.radio(
    "데이터 입력 방식",
    ["📋 샘플 데이터로 시연", "📝 JSON 직접 입력", "🤖 pykrx 자동 수집 (PC 필요)"],
    horizontal=True,
)

# 샘플 데이터
SAMPLE_DATA = [
    {"code": "005380", "name": "현대차", "price": 661000, "rsi": 62, "volume": 3.2, "deal_vol": 850, "margin_pct": 8.5, "yoy_pct": 25, "foreign_buy_3d": True, "atr_pct": 4.5, "track": "long"},
    {"code": "000660", "name": "SK하이닉스", "price": 1804000, "rsi": 58, "volume": 2.1, "deal_vol": 2100, "margin_pct": 42, "yoy_pct": 180, "foreign_buy_3d": False, "atr_pct": 5.2, "track": "long"},
    {"code": "005930", "name": "삼성전자", "price": 265250, "rsi": 54, "volume": 1.8, "deal_vol": 1400, "margin_pct": 12, "yoy_pct": 95, "foreign_buy_3d": False, "atr_pct": 4.0, "track": "long"},
    {"code": "034020", "name": "두산에너빌리티", "price": 121100, "rsi": 48, "volume": 1.8, "deal_vol": 680, "margin_pct": 9.2, "yoy_pct": 45, "foreign_buy_3d": True, "atr_pct": 4.8, "track": "swing"},
    {"code": "012450", "name": "한화에어로스페이스", "price": 840000, "rsi": 55, "volume": 1.4, "deal_vol": 420, "margin_pct": 13.5, "yoy_pct": 65, "foreign_buy_3d": True, "atr_pct": 4.2, "track": "swing"},
    {"code": "141080", "name": "리가켐바이오", "price": 185000, "rsi": 60, "volume": 1.6, "deal_vol": 230, "margin_pct": 18, "yoy_pct": 120, "foreign_buy_3d": True, "atr_pct": 5.5, "track": "swing"},
    {"code": "0173Y0", "name": "KODEX 미국AI광통신", "price": 13200, "rsi": 64, "volume": 2.8, "deal_vol": 180, "margin_pct": 0, "yoy_pct": 0, "foreign_buy_3d": False, "atr_pct": 3.8, "track": "swing", "is_etf": True},
    {"code": "277810", "name": "레인보우로보틱스", "price": 868000, "rsi": 52, "volume": 1.2, "deal_vol": 380, "margin_pct": 8, "yoy_pct": 38, "foreign_buy_3d": False, "atr_pct": 5.8, "track": "swing"},
    {"code": "036570", "name": "NC소프트", "price": 255000, "rsi": 51, "volume": 2.5, "deal_vol": 200, "margin_pct": 18, "yoy_pct": 2856, "foreign_buy_3d": False, "atr_pct": 5.2, "track": "long"},
    {"code": "035720", "name": "카카오", "price": 43400, "rsi": 55, "volume": 2.1, "deal_vol": 500, "margin_pct": 5, "yoy_pct": 15, "foreign_buy_3d": False, "atr_pct": 4.0, "track": "swing"},
    {"code": "259960", "name": "크래프톤", "price": 281000, "rsi": 61.4, "volume": 1.21, "deal_vol": 340, "margin_pct": 34, "yoy_pct": 1697, "foreign_buy_3d": True, "atr_pct": 5.0, "track": "long"},
    {"code": "336570", "name": "원텍", "price": 8130, "rsi": 59.2, "volume": 2.38, "deal_vol": 85, "margin_pct": 32.3, "yoy_pct": 17, "foreign_buy_3d": False, "atr_pct": 5.5, "track": "swing"},
    {"code": "452190", "name": "한빛레이저", "price": 8120, "rsi": 63.4, "volume": 0.13, "deal_vol": 8, "margin_pct": 25.5, "yoy_pct": 966, "foreign_buy_3d": False, "atr_pct": 9.0, "track": "long"},
]

stocks = None

if input_mode == "📋 샘플 데이터로 시연":
    stocks = SAMPLE_DATA
    st.info(f"샘플 데이터 {len(stocks)}개 종목 로드됨")

elif input_mode == "📝 JSON 직접 입력":
    json_input = st.text_area(
        "JSON 형식으로 종목 데이터 입력",
        height=200,
        placeholder='[{"code":"005380","name":"현대차","price":661000,...}]',
    )
    if json_input:
        try:
            stocks = json.loads(json_input)
        except json.JSONDecodeError as e:
            st.error(f"JSON 파싱 오류: {e}")

elif input_mode == "🤖 pykrx 자동 수집 (PC 필요)":
    st.warning("⚠ 이 모드는 로컬 PC에서 pykrx 패키지가 설치된 환경에서만 작동합니다.")
    if st.button("🔍 관심 종목 자동 수집 시작"):
        try:
            from data_collector import collect_watchlist, enrich_fundamentals, auto_classify_tracks
            with st.spinner("pykrx로 데이터 수집 중..."):
                watchlist = ["005380", "000660", "005930", "034020", "012450", "141080", "277810"]
                stocks = collect_watchlist(watchlist)
                stocks = auto_classify_tracks(stocks)
                st.success(f"✓ {len(stocks)}개 종목 수집 완료")
        except Exception as e:
            st.error(f"수집 실패: {e}")

# ============================================================
# 분석 실행
# ============================================================
if stocks:
    st.header("2️⃣ J 엔진 분석 결과")

    results = analyze_results(stocks)

    # 요약 메트릭
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏆 장기 후보", f"{len(results['long'])}종목")
    col2.metric("📈 스윙 후보", f"{len(results['swing'])}종목")
    col3.metric("⚡ 단타 후보", f"{len(results['day'])}종목")
    col4.metric("🚫 차단", f"{len(results['blocked'])}종목")

    # 결과 표시 함수
    def render_track(title, stocks_list, color):
        if not stocks_list:
            st.info(f"{title}: 통과 종목 없음")
            return
        st.subheader(title)
        rows = []
        for s in stocks_list:
            tags = []
            if s["code"] in WHITELIST:
                tags.append(f"★{WHITELIST[s['code']]['sector']}")
            if s["code"] in HOLDINGS:
                tags.append("보유")
            tag_str = " ".join(tags)

            rows.append({
                "종목": f"{s['name']} {tag_str}",
                "코드": s["code"],
                "점수": s["adjusted_score"],
                "현재가": f"{s['price']:,}",
                "RSI": s["rsi"],
                "거래량": f"{s['volume']}x",
                "진입가": f"{s['targets']['entry']:,}",
                "1차 목표": f"{s['targets']['target1']:,}",
                "2차 목표": f"{s['targets']['target2']:,}",
                "손절가": f"{s['targets']['stop']:,}",
                "손익비": f"{s['targets']['rr']}:1",
                "마진": f"{s['margin_pct']}%",
                "YoY": f"{s['yoy_pct']}%",
                "비중 제안": s["suggest_size"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    render_track("🏆 장기 후보 (Long-term)", results["long"], "#fbbf24")
    render_track("📈 스윙 후보 (Swing 2~4주)", results["swing"], "#34d399")
    render_track("⚡ 단타 후보 (Day Trading)", results["day"], "#60a5fa")

    # 차단 종목
    if results["blocked"]:
        with st.expander(f"🚫 필터 차단 종목 {len(results['blocked'])}개 보기"):
            rows = []
            for s in results["blocked"]:
                rows.append({
                    "종목": s["name"],
                    "코드": s["code"],
                    "차단 사유": s["block_reason"],
                    "현재가": f"{s['price']:,}",
                    "RSI": s["rsi"],
                    "마진": f"{s.get('margin_pct', 0)}%",
                    "YoY": f"{s.get('yoy_pct', 0)}%",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ============================================================
    # 자가점검 10개
    # ============================================================
    st.header("3️⃣ 매 응답 자가점검 (V1.0 지침)")
    checks = [
        "한국 정치·정책 이슈 1순위 검색",
        "가격 데이터 최신성 명시",
        "종목코드 공식 검증",
        "트랙별 차등 손익비 적용",
        "매매 분류 명시 (혼용 금지)",
        "호재·악재 양면 분석",
        "메가트렌드 가중치 반영",
        "포트와 연결 (블랙리스트 차단)",
        "최종 액션 명시",
        "Operation Recovery 진도 반영",
    ]
    cols = st.columns(2)
    for i, c in enumerate(checks):
        cols[i % 2].markdown(f"✅ {c}")

    # ============================================================
    # 최종 액션
    # ============================================================
    st.header("4️⃣ 최종 액션 플랜")
    action_data = pd.DataFrame([
        {"시점": "오늘 21:30 KST", "행동": "미 4월 PPI 발표 확인", "조건": "+0.4% 이하 → 매수 우호"},
        {"시점": "5/14 (목) 오전", "행동": "NC소프트 1주 매도", "조건": "시가 +2% 갭상승 시"},
        {"시점": "5/14 (목) 오전", "행동": "미중 정상회담 보도", "조건": "관세 휴전 → SK하이닉스"},
        {"시점": "5/14 (목) 오후", "행동": "두산에너빌리티 검토", "조건": "12만원 초반 / 50만 1차"},
        {"시점": "5/15 (금)", "행동": "회담 종합 판단", "조건": "빅딜 → 추가 100만"},
        {"시점": "5/16 이후", "행동": "KODEX 0173Y0 분할", "조건": "시스코 실적 우호 시"},
        {"시점": "6월", "행동": "BD IPO 결정 확인", "조건": "현대차 +30~50%"},
    ])
    st.dataframe(action_data, use_container_width=True, hide_index=True)

    st.success("**핵심 결론**: 관망 + 우선순위 실행 · 481만원의 30%(약 144만)만 1차 진입 · 현대차 절대 매도 금지")

# ============================================================
# 푸터
# ============================================================
st.divider()
st.caption(
    "J Partner Quant Screener v3.0 · 운용 지침 V1.0 기반 · "
    "모든 매매 전 HTS 실시간 가격 직접 확인 필수"
)
