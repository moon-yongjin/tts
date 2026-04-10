import os
from pydub import AudioSegment
from pydub.silence import split_on_silence

input_path = "/Users/a12/Downloads/Full_ZeroShot_233646.wav"
output_path = "/Users/a12/Downloads/Full_ZeroShot_233646_Trimmed.wav"

print(f"📂 파일 로딩 중: {input_path}")
audio = AudioSegment.from_wav(input_path)

print("✂️ 무음 구간 탐색 및 분할 중...")
# silence_thresh: 무음으로 판단할 기준 (dBFS)
# min_silence_len: 최소 무음 길이 (ms)
# keep_silence: 분할 후 앞뒤로 남겨둘 무음 길이 (ms)
chunks = split_on_silence(
    audio, 
    min_silence_len=500, 
    silence_thresh=-45, 
    keep_silence=200
)

print(f"🎙️ 총 {len(chunks)}개의 유효 구간 발견. 결합 중...")
combined = AudioSegment.empty()
for chunk in chunks:
    combined += chunk

print(f"📤 결과 저장 중: {output_path}")
combined.export(output_path, format="wav")
print("✅ 완료!")
