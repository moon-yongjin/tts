# 🍌 이미지 순서 복구 도구 가이드 (NB2용)

현상: 구글 플로우에서 생성된 300장의 이미지가 다운로드 시 순서가 뒤섞여 찾기 힘든 문제 해결을 위한 도구입니다.

## 🛠 작동 원리
이미지 파일명에 포함된 **프롬프트 텍스트**와 원본 **대본(프롬프트 리스트)**을 비교(Fuzzy Matching)하여, 순차적으로 `001_`, `002_` 번호를 붙여 새 폴더에 복사합니다.

## 📂 폴더 구조 및 파일
- **스크립트**: `/Users/a12/projects/tts/reorder_tool/reorder_images_by_prompt.py`
- **입력 필요**: 
    1. 원본 프롬프트가 순서대로 적힌 텍스트 파일 (.txt)
    2. 뒤섞인 이미지가 들어있는 폴더

## 🚀 사용법
터미널에서 아래 명령어를 실행하거나, 제가 대신 실행해 드릴 수 있습니다.

```bash
python /Users/a12/projects/tts/reorder_tool/reorder_images_by_prompt.py \
    /path/to/your/prompts.txt \
    /Users/a12/Downloads/NB2_output \
    /Users/a12/Downloads/NB2_Ordered
```

## ⚠️ 주의사항
- **백업**: 원본 파일은 건드리지 않고 '복사' 방식으로 진행하므로 안전합니다.
- **매칭 정확도**: 파일명과 대본의 텍스트가 너무 다를 경우 매칭에 실패할 수 있습니다. (성공률 보고됨)

### ⚡️ 간편 실행 커맨드 (Shortcut)
이제 복잡한 명령어를 칠 필요 없이, 터미널에서 아래 한 줄만 실행하면 정합성 체크와 정렬이 즉시 수행됩니다:

```bash
/Users/a12/projects/tts/reorder_tool/reorder.sh
```

---
**국장님, 300개 대본이 들어있는 텍스트 파일 경로를 알려주시거나, 해당 폴더에 대본 파일을 넣어주시면 제가 즉시 실행하여 정리해 드리겠습니다!**
