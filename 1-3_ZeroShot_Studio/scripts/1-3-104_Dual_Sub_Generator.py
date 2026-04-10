import os
import sys
import json
import mlx.core as mx
from mlx_audio.tts import load
import numpy as np
import soundfile as sf
import librosa
import tempfile
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import datetime
from pathlib import Path
import re

# 🎙️ Qwen3-TTS [Dual-Speaker Worker: Sequential Batch Processor]

PROJECT_ROOT = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
MODEL_PATH = PROJECT_ROOT / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
sys.path.append(str(PROJECT_ROOT))

# 📦 [목소리 세팅] - 마스터로부터 인덱스를 받음
VOICES = {
    "1": {"file": "/Users/a12/projects/tts/voices/Reference/Screen_Recording_20260318_050504_YouTube_extracted.wav", "text": "보면 매출 자체는 나쁘지가 않아요. 656억 정도로 매출은 굉장히 잘 나오지만 일단 비용이 너무 높습니다. 영업 비용만 해도 946억이 나와서 영업 손실이 나고 있는 회사예요.", "speed": 1.0},
    "2": {"file": "/Users/a12/projects/tts/voices/Reference/Screen_Recording_20260318_040927_YouTube.mp4", "text": "사람들은 20달러가 동일한 가치처럼 느껴지겠지만 실제적으로 우리가 판매를 할 때 크로스보더 셀러, 우리 역직구의 셀러들은 이익을 더 많이 볼 수 있다라고.", "speed": 1.0},
    "3": {"file": "/Users/a12/projects/tts/voices/Reference/ClassicUnni_Ref.mp4", "text": "안녕하세요, 오늘 전해드릴 소식은 유튜브 화면 녹화 영상을 기반으로 한 인공지능 음성 복제 기술입니다.", "speed": 1.0},
    "4": {"file": "/Users/a12/projects/tts/voices/Reference/KangJiYoung3_Ref.mp4", "text": "강지영 아나운서 스타일의 목소리 톤을 참고하기 위한 레퍼런스 데이터입니다.", "speed": 1.0},
    "5": {"file": "/Users/a12/projects/tts/voices/Reference/Woman4_감성_슬픔_Clean.wav", "text": "아버지가 인팀 전이 많지가 되셔서 돌아오셨고 있는 모든 걸 그냥 다 두신 그런 날만 되면은 저희는 책가방을 싸들고 있다가 새벽 2시나 새벽 3시쯤 어디론가 다 숨어야되는 옆집의 소리가 들리까봐 아버지가 TV 볼륨을 맥스로 올리고 폭행이 시작되어서 초등학교 3학년 때 엄마가 집을 나가셨어요.", "speed": 1.0},
    "6": {"file": "/Users/a12/projects/tts/voices/Reference/Screen_Recording_20260322_013938_TikTok-Lite.mp4", "text": "BTS 공연을 간다고요? 그냥 거기를 지나간다고요? 잠시만요. 아래 캡션에 광화문 근처 관련", "speed": 1.0},
    "7": {"file": "/Users/a12/projects/tts/voices/Reference/Traffic_Broadcasting.wav", "text": "내륙 중심으로 아침 기온은 영하권의 기온을 보이는 곳이 많아서 이맘때와 아침 기온이 비슷하거나 조금은 낮겠습니다.", "speed": 1.0},
    "8": {"file": "/Users/a12/projects/tts/voices/Reference/Audiobook.wav", "text": "픽업트럭 한 대가 먼지를 일으키며 사라져갔다. 거친 밥에 목이 메었다. 다리를 심하게", "speed": 1.0},
    "9": {"file": "/Users/a12/projects/tts/reference_audio_3.wav", "text": "술 더 떠서 주민회 회장까지 한다는 것이었다. 또다시 전화와 인터폰을 왕래하느라 입맛이 떨어져 아침에 설친 그는 주민회 회장까지 한다는 것이었다.", "speed": 1.0, "gain": 1.2},
    "10": {"file": "/Users/a12/projects/tts/voices/Reference/NewTikTok_Ref_0403.wav", "text": " 살 통통이 오른 가을 물고기 넣고 어탕을 끓입니다. 특별한 재료도 비법도 필요 없습니다.", "speed": 1.0},
    "11": {"file": "/Users/a12/projects/tts/voices/Reference/ChaJuYoung_Ref_0403.wav", "text": " 회장님, 제가 얼마나 회장님 최선을 다해서 모셨는지 아시죠? 가실 때 가시더라도 유서에 우리 희진이 집은 없을 것 같아요.", "speed": 1.0},
    "12": {"file": "/Users/a12/projects/tts/voices/Reference/NewMistress_Ref_0403.wav", "text": "이 공간 아직도 이렇게 쓰세요? 불편한 거 알면서도 정리가 힘드셨죠? 저도 큰맘 먹고 이번에 싹 정리했어요. 이젠 더 이상 미루지 마시고 한번 바꿔보세요. 상품 정보 궁금하시다면 댓글에 편리 라고 남겨주세요.", "speed": 1.0},
    "13": {"file": "/Users/a12/projects/tts/voices/Reference/YooHaeJin_Ref_0404.wav", "text": "봐봐. 진서진철, 진이 엄마 나 좀 봐봐. 내가 남자랑 잔다는 게 상상이네. 내가 이렇게 하고. 아니야. 뭐. 야 이거 이렇게 하고 잔다는 게 상상이 돼.", "speed": 1.0},
    "14": {"file": "/Users/a12/projects/tts/voices/Reference/JeongSeungJe_Ref_0404.wav", "text": "교회가 있어요. A 합집합 B, A 교집합 B 그래요. 이거를 어떤 사람은 컵같이 생겼다 그래서 A 컵 B", "speed": 1.0},
    "15": {"file": "/Users/a12/projects/tts/voices/Reference/Voice15_Ref_0404.wav", "text": "생각하시면 어렵지 않게 적용이 되실 거예요. 자 먼저 시범 보여드리겠습니다. 시범을 보여드리지만 제 소리를 들으시는 게 아니라 제 호흡이", "speed": 1.0},
    "16": {"file": "/Users/a12/projects/tts/voices/Reference/Voice16_Ref_0404.wav", "text": "하는 거 아니야 이거잖아 이거 이거 이거 이거 이거 최소 이렇게 주문할게 우리 라인 비워놔 우리 라인에 다른 손님 받지마 1억개 내가 못 팔면 내가 책임질게 무조건 1억개를 만들 준비만 해놔 2천9 2천개 만들 준비만 해놔 아니 그건 우리끼리 나눠 먹고 안되면 내가", "speed": 1.0},
    "17": {"file": "/Users/a12/projects/tts/voices/Reference/Voice17_Ref_0404.wav", "text": "항상 그 1등을 유지하는 거라고만 생각했고 부럽다고 생각했어요. 근데 어느 날 저한테 얘기 좀 하재요. 벤치로 갔어요.", "speed": 1.0},
    "18": {"file": "/Users/a12/projects/tts/1-3_ZeroShot_Studio/voices/Reference/TikTokLite_0405_Ref.wav", "text": "결단력 있고 실행력 보이고 있는 이재명 정부와 밀어주시다.", "speed": 1.1},
    "19": {"file": "/Users/a12/projects/tts/1-3_ZeroShot_Studio/voices/Reference/YouTube_0403_Ref.wav", "text": "그렇지? 그래도 말만 존경하니 뭐니 직접 해봐야 느끼고 아는 거지.", "speed": 1.0},
    "20": {"file": "/Users/a12/projects/tts/1-3_ZeroShot_Studio/voices/Reference/260408_084840_ref.wav", "text": "안녕하세요 요즘에 오토이스크 안 돼서 곤란해하시는 분들 많으시죠?", "speed": 1.0},
    "21": {"file": "/Users/a12/projects/tts/1-3_ZeroShot_Studio/voices/Reference/TikTokLite_0409_Ref.wav", "text": "3분의 1이 완전히 구겨졌다. 바닥에 흩어진 헤드라이트 아이라인을 주섬주섬 주워 담으며 보니", "speed": 1.1},
    "22": {"file": "/Users/a12/projects/tts/1-3_ZeroShot_Studio/voices/Reference/YouTube_0409_234401_Ref.wav", "text": "젊은 여종들의 그림자가 어스름에 어른거리자 시선이 절로 따라 갔습니다.", "speed": 1.0},
    "23": {"file": "/Users/a12/projects/tts/1-3_ZeroShot_Studio/voices/Reference/YouTube_0409_234501_Ref.wav", "text": "그리고 가장 충격적인 건요. 이 아이가 나중에 늙고 병들어 죽 게 되면", "speed": 1.0},
    "24": {"file": "/Users/a12/projects/tts/1-3_ZeroShot_Studio/voices/Reference/YouTube_0409_234701_Ref.wav", "text": "보릿살 한 줌 뿐 그나마도 내일 아침을 위해 아껴둔 것이었습니 다. 그날 밤 눈보라가 몰아쳤습니다.", "speed": 1.0}
}

