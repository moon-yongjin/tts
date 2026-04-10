import os
import sys
import re
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from pathlib import Path
import mlx.core as mx
from mlx_audio.tts import load
import numpy as np
import soundfile as sf
import librosa
import tempfile
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
import datetime
import shutil

# ─────────────────────────────────────────────
# 1. 경로 설정 (지침 준수)
# ─────────────────────────────────────────────
PROJECT_ROOT      = Path("/Users/a12/projects/tts/qwen3-tts-apple-silicon")
MODEL_PATH        = PROJECT_ROOT / "models/Qwen3-TTS-12Hz-1.7B-Base-8bit"
sys.path.append(str(PROJECT_ROOT))

TARGET_SCRIPT_PATH = Path("/Users/a12/projects/tts/대본.txt")
OUTPUT_DIR         = Path.home() / "Downloads"
REF_FOLDER         = Path("/Users/a12/projects/tts/1-3_ZeroShot_Studio/voices/Reference")

# 통합 파이프라인 파일 (자동 등록 대상)
FILE_GEN    = Path("/Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/1-3-104_Dual_Sub_Generator.py")
FILE_MASTER = Path("/Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/1-3-104_Dual_Split_Master.py")
FILE_CMD    = Path("/Users/a12/projects/tts/1_1통합파이프뉴_듀얼_고품질.command")

# ─────────────────────────────────────────────
# 2. 유틸리티 함수
# ─────────────────────────────────────────────
def trim_silence(audio, threshold=-50.0, padding_ms=200):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    duration   = len(audio)
    trimmed    = audio[start_trim:duration]
    silence    = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(100) + silence

def num_to_sino(num):
    if not num: return ""
    if isinstance(num, str): num = int(num.replace(',', ''))
    if num == 0: return '영'
    digits = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']; units = ['', '십', '백', '천']; big_units = ['', '만', '억', '조']
    result, num_str = "", str(num)
    groups = []
    while num_str: groups.append(num_str[-4:]); num_str = num_str[:-4]
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
    text = text.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")
    text = text.replace('"', '').replace("'", "")
    text = text.replace('. ', '.').replace('.', '.. ')
    text = text.replace("외양간", "외양깐").replace("땅바닥", "땅빠닥").replace("임명장", "임명짱")
    def ordinal_repl(m):
        n = int(m.group(1)); ord_map = {1:'첫', 2:'두', 3:'세', 4:'네', 5:'다섯'}
        return ord_map.get(n, num_to_sino(n)) + " 번째"
    text = re.sub(r'(\d+)\s*번째', ordinal_repl, text)
    native_map = {1:'한',2:'두',3:'세',4:'네',5:'다섯',6:'여섯',7:'일곱',8:'여덟',9:'아홉',10:'열',20:'스무'}
    text = re.sub(r'(\d+)\s*(살|명|개(?!월)|시|마리|권|쪽|장)', lambda m: native_map.get(int(m.group(1)), num_to_sino(m.group(1))) + " " + m.group(2), text)
    text = re.sub(r'(\d+)\s*(개월|세|년|월|일|분|초|원|달러|층|호|회|차|위|평)', lambda m: num_to_sino(m.group(1)) + " " + m.group(2), text)
    text = re.sub(r'\d+', lambda m: num_to_sino(m.group(0)), text)
    return re.sub(r'\s+', ' ', text).strip()

def format_srt_time(seconds):
    td = datetime.timedelta(seconds=seconds); t = int(td.total_seconds())
    return f"{t // 3600:02d}:{(t % 3600) // 60:02d}:{t % 60:02d},{int(td.microseconds / 1000):03d}"

def split_chunks(text, max_chars=180):
    text = text.replace('\r\n', '\n').replace('\n\n', ' _BREAK_ ').replace('\n', ' ')
    blocks = text.split(' _BREAK_ '); final = []
    for block in blocks:
        block = block.strip()
        if not block: continue
        sentences = re.findall(r'.*?[.!?]+(?:\s+|$)|.+$', block)
        cur = ""
        for s in sentences:
            s = s.strip()
            if not s: continue
            if len(cur) + len(s) + (1 if cur else 0) <= max_chars: cur = (cur + " " + s).strip()
            else:
                if cur: final.append(cur); cur = s
        if cur: final.append(cur)
    return [c.strip() for c in final if c.strip()]

