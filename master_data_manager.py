"""
Master Data Manager v2 — 종목 마스터 + 시가총액 통합 캐시
KRX 접근 횟수 최소화로 차단 방지
"""

import os
import json
import time
from datetime import datetime, timedelta

try:
    import FinanceDataReader as fdr
    FDR_AVAILABLE = True
except ImportError:
    FDR_AVAILABLE = False
    print("⚠ FinanceDataReader 미설치")


MASTER_CACHE_DIR = "cache"
os.makedirs(MASTER_CACHE_DIR, exist_ok=True)
MASTER_CACHE_FILE = os.path.join(MASTER_CACHE_DIR, "stock_master.json")


# ============================================================
# 폴백 종목명
# ============================================================
FALLBACK_NAMES = {
    "005380": "현대차", "000660": "SK하이닉스", "005930": "삼성전자",
    "034020": "두산에너빌리티", "012450": "한화에어로스페이스",
    "141080": "리가켐바이오", "277810": "레인보우로보틱스",
    "138080": "오이솔루션", "083650": "비에이치아이",
    "272210": "한화시스템", "099320": "쎄트렉아이",
    "012330": "현대모비스", "319400": "현대무벡스",
    "454910": "두산로보틱스", "079550": "LIG넥스원",
    "064350": "현대로템", "010120": "LS ELECTRIC",
    "267260": "HD현대일렉트릭", "010140": "삼성중공업",
    "009540": "HD한국조선해양", "036570": "엔씨소프트",
    "035720": "카카오", "042660": "한화오션", "267270": "HD현대건설기계",
}


# ============================================================
# 캐시 관리
# ============================================================
def is_cache_fresh(max_age_hours=24):
    if not os.path.exists(MASTER_CACHE_FILE):
        return False
    try:
        with open(MASTER_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data["cached_at"])
        age = datetime.now() - cached_at
        return age < timedelta(hours=max_age_hours)
    except Exception:
        return False


def fetch_master_from_fdr():
    """FDR로 KRX 전체 종목 마스터 + 시가총액 가져오기"""
    if not FDR_AVAILABLE:
        return None
    
    try:
        print("📥 FinanceDataReader로 KRX 종목 마스터 수집 중...")
        df = fdr.StockListing('KRX')
        
        # 시가총액 컬럼 자동 감지
        cap_col = None
        for c in ['Marcap', 'MarketCap', '시가총액', 'Market Cap']:
            if c in df.columns:
                cap_col = c
                break
        
        if cap_col:
            print(f"  시가총액 컬럼 발견: {cap_col}")
        else:
            print(f"  ⚠ 시가총액 컬럼 없음 (종목명만 저장)")
        
        master = {}
        for _, row in df.iterrows():
            try:
                code = str(row.get('Code', '')).strip()
                name = str(row.get('Name', '')).strip()
                market = str(row.get('Market', '')).strip()
                
                if not code or not name or len(code) != 6:
                    continue
                
                # 시가총액 (있으면)
                marcap = 0
                if cap_col:
                    try:
                        raw = row.get(cap_col)
                        if raw and not (isinstance(raw, float) and (raw != raw)):
                            marcap = float(raw)
                    except Exception:
                        marcap = 0
                
                master[code] = {
                    "name": name,
                    "market": market,
                    "marcap": marcap,  # 원 단위
                }
            except Exception:
                continue
        
        print(f"  ✓ {len(master)}개 종목 수집 완료")
        
        # 시가총액 통계
        if cap_col:
            with_cap = sum(1 for v in master.values() if v.get("marcap", 0) > 0)
            print(f"  ✓ 시가총액 포함: {with_cap}개")
        
        return master
    except Exception as e:
        print(f"  ⚠ FDR 수집 실패: {e}")
        return None


