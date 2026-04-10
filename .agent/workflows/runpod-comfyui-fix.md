---
description: 런팟 ComfyUI가 안 될 때 고치는 방법 (트러블슈팅 가이드)
---

# 런팟 ComfyUI 트러블슈팅 가이드

## 접속 정보
- **IP**: 213.173.109.153
- **SSH 포트**: 13006
- **SSH 키**: `/Users/a12/projects/tts/id_ed25519_runpod`
- **로컬 터널 포트**: 8181 → 런팟 8188

---

## 1단계: 런팟 SSH 접속 (터미널 탭 1)

```bash
ssh -i /Users/a12/projects/tts/id_ed25519_runpod -p 13006 -o StrictHostKeyChecking=no root@213.173.109.153
```

---

## 2단계: 기존 프로세스 정리 + 필수 라이브러리 설치

```bash
pkill -9 -f main.py
pip install natsort piexif sqlalchemy alembic aiohttp gguf sentencepiece protobuf
```

> **왜?**: 런팟은 서버를 껐다 켜면 pip 라이브러리가 날아간다. 매번 재설치 필요.

---

## 3단계: ComfyUI 백그라운드 실행

```bash
cd /workspace/ComfyUI
nohup python3 main.py --listen 127.0.0.1 > comfy_internal.log 2>&1 &
```

> **주의**: 반드시 `nohup ... &`로 백그라운드 실행할 것! 포그라운드로 실행하면 다른 명령어 칠 때 ComfyUI가 꺼짐.

### 정상 확인:
```bash
tail -f comfy_internal.log
```
- ✅ **성공**: `Starting server` + `http://127.0.0.1:8188` 이 보이면 OK → `Ctrl+C`로 tail 끊기
- ❌ **실패**: `ModuleNotFoundError` 에러 → 2단계의 pip install에 빠진 모듈 추가 설치

---

## 4단계: SSH 터널 열기 (로컬 맥 터미널 탭 2)

> ⚠️ **반드시 로컬 맥 터미널**(프롬프트가 `(base) a12@555`인 창)에서 실행!
> `root@` 프롬프트가 보이는 런팟 창에서 치면 안 됨!

```bash
lsof -t -i:8181 | xargs kill -9 2>/dev/null
ssh -N -L 8181:127.0.0.1:8188 root@213.173.109.153 -p 13006 -i /Users/a12/projects/tts/id_ed25519_runpod -o StrictHostKeyChecking=no
```

- 커서가 멈추고 아무 반응 없으면 **정상** (터널 유지 중)
- `Address already in use` → 첫 줄(lsof kill)이 기존 점유 해제해 줌
- `channel 2: open failed` → 무시해도 됨 (SSH 내부 체크 메시지)

---

## 5단계: 브라우저 접속

- **http://localhost:8181** 로 접속
- ComfyUI 화면이 뜨면 성공!

---

## 자주 나오는 에러 모음

| 에러 | 원인 | 해결 |
|------|------|------|
| `ModuleNotFoundError: No module named 'natsort'` | 런팟 재시작 시 라이브러리 초기화됨 | `pip install natsort` |
| `ModuleNotFoundError: No module named 'piexif'` | 같은 원인 | `pip install piexif` |
| `Address already in use (8181)` | 이전 터널이 안 죽음 | `lsof -t -i:8181 \| xargs kill -9` |
| `channel 2: open failed` | SSH 내부 체크 | 무시 (정상) |
| `Connection reset by peer` | ComfyUI가 런팟에서 안 돌고 있음 | 3단계 다시 실행 |
| `CUDA out of memory` | 다른 프로세스가 GPU 점유 | `pkill -9 -f run.py` 등으로 정리 |

---

## 원클릭 시동 스크립트

위 과정이 귀찮을 때는 로컬에서 이 스크립트 더블클릭:
- **파일**: `/Users/a12/projects/tts/런팟_컨피_원클릭_시동.command`
- 2~5단계를 자동으로 실행해 줌
