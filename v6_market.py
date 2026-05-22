# ============================================
# J Quant V6.0 - 실시간 시장 지표 (HTML 파싱)
# 네이버 금융 페이지 직접 파싱
# ============================================
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict


class MarketIndexCollector:
    """실시간 시장 지표 자동 수집 (네이버 금융 HTML)"""
    
    def __init__(self):
        self.collection_time = None
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    def get_realtime_index(self) -> Dict:
        self.collection_time = datetime.now()
        
        return {
            'collection_time': self.collection_time.strftime("%Y-%m-%d %H:%M:%S"),
            'kospi': self._get_index('KOSPI'),
            'kosdaq': self._get_index('KOSDAQ'),
            'usd_krw': self._get_exchange(),
        }
    
    def _get_index(self, code: str) -> Dict:
        """지수 실시간 (네이버 금융 HTML)"""
        try:
            url = f"https://finance.naver.com/sise/sise_index.naver?code={code}"
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'euc-kr'
            soup = BeautifulSoup(r.text, 'html.parser')
            
            now_value = soup.select_one('#now_value')
            change_rate = soup.select_one('#change_value_and_rate')
            
            if now_value:
                price = now_value.text.strip()
                change = change_rate.text.strip().replace('\n', ' ').replace('\t', '') if change_rate else ""
                
                return {
                    'price': price,
                    'change': change,
                    'status': 'success'
                }
            else:
                return {'status': 'failed', 'error': '셀렉터 없음'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)[:50]}
    
    def _get_exchange(self) -> Dict:
        """원/달러 환율 (네이버 금융 HTML)"""
        try:
            url = "https://finance.naver.com/marketindex/"
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'euc-kr'
            soup = BeautifulSoup(r.text, 'html.parser')
            
            usd = soup.select_one('#exchangeList .value')
            
            if usd:
                return {'price': usd.text.strip(), 'status': 'success'}
            else:
                return {'status': 'failed', 'error': '셀렉터 없음'}
        except Exception as e:
            return {'status': 'failed', 'error': str(e)[:50]}


if __name__ == "__main__":
    print("=" * 60)
    print("V6.0 MarketIndexCollector — 실시간 시장 지표")
    print("=" * 60)
    
    collector = MarketIndexCollector()
    print("\n🔄 실시간 지수 수집 중...")
    
    result = collector.get_realtime_index()
    
    print(f"\n⏰ 수집 시각: {result['collection_time']}")
    print("─" * 60)
    
    kospi = result['kospi']
    if kospi['status'] == 'success':
        print(f"🇰🇷 코스피: {kospi['price']} ({kospi['change']})")
    else:
        print(f"🇰🇷 코스피: 실패 ({kospi.get('error')})")
    
    kosdaq = result['kosdaq']
    if kosdaq['status'] == 'success':
        print(f"🇰🇷 코스닥: {kosdaq['price']} ({kosdaq['change']})")
    else:
        print(f"🇰🇷 코스닥: 실패 ({kosdaq.get('error')})")
    
    fx = result['usd_krw']
    if fx['status'] == 'success':
        print(f"💵 원/달러: {fx['price']}")
    else:
        print(f"💵 원/달러: 실패 ({fx.get('error')})")
    
    print("\n" + "=" * 60)
    print(f"✅ 테스트 완료 ({datetime.now().strftime('%H:%M:%S')})")
    print("=" * 60)