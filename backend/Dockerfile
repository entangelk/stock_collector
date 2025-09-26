# 다단계 빌드 - 최적화된 Stock Collector Backend
FROM python:3.11-slim as builder

# 빌드 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치 (캐시 최적화)
COPY requirements.txt /tmp/requirements.txt
RUN pip install --user --no-cache-dir -r /tmp/requirements.txt

# 런타임 이미지
FROM python:3.11-slim

# 런타임 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 사용자 생성 (보안)
RUN groupadd -r stockuser && useradd -r -g stockuser stockuser

# Python 패키지를 빌더에서 복사
COPY --from=builder /root/.local /home/stockuser/.local

# PATH에 사용자 패키지 디렉토리 추가
ENV PATH="/home/stockuser/.local/bin:$PATH"

# 작업 디렉토리 설정
WORKDIR /app

# 애플리케이션 코드 복사
COPY --chown=stockuser:stockuser . /app

# 로그 디렉토리 생성
RUN mkdir -p /app/logs && chown -R stockuser:stockuser /app/logs

# 사용자 권한으로 전환
USER stockuser

# 환경변수 설정
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 포트 노출 (stock collector는 8003 포트 사용 예상)
EXPOSE 8003

# 헬스체크 추가
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# 앱 시작
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "1"]