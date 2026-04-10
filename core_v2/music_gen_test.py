import os
import shutil
import time
from gradio_client import Client

# [설정] Tencent SongGeneration Hugging Face Space
SPACE_ID = "tencent/SongGeneration"
HF_TOKEN = "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"
OUTPUT_DIR = "/Users/a12/Downloads/Toffee_Music_Sample"

def generate_music_sample():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 결과 폴더 생성됨: {OUTPUT_DIR}")
    
    print(f"🚀 [Tencent SongGen] 허깅페이스 스페이스 연결 중... ({SPACE_ID})")
    try:
        client = Client(SPACE_ID, token=HF_TOKEN)
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return

    # [프롬프트] 밝고 리드미컬한 쇼츠용 BGM (짠짠짠짠 느낌)
    description = "Bright, upbeat, happy, rhythmic, catchy pop, 128bpm, high quality, energetic, for dance shorts."
    lyric = "[inst-long]"
    
    print(f"🎵 음악 생성 시작...")
    print(f"   - 스타일: {description}")
    
    try:
        # API: predict(lyric, description, prompt_audio, genre, cfg_coef, temperature, api_name="/generate_song")
        result = client.predict(
            lyric=lyric,
            description=description,
            prompt_audio=None,
            genre="Electronic",
            cfg_coef=1.8,
            temperature=0.8,
            api_name="/generate_song"
        )
        
        print(f"📊 Raw Result: {result}")
        
        if result is None or (isinstance(result, (list, tuple)) and result[0] is None):
            print("❌ 생성 실패: 결과값이 None입니다. 서버 부하가 높거나 대기 중일 수 있습니다.")
            return None

        # 결과 구조: (generated_song_path, generated_info)
        audio_temp_path, info = result
        
        if audio_temp_path is None:
            print(f"❌ 생성 실패: 오디오 파일 경로가 없습니다. (Info: {info})")
            return None

        timestamp = int(time.time())
        final_filename = f"Toffee_BGM_{timestamp}.mp3"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        
        shutil.move(audio_temp_path, final_path)
        print(f"✅ 생성 성공! 파일 위치: {final_path}")
        return final_path
        
    except Exception as e:
        print(f"❌ 생성 도중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    generate_music_sample()
