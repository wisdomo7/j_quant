"""
J Engine v4.0 — 보수형/공격형 듀얼 모드 분석 엔진
J 파트너 운용 지침 V1.0 + 4단계 스마트 스캐닝 통합
"""

# ============================================================
# 블랙리스트: 사용자 손절 종목 (재진입 차단)
# ============================================================
BLACKLIST = {
    "036570": "NC소프트 — 정리 중",
    "035720": "카카오 — 손절 완료",
    "042660": "한화오션 — 손절 완료",
    "267270": "HD건설기계 — 손절 완료",
}

# ============================================================
# 화이트리스트: 메가트렌드 종목 (확장)
# ============================================================
WHITELIST = {
    # 핵심 메가트렌드
    "005380": {"name": "현대차", "sector": "로봇·자동차", "bonus": 15},
    "000660": {"name": "SK하이닉스", "sector": "반도체", "bonus": 15},
    "005930": {"name": "삼성전자", "sector": "반도체", "bonus": 12},
    "034020": {"name": "두산에너빌리티", "sector": "원전·SMR", "bonus": 15},
    "012450": {"name": "한화에어로스페이스", "sector": "방산", "bonus": 12},
    "141080": {"name": "리가켐바이오", "sector": "바이오 ADC", "bonus": 12},
    "0173Y0": {"name": "KODEX 미국AI광통신", "sector": "광통신 ETF", "bonus": 15},
    "138080": {"name": "오이솔루션", "sector": "광통신", "bonus": 10},
    "083650": {"name": "비에이치아이", "sector": "원전·SMR", "bonus": 10},
    "277810": {"name": "레인보우로보틱스", "sector": "휴머노이드", "bonus": 10},
    "272210": {"name": "한화시스템", "sector": "우주항공", "bonus": 10},
    "099320": {"name": "쎄트렉아이", "sector": "우주항공", "bonus": 8},
    "012330": {"name": "현대모비스", "sector": "로봇 부품", "bonus": 10},
    "319400": {"name": "현대무벡스", "sector": "로봇·물류", "bonus": 8},
    "454910": {"name": "두산로보틱스", "sector": "협동로봇", "bonus": 8},
    # 추가 메가트렌드
    "010140": {"name": "삼성중공업", "sector": "조선", "bonus": 10},
    "009540": {"name": "HD한국조선해양", "sector": "조선", "bonus": 10},
    "079550": {"name": "LIG넥스원", "sector": "방산", "bonus": 12},
    "064350": {"name": "현대로템", "sector": "방산", "bonus": 10},
    "047810": {"name": "한국항공우주", "sector": "방산·우주", "bonus": 10},
    "010120": {"name": "LS ELECTRIC", "sector": "전력·AI인프라", "bonus": 10},
    "267260": {"name": "HD현대일렉트릭", "sector": "전력·AI인프라", "bonus": 10},
}

HOLDINGS = ["005380", "036570"]

# 매매 분류 파라미터
RR_MIN_CONSERVATIVE = {"day": 1.5, "swing": 2.0, "long": 3.0}
RR_MIN_AGGRESSIVE = {"day": 1.2, "swing": 1.5, "long": 2.0}

FUND_FILTER_CONSERVATIVE = {
    "day":   {"margin_min": -50,  "yoy_min": -100},
    "swing": {"margin_min": 5,    "yoy_min": 0},
    "long":  {"margin_min": 10,   "yoy_min": 20},
}

FUND_FILTER_AGGRESSIVE = {
    "day":   {"margin_min": -500, "yoy_min": -500},
    "swing": {"margin_min": -10,  "yoy_min": -20},
    "long":  {"margin_min": 0,    "yoy_min": 0},
}

LIQUIDITY_MIN_CONSERVATIVE = {"day": 50, "swing": 30, "long": 20}
LIQUIDITY_MIN_AGGRESSIVE = {"day": 30, "swing": 20, "long": 10}

STOP_PCT = {"day": 0.03, "swing": 0.07, "long": 0.15}


