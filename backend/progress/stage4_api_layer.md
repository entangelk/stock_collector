# 4단계: API 서버 구축

> **참고:** 작업진행 md파일을 읽고 이어서 작업을 진행하고, 진행하면서 해당내용을 프로그래스 폴더에 각 단계별로 별개의 md파일을 별도로 생성해서 관리하세요.

## 목표
FastAPI 기반 주식 데이터 분석 API 서버 구축

## API 엔드포인트 설계

### 4.1 기본 데이터 API
```
GET /stocks - 추적 종목 리스트 조회
GET /stocks/{ticker} - 특정 종목 상세 분석 데이터 조회
```

### 4.2 스크리너 API
```
GET /screener?strategy_name=... - 기술적 조건 기반 종목 필터링
```
- 동적 필터링 시스템
- `strategies/` 폴더 모듈화 구조
- 확장 가능한 전략 패턴

### 4.3 AI 분석 API
```  
POST /ai/analysis - Gemini 기반 종목 분석
```
- 스크리너 결과를 입력받아 AI 분석 수행
- `prompts/` 폴더 프롬프트 관리
- Google Gemini 연동 (langchain-google-genai)

## 세부 작업 목록

### 4.1 FastAPI 애플리케이션 구조
- [x] main.py - 애플리케이션 엔트리포인트  
- [x] routers/ 폴더 - 라우터 모듈 분리
- [x] middleware/ 폴더 - 미들웨어 구현

### 4.2 API 라우터 구현
- [x] stocks.py - 기본 주식 데이터 API
- [x] screener.py - 스크리너 API
- [x] ai_analysis.py - AI 분석 API

### 4.3 비즈니스 로직 계층
- [x] services/ 폴더 생성
- [x] 데이터 처리 및 분석 서비스
- [x] AI 분석 서비스

### 4.4 스크리너 전략 시스템
- [x] strategies/ 폴더 생성
- [x] 기술적 분석 전략 모듈들
  - [x] macd_golden_cross.py - MACD 골든크로스 전략
  - [x] rsi_oversold.py - RSI 과매도 전략
  - [x] bollinger_squeeze.py - 볼린저 밴드 스퀴즈 전략
  - [x] moving_average_crossover.py - 이동평균 크로스오버 전략

### 4.5 AI 프롬프트 관리
- [x] prompts/ 폴더 생성
- [x] 분석 타입별 프롬프트 템플릿
  - [x] technical_analysis_prompt.py - 기술적 분석
  - [x] market_overview_prompt.py - 시장 개요 분석
  - [x] trading_opportunity_prompt.py - 매매 기회 분석
  - [x] risk_assessment_prompt.py - 리스크 평가
- [x] Gemini API 연동 모듈

### 4.6 응답 모델 및 검증
- [x] schemas/ 폴더 생성 (2단계에서 완료)
- [x] Pydantic 응답 모델 정의
- [x] API 문서화 (Swagger/OpenAPI)

## 구현된 API 엔드포인트

### 주식 데이터 API (`/stocks`)
- `GET /stocks` - 추적 종목 리스트 조회
- `GET /stocks/{ticker}` - 특정 종목 상세 분석 데이터
- `GET /stocks/{ticker}/raw` - 원본 OHLCV 데이터  
- `GET /stocks/{ticker}/statistics` - 종목 통계
- `POST /stocks/{ticker}/refresh` - 분석 강제 갱신

### 스크리너 API (`/screener`)
- `GET /screener/strategies` - 사용 가능한 전략 목록
- `GET /screener/strategies/{name}` - 특정 전략 상세 정보
- `POST /screener` - 전략 기반 종목 스크리닝
- `GET /screener` - GET 방식 스크리닝
- `POST /screener/{strategy}/detailed` - 상세 분석 결과

### AI 분석 API (`/ai`)
- `GET /ai/model-info` - AI 모델 정보
- `GET /ai/prompts` - 사용 가능한 프롬프트 목록
- `POST /ai/analysis` - 종목 AI 분석
- `GET /ai/analysis` - GET 방식 AI 분석
- `POST /ai/screener-analysis` - 스크리너 결과 AI 분석
- `POST /ai/custom-analysis` - 커스텀 AI 분석

## 구현된 주요 기능

### 스크리너 전략
1. **MACD Golden Cross** - MACD 골든크로스 패턴 탐지
2. **RSI Oversold** - RSI 과매도 구간 반등 기회 탐지  
3. **Bollinger Squeeze** - 볼린저 밴드 스퀴즈 패턴 탐지
4. **Moving Average Crossover** - 이동평균 크로스오버 패턴 탐지

### AI 분석 프롬프트
1. **Technical Analysis** - 상세 기술적 분석
2. **Market Overview** - 시장 개요 및 섹터 분석
3. **Trading Opportunity** - 구체적 매매 전략 제시
4. **Risk Assessment** - 리스크 평가 및 포트폴리오 관리

### 통합 기능
- 스크리너로 종목 선별 → AI로 분석하는 파이프라인
- 실시간 헬스체크 (`/health`)
- 자동 API 문서화 (FastAPI Swagger UI)
- 에러 처리 및 로깅

## 진행 상황
- 🟢 FastAPI 애플리케이션 구조 완료
- 🟢 주식 데이터 API 완료
- 🟢 스크리너 API 및 전략 시스템 완료
- 🟢 AI 분석 API 및 프롬프트 시스템 완료
- 🟢 서비스 계층 구현 완료
- 🟢 4단계 완료

## 다음 단계
완료 후 → [5단계: 인프라 및 배포](stage5_infrastructure.md)로 진행