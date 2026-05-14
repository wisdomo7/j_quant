# 🎯 J Partner Quant System v4.0 — Streamlit Cloud 배포

정재영님 전용 모바일 매수 후보 발굴 시스템

## ✅ 포함 파일

| 파일 | 설명 |
|---|---|
| `app_v4.py` | 메인 Streamlit 앱 (비밀번호 보호) |
| `j_engine_v4.py` | J 엔진 — 듀얼 점수 분석 |
| `data_collector_v4.py` | 데이터 수집기 v4.0.6 |
| `master_data_manager.py` | 종목 마스터 캐시 관리 |
| `scheduler_v4.py` | 자동 스캔 스케줄러 |
| `requirements.txt` | Python 패키지 목록 |
| `.gitignore` | GitHub 제외 파일 |

## 🚀 배포 절차 (총 1시간)

### 1단계: GitHub 가입 + 저장소 생성 (10분)

1. `github.com` 접속 → "Sign up" 클릭
2. 이메일·비밀번호·사용자명 입력
3. 무료 가입 완료
4. 좌측 상단 "+ New repository" 클릭
5. Repository name: `j_quant_system`
6. **Private** 선택 (코드 비공개 필수)
7. "Create repository" 클릭

### 2단계: 파일 업로드 (15분)

**방법 A: 웹 브라우저 직접 업로드 (가장 쉬움)**
1. 방금 만든 저장소 페이지에서 "uploading an existing file" 클릭
2. 7개 파일 모두 드래그 앤 드롭
3. "Commit changes" 클릭

**방법 B: GitHub Desktop 사용 (자동 동기화)**
1. `desktop.github.com` 다운로드 + 설치
2. 로그인 → 저장소 Clone
3. 자동 생성된 폴더에 7개 파일 복사
4. "Commit to main" → "Push origin" 클릭

### 3단계: Streamlit Cloud 배포 (5분)

1. `share.streamlit.io` 접속
2. "Continue with GitHub" 클릭 (GitHub 계정 연동)
3. "New app" 클릭
4. 설정:
   - Repository: `j_quant_system`
   - Branch: `main`
   - Main file path: `app_v4.py`
   - App URL: `jung-quant` (또는 원하는 이름)
5. **"Advanced settings" 클릭**
6. **Python version**: `3.11` 선택 (중요)
7. **Secrets** 입력란에 다음 추가:
   ```
   APP_PASSWORD = "원하는비밀번호"
   ```
   예: `APP_PASSWORD = "jung2026"`
8. "Deploy" 클릭
9. **3~5분 대기** (자동으로 패키지 설치 + 실행)

### 4단계: 모바일 접속 (1분)

배포 완료 후 URL 예시:
```
https://jung-quant.streamlit.app
```

**핸드폰 접속**:
1. Chrome 또는 Safari로 URL 입력
2. 비밀번호 입력 (Secrets에 설정한 값)
3. 메뉴 → "홈 화면에 추가"
4. 앱처럼 사용 가능

## 🔐 보안

- **비밀번호 보호**: Secrets에 저장된 비밀번호만 알면 접속 가능
- **저장소 Private**: 코드 비공개로 외부 노출 차단
- **HTTPS 자동 적용**: Streamlit Cloud가 자동 처리

## ⚠️ 주의사항

### KRX 접속 한계
Streamlit Cloud 서버 IP는 한국 KRX에 차단됨. 해결:
- **자체 캐시 사용**: 노트북에서 캐시 만든 후 GitHub에 함께 업로드
- **FDR 우선**: pykrx보다 FinanceDataReader 위주로 작동
- **빠른 모드**: 관심 종목만 스캔할 때는 정상 작동

### 캐시 사전 업로드 (권장)
```
1. 노트북에서 python master_data_manager.py 실행
2. cache/stock_master.json 생성됨
3. GitHub 저장소에 cache 폴더 통째로 업로드
4. .gitignore에서 cache 부분 주석 처리 확인
```

## 🔄 업데이트 방법

코드 수정 후 GitHub에 푸시하면 **자동으로 재배포**됩니다.

1. GitHub Desktop에서 변경사항 Commit
2. Push origin
3. Streamlit Cloud가 자동 감지 → 1-2분 후 재배포 완료

## 📱 모바일 사용 팁

- **가로 모드 권장**: 표 데이터 가독성 향상
- **다크 모드 자동**: 시스템 설정 따름
- **홈 화면 추가**: PWA처럼 작동
- **3G/4G로도 사용 가능**: 데이터 사용량 적음

## 🆘 문제 해결

| 문제 | 해결 |
|---|---|
| "ModuleNotFoundError" 에러 | requirements.txt 확인, Python 3.11 선택 |
| 비밀번호 안 통과 | Streamlit Secrets에서 APP_PASSWORD 확인 |
| 스캔 결과 0개 | KRX 차단 가능성, 노트북 캐시 업로드 권장 |
| 페이지 로딩 매우 느림 | 첫 접속 시 정상, 30초 대기 |

## 💡 다음 단계 (선택)

2개월 사용 후 만족도 평가:
- ✅ 만족: 그대로 사용
- ❌ 불만족: Next.js + Vercel 재구축 검토

---

J Partner Quant System v4.0.2
정재영님 전용 / 비공개 시스템