def calc_targets(stock):
    """트랙별 진입가·손절가·목표가 계산"""
    atr = stock.get("atr_pct", 5.0) / 100
    track = stock["track"]
    stop_pct = STOP_PCT[track]

    if track == "day":
        t1_pct = max(0.03, atr * 1.0)
        t2_pct = max(0.05, atr * 1.5)
    elif track == "swing":
        t1_pct = max(0.10, atr * 2.5)
        t2_pct = max(0.18, atr * 4.0)
    else:
        t1_pct = max(0.30, atr * 6.0)
        t2_pct = max(0.50, atr * 10.0)

    entry = stock["price"]
    stop = round(entry * (1 - stop_pct))
    target1 = round(entry * (1 + t1_pct))
    target2 = round(entry * (1 + t2_pct))
    rr = round((target1 - entry) / (entry - stop), 1) if (entry - stop) > 0 else 0

    return {
        "entry": entry, "stop": stop, "target1": target1, "target2": target2,
        "rr": rr,
        "stop_pct": round(stop_pct * 100, 1),
        "t1_pct": round(t1_pct * 100, 1),
        "t2_pct": round(t2_pct * 100, 1),
    }


def score_stock(stock, mode="conservative"):
    """0~100점 스코어링 (보수형/공격형 차등)"""
    tech, fund, supply, mega = 0, 0, 0, 0
    reasons = []

    # 1. 기술적 (30점)
    rsi = stock.get("rsi", 50)
    volume = stock.get("volume", 1.0)
    
    if 40 <= rsi <= 65:
        tech += 15
        reasons.append("RSI 중립")
    elif 65 < rsi <= 75:
        tech += 10 if mode == "aggressive" else 8
        reasons.append("RSI 강세")
    elif rsi > 75:
        tech += 5 if mode == "aggressive" else -5
        reasons.append("RSI 과열")
    elif rsi < 40:
        tech += 5
        reasons.append("RSI 침체")

    if 1.5 <= volume <= 5:
        tech += 15
        reasons.append("거래량 양호")
    elif volume > 5:
        tech += 12 if mode == "aggressive" else 5
        reasons.append("거래량 폭발")
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
        m = stock.get("margin_pct", 0)
        y = stock.get("yoy_pct", 0)
        
        if m >= 20:
            fund += 15
        elif m >= 10:
            fund += 10
        elif m >= 5:
            fund += 5
        elif m < 0:
            fund += -5 if mode == "aggressive" else -15

        if y >= 100:
            fund += 15
        elif y >= 50:
            fund += 10
        elif y >= 20:
            fund += 7
        elif y < 0:
            fund += -3 if mode == "aggressive" else -10

    # 3. 수급 (20점)
    if stock.get("foreign_buy_3d", False):
        supply += 15
        reasons.append("외국인 3일 매수")
    if stock.get("inst_buy_3d", False):
        supply += 10
        reasons.append("기관 매수")
    if stock.get("foreign_buy_3d") and stock.get("inst_buy_3d"):
        supply += 5
        reasons.append("★ 쌍끌이")
    
    deal_vol = stock.get("deal_vol", 0)
    if deal_vol >= 100:
        supply += 5
    elif deal_vol < 30:
        supply -= 5

    # 4. 메가트렌드 (20점)
    if stock["code"] in WHITELIST:
        info = WHITELIST[stock["code"]]
        mega = info["bonus"]
        reasons.append(f"★ {info['sector']}")
    
    # 신고가 보너스 (공격형만 큰 가산)
    if stock.get("near_52w_high", False):
        bonus = 10 if mode == "aggressive" else 5
        mega += bonus
        reasons.append("52주 신고가권")

    total = max(0, min(100, tech + fund + supply + mega))
    return {
        "score": round(total),
        "reasons": reasons,
        "breakdown": {"tech": tech, "fund": fund, "supply": supply, "mega": mega},
    }