# ─────────────────────────────────────────────
# 3. 자동 등록 시스템 (Advanced Stage 4)
# ─────────────────────────────────────────────
def backup_file(path):
    if path.exists():
        backup_path = path.with_suffix(path.suffix + ".bak")
        shutil.copy2(path, backup_path)
        print(f"📦 백업 생성: {backup_path.name}")

def register_voice(ref_path, ref_text, speed):
    """지침에 따라 3개 파일에 보이스 자동 등록"""
    # ① 이름 입력 받기
    root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
    v_name = simpledialog.askstring("정식 등록", "통합 파이프라인에 등록할 성우 이름을 입력하세요:\n(예: 용진_화남, 여자성우_차분)", parent=root)
    root.destroy()
    if not v_name:
        print("⚠️ 등록 취소됨 (이름 미입력)")
        return None

    # ② 파일 로드 및 ID 찾기
    with open(FILE_MASTER, "r", encoding="utf-8") as f: content_master = f.read()
    
    all_ids = re.findall(r'"(\d+)":', content_master)
    if not all_ids:
        print("❌ 마스터 파일에서 ID를 찾을 수 없습니다.")
        return None
    
    last_id     = max(int(i) for i in all_ids)
    next_id     = str(last_id + 1)
    last_id_str = str(last_id)
    print(f"🔢 할당된 순번: {next_id}")

    # ③ 파일 수정: Dual_Sub_Generator.py
    backup_file(FILE_GEN)
    with open(FILE_GEN, "r", encoding="utf-8") as f: content_gen = f.read()
    gen_entry = f'    "{next_id}": {{"file": "{ref_path}", "text": "{ref_text}", "speed": {speed}}}'
    # 마지막 항목(last_id) 뒤에 콤마 추가 후 새 항목 삽입
    content_gen = re.sub(
        r'("' + last_id_str + r'":\s*\{[^\}]+\})\s*\n\}',
        r'\1,\n' + gen_entry + r'\n}',
        content_gen
    )
    with open(FILE_GEN, "w", encoding="utf-8") as f: f.write(content_gen)

    # ④ 파일 수정: Dual_Split_Master.py
    backup_file(FILE_MASTER)
    master_entry = f'    "{next_id}": "{v_name}"'
    content_master = re.sub(
        r'("' + last_id_str + r'":\s*"[^"]*")\s*\n\}',
        r'\1,\n' + master_entry + r'\n}',
        content_master
    )
    with open(FILE_MASTER, "w", encoding="utf-8") as f: f.write(content_master)

    # ⑤ 파일 수정: 1_1통합파이프뉴_듀얼_고품질.command — 마지막 번호 뒤에 이어붙이기
    backup_file(FILE_CMD)
    with open(FILE_CMD, "r", encoding="utf-8") as f: lines = f.readlines()
    for i, line in enumerate(lines):
        if re.search(rf'\b{last_id_str}\b.*:', line) and line.startswith('#'):
            stripped = line.rstrip('\n').rstrip()
            if len(stripped) > 72:  # 줄이 너무 길면 다음 줄에
                lines.insert(i + 1, f"# {next_id}: {v_name}\n")
            else:
                lines[i] = stripped + f" {next_id}: {v_name}\n"
            break
    with open(FILE_CMD, "w", encoding="utf-8") as f: f.writelines(lines)

    print(f"✅ 등록 완료! 성우[{next_id}: {v_name}]가 통합 파이프라인에 추가되었습니다.")
    return next_id

