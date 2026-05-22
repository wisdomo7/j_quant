# ============================================
# J Quant V6.0 - 종목 발굴 통합 스캐너
# data_collector_v5 (기존) + j_engine_v4 (기존) + V5.2 (신규)
# V1.0 룰: 모든 데이터에 시점 + 출처 명시
# ============================================
import json
import os
from datetime import datetime
from typing import Dict, List

# 기존 V4 시스템 활용 (정재영님 노트북에 이미 있음)
try:
    from data_collector_v5 import smart_scan_all, quick_collect_watchlist
    HAS_V5 = True
    print("✅ data_collector_v5 로드 성공")
except ImportError:
    try:
        from data_collector import collect_watchlist, enrich_fundamentals, auto_classify_tracks
        HAS_V5 = False
        print("⚠️ data_collector_v5 없음, v3 폴백 사용")
    except ImportError:
        print("❌ 데이터 수집 모듈 없음")
        HAS_V5 = False

from j_engine_v4 import analyze_dual_mode

# V5.2 신규 모듈
from v5_filter import JQuantV5Filter
from v51_korea import ForeignInstitutionalTracker, MarketPhaseAdaptive
from v52_learning import BacktestingEngine


class V6Scanner:
    """V6.0 통합 종목 발굴 시스템"""
    
    def __init__(self):
        self.v5_filter = JQuantV5Filter()
        self.foreign_inst = ForeignInstitutionalTracker()
        self.market = MarketPhaseAdaptive()
        self.backtest = BacktestingEngine()
        self.scan_time = None
        self.data_source = None
    
    def scan_market(self, mode='quick'):
        """
        시장 스캔
        mode: 'full' (전체 2400종목) or 'quick' (관심 20종목)
        """
        self.scan_time = datetime.now()
        print(f"\n🔄 시장 스캔 시작 ({self.scan_time.strftime('%H:%M:%S')})")
        print(f"   모드: {mode}")
        
        stocks = None
        
        if HAS_V5:
            if mode == 'full':
                print("📊 데이터 출처: KRX 전체 시장 (pykrx)")
                self.data_source = "KRX 전체 (pykrx)"
                try:
                    stocks = smart_scan_all(
                        min_market_cap=500,
                        min_deal_vol=10,
                        min_volume_ratio=1.5
                    )
                except Exception as e:
                    print(f"⚠️ 전체 스캔 실패: {e}")
                    print("📊 폴백: 관심 종목 빠른 수집")
                    mode = 'quick'
            
            if mode == 'quick':
                print("📊 데이터 출처: KRX 관심 종목 (pykrx)")
                self.data_source = "KRX 관심 종목 (pykrx)"
                watchlist = [
                    "005380", "000660", "005930", "034020", "012450",
                    "141080", "277810", "083650", "064350", "267270",
                    "454910", "012330", "319400", "010140", "009540",
                    "079550", "047810", "010120", "267260", "138080",
                ]
                try:
                    stocks = quick_collect_watchlist(watchlist)
                except Exception as e:
                    print(f"⚠️ 관심 종목 수집 실패: {e}")
        else:
            print("⚠️ V5 수집 모듈 없음, 샘플 데이터 사용")
            self.data_source = "샘플 데이터 (수집 모듈 없음)"
            stocks = self._sample_stocks()
        
        if not stocks:
            print("❌ 수집된 종목 없음")
            return None
        
        print(f"✅ {len(stocks)}개 종목 수집 ({datetime.now().strftime('%H:%M:%S')})")
        return stocks
    
    def _sample_stocks(self):
        """폴백 샘플 종목"""
        return [
            {"code": "034020", "name": "두산에너빌리티", "price": 108000, "rsi": 45,
             "volume": 1.5, "deal_vol": 500, "margin_pct": 9.2, "yoy_pct": 30,
             "foreign_buy_3d": True, "inst_buy_3d": True, "atr_pct": 4.5,
             "track": "long", "score": 65},
            {"code": "005380", "name": "현대차", "price": 653000, "rsi": 65,
             "volume": 2.0, "deal_vol": 1000, "margin_pct": 8.5, "yoy_pct": 25,
             "foreign_buy_3d": True, "inst_buy_3d": True, "atr_pct": 4.0,
             "track": "long", "score": 75},
        ]
    
    def analyze_with_v6(self, stocks, market_data=None):
        """V4 듀얼 + V5.2 필터 통합 분석"""
        print(f"\n🧠 V6.0 분석 시작 ({datetime.now().strftime('%H:%M:%S')})")
        
        v4_results = analyze_dual_mode(stocks)
        
        for mode in ['conservative', 'aggressive']:
            for track in ['long', 'swing', 'day']:
                filtered = []
                blocked = []
                
                for stock in v4_results[mode][track]:
                    v5_check = self.v5_filter.filter_stock({
                        'rsi': stock.get('rsi', 50),
                        'volume': stock.get('volume', 1.0),
                        'yoy_pct': stock.get('yoy_pct', 0),
                        'score': stock.get('score', 0),
                        'code': stock.get('code', ''),
                        'name': stock.get('name', '')
                    })
                    
                    if v5_check['passed']:
                        bonus = self.foreign_inst.check_combined_buying(
                            stock.get('foreign_buy_3d', False),
                            stock.get('inst_buy_3d', False)
                        )
                        stock['v5_bonus'] = bonus['bonus_score']
                        stock['v5_signal'] = bonus['signal']
                        filtered.append(stock)
                    else:
                        stock['v5_blocked'] = v5_check['blocked_reasons']
                        blocked.append(stock)
                
                v4_results[mode][track] = filtered
                v4_results[mode][f'{track}_blocked'] = blocked
        
        if market_data:
            v4_results['market_phase'] = self.market.adapt(
                kospi_rsi=market_data.get('kospi_rsi', 50),
                vix=market_data.get('vix', 25),
                foreign_net=market_data.get('foreign_net', 0)
            )
        
        # 메타데이터 추가 (V1.0 룰)
        v4_results['metadata'] = {
            "scan_time": self.scan_time.strftime("%Y-%m-%d %H:%M:%S") if self.scan_time else None,
            "data_source": self.data_source,
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_stocks_scanned": len(stocks)
        }
        
        return v4_results
    
    def save_results(self, results, news_data=None):
        """결과 캐시 저장"""
        os.makedirs('cache', exist_ok=True)
        
        cache = {
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
            "news": news_data
        }
        
        path = "cache/v6_scan.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"💾 캐시 저장: {path}")


