"""
J Partner Quant V6.0 - 종목 발굴 시스템 (최종)
실시간 지수 + 뉴스 + 정치 + 종목 발굴 + V5.3
"""
import streamlit as st
from datetime import datetime

from v6_news import NewsCollector
from v6_politics import PoliticsTracker
from v6_scanner import V6Scanner
from v6_market import MarketIndexCollector
from v51_korea import MarketPhaseAdaptive
from v52_learning import UserPatternLearner, BacktestingEngine


st.set_page_config(page_title="J Partner Quant V6.0", page_icon="🎯", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #1a1f2e; color: #ffffff; }
h1, h2, h3, h4 { color: #60a5fa !important; }
.sidebar-section {
    background: #2a3654; padding: 12px; border-radius: 8px;
    margin: 8px 0; color: white !important;
}
.issue-critical {
    background: linear-gradient(90deg, #991b1b, #b91c1c);
    padding: 16px; border-radius: 10px; margin: 8px 0;
    color: white; border-left: 6px solid #fbbf24;
}
.issue-high {
    background: linear-gradient(90deg, #92400e, #b45309);
    padding: 16px; border-radius: 10px; margin: 8px 0;
    color: white; border-left: 6px solid #fde68a;
}
.issue-normal {
    background: #2a4570; padding: 16px; border-radius: 10px;
    margin: 8px 0; color: white; border-left: 6px solid #60a5fa;
}
.stock-card {
    background: linear-gradient(135deg, #1e3a5f, #2a4570);
    padding: 14px; border-radius: 10px; margin: 6px 0;
    border-left: 4px solid #34d399; color: white;
}
.stock-blocked {
    background: linear-gradient(135deg, #4a1e1e, #6b2a2a);
    padding: 12px; border-radius: 8px; margin: 6px 0;
    border-left: 4px solid #ef4444; color: white;
}
.v5-bonus {
    background: #2563eb; color: white; padding: 4px 10px;
    border-radius: 6px; font-size: 13px; font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

st.title("🎯 J Partner Quant V6.0")
st.caption(f"📰 뉴스 + 🏛 정치 + 💎 종목 발굴 + 🛡 V5.3 + 📊 실시간 지수 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST")

# ============================================================
# 사이드바 (종목 발굴 중심)
# ============================================================
with st.sidebar:
    # ───── ① 시장 지수 (실시간) ─────
    st.header("🌐 시장 지수 (실시간)")
    
    if st.button("🔄 지수 새로고침", use_container_width=True):
        with st.spinner("실시간 지수 수집 중..."):
            mc = MarketIndexCollector()
            st.session_state['market_index'] = mc.get_realtime_index()
    
    if 'market_index' not in st.session_state:
        try:
            mc = MarketIndexCollector()
            st.session_state['market_index'] = mc.get_realtime_index()
        except:
            st.session_state['market_index'] = None
    
    mi = st.session_state.get('market_index')
    if mi:
        kospi = mi.get('kospi', {})
        kosdaq = mi.get('kosdaq', {})
        fx = mi.get('usd_krw', {})
        
        kospi_str = f"{kospi.get('price', '?')} ({kospi.get('change', '')})" if kospi.get('status') == 'success' else "수집 실패"
        kosdaq_str = f"{kosdaq.get('price', '?')} ({kosdaq.get('change', '')})" if kosdaq.get('status') == 'success' else "수집 실패"
        fx_str = fx.get('price', '?') if fx.get('status') == 'success' else "수집 실패"
        
        st.markdown(f"""
        <div class="sidebar-section">
            <strong>📊 실시간 시장</strong><br>
            <small>⏰ {mi.get('collection_time', '')[-8:]}</small><br>
            🇰🇷 코스피 {kospi_str}<br>
            🇰🇷 코스닥 {kosdaq_str}<br>
            💵 원/달러 {fx_str}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ 지수 수집 실패 - 새로고침 클릭")
    
    # ───── ② 시장 국면 (V5.1) ─────
    st.header("📊 시장 국면 V5.1")
    kospi_rsi = st.number_input("코스피 RSI", value=55.0, step=1.0)
    vix = st.number_input("VIX", value=22.0, step=1.0)
    foreign_net = st.number_input("외국인 (만주)", value=-240, step=100)
    
    market = MarketPhaseAdaptive()
    phase = market.adapt(kospi_rsi=kospi_rsi, vix=vix, foreign_net=foreign_net)
    
    st.markdown(f"""
    <div class="sidebar-section">
        <strong>{phase['rsi_mode']}</strong><br>
        🌍 외국인: {phase['foreign_status']}<br>
        💰 보수/공격: {phase['conservative_pct']}/{phase['aggressive_pct']}%<br>
        ⚡ 단타: {'✅ 가능' if phase['day_trade_allowed'] else '❌ 금지'}
    </div>
    """, unsafe_allow_html=True)
    
    # ───── ③ V6.0 가동 ─────
    st.markdown("---")
    st.header("🚀 V6.0 자동 가동")
    scan_mode = st.radio("스캔 모드", ["관심 20종목", "전체 2400종목"], index=0)
    
    if st.button("🚀 V6.0 전체 가동", use_container_width=True, type="primary"):
        with st.spinner("V6.0 가동 중... (1-5분)"):
            try:
                st.session_state['market_index'] = MarketIndexCollector().get_realtime_index()
            except:
                pass
            
            news_data = NewsCollector().collect_news(hours_back=24)
            st.session_state['news_data'] = news_data
            
            issues = PoliticsTracker().detect_active_issues(news_data)
            st.session_state['political_issues'] = issues
            
            scanner = V6Scanner()
            mode = 'full' if '전체' in scan_mode else 'quick'
            stocks = scanner.scan_market(mode=mode)
            if stocks:
                market_data = {'kospi_rsi': kospi_rsi, 'vix': vix, 'foreign_net': foreign_net}
                results = scanner.analyze_with_v6(stocks, market_data)
                st.session_state['scan_results'] = results
                scanner.save_results(results, news_data)
            
            st.success("✅ V6.0 가동 완료!")

# ============================================================
# 메인 탭
# ============================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💎 종목 발굴", "🏛 정치 이슈", "📰 뉴스", "🚫 차단", "📈 패턴"])

# ───── 탭 1: 종목 발굴 ─────
with tab1:
    st.header("💎 자동 발굴 종목")
    
    if 'scan_results' in st.session_state and st.session_state['scan_results']:
        results = st.session_state['scan_results']
        meta = results.get('metadata', {})
        
        col1, col2, col3 = st.columns(3)
        col1.metric("⏰ 스캔", meta.get('scan_time', '')[-8:])
        col2.metric("📡 출처", "KRX")
        col3.metric("📊 분석", f"{meta.get('total_stocks_scanned', 0)}개")
        
        st.markdown("---")
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.subheader("🛡 보수형")
            for track_name, track_key in [("🏆 장기", "long"), ("📈 스윙", "swing"), ("⚡ 단타", "day")]:
                stocks = results['conservative'].get(track_key, [])
                if stocks:
                    with st.expander(f"{track_name} ({len(stocks)})", expanded=(track_key=='long')):
                        for s in stocks[:10]:
                            bonus = s.get('v5_bonus', 0)
                            bonus_tag = f'<span class="v5-bonus">V5.1 +{bonus}점</span>' if bonus > 0 else ''
                            targets = s.get('targets', {})
                            st.markdown(f"""
                            <div class="stock-card">
                                <strong>{s['name']}</strong> ({s['code']}) {bonus_tag}<br>
                                💰 {s.get('price', 0):,}원 | 점수 {s.get('score', 0)} | RSI {s.get('rsi', 0):.1f}<br>
                                🎯 진입 {targets.get('entry', 0):,} / 손절 {targets.get('stop', 0):,} / 1차 {targets.get('target1', 0):,}<br>
                                📐 손익비 {targets.get('rr', 0)}:1
                            </div>
                            """, unsafe_allow_html=True)
        
        with col_b:
            st.subheader("⚔ 공격형")
            for track_name, track_key in [("🏆 장기", "long"), ("📈 스윙", "swing"), ("⚡ 단타", "day")]:
                stocks = results['aggressive'].get(track_key, [])
                if stocks:
                    with st.expander(f"{track_name} ({len(stocks)})"):
                        for s in stocks[:10]:
                            bonus = s.get('v5_bonus', 0)
                            bonus_tag = f'<span class="v5-bonus">V5.1 +{bonus}점</span>' if bonus > 0 else ''
                            targets = s.get('targets', {})
                            st.markdown(f"""
                            <div class="stock-card">
                                <strong>{s['name']}</strong> ({s['code']}) {bonus_tag}<br>
                                💰 {s.get('price', 0):,}원 | 점수 {s.get('score', 0)}<br>
                                🎯 진입 {targets.get('entry', 0):,} / 손절 {targets.get('stop', 0):,}
                            </div>
                            """, unsafe_allow_html=True)
    else:
        st.info("👈 사이드바 '🚀 V6.0 전체 가동' 버튼을 눌러주세요")

# ───── 탭 2: 정치 이슈 ─────
with tab2:
    st.header("🏛 오늘의 활성 정치/정책 이슈")
    
    if 'political_issues' in st.session_state and st.session_state['political_issues']:
        issues = st.session_state['political_issues']
        
        col1, col2, col3 = st.columns(3)
        col1.metric("🚨 ★★★★★", sum(1 for i in issues if i['weight'] >= 5))
        col2.metric("⚠️ ★★★★", sum(1 for i in issues if i['weight'] == 4))
        col3.metric("📊 ★★★", sum(1 for i in issues if i['weight'] <= 3))
        
        st.markdown("---")
        
        for issue in issues:
            stars = "★" * issue['weight']
            css = "issue-critical" if issue['weight'] >= 5 else "issue-high" if issue['weight'] == 4 else "issue-normal"
            
            html = f"""
            <div class="{css}">
                <h4 style="color: white; margin: 0;">{stars} {issue['category']}</h4>
                <p><strong>🔑 키워드:</strong> {issue['keyword']} | <strong>📊 보도:</strong> {issue['news_count']}건 | ⏱ {issue['latest_freshness']}</p>
                <p><strong>🎯 영향:</strong> {issue['impact']}</p>
                <p><strong>📈 영향 종목:</strong> {', '.join(issue['stocks_affected'][:5])}</p>
                <p><strong>📰 관련 뉴스:</strong></p><ul>
            """
            for news in issue['news_examples']:
                html += f"<li>{news['title']}<br><small>🕐 {news['time']} ({news['freshness']})</small></li>"
            html += "</ul></div>"
            
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("👈 사이드바 '🚀 V6.0 전체 가동' 버튼을 눌러주세요")

# ───── 탭 3: 뉴스 ─────
with tab3:
    st.header("📰 실시간 핵심 뉴스 (24시간)")
    
    if 'news_data' in st.session_state and st.session_state['news_data']:
        news_data = st.session_state['news_data']
        meta = news_data['metadata']
        
        col1, col2 = st.columns(2)
        col1.metric("⏰ 수집 시각", meta['collection_time'][-8:])
        col2.metric("📰 수집 뉴스", f"{meta['total_news']}건")
        
        st.markdown("---")
        
        for news in news_data['news'][:25]:
            stars = "★" * news['importance']
            css = "issue-critical" if news['importance'] >= 5 else "issue-high" if news['importance'] >= 4 else "issue-normal"
            
            st.markdown(f"""
            <div class="{css}">
                <strong style="font-size: 14px;">{stars} [{news['source_type']}]</strong><br>
                <strong style="font-size: 16px;">{news['title']}</strong><br>
                🏢 {news['publisher']} | 🕐 {news['published']} | {news['freshness']}<br>
                🔑 {', '.join(news['keywords'])} | <a href="{news['url']}" target="_blank" style="color: #93c5fd;">[원문]</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👈 V6.0 전체 가동을 먼저 실행해주세요")

# ───── 탭 4: 차단 ─────
with tab4:
    st.header("🚫 V5.3 객관적 필터 차단 종목")
    st.caption("과매수·어닝쇼크·실적D-7·거래량폭발 (종목명 차단 폐지)")
    
    if 'scan_results' in st.session_state and st.session_state['scan_results']:
        results = st.session_state['scan_results']
        
        all_blocked = []
        seen = set()
        for mode in ['conservative', 'aggressive']:
            for track in ['long', 'swing', 'day']:
                for s in results[mode].get(f'{track}_blocked', []):
                    if s.get('code') not in seen:
                        all_blocked.append(s)
                        seen.add(s.get('code'))
        
        if all_blocked:
            for s in all_blocked:
                reasons = s.get('v5_blocked', [])
                st.markdown(f"""
                <div class="stock-blocked">
                    <strong>❌ {s['name']}</strong> ({s['code']})<br>
                    💰 {s.get('price', 0):,}원 | {', '.join(reasons)}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ 차단 종목 없음")
    else:
        st.info("👈 V6.0 전체 가동을 먼저 실행해주세요")

# ───── 탭 5: 패턴 ─────
with tab5:
    st.header("📈 매매 패턴 학습")
    
    learner = UserPatternLearner()
    pattern = learner.analyze_pattern()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 누적 매매", f"{pattern.get('trade_count', 0)}회")
    col2.metric("🏆 승률", f"{pattern.get('win_rate', 0)}%")
    col3.metric("✅ 완료", f"{pattern.get('completed_trades', 0)}건")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("💪 강점")
        for s in pattern.get('strengths', []):
            st.success(s)
    with col_b:
        st.subheader("⚠️ 약점")
        for w in pattern.get('weaknesses', []):
            st.warning(w)
    
    backtest = BacktestingEngine()
    accuracy = backtest.calculate_accuracy()
    
    st.markdown("---")
    st.subheader("🔬 J 추천 적중률")
    c1, c2 = st.columns(2)
    c1.metric("📋 누적 추천", f"{accuracy.get('total_recommendations', 0)}건")
    c2.metric("🎯 적중률", f"{accuracy.get('accuracy_pct', 0)}%")


st.divider()
st.caption(f"J Partner Quant V6.0 · 종목 발굴 시스템 · 모든 매매 전 HTS 가격 확인 필수")