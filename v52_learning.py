# ============================================
# J Quant V5.2 - 학습 + 자동 알림 모듈
# 사용자 패턴 학습, 백테스팅, 텔레그램 알림
# ============================================
import json
import os
from datetime import datetime
from typing import Dict, List


class UserPatternLearner:
    """사용자 매매 패턴 학습 (V1.3 ⑨)"""
    
    def __init__(self):
        # 데이터 폴더 자동 생성
        self.data_dir = "./data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.pattern_path = os.path.join(self.data_dir, "user_pattern.json")
    
    def record_trade(self, trade: Dict):
        """매매 기록 저장"""
        history = self._load()
        if 'trades' not in history:
            history['trades'] = []
        
        trade['timestamp'] = datetime.now().isoformat()
        history['trades'].append(trade)
        self._save(history)
        print(f"✓ 매매 기록 저장: {trade.get('stock', '')} {trade.get('action', '')}")
    
    def analyze_pattern(self) -> Dict:
        """누적 매매 패턴 분석"""
        history = self._load()
        trades = history.get('trades', [])
        
        if len(trades) < 3:
            return {
                "status": "데이터 부족",
                "trade_count": len(trades),
                "need_minimum": 30,
                "message": f"30회 이상 매매 누적 시 의미있는 패턴 분석 가능 (현재 {len(trades)}회)"
            }
        
        # 강점 분석
        strengths = []
        weaknesses = []
        
        # J 추천 신속 진입
        fast_entries = [t for t in trades if t.get('j_recommended') and t.get('entry_speed') == 'fast']
        if len(fast_entries) >= 3:
            strengths.append("✅ J 추천 신속 진입 패턴")
        
        # 손절 미루기
        delayed_stops = [t for t in trades if t.get('action') == '손절' and t.get('delay_days', 0) > 1]
        if len(delayed_stops) >= 1:
            weaknesses.append(f"❌ 손절 미루기 패턴 (자동 보완: ★★★ 강도)")
        
        # 승률
        completed = [t for t in trades if t.get('result') in ['익절', '손절']]
        wins = [t for t in completed if t.get('result') == '익절']
        win_rate = round(len(wins) / len(completed) * 100, 1) if completed else 0
        
        return {
            "trade_count": len(trades),
            "strengths": strengths,
            "weaknesses": weaknesses,
            "win_rate": win_rate,
            "completed_trades": len(completed)
        }
    
    def _load(self) -> Dict:
        if not os.path.exists(self.pattern_path):
            return {}
        try:
            with open(self.pattern_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save(self, data: Dict):
        with open(self.pattern_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class BacktestingEngine:
    """추천 적중률 자동 계산"""
    
    def __init__(self):
        self.data_dir = "./data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.rec_path = os.path.join(self.data_dir, "recommendations.json")
    
    def record_recommendation(self, rec: Dict):
        """J 추천 기록"""
        history = self._load()
        if 'recommendations' not in history:
            history['recommendations'] = []
        
        rec['timestamp'] = datetime.now().isoformat()
        rec['status'] = '진행중'
        history['recommendations'].append(rec)
        self._save(history)
    
    def update_result(self, stock_code: str, current_price: float):
        """추천 결과 자동 업데이트"""
        history = self._load()
        updated = 0
        
        for rec in history.get('recommendations', []):
            if rec.get('code') == stock_code and rec.get('status') == '진행중':
                entry = rec.get('entry_price', 0)
                target = rec.get('target_price', 0)
                stop = rec.get('stop_loss', 0)
                
                if current_price >= target:
                    rec['status'] = '익절 달성'
                    rec['return_pct'] = round((current_price - entry) / entry * 100, 2)
                    updated += 1
                elif current_price <= stop:
                    rec['status'] = '손절 도달'
                    rec['return_pct'] = round((current_price - entry) / entry * 100, 2)
                    updated += 1
        
        self._save(history)
        return updated
    
    def calculate_accuracy(self) -> Dict:
        """누적 적중률 계산"""
        history = self._load()
        recs = history.get('recommendations', [])
        
        completed = [r for r in recs if r.get('status') in ['익절 달성', '손절 도달']]
        
        if not completed:
            return {
                "accuracy": 0,
                "total_recommendations": len(recs),
                "completed": 0,
                "message": "완료된 추천 데이터 부족"
            }
        
        wins = [r for r in completed if r.get('status') == '익절 달성']
        accuracy = round(len(wins) / len(completed) * 100, 1)
        avg_return = round(
            sum(r.get('return_pct', 0) for r in completed) / len(completed), 2
        )
        
        return {
            "accuracy_pct": accuracy,
            "total_recommendations": len(recs),
            "completed": len(completed),
            "wins": len(wins),
            "avg_return_pct": avg_return
        }
    
    def _load(self) -> Dict:
        if not os.path.exists(self.rec_path):
            return {}
        try:
            with open(self.rec_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def _save(self, data: Dict):
        with open(self.rec_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class TelegramAlerter:
    """텔레그램 자동 알림 (V1.4 ⑫)"""
    
    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = chat_id or os.environ.get('TELEGRAM_CHAT_ID', '')
    
    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)
    
    def send_alert(self, message: str, priority: str = "normal") -> bool:
        """텔레그램 메시지 전송"""
        if not self.is_configured():
            print(f"⚠️ 텔레그램 미설정 (스킵): {message[:50]}")
            return False
        
        try:
            import requests
            prefix = {
                "critical": "🚨🚨🚨 ",
                "high": "🚨 ",
                "normal": "📊 ",
                "info": "💡 "
            }.get(priority, "")
            
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": prefix + message
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"⚠️ 알림 전송 실패: {e}")
            return False


# ============================================
# 테스트
# ============================================
if __name__ == "__main__":
    print("=" * 50)
    print("V5.2 학습 + 알림 모듈 테스트")
    print("=" * 50)
    
    # 테스트 1: 정재영님 5/20 매매 기록
    print("\n[테스트 1] 사용자 패턴 학습")
    learner = UserPatternLearner()
    
    # NC 손절 기록 (5일 미루다 결국 손절)
    learner.record_trade({
        "stock": "NC소프트",
        "action": "손절",
        "type": "장기",
        "delay_days": 5,
        "result": "손절",
        "amount": -549896
    })
    
    # 비에이치아이 V1.2 물타기 (J 추천 신속 진입)
    learner.record_trade({
        "stock": "비에이치아이",
        "action": "물타기",
        "type": "스윙",
        "j_recommended": True,
        "entry_speed": "fast",
        "result": "익절",
        "amount": 54900
    })
    
    # 현대차 추가 매수
    learner.record_trade({
        "stock": "현대차",
        "action": "매수",
        "type": "장기",
        "j_recommended": True,
        "entry_speed": "fast",
        "result": "익절"
    })
    
    pattern = learner.analyze_pattern()
    print(f"매매 기록: {pattern.get('trade_count', 0)}회")
    print(f"강점: {pattern.get('strengths', [])}")
    print(f"약점: {pattern.get('weaknesses', [])}")
    print(f"승률: {pattern.get('win_rate', 0)}%")
    
    # 테스트 2: 추천 적중률
    print("\n[테스트 2] 백테스팅")
    backtest = BacktestingEngine()
    
    backtest.record_recommendation({
        "code": "034020",
        "name": "두산에너빌리티",
        "entry_price": 101900,
        "target_price": 130000,
        "stop_loss": 90900,
        "confidence": 82
    })
    
    # 두산E 현재가 108,000원으로 결과 업데이트
    backtest.update_result("034020", 108000)
    
    accuracy = backtest.calculate_accuracy()
    print(f"누적 추천: {accuracy.get('total_recommendations', 0)}건")
    print(f"완료: {accuracy.get('completed', 0)}건")
    print(f"메시지: {accuracy.get('message', '')}")
    
    # 테스트 3: 텔레그램 알림 (미설정 상태)
    print("\n[테스트 3] 텔레그램 알림")
    alerter = TelegramAlerter()
    print(f"텔레그램 설정 상태: {alerter.is_configured()}")
    alerter.send_alert("V5.2 시스템 가동 시작!", priority="info")
    
    print("\n" + "=" * 50)
    print("V5.2 테스트 완료!")
    print("data 폴더 자동 생성됨 → 매매 기록 누적 시작")
    print("=" * 50)