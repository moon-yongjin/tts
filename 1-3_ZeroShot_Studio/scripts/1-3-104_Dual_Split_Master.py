import os
import sys
import json
import subprocess
import time
from pathlib import Path
from pydub import AudioSegment
import re

# 🎙️ Qwen3-TTS [Dual-Speaker Master: Dynamic Batching & Engine Reset]

SOURCE_SCRIPT = "/Users/a12/projects/tts/대본.txt"
VENV_PYTHON = "/Users/a12/projects/tts/qwen3-tts-apple-silicon/.venv/bin/python3"
SUB_GEN_SCRIPT = "/Users/a12/projects/tts/1-3_ZeroShot_Studio/scripts/1-3-104_Dual_Sub_Generator.py"
OUTPUT_FOLDER = Path("/Users/a12/Downloads")

MAX_CHARS = 180  # 청크(조각) 분할 기준: 그대로 유지 (1청크마다 엔진 리셋)

VOICES = {
    "1": "새 레퍼런스 (금융/비즈니스 차분한 톤)",
    "2": "인강샘 (비즈니스/강사 또박또박한 톤)",
    "3": "클래식언니 (유튜브 나레이션 톤)",
    "4": "강지영3 (아나운서 톤)",
    "5": "감성_슬픔 (드라마/복수 추천 톤)",
    "6": "슬슬이 (틱톡 숏폼 / 대화톤)",
    "7": "교통방송 (차분한 나레이션 톤)",
    "8": "오디오북 (픽업트럭 감성 톤)",
    "9": "오디오1 (주민회 회장 톤 - 레퍼런스3 교정본)",
    "10": "아침마당 (푸근한 중년 여성 톤 - 0403)",
    "11": "차주영 (임팩트 있는 화난 연기 톤 - 0403)",
    "12": "깔끔정리녀 (조곤조곤한 정보전달 톤 - 0403)",
    "13": "유해진 (특유의 코믹하고 억울한 연기 톤 - 0404)",
    "14": "정승재 (열정적인 1타 강사 강의 톤 - 0404)",
    "15": "교육/설명 (차분하고 신뢰감 있는 톤 - 0404)",
    "16": "협상/사업가 (확신에 찬 강한 어조 - 0404)",
    "17": "감성/스토리 (부드럽고 차분한 나레이션 톤 - 0404)",
    "18": "TikTokLite (0405 - 뉴스/연설)",
    "19": "YouTube (0403 - 생활/대화)",
    "20": "용진",
    "21": "여자성우",
    "22": "봉봉 (234401)",
    "23": "충격비밀 (234501)",
    "24": "보릿살 (234701)"
}

def split_chunks_single_role(text, max_chars=180):
    text = text.replace('\r\n', '\n').replace('\n\n', ' _DOUBLE_BREAK_ ')
    text = text.replace('\n', ' ')
    blocks = text.split(' _DOUBLE_BREAK_ ')
    final_chunks = []
    for block in blocks:
        block = block.strip()
        if not block: continue
        
        # 문장 단위(., !, ?)로 먼저 분리 (뒤에 오는 공백 포함)
        sentences = re.findall(r'.*?[.!?]+(?:\s+|$)|.*?.+$', block)
        
        current_chunk = ""
        for s in sentences:
            s = s.strip()
            if not s: continue
            
            # 현재 청크에 이 문장을 합쳤을 때 제한을 넘는지 확인
            if len(current_chunk) + len(s) + (1 if current_chunk else 0) <= max_chars:
                current_chunk = (current_chunk + " " + s).strip()
            else:
                # 합치면 넘어가니까 일단 현재까지 쌓인 걸 배출
                if current_chunk:
                    final_chunks.append(current_chunk)
                    current_chunk = s
                else:
                    # 문장 하나가 180자를 넘어가는 극단적인 경우
                    if len(s) > max_chars:
                        words = s.split(" ")
                        for w in words:
                            if not w: continue
                            if len(current_chunk) + len(w) + 1 <= max_chars:
                                current_chunk = (current_chunk + " " + w).strip()
                            else:
                                if current_chunk: final_chunks.append(current_chunk)
                                current_chunk = w
                    else:
                        current_chunk = s
        
        if current_chunk:
            final_chunks.append(current_chunk)
    
    return [c.strip() for c in final_chunks if c.strip()]

def split_chunks_dual_advanced(text, max_chars=180):
    text = text.replace('“', '"').replace('”', '"')
    parts = re.split(r'("[^"]*")', text)
    result = []
    for p in parts:
        if not p: continue
        role = "dialogue" if p.startswith('"') else "narration"
        clean_text = p.replace('"', '').strip()
        if not clean_text: continue
        sub_chunks = split_chunks_single_role(clean_text, MAX_CHARS)
        for sc in sub_chunks:
            chunk_text = sc.strip()
            # 청크 끝이 너무 짧게 끝나는 것을 방지하기 위해 마침표 3개를 추가
            if not chunk_text.endswith("..."):
                chunk_text += "..."
            result.append({"role": role, "text": chunk_text})
    return result

