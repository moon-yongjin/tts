# 🍌 Nano Banana 이미지 생성 표준 지침 (v3.0)

이 지침은 **구글 제미나이(Gemini) 기반의 'Nano Banana'** 환경에서 이미지 생성 실패를 방지하고, 극강의 캐릭터 일관성과 드라마틱한 퀄리티를 유지하기 위한 표준입니다.

---

## 🛠️ [1단계] 캐릭터 에셋 고정 (Face-only Assets)

캐릭터의 일관성은 '얼굴'에서 나옵니다. 첫 단계에서는 배경/전신을 배제한 **얼굴 전용 에셋**을 먼저 생성합니다.

- **[변경 지침] 단일 얼굴 고정 (Single Face Only):** 기존의 8방향 시트 방식은 얼굴이 여러 개 나오는 오류를 유발하므로, 이제부터는 **단 한 장의 고퀄리티 얼굴 Portrait**만 생성합니다.
- **프롬프트 요령:** 
    - `Extreme close-up photorealistic portrait of [Age/Gender]`
    - `Focusing on detailed facial features, eyes, and skin texture`
    - `Neutral light gray background` (배경 간섭 제거)
    - **[필수 키워드]** `Single face only, A single person view, No grid, No split screen, No view sheet`

---

## 🛡️ [2단계] 구글 정책 안전 가이드 (Safety Policy)

구글의 세이프티 필터(폭력, 상해, 위협 등)에 걸려 이미지가 차단되는 것을 방지하기 위해 **'순화된 감정 표현'**을 사용합니다.

| 거부될 위험이 있는 단어 | 대체 가능한 추천 표현 (Safe & Dramatic) |
| :--- | :--- |
| Bruise (멍), Scar (흉터) | Hidden pain, Weary posture, Weathered skin texture |
| Violence (폭력), Threat (위협) | Intense atmosphere, Shadowy dominance, Tense alert |
| Fear (공포), Terror (공포) | Wide-eyed realization, Tense emotional depth, Gasps |
| Blood (피), Slap (싸대기) | Red-tinted lighting, Emotional shock, Sudden departure |
| Death (죽음), Funeral (장례) | Peaceful silence, Eternal rest, Falling petals, Quiet departure |
| Illness (질병), Cancer (위암) | Fading energy, Faint health, Weary battle, Silent medical journey |
| Hospital (병원) | Serene medical facility, High-tech recovery room, Quiet healing space |

---

## 🎨 [4단계] 은유적 표현 (Symbolic Representation)

정책 위반을 피하면서도 감동을 극대화하기 위해 직접적인 단어 대신 **은유적 묘사**를 풍부하게 사용합니다.

- **[슬픈 소식/질병]**: `Dark clouds gathering`, `A single leaf falling in the wind`, `Fading energy of a long journey`.
- **[임종/작별]**: `Sunset over the horizon`, `A flickering candle going out gently`, `White lilies in a soft glowing room`.
- **[요양원/단절]**: `Unfamiliar sterile sanctuary`, `A lonely bridge between the past and present`.

---

## 📋 [3단계] 배치(Batch) 프롬프트 포맷

'Auto Nano Banana' 툴의 원활한 가동을 위해 아래의 마킹 규칙을 반드시 준수합니다.

- **넘버링:** `001`부터 시작하는 3자리 숫자를 사용합니다. (에셋 정의와 프롬프트 모두 동일하게 적용)
- **구분자:** 세로 작대기(`|`)를 사용하여 3자리 ID와 제목, 프롬프트를 구분합니다.
- **개행:** 각 항목은 반드시 엔터(Newline)로 구분합니다.

**✅ 표준 포맷 예시 (에셋 정의):**
`001 | @Asset_Name | Description and visual details of the character or background.`

**✅ 표준 포맷 예시 (프롬프트):**
`001 | Scene_001 | @[AssetName] [Action/Mood/Lighting] inside @[BackgroundAsset]`

---

### 🖼️ [에셋 생성 지침] 상반신 & 무인(Empty) 배경
- **캐릭터 에셋 (Character Assets):**
    - **가변성 확보:** 나중에 어디든 활용할 수 있도록 반드시 **상반신(Waist-up)** 샷으로 구성합니다.
    - **배경 제거:** `plain light gray background` 또는 `white background`를 사용하여 인물 이외의 요소를 배제합니다.
- **배경 에셋 (Background Assets):**
    - **인물 금지:** 배경 에셋 프롬프트에는 반드시 `no people`, `empty` 키워드를 삽입하여 인물이 없는 순수한 공간만 생성합니다.

- **필수 키워드:** `A single person`, `Single view`, `No grid`, `No split screen`, `Centered composition`, `Cinematic wide shot`
- **호출 예시:** `@[Mother] as a single Korean woman in a wide cinematic view, single view, no grid, no split screen.`

### 🌏 [인종 고정] 한국인 전용 (Korean Only)
배경이나 엑스트라에 외국인이 등장하여 몰입감을 해치는 것을 방지하기 위해 **인종 키워드**를 명시합니다.

- **원칙:** 모든 캐릭터 호출 시 `Korean` 또는 `Asian` 키워드를 함께 사용합니다.
- **예시:** `@[Sujin] as a Korean woman`, `A Korean home setting`, `Korean husband @[Jungwoo]`.
- **주의:** 해외 여행 장면(예: 터키)이라 하더라도 등장인물은 반드시 한국인임을 명시하여 이질감을 제거합니다.

---

## 🚀 제작 팁 (Best Practices)
"화가 났다" 대신 "눈동자에 차가운 이성이 타오른다(Eyes burning with cold resolve)"와 같이 정서적/시각적 묘사를 사용하세요.
...
