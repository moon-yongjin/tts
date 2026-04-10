import os
import shutil
import time
from gradio_client import Client

# [설정] ACE-Step Local (Gradio)
SPACE_ID = "http://localhost:7860"
HF_TOKEN = None # 로컬 구동 시 토큰 불필요
OUTPUT_DIR = "/Users/a12/Downloads/Toffee_ACE_Step_Sample"

def generate_ace_step_sample():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📁 결과 폴더 생성됨: {OUTPUT_DIR}")
    
    print(f"🚀 [ACE-Step] 로컬 서버 연결 중... ({SPACE_ID})")
    try:
        client = Client(SPACE_ID)
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return

    # [프롬프트] K-Funk Fusion: 슬랩 베이스, 훵크 리듬 + 한국 전통 악기(가야금, 깽과리)
    prompt = "K-Funk fusion, high-energy Funk, slap bass guitar, tight horn section, syncopated rhythm, 85 BPM, mixed with Korean traditional Gayageum plucking, Kkwaenggwari percussion accents, groovy, addictive melody, 1970s soulful vibe, vibrant, celebratory, high quality, no vocals"
    
    # [가사/구조] XML 구조를 사용하여 훵크 리듬과 한국풍 선율 조화
    lyrics = """
<SONG_PROMPT>
<HEADER>
[STYLE: K-Funk, Soul Groove]
[MOOD: Energetic, Party, Sweat, Rhythmic]
[INSTRUMENTATION: Slap Bass, Electric Guitar, Horn Section, Gayageum, Kkwaenggwari, Drum Kit]
[TEMPO: 85 BPM]
[VOCALS: None]
</HEADER>
<SONG_MODULES>
<INTRO> [Vintage drum break, tight syncopated rhythm, 85 BPM] </INTRO>
<CHORUS> [Main k-funk hook, slap bass riff combined with gayageum melody, sharp horn accents, k-percussion energy, addictive groove, no vocals] </CHORUS>
</SONG_MODULES>
</SONG_PROMPT>
[instrumental]
"""
    
    print(f"🎵 ACE-Step 음악 생성 시작...")
    try:
        # API: predict(audio_duration, prompt, lyrics, infer_step, guidance_scale, scheduler_type, cfg_type, omega_scale, manual_seeds, guidance_interval, guidance_interval_decay, min_guidance_scale, use_erg_tag, use_erg_lyric, use_erg_diffusion, oss_steps, guidance_scale_text, guidance_scale_lyric, audio2audio_enable, ref_audio_strength, ref_audio_input, lora_name_or_path, api_name="/__call__")
        result = client.predict(
            audio_duration=30, # 30초
            prompt=prompt,
            lyrics=lyrics,
            infer_step=60,
            guidance_scale=15.0,
            scheduler_type="euler",
            cfg_type="apg",
            omega_scale=10.0,
            manual_seeds=None,
            guidance_interval=0.5,
            guidance_interval_decay=0.0,
            min_guidance_scale=3.0,
            use_erg_tag=True,
            use_erg_lyric=False,
            use_erg_diffusion=True,
            oss_steps=None,
            guidance_scale_text=0.0,
            guidance_scale_lyric=0.0,
            audio2audio_enable=False,
            ref_audio_strength=0.5,
            ref_audio_input=None,
            lora_name_or_path="none",
            api_name="/__call__"
        )
        
        # 결과 구조: (audio_path, parameters_json)
        audio_temp_path, parameters = result
        
        if audio_temp_path is None:
            print(f"❌ 생성 실패: 오디오 파일 경로가 없습니다. (Params: {parameters})")
            return None

        timestamp = int(time.time())
        final_filename = f"ACE_Step_BGM_{timestamp}.mp3"
        final_path = os.path.join(OUTPUT_DIR, final_filename)
        
        shutil.move(audio_temp_path, final_path)
        print(f"✅ 생성 성공! 파일 위치: {final_path}")
        return final_path
        
    except Exception as e:
        print(f"❌ 생성 도중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    generate_ace_step_sample()
