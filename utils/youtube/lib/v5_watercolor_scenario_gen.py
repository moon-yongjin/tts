import os
import json
import re
import subprocess
from pathlib import Path
from google import genai
from google.genai import types

class WatercolorVisualDirector:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.0-flash"

    def analyze_scenes(self, transcript_path, num_scenes=10):
        print(f"🎬 대본 분석 중: {transcript_path.name}")
        with open(transcript_path, "r", encoding="utf-8") as f:
            script_text = f.read()

        prompt = f"""
다음은 유튜브 사연의 핵심 대본입니다. 이 내용을 바탕으로 쇼츠 영상에 들어갈 **가장 임팩트 있고 시각적인 장면 {num_scenes}개**를 선정해 주세요. 

**작성 가이드:**
1. **장면 설명**: 각 장면을 한국어로 아주 구체적으로 묘사하세요. (예: "어린 언니가 동생을 등에 업고 비오는 거리를 걷고 있는 모습")
2. **시각적 고난 중심**: 사연의 감동이 가장 잘 전달되는 '고생'의 순간들을 포함하세요.

Output JSON ONLY:
[
  {{"scene_num": 1, "description": "한글 장면 묘사"}},
  ...
]

대본:
{script_text}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"❌ 장면 분석 실패: {e}")
            return []

    def translate_to_watercolor(self, korean_desc):
        prompt = f"""
당신은 거칠고 표현력이 강한 '수채화 화가' 스타일의 프롬프트 엔지니어입니다.
사용자가 입력한 한국어 묘사를 투박하면서도 예술적인 **'거친 수채화풍(Rough Watercolor)'** 영어 프롬프트로 변환하세요.

**[스타일 규칙]**
- Watercolor painting, rough brushstrokes, expressive style, textured paper, raw watercolor, splattered paint.
- **Protagonist: Korean ethnicity, East Asian features.**
- 1:1 aspect ratio, square composition.
- No clean/refined/soft words.

[한국어 묘사]: {korean_desc}

영어 키워드만 출력하세요:
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except:
            return f"watercolor painting, {korean_desc}"

def run_watercolor_gen(api_key, transcript_path, output_json, num_scenes=10):
    director = WatercolorVisualDirector(api_key)
    
    # 1. 장면 추출
    scenes = director.analyze_scenes(transcript_path, num_scenes)
    if not scenes: return False

    # 2. 수채화 프롬프트 변환
    print(f"🎨 {len(scenes)}개의 장면을 수채화 프롬프트로 변환 중...")
    processed_scenes = []
    for s in scenes:
        eng_prompt = director.translate_to_watercolor(s["description"])
        processed_scenes.append({
            "scene_num": s["scene_num"],
            "description_ko": s["description"],
            "visual_prompt": eng_prompt,
            "prompt": eng_prompt, # Whisk_gen 호환성
            "character_refs": ["CHAR_01", "CHAR_03"], # 3개 슬롯 중 2개를 캐릭터 레퍼런스로 채움
            "location_ref": "LOC_01"                  # 3번째 슬롯을 장소 레퍼런스로 채움
        })

    # 3. JSON 저장
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(processed_scenes, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 프롬프트 생성 완료: {output_json}")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True)
    parser.add_argument("--output", default="watercolor_prompts.json")
    parser.add_argument("--num", type=int, default=10)
    args = parser.parse_args()

    # config.json에서 키 로드
    with open("/Users/a12/projects/tts/config.json", "r") as f:
        config = json.load(f)
    
    res = run_watercolor_gen(config["Gemini_API_KEY"], Path(args.script), Path(args.output), args.num)
    if res:
        print("\n💡 이제 생성된 JSON 파일을 확인/수정하신 후 Whisk로 전송할 수 있습니다.")
