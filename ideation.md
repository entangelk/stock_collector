# **[최종 설계] AI 기반 주식 분석 데이터 파이프라인 구축**

## **1. 프로젝트 개요**

### **1.1. 목표**
KOSPI 및 KOSDAQ 시장의 특정 조건(시가총액 1000억 원 이상)을 만족하는 종목들의 일일 주가 데이터를 수집, 정제, 분석하고, 최종적으로는 정적/동적 필터링 및 생성형 AI 분석 결과를 API 형태로 제공하는, 장애 복구 기능이 내장된 자동화 파이프라인을 구축한다.

### **1.2. 시스템 환경**
- **서버:** Cloud Server (AWS EC2, Google Cloud VM 등)
- **운영체제:** Ubuntu 22.04 LTS
- **핵심 기술 스택:**
  - **언어:** Python 3.10+
  - **데이터 수집:** `pykrx`, `pandas`
  - **데이터베이스:** MongoDB
  - **백엔드 API:** FastAPI
  - **AI 분석:** Google Gemini (via `langchain-google-genai`)
  - **프로세스 관리:** `cron` (Ubuntu 내장 스케줄러)

---

## **2. 데이터베이스 설계 (MongoDB)**

모든 시간 데이터는 **UTC**를 기준으로 저장한다.

### **2.1. `system_info` DB: 시스템 메타데이터 관리**
- **`target_tickers` Collection:** 추적 대상 종목 목록.
  ```json
  {
    "ticker": "005930",
    "name": "삼성전자",
    "market_cap": 60000000000000,
    "added_date": "2025-09-15",
    "is_active": true,
    "last_analyzed_date": "2025-09-14" // 분석이 성공적으로 완료된 마지막 KST 날짜
  }
  ```
- **`job_status` Collection:** 자동화 스크립트의 실행 상태 기록.
  ```json
  {
    "_id": "2025-09-15_daily_update",
    "job_name": "daily_update",
    "date_kst": "2025-09-15",
    "status": "completed", // running, completed, failed
    "start_time_utc": "2025-09-15T10:00:00Z",
    "end_time_utc": "2025-09-15T10:05:12Z"
  }
  ```

### **2.2. `stock_data` DB: 원본 OHLCV 데이터**
- 티커별 Collection으로 구성 (예: `005930`). 데이터는 수정 없이 추가만 된다.

### **2.3. `stock_analyzed` DB: 기술적 분석 완료 데이터**
- 티커별 Collection으로 구성. 데이터는 매일 재계산되어 덮어씌워진다.

---

## **3. 처리 계층: 자동화 스크립트 설계 (장애 복구 기능 내장)**

### **3.1. Part 1: 초기 설정 (`manual_setup.py`)**
- **실행:** 사용자가 서버에 접속하여 직접 수동 실행.
- **역할:** `system_info.target_tickers` 컬렉션 초기화 및 과거 300일치 데이터(`stock_data`) 초기 적재.

### **3.2. Part 2: 일일 데이터 수집 (`daily_update.py`)**
- **실행:** `cron`을 통해 **매 영업일 19:00 KST**에 실행.
- **핵심 로직 (Self-Healing):**
    1.  `job_status`를 확인하여 마지막으로 성공한 날짜를 찾는다.
    2.  마지막 성공일의 다음 날부터 오늘(KST 기준)까지의 모든 날짜에 대해 루프를 실행한다.
    3.  루프 안에서 각 날짜가 영업일인지 확인한다.
    4.  영업일이라면, 해당 날짜의 데이터를 `pykrx`로 수집하여 `stock_data` DB에 `upsert`한다.
    5.  이를 통해 하루 이상 장애가 발생해도, 다음 실행 시 빠진 모든 영업일 데이터를 스스로 따라잡아 수집한다.
    6.  실행 시작과 끝(성공/실패)을 `job_status`에 기록한다.

### **3.3. Part 3: 시간 분산 분석 (`hourly_analysis.py`)**
- **실행:** `cron`을 통해 **매 영업일 19:10 ~ 익일 08:10, 매시간 10분**에 실행.
- **핵심 로직 (State-Based Trigger & Recovery):**
    1.  **선행 작업 확인:** `job_status`를 조회하여 오늘 날짜의 `daily_update` 작업이 `completed` 상태인지 확인한다. 그렇지 않다면 즉시 종료하여 데이터 오염을 방지한다.
    2.  **상태 기반 복구:** `system_info.target_tickers`에서 `last_analyzed_date`가 오늘 날짜가 아닌 모든 종목을 분석 대상으로 선정한다. (어제 분석이 중단되었다면, 밀린 작업이 자동으로 포함됨)
    3.  **우선순위 처리:** 분석 대상을 시가총액(`market_cap`) 순으로 정렬한다.
    4.  시간당 할당량만큼 순차적으로 분석을 수행하고, 성공한 종목의 `last_analyzed_date`를 오늘 날짜로 업데이트한다.
    5.  50분 실행 시간 제한 안전장치를 포함한다.

