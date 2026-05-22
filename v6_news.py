# J Quant V6.0 - 실시간 뉴스 수집 (강화판) + 한국시간(KST)
import os, time
os.environ['TZ'] = 'Asia/Seoul'
try:
    time.tzset()
except AttributeError:
    pass

import feedparser
from datetime import datetime, timedelta
from typing import Dict, List


class NewsCollector:
    """실시간 뉴스 자동 수집 + 시점·출처·신선도 명시 (KST)"""

    CRITICAL_KEYWORDS = {
        "트럼프": 5, "Trump": 5, "파월": 5, "Powell": 5, "FOMC": 5,
        "관세": 5, "tariff": 5, "연준": 5,
        "대통령": 5, "총리": 5, "정책실장": 5, "긴급조정": 5,
        "이재명": 5, "김민석": 5,
        "엔비디아": 4, "NVDA": 4, "삼성전자": 4, "SK하이닉스": 4,
        "현대차": 4, "한미반도체": 4,
        "HBM": 3, "원전": 3, "SMR": 3, "방산": 3,
        "외국인": 3, "환율": 3, "금리": 4,
        "미중": 4, "이란": 4, "북한": 3, "중국": 3,
        "초과세수": 4, "국민배당금": 4, "탈원전": 4,
        "AI보조금": 4, "반도체보조금": 4, "방산수출": 4,
    }

    RSS_FEEDS = {
        "한국경제_증권": {"url": "https://www.hankyung.com/feed/finance", "publisher": "한국경제신문", "type": "증권"},
        "매일경제_증권": {"url": "https://www.mk.co.kr/rss/40300001/", "publisher": "매일경제신문", "type": "증권"},
        "이데일리_시황": {"url": "https://rss.edaily.co.kr/edaily_news_finance.xml", "publisher": "이데일리", "type": "증권"},
        "연합뉴스_정치": {"url": "https://www.yna.co.kr/rss/politics.xml", "publisher": "연합뉴스", "type": "정치"},
        "이데일리_정치": {"url": "https://rss.edaily.co.kr/edaily_news_politics.xml", "publisher": "이데일리", "type": "정치"},
        "한국경제_정치": {"url": "https://www.hankyung.com/feed/politics", "publisher": "한국경제신문", "type": "정치"},
        "연합뉴스_경제": {"url": "https://www.yna.co.kr/rss/economy.xml", "publisher": "연합뉴스", "type": "경제"},
        "이데일리_국제": {"url": "https://rss.edaily.co.kr/edaily_news_international.xml", "publisher": "이데일리", "type": "국제"},
    }

    def __init__(self):
        self.collection_time = None

    def _calculate_freshness(self, pub_date) -> str:
        if not pub_date:
            return "⚠️ 시점 미상"
        now = datetime.now()
        delta = now - pub_date
        if delta.total_seconds() < 600:
            return "🔥 방금 (10분 이내)"
        elif delta.total_seconds() < 3600:
            mins = int(delta.total_seconds() / 60)
            return f"🟢 {mins}분 전"
        elif delta.total_seconds() < 21600:
            hours = int(delta.total_seconds() / 3600)
            return f"🟡 {hours}시간 전"
        elif delta.days < 1:
            hours = int(delta.total_seconds() / 3600)
            return f"🟠 {hours}시간 전 (어제)"
        elif delta.days < 3:
            return f"🔴 {delta.days}일 전 (낡음)"
        else:
            return f"⚫ {delta.days}일 전 (매우 낡음 - 무시 권장)"

    def collect_news(self, hours_back: int = 24) -> Dict:
        self.collection_time = datetime.now()
        all_news = []
        cutoff = datetime.now() - timedelta(hours=hours_back)
        sources_used = []
        sources_failed = []

        for source_name, source_info in self.RSS_FEEDS.items():
            try:
                feed = feedparser.parse(source_info['url'])
                if not feed.entries:
                    sources_failed.append(f"{source_name}: 빈 결과")
                    continue
                sources_used.append(f"{source_name}({source_info['type']})")
                for entry in feed.entries[:30]:
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        # UTC → KST 변환 (+9시간)
                        pub_date = datetime(*entry.published_parsed[:6]) + timedelta(hours=9)
                    if pub_date and pub_date < cutoff:
                        continue
                    title = entry.get('title', '')
                    matched_keywords = []
                    importance = 0
                    for keyword, stars in self.CRITICAL_KEYWORDS.items():
                        if keyword in title:
                            matched_keywords.append(keyword)
                            importance = max(importance, stars)
                    if matched_keywords:
                        all_news.append({
                            "title": title,
                            "source": source_name,
                            "publisher": source_info['publisher'],
                            "source_type": source_info['type'],
                            "url": entry.get('link', ''),
                            "published": pub_date.strftime("%Y-%m-%d %H:%M") if pub_date else "시점 미상",
                            "published_dt": pub_date,
                            "freshness": self._calculate_freshness(pub_date),
                            "collection_time": self.collection_time.strftime("%Y-%m-%d %H:%M"),
                            "keywords": matched_keywords,
                            "importance": importance
                        })
            except Exception as e:
                sources_failed.append(f"{source_name}: {str(e)[:30]}")

        seen_titles = set()
        unique_news = []
        for news in all_news:
            if news['title'] not in seen_titles:
                seen_titles.add(news['title'])
                unique_news.append(news)
        unique_news.sort(key=lambda x: -x['importance'])

        return {
            "metadata": {
                "collection_time": self.collection_time.strftime("%Y-%m-%d %H:%M:%S"),
                "sources_used": sources_used,
                "sources_failed": sources_failed,
                "total_news": len(unique_news),
                "duplicates_removed": len(all_news) - len(unique_news),
                "hours_back": hours_back
            },
            "news": unique_news
        }


if __name__ == "__main__":
    collector = NewsCollector()
    result = collector.collect_news(hours_back=24)
    meta = result['metadata']
    print(f"수집 시각(KST): {meta['collection_time']}")
    print(f"활용 출처: {len(meta['sources_used'])}개")
    print(f"수집 뉴스: {meta['total_news']}건")
    for i, news in enumerate(result['news'][:10], 1):
        print(f"[{i}] {'★'*news['importance']} {news['title']}")
        print(f"    {news['published']} | {news['freshness']}")
