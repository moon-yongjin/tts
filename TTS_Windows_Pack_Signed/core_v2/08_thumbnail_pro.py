import os
import json
import re
import sys
import subprocess
import random
import time
import google.generativeai as genai

# [설정]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(SCRIPT_DIR) == "core_v2":
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    CORE_DIR = SCRIPT_DIR
else:
    ROOT_DIR = SCRIPT_DIR
    CORE_DIR = os.path.join(ROOT_DIR, "core_v2")

FFMPEG_EXE = "/Users/a12/miniforge3/envs/qwen-tts/bin/ffmpeg"
if not os.path.exists(FFMPEG_EXE):
    FFMPEG_EXE = "ffmpeg"

DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
GOOGLE_API_KEY = "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"

genai.configure(api_key=GOOGLE_API_KEY)

# [가챠 색상 팔레트 - 5가지 조합 (ASS 전용 BGR 형식)]
# Primary: 메인글자, Highlight1: 주어, Highlight2: 숫자, Border: 테두리 프레임
GACHA_PALETTES = [
    {"name": "네온 골드", "primary": "FFFFFF", "hl1": "00FFFF", "hl2": "FFFF00", "border": "00FFFF"}, # 노랑 테두리
    {"name": "일렉트릭 블루", "primary": "FFFFFF", "hl1": "00FFFF", "hl2": "00FF00", "border": "FF0000"}, # 블루 테두리
    {"name": "핫 레드", "primary": "FFFFFF", "hl1": "00FFFF", "hl2": "FFFF00", "border": "0000FF"}, # 레드 테두리
    {"name": "사이버 핑크", "primary": "FFFFFF", "hl1": "00FFFF", "hl2": "FFFF00", "border": "FF00FF"}, # 핑크 테두리
    {"name": "에메랄드 포스", "primary": "FFFFFF", "hl1": "0000FF", "hl2": "00FFFF", "border": "00FF00"}  # 그린 테두리
]

def get_latest_folder():
    folders = [os.path.join(DOWNLOADS_DIR, d) for d in os.listdir(DOWNLOADS_DIR) 
               if os.path.isdir(os.path.join(DOWNLOADS_DIR, d)) and (d.startswith("무협_생성_") or d.startswith("무협_로컬생성_"))]
    if not folders: return None
    return max(folders, key=os.path.getmtime)

def suggest_thumbnail_gacha(script_text):
    """5가지 다양한 스타일의 문구와 옆자리 작은 문구 추천"""
    model = genai.GenerativeModel('gemini-2.0-flash')
    prompt = f"""
    Analyze this script and suggest 5 high-impact thumbnail title sets for a YouTube video.
    
    Rules:
    1. 'main': 2 lines of text (approx 12-18 chars total).
    2. 'side': A short punchy comment (e.g. "진짜 충격적임", "아무도 몰랐다") to place on the side of a character.
    3. 'keyword': The main subject/action to highlight.
    4. 'amount': Any number or shocking detail like "300억", "살인마", "범인" to highlight in a secondary color.
    
    Return ONLY a JSON array.
    
    Format JSON:
    [
      {{ "line1": "300억 가로챈 남편의", "line2": "추악하고 소름돋는 정체", "keyword": "정체", "amount": "300억", "side": "이게 실화라고?" }},
      ... (TOTAL 5 SETS)
    ]
    
    Script Content:
    {script_text[:3000]}
    """
    try:
        resp = model.generate_content(prompt)
        clean = resp.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except:
        return [{"line1": "10년을 기다린 복수의", "line2": "처절한 마지막 승부", "keyword": "복수", "amount": "10년", "side": "결말 미쳤음"}] * 5

def create_gacha_ass(ass_path, title_obj, palette):
    """자간 축소(-6), 위아래 초필살 밀착(별도 이벤트), 3색 하이라이팅"""
    l1, l2 = title_obj['line1'], title_obj['line2']
    hl1, hl2 = title_obj['keyword'], title_obj['amount']
    side = title_obj.get('side', "")
    
    p, h1, h2 = palette['primary'], palette['hl1'], palette['hl2']
    
    # 컬러 하이라이팅 함수 (원본 케이스 보존)
    def apply_color(text, keyword, color):
        if not keyword: return text
        pattern = re.compile(re.escape(str(keyword)), re.IGNORECASE)
        # re.sub에서 백슬래시는 \\\\로 이스케이프해야 합니다.
        return pattern.sub(f"{{\\\\c&H{color}&}}{keyword}{{\\\\c&H{p}&}}", text)

    l1_styled = apply_color(l1, hl1, h1)
    l1_styled = apply_color(l1_styled, hl2, h2)
    l2_styled = apply_color(l2, hl1, h1)
    l2_styled = apply_color(l2_styled, hl2, h2)
    
    # [정밀 위치 계산]
    # PlayResY 720 기준, 노란 테두리(30px) 바로 위에 얹히도록 좌표 설정
    y_end = 685 
    gap = 100 # 130 폰트 대비 100 간격은 글자가 거의 맞닿는 포스터 스타일
    
    ass_header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Cafe24 Ohsquare,130,&H00{p}&,&H00000000,&H00000000,-1,0,0,0,100,100,-6,0,1,1,6,2,10,10,10,1
