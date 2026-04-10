import os
import shutil
import subprocess
import time
import glob
import sys
import json
import re
import unicodedata
from pathlib import Path
import google.generativeai as genai
# import natsort  # 의존성 제거: 수동 구현된 natural_sort_key 사용

# --- 설정 (Paths) ---
PROJ_ROOT = Path("/Users/a12/projects/tts")
CORE_V2 = PROJ_ROOT / "core_v2"
DOWNLOADS_DIR = Path(os.path.expanduser("~")) / "Downloads"
PROJECT_ROOT = PROJ_ROOT / "remotion-hello-world"
PUBLIC_DIR = PROJECT_ROOT / "public"
IMAGES_DIR = PUBLIC_DIR / "images"
SFX_PUBLIC_DIR = PUBLIC_DIR / "sfx"
LIB_SFX_DIR = CORE_V2 / "Library" / "sfx"
CONFIG_PATH = PROJ_ROOT / "config.json"

# NFC/NFD 통합 대응
def normalize_name(n):
    return unicodedata.normalize('NFC', n)

def natural_sort_key(s):
    """숫자를 인식하는 정렬 키 (Natural Sort)"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', str(s))]

def get_latest_image_dir(base_dir):
    prefixes = ("다이어리_", "무협_", "틱톡_", "시나리오_", "막장_", "drama_")
    subdirs = []
    for d in os.listdir(base_dir):
        full_path = base_dir / d
        if not full_path.is_dir():
            continue
        
        # 폴더 내부에 PNG 파일이 최소 하나라도 있는지 확인 (비어있는 폴더 방지)
        if not any(f.lower().endswith(".png") for f in os.listdir(full_path)):
            continue

        norm_d = normalize_name(d)
        if any(norm_d.startswith(p) for p in prefixes):
            subdirs.append(full_path)
    
    subdirs = sorted(subdirs, key=lambda x: x.stat().st_mtime, reverse=True)
    return subdirs[0] if subdirs else None

def get_latest_file(pattern, directory):
    files = list(directory.glob(pattern))
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def parse_srt(srt_path):
    if not srt_path or not srt_path.exists(): return []
    events = []
    try:
        with open(srt_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
        blocks = re.split(r'\n\s*\n', content.strip())
        for block in blocks:
            lines = block.splitlines()
            if len(lines) >= 3:
                times = re.findall(r'(\d{2}:\d{2}:\d{2},\d{3})', lines[1])
                if len(times) >= 2:
                    h, m, s_ms = times[0].split(':')
                    s, ms = s_ms.split(',')
                    start_sec = (int(h)*3600 + int(m)*60 + int(s)) + int(ms)/1000
                    events.append({'timestamp': start_sec, 'text': " ".join(lines[2:])})
    except Exception as e:
        print(f"⚠️ SRT 파싱 오류: {e}")
    return events

def run_ai_sfx_director(srt_events, apiKey):
    print("🤖 [AI Director] 대본 분석 및 효과음 리스트 생성 중...")
    
    if not srt_events: return []
    
    if not apiKey:
        print("⚠️ Gemini API Key가 없어 SFX 자동 배치를 건너뜁니다.")
        return []

    genai.configure(api_key=apiKey)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # 효과음 라이브러리 목록
    sfx_library = [f for f in os.listdir(LIB_SFX_DIR) if f.lower().endswith(('.mp3', '.wav'))]
    sfx_names = ", ".join([os.path.splitext(f)[0] for f in sfx_library])
    
    # 10초 간격으로 배치 시도
    sfx_config = []
    last_sfx_time = -10
    
    for event in srt_events:
        curr_time = event['timestamp']
        if curr_time - last_sfx_time < 10: continue
        
        prompt = f"""
