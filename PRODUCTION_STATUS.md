# 🍌 프로젝트 가동 지침 및 현황 (PROJECT MANUAL)

이 문서는 모든 AI 에이전트가 국장님의 지시 사항을 망각하지 않고 즉각 현재 상태를 파악하기 위한 **절대 매뉴얼**입니다.

## 🚨 운영 철칙 (Main Directives)
1. **백업 보존**: `_backup_`이 포함된 모든 폴더는 시스템 보존용이며, 에이전트가 수정/삭제할 수 없음.
2. **격리된 작업**: 모든 작업과 실행은 지정된 폴더(`google_flow_pro` 등) 내부에서만 수행한다. 불필요하게 하위 디렉토리를 뒤지거나 구조를 변경하지 않는다.

## 🛠️ 핵심 도구 현황
### 1. 이미지 순서 정렬기 (Reorder Tool)
- **위치**: `/Users/a12/projects/tts/reorder_tool/reorder_images_by_prompt.py`
- **목적**: 다운로드된 이미지(300장 등)가 뒤섞였을 때, 대본(프롬프트 리스트)과 매칭하여 `001_`, `002_` 순서대로 자동 정렬.
- **실행**: `/Users/a12/projects/tts/reorder_tool/REORDER_GUIDE.md` 참조.

### 2. 구글플로우 익스텐션 (NANO BANANA PRO)
- **위치**: `/Users/a12/projects/tts/google_flow_pro`
- **특이사항**: 현재 3초 간격 'Push-only' 모드로 작동 중. (다운로드 자동화는 비활성화됨)

## 📍 다음 작업 시 체크리스트
- [ ] 대본 파일(.txt)을 받아 `reorder_tool`로 이미지 정렬 실행.
- [ ] 정렬된 결과(`NB2_Ordered` 폴더) 국장님께 보고.

---
**국장님, 이 지침서가 모든 에이전트의 '뇌'에 첫 번째로 읽히도록 설정해 두었습니다.**
