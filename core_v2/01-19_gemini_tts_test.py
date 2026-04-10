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

# SDK 기본값(v1beta) 사용을 위해 별도 설정 없이 Client 초기화
client = genai.Client(api_key=API_KEY)

# 2. 대본 로드
TEST_TEXT = "박순자 할머니의 이야기입니다. '오냐, 너희가 판 무덤에 직접 들어가 봐라.' 따뜻하지만 서늘한 목소리로 들려주세요."

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

def test_gemini_25_preview_tts():
    """방식 1: Gemini 2.5 Flash Preview TTS (전용 TTS)"""
    model_id = "gemini-2.5-flash-preview-tts"
    print(f"🎙️ [방식 1] {model_id} 테스트 시작...")
    output_path = os.path.join(DOWNLOADS_DIR, "Gemini_25_Preview_TTS.mp3")
    
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=TEST_TEXT,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"]
            )
        )
        
        audio_found = False
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                with open(output_path, "wb") as f:
                    f.write(part.inline_data.data)
                print(f"✅ 방식 1 완료: {output_path}")
                audio_found = True
                break
        return audio_found
    except Exception as e:
        print(f"❌ 방식 1 실패: {e}")
        return False

async def test_gemini_native_audio_live(model_id="gemini-2.0-flash-exp", voice_name="Puck"):
    """방식 2: Gemini Native Audio (Live API / Bidi)"""
    print(f"🔊 [방식 2] {model_id} (Live API) 테스트 시작 ({voice_name})...")
    output_path = os.path.join(DOWNLOADS_DIR, f"Gemini_Native_Live_{voice_name}.mp3")
    
    audio_data = bytearray()
    
    try:
        # Live API 설정
        config = types.LiveConnectConfig(
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            )
        )
        
        async with client.aio.live.connect(model=model_id, config=config) as session:
            # 텍스트 전송
            await session.send(input=TEST_TEXT, end_of_turn=True)
            
            # 응답 수신 루프
            async for message in session.receive():
                if message.server_content and message.server_content.model_turn:
                    for part in message.server_content.model_turn.parts:
                        if part.inline_data:
                            audio_data.extend(part.inline_data.data)
                
                if message.server_content and message.server_content.turn_complete:
                    break
                    
        if audio_data:
            with open(output_path, "wb") as f:
                f.write(audio_data)
            print(f"✅ 방식 2 완료: {output_path}")
            return True
        else:
            print("⚠️ 방식 2: 오디오 데이터 수신 실패.")
            return False
            
    except Exception as e:
        print(f"❌ 방식 2 실패: {e}")
        return False

if __name__ == "__main__":
    print(f"🚀 Gemini Dual TTS Comparison Test (v4)")
    
    # 1. Preview TTS
    test_gemini_25_preview_tts()
    
    # 2. Native Audio (Live API) - gemini-2.0-flash-exp 시도
    try:
        asyncio.run(test_gemini_native_audio_live(model_id="gemini-2.0-flash-exp", voice_name="Aoide"))
    except:
        # 실패 시 2.5 네이티브 모델로 재시도
        print("🔄 gemini-2.0-flash-exp 실패. gemini-2.5-flash-native-audio-latest로 재시도...")
        asyncio.run(test_gemini_native_audio_live(model_id="gemini-2.5-flash-native-audio-latest", voice_name="Puck"))
    
    print("\n✨ 테스트가 종료되었습니다. Downloads 폴더를 확인하세요.")
