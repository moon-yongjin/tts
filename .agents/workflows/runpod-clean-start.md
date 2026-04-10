---
description: 런팟 클린 스타트 가이드 (이미지 생성 세션용)
---

# 🚀 런팟 클린 스타트 체크리스트

## 1. 런팟 시작 & 터널링
```bash
# 런팟 웹에서 Pod 시작 후
./런팟_컨피_원클릭_시동.command
```
// turbo
- 터널링 확인: `curl -s http://127.0.0.1:8181/object_info | head -c 100`

## 2. 서버 출력 폴더 비우기 (번호 꼬임 방지)
```bash
ssh -p 13006 -i /Users/a12/projects/tts/id_ed25519_runpod -o StrictHostKeyChecking=no root@213.173.109.153 "rm -f /workspace/ComfyUI/output/GGUF_Scene_*.png && echo '✅ output 폴더 클린 완료'"
```
> ⚠️ 이걸 안 하면 Scene_016 같은 엉뚱한 번호부터 생성됨

## 3. 로컬 프롬프트 캐시 삭제
```bash
rm -f /Users/a12/projects/tts/visual_prompts.json /Users/a12/projects/tts/visual_prompts_master.json
```
// turbo
> 캐시가 남아있으면 프롬프트 수정사항이 반영 안 됨

## 4. 이미지 생성 실행
```bash
./02-3-20_오디오_기준_이미지_자동생성.command
```
- v2 커넥터(02-141) 사용 시: `.command` 파일 10번째 줄에서 `02-141` 확인

## 5. 작업 끝나면 런팟 정지
- RunPod 웹 대시보드에서 **Stop** (Delete 아님!)

---

## ⚡ 오늘의 교훈 요약

| 문제 | 원인 | 해결 |
|------|------|------|
| Scene_016부터 시작 | 서버 output 폴더에 이전 파일 잔존 | 시작 전 output 폴더 클린 |
| 28/44만 다운로드 | WebSocket이 큐 등록 후에 연결됨 | v2 커넥터(02-141) 사용 |
| 가슴 노출 이미지 | 프롬프트에 자극적 단어 포함 | PROTAGONIST_DESC 고정 + 금칙어 블랙리스트 |
| 레퍼런스 파일 없음 | Downloads에 보관하지 않는 정책 | voices/Reference_Audios/에 통합 보관 |