def trim_silence(audio, threshold=-50.0, padding_ms=200):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:duration] 
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(100) + silence # 💡 페이드아웃을 100ms로 늘려 끝음절 보존 강화

def num_to_sino(num):
    """일, 이, 삼... (Sino-Korean)"""
    if not num: return ""
    if isinstance(num, str):
        num = int(num.replace(',', ''))
    if num == 0: return '영'
    digits = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
    units = ['', '십', '백', '천']
    big_units = ['', '만', '억', '조', '경']
    result = ""
    num_str = str(num)
    groups = []
    while num_str:
        groups.append(num_str[-4:])
        num_str = num_str[:-4]
    for i, group in enumerate(groups):
        group_res = ""
        for j, d_char in enumerate(reversed(group)):
            d = int(d_char)
            if d > 0:
                if d == 1 and j > 0: group_res = units[j] + group_res
                else: group_res = digits[d] + units[j] + group_res
        if group_res:
            if i == 1 and group_res == '일': result = big_units[i] + result
            else: result = group_res + big_units[i] + result
    return result

def normalize_text(text):
    text = text.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    text = text.replace('"', '').replace("'", "")
    text = text.replace('. ', '.').replace('.', '.. ')
    text = text.replace("외양간", "외양깐").replace("땅바닥", "땅빠닥").replace("임명장", "임명짱")
    
    # 콤마 제거 (금액 등)
    text = re.sub(r'(\d+),(\d+)', r'\1\2', text)
    
    # 1. '번째' (첫 번째, 두 번째...)
    def ordinal_repl(m):
        n = int(m.group(1))
        ord_map = {1: '첫', 2: '두', 3: '세', 4: '네', 5: '다섯'}
        if n in ord_map: return ord_map[n] + " 번째"
        return num_to_sino(n) + " 번째"
    text = re.sub(r'(\d+)\s*번째', ordinal_repl, text)
    
    # 2. Native units (살, 명, 개(?!월), 시, 마리...)
    native_units_map = {1: '한', 2: '두', 3: '세', 4: '네', 5: '다섯', 6: '여섯', 7: '일곱', 8: '여덟', 9: '아홉', 10: '열', 20: '스무'}
    native_units = r'(살|명|개(?!월)|시|마리|권|쪽|장)'
    def native_repl(m):
        n = int(m.group(1))
        if n in native_units_map: return native_units_map[n] + " " + m.group(2)
        return num_to_sino(n) + " " + m.group(2)
    text = re.sub(r'(\d+)\s*' + native_units, native_repl, text)
    
    # 3. Sino units (개월, 세, 년, 월, 일, 분, 초, 원, 층, 호, 회, 차, 위, 평)
    sino_units = r'(개월|세|년|월|일|분|초|원|달러|층|호|회|차|위|평|세대)'
    def sino_repl(m):
        return num_to_sino(m.group(1)) + " " + m.group(2)
    text = re.sub(r'(\d+)\s*' + sino_units, sino_repl, text)
    
    # 4. Standalone digits (Sino)
    text = re.sub(r'\d+', lambda m: num_to_sino(m.group(0)), text)
    
    return re.sub(r'\s+', ' ', text).strip()

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds)
    hours = int(td.total_seconds()) // 3600
    minutes = (int(td.total_seconds()) % 3600) // 60
    secs = int(td.total_seconds()) % 60
    millis = int(td.microseconds / 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def main():
    if len(sys.argv) < 5:
        print("Usage: python sub_gen.py <batch_json_path> <nav_idx> <dia_idx> <out_wav>")
        return

    batch_file = sys.argv[1]
    nav_idx = sys.argv[2]
    dia_idx = sys.argv[3]
    out_wav = sys.argv[4]

    with open(batch_file, "r", encoding="utf-8") as f:
        pieces = json.load(f)

    print(f"🚀 [Worker] Loading Model & Processing {len(pieces)} pieces...")
    model = load(str(MODEL_PATH))

    combined_audio = AudioSegment.empty()
    srt_entries = []
    current_time_sec = 0.0
    PAUSE_MS = 500

    nav_preset = VOICES[nav_idx]
    dia_preset = VOICES[dia_idx]

    for i, piece in enumerate(pieces):
        role = piece["role"]
        raw_text = piece["text"]
        text = normalize_text(raw_text)
        if not text.rstrip().endswith(('.', '!', '?', '..')):
            text = text.rstrip() + ".. " # 💡 끝음절 짤림 방지: 문장 부호 없으면 마침표 2개 강제 삽입
        else:
            text = text.rstrip() + " "
        active_preset = nav_preset if role == "narration" else dia_preset
        
        print(f"🎙️ Generating [{i+1}/{len(pieces)}] ({role}): {text[:30]}...")
        
        ref_wav, sr = librosa.load(active_preset["file"], sr=24000)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            sf.write(tmp.name, ref_wav, sr)
            temp_ref_path = tmp.name

        try:
            results = model.generate(
                text=text,
                ref_audio=temp_ref_path,
                ref_text=active_preset["text"],
                language="Korean",
                temperature=0.8,
                top_p=0.9,
                speed=active_preset.get("speed", 1.0)
            )

            segment_audio_mx = None
            for res in results:
                if segment_audio_mx is None: segment_audio_mx = res.audio
                else: segment_audio_mx = mx.concatenate([segment_audio_mx, res.audio])

            if segment_audio_mx is not None:
                audio_np = np.array(segment_audio_mx)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as stmp:
                    sf.write(stmp.name, audio_np, 24000)
                    stmp_path = stmp.name
                
                segment_pydub = AudioSegment.from_wav(stmp_path)
                os.unlink(stmp_path)
                segment_pydub = trim_silence(segment_pydub)
                
                # [수정] 개별 목소리별 게인(Gain) 적용 (사용자 요청: 9번 15% 증폭 등)
                if "gain" in active_preset:
                    segment_pydub = segment_pydub + active_preset["gain"]
                
                duration_sec = len(segment_pydub) / 1000.0
                srt_entries.append(f"{i+1}\n{format_srt_time(current_time_sec)} --> {format_srt_time(current_time_sec + duration_sec)}\n{raw_text}\n\n")
                
                combined_audio += segment_pydub + AudioSegment.silent(duration=PAUSE_MS)
                current_time_sec += duration_sec + (PAUSE_MS / 1000.0)

        finally:
            if os.path.exists(temp_ref_path): os.unlink(temp_ref_path)

    # Save results
    combined_audio.export(out_wav, format="wav")
    with open(out_wav.replace(".wav", ".srt"), "w", encoding="utf-8") as f:
        f.writelines(srt_entries)
    print(f"✅ Chunk Completed: {out_wav}")

if __name__ == "__main__":
    main()