if __name__ == "__main__":
    print("=" * 70)
    print("V6.0 Scanner 테스트 — 종목 발굴 통합")
    print("=" * 70)
    
    scanner = V6Scanner()
    
    # 1. 종목 스캔
    stocks = scanner.scan_market(mode='quick')
    
    if stocks:
        # 2. V6 분석
        market_data = {
            'kospi_rsi': 70,
            'vix': 22,
            'foreign_net': -221
        }
        results = scanner.analyze_with_v6(stocks, market_data)
        
        # 3. 메타데이터 출력 (V1.0 룰)
        meta = results.get('metadata', {})
        print("\n" + "─" * 70)
        print("📊 분석 메타데이터")
        print("─" * 70)
        print(f"  ⏰ 스캔 시작: {meta.get('scan_time')}")
        print(f"  📡 데이터 출처: {meta.get('data_source')}")
        print(f"  🧠 분석 완료: {meta.get('analysis_time')}")
        print(f"  📊 총 종목수: {meta.get('total_stocks_scanned')}개")
        
        # 4. 결과 요약
        print("\n" + "=" * 70)
        print("💎 분석 결과 요약")
        print("=" * 70)
        
        cons = results['conservative']
        agg = results['aggressive']
        print(f"\n🛡 보수형: 장기 {len(cons['long'])} / 스윙 {len(cons['swing'])} / 단타 {len(cons['day'])}")
        print(f"⚔ 공격형: 장기 {len(agg['long'])} / 스윙 {len(agg['swing'])} / 단타 {len(agg['day'])}")
        
        # 5. 시장 국면
        if 'market_phase' in results:
            mp = results['market_phase']
            print(f"\n🌐 시장 국면: {mp['rsi_mode']}")
            print(f"   외국인: {mp['foreign_status']}")
        
        # 6. 보수형 장기 TOP 5
        if cons['long']:
            print("\n" + "─" * 70)
            print("🏆 보수형 장기 TOP 5 (V5.2 통과)")
            print("─" * 70)
            for i, s in enumerate(cons['long'][:5], 1):
                bonus = s.get('v5_bonus', 0)
                signal = s.get('v5_signal', '')
                print(f"\n[{i}] {s['name']} ({s['code']})")
                print(f"   💰 {s.get('price', 0):,}원 | 점수 {s.get('score', 0)}")
                if bonus > 0:
                    print(f"   🎯 V5.1 보너스 +{bonus}점 / {signal}")
        
        # 7. 캐시 저장
        scanner.save_results(results)
    
    print("\n" + "=" * 70)
    print(f"✅ V6.0 Scanner 테스트 완료 ({datetime.now().strftime('%H:%M:%S')})")
    print("=" * 70)