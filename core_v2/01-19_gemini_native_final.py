import os
import json
import asyncio
from google import genai
from google.genai import types

# 1. Config 로드
CONFIG_PATH = "/Users/a12/projects/tts/config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)
    API_KEY = config.get("Gemini_API_KEY")

client = genai.Client(api_key=API_KEY, http_options={'api_version': 'v1beta'})

TEST_TEXT = "네이티브 오디오 라이브 에이피아이 테스트입니다. 인자한 할머니 목소리로 부탁해요."
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

async def test_native_audio_final():
    model_id = "gemini-2.5-flash-native-audio-preview-12-2025"
    print(f"🔊 [최종 시도] {model_id} (Live API) 시작...")
    output_path = os.path.join(DOWNLOADS_DIR, "Gemini_Native_Final.mp3")
    
    audio_data = bytearray()
    
    try:
        # 12-2025 프리뷰 모델을 사용하여 Live API 연결
        # voice_name: Aoide, Charon, Fenrir, Kore, Puck
        config = {
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": "Aoide"}
                }
            }
        }
        
        async with client.aio.live.connect(model=model_id, config=config) as session:
            # 텍스트 전송
            await session.send(input=TEST_TEXT, end_of_turn=True)
            
            # 응답 수신 루프 (최대 10초 대기)
            try:
                async with asyncio.timeout(15):
                    async for message in session.receive():
                        if message.server_content and message.server_content.model_turn:
                            for part in message.server_content.model_turn.parts:
                                if part.inline_data:
                                    audio_data.extend(part.inline_data.data)
                        
                        if message.server_content and message.server_content.turn_complete:
                            break
            except asyncio.TimeoutError:
                print("⚠️ 타임아웃 발생 (데이터 수신 중단)")

        if audio_data:
            with open(output_path, "wb") as f:
                f.write(audio_data)
            print(f"✅ 최종 시도 완료: {output_path} ({len(audio_data)} bytes)")
            return True
        else:
            print("⚠️ 수신된 오디오가 없습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 최종 시도 에러: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_native_audio_final())
