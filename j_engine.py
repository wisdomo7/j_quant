"""
J Engine v3.0 — J 파트너 운용 지침 V1.0 핵심 엔진
정재영님 맞춤 블랙리스트·화이트리스트·펀더멘털·손익비·메가트렌드 통합
"""

# ============================================================
# 블랙리스트: 사용자 손절 종목 (재진입 차단)
# ============================================================
BLACKLIST = {
    "036570": "NC소프트 — 정리 중 (평단 낮추기 금지)",
    "035720": "카카오 — 손절 완료",
    "042660": "한화오션 — 손절 완료",
    "267270": "HD건설기계 — 손절 완료",
}

# ============================================================
# 화이트리스트: 메가트렌드 + 사용자 관심 (가산점)
# ============================================================
WHITELIST = {
    "005380": {"name": "현대차", "sector": "로봇·자동차", "bonus": 15, "note": "BD IPO"},
    "000660": {"name": "SK하이닉스", "sector": "반도체", "bonus": 15, "note": "HBM"},
    "005930": {"name": "삼성전자", "sector": "반도체", "bonus": 12, "note": "메모리"},
    "034020": {"name": "두산에너빌리티", "sector": "원전·SMR", "bonus": 15, "note": "AI 전력"},
    "012450": {"name": "한화에어로스페이스", "sector": "방산", "bonus": 12, "note": "호르무즈"},
    "141080": {"name": "리가켐바이오", "sector": "바이오 ADC", "bonus": 12, "note": "기술수출"},
    "0173Y0": {"name": "KODEX 미국AI광통신", "sector": "광통신 ETF", "bonus": 15, "note": "AI 인프라"},
    "138080": {"name": "오이솔루션", "sector": "광통신", "bonus": 10, "note": "광부품"},
    "083650": {"name": "비에이치아이", "sector": "원전·SMR", "bonus": 10, "note": "SMR"},
    "277810": {"name": "레인보우로보틱스", "sector": "휴머노이드", "bonus": 10, "note": "MSCI 편입"},
    "272210": {"name": "한화시스템", "sector": "우주항공", "bonus": 10, "note": "위성통신"},
    "099320": {"name": "쎄트렉아이", "sector": "우주항공", "bonus": 8, "note": "위성"},
    "012330": {"name": "현대모비스", "sector": "로봇 부품", "bonus": 10, "note": "BD 액추에이터"},
    "319400": {"name": "현대무벡스", "sector": "로봇·물류", "bonus": 8, "note": "BD 밸류체인"},
    "454910": {"name": "두산로보틱스", "sector": "협동로봇", "bonus": 8, "note": "로봇"},
}

# 사용자 보유 종목
HOLDINGS = ["005380", "036570"]

# ============================================================
# 트랙별 운용 파라미터
# ============================================================

# 시장 국면별 가중치 (RSI 86 과열 = 단타 페널티)
MARKET_WEIGHTS = {"day": 0.7, "swing": 1.0, "long": 1.3}

# 트랙별 최소 손익비
RR_MIN = {"day": 1.5, "swing": 2.0, "long": 3.0}

# 트랙별 펀더멘털 하드 필터
FUND_FILTER = {
    "day":   {"margin_min": -100, "yoy_min": -300},  # 단타: 모멘텀 우선
    "swing": {"margin_min": 5,    "yoy_min": 0},     # 스윙: 흑자 필수
    "long":  {"margin_min": 10,   "yoy_min": 20},    # 장기: 강한 펀더멘털
}

# 트랙별 최소 거래대금 (억원)
LIQUIDITY_MIN = {"day": 50, "swing": 30, "long": 20}

# 트랙별 손절 비율
STOP_PCT = {"day": 0.03, "swing": 0.07, "long": 0.15}


# ============================================================
# 종목 평가 함수
# ============================================================

