import os
import random
from moviepy.editor import ImageClip, VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, vfx
from moviepy.video.tools.subtitles import SubtitlesClip
from pathlib import Path

# ==========================================
# 🛠️ 1. 경로 설정 및 사용자 매개변수
# ==========================================
BASE_DIR = Path("/Users/a12/projects/tts/Grok_Edit_Input")
IMG_DIR = BASE_DIR / "images"      # 원본 이미지들 (01.png, 02.png...)
VID_DIR = BASE_DIR / "videos"      # 그록에서 연동 다운받은 영상들 (02_grok.mp4 처럼 이미지 번호 매칭)
SFX_DIR = BASE_DIR / "audio"       # 효과음 및 목소리
STICKER_DIR = BASE_DIR / "stickers" # 구독/좋아요 팝업 이미지(.png 등)
SUB_DIR = BASE_DIR / "subtitles"  # 자막 (.srt)

OUTPUT_DIR = Path.home() / "Downloads"

# [핵심 노드] 최초 오디오 및 자막
REF_AUDIO = SFX_DIR / "voice.wav"  # 생성된 목소리
REF_SRT = SUB_DIR / "voice.srt"    # 생성된 자막
SFX_FILE = SFX_DIR / "5-0효과음_추가.wav" # 추가할 효과음

# 자막 서식 (Font, Shadow)
FONT_NAME = "Cafe24Danjeonghae" # 폰트 (설치가 안되어 있을 경우 기본 폰트 대체)
FONT_SIZE = 60                   # 자막 폰트 크기
SUBTITLE_POS = ('center', 'bottom') # 하단 배치

TARGET_SIZE = (1080, 1920) # 9:16 쇼츠 비율

# ==========================================
# 📐 2. 헬퍼 함수 (자동 크롭 및 보정)
# ==========================================
def resize_and_pad(clip, target_size=TARGET_SIZE):
    """가로형 이미지를 위아래 블러 덧대거나 비율을 9:16 세로형으로 피팅합니다."""
    # 심플 크롭/리사이즈 (필요에 따라 복잡한 Blur 배경 추가 가능)
    return clip.resize(width=target_size[0]).set_position(('center', 'center'))

def load_srt(srt_path):
    """SRT 자막을 파싱하여 리스트로 뱉어냅니다."""
    generator = lambda txt: TextClip(txt, font=FONT_NAME, fontsize=FONT_SIZE, color='white', stroke_color='black', stroke_width=2)
    return SubtitlesClip(str(srt_path), generator)

# ==========================================
# 🎬 3. 메인 파이프 라인 (조립 가동)
# ==========================================
def main():
    print("==========================================")
    print("🎬 [하이브리드 조립기] 그록 비디오 ➡️ MP4 자동화")
    print("==========================================")

    if not REF_AUDIO.exists() or not REF_SRT.exists():
        print("💡 [오류]: voice.wav 나 voice.srt 가 존재하지 않습니다.")
        return

    # 1. 오디오 로드
    main_audio = AudioFileClip(str(REF_AUDIO))
    total_duration = main_audio.duration
    print(f"🔊 메인 오디오 길이: {total_duration:.2f}초")

    # 2. 이미지 & 비디오 리스팅 및 매칭
    # [순번 대응 구조 필수] 01.png -> 01_grok_video.mp4 가 있으면 비디오로, 없으면 이미지(3초)로 처리
    img_files = sorted(list(IMG_DIR.glob("*.png")))
    vid_files = sorted(list(VID_DIR.glob("*.mp4")))

    clips = []
    
    # 💡 유동형 인코딩: 각 씬의 절대 시간을 SRT 구간에 맞춰 유연하게 조립하거나 3초 기준 계산 가능
    # 여기서는 "3초 가조립 베이스"를 구현합니다.
    for i, img_path in enumerate(img_files):
        num_prefix = f"{i+1:02d}" # "01", "02", "03" ...
        
        # 대응되는 그록 비디오가 있는지 탐색
        matched_vid = next((v for v in vid_files if num_prefix in v.name), None)

        if matched_vid:
            print(f"🎥 [{num_prefix}] 그록 비디오 감지 ➡️ 대체 투입")
            core_clip = VideoFileClip(str(matched_vid))
            # 그록이 6초라 통으로 가져갈 시 오디오 타임라인과 맞는지 확인 필수!
        else:
            print(f"📸 [{num_prefix}] 정적 이미지 ➡️ 3초 기본 생성")
            core_clip = ImageClip(str(img_path)).set_duration(3.0)

        # 9:16 화면비 맞춤
        core_clip = resize_and_pad(core_clip)
        clips.append(core_clip)

    # 3. 비디오 이어 붙이기 (디졸브 크로스페이드 1초 적용)
    # MoviePy 2.x 에서는 concatenate_videoclips 에 padding이나 transition 을 덧댈 수 있습니다.
    final_video = concatenate_videoclips(clips, method="compose") # 디졸브 전환은 vfx.crossfadein 추가 응용

    # 4. 자막(SRT) 스티칭 연동
    subtitles = load_srt(REF_SRT)
    subtitles = subtitles.set_position(('center', TARGET_SIZE[1] / 3 * 2)) # 하단 1/3 지점

    # 5. 스티커 (랜덤 시간 팝업)
    stickers = []
    sticker_files = list(STICKER_DIR.glob("*.png"))
    
    if sticker_files:
        # 무작위 분해 2~3회 호출
        for _ in range(2): 
            stk_path = random.choice(sticker_files)
            stk_clip = ImageClip(str(stk_path)).set_duration(2.0).resize(width=200) # 2초 팝업
            rand_time = random.uniform(5.0, total_duration - 5.0)
            rand_pos = (random.randint(100, 800), random.randint(300, 1200)) # 랜덤 포지션
            stk_clip = stk_clip.set_start(rand_time).set_position(rand_pos)
            stickers.append(stk_clip)

    # 6. 최종 합성 (영상 + 자막 + 스티커들)
    composite_items = [final_video, subtitles] + stickers
    video_with_assets = CompositeVideoClip(composite_items, size=TARGET_SIZE).set_duration(total_duration)

    # 7. 오디오 믹싱 (효과음 덧대기)
    audio_tracks = [main_audio]
    if SFX_FILE.exists():
        sfx_clip = AudioFileClip(str(SFX_FILE)).volumex(0.3) # 30% 볼륨
        # 효과음을 특정 초에 심고 싶다면 sfx_clip.set_start(초) 사용
        audio_tracks.append(sfx_clip)
        
    final_audio = AudioFileClip(str(REF_AUDIO)) # CompositeAudioClip([main_audio, sfx_clip]) 응용 대체 가능
    video_with_assets = video_with_assets.set_audio(final_audio)

    # 8. 최종 렌더링
    output_path = OUTPUT_DIR / "그록조립_최종결과물.mp4"
    print(f"\n🚀 최종 비디오 렌더링 시작 ➡️ {output_path}")
    
    video_with_assets.write_videofile(
        str(output_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4
    )
    print("\n✅ 렌더링 완료!")

if __name__ == "__main__":
    main()
