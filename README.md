# 📈 Stock Collector - AI 기반 한국 주식 분석 시스템

> **백엔드 구조 정리 완료** ✅
> 향후 통합 아키텍처 적용을 위한 백엔드 분리 및 Docker 컨테이너화

---

## 🏗️ 프로젝트 구조

```
stock_collector/
├── 🗂️ backend/                    # 백엔드 API 서버 (포트 8003)
│   ├── Dockerfile               # 백엔드 컨테이너 설정
│   ├── main.py                 # FastAPI 애플리케이션
│   ├── requirements.txt        # Python 의존성
│   ├── config.py               # 설정 관리
│   ├── database.py             # MongoDB 연결 관리
│   ├── collectors/             # 주식 데이터 수집
│   │   ├── stock_data_collector.py
│   │   ├── technical_analysis.py
│   │   └── technical_analyzer.py
│   ├── routers/                # FastAPI 라우터
│   ├── schemas/                # Pydantic 모델
│   ├── services/               # 비즈니스 로직
│   ├── strategies/             # 투자 전략 분석
│   ├── utils/                  # 유틸리티 함수
│   ├── repositories/           # 데이터 저장소 계층
│   ├── prompts/                # AI 프롬프트 템플릿
│   └── progress/               # 진행 상황 추적
│
├── 📁 backup_original/           # 원본 파일 백업
├── .env.template              # 환경변수 템플릿
├── ideation.md               # 아이디어 정리
└── 작업진행.md                # 작업 진행 상황
```

---

## ⚡ 주요 기능

### **📊 주식 데이터 수집**
- **실시간 데이터**: pykrx 기반 한국 주식 시장 데이터 수집
- **기술적 분석**: 이동평균, RSI, MACD 등 기술지표 계산
- **시장 스크리닝**: 시가총액, 거래량 기반 종목 필터링

### **🤖 AI 기반 분석**
- **Gemini AI**: Google Gemini API를 통한 종목 분석
- **자동화된 분석**: 일 50종목 한정 분석 시스템
- **투자 전략**: AI 기반 투자 추천 및 위험도 분석

### **⏰ 자동화 시스템**
- **일간 업데이트**: 19:00 일일 데이터 업데이트
- **분석 스케줄링**: 19:10~08:10 자동 분석 실행
- **진행 상황 추적**: MongoDB 기반 작업 상태 관리

---

## 🚀 실행 방법

### **Docker 컨테이너 실행**
```bash
cd backend
docker build -t stock-collector-backend .
docker run -d --name stock-collector-backend \
  -p 8003:8003 \
  --env-file ../.env \
  stock-collector-backend
```

### **개발 모드 실행**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### **접근 URL**
- **🔧 API 문서**: http://localhost:8003/docs
- **💓 헬스체크**: http://localhost:8003/health
- **📊 루트 엔드포인트**: http://localhost:8003/

---

## 🔧 환경변수 설정

### **필수 환경변수**
```env
# MongoDB 연결
MONGODB_URL=mongodb://localhost:27017

# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here

# 서버 설정
API_HOST=0.0.0.0
API_PORT=8003
DEBUG=false

# 로깅 설정
LOG_LEVEL=INFO
LOG_FILE_PATH=./logs/app.log

# 분석 설정
MIN_MARKET_CAP=100000000000  # 1000억원
MAX_ANALYSIS_PER_HOUR=50
ANALYSIS_TIME_LIMIT_MINUTES=50

# 스케줄 설정
DAILY_UPDATE_TIME=19:00
ANALYSIS_START_TIME=19:10
ANALYSIS_END_TIME=08:10
TIMEZONE=Asia/Seoul
```

### **환경변수 파일 생성**
```bash
cp .env.template .env
# .env 파일을 편집하여 실제 값 입력
```

---

## 🔄 API 엔드포인트

### **기본 엔드포인트**
```http
GET  /                    # API 정보
GET  /health             # 헬스체크 (DB, AI 서비스 상태)
```

### **주식 데이터**
```http
GET  /stocks/            # 주식 목록 조회
GET  /stocks/{code}      # 특정 종목 정보
POST /stocks/collect     # 데이터 수집 실행
```

