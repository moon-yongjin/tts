import os
import mlx.core as mx
from mlx_audio.tts import load
import soundfile as sf
import numpy as np

MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit"
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "speaker_previews")
os.makedirs(OUTPUT_DIR, exist_ok=True)

speakers = ['ryan', 'aiden', 'eric', 'dylan', 'uncle_fu', 'sohee']
test_text = "안녕하세요. 서울 표준어를 사용하는 성우입니다. 차분하고 단호한 어조로 안내해 드리겠습니다."
instruct = "당신은 서울 표준어를 사용하는 20년 경력의 한국인 성우입니다. 중급 뉴스 앵커처럼 차분하고 단호하게 발음하세요."

print(f"🚀 모델 로딩: {MODEL_ID}")
model = load(MODEL_ID)

for spm in speakers:
    print(f"🎙️ {spm} 생성 중...")
    results = model.generate(
        text=test_text,
        voice=spm,
        language="Korean",
        instruct=instruct,
        temperature=0.0
    )
    
    audio_mx = None
    for res in results:
        if audio_mx is None: audio_mx = res.audio
        else: audio_mx = mx.concatenate([audio_mx, res.audio])
    
    if audio_mx is not None:
        file_path = os.path.join(OUTPUT_DIR, f"preview_{spm}.wav")
        sf.write(file_path, np.array(audio_mx), 24000)
        print(f"✅ 저장됨: {file_path}")

print(f"✨ 모든 미리보기가 {OUTPUT_DIR} 에 저장되었습니다.")
