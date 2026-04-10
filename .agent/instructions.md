# User Interaction Guidelines

## CRITICAL: Report and Approval Policy

> [!CAUTION]
> **실행 전 '보고' 지침을 어기지 마십시오.** (NEVER skip reporting before execution.)
> 
> 1. 모든 코드 수정, 새로운 스크립트 생성, 파일 이동/삭제 전에는 반드시 **[구체적인 계획]**을 보고하고 사용자 승인을 받으십시오.
> 2. 사용자가 질문만 했을 경우, 임의로 코드를 수정하여 실행하지 말고 **[의견/답변]**만 먼저 전달하십시오.
> 3. 이미 승인된 계획이라도, 큰 변경이 발생하면 다시 보고하십시오. 
> 4. 이를 어길 시 시스템 신뢰에 치명적인 영향을 미칩니다. (Strict compliance is mandatory.)

## Project Specific Rules
- Asset Management: Be extremely careful with scripts that use `shutil.rmtree` or `shutil.move` (e.g., `07-2_remotion_auto_render.py`). Verify asset presence before execution.
- **Strict File Verification**: On Mac, always verify that files are created and accessible via absolute paths to prevent NFD/NFC encoding issues.
- **Numbered Script Consistency**: Before creating a new numbered script (e.g., `1-3-4`), always search for and analyze existing scripts in the sequence (`1-3-2`, `1-3-3`) to follow the established engine patterns and configurations.
- **Strict Parameter Fix**: Qwen3 Zero-Shot TTS(01-3-3, 1-3-4 등 모든 제로샷 스크립트)의 레퍼런스 오디오 길이는 **6.0초**로 고정한다. 사용자의 명시적인 요청 없이는 핵심 생성 파라미터(duration, temperature 등)를 임의로 변경하지 않는다.
- **Strict Gender Consistency**: 한국어 대본의 호칭(형, 누나, 오빠, 언니 등)을 정확히 해석하여 주인공의 성별을 고정한다. '형'이라고 부르면 주인공은 반드시 **남성(boy/man)**으로 묘사하며, 임의로 성별을 바꾸지 않는다.
- **Strict Aspect Ratio**: 모든 생성 이미지는 기본적으로 **1:1 비율(640x640)**로 생성한다. 세로형이나 가로형 요청이 명시적으로 없을 경우 멋대로 비율을 바꾸지 않는다.
- **Asset Cleanup Protocol**: 해상도나 성별 등 주요 설정을 변경하여 재생성할 때는, 구형 파일(예: Long image)과 섞이지 않도록 반드시 `ComfyUI/output` 폴더의 관련 파일을 삭제하거나 완전히 새로운 다운로드 폴더를 생성한다.
- Aesthetic Consistency: Maintain white background + high-contrast red/black text for headers as established.
- **Question Response Policy**: 사용자가 질문을 던질 경우, 명시적인 실행 요청이 없다면 마음대로 코드를 수정하거나 실행하지 않고 '대답(의견)'만 먼저 전달한다.
- Language Policy: 대답은 항상 한국말로 한다. (Always respond in Korean).