def evaluate_stock(stock: dict) -> dict:
    """
    종목 1개를 J 엔진으로 평가
    
    Input dict 필수 필드:
        code, name, price, rsi, volume(20일 평균 대비 배수),
        deal_vol(거래대금 억원), margin_pct(영업이익률 %), yoy_pct(영업이익 YoY %),
        foreign_buy_3d(bool), atr_pct(%), track(day/swing/long)
    
    Optional: is_etf (default False)
    
    Returns: 평가 완료된 dict (status, score, targets 등 포함)
    """
    result = dict(stock)
    result["status"] = "pass"
    result["block_reason"] = None

    code = stock["code"]
    track = stock["track"]
    is_etf = stock.get("is_etf", False)

    # 1. 블랙리스트 차단
    if code in BLACKLIST:
        result["status"] = "blocked"
        result["block_reason"] = BLACKLIST[code]
        return result

    # 2. 펀더멘털 하드 필터
    fr = FUND_FILTER[track]
    if not is_etf:
        if stock["margin_pct"] < fr["margin_min"]:
            result["status"] = "blocked"
            result["block_reason"] = f"펀더멘털: 영업이익률 {stock['margin_pct']}% < {fr['margin_min']}%"
            return result
        if stock["yoy_pct"] < fr["yoy_min"]:
            result["status"] = "blocked"
            result["block_reason"] = f"펀더멘털: 영업이익 YoY {stock['yoy_pct']}% < {fr['yoy_min']}%"
            return result

    # 3. 유동성 필터
    if stock["deal_vol"] < LIQUIDITY_MIN[track]:
        result["status"] = "blocked"
        result["block_reason"] = f"유동성: 거래대금 {stock['deal_vol']}억 < {LIQUIDITY_MIN[track]}억"
        return result

    # 4. 손익비 계산
    targets = calc_targets(stock)
    result["targets"] = targets

    # 5. 손익비 최소 기준
    if targets["rr"] < RR_MIN[track]:
        result["status"] = "blocked"
        result["block_reason"] = f"손익비: {targets['rr']}:1 < {RR_MIN[track]}:1"
        return result

    # 6. 스코어링
    scoring = score_stock(stock)
    result["score"] = scoring["score"]
    result["reasons"] = scoring["reasons"]
    result["breakdown"] = scoring["breakdown"]

    # 7. 시장 국면 가중치 적용
    result["adjusted_score"] = round(result["score"] * MARKET_WEIGHTS[track])

    # 8. 포지션 사이즈 제안
    result["suggest_size"] = suggest_position_size(track, result["score"])

    return result


def calc_targets(stock: dict) -> dict:
    """트랙별 차등 손익비로 진입가·손절가·목표가 계산"""
    atr = stock["atr_pct"] / 100
    track = stock["track"]
    stop_pct = STOP_PCT[track]

    if track == "day":
        t1_pct = max(0.03, atr * 1.0)
        t2_pct = max(0.05, atr * 1.5)
    elif track == "swing":
        t1_pct = max(0.10, atr * 2.5)
        t2_pct = max(0.18, atr * 4.0)
    else:  # long
        t1_pct = max(0.30, atr * 6.0)
        t2_pct = max(0.50, atr * 10.0)

    entry = stock["price"]
    stop = round(entry * (1 - stop_pct))
    target1 = round(entry * (1 + t1_pct))
    target2 = round(entry * (1 + t2_pct))
    rr = round((target1 - entry) / (entry - stop), 1)

    return {
        "entry": entry,
        "stop": stop,
        "target1": target1,
        "target2": target2,
        "rr": rr,
        "stop_pct": round(stop_pct * 100, 1),
        "t1_pct": round(t1_pct * 100, 1),
        "t2_pct": round(t2_pct * 100, 1),
    }