---

## **4. API 제공 계층: FastAPI 서버 설계**

### **4.1. 기본 데이터 API (`GET /stocks`, `GET /stocks/{ticker}`)**
- 추적 종목 리스트 및 특정 종목의 상세 분석 데이터 제공.

### **4.2. 스크리너 API (`GET /screener?strategy_name=...`)**
- 특정 기술적 조건(예: MACD 골든크로스)을 만족하는 종목을 동적으로 필터링하여 제공.
- `strategies/` 폴더에 전략을 모듈화하여 확장성을 확보.

### **4.3. AI 분석 API (`POST /ai/analysis`)**
- 스크리너를 통해 필터링된 종목 리스트를 입력받아, 지정된 프롬프트에 따라 Gemini가 생성한 분석 결과를 제공.
- `prompts/` 폴더에 프롬프트와 실행 로직을 모듈화하여 관리.

---

## **5. 인프라 및 배포 (Ubuntu 기준)**

### **5.1. 서버 권장 사양**
- **RAM: 4GB 이상.** DB 기반의 다중 서비스를 안정적으로 운영하고, 디스크 I/O 병목을 유발하는 스래싱(Thrashing) 현상을 방지하기 위한 필수 사양.

### **5.2. 초기 서버 설정**
```bash
# 1. 패키지 업데이트
sudo apt-get update && sudo apt-get upgrade -y

# 2. MongoDB 설치 (공식 문서 참조 권장)
# https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/

# 3. Python 및 가상환경 도구 설치
sudo apt-get install python3.10-venv python3-pip -y

# 4. 프로젝트 디렉토리 및 로그 디렉토리 생성
mkdir -p /home/ubuntu/stock_project/logs
cd /home/ubuntu/stock_project

# 5. 가상환경 설정
python3 -m venv venv
source venv/bin/activate

# 6. 필요 패키지 설치 (추후 requirements.txt 파일로 관리)
pip install pykrx pandas pymongo fastapi "uvicorn[standard]" gunicorn langchain-google-genai schedule
```

### **5.3. 자동화 스크립트 스케줄링 (`crontab`)**
- `crontab -e` 명령어로 편집기 실행 후 아래 내용 추가:
- **로그 리다이렉션(`>> ... 2>&1`)**: 스크립트의 모든 정상/오류 출력을 `cron.log` 파일에 기록하여 장애 발생 시 원인 분석을 용이하게 함.
```cron
# KST(UTC+9) 시간대 기준으로 Cron 작업 실행
CRON_TZ=Asia/Seoul

# 매주 월-금 19:00, 일일 데이터 수집 스크립트 실행
0 19 * * 1-5 /home/ubuntu/stock_project/venv/bin/python3 /home/ubuntu/stock_project/daily_update.py >> /home/ubuntu/stock_project/logs/cron.log 2>&1

# 매주 월-금 19:10 ~ 23:10, 시간 분산 분석 스크립트 실행
10 19-23 * * 1-5 /home/ubuntu/stock_project/venv/bin/python3 /home/ubuntu/stock_project/hourly_analysis.py >> /home/ubuntu/stock_project/logs/cron.log 2>&1

# 매주 월-금 00:10 ~ 08:10, 시간 분산 분석 스크립트 실행 (다음날)
10 0-8 * * 1-5 /home/ubuntu/stock_project/venv/bin/python3 /home/ubuntu/stock_project/hourly_analysis.py >> /home/ubuntu/stock_project/logs/cron.log 2>&1
```

### **5.4. API 서버 실행 (Production)**
- `gunicorn`을 사용하여 FastAPI 애플리케이션을 안정적으로 실행.
```bash
# /home/ubuntu/stock_project 디렉토리에서 실행
# API 서버 코드 파일이 main.py라고 가정
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000
# -w 4: 4개의 워커 프로세스 사용 (CPU 코어 수에 맞춰 조절)
# -k uvicorn.workers.UvicornWorker: Uvicorn으로 실행
# main:app: main.py 파일의 app 객체를 의미
# -b 0.0.0.0:8000: 8000번 포트로 외부 접속 허용
```