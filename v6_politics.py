# ============================================
# J Quant V6.0 - 실시간 정치 이슈 자동 추적
# 뉴스 → 정치 키워드 감지 → 영향 종목 자동 매핑
# ============================================
from datetime import datetime
from typing import Dict, List
from v6_news import NewsCollector


class PoliticsTracker:
    """실시간 정치 이슈 자동 추적 (V6.0)"""
    
    # 정치 핵심 키워드 + 카테고리 + 가중치 + 영향 종목
    POLITICAL_MAP = {
        # ═════ 미국 정치 (★★★★★) ═════
        "트럼프": {
            "category": "🇺🇸 미국 대통령",
            "weight": 5,
            "stocks": ["삼성전자", "SK하이닉스", "현대차", "한화에어로", "삼성중공업"],
            "impact": "관세·반도체·자동차·방산·조선 영향"
        },
        "파월": {
            "category": "🇺🇸 연준 의장",
            "weight": 5,
            "stocks": ["삼성전자", "SK하이닉스", "코스피 전체"],
            "impact": "금리·달러·외국인 수급"
        },
        "FOMC": {
            "category": "🇺🇸 통화정책",
            "weight": 5,
            "stocks": ["코스피 전체", "삼성전자", "SK하이닉스"],
            "impact": "금리 결정 → 글로벌 자금"
        },
        "관세": {
            "category": "🇺🇸 통상정책",
            "weight": 5,
            "stocks": ["현대차", "기아", "삼성전자", "SK하이닉스", "포스코"],
            "impact": "수출주 직격"
        },
        
        # ═════ 한국 정치 (★★★★★) ═════
        "대통령": {
            "category": "🇰🇷 대통령",
            "weight": 5,
            "stocks": ["관련 정책 종목"],
            "impact": "정책 방향성"
        },
        "총리": {
            "category": "🇰🇷 국무총리",
            "weight": 5,
            "stocks": ["관련 정책 종목"],
            "impact": "정책 집행"
        },
        "정책실장": {
            "category": "🇰🇷 정책실장",
            "weight": 5,
            "stocks": ["반도체", "자동차"],
            "impact": "경제 정책"
        },
        "긴급조정": {
            "category": "🏭 노동정책",
            "weight": 5,
            "stocks": ["삼성전자", "현대차", "기아"],
            "impact": "파업 종목 직격"
        },
        "긴급조정권": {
            "category": "🏭 노동정책",
            "weight": 5,
            "stocks": ["삼성전자", "현대차", "기아"],
            "impact": "파업 종목 직격"
        },
        
        # ═════ 정책 키워드 (★★★★) ═════
        "초과세수": {
            "category": "💰 조세정책",
            "weight": 4,
            "stocks": ["삼성전자", "SK하이닉스"],
            "impact": "반도체 대형주 영향"
        },
        "국민배당금": {
            "category": "💰 조세정책",
            "weight": 4,
            "stocks": ["삼성전자", "SK하이닉스"],
            "impact": "반도체 대형주 영향"
        },
        "탈원전": {
            "category": "⚡ 에너지정책",
            "weight": 4,
            "stocks": ["두산에너빌리티", "비에이치아이", "한국전력"],
            "impact": "원전 종목 직격"
        },
        "방산": {
            "category": "🚁 방산정책",
            "weight": 4,
            "stocks": ["한화에어로", "LIG넥스원", "현대로템", "KAI"],
            "impact": "방산 종목 호재/악재"
        },
        "AI보조금": {
            "category": "🤖 산업정책",
            "weight": 4,
            "stocks": ["한미반도체", "주성엔지니어링"],
            "impact": "반도체 장비 호재"
        },
        "반도체보조금": {
            "category": "🤖 산업정책",
            "weight": 4,
            "stocks": ["한미반도체"],
            "impact": "반도체 장비 호재"
        },
        
        # ═════ 외교/거시 (★★★★) ═════
        "미중": {
            "category": "🌐 외교",
            "weight": 4,
            "stocks": ["삼성전자", "SK하이닉스", "현대차"],
            "impact": "수출·기술 패권"
        },
        "이란": {
            "category": "🌐 외교/원유",
            "weight": 4,
            "stocks": ["에쓰오일", "현대차", "환율"],
            "impact": "원유·환율"
        },
        "북한": {
            "category": "🌐 한반도",
            "weight": 3,
            "stocks": ["방산주", "원/달러"],
            "impact": "지정학 리스크"
        },
        
        # ═════ 기타 (★★★) ═════
        "외국인": {
            "category": "💵 외국인 수급",
            "weight": 3,
            "stocks": ["코스피 전체"],
            "impact": "수급 방향"
        },
        "환율": {
            "category": "💵 환율",
            "weight": 3,
            "stocks": ["삼성전자", "현대차", "수출주"],
            "impact": "수출 경쟁력"
        },
        "금리": {
            "category": "💵 금리",
            "weight": 4,
            "stocks": ["은행주", "건설주", "성장주"],
            "impact": "자금 비용"
        },
    }
    
    def __init__(self):
        self.detection_time = None
    
    def detect_active_issues(self, news_data: Dict) -> List[Dict]:
        """뉴스 데이터에서 활성 정치 이슈 자동 감지"""
        self.detection_time = datetime.now()
        
        if not news_data or 'news' not in news_data:
            return []
        
        issue_aggregator = {}
        
        for news in news_data['news']:
            for keyword in news.get('keywords', []):
                if keyword in self.POLITICAL_MAP:
                    if keyword not in issue_aggregator:
                        info = self.POLITICAL_MAP[keyword]
                        issue_aggregator[keyword] = {
                            'keyword': keyword,
                            'category': info['category'],
                            'weight': info['weight'],
                            'impact': info['impact'],
                            'stocks_affected': info['stocks'],
                            'news_count': 0,
                            'news_examples': [],
                            'latest_freshness': '',
                            'latest_time': None
                        }
                    
                    issue_aggregator[keyword]['news_count'] += 1
                    
                    if len(issue_aggregator[keyword]['news_examples']) < 3:
                        issue_aggregator[keyword]['news_examples'].append({
                            'title': news['title'],
                            'time': news['published'],
                            'freshness': news['freshness'],
                            'source': news.get('publisher', ''),
                            'url': news.get('url', '')
                        })
                    
                    if not issue_aggregator[keyword]['latest_freshness']:
                        issue_aggregator[keyword]['latest_freshness'] = news['freshness']
        
        # 중요도 + 보도수 순 정렬
        active_issues = list(issue_aggregator.values())
        active_issues.sort(key=lambda x: (-x['weight'], -x['news_count']))
        
        return active_issues
    
    def get_summary(self, active_issues: List[Dict]) -> Dict:
        """이슈 요약 통계"""
        if not active_issues:
            return {"total": 0, "critical": 0, "high": 0}
        
        return {
            "total": len(active_issues),
            "critical": sum(1 for i in active_issues if i['weight'] >= 5),
            "high": sum(1 for i in active_issues if i['weight'] == 4),
            "normal": sum(1 for i in active_issues if i['weight'] <= 3),
            "detection_time": self.detection_time.strftime("%Y-%m-%d %H:%M:%S")
        }


