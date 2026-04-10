import os
import time
import json
import subprocess
import re
from pathlib import Path
from pydub import AudioSegment

class LiveSyncEditor:
    def __init__(self, txt_path, video_source, output_wav):
        self.txt_path = Path(txt_path)
        self.video_source = Path(video_source)
        self.output_wav = Path(output_wav)
        self.last_mtime = 0
        self.full_audio = None
        self.temp_wav = self.output_wav.parent / "sync_temp_full.wav"

    def prepare_base_audio(self):
        """원본 영상을 고품질 WAV로 미리 변환 (속도 향상)"""
        if not self.temp_wav.exists():
            print(f"📦 원본 오디오 추출 중...")
            subprocess.run([
                "ffmpeg", "-y", "-i", str(self.video_source),
                "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
                str(self.temp_wav)
            ], capture_output=True)
        self.full_audio = AudioSegment.from_wav(str(self.temp_wav))

    def parse_txt_and_merge(self):
        """텍스트 파일의 타임스탬프를 읽어 오디오 병합"""
        print(f"🔄 편집 감지! 새 오디오 생성 중...")
        
        with open(self.txt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        combined = AudioSegment.empty()
        count = 0
        
        for line in lines:
            # [123.45s] 형식의 타임스탬프 추출
            match = re.search(r"\[(\d+\.?\d*)s\]", line)
            if match:
                start_sec = float(match.group(1))
                
                # 타임스탬프 뒤의 텍스트가 비어 있거나 무의미한 문표만 있으면 스킵
                content = re.sub(r"\[\d+\.?\d*s\]", "", line).strip()
                # 의미 있는 글자가 하나라도 있어야 함 (한글/영문/숫자)
                if not re.search(r"[가-힣a-zA-Z0-9]", content):
                    print(f"⏩ 스킵 (내용 없음): {line.strip()}")
                    continue

                end_sec = self.get_end_time(start_sec)
                
                if end_sec > start_sec:
                    start_ms = int(start_sec * 1000)
                    end_ms = int(end_sec * 1000)
                    chunk = self.full_audio[start_ms:end_ms]
                    
                    if len(combined) > 0:
                        combined = combined.append(chunk, crossfade=100)
                    else:
                        combined = chunk
                    combined += AudioSegment.silent(duration=200) # 여운
                    count += 1

        if count > 0:
            combined.export(str(self.output_wav), format="wav")
            print(f"✅ 동기화 완료! ({count}개 조각) -> {self.output_wav.name}")
        else:
            print("⚠️ 남은 유효한 텍스트 줄이 없습니다.")

    def get_end_time(self, start_time):
        """JSON 데이터에서 해당 시작 시간에 맞는 종료 시간을 찾음"""
        # (이 부분은 외부에서 segments 데이터를 주입받아 처리)
        for s in self.segments:
            if abs(s["start"] - start_time) < 0.1:
                return s["end"]
        return start_time + 2.0 # 못 찾을 시 기본 2초

    def start_watch(self, segments):
        self.segments = segments
        self.prepare_base_audio()
        print(f"👀 감시 시작: {self.txt_path.name}")
        print("💡 텍스트를 지우고 저장(Cmd+S)하면 오디오가 즉시 바뀝니다.")
        
        while True:
            try:
                mtime = os.path.getmtime(self.txt_path)
                if mtime != self.last_mtime:
                    self.parse_txt_and_merge()
                    self.last_mtime = mtime
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)

if __name__ == "__main__":
    import sys
    # 고정된 경로 테스트용
    txt = "/Users/a12/Downloads/extracted_assets/test_story_04_pinpoint/04_Pinpoint_Visual_Hardship_Transcript.txt"
    vid = "/Users/a12/Downloads/100분_눈물_콧물_주의_슬픈_사연_모음_책임감이라는_단어가_주는_마음의_무게에서_벗어나_나를_먼저_돌아보기_김창옥쇼2_clips/04_치매_시어머니를_모시며_앞집_아저씨처럼_느껴지는_남편.mp4"
    json_data = "/Users/a12/Downloads/extracted_assets/test_story_04/04_Diarized_Result_Pre_Shorts.json"
    out = "/Users/a12/Downloads/extracted_assets/test_story_04_pinpoint/04_LIVE_SYNC_EDIT.wav"

    with open(json_data, "r", encoding="utf-8") as f:
        segs = json.load(f)

    syncer = LiveSyncEditor(txt, vid, out)
    syncer.start_watch(segs)