Style: Side,Cafe24 Ohsquare,55,&H00{h1}&,&H00000000,&H00000000,-1,0,0,0,100,100,0,12,1,1,2,6,30,30,350,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,0:00:00.00,0:00:10.00,Main,,0,0,0,,{{\\pos(640,{y_end-gap})}}{l1_styled}
Dialogue: 1,0:00:00.00,0:00:10.00,Main,,0,0,0,,{{\\pos(640,{y_end})}}{l2_styled}
Dialogue: 2,0:00:00.00,0:00:10.00,Side,,0,0,0,,{side}
"""
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_header)

def run_gacha_thumbnail():
    print("\n" + "="*50)
    print("🎰 [GACHA] 시네마틱 섬네일 엔진 - 5가지 색상 & 문구")
    print("="*50)
    
    script_path = os.path.join(ROOT_DIR, "대본.txt")
    with open(script_path, "r", encoding="utf-8") as f: script_text = f.read()

    print("🎲 AI가 5가지 '가챠' 문구를 생성 중...")
    titles = suggest_thumbnail_gacha(script_text)
    
    for i, t in enumerate(titles):
        print(f"{i+1}. [{t['side']}] {t['line1']} / {t['line2']}")
    print("6. [직접 입력] 원하는 문구를 직접 작성")

    choice = input("\n👉 문구 선택 (번호): ").strip()
    
    selected_title = titles[0] # Default
    if choice == "6":
        print("\n📝 [수동 입력 모드]")
        l1 = input("메인 줄 1: ").strip()
        l2 = input("메인 줄 2: ").strip()
        kw = input("강조할 주어 (색상1): ").strip()
        amt = input("강조할 숫자/단어 (색상2): ").strip()
        side = input("사이드 문구: ").strip()
        selected_title = {"line1": l1, "line2": l2, "keyword": kw, "amount": amt, "side": side}
    elif choice.isdigit() and 1<=int(choice)<=5:
        selected_title = titles[int(choice)-1]

    # 가챠 색상 뽑기
    palette = random.choice(GACHA_PALETTES)
    print(f"\n🎨 뽑힌 색상 팔레트: [{palette['name']}] (테두리: {palette['border']})")

    target_dir = get_latest_folder()
    images = sorted([f for f in os.listdir(target_dir) if f.endswith(".png") or f.endswith(".jpg")])
    img_choice = input(f"📸 이미지 번호 (기본 끝번): ").strip()
    img_path = os.path.join(target_dir, images[int(img_choice)-1]) if img_choice.isdigit() else os.path.join(target_dir, images[-1])

    ass_path = os.path.join(target_dir, "thumb_gacha.ass")
    create_gacha_ass(ass_path, selected_title, palette)
    
    # [수정 기능 추가] ASS 파일 수정 기회 제공
    print(f"\n⚡ ASS 자막 파일이 생성되었습니다: {ass_path}")
    edit_yn = input("👉 렌더링 전, 글씨 위치나 크기를 수정하시겠습니까? (y/n, 엔터=No): ").strip().lower()
    if edit_yn == 'y':
        print(f"   ⏳ 파일을 수정하고 저장한 뒤 엔터를 누르세요...")
        print(f"   (팁: {ass_path} 파일을 열어서 '\\pos(x,y)' 좌표나 'Fontsize'를 조절하세요)")
        if sys.platform == "darwin": subprocess.run(["open", "-t", ass_path]) # 맥에서 텍스트 편집기 열기
        input("   [수정 완료 후 엔터 입력]")
    
    ts = int(time.time())%1000
    output_path = os.path.join(DOWNLOADS_DIR, f"gacha_thumb_{palette['name'].replace(' ', '')}_{ts}.jpg")
    ass_path_fixed = os.path.abspath(ass_path).replace('\\', '/').replace(':', '\\:')
    fonts_dir = CORE_DIR.replace('\\', '/').replace(':', '\\:')

    # Border color matching palette
    cmd = [
        FFMPEG_EXE, "-y",
        "-i", img_path,
        "-vf", f"drawbox=t=30:c=0x{palette['border']},subtitles=filename='{ass_path_fixed}':fontsdir='{fonts_dir}'",
        "-vframes", "1",
        output_path
    ]
    
    print(f"\n🎬 [{palette['name']}] 스타일로 렌더링 중...")
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✨ 가챠 성공! 완성: {output_path}")
        if sys.platform == "darwin": subprocess.run(["open", output_path])
    except Exception as e: print(f"❌ 실패: {e}")

if __name__ == "__main__":
    run_gacha_thumbnail()
