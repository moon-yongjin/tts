import os
import numpy as np
from pydub import AudioSegment

# [설정]
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
FFMPEG_PATH = r"C:\Users\moori\Downloads\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\ffmpeg-2026-01-07-git-af6a1dd0b2-essentials_build\bin\ffmpeg"
AudioSegment.converter = FFMPEG_PATH

def generate_tone(frequency, duration_ms, wave_type="Sine", volume=-15.0):
    sample_rate = 44100
    n_samples = int(sample_rate * (duration_ms / 1000.0))
    t = np.linspace(0, duration_ms/1000.0, n_samples, False)
    
    if wave_type == "Square":
        samples = np.sign(np.sin(2 * np.pi * frequency * t))
    elif wave_type == "Sawtooth":
        samples = 2 * (t * frequency - np.floor(t * frequency + 0.5))
    else: # Sine as default
        samples = np.sin(2 * np.pi * frequency * t)
        
    # Attack/Release Envelope (Click 방지)
    attack = int(sample_rate * 0.005)
    release = int(sample_rate * 0.05)
    if n_samples > (attack + release):
        env = np.ones(n_samples)
        env[:attack] = np.linspace(0, 1, attack)
        env[-release:] = np.linspace(1, 0, release)
        samples *= env
        
    samples_int = (samples * 32767).astype(np.int16)
    audio = AudioSegment(samples_int.tobytes(), frame_rate=sample_rate, sample_width=2, channels=1)
    return audio + volume

def create_tense_sample(duration_sec=10):
    print(f"🧨 긴장 모드(Tense) 샘플 생성 중... (BPM 130, Square Wave)")
    
    bpm = 130
    beat_ms = int(60000 / bpm)
    duration_ms = duration_sec * 1000
    
    # 긴장감을 주는 불협화음/단조 음계 (C Minor Diminished)
    # C4, Eb4, Gb4, Ab4
    scale = [261.63, 311.13, 369.99, 415.30] 
    
    full_audio = AudioSegment.silent(duration=duration_ms)
    
    # 4마디 긴장감 패턴
    pattern_len_ms = beat_ms * 4
    for i in range(duration_ms // beat_ms):
        pos = i * beat_ms
        
        # 1. 베이스 킥 (저음 펄스)
        kick = generate_tone(50, 150, wave_type="Sine", volume=-5.0)
        full_audio = full_audio.overlay(kick, position=pos)
        
        # 2. 날카로운 리듬 (Square Wave)
        if i % 2 == 0:
            freq = scale[i % len(scale)]
            note = generate_tone(freq, int(beat_ms * 0.4), wave_type="Square", volume=-20.0)
            full_audio = full_audio.overlay(note, position=pos)
            
        # 3. 엇박자 긴장 효과 (Sawtooth)
        if i % 4 == 3:
            sfx_note = generate_tone(scale[0]*2, int(beat_ms * 0.2), wave_type="Sawtooth", volume=-25.0)
            full_audio = full_audio.overlay(sfx_note, position=pos + (beat_ms // 2))

    output_path = os.path.join(DOWNLOADS_DIR, "Tense_BGM_Sample.mp3")
    full_audio.fade_in(500).fade_out(1000).export(output_path, format="mp3")
    print(f"✅ 샘플 생성 완료: {output_path}")

if __name__ == "__main__":
    create_tense_sample()