def main():
    print("\n" + "="*50)
    print("🎙️ Qwen3-TTS [고품질 듀얼스피커 자동 분할 파이프라인]")
    print("="*50)

    for k, v in VOICES.items(): print(f"  [{k}] {v}")
    
    # Check if we are in non-interactive mode (for testing)
    if len(sys.argv) >= 3:
        nav_idx = sys.argv[1]
        dia_idx = sys.argv[2]
    else:
        nav_idx = input("\n▶️ 1. [나레이션] 목소리 번호 (1-19): ").strip()
        dia_idx = input("▶️ 2. [따옴표 대사] 목소리 번호 (1-19): ").strip()

    if nav_idx not in VOICES or dia_idx not in VOICES:
        print("❌ 잘못된 선택입니다.")
        return

    if not os.path.exists(SOURCE_SCRIPT):
        print(f"❌ Error: {SOURCE_SCRIPT} not found")
        return

    print(f"\n✅ 배정 완료: 나레이션(#{nav_idx}), 대사(#{dia_idx})")

    with open(SOURCE_SCRIPT, "r", encoding="utf-8") as f:
        script_text = f.read()

    all_pieces = split_chunks_dual_advanced(script_text)
    # 1청크(조각)마다 엔진 리셋 (항상 안정적인 상태 유지)
    batches = [[p] for p in all_pieces]
    
    print(f"📦 총 {len(all_pieces)}개 피스 -> {len(batches)}개 배치로 분할 완료.")

    temp_wavs = []
    for i, batch in enumerate(batches):
        batch_json = f"/tmp/dual_batch_{i}.json"
        with open(batch_json, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False)
        
        out_wav = f"/tmp/dual_out_{i}.wav"
        temp_wavs.append(out_wav)
        
        cmd = [VENV_PYTHON, SUB_GEN_SCRIPT, batch_json, nav_idx, dia_idx, out_wav]
        print(f"\n🔄 [배치 {i+1}/{len(batches)}] 엔진 리셋 및 생성 중...")
        subprocess.run(cmd)

    # Merging
    combined_audio = AudioSegment.empty()
    final_srt_content = []
    cumulative_offset = 0.0
    global_index = 1

    print("\n🔗 [Merging] 최종 합본 생성 중...")
    for wav in temp_wavs:
        if not os.path.exists(wav): continue
        seg = AudioSegment.from_wav(wav)
        duration = len(seg) / 1000.0
        combined_audio += seg

        srt = wav.replace(".wav", ".srt")
        if os.path.exists(srt):
            with open(srt, "r", encoding="utf-8") as f:
                lines = f.readlines()
            for line in lines:
                if " --> " in line:
                    start, end = line.strip().split(" --> ")
                    s_h, s_m, s_s = start.replace(",", ".").split(":")
                    e_h, e_m, e_s = end.replace(",", ".").split(":")
                    s_sec = float(s_h)*3600 + float(s_m)*60 + float(s_s) + cumulative_offset
                    e_sec = float(e_h)*3600 + float(e_m)*60 + float(e_s) + cumulative_offset
                    def fmt(s):
                        h = int(s // 3600)
                        m = int((s % 3600) // 60)
                        return f"{h:02d}:{m:02d}:{s%60:06.3f}".replace(".", ",")
                    line = f"{fmt(s_sec)} --> {fmt(e_sec)}\n"
                elif line.strip().isdigit():
                    line = f"{global_index}\n"
                    global_index += 1
                final_srt_content.append(line)
            final_srt_content.append("\n")
        cumulative_offset += duration

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    res_wav = OUTPUT_FOLDER / f"고품질_듀얼합본_{timestamp}.wav"
    res_srt = OUTPUT_FOLDER / f"고품질_듀얼합본_{timestamp}.srt"
    
    combined_audio.export(res_wav, format="wav")
    with open(res_srt, "w", encoding="utf-8-sig") as f:
        f.writelines(final_srt_content)

    print(f"\n✨ 생성 완료! 다운로드 폴더를 확인하세요.")
    print(f"🔈 {res_wav.name}")
    print(f"📜 {res_srt.name}")

    # ✂️ [자동화] 자막 분할 후작업 가동 (8~10자 쪼개기)
    sub_split_script = "/Users/a12/projects/tts/core_v2/04_srt_subsplitter.py"
    if os.path.exists(sub_split_script):
        print("\n✂️ [자동화] 자막 분할 후작업 가동 중 (8~12자 비례배분)...")
        subprocess.run([sys.executable, sub_split_script])

if __name__ == "__main__":
    main()
