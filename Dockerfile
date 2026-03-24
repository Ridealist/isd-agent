# 1. Base 이미지 (Python 3.11은 CrewAI와 호환성이 가장 좋음)
FROM python:3.11-slim-bookworm

# 2. 작업 디렉토리를 /app으로 설정
WORKDIR /app

# 3. 의존성 패키지 설치
RUN apt-get update && apt-get install -y \
    libmagic1 \
    build-essential \
    curl \
    git \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# 4. pip 및 빌드 도구 최신화 (의존성 해석 능력 향상)
RUN python -m pip install --upgrade pip setuptools wheel

# 5. requirements.txt 복사 및 패키지 설치
COPY requirements.txt /app/

# --no-cache-dir를 사용하여 이미지 용량을 줄이고, 
# 의존성 충돌 시 pip가 더 유연하게 대처하도록 합니다.
RUN pip install --no-cache-dir -r requirements.txt

# 6. python-magic 재설치 (시스템 라이브러리와의 연결 보장)
RUN pip install --upgrade --force-reinstall python-magic

# 7. 실행할 streamlit_app.py를 컨테이너 /app으로 복사
COPY . /app/

# 8. 포트 오픈 및 헬스 체크
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

#9. 실행될 컨테이너 구성
ENTRYPOINT [ "streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0" ]