def evaluate_stock(stock, mode="conservative"):
    """단일 종목 평가 - 보수형 또는 공격형"""
    result = dict(stock)
    result["status"] = "pass"
    result["block_reason"] = None
    result["mode"] = mode

    code = stock["code"]
    track = stock["track"]
    is_etf = stock.get("is_etf", False)

    # 1. 블랙리스트 (양 모드 공통)
    if code in BLACKLIST:
        result["status"] = "blocked"
        result["block_reason"] = BLACKLIST[code]
        return result

    # 2. 펀더멘털 필터 (모드별 차등)
    fund_filter = FUND_FILTER_AGGRESSIVE if mode == "aggressive" else FUND_FILTER_CONSERVATIVE
    fr = fund_filter[track]
    if not is_etf:
        if stock.get("margin_pct", 0) < fr["margin_min"]:
            result["status"] = "blocked"
            result["block_reason"] = f"펀더멘털: 마진 {stock.get('margin_pct')}% < {fr['margin_min']}%"
            return result
        if stock.get("yoy_pct", 0) < fr["yoy_min"]:
            result["status"] = "blocked"
            result["block_reason"] = f"펀더멘털: YoY {stock.get('yoy_pct')}% < {fr['yoy_min']}%"
            return result

    # 3. 유동성 필터 (모드별 차등)
    liq_filter = LIQUIDITY_MIN_AGGRESSIVE if mode == "aggressive" else LIQUIDITY_MIN_CONSERVATIVE
    if stock.get("deal_vol", 0) < liq_filter[track]:
        result["status"] = "blocked"
        result["block_reason"] = f"유동성: {stock.get('deal_vol')}억 < {liq_filter[track]}억"
        return result

    # 4. 손익비
    targets = calc_targets(stock)
    result["targets"] = targets

    rr_filter = RR_MIN_AGGRESSIVE if mode == "aggressive" else RR_MIN_CONSERVATIVE
    if targets["rr"] < rr_filter[track]:
        result["status"] = "blocked"
        result["block_reason"] = f"손익비: {targets['rr']}:1 < {rr_filter[track]}:1"
        return result

    # 5. 스코어링
    scoring = score_stock(stock, mode)
    result["score"] = scoring["score"]
    result["reasons"] = scoring["reasons"]
    result["breakdown"] = scoring["breakdown"]

    # 6. 비중 제안
    result["suggest_size"] = suggest_position_size(track, result["score"], mode)

    return result


def suggest_position_size(track, score, mode):
    """비중 제안 - 공격형은 작게"""
    if mode == "aggressive":
        if track == "long":
            return "30~50만 (공격)"
        elif track == "swing":
            return "20~40만 (공격)"
        else:
            return "10~20만 (공격)"
    else:
        if track == "long":
            return "150~200만" if score >= 75 else "80~120만"
        elif track == "swing":
            return "60~100만" if score >= 70 else "30~50만"
        else:
            return "30~50만" if score >= 65 else "20만"


def auto_classify_track(stock):
    """RSI·거래량·메가트렌드 기반 자동 트랙 분류"""
    rsi = stock.get("rsi", 50)
    volume = stock.get("volume", 1.0)
    code = stock["code"]

    # 화이트리스트 핵심 종목은 장기 우선
    if code in WHITELIST:
        info = WHITELIST[code]
        if info["sector"] in ["로봇·자동차", "반도체", "광통신 ETF", "원전·SMR"]:
            return "long"

    # 거래량 폭발 + RSI 60+ = 단타
    if volume >= 4.0 and rsi >= 60:
        return "day"

    # RSI 중립 + 거래량 양호 = 스윙
    if 40 <= rsi <= 70 and 1.5 <= volume <= 4:
        return "swing"

    return "long"


def analyze_dual_mode(stocks):
    """보수형과 공격형 결과를 동시에 산출"""
    # 트랙 자동 분류
    for s in stocks:
        if "track" not in s:
            s["track"] = auto_classify_track(s)

    # 보수형 분석
    conservative = [evaluate_stock(s, "conservative") for s in stocks]
    cons_long = sorted([s for s in conservative if s["status"] == "pass" and s["track"] == "long"],
                       key=lambda x: -x["score"])
    cons_swing = sorted([s for s in conservative if s["status"] == "pass" and s["track"] == "swing"],
                        key=lambda x: -x["score"])
    cons_day = sorted([s for s in conservative if s["status"] == "pass" and s["track"] == "day"],
                      key=lambda x: -x["score"])

    # 공격형 분석
    aggressive = [evaluate_stock(s, "aggressive") for s in stocks]
    agg_long = sorted([s for s in aggressive if s["status"] == "pass" and s["track"] == "long"],
                      key=lambda x: -x["score"])
    agg_swing = sorted([s for s in aggressive if s["status"] == "pass" and s["track"] == "swing"],
                       key=lambda x: -x["score"])
    agg_day = sorted([s for s in aggressive if s["status"] == "pass" and s["track"] == "day"],
                     key=lambda x: -x["score"])

    blocked = [s for s in conservative if s["status"] == "blocked"]

    return {
        "conservative": {
            "long": cons_long[:15],
            "swing": cons_swing[:15],
            "day": cons_day[:10],
            "total": len(cons_long) + len(cons_swing) + len(cons_day),
        },
        "aggressive": {
            "long": agg_long[:15],
            "swing": agg_swing[:15],
            "day": agg_day[:10],
            "total": len(agg_long) + len(agg_swing) + len(agg_day),
        },
        "blocked": blocked,
        "total_input": len(stocks),
    }
