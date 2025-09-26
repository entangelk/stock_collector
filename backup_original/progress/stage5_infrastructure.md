# 5단계: 인프라 및 배포

> **참고:** 작업진행 md파일을 읽고 이어서 작업을 진행하고, 진행하면서 해당내용을 프로그래스 폴더에 각 단계별로 별개의 md파일을 별도로 생성해서 관리하세요.

## 목표
Ubuntu 서버 환경에서 안정적인 운영을 위한 인프라 구축 및 배포

## 서버 환경

### 5.1 권장 사양
- **RAM:** 4GB 이상
- **OS:** Ubuntu 22.04 LTS
- **플랫폼:** AWS EC2, Google Cloud VM 등

### 5.2 초기 서버 설정 스크립트
```bash
# 패키지 업데이트
sudo apt-get update && sudo apt-get upgrade -y

# MongoDB 설치
# https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/

# Python 및 가상환경 도구 설치  
sudo apt-get install python3.10-venv python3-pip -y

# 프로젝트 디렉토리 생성
mkdir -p /home/ubuntu/stock_project/logs
cd /home/ubuntu/stock_project

# 가상환경 설정
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install pykrx pandas pymongo fastapi "uvicorn[standard]" gunicorn langchain-google-genai schedule
```

## 자동화 스케줄링

### 5.3 Crontab 설정
```cron
# KST(UTC+9) 시간대 설정
CRON_TZ=Asia/Seoul

# 매주 월-금 19:00, 일일 데이터 수집
0 19 * * 1-5 /home/ubuntu/stock_project/venv/bin/python3 /home/ubuntu/stock_project/daily_update.py >> /home/ubuntu/stock_project/logs/cron.log 2>&1

# 매주 월-금 19:10 ~ 23:10, 시간 분산 분석  
10 19-23 * * 1-5 /home/ubuntu/stock_project/venv/bin/python3 /home/ubuntu/stock_project/hourly_analysis.py >> /home/ubuntu/stock_project/logs/cron.log 2>&1

# 매주 월-금 00:10 ~ 08:10, 시간 분산 분석 (다음날)
10 0-8 * * 1-5 /home/ubuntu/stock_project/venv/bin/python3 /home/ubuntu/stock_project/hourly_analysis.py >> /home/ubuntu/stock_project/logs/cron.log 2>&1
```

### 5.4 API 서버 운영 (Production)
```bash
# Gunicorn을 사용한 FastAPI 서버 실행
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000
# -w 4: 4개 워커 프로세스
# -k uvicorn.workers.UvicornWorker: Uvicorn 워커 사용
# main:app: main.py의 app 객체
# -b 0.0.0.0:8000: 8000번 포트 외부 접속 허용
```

## 세부 작업 목록

### 5.1 배포 스크립트
- [ ] deploy/ 폴더 생성
- [ ] setup_server.sh - 서버 초기 설정 스크립트
- [ ] install_dependencies.sh - 의존성 설치 스크립트

### 5.2 서비스 관리
- [ ] systemd 서비스 파일 생성
- [ ] API 서버 자동 시작 설정
- [ ] 로그 로테이션 설정

### 5.3 모니터링 및 로깅
- [ ] 헬스체크 엔드포인트 구현
- [ ] 로그 수집 및 분석 도구 설정
- [ ] 알림 시스템 구축

### 5.4 보안 설정
- [ ] 방화벽 설정 (UFW)
- [ ] SSL/TLS 인증서 설정
- [ ] 환경변수 보안 관리

### 5.5 백업 및 복구
- [ ] MongoDB 백업 스크립트
- [ ] 자동 백업 스케줄링
- [ ] 복구 절차 문서화

## 진행 상황
- 🔵 진행 중: 인프라 요구사항 분석

## 다음 단계
완료 후 → 전체 시스템 통합 테스트 및 운영 시작