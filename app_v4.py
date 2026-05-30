import os, time
os.environ['TZ'] = 'Asia/Seoul'
try:
    time.tzset()
except AttributeError:
    pass

"""
J Partner Quant V6.0 - 종목 발굴 시스템 (최종) + 한국시간(KST)
"""
import streamlit as st
from datetime import datetime

from v6_news import NewsCollector
from v6_politics import PoliticsTracker
from v6_scanner import V6Scanner
from v6_market import MarketIndexCollector
from v51_korea import MarketPhaseAdaptive
from v52_learning import UserPatternLearner, BacktestingEngine


# ============================================================
# 🔍 종목 수집 모듈 import 진단 (문제 추적용 · 해결되면 제거 가능)
#    - 종목 가격이 샘플(가짜)로 나오는 진짜 원인을 화면에 표시
# ============================================================
_IMPORT_DIAG = []

# 1) data_collector_v5 (실제 종목 데이터 수집 모듈)
try:
    import data_collector_v5 as _dc_diag
    _IMPORT_DIAG.append(("ok", "data_collector_v5", "정상 로딩됨"))
    for _fn in ["smart_scan_all", "quick_collect_watchlist"]:
        if hasattr(_dc_diag, _fn):
            _IMPORT_DIAG.append(("ok", f"data_collector_v5.{_fn}", "함수 있음"))
        else:
            _IMPORT_DIAG.append(("err", f"data_collector_v5.{_fn}", "함수 없음!"))
except Exception:
    import traceback as _tb_diag
    _IMPORT_DIAG.append(("err", "data_collector_v5", _tb_diag.format_exc()))

# 2) master_data_manager (종목 마스터 데이터)
try:
    import master_data_manager as _mdm_diag
    _IMPORT_DIAG.append(("ok", "master_data_manager", "정상 로딩됨"))
except Exception:
    import traceback as _tb_diag
    _IMPORT_DIAG.append(("err", "master_data_manager", _tb_diag.format_exc()))

# 3) v6_scanner 내부의 HAS_V5 플래그 (False면 = 샘플로 빠진다는 결정적 증거)
try:
    from v6_scanner import HAS_V5 as _HAS_V5_diag
    _IMPORT_DIAG.append(
        ("ok" if _HAS_V5_diag else "err", "v6_scanner.HAS_V5", str(_HAS_V5_diag))
    )
except Exception:
    _IMPORT_DIAG.append(
        ("warn", "v6_scanner.HAS_V5", "HAS_V5 변수를 읽을 수 없음 (구조에 따라 정상일 수 있음)")
    )

# 4) 핵심 외부 라이브러리 설치 여부
for _lib in ["yfinance", "FinanceDataReader", "pandas", "numpy"]:
    try:
        __import__(_lib)
        _IMPORT_DIAG.append(("ok", f"라이브러리 {_lib}", "설치됨"))
    except Exception:
        import traceback as _tb_diag
        _IMPORT_DIAG.append(("err", f"라이브러리 {_lib}", _tb_diag.format_exc()))


