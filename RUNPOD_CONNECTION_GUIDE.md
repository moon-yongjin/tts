# 런팟(RunPod) ComfyUI 접속 및 유지 가이드

이 문서는 런팟 서버를 껐다 켰을 때 발생하는 접속 문제와 라이브러리 초기화 문제를 해결하기 위한 고정 지침입니다.

## 1. 핵심 문제 원인
런팟 서버는 구조상 `/workspace` 폴더 내의 파일만 영구 저장됩니다. 
- **저장됨**: `ComfyUI` 코드, 각 모델 파일(`.safetensors`, `.gguf`), 커스텀 노드(플러그인) 폴더.
- **초기화됨**: `pip install`로 설치한 파이썬 패키지(라이브러리). 

이 때문에 서버를 재시작하면 **"Node Not Found (UnetLoaderGGUF)"** 등의 에러가 발생하며 작동하지 않는 것입니다.

## 2. 해결 방법: 원클릭 자동 시동 (Self-Healing)
이미 `런팟_컨피_원클릭_시동.command` 파일에 **자가 치유(Self-healing)** 로직을 심어두었습니다.

### [작동 원리]
1. **접속 정보 확인**: 파일 상단의 `RP_IP`와 `RP_PORT`를 현재 런팟 대시보드 정보와 맞춥니다.
2. **자동 라이브러리 확인**: 서버에 접속하자마자 필수 패키지(`gguf`, `sqlalchemy` 등)가 있는지 확인하고 없으면 자동으로 설치합니다.
3. **ComfyUI 강제 재시작**: 기존에 꼬여있는 프로세스를 죽이고, 설치된 라이브러리가 적용된 상태로 깨끗하게 다시 켭니다.
4. **보안 터널 생성**: 로컬의 `8181` 포트와 런팟의 `8188`을 터널링하여 브라우저(`http://localhost:8181`)를 띄웁니다.

## 3. 런팟 정보 업데이트 방법
런팟을 새로 켤 때마다 포트 번호가 바뀌므로, 아래 파일만 수정하면 됩니다.

- **파일**: `런팟_컨피_원클릭_시동.command`
- **수정 부분**:
  ```bash
  RP_IP="213.173.109.153"   # 런팟 IP
  RP_PORT="13006"           # 런팟 SSH 포트 (TCP 포트 아님!)
  ```

## 4. 장애 발생 시 터미널 응급 처치
만약 클릭 시동이 안 된다면, 터미널에서 아래 명령어를 복사해서 붙여넣으세요. (포트 번호 `13006`은 상황에 맞게 수정)

```bash
ssh -i ~/projects/tts/id_ed25519_runpod -p 13006 root@213.173.109.153 "python3 -m pip install sqlalchemy alembic aiohttp gguf sentencepiece protobuf; pkill -9 -f main.py; cd /workspace/ComfyUI && nohup python3 main.py --listen 127.0.0.1 > comfy_internal.log 2>&1 &"
```

---
**주의**: 로컬 ComfyUI(`8188`)와 런팟 ComfyUI(`8181`)를 동시에 쓸 수 있도록 세팅되어 있으니, 로컬 작업 중에도 안심하고 쓰셔도 됩니다.
