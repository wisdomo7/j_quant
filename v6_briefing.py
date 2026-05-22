# ============================================
# J Quant V6.0 - 매일 자동 브리핑 시스템
# 뉴스 + 종목 발굴 + 시장 국면 통합
# V1.0 룰: 모든 데이터에 시점 + 출처 명시
# ============================================
import json
import os
from datetime import datetime
from typing import Dict, List

from v6_news import NewsCollector
from v6_scanner import V6Scanner


class DailyBriefing:
    """매일 자동 J 브리핑 생성"""
    
    def __init__(self):
        self.briefing_time = None
        self.news_data = None
        self.scan_results = None
    
    def generate(self, scan_mode='quick', save_to_file=True):
        """일일 브리핑 자동 생성"""
        self.briefing_time = datetime.now()
        
        print("=" * 75)
        print(f"  🎯 J Partner Daily Briefing")
        print(f"  {self.briefing_time.strftime('%Y년 %m월 %d일 %H:%M:%S')} KST")
        print("=" * 75)
        
        # 1. 뉴스 자동 수집
        print("\n📰 [1/4] 뉴스 자동 수집 시작...")
        news_collector = NewsCollector()
        self.news_data = news_collector.collect_news(hours_back=24)
        print(f"   ✓ {self.news_data['metadata']['total_news']}건 수집 완료")
        
        # 2. 종목 자동 스캔
        print("\n📊 [2/4] 종목 자동 스캔 시작...")
        scanner = V6Scanner()
        stocks = scanner.scan_market(mode=scan_mode)
        
        if stocks:
            market_data = {
                'kospi_rsi': 70,   # 추후 실시간 수집
                'vix': 22,
                'foreign_net': -221
            }
            self.scan_results = scanner.analyze_with_v6(stocks, market_data)
            scanner.save_results(self.scan_results, self.news_data)
        
        # 3. 통합 브리핑 출력
        print("\n🎯 [3/4] 통합 브리핑 생성")
        self._print_full_briefing()
        
        # 4. 파일 저장
        if save_to_file:
            print("\n💾 [4/4] 브리핑 파일 저장")
            self._save_briefing_file()
        
        return {
            "news": self.news_data,
            "scan": self.scan_results,
            "briefing_time": self.briefing_time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _print_full_briefing(self):
        """통합 브리핑 출력"""
        
        # ───── 섹션 1: 시장 국면 ─────
        print("\n" + "=" * 75)
        print("🌐 시장 국면 (V5.1 자동 분석)")
        print("=" * 75)
        
        if self.scan_results and 'market_phase' in self.scan_results:
            mp = self.scan_results['market_phase']
            print(f"\n  📊 국면: {mp['rsi_mode']}")
            print(f"  💰 보수/공격: {mp['conservative_pct']}% / {mp['aggressive_pct']}%")
            print(f"  🌍 외국인: {mp['foreign_status']}")
            print(f"  ⚡ 단타 가능: {'✅' if mp['day_trade_allowed'] else '❌'}")
        
        # ───── 섹션 2: 핵심 뉴스 TOP 5 ─────
        print("\n" + "=" * 75)
        print("📰 핵심 뉴스 TOP 5 (24시간 이내, 중요도순)")
        print("=" * 75)
        
        if self.news_data and self.news_data['news']:
            news_list = self.news_data['news'][:5]
            meta = self.news_data['metadata']
            print(f"\n  ⏰ 수집 시각: {meta['collection_time']}")
            print(f"  📡 출처: {', '.join(meta['sources_used'])}")
            
            for i, news in enumerate(news_list, 1):
                stars = "★" * news['importance']
                print(f"\n  [{i}] {stars}")
                print(f"      📌 {news['title']}")
                print(f"      🏢 {news['publisher']}")
                print(f"      🕐 {news['published']} ({news['freshness']})")
                print(f"      🔑 {', '.join(news['keywords'])}")
        else:
            print("\n  ⚠️ 핵심 뉴스 없음")
        
        # ───── 섹션 3: 보수형 추천 TOP 5 ─────
        print("\n" + "=" * 75)
        print("🛡 보수형 추천 TOP 5 (V5.2 6대 차단 통과)")
        print("=" * 75)
        
        if self.scan_results:
            meta = self.scan_results.get('metadata', {})
            print(f"\n  ⏰ 스캔 시각: {meta.get('scan_time')}")
            print(f"  📡 데이터: {meta.get('data_source')}")
            
            cons_long = self.scan_results['conservative']['long'][:5]
            if cons_long:
                for i, s in enumerate(cons_long, 1):
                    bonus = s.get('v5_bonus', 0)
                    signal = s.get('v5_signal', '')
                    print(f"\n  [{i}] {s['name']} ({s['code']})")
                    print(f"      💰 현재가: {s.get('price', 0):,}원")
                    print(f"      📊 점수: {s.get('score', 0)}점")
                    print(f"      📈 RSI: {s.get('rsi', 0):.1f}")
                    if bonus > 0:
                        print(f"      🎯 V5.1 보너스: +{bonus}점 ({signal})")
                    if 'targets' in s:
                        t = s['targets']
                        print(f"      🎯 진입: {t.get('entry', 0):,}원 / 손절: {t.get('stop', 0):,}원 / 1차: {t.get('target1', 0):,}원")
                        print(f"      📐 손익비: {t.get('rr', 0)}:1")
            else:
                print("\n  ⚠️ 통과 종목 없음")
        
        # ───── 섹션 4: 공격형 단타 TOP 3 ─────
        print("\n" + "=" * 75)
        print("⚔ 공격형 단타 TOP 3 (모멘텀 종목)")
        print("=" * 75)
        
        if self.scan_results:
            agg_day = self.scan_results['aggressive']['day'][:3]
            agg_swing = self.scan_results['aggressive']['swing'][:3]
            
            if agg_day:
                print("\n  📊 단타 (1일):")
                for i, s in enumerate(agg_day, 1):
                    print(f"\n  [{i}] {s['name']} ({s['code']})")
                    print(f"      💰 {s.get('price', 0):,}원 | 점수 {s.get('score', 0)}")
            
            if agg_swing:
                print("\n  📊 스윙 (2-4주):")
                for i, s in enumerate(agg_swing, 1):
                    print(f"\n  [{i}] {s['name']} ({s['code']})")
                    print(f"      💰 {s.get('price', 0):,}원 | 점수 {s.get('score', 0)}")
            
            if not agg_day and not agg_swing:
                print("\n  ⚠️ 모멘텀 종목 없음")
        
        # ───── 섹션 5: V5.0이 차단한 종목 ─────
        print("\n" + "=" * 75)
        print("🚫 V5.2가 차단한 종목 (5/19 두산로보 사고 재발 방지)")
        print("=" * 75)
        
        if self.scan_results:
            all_blocked = []
            for mode in ['conservative', 'aggressive']:
                for track in ['long', 'swing', 'day']:
                    blocked = self.scan_results[mode].get(f'{track}_blocked', [])
                    for s in blocked:
                        if s not in all_blocked:
                            all_blocked.append(s)
            
            if all_blocked:
                for s in all_blocked[:5]:
                    reasons = s.get('v5_blocked', [])
                    print(f"\n  ❌ {s['name']} ({s['code']}): {', '.join(reasons)}")
            else:
                print("\n  ✅ 차단 종목 없음 (모두 V5.2 통과)")
        
        # ───── 최종 액션 ─────
        print("\n" + "=" * 75)
        print("🎯 최종 액션 (J 운용 지침 V1.0)")
        print("=" * 75)
        print("\n  ⏰ 오늘 즉시: 보유 종목 손절선 점검")
        print("  📊 시장 국면 반영: 신규 매수 보류 (과열 경고)")
        print("  📰 뉴스 모니터링: 24시간 이내 ★★★★★ 뉴스 우선")
        print("  ⚡ 단타: VIX 30↓ 가능 / 30↑ 금지")
    
    def _save_briefing_file(self):
        """브리핑 파일 저장 (HTML/JSON)"""
        os.makedirs('briefings', exist_ok=True)
        
        today = self.briefing_time.strftime("%Y%m%d_%H%M")
        json_path = f"briefings/briefing_{today}.json"
        
        data = {
            "briefing_time": self.briefing_time.strftime("%Y-%m-%d %H:%M:%S"),
            "news": self.news_data,
            "scan": self.scan_results
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"   ✓ 저장: {json_path}")


if __name__ == "__main__":
    briefing = DailyBriefing()
    briefing.generate(scan_mode='quick')
    
    print("\n" + "=" * 75)
    print(f"✅ V6.0 Daily Briefing 완료 ({datetime.now().strftime('%H:%M:%S')})")
    print("=" * 75)