동화/드라마의 오디오 디렉터로서 자막 내용에 어울리는 효과음 하나를 목록에서 골라주세요.
자막: "{event['text']}"
효과음 목록: {sfx_names}
- 반드시 목록에 있는 파일명(확장자 제외) 하나만 답변하세요.
- 어울리는 게 없으면 'None'이라고 하세요.
- 답변은 파일명만 딱 한 단어로 하세요.
"""
        try:
            response = model.generate_content(prompt)
            choice = response.text.strip().lower()
            if "none" in choice: continue
            
            for f in sfx_library:
                fname = os.path.splitext(f)[0].lower()
                if fname == choice or (len(choice) >= 4 and choice in fname):
                    sfx_config.append({
                        "timestamp": curr_time,
                        "sfx_file": f,
                        "reason": event['text'][:20]
                    })
                    print(f"   🔔 SFX 매칭: {f} @ {curr_time:.1f}s")
                    last_sfx_time = curr_time
                    break
        except: pass
        
    return sfx_config

def generate_video_title(script_text, api_key):
    """대본 내용을 바탕으로 자극적이고 맛깔나는 제목 생성"""
    if not api_key: return "배은망덕한 자식들의 몰락" # 기본값
    
    print("🤖 [AI Director] 영상 제목 생성 중...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    prompt = f"""
동화/드라마 유튜브 채널의 제목을 지어주세요. 
시청자들의 클릭을 유도할 수 있도록 자극적이고 통쾌한 '참교육' 느낌이 나야 합니다.
대본 내용:
{script_text[:1000]}...

