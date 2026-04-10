# 🛡️ TTS Project Core Engineering Rules (V1)

이 문서는 프로젝트의 생산성을 극대화하고, 저지능 반복 작업을 배제하며 고지능 에이전트(Llama-3-70B + Gemini)의 협업 효율을 높이기 위한 핵심 설계 지침입니다.

## 1. 📂 아키텍처 원칙 (Architecture Principles)
- **Atomic Scripts**: 모든 스크립트는 하나의 명확한 목적을 가집니다. (예: `gen_audio.py`, `mix_bgm.py`)
- **JSON Driven**: 모든 설정, 프롬프트, 규칙은 코드와 분리하여 JSON 파일(`config.json`, `learned_patterns.json`)에서 관리합니다.
- **Fail-Safe Fallback**: API 호출 실패 시 반드시 차선책(Ollama 또는 Mock 데이터)을 준비합니다.

## 2. 🤖 고지능 에이전트 협업 전략 (Agent Collaboration)
- **Role Distribution**: 
    - **Gemini (Flash)**: 빠른 실행, 코드 수정, 실시간 도구 호출 및 파일 관리 담당.
    - **Llama-3-70B (HF)**: 고난도 아키텍처 설계, 코드 논리 검토, 전략적 스토리라인 분석 담당.
- **Double-Check Loop**: 중요한 코드 변경은 적용 전 반드시 Llama-3-70B의 'Review' 단계를 거칩니다.

## 3. 🐍 코딩 표준 (Coding Standards)
- **Path Isolation**: 모든 경로는 `Pathlib`을 사용하며, 프로젝트 루트(`PROJ_ROOT`)를 기준으로 상대 경로를 절대 경로로 변환하여 사용합니다.
- **Verbose Logging**: 모든 에이전트 활동은 `[에이전트 이름] 작업 내용` 형식으로 콘솔에 기록하여 디버깅 가독성을 높입니다.
- **Safety First**: 파일 삭제나 위험한 시스템 명령은 반드시 `Safety Rejection` 로직을 통과해야 합니다.

## 4. 🚀 생산성 극대화 (Productivity Boost)
- **No Manual Repetition**: 3회 이상 반복되는 작업은 즉시 `core_v2/utils_helper.py` 또는 신규 자동화 스크립트로 구현합니다.
- **Quota Maximization**: 매일 25분 할당량은 '코드 리팩토링' -> '신규 기능 설계' -> '대본 최적화' 순으로 우선순위를 두어 소진합니다.
