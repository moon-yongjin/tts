# 🍌 AI 스토리 비주얼 제작 표준 지침 (Surgical Strike Workflow)

이 지침은 구글 Flow(Imagen 3)와 `google_flow_pro` 확장 프로그램을 사용하여 **매번 다른 대본이 오더라도 동일한 퀄리티와 일관성**을 유지하기 위한 핵심 가이드입니다.

---

## 🛠️ [기본 틀] 제작 공정 (2-Phase Workflow)

새로운 대본이 들어오면 반드시 아래 **2단계 공정**을 순서대로 수행합니다.

### 1단계: 고정 에셋(Fixed Assets) 생성
대본에 등장하는 주인공과 주요 장소를 '기준점'으로 박제하는 단계입니다.
- **캐릭터**: 8방향 턴어라운드 시트 (Front, Side, Back, Face views)
  - *핵심 키워드*: `character reference sheet`, `8 views`, `cinematic realistic photography`, `plain light gray background`, `consistent features`.
- **장소/환경**: 4분할 그리드 시트 (Wide, Reverse, Low, Detail views)
  - *핵심 키워드*: `environment reference sheet`, `4 panels 2x2 grid`, `same space`, `consistent lighting`.

### 2단계: 장면(Scene) 생성 (Asset Mapping)
1단계에서 만든 고정 에셋을 호출하여 대본의 각 장면을 그리는 단계입니다.
- **호출 문법**: 반드시 **`@[에셋명]`** 형식을 사용합니다.
- **프롬프트 구성**: `@[에셋명] + [동작/상황] + [장소 에셋] + [분위기/화질]`
- **일관성 유지**: 캐릭터의 이름이나 특징을 매번 길게 설명하지 말고, 오직 고정된 에셋 호출에만 의존합니다.

---

## 🎨 프롬프트 설계 표준 (Character & Environment)

### 캐릭터 (Korean 필수)
반드시 **'Korean'** 키워드를 넣어서 외국인 혼입을 방지하고, 성별/나이/핵심 의상을 고정합니다.
> 예시: `Korean male in his early 30s as a law student, slim build, sharp features, rectangular black-framed glasses...`

### 배경 (Yeonnam-dong / Gangnam Style)
대본의 분위기에 맞는 한국적 배경(연남동 골목, 강남 사무실 등)을 4분할 시트로 먼저 고정합니다.

---

## 🚀 실행 요령
1. 새로운 대본 승인 즉시 **[에셋용 프롬프트]** 5~8개를 먼저 뽑아 구글 Flow에서 실행합니다.
2. 생성된 레퍼런스 시트를 에셋으로 등록(고정)합니다.
3. 이후 **[장면용 프롬프트]**를 일괄 생성하여 `google_flow_pro`로 자동 실행합니다.

---
**✅ 이 지침은 모든 스토리 프로젝트의 '기본틀'이며, 대본이 바뀔 때마다 이 틀에 맞춰 프롬프트만 교체합니다.**