- 반드시 한국어로 답변하세요.
- 한 문장으로 맛깔나게 지어주세요.
- 제목만 딱 답변하세요. (예: 아들을 버린 비정한 어머니의 비참한 최후)
- 이모티콘이나 특수기호는 제외하세요.
"""
    try:
        response = model.generate_content(prompt)
        return response.text.replace('"', '').replace("'", "").strip()
    except Exception as e:
        print(f"⚠️ 제목 생성 실패: {e}")
        return "배은망덕한 자식들의 몰락"

def run_auto_render():
    print("\n" + "="*50)
    print("🚀 [Step 07-2] 리모션 이미지 애니메이션 자동화 렌더러 시작")
    print("="*50)

    # 0. 프로젝트 청소 (기존 에셋 제거)
    print("\n🧹 기존 에셋 및 출력물 청소 중...")
    if IMAGES_DIR.exists(): shutil.rmtree(IMAGES_DIR)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    OUT_DIR = PROJECT_ROOT / "out"
    if OUT_DIR.exists():
        for f in os.listdir(OUT_DIR):
            try:
                f_path = OUT_DIR / f
                if f_path.is_file(): os.remove(f_path)
            except: pass
            
    for ext in ["wav", "mp3", "srt"]:
        p = PUBLIC_DIR / f"latest_drama.{ext}"
        if p.exists(): os.remove(p)

    # 1. 대상 찾기 (다운로드 폴더 기반)
    # 오디오: mp3 우선, 없으면 wav
    latest_audio = get_latest_file("*.mp3", DOWNLOADS_DIR) or get_latest_file("*.wav", DOWNLOADS_DIR)
    latest_srt = get_latest_file("*.srt", DOWNLOADS_DIR)
    
    # 이미지:prefix "마지막 야상곡" 혹은 "드라마_" 등으로 시작하는 최신 폴더 혹은 파일들
    latest_img_dir = get_latest_image_dir(DOWNLOADS_DIR)
    
    # 1.1 이미지 분석 (Variation_1 폴더가 있으면 그 안에서 수집)
    images = []
    source_dir = None

    if latest_img_dir:
        # 1.1.1 Variation_1 폴더가 있는지 우선 확인
        var1_dir = latest_img_dir / "Variation_1"
        if var1_dir.exists() and var1_dir.is_dir():
            print(f"   📂 Variation_1 폴더 발견! 해당 폴더에서 이미지를 가져옵니다.")
            source_dir = var1_dir
        else:
            source_dir = latest_img_dir
        
        raw_images = [f for f in os.listdir(source_dir) if f.lower().endswith(".png")]
        images = sorted(raw_images, key=natural_sort_key)
    else:
        # 폴더가 없으면 에셋명이 특정 패턴인 것들을 직접 찾음
        raw_images = [f for f in os.listdir(DOWNLOADS_DIR) if f.lower().endswith(".png") and any(p in normalize_name(f) for p in ["장면_", "Scene_"])]
        if not raw_images:
            raw_images = [f for f in os.listdir(DOWNLOADS_DIR) if f.lower().endswith(".png")]
            
        images = sorted(raw_images, key=natural_sort_key)
        source_dir = DOWNLOADS_DIR

    if not latest_audio or not latest_srt or not images:
        print("❌ 필수 에셋이 부족합니다. (오디오, 자막, 혹은 이미지)")
        if not latest_audio: print("   - 오디오 없음 (*.mp3 or *.wav)")
        if not latest_srt: print("   - 자막 없음 (*.srt)")
        if not images: print("   - 이미지 없음 (*.png)")
        return

    # 2. 에셋 이동
    print(f"\n📂 에셋 이동 및 표준화 중...")
    print(f"   🎙️ 오디오: {latest_audio.name}")
    print(f"   📜 자막: {latest_srt.name}")
    print(f"   🖼️ 이미지: {len(images)}개")
    
    # 확장자 유지하며 이름 표준화 (Remotion DramaVideo.tsx가 mp3를 찾으면 mp3로, wav면 wav로)
    audio_ext = latest_audio.suffix.lower().replace('.', '')
    DRAMA_AUDIO = PUBLIC_DIR / f"latest_drama.{audio_ext}"
    DRAMA_SRT = PUBLIC_DIR / "latest_drama.srt"
    
    shutil.copy2(latest_audio, DRAMA_AUDIO)
    shutil.copy2(latest_srt, DRAMA_SRT)
    
    # 2.1 이미지 이동 및 리네이밍 (image_000.png...)
    image_list = []
    for i, img in enumerate(images):
        new_name = f"image_{i:03d}.png"
        shutil.copy2(source_dir / img, IMAGES_DIR / new_name)
        image_list.append(new_name)
    
    with open(PUBLIC_DIR / "images.json", "w", encoding="utf-8") as f:
        json.dump(image_list, f, ensure_ascii=False, indent=2)

    # 2.1.1 인트로 비디오
    intro_source = DOWNLOADS_DIR / "intro.mp4"
    if intro_source.exists():
        print("🎬 새로운 인트로 비디오 발견!")
        intro_dest_dir = PUBLIC_DIR / "videos"
        intro_dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(intro_source, intro_dest_dir / "intro.mp4")

    # API 키 로드
    apiKey = None
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            apiKey = json.load(f).get("Gemini_API_KEY")

    # 2.2 SFX 및 제목 자동화 로직
    srt_events = parse_srt(latest_srt)
    sfx_config = run_ai_sfx_director(srt_events, apiKey)
    
    # 자막 내용을 하나의 텍스트로 합쳐서 제목 생성의 소스로 사용
    full_subtitle_text = " ".join([e['text'] for e in srt_events])
    video_title = generate_video_title(full_subtitle_text, apiKey)
    print(f"🎬 생성된 제목: {video_title}")

    # 기존 metadata.json이 있으면 트리밍 정보(trimStart, trimEnd) 보관
    old_trims = {}
    META_PATH = PUBLIC_DIR / "metadata.json"
    if META_PATH.exists():
        try:
            with open(META_PATH, "r", encoding="utf-8") as f:
                old_meta = json.load(f)
                for item in old_meta.get("images", []):
                    if isinstance(item, dict) and "name" in item:
                        # 파일명(image_000.mp4 등)을 키로 트리밍 정보 저장
                        old_trims[item["name"]] = {
                            "trimStart": item.get("trimStart"),
                            "trimEnd": item.get("trimEnd")
                        }
        except: pass

    # metadata.json 및 sfx_config_drama.json 저장
    final_images = []
    for img_name in image_list:
        if img_name in old_trims:
            trimmed_item = {"name": img_name}
            if old_trims[img_name]["trimStart"] is not None:
                trimmed_item["trimStart"] = old_trims[img_name]["trimStart"]
            if old_trims[img_name]["trimEnd"] is not None:
                trimmed_item["trimEnd"] = old_trims[img_name]["trimEnd"]
            final_images.append(trimmed_item)
        else:
            final_images.append(img_name)

    metadata = {
        "title": video_title,
        "audio_file": DRAMA_AUDIO.name,
        "images": final_images
    }
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    with open(PUBLIC_DIR / "sfx_config_drama.json", "w", encoding="utf-8") as f:
        json.dump(sfx_config, f, ensure_ascii=False, indent=2)
    
    # 사용된 SFX 파일들만 public/sfx로 복사
    if SFX_PUBLIC_DIR.exists(): shutil.rmtree(SFX_PUBLIC_DIR)
    SFX_PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    
    for item in sfx_config:
        sfx_name = item["sfx_file"]
        src_sfx = LIB_SFX_DIR / sfx_name
        if src_sfx.exists():
            shutil.copy2(src_sfx, SFX_PUBLIC_DIR / sfx_name)
            
    print(f"✅ 에셋 및 메타데이터 설정 완료 (효과음 {len(sfx_config)}개 배치됨)")

    # 3. 리모션 렌더링 실행
    print("\n🎬 리모션 렌더링 시작...")
    timestamp = int(time.time())
    final_filename = f"DRAMA_FINAL_{timestamp}.mp4"
    output_path = PROJECT_ROOT / "out" / final_filename
    
    render_cmd = ["npx", "remotion", "render", "src/index.ts", "JunkyardDrama", str(output_path), "--chromium-flags=\"--disable-web-security\""]

    try:
        subprocess.run(render_cmd, cwd=str(PROJECT_ROOT), check=True)
        print(f"✅ 리모션 본편 렌더링 완료: {output_path}")

        # 4. 외부 인트로 합치기 (FFmpeg)
        print("\n🎬 인트로와 본편 합치는 중...")
        intro_path = PUBLIC_DIR / "videos" / "intro.mp4"
        merged_filename = f"INTRO_{timestamp}.mp4"
        merged_output_path = PROJECT_ROOT / "out" / merged_filename

        if intro_path.exists():
            print("⚙️ 영상 규칙 정규화 및 합치기 진행 중 (Fill/Crop 모드: 1080x1920, 30fps)...")
            # 가로형 인트로를 세로형 틀에 '꽉 채우기' 위해 increase + crop 적용
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", str(intro_path),
                "-i", str(output_path),
                "-filter_complex", 
                "[0:v]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v0];"
                "[1:v]fps=30,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[v1];"
                "[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a0];"
                "[1:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[a1];"
                "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]",
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                "-c:a", "aac", "-b:a", "192k",
                str(merged_output_path)
            ]

            subprocess.run(ffmpeg_cmd, check=True)
            print(f"✅ 인트로 합치기 완료: {merged_output_path}")
            
            final_delivery_path = merged_output_path
        else:
            print("⚠️ 인트로 영상(intro.mp4)을 찾을 수 없어 본편만 전달합니다.")
            final_delivery_path = output_path

        destination = DOWNLOADS_DIR / final_delivery_path.name
        shutil.move(str(final_delivery_path), str(destination))
        print(f"🚚 최종 영상이 다운로드 폴더로 배송되었습니다: {destination}")

    except subprocess.CalledProcessError as e:
        print(f"❌ 렌더링 또는 합치기 중 오류 발생: {e}")
        return

    print("\n🎉 모든 작업이 끝났습니다!")
    print("="*50)

if __name__ == "__main__":
    run_auto_render()
