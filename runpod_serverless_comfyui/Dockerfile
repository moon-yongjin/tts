FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# RunPod 서버리스 SDK 설치
RUN pip install runpod requests

# 핸들러 스크립트 복사
COPY handler.py /handler.py
COPY start.sh /start.sh

# 실행 권한 부여
RUN chmod +x /start.sh

# 컨테이너 시작 시 실행될 엔트리포인트
CMD ["/start.sh"]
