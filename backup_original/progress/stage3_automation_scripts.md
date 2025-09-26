# 3단계: 자동화 스크립트 개발

> **참고:** 작업진행 md파일을 읽고 이어서 작업을 진행하고, 진행하면서 해당내용을 프로그래스 폴더에 각 단계별로 별개의 md파일을 별도로 생성해서 관리하세요.

## 목표
장애 복구 기능이 내장된 자동화 스크립트 개발

## 스크립트 구성

### 3.1 Part 1: 초기 설정 (manual_setup.py)
- **실행 방식:** 사용자 수동 실행
- **기능:**
  - `system_info.target_tickers` 컬렉션 초기화
  - 과거 300일치 데이터 초기 적재
  - 시가총액 1000억 원 이상 종목 필터링

### 3.2 Part 2: 일일 데이터 수집 (daily_update.py)  
- **실행 시간:** 매 영업일 19:00 KST (cron)
- **Self-Healing 로직:**
  1. `job_status` 확인하여 마지막 성공 날짜 탐지
  2. 마지막 성공일 다음날부터 오늘까지 루프 실행
  3. 영업일 여부 확인
  4. `pykrx`를 통한 데이터 수집 및 `upsert`
  5. 실행 상태를 `job_status`에 기록

### 3.3 Part 3: 시간 분산 분석 (hourly_analysis.py)
- **실행 시간:** 매 영업일 19:10 ~ 익일 08:10, 매시간 10분 (cron)
- **State-Based Trigger & Recovery:**
  1. 선행 작업(`daily_update`) 완료 확인
  2. `last_analyzed_date` 기반 분석 대상 선정
  3. 시가총액 순 우선순위 처리
  4. 시간당 할당량 분석 수행
  5. 50분 실행 시간 제한 안전장치

## 세부 작업 목록

### 3.1 공통 유틸리티
- [x] utils/ 폴더 생성
- [x] 날짜 처리, 영업일 계산 유틸리티
- [x] 로깅 설정 및 관리

### 3.2 데이터 수집 모듈
- [x] collectors/ 폴더 생성  
- [x] pykrx 기반 주가 데이터 수집기
- [x] 기술적 지표 계산 모듈

### 3.3 각 스크립트 구현
- [x] manual_setup.py - 초기 설정 스크립트
- [x] daily_update.py - 일일 데이터 수집 스크립트  
- [x] hourly_analysis.py - 시간 분산 분석 스크립트

### 3.4 장애 복구 로직
- [x] 작업 상태 추적 시스템
- [x] 실패 시 재시도 로직
- [x] 데이터 무결성 검증

## 구현된 컴포넌트

### 유틸리티 모듈 (`utils/`)
- `date_utils.py` - 한국 주식시장 영업일 계산
- 한국 공휴일 처리
- KST 시간대 관리
- 시장 개장시간 확인

### 데이터 수집기 (`collectors/`)
- `StockDataCollector` - pykrx 기반 주가 데이터 수집
- `TechnicalAnalyzer` - 기술적 지표 계산
- 대형주 필터링 기능
- 데이터 무결성 검증

### 자동화 스크립트들

#### `manual_setup.py` - 초기 설정
- 시가총액 1000억 이상 종목 수집
- 300일 과거 데이터 초기 적재
- 대화형 설정 인터페이스

#### `daily_update.py` - 일일 데이터 수집 (Self-Healing)
- 마지막 성공일 자동 탐지
- 누락된 영업일 데이터 자동 보완
- `cron: 0 19 * * 1-5` (평일 19:00 KST)

#### `hourly_analysis.py` - 시간분산 분석 (State-Based Recovery)
- 선행 작업(daily_update) 완료 확인
- 미분석 종목 우선순위 처리
- 50분 실행시간 제한
- `cron: 10 19-23,0-8 * * 1-5`

### 장애 복구 기능

#### Self-Healing (daily_update.py)
1. `job_status` 확인으로 마지막 성공 날짜 탐지
2. 마지막 성공일 다음날부터 어제까지 루프
3. 영업일 여부 확인 후 데이터 수집
4. 실행 상태 추적 및 기록

#### State-Based Recovery (hourly_analysis.py) 
1. `daily_update` 완료 상태 확인
2. `last_analyzed_date` 기반 미분석 종목 선정
3. 시가총액 순 우선순위 처리
4. 시간당 할당량 분석 수행

## 진행 상황
- 🟢 유틸리티 모듈 완료
- 🟢 데이터 수집 모듈 완료  
- 🟢 자동화 스크립트 완료
- 🟢 장애 복구 로직 완료
- 🟢 3단계 완료

## 다음 단계
완료 후 → [4단계: API 서버 구축](stage4_api_layer.md)로 진행