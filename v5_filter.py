# ============================================
# J Quant V5.3 - 스마트 과매수 판별 필터
# 건전한 과매수 vs 위험한 과매수 구분
# ============================================
from datetime import datetime
from typing import Dict, List


# 메가트렌드 종목 (j_engine_v4 화이트리스트 기반)
MEGA_TREND_STOCKS = {
    "005380", "000660", "005930", "034020", "012450",
    "141080", "277810", "138080", "083650", "272210",
    "099320", "012330", "319400", "454910", "010140",
    "009540", "079550", "064350", "047810", "010120",
    "267260", "0173Y0",
}

MEGA_TREND_KEYWORDS = ['AI', '반도체', '방산', '원전', '로봇', '바이오',
                      'HBM', 'SMR', '우주', '휴머노이드', '광통신']


class JQuantV5Filter:
    """V5.3 스마트 차단 필터 - 건전한 과매수 vs 위험한 과매수 구분"""
    
    def filter_stock(self, stock: Dict) -> Dict:
        """스마트 차단 조건 검사"""
        reasons = []
        warnings = []  # 경고만 (차단 X)
        
        rsi = stock.get('rsi', 50)
        vol = stock.get('volume', 1.0)
        op_yoy = stock.get('yoy_pct', 0)
        score = stock.get('score', 0)
        code = stock.get('code', '')
        name = stock.get('name', '')
        marcap = stock.get('marcap', 0)  # 원 단위
        foreign_3d = stock.get('foreign_buy_3d', False)
        sector = stock.get('sector', '')
        
        # ════════════════════════════════════════
        # ① 스마트 과매수 판별 (V5.3 핵심 개선)
        # ════════════════════════════════════════
        if rsi >= 70:
            # 건전한 과매수 5대 조건 체크
            is_megatrend = (code in MEGA_TREND_STOCKS) or \
                          any(kw in sector for kw in MEGA_TREND_KEYWORDS)
            
            is_large_cap = marcap >= 5_000_000_000_000  # 시총 5조+
            
            has_strong_earnings = op_yoy >= 20  # 영업이익 +20%+
            
            has_foreign_inflow = foreign_3d  # 외국인 3일+ 매수
            
            normal_volume = vol <= 5.0  # 거래량 폭발 아님
            
            healthy_count = sum([
                is_megatrend, is_large_cap, has_strong_earnings,
                has_foreign_inflow, normal_volume
            ])
            
            # 5개 중 3개 이상 충족 = 건전한 과매수 (통과)
            if healthy_count >= 3:
                warnings.append(f"⚠️ RSI {rsi:.1f} 과매수 (건전 - {healthy_count}/5 충족)")
                # 차단 X, 경고만
            else:
                reasons.append(f"❌ RSI {rsi:.1f} 위험한 과매수 ({healthy_count}/5)")
        
        # ════════════════════════════════════════
        # ② 거래량 10배+ 과열 (세력 이탈)
        # ════════════════════════════════════════
        if vol >= 10.0:
            # 메가트렌드 대형주는 +20배까지 허용
            if (code in MEGA_TREND_STOCKS) and marcap >= 10_000_000_000_000 and vol < 20:
                warnings.append(f"⚠️ 거래량 {vol:.1f}배 (대형주 모멘텀)")
            else:
                reasons.append(f"❌ 거래량 {vol:.1f}배 폭발 (세력 이탈 위험)")
        
        # ════════════════════════════════════════
        # ③ 어닝쇼크 차단 (V5.0 그대로)
        # ════════════════════════════════════════
        if op_yoy <= -20:
            # 단, 메가트렌드 대형주는 -30%까지 허용 (사이클 바닥)
            if (code in MEGA_TREND_STOCKS) and marcap >= 10_000_000_000_000 and op_yoy >= -30:
                warnings.append(f"⚠️ 영업이익 {op_yoy:.1f}% (사이클 바닥 가능)")
            else:
                reasons.append(f"❌ 영업이익 YoY {op_yoy:.1f}% 어닝쇼크")
        
        # ════════════════════════════════════════
        # ④ 실적 D-7 차단 (V5.0 그대로)
        # ════════════════════════════════════════
        edate = stock.get('earnings_date', '')
        if edate:
            try:
                ed = datetime.strptime(edate, "%Y-%m-%d")
                days = (ed - datetime.now()).days
                if 0 <= days <= 7:
                    reasons.append(f"❌ 실적발표 D-{days}")
            except:
                pass
        
        # ════════════════════════════════════════
        # ⑤ 투자위험종목 차단
        # ════════════════════════════════════════
        if stock.get('is_warning', False):
            reasons.append("❌ 투자위험종목")
        
        # ════════════════════════════════════════
        # ⑥ 점수 미달 (메가트렌드는 35점, 일반은 45점)
        # ════════════════════════════════════════
        threshold = 35 if (code in MEGA_TREND_STOCKS) else 45
        if score < threshold:
            reasons.append(f"❌ 점수 {score} < {threshold}")
        
        return {
            "passed": len(reasons) == 0,
            "blocked_reasons": reasons,
            "warnings": warnings,  # 통과했지만 주의 사항
            "stock_code": code,
            "stock_name": name,
            "is_megatrend": code in MEGA_TREND_STOCKS,
            "marcap_billion": marcap / 100_000_000 if marcap else 0  # 억원
        }