st.set_page_config(page_title="J Partner Quant V6.0", page_icon="🎯", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #1a1f2e; color: #ffffff; }
h1, h2, h3, h4 { color: #60a5fa !important; }
.sidebar-section { background: #2a3654; padding: 12px; border-radius: 8px; margin: 8px 0; color: white !important; }
.issue-critical { background: linear-gradient(90deg, #991b1b, #b91c1c); padding: 16px; border-radius: 10px; margin: 8px 0; color: white; border-left: 6px solid #fbbf24; }
.issue-high { background: linear-gradient(90deg, #92400e, #b45309); padding: 16px; border-radius: 10px; margin: 8px 0; color: white; border-left: 6px solid #fde68a; }
.issue-normal { background: #2a4570; padding: 16px; border-radius: 10px; margin: 8px 0; color: white; border-left: 6px solid #60a5fa; }
.stock-card { background: linear-gradient(135deg, #1e3a5f, #2a4570); padding: 14px; border-radius: 10px; margin: 6px 0; border-left: 4px solid #34d399; color: white; }
.stock-blocked { background: linear-gradient(135deg, #4a1e1e, #6b2a2a); padding: 12px; border-radius: 8px; margin: 6px 0; border-left: 4px solid #ef4444; color: white; }
.v5-bonus { background: #2563eb; color: white; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.title("🎯 J Partner Quant V6.0")
st.caption(f"📰 뉴스 + 🏛 정치 + 💎 종목 발굴 + 🛡 V5.3 + 📊 실시간 지수 · {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST")

with st.sidebar:
    st.header("🌐 시장 지수 (실시간)")
    if st.button("🔄 지수 새로고침", use_container_width=True):
        with st.spinner("실시간 지수 수집 중..."):
            st.session_state['market_index'] = MarketIndexCollector().get_realtime_index()
    if 'market_index' not in st.session_state:
        try:
            st.session_state['market_index'] = MarketIndexCollector().get_realtime_index()
        except:
            st.session_state['market_index'] = None
    mi = st.session_state.get('market_index')
    if mi:
        kospi = mi.get('kospi', {}); kosdaq = mi.get('kosdaq', {}); fx = mi.get('usd_krw', {})
        kospi_str = f"{kospi.get('price', '?')} ({kospi.get('change', '')})" if kospi.get('status') == 'success' else "수집 실패"
        kosdaq_str = f"{kosdaq.get('price', '?')} ({kosdaq.get('change', '')})" if kosdaq.get('status') == 'success' else "수집 실패"
        fx_str = fx.get('price', '?') if fx.get('status') == 'success' else "수집 실패"
        st.markdown(f"""<div class="sidebar-section"><strong>📊 실시간 시장</strong><br><small>⏰ {mi.get('collection_time', '')[-8:]}</small><br>🇰🇷 코스피 {kospi_str}<br>🇰🇷 코스닥 {kosdaq_str}<br>💵 원/달러 {fx_str}</div>""", unsafe_allow_html=True)
    else:
        st.warning("⚠️ 지수 수집 실패 - 새로고침 클릭")

    st.header("📊 시장 국면 V5.1")
    kospi_rsi = st.number_input("코스피 RSI", value=55.0, step=1.0)
    vix = st.number_input("VIX", value=22.0, step=1.0)
    foreign_net = st.number_input("외국인 (만주)", value=-240, step=100)
    phase = MarketPhaseAdaptive().adapt(kospi_rsi=kospi_rsi, vix=vix, foreign_net=foreign_net)
    st.markdown(f"""<div class="sidebar-section"><strong>{phase['rsi_mode']}</strong><br>🌍 외국인: {phase['foreign_status']}<br>💰 보수/공격: {phase['conservative_pct']}/{phase['aggressive_pct']}%<br>⚡ 단타: {'✅ 가능' if phase['day_trade_allowed'] else '❌ 금지'}</div>""", unsafe_allow_html=True)

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
            st.session_state['political_issues'] = PoliticsTracker().detect_active_issues(news_data)
            scanner = V6Scanner()
            mode = 'full' if '전체' in scan_mode else 'quick'
            stocks = scanner.scan_market(mode=mode)
            if stocks:
                results = scanner.analyze_with_v6(stocks, {'kospi_rsi': kospi_rsi, 'vix': vix, 'foreign_net': foreign_net})
                st.session_state['scan_results'] = results
                scanner.save_results(results, news_data)
            st.success("✅ V6.0 가동 완료!")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["💎 종목 발굴", "🏛 정치 이슈", "📰 뉴스", "🚫 차단", "📈 패턴"])

with tab1:
    st.header("💎 자동 발굴 종목")

    # ========================================================
    # 🔍 종목 수집 모듈 진단 결과 (문제 원인 표시)
    # ========================================================
    _diag_has_err = any(_s == "err" for _s, _, _ in _IMPORT_DIAG)
    _exp_title = "🔍 수집 모듈 진단 결과 " + ("⚠️ 문제 발견 — 펼쳐서 확인" if _diag_has_err else "✅ 모두 정상")
    with st.expander(_exp_title, expanded=_diag_has_err):
        st.caption("종목 가격이 가짜(샘플)로 나오는 원인을 찾기 위한 진단입니다. 문제 해결 후 이 부분은 제거할 수 있어요.")
        for _status, _name, _msg in _IMPORT_DIAG:
            if _status == "ok":
                st.success(f"✅ {_name} — {_msg}")
            elif _status == "warn":
                st.warning(f"⚠️ {_name} — {_msg}")
            else:
                st.error(f"❌ {_name} 실패 — 아래가 정확한 원인입니다:")
                st.code(_msg)
    # ========================================================

    if 'scan_results' in st.session_state and st.session_state['scan_results']:
        results = st.session_state['scan_results']; meta = results.get('metadata', {})
        c1, c2, c3 = st.columns(3)
        c1.metric("⏰ 스캔", meta.get('scan_time', '')[-8:]); c2.metric("📡 출처", "KRX"); c3.metric("📊 분석", f"{meta.get('total_stocks_scanned', 0)}개")
        st.markdown("---")
        ca, cb = st.columns(2)
        with ca:
            st.subheader("🛡 보수형")
            for tn, tk in [("🏆 장기", "long"), ("📈 스윙", "swing"), ("⚡ 단타", "day")]:
                stocks = results['conservative'].get(tk, [])
                if stocks:
                    with st.expander(f"{tn} ({len(stocks)})", expanded=(tk=='long')):
                        for s in stocks[:10]:
                            b = s.get('v5_bonus', 0); bt = f'<span class="v5-bonus">V5.1 +{b}점</span>' if b > 0 else ''; t = s.get('targets', {})
                            st.markdown(f"""<div class="stock-card"><strong>{s['name']}</strong> ({s['code']}) {bt}<br>💰 {s.get('price', 0):,}원 | 점수 {s.get('score', 0)} | RSI {s.get('rsi', 0):.1f}<br>🎯 진입 {t.get('entry', 0):,} / 손절 {t.get('stop', 0):,} / 1차 {t.get('target1', 0):,}<br>📐 손익비 {t.get('rr', 0)}:1</div>""", unsafe_allow_html=True)
        with cb:
            st.subheader("⚔ 공격형")
            for tn, tk in [("🏆 장기", "long"), ("📈 스윙", "swing"), ("⚡ 단타", "day")]:
                stocks = results['aggressive'].get(tk, [])
                if stocks:
                    with st.expander(f"{tn} ({len(stocks)})"):
                        for s in stocks[:10]:
                            b = s.get('v5_bonus', 0); bt = f'<span class="v5-bonus">V5.1 +{b}점</span>' if b > 0 else ''; t = s.get('targets', {})
                            st.markdown(f"""<div class="stock-card"><strong>{s['name']}</strong> ({s['code']}) {bt}<br>💰 {s.get('price', 0):,}원 | 점수 {s.get('score', 0)}<br>🎯 진입 {t.get('entry', 0):,} / 손절 {t.get('stop', 0):,}</div>""", unsafe_allow_html=True)
    else:
        st.info("👈 사이드바 '🚀 V6.0 전체 가동' 버튼을 눌러주세요")

with tab2:
    st.header("🏛 오늘의 활성 정치/정책 이슈")
    if 'political_issues' in st.session_state and st.session_state['political_issues']:
        issues = st.session_state['political_issues']
        c1, c2, c3 = st.columns(3)
        c1.metric("🚨 ★★★★★", sum(1 for i in issues if i['weight'] >= 5)); c2.metric("⚠️ ★★★★", sum(1 for i in issues if i['weight'] == 4)); c3.metric("📊 ★★★", sum(1 for i in issues if i['weight'] <= 3))
        st.markdown("---")
        for issue in issues:
            stars = "★" * issue['weight']; css = "issue-critical" if issue['weight'] >= 5 else "issue-high" if issue['weight'] == 4 else "issue-normal"
            html = f"""<div class="{css}"><h4 style="color: white; margin: 0;">{stars} {issue['category']}</h4><p><strong>🔑 키워드:</strong> {issue['keyword']} | <strong>📊 보도:</strong> {issue['news_count']}건 | ⏱ {issue['latest_freshness']}</p><p><strong>🎯 영향:</strong> {issue['impact']}</p><p><strong>📈 영향 종목:</strong> {', '.join(issue['stocks_affected'][:5])}</p><p><strong>📰 관련 뉴스:</strong></p><ul>"""
            for news in issue['news_examples']:
                html += f"<li>{news['title']}<br><small>🕐 {news['time']} ({news['freshness']})</small></li>"
            html += "</ul></div>"
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("👈 사이드바 '🚀 V6.0 전체 가동' 버튼을 눌러주세요")

with tab3:
    st.header("📰 실시간 핵심 뉴스 (24시간)")
    if 'news_data' in st.session_state and st.session_state['news_data']:
        news_data = st.session_state['news_data']; meta = news_data['metadata']
        c1, c2 = st.columns(2); c1.metric("⏰ 수집 시각", meta['collection_time'][-8:]); c2.metric("📰 수집 뉴스", f"{meta['total_news']}건")
        st.markdown("---")
        for news in news_data['news'][:25]:
            stars = "★" * news['importance']; css = "issue-critical" if news['importance'] >= 5 else "issue-high" if news['importance'] >= 4 else "issue-normal"
            st.markdown(f"""<div class="{css}"><strong style="font-size: 14px;">{stars} [{news['source_type']}]</strong><br><strong style="font-size: 16px;">{news['title']}</strong><br>🏢 {news['publisher']} | 🕐 {news['published']} | {news['freshness']}<br>🔑 {', '.join(news['keywords'])} | <a href="{news['url']}" target="_blank" style="color: #93c5fd;">[원문]</a></div>""", unsafe_allow_html=True)
    else:
        st.info("👈 V6.0 전체 가동을 먼저 실행해주세요")

with tab4:
    st.header("🚫 V5.3 객관적 필터 차단 종목")
    st.caption("과매수·어닝쇼크·실적D-7·거래량폭발 (종목명 차단 폐지)")
    if 'scan_results' in st.session_state and st.session_state['scan_results']:
        results = st.session_state['scan_results']; all_blocked = []; seen = set()
        for mode in ['conservative', 'aggressive']:
            for track in ['long', 'swing', 'day']:
                for s in results[mode].get(f'{track}_blocked', []):
                    if s.get('code') not in seen:
                        all_blocked.append(s); seen.add(s.get('code'))
        if all_blocked:
            for s in all_blocked:
                st.markdown(f"""<div class="stock-blocked"><strong>❌ {s['name']}</strong> ({s['code']})<br>💰 {s.get('price', 0):,}원 | {', '.join(s.get('v5_blocked', []))}</div>""", unsafe_allow_html=True)
        else:
            st.success("✅ 차단 종목 없음")
    else:
        st.info("👈 V6.0 전체 가동을 먼저 실행해주세요")

with tab5:
    st.header("📈 매매 패턴 학습")
    pattern = UserPatternLearner().analyze_pattern()
    c1, c2, c3 = st.columns(3); c1.metric("📊 누적 매매", f"{pattern.get('trade_count', 0)}회"); c2.metric("🏆 승률", f"{pattern.get('win_rate', 0)}%"); c3.metric("✅ 완료", f"{pattern.get('completed_trades', 0)}건")
    ca, cb = st.columns(2)
    with ca:
        st.subheader("💪 강점")
        for s in pattern.get('strengths', []): st.success(s)
    with cb:
        st.subheader("⚠️ 약점")
        for w in pattern.get('weaknesses', []): st.warning(w)
    accuracy = BacktestingEngine().calculate_accuracy()
    st.markdown("---"); st.subheader("🔬 J 추천 적중률")
    d1, d2 = st.columns(2); d1.metric("📋 누적 추천", f"{accuracy.get('total_recommendations', 0)}건"); d2.metric("🎯 적중률", f"{accuracy.get('accuracy_pct', 0)}%")

st.divider()
st.caption("J Partner Quant V6.0 · 종목 발굴 시스템 · 모든 매매 전 HTS 가격 확인 필수")