def score_stock(stock: dict) -> dict:
    """0~100점 종합 스코어 (기술 30 + 펀더 30 + 수급 20 + 메가 20)"""
    tech = 0
    fund = 0
    supply = 0
    mega = 0
    reasons = []

    # 1. 기술적 (30점)
    rsi = stock["rsi"]
    if 40 <= rsi <= 65:
        tech += 15
        reasons.append("RSI 중립")
    elif 65 < rsi <= 75:
        tech += 8
        reasons.append("RSI 강세")
    elif rsi > 75:
        tech -= 5
        reasons.append("RSI 과열")
    elif rsi < 40:
        tech += 5
        reasons.append("RSI 침체")

    volume = stock["volume"]
    if 1.5 <= volume <= 5:
        tech += 15
        reasons.append("거래량 양호")
    elif volume > 5:
        tech += 5
        reasons.append("거래량 폭발(주의)")
    elif volume < 0.5:
        tech -= 10
        reasons.append("비유동성")
    else:
        tech += 8

    # 2. 펀더멘털 (30점)
    if stock.get("is_etf", False):
        fund = 20
        reasons.append("ETF")
    else:
        m = stock["margin_pct"]
        if m >= 20:
            fund += 15
        elif m >= 10:
            fund += 10
        elif m >= 5:
            fund += 5
        elif m < 0:
            fund -= 15

        y = stock["yoy_pct"]
        if y >= 100:
            fund += 15
        elif y >= 50:
            fund += 10
        elif y >= 20:
            fund += 7
        elif y < 0:
            fund -= 10

    # 3. 수급 (20점)
    if stock.get("foreign_buy_3d", False):
        supply += 15
        reasons.append("외국인 3일 매수")
    if stock["deal_vol"] >= 100:
        supply += 5
    elif stock["deal_vol"] < 30:
        supply -= 5

    # 4. 메가트렌드 (20점)
    if stock["code"] in WHITELIST:
        info = WHITELIST[stock["code"]]
        mega = info["bonus"]
        reasons.append(f"★ {info['sector']}")

    total = max(0, min(100, tech + fund + supply + mega))
    return {
        "score": round(total),
        "reasons": reasons,
        "breakdown": {"tech": tech, "fund": fund, "supply": supply, "mega": mega},
    }


def suggest_position_size(track: str, score: int) -> str:
    """가용 481만원 기준, 단일 종목 30% 룰 적용한 비중 제안"""
    if track == "long":
        if score >= 75:
            return "150~200만 (대형)"
        elif score >= 60:
            return "80~120만 (중)"
        else:
            return "50만 (탐색)"
    elif track == "swing":
        if score >= 70:
            return "60~100만"
        else:
            return "30~50만"
    else:  # day
        if score >= 65:
            return "30~50만"
        else:
            return "20만 (소규모)"


# ============================================================
# 트랙 자동 분류 (RSI·거래량 기반)
# ============================================================
def auto_classify_track(stock: dict) -> str:
    """RSI·거래량으로 단타/스윙/장기 자동 분류"""
    rsi = stock["rsi"]
    volume = stock["volume"]
    code = stock["code"]

    # 화이트리스트 메가트렌드 종목 = 장기 우선
    if code in WHITELIST:
        info = WHITELIST[code]
        if info["sector"] in ["로봇·자동차", "반도체", "광통신 ETF", "원전·SMR"]:
            return "long"

    # 거래량 폭발 + RSI 60+ = 단타
    if volume >= 4.0 and rsi >= 60:
        return "day"

    # RSI 40~70 + 거래량 1.5~4 = 스윙
    if 40 <= rsi <= 70 and 1.5 <= volume <= 4:
        return "swing"

    # 그 외 = 장기 (펀더멘털 검증)
    return "long"


# ============================================================
# 분석 결과 통계
# ============================================================
def analyze_results(stocks: list) -> dict:
    """전체 분석 결과 통계"""
    evaluated = [evaluate_stock(s) for s in stocks]

    long_pass = sorted(
        [s for s in evaluated if s["status"] == "pass" and s["track"] == "long"],
        key=lambda x: -x["adjusted_score"],
    )
    swing_pass = sorted(
        [s for s in evaluated if s["status"] == "pass" and s["track"] == "swing"],
        key=lambda x: -x["adjusted_score"],
    )
    day_pass = sorted(
        [s for s in evaluated if s["status"] == "pass" and s["track"] == "day"],
        key=lambda x: -x["adjusted_score"],
    )
    blocked = [s for s in evaluated if s["status"] == "blocked"]

    return {
        "long": long_pass,
        "swing": swing_pass,
        "day": day_pass,
        "blocked": blocked,
        "total_input": len(stocks),
        "total_pass": len(long_pass) + len(swing_pass) + len(day_pass),
        "total_blocked": len(blocked),
    }
