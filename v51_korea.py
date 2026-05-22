# ============================================
# J Quant V5.1 - 한국 시장 특화 모듈
# 외국인+기관 쌍끌이, 공매도, 52주, 정책 트리거
# ============================================
from typing import Dict, List


class ForeignInstitutionalTracker:
    """외국인+기관 쌍끌이 시그널 (+20점 보너스)"""
    
    def check_combined_buying(self, foreign_3d: bool, inst_3d: bool) -> Dict:
        """3일 연속 외국인+기관 동시 매수 체크"""
        if foreign_3d and inst_3d:
            return {
                "bonus_score": 20,
                "signal": "★★★ 외국인+기관 쌍끌이",
                "qualified": True
            }
        elif foreign_3d:
            return {
                "bonus_score": 10,
                "signal": "★ 외국인 매수",
                "qualified": False
            }
        elif inst_3d:
            return {
                "bonus_score": 10,
                "signal": "★ 기관 매수",
                "qualified": False
            }
        else:
            return {"bonus_score": 0, "signal": "수급 약함", "qualified": False}


class Position52WeekTracker:
    """52주 신고가/저점 위치 자동 감지"""
    
    def check_position(self, current: float, week52_high: float,
                       week52_low: float) -> Dict:
        """52주 가격 범위 내 현재 위치"""
        if week52_high == week52_low:
            return {"position": "데이터 부족", "pct": 0}
        
        position_pct = (current - week52_low) / (week52_high - week52_low) * 100
        
        if position_pct >= 95:
            signal = "★★★ 52주 신고가권 (모멘텀 / 과매수 주의)"
        elif position_pct >= 80:
            signal = "★★ 고점 근접 (강세)"
        elif position_pct <= 5:
            signal = "⚠️ 52주 신저가권 (펀더 강하면 V자 기회)"
        elif position_pct <= 20:
            signal = "★ 저점 근접 (매수 후보, 펀더 5체크 필수)"
        else:
            signal = "중립"
        
        return {
            "position_pct": round(position_pct, 1),
            "signal": signal
        }


class PolicyTriggerMatrix:
    """정책 발언 트리거 매트릭스 (V1.1 ③)"""
    
    POLICY_MAP = {
        "초과세수": {"impact": "반도체 대형주 직격", "stocks": ["삼성전자", "SK하이닉스"]},
        "국민배당금": {"impact": "반도체 대형주 직격", "stocks": ["삼성전자", "SK하이닉스"]},
        "긴급조정권": {"impact": "노조 종목 직격", "stocks": ["삼성전자", "현대차", "기아"]},
        "탈원전": {"impact": "원전 직격", "stocks": ["두산에너빌리티", "비에이치아이"]},
        "AI보조금": {"impact": "반도체 장비 호재", "stocks": ["한미반도체", "주성엔지니어링"]},
        "반도체보조금": {"impact": "반도체 장비 호재", "stocks": ["한미반도체"]},
        "방산수출지원": {"impact": "방산 호재", "stocks": ["한화에어로", "LIG넥스원", "현대로템"]},
        "상법개정": {"impact": "지주사 영향", "stocks": ["LG", "SK", "한화"]},
    }
    
    SPEAKER_WEIGHT = {
        "대통령": 5,
        "정책실장": 5,
        "총리": 5,
        "기재부장관": 4,
        "금융위원장": 4,
        "산업부장관": 3,
        "여당원내대표": 2,
    }
    
    def analyze(self, speaker: str, keyword: str) -> Dict:
        """발언 분석 → 종목별 영향"""
        weight = self.SPEAKER_WEIGHT.get(speaker, 1)
        
        if keyword in self.POLICY_MAP:
            policy = self.POLICY_MAP[keyword]
            block_24h = weight >= 5
            
            return {
                "speaker": speaker,
                "keyword": keyword,
                "weight": "★" * weight,
                "impact": policy['impact'],
                "stocks_affected": policy['stocks'],
                "action": "신규 매수 24시간 보류" if block_24h else "주의 관찰",
                "block_24h": block_24h
            }
        
        return {"keyword": keyword, "impact": "매핑 없음"}


class MarketPhaseAdaptive:
    """시장 국면 자동 적응"""
    
    def adapt(self, kospi_rsi: float, vix: float = 25,
              foreign_net: int = 0) -> Dict:
        """시장 국면별 매매 모드 자동 결정"""
        
        # 코스피 RSI 기반
        if kospi_rsi >= 80:
            mode = "극단과열 - 현금 50%+"
            conservative_pct = 70
        elif kospi_rsi >= 70:
            mode = "과열 경고 - 신규 자제"
            conservative_pct = 60
        elif kospi_rsi >= 50:
            mode = "정상 운용"
            conservative_pct = 50
        elif kospi_rsi >= 30:
            mode = "정상 매수"
            conservative_pct = 30
        else:
            mode = "적극 매수 (RSI 30 이하)"
            conservative_pct = 20
        
        # VIX 단타 가능 여부
        day_trade_allowed = vix < 30
        
        # 외국인 임계점 (V1.1 ②)
        if foreign_net >= -100:
            foreign_status = "정상"
        elif foreign_net >= -300:
            foreign_status = "주의/경고"
        elif foreign_net >= -500:
            foreign_status = "위험 - 손절선 점검"
        else:
            foreign_status = "비상 - 현금 50%+"
        
        return {
            "rsi_mode": mode,
            "conservative_pct": conservative_pct,
            "aggressive_pct": 100 - conservative_pct,
            "day_trade_allowed": day_trade_allowed,
            "foreign_status": foreign_status,
            "kospi_rsi": kospi_rsi
        }


# ============================================
# 테스트 (5/20 실전 데이터로 검증)
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("V5.1 한국 시장 특화 모듈 테스트")
    print("=" * 50)
    
    # 테스트 1: 시장 국면 (5/20 폭등 상황)
    market = MarketPhaseAdaptive()
    result = market.adapt(kospi_rsi=70, vix=22, foreign_net=-221)
    print(f"\n[테스트 1] 5/20 시장 국면")
    print(f"국면: {result['rsi_mode']}")
    print(f"보수/공격 비중: {result['conservative_pct']}%/{result['aggressive_pct']}%")
    print(f"외국인: {result['foreign_status']}")
    
    # 테스트 2: 정책 트리거 (5/17 김민석 총리 긴급조정권 발언)
    policy = PolicyTriggerMatrix()
    result2 = policy.analyze("총리", "긴급조정권")
    print(f"\n[테스트 2] 김민석 총리 긴급조정권 발언")
    print(f"가중치: {result2['weight']}")
    print(f"영향: {result2['impact']}")
    print(f"영향 종목: {result2['stocks_affected']}")
    print(f"액션: {result2['action']}")
    
    # 테스트 3: 52주 위치 (두산E 5/20)
    pos = Position52WeekTracker()
    result3 = pos.check_position(current=108000, week52_high=139200, week52_low=91000)
    print(f"\n[테스트 3] 두산E 52주 위치")
    print(f"위치: {result3['position_pct']}%")
    print(f"시그널: {result3['signal']}")
    
    # 테스트 4: 외국인+기관 쌍끌이
    foreign = ForeignInstitutionalTracker()
    result4 = foreign.check_combined_buying(foreign_3d=True, inst_3d=True)
    print(f"\n[테스트 4] 쌍끌이 시그널")
    print(f"점수 보너스: +{result4['bonus_score']}점")
    print(f"시그널: {result4['signal']}")
    
    print("\n" + "=" * 50)
    print("V5.1 테스트 완료!")
    print("=" * 50)