# ============================================
# J Engine V5.2 - 기존 V4.0 + V5.2 통합
# 기존 j_engine_v4.py를 그대로 활용하면서
# v5_filter, v51_korea, v52_learning 추가 적용
# ============================================
from j_engine_v4 import analyze_dual_mode, evaluate_stock
from v5_filter import JQuantV5Filter
from v51_korea import (
    ForeignInstitutionalTracker,
    Position52WeekTracker,
    PolicyTriggerMatrix,
    MarketPhaseAdaptive
)
from v52_learning import (
    UserPatternLearner,
    BacktestingEngine,
    TelegramAlerter
)


class JEngineV52:
    """V4.0 + V5.2 통합 엔진"""
    
    def __init__(self):
        self.v5_filter = JQuantV5Filter()
        self.foreign_inst = ForeignInstitutionalTracker()
        self.pos_52w = Position52WeekTracker()
        self.policy = PolicyTriggerMatrix()
        self.market_phase = MarketPhaseAdaptive()
        self.pattern_learner = UserPatternLearner()
        self.backtest = BacktestingEngine()
        self.alerter = TelegramAlerter()
    
    def analyze_with_v52(self, stocks, market_data=None):
        """V4.0 듀얼 모드 + V5.2 추가 필터링"""
        
        # 1. V4.0 기존 분석
        v4_results = analyze_dual_mode(stocks)
        
        # 2. V5.0 6대 차단 적용 (보수형/공격형 둘 다)
        for mode in ['conservative', 'aggressive']:
            for track in ['long', 'swing', 'day']:
                filtered = []
                blocked_by_v5 = []
                
                for stock in v4_results[mode][track]:
                    # V5.0 6대 차단 체크
                    filter_data = {
                        'rsi': stock.get('rsi', 50),
                        'volume': stock.get('volume', 1.0),
                        'yoy_pct': stock.get('yoy_pct', 0),
                        'score': stock.get('score', 0),
                        'code': stock.get('code', ''),
                        'name': stock.get('name', '')
                    }
                    
                    v5_check = self.v5_filter.filter_stock(filter_data)
                    
                    if v5_check['passed']:
                        # V5.1 보너스 점수 추가
                        bonus_data = self.foreign_inst.check_combined_buying(
                            stock.get('foreign_buy_3d', False),
                            stock.get('inst_buy_3d', False)
                        )
                        stock['v5_bonus'] = bonus_data['bonus_score']
                        stock['v5_signal'] = bonus_data['signal']
                        filtered.append(stock)
                    else:
                        stock['v5_blocked'] = v5_check['blocked_reasons']
                        blocked_by_v5.append(stock)
                
                v4_results[mode][track] = filtered
                v4_results[mode][f'{track}_v5_blocked'] = blocked_by_v5
        
        # 3. 시장 국면 분석 추가
        if market_data:
            v4_results['market_phase'] = self.market_phase.adapt(
                kospi_rsi=market_data.get('kospi_rsi', 50),
                vix=market_data.get('vix', 25),
                foreign_net=market_data.get('foreign_net', 0)
            )
        
        # 4. 백테스팅 기록
        for mode in ['conservative', 'aggressive']:
            for track in ['long', 'swing', 'day']:
                for stock in v4_results[mode][track][:5]:  # 상위 5개만
                    self.backtest.record_recommendation({
                        "code": stock.get('code', ''),
                        "name": stock.get('name', ''),
                        "mode": mode,
                        "track": track,
                        "entry_price": stock.get('price', 0),
                        "target_price": stock.get('targets', {}).get('target1', 0),
                        "stop_loss": stock.get('targets', {}).get('stop', 0),
                    })
        
        # 5. 사용자 패턴 분석
        v4_results['user_pattern'] = self.pattern_learner.analyze_pattern()
        
        # 6. 백테스팅 적중률
        v4_results['accuracy'] = self.backtest.calculate_accuracy()
        
        return v4_results


# ============================================
# 테스트
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("J Engine V5.2 통합 테스트")
    print("=" * 50)
    
    # 정재영님 5/20 실제 보유 종목 + 추천 종목
    test_stocks = [
        {
            "code": "034020", "name": "두산에너빌리티",
            "price": 108000, "rsi": 45, "volume": 1.5,
            "deal_vol": 500, "margin_pct": 9.2, "yoy_pct": 30,
            "foreign_buy_3d": True, "inst_buy_3d": True,
            "atr_pct": 4.5, "track": "long",
            "score": 65
        },
        {
            "code": "454910", "name": "두산로보틱스",
            "price": 94700, "rsi": 49, "volume": 4.8,
            "deal_vol": 300, "margin_pct": -5, "yoy_pct": -30,  # 어닝쇼크
            "foreign_buy_3d": False, "inst_buy_3d": False,
            "atr_pct": 6.0, "track": "long",
            "score": 43  # V5에서 차단됨
        },
        {
            "code": "005380", "name": "현대차",
            "price": 653000, "rsi": 65, "volume": 2.0,
            "deal_vol": 1000, "margin_pct": 8.5, "yoy_pct": 25,
            "foreign_buy_3d": True, "inst_buy_3d": True,
            "atr_pct": 4.0, "track": "long",
            "score": 75
        }
    ]
    
    # 시장 데이터 (5/20)
    market_data = {
        "kospi_rsi": 75,
        "vix": 22,
        "foreign_net": -221
    }
    
    engine = JEngineV52()
    results = engine.analyze_with_v52(test_stocks, market_data)
    
    print(f"\n[시장 국면]")
    if 'market_phase' in results:
        mp = results['market_phase']
        print(f"국면: {mp['rsi_mode']}")
        print(f"외국인 상태: {mp['foreign_status']}")
    
    print(f"\n[보수형 장기 통과 종목]")
    for s in results['conservative']['long']:
        bonus = s.get('v5_bonus', 0)
        signal = s.get('v5_signal', '')
        print(f"  {s['name']} {s.get('price', 0):,}원 / "
              f"V5 보너스 +{bonus}점 / {signal}")
    
    if 'conservative' in results and 'long_v5_blocked' in results['conservative']:
        blocked = results['conservative']['long_v5_blocked']
        if blocked:
            print(f"\n[V5에서 차단된 종목]")
            for s in blocked:
                print(f"  {s['name']}: {s.get('v5_blocked', [])}")
    
    print(f"\n[사용자 패턴]")
    pattern = results.get('user_pattern', {})
    print(f"매매 기록: {pattern.get('trade_count', 0)}회")
    print(f"승률: {pattern.get('win_rate', 0)}%")
    
    print(f"\n[백테스팅]")
    accuracy = results.get('accuracy', {})
    print(f"누적 추천: {accuracy.get('total_recommendations', 0)}건")
    
    print("\n" + "=" * 50)
    print("V5.2 통합 엔진 테스트 완료!")
    print("=" * 50)