# ─────────────────────────────────────────────
# 4. 메인 워크플로우
# ─────────────────────────────────────────────
def main():
    print("\n==========================================")
    print("🎙️ Qwen3-TTS [순번 자동 등록 & 제로샷 생성러]")
    print("==========================================")

    # ① 파일 선택 UI
    root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
    ref_path = filedialog.askopenfilename(title="🎙️ 레퍼런스 오디오 선택 (WAV/MP4)", initialdir=str(REF_FOLDER), filetypes=[("오디오/비디오", "*.wav *.mp4 *.m4a *.mp3"), ("모든 파일", "*.*")])
    root.destroy()
    if not ref_path: return

    # ② 정보 입력 (대사, 속도)
    root = tk.Tk(); root.withdraw(); root.attributes('-topmost', True)
    ref_text = simpledialog.askstring("레퍼런스 대사", "오디오에서 말하는 내용을 입력하세요:", parent=root)
    speed_str = simpledialog.askstring("배속", "생성 속도 (기본 1.0):", initialvalue="1.1", parent=root)
    root.destroy()
    ref_text = ref_text.strip() if ref_text else ""
    try: speed = float(speed_str) if speed_str else 1.1
    except: speed = 1.1

    # ③ 정식 등록 실행 (ID 할당)
    voice_id = register_voice(ref_path, ref_text, speed)
    if not voice_id:
        print("⚠️ 등록 없이 생성을 중단하거나 일회성 모드로 전환할 수 있습니다. (현재는 중단)")
        return

    # ④ TTS 생성 실행
    if not TARGET_SCRIPT_PATH.exists(): print(f"❌ 대본 없음: {TARGET_SCRIPT_PATH}"); return
    with open(TARGET_SCRIPT_PATH, "r", encoding="utf-8") as f: raw_text = f.read().strip()
    
    target_text = normalize_text(raw_text)
    chunks = split_chunks(target_text)
    print(f"\n🚀 모델 로드 및 생성 시작 (성우 #{voice_id})")
    model = load(str(MODEL_PATH))

    ref_wav, sr = librosa.load(ref_path, sr=24000)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, ref_wav, sr); temp_ref_path = tmp.name

    combined_audio = AudioSegment.empty(); srt_entries = []; current_time_sec = 0.0; PAUSE_MS = 500

    try:
        for i, chunk in enumerate(chunks):
            print(f"🎙️  [{i+1}/{len(chunks)}] {chunk[:40]}...")
            gen_text = chunk.rstrip() + ("... " if not chunk.rstrip().endswith(('.', '!', '?')) else " ")
            results = model.generate(text=gen_text, ref_audio=temp_ref_path, ref_text=ref_text, language="Korean", temperature=0.8, top_p=0.9, speed=speed)

            segment_mx = None
            for res in results:
                if segment_mx is None: segment_mx = res.audio
                else: segment_mx = mx.concatenate([segment_mx, res.audio])

            if segment_mx is not None:
                audio_np = np.array(segment_mx)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as stmp:
                    sf.write(stmp.name, audio_np, 24000); stmp_path = stmp.name
                seg_pydub = AudioSegment.from_wav(stmp_path); os.unlink(stmp_path)
                seg_pydub = trim_silence(seg_pydub)

                dur = len(seg_pydub) / 1000.0
                srt_entries.append(f"{i+1}\n{format_srt_time(current_time_sec)} --> {format_srt_time(current_time_sec + dur)}\n{chunk}\n\n")
                combined_audio += seg_pydub + AudioSegment.silent(duration=PAUSE_MS)
                current_time_sec += dur + (PAUSE_MS / 1000.0)
    finally:
        if os.path.exists(temp_ref_path): os.unlink(temp_ref_path)

    if len(combined_audio) > 0:
        out_path = OUTPUT_DIR / f"Voice_{voice_id}_Gen_{datetime.datetime.now().strftime('%H%M%S')}.wav"
        combined_audio.export(str(out_path), format="wav")
        with open(str(out_path).replace(".wav", ".srt"), "w", encoding="utf-8-sig") as f: f.writelines(srt_entries)
        print(f"\n✨ 완료! 성우 #{voice_id}로 생성되었습니다.\n🔈 {out_path}")

if __name__ == "__main__":
    main()