def load_master_cache():
    try:
        with open(MASTER_CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("master", {})
    except Exception:
        return {}


def save_master_cache(master):
    try:
        data = {
            "cached_at": datetime.now().isoformat(),
            "count": len(master),
            "master": master,
        }
        with open(MASTER_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"⚠ 캐시 저장 실패: {e}")
        return False


def get_master_data(force_refresh=False):
    """종목 마스터 가져오기 (캐시 우선)"""
    # 1. 캐시 확인
    if not force_refresh and is_cache_fresh():
        master = load_master_cache()
        if master and len(master) > 100:
            print(f"📦 종목 마스터 캐시 로드: {len(master)}개")
            return master
    
    # 2. FDR로 수집
    master = fetch_master_from_fdr()
    if master and len(master) > 100:
        save_master_cache(master)
        return master
    
    # 3. 기존 캐시 재사용
    master = load_master_cache()
    if master:
        print(f"⚠ FDR 실패, 기존 캐시 사용: {len(master)}개")
        return master
    
    # 4. 폴백
    print(f"⚠ 폴백 사용: {len(FALLBACK_NAMES)}개")
    return {code: {"name": name, "market": "", "marcap": 0} for code, name in FALLBACK_NAMES.items()}


# ============================================================
# 종목 정보 조회 API
# ============================================================
_MASTER_CACHE = None


def _get_cache():
    global _MASTER_CACHE
    if _MASTER_CACHE is None:
        _MASTER_CACHE = get_master_data()
    return _MASTER_CACHE


def get_stock_name(code, master=None):
    """종목명 조회"""
    if master is None:
        master = _get_cache()
    
    if code in master:
        info = master[code]
        if isinstance(info, dict):
            name = info.get("name", "")
        else:
            name = str(info)
        
        if isinstance(name, str) and name and not _is_invalid(name):
            return name
    
    if code in FALLBACK_NAMES:
        return FALLBACK_NAMES[code]
    
    return code


def get_stock_market(code, master=None):
    """시장 구분 조회"""
    if master is None:
        master = _get_cache()
    
    if code in master:
        info = master[code]
        if isinstance(info, dict):
            return info.get("market", "")
    return ""


def get_stock_marcap(code, master=None):
    """시가총액 조회 (원 단위)"""
    if master is None:
        master = _get_cache()
    
    if code in master:
        info = master[code]
        if isinstance(info, dict):
            return float(info.get("marcap", 0))
    return 0


def get_all_codes(master=None):
    """전체 종목 코드 리스트"""
    if master is None:
        master = _get_cache()
    return list(master.keys())


def get_codes_by_marcap(min_marcap_eok=500, master=None):
    """시가총액 기준 필터링된 종목 코드 리스트"""
    if master is None:
        master = _get_cache()
    
    min_marcap_won = min_marcap_eok * 1e8
    result = []
    for code, info in master.items():
        if isinstance(info, dict):
            marcap = info.get("marcap", 0)
            market = info.get("market", "")
            if marcap >= min_marcap_won and market in ["KOSPI", "KOSDAQ"]:
                result.append((code, marcap))
    
    # 시가총액 큰 순 정렬
    result.sort(key=lambda x: -x[1])
    return [code for code, _ in result]


def refresh_cache():
    global _MASTER_CACHE
    _MASTER_CACHE = None
    return get_master_data(force_refresh=True)


# ============================================================
# 데이터 검증
# ============================================================
def _is_invalid(name):
    invalid_keywords = ["Empty", "DataFrame", "Columns:", "Index:", "NaN", "None"]
    for kw in invalid_keywords:
        if kw in name:
            return True
    if "\n" in name or len(name) > 50:
        return True
    return False


def validate_number(value, default=0, min_val=None, max_val=None):
    import pandas as pd
    try:
        if value is None or pd.isna(value):
            return default
        num = float(value)
        if min_val is not None and num < min_val:
            return default
        if max_val is not None and num > max_val:
            return default
        return num
    except Exception:
        return default


def validate_int(value, default=0, min_val=None, max_val=None):
    num = validate_number(value, default, min_val, max_val)
    try:
        return int(num)
    except Exception:
        return default


def validate_bool(value, default=False):
    import pandas as pd
    try:
        if value is None or pd.isna(value):
            return default
        return bool(value)
    except Exception:
        return default


# ============================================================
# 단독 실행
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("종목 마스터 캐시 강제 갱신 (v2 - 시가총액 포함)")
    print("=" * 50)
    
    master = refresh_cache()
    print(f"\n총 {len(master)}개 종목 캐시됨")
    
    # 시가총액 통계
    with_cap = sum(1 for v in master.values() if v.get("marcap", 0) > 0)
    print(f"시가총액 포함: {with_cap}개")
    
    # 시가총액 상위 5개
    sorted_by_cap = sorted(
        [(c, i) for c, i in master.items() if i.get("marcap", 0) > 0],
        key=lambda x: -x[1].get("marcap", 0)
    )[:5]
    
    print("\n시가총액 상위 5개:")
    for code, info in sorted_by_cap:
        cap_eok = info["marcap"] / 1e8
        print(f"  {code}: {info['name']:15s} {cap_eok:>10,.0f}억 ({info['market']})")
    
    # 시가총액 500억 이상
    big_codes = get_codes_by_marcap(500, master)
    print(f"\n시가총액 500억 이상: {len(big_codes)}개")
