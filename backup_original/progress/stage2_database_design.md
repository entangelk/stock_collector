# 2단계: 데이터베이스 설계

> **참고:** 작업진행 md파일을 읽고 이어서 작업을 진행하고, 진행하면서 해당내용을 프로그래스 폴더에 각 단계별로 별개의 md파일을 별도로 생성해서 관리하세요.

## 목표
MongoDB 기반 주식 데이터 저장 및 관리 시스템 설계

## 데이터베이스 구조

### 2.1 system_info DB: 시스템 메타데이터 관리
#### target_tickers Collection
```json
{
  "ticker": "005930",
  "name": "삼성전자", 
  "market_cap": 60000000000000,
  "added_date": "2025-09-15",
  "is_active": true,
  "last_analyzed_date": "2025-09-14"
}
```

#### job_status Collection  
```json
{
  "_id": "2025-09-15_daily_update",
  "job_name": "daily_update",
  "date_kst": "2025-09-15", 
  "status": "completed",
  "start_time_utc": "2025-09-15T10:00:00Z",
  "end_time_utc": "2025-09-15T10:05:12Z"
}
```

### 2.2 stock_data DB: 원본 OHLCV 데이터
- 티커별 Collection 구성 (예: `005930`)
- 수정 없이 추가만 수행

### 2.3 stock_analyzed DB: 기술적 분석 완료 데이터  
- 티커별 Collection 구성
- 매일 재계산되어 덮어씌워짐

## 세부 작업 목록

### 2.1 데이터베이스 연결 모듈
- [x] database.py - MongoDB 연결 관리
- [x] 연결 풀 설정 및 예외 처리

### 2.2 데이터 모델 정의
- [x] schemas/models.py - Pydantic 모델 정의
- [x] 스키마 검증 로직

### 2.3 데이터 액세스 계층
- [x] repositories/ 폴더 생성
- [x] 각 컬렉션별 CRUD 조작 구현

### 2.4 데이터베이스 초기화
- [x] db_init.py - 데이터베이스 초기화 스크립트
- [x] 인덱스 생성 및 헬스체크

## 구현된 컴포넌트

### 데이터베이스 연결 (`database.py`)
- MongoDB 연결 관리자
- 자동 재연결 및 예외 처리
- 데이터베이스별 컬렉션 접근자

### 데이터 모델 (`schemas/`)
- `TargetTicker` - 추적 대상 종목
- `JobStatusRecord` - 작업 상태 기록
- `OHLCVData` - 주가 데이터
- `AnalyzedStockData` - 분석된 주식 데이터
- API 요청/응답 모델들

### 리포지토리 계층 (`repositories/`)
- `BaseRepository` - 공통 CRUD 연산
- `TargetTickerRepository` - 대상 종목 관리
- `JobStatusRepository` - 작업 상태 관리
- `StockDataRepository` - 주가 데이터 관리

### 데이터베이스 초기화
- 자동 인덱스 생성
- 샘플 데이터 생성
- 헬스체크 기능

## 진행 상황
- 🟢 데이터베이스 연결 모듈 완료
- 🟢 Pydantic 모델 정의 완료
- 🟢 리포지토리 계층 구현 완료
- 🟢 2단계 완료

## 다음 단계
완료 후 → [3단계: 자동화 스크립트 개발](stage3_automation_scripts.md)로 진행