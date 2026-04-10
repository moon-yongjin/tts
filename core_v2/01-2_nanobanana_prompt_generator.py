import json
import os
import argparse
from google import genai
from google.genai import types

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
SCRIPT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "대본.txt")
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "나노바나나_프롬프트.txt")

def load_gemini_key():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("Gemini_API_KEY")
    except:
        return None

STYLES = {
    "Photorealistic": "Ultra-realistic, 8k professional photography, cinematic lighting, vivid facial details, photorealistic textures",
    "DaveTheDiver": "Masterpiece, best quality, ultra-detailed 3D game render, authentic Dave the Diver style, 8K, vibrant cel-shaded 3D cartoon, chibi-proportioned character with big expressive eyes and cheerful smile, big head relative to body, thick limbs, dynamic 3D lighting, sharp cel-shading, volumetric shadows, glossy surfaces, rich polygon details, cute highly detailed 3D game character like Dave the Diver",
    "Watercolor": "Cinematic watercolor illustration, vibrant and fluid colors, soft edges, intricate details, artistic painterly feel",
    "Ghibli": "Studio Ghibli animation style, flat distinct colors, beautiful highly detailed background, anime masterpiece, nostalgic atmosphere"
}

def build_prompt(script_content, char_count, bg_count, style_id):
    art_style_instruction = STYLES.get(style_id, STYLES["Photorealistic"])

    prompt = f"""
당신은 '나노바나나' 이미지 프롬프트 생성 전문가입니다.
사용자가 제공한 대본을 분석하여 아래 형식의 파일(Markdown)을 작성하세요.

[화풍 가이드]
이 대본의 모든 에셋 프롬프트와 배경 프롬프트, 장면(Scene)의 기본 스타일(종합적인 분위기)은 다음과 같습니다.
각 설명에 이 화풍의 특징을 자연스럽게 녹여내세요!
화풍 설정: "{art_style_instruction}"

[형식 - 필수 준수]
- 파일은 두 단계로 구성됩니다:
  ## [1단계] 캐릭터 및 배경 에셋 (Assets)
  ## [2단계] 시네마틱 장면 프롬프트 (Prompts)
- 에셋의 번호는 001부터 순차적으로 기입 (형식: 001 | @Asset_Name | Description in English...)
- 캐릭터 에셋은 반드시 {char_count}명 생성하세요. (초상화 형태, 상반신 샷 위주, Waist-up photorealistic portrait)
- 배경 에셋은 반드시 {bg_count}곳 생성하세요. (인물 금지, no people, empty, wide cinematic shot)
- 2단계 시나리오 프롬프트는 대본의 주요 흐름을 따라가며 20~30개 컷을 영어 프롬프트로 생성합니다.
  (형식: 001 | Scene_001 | @[Person_Asset] doing [Action] inside @[Background_Asset], using [Lighting/Mood])

[주의]
- 거부될 위험이 있는 단어(피, 살인폭력 등)는 은유적 표현(Blood -> Red-tinted lighting 등)으로 완화하여 작성하세요.
- 한국 배경이 확실하다면 한국인으로(Korean) 지정하세요.

[대본 본문]
{script_content}

---
서론이나 부연 설명 없이, 코드블록(```markdown) 없이 오직 위에서 요구한 최종 파일의 내용 텍스트만 출력하세요.
"""
    return prompt

def main(args):
    api_key = load_gemini_key()
    if not api_key:
        print("❌ config.json 파일에서 Gemini_API_KEY를 찾을 수 없습니다.")
        return

    if not os.path.exists(SCRIPT_FILE):
        print(f"❌ 대본 파일이 존재하지 않습니다: {SCRIPT_FILE}")
        return

    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        script_content = f.read()

    print(f"🤖 Gemini 2.0 Flash 모델로 프롬프트 생성 중...")
    print(f"   (화풍: {args.style} / 캐릭터 {args.chars}명 / 배경 {args.bgs}곳)")
    
    prompt = build_prompt(script_content, args.chars, args.bgs, args.style)
    
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt
        )
        
        result_text = response.text.replace("```markdown", "").replace("```", "").strip()
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(result_text)
            
        print(f"✅ 프롬프트 생성 완료! 파일 저장: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"❌ API 호출 중 에러 발생: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chars", type=int, default=4)
    parser.add_argument("--bgs", type=int, default=4)
    parser.add_argument("--style", type=str, default="Photorealistic")
    
    args = parser.parse_args()
    main(args)
