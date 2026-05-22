"""
J Partner Quant Screener v5.2
V4.0 듀얼 모드 + V5.2 통합 (분류·6대차단·시장국면·패턴학습)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

from j_engine_v52 import JEngineV52
from v5_filter import JQuantV5Filter
from v51_korea import MarketPhaseAdaptive, PolicyTriggerMatrix
from v52_learning import UserPatternLearner, BacktestingEngine

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(
    page_title="J Partner Quant V5.2",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background-color: #0a0e1a; }
h1, h2, h3 { color: #60a5fa; }
.block-pass { background: #065f46; color: #34d399; padding: 8px; border-radius: 4px; }
.block-fail { background: #7f1d1d; color: #f87171; padding: 8px; border-radius: 4px; }
.v5-bonus { background: #1e40af; color: #93c5fd; padding: 2px 8px; border-radius: 3px; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 헤더
# ============================================================
st.title("🎯 J Partner Quant V5.2")
st.caption(f"V4.0 듀얼 모드 + V5.2 통합 시스템 · {datetime.now().strftime('%Y-%m-%d %H:%M')} KST")

# ============================================================
# 사이드바
# ============================================================
with st.sidebar:
    st.header("🌐 시장 국면 V5.1")
    
    # 시장 데이터 입력
    kospi_rsi = st.number_input("코스피 RSI", value=70.0, min_value=0.0, max_value=100.0, step=1.0)
    vix = st.number_input("VIX", value=22.0, min_value=0.0, step=1.0)
    foreign_net = st.number_input("외국인 순매수 (만주)", value=-221, step=100)
    
    market = MarketPhaseAdaptive()
    phase = market.adapt(kospi_rsi=kospi_rsi, vix=vix, foreign_net=foreign_net)
    
    st.markdown("---")
    st.markdown(f"**시장 국면**: {phase['rsi_mode']}")
    st.markdown(f"**보수/공격**: {phase['conservative_pct']}%/{phase['aggressive_pct']}%")
    st.markdown(f"**외국인**: {phase['foreign_status']}")
    st.markdown(f"**단타 가능**: {'✅' if phase['day_trade_allowed'] else '❌'}")
    
    st.markdown("---")
    st.header("📊 V5.2 시스템")
    st.success("V5.0 6대 차단 ✅")
    st.success("V5.1 한국 특화 ✅")
    st.success("V5.2 패턴 학습 ✅")

# ============================================================
# 메인 화면
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs(["📊 종목 분석", "📈 패턴 학습", "🔬 백테스팅", "📋 정책 트리거"])

# ============================================================
# 탭 1: 종목 분석
# ============================================================
with tab1:
    st.header("V5.2 종목 분석")
    
    # 정재영님 5/20 보유 종목 샘플
    sample_stocks = [
        {"code": "034020", "name": "두산에너빌리티", "price": 108000, "rsi": 45, "volume": 1.5,
         "deal_vol": 500, "margin_pct": 9.2, "yoy_pct": 30, "foreign_buy_3d": True, 
         "inst_buy_3d": True, "atr_pct": 4.5, "track": "long", "score": 65},
        {"code": "005380", "name": "현대차", "price": 653000, "rsi": 65, "volume": 2.0,
         "deal_vol": 1000, "margin_pct": 8.5, "yoy_pct": 25, "foreign_buy_3d": True,
         "inst_buy_3d": True, "atr_pct": 4.0, "track": "long", "score": 75},
        {"code": "005930", "name": "삼성전자", "price": 296000, "rsi": 55, "volume": 1.8,
         "deal_vol": 1400, "margin_pct": 12, "yoy_pct": 25, "foreign_buy_3d": False,
         "inst_buy_3d": True, "atr_pct": 4.0, "track": "long", "score": 70},
        {"code": "454910", "name": "두산로보틱스", "price": 94700, "rsi": 49, "volume": 4.8,
         "deal_vol": 300, "margin_pct": -5, "yoy_pct": -30, "foreign_buy_3d": False,
         "inst_buy_3d": False, "atr_pct": 6.0, "track": "long", "score": 43},  # V5 차단
    ]
    
    if st.button("🚀 V5.2 분석 실행", use_container_width=True):
        with st.spinner("V5.2 분석 중..."):
            engine = JEngineV52()
            market_data = {"kospi_rsi": kospi_rsi, "vix": vix, "foreign_net": foreign_net}
            results = engine.analyze_with_v52(sample_stocks, market_data)
            
            st.session_state['results'] = results
            st.success("✅ 분석 완료!")
    
    # 결과 표시
    if 'results' in st.session_state:
        results = st.session_state['results']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🛡 보수형 (Conservative)")
            for track_label, track_key in [("🏆 장기", "long"), ("📈 스윙", "swing"), ("⚡ 단타", "day")]:
                stocks = results['conservative'].get(track_key, [])
                if stocks:
                    st.markdown(f"**{track_label} ({len(stocks)}종목)**")
                    for s in stocks:
                        bonus_html = f'<span class="v5-bonus">V5.1 +{s.get("v5_bonus", 0)}점 {s.get("v5_signal", "")}</span>'
                        st.markdown(
                            f"- **{s['name']}** ({s['code']}) {s.get('price', 0):,}원 / "
                            f"점수 {s.get('score', 0)} {bonus_html}",
                            unsafe_allow_html=True
                        )
        
        with col2:
            st.subheader("⚔ 공격형 (Aggressive)")
            for track_label, track_key in [("🏆 장기", "long"), ("📈 스윙", "swing"), ("⚡ 단타", "day")]:
                stocks = results['aggressive'].get(track_key, [])
                if stocks:
                    st.markdown(f"**{track_label} ({len(stocks)}종목)**")
                    for s in stocks:
                        bonus_html = f'<span class="v5-bonus">V5.1 +{s.get("v5_bonus", 0)}점 {s.get("v5_signal", "")}</span>'
                        st.markdown(
                            f"- **{s['name']}** ({s['code']}) {s.get('price', 0):,}원 / "
                            f"점수 {s.get('score', 0)} {bonus_html}",
                            unsafe_allow_html=True
                        )
        
        # V5에서 차단된 종목
        st.markdown("---")
        st.subheader("🚫 V5.0이 차단한 종목 (V4는 통과시켰을 종목)")
        for track in ['long', 'swing', 'day']:
            blocked = results['conservative'].get(f'{track}_v5_blocked', [])
            for s in blocked:
                reasons = s.get('v5_blocked', [])
                st.error(f"**{s['name']}** ({s['code']}): {', '.join(reasons)}")

# ============================================================
# 탭 2: 패턴 학습
# ============================================================
with tab2:
    st.header("📈 사용자 패턴 학습 (V5.2)")
    
    learner = UserPatternLearner()
    pattern = learner.analyze_pattern()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 매매 기록", f"{pattern.get('trade_count', 0)}회")
    col2.metric("🏆 승률", f"{pattern.get('win_rate', 0)}%")
    col3.metric("✅ 완료 매매", f"{pattern.get('completed_trades', 0)}건")
    
    st.subheader("💪 강점")
    for s in pattern.get('strengths', []):
        st.success(s)
    
    st.subheader("⚠️ 약점 (J가 자동 보완)")
    for w in pattern.get('weaknesses', []):
        st.warning(w)
    
    if pattern.get('trade_count', 0) < 30:
        st.info(f"💡 30회 이상 매매 누적 시 의미있는 패턴 분석 가능 (현재 {pattern.get('trade_count', 0)}회)")

# ============================================================
# 탭 3: 백테스팅
# ============================================================
with tab3:
    st.header("🔬 추천 적중률 (백테스팅)")
    
    backtest = BacktestingEngine()
    accuracy = backtest.calculate_accuracy()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 누적 추천", f"{accuracy.get('total_recommendations', 0)}건")
    col2.metric("✅ 완료", f"{accuracy.get('completed', 0)}건")
    col3.metric("🎯 적중률", f"{accuracy.get('accuracy_pct', 0)}%")
    
    if accuracy.get('completed', 0) > 0:
        st.metric("💰 평균 수익률", f"{accuracy.get('avg_return_pct', 0)}%")
    else:
        st.info(accuracy.get('message', '데이터 누적 중...'))

# ============================================================
# 탭 4: 정책 트리거
# ============================================================
with tab4:
    st.header("📋 정책 발언 자동 분석 (V5.1)")
    
    col1, col2 = st.columns(2)
    speaker = col1.selectbox("발언 주체", 
                              ["대통령", "정책실장", "총리", "기재부장관", "금융위원장", "산업부장관"])
    keyword = col2.selectbox("키워드",
                              ["초과세수", "국민배당금", "긴급조정권", "탈원전", 
                               "AI보조금", "반도체보조금", "방산수출지원", "상법개정"])
    
    if st.button("정책 영향 분석"):
        policy = PolicyTriggerMatrix()
        result = policy.analyze(speaker, keyword)
        
        st.markdown(f"### 분석 결과")
        st.markdown(f"**가중치**: {result['weight']}")
        st.markdown(f"**영향**: {result['impact']}")
        st.markdown(f"**영향 종목**: {', '.join(result['stocks_affected'])}")
        
        if result['block_24h']:
            st.error(f"🚨 {result['action']}")
        else:
            st.warning(f"⚠️ {result['action']}")


st.divider()
st.caption("J Partner Quant V5.2 · 모든 매매 전 HTS 실시간 가격 직접 확인 필수")