# ============================================
# 테스트
# ============================================
if __name__ == "__main__":
    print("=" * 75)
    print("V6.0 PoliticsTracker — 실시간 정치 이슈 자동 추적")
    print("=" * 75)
    
    # 1. 뉴스 수집
    print("\n📰 [1/2] 뉴스 자동 수집...")
    news_collector = NewsCollector()
    news_data = news_collector.collect_news(hours_back=24)
    print(f"   ✓ {news_data['metadata']['total_news']}건 수집")
    
    # 2. 정치 이슈 자동 감지
    print("\n🏛 [2/2] 정치 이슈 자동 감지...")
    politics = PoliticsTracker()
    active_issues = politics.detect_active_issues(news_data)
    summary = politics.get_summary(active_issues)
    
    print(f"\n⏰ 감지 시각: {summary.get('detection_time', '')}")
    print(f"🔥 활성 이슈: 총 {summary['total']}개")
    print(f"   ★★★★★ {summary['critical']}개")
    print(f"   ★★★★ {summary['high']}개")
    print(f"   ★★★ {summary['normal']}개")
    
    if active_issues:
        print("\n" + "=" * 75)
        print("🚨 오늘의 활성 정치/정책 이슈 (실시간)")
        print("=" * 75)
        
        for i, issue in enumerate(active_issues, 1):
            stars = "★" * issue['weight']
            print(f"\n[{i}] {stars} {issue['category']}")
            print(f"   🔑 키워드: {issue['keyword']}")
            print(f"   📊 보도수: {issue['news_count']}건")
            print(f"   🎯 영향: {issue['impact']}")
            print(f"   📈 종목: {', '.join(issue['stocks_affected'][:5])}")
            print(f"   ⏱  최근: {issue['latest_freshness']}")
            
            print(f"\n   📰 관련 뉴스:")
            for news in issue['news_examples']:
                print(f"      • {news['title'][:50]}...")
                print(f"        🕐 {news['time']} ({news['freshness']})")
    else:
        print("\n⚠️ 현재 활성 정치 이슈 없음 (정상 운용)")
    
    print("\n" + "=" * 75)
    print(f"✅ 테스트 완료 ({datetime.now().strftime('%H:%M:%S')})")
    print("=" * 75)