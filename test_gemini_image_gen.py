import json
import os
from google import genai
from google.genai import types

# Config 로드
CONFIG_PATH = "/Users/a12/projects/tts/config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)
    GEMINI_API_KEY = config.get("Gemini_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

# gemini-2.5-flash-image 테스트
model_id = "gemini-2.5-flash-image"
prompt = "A beautiful cinematic portrait of a woman in a traditional Korean room, 9:16 vertical, photorealistic, cinematic lighting."

print(f"🚀 {model_id}로 이미지 생성 테스트 중...")

try:
    # generate_images가 아닌 generate_content로 시도 (supported_actions에 generateContent만 있음)
    # 또는 generate_images를 지원하는지 확인
    try:
        response = client.models.generate_images(
            model=model_id,
            prompt=prompt,
            config={'number_of_images': 1, 'aspect_ratio': '9:16'}
        )
        print("✅ generate_images 성공!")
        image = response.generated_images[0]
        with open("test_gemini_2.5_image.png", "wb") as f:
            f.write(image.image_bytes)
        print("✅ 이미지 저장 완료: test_gemini_2.5_image.png")
    except Exception as e:
        print(f"⚠️ generate_images 실패: {e}")
        print("🔄 generate_content로 재시도 중...")
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        print("✅ generate_content 응답 수신!")
        # 응답에 이미지가 포함되어 있는지 확인
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                print(f"📸 이미지 데이터 감지! (MIME: {part.inline_data.mime_type})")
                with open("test_gemini_2.5_content.png", "wb") as f:
                    f.write(part.inline_data.data)
                print("✅ 이미지 저장 완료: test_gemini_2.5_content.png")
            elif hasattr(part, 'text') and part.text:
                print(f"📝 텍스트 응답: {part.text[:200]}...")

except Exception as e:
    print(f"❌ 최종 생성 실패: {e}")