# ============================================
# 테스트 — 정재영님 지적 검증
# ============================================
if __name__ == "__main__":
    print("=" * 70)
    print("V5.3 스마트 과매수 판별 테스트")
    print("=" * 70)
    
    filter = JQuantV5Filter()
    
    # 테스트 1: 삼성전자 (RSI 72.2 과매수지만 펀더 강함)
    samsung = {
        "code": "005930",
        "name": "삼성전자",
        "rsi": 72.2,
        "volume": 1.8,
        "yoy_pct": 25,  # 메모리 사이클
        "score": 70,
        "marcap": 415_000_000_000_000,  # 시총 415조
        "foreign_buy_3d": False,
        "is_warning": False
    }
    
    result = filter.filter_stock(samsung)
    print(f"\n[1] 삼성전자 (RSI 72.2)")
    print(f"   통과: {result['passed']}")
    if result['blocked_reasons']:
        print(f"   차단: {result['blocked_reasons']}")
    if result['warnings']:
        print(f"   경고: {result['warnings']}")
    
    # 테스트 2: SK하이닉스 (RSI 75.8 + HBM)
    skh = {
        "code": "000660",
        "name": "SK하이닉스",
        "rsi": 75.8,
        "volume": 2.1,
        "yoy_pct": 180,  # HBM 슈퍼사이클
        "score": 75,
        "marcap": 145_000_000_000_000,
        "foreign_buy_3d": True,
        "is_warning": False
    }
    
    result2 = filter.filter_stock(skh)
    print(f"\n[2] SK하이닉스 (RSI 75.8)")
    print(f"   통과: {result2['passed']}")
    if result2['blocked_reasons']:
        print(f"   차단: {result2['blocked_reasons']}")
    if result2['warnings']:
        print(f"   경고: {result2['warnings']}")
    
    # 테스트 3: 현대모비스 (RSI 72.3 메가트렌드)
    mobis = {
        "code": "012330",
        "name": "현대모비스",
        "rsi": 72.3,
        "volume": 2.0,
        "yoy_pct": 22,
        "score": 65,
        "marcap": 28_000_000_000_000,
        "foreign_buy_3d": True,
        "is_warning": False
    }
    
    result3 = filter.filter_stock(mobis)
    print(f"\n[3] 현대모비스 (RSI 72.3)")
    print(f"   통과: {result3['passed']}")
    if result3['blocked_reasons']:
        print(f"   차단: {result3['blocked_reasons']}")
    if result3['warnings']:
        print(f"   경고: {result3['warnings']}")
    
    # 테스트 4: 두산로보틱스 (5/19 어닝쇼크)
    dr = {
        "code": "454910",
        "name": "두산로보틱스",
        "rsi": 49.3,
        "volume": 4.8,
        "yoy_pct": -30,  # 어닝쇼크
        "score": 43,
        "marcap": 1_500_000_000_000,
        "foreign_buy_3d": False,
        "is_warning": False
    }
    
    result4 = filter.filter_stock(dr)
    print(f"\n[4] 두산로보틱스 (어닝쇼크)")
    print(f"   통과: {result4['passed']}")
    if result4['blocked_reasons']:
        print(f"   차단: {result4['blocked_reasons']}")
    
    # 테스트 5: 부실 종목 (RSI 75 + 시총 작음 + 펀더 X)
    junk = {
        "code": "999999",
        "name": "부실주식",
        "rsi": 75,
        "volume": 12.0,  # 폭발
        "yoy_pct": -25,
        "score": 30,
        "marcap": 500_000_000_000,  # 시총 5천억
        "foreign_buy_3d": False,
        "is_warning": False
    }
    
    result5 = filter.filter_stock(junk)
    print(f"\n[5] 부실 종목 (위험한 과매수)")
    print(f"   통과: {result5['passed']}")
    if result5['blocked_reasons']:
        print(f"   차단: {result5['blocked_reasons']}")
    
    print("\n" + "=" * 70)
    print("V5.3 테스트 완료!")
    print("핵심: 펀더멘털 강한 대형주는 RSI 70+여도 통과")
    print("=" * 70)