### **스크리닝**
```http
GET  /screener/filter    # 조건별 종목 필터링
POST /screener/analysis  # 종목 분석 실행
```

### **AI 분석**
```http
POST /ai/analyze/{code}  # 특정 종목 AI 분석
GET  /ai/results         # 분석 결과 조회
POST /ai/strategy        # 투자 전략 생성
```

---

## 📊 데이터베이스 구조

### **MongoDB 컬렉션**
```
stock_data (주식 데이터)
├── daily_prices        # 일별 가격 데이터
├── technical_indicators # 기술적 지표
└── market_info         # 시장 정보

stock_analyzed (분석 결과)
├── ai_analysis         # AI 분석 결과
├── investment_strategy # 투자 전략
└── risk_assessment     # 위험도 평가

system_info (시스템)
├── analysis_progress   # 분석 진행 상황
├── job_schedules      # 작업 스케줄
└── error_logs         # 에러 로그
```

---

## 🛡️ 보안 및 제한사항

### **API 제한**
- **시간당 분석 한도**: 50종목
- **분석 시간 제한**: 50분
- **최소 시가총액**: 1000억원 이상

### **보안 설정**
- **CORS 정책**: 프로덕션 환경에서 제한 필요
- **API 키 보안**: 환경변수로 관리
- **로깅**: 모든 API 호출 및 에러 기록

---

## 📈 모니터링

### **시스템 상태 확인**
```bash
# 헬스체크
curl http://localhost:8003/health

# 시스템 상태
curl http://localhost:8003/
```

### **로그 확인**
```bash
# 애플리케이션 로그
tail -f backend/logs/app.log

# Docker 컨테이너 로그
docker logs -f stock-collector-backend
```

---

## 📝 개발 가이드

### **새 기능 추가**
1. **라우터 추가**: `backend/routers/`에 새 라우터 생성
2. **데이터 모델**: `backend/schemas/`에 Pydantic 모델 정의
3. **비즈니스 로직**: `backend/services/`에 서비스 클래스 구현
4. **데이터 접근**: `backend/repositories/`에 저장소 계층 구현

### **코드 품질**
```bash
# 코드 포맷팅
black backend/
isort backend/

# 린팅
flake8 backend/

# 테스트
pytest backend/
```

---

## 🔮 향후 계획

### **프론트엔드 개발 (예정)**
- React/Vue.js 기반 대시보드
- 실시간 차트 및 데이터 시각화
- 사용자 맞춤형 포트폴리오 관리

### **통합 아키텍처 적용**
- Caddy 리버스 프록시 통합
- my_portfolio 인프라와 연동
- 포트 8003 할당으로 멀티 서비스 환경 구축

---

## 🗂️ 파일 복구

### **원본 파일 위치**
```
backup_original/
├── main.py              # 원본 FastAPI 앱
├── collectors/          # 데이터 수집 모듈
├── routers/            # API 라우터
├── services/           # 비즈니스 로직
└── ...                 # 기타 원본 파일들
```

### **원본 구조 복구 방법**
```bash
# ⚠️ 주의: 현재 백엔드 구조가 덮어써집니다
cp -r backup_original/* .
```

---

## 🔗 관련 문서

- **📋 아이디어 정리**: [ideation.md](./ideation.md)
- **📊 작업 진행**: [작업진행.md](./작업진행.md)
- **🏗️ 통합 가이드**: `/my_portfolio/ai_process/INTEGRATION_GUIDE.md`

---

## 🆘 트러블슈팅

### **일반적인 문제**

**❌ MongoDB 연결 실패**
```bash
# 해결: MongoDB 서버 상태 확인
docker ps | grep mongo
curl http://localhost:8003/health
```

**❌ Google API 키 오류**
```env
# 해결: .env 파일에서 API 키 확인
GOOGLE_API_KEY=your_actual_api_key_here
```

**❌ pykrx 데이터 수집 오류**
```python
# 해결: 시장 개장 시간 확인 (09:00~15:30 KST)
# 주말/공휴일에는 데이터 수집 불가
```

---

**📅 구조 정리 완료**: 2024-09-26
**🔧 아키텍처**: FastAPI + MongoDB + Docker
**📊 상태**: ✅ 백엔드 준비 완료 (프론트엔드 개발 대기)