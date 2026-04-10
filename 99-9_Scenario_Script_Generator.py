import json
from google import genai
from google.genai import types
import random
import time
import os
import sys
import subprocess
from pathlib import Path

# [설정]
CONFIG_PATH = "/Users/a12/projects/tts/config.json"

def load_gemini_key():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("Gemini_API_KEY")
    except:
        return None

GOOGLE_API_KEY = load_gemini_key()
if not GOOGLE_API_KEY:
    print("❌ API Key를 찾을 수 없습니다.")
    exit(1)

client = genai.Client(api_key=GOOGLE_API_KEY)
MODEL_NAME = 'gemini-2.0-flash'

DOWNLOADS_DIR = Path.home() / "Downloads"

# ---------------------------------------------------------
# [데이터베이스] 랜덤 요소 리스트 (완전 랜덤 믹스용)
# ---------------------------------------------------------
THEMES = ["의료", "항공", "호텔", "건설", "예술", "IT", "법조계", "교육", "스포츠", "방송"]
LOCATIONS = [
    "강남 VIP 전용 성형외과 로비", "국제공항 퍼스트 클래스 라운지", "6성급 호텔 스카이라운지 레스토랑", 
    "대기업 신사옥 건설 현장 사무소", "청담동 프라이빗 아트 갤러리", "판교 게임 회사 본사 로비",
    "대법원 앞 1인 시위 현장", "명문 사립 초등학교 교무실", "프로야구 구단주 전용 스카이박스", "생방송 뉴스 스튜디오"
]
HERO_IDENTITIES = [
    "전 세계 의료기기 특허권자이자 재단 이사장", "글로벌 항공 연맹 의장 겸 파일럿", "미슐랭 가이드 아시아 총괄 평가관", 
    "프리츠커상을 수상한 전설적인 건축가", "세계 3대 경매 회사 회장", "서버 아키텍처 원천 기술 보유자 (전설의 개발자)",
    "대법관 출신의 전설적인 인권 변호사", "노벨상 수상자 출신의 교육 재단 이사장", "메이저리그 명예의 전당 헌액자", "방송국 지분 51%를 소유한 대주주"
]
VILLAIN_JOBS = [
    "성형외과 상담 실장", "라운지 총괄 매니저", "레스토랑 지배인", "현장 소장", "갤러리 수석 큐레이터", "인사팀 채용 담당 임원",
    "법원 경비 대장", "교감 선생님", "구단 홍보 팀장", "메인 뉴스 앵커"
]
ITEMS = [
    "낡은 왕진 가방과 청진기", "기름 묻은 정비용 장갑과 로그북", "다 닳은 젓가락과 낡은 수첩", 
    "너덜너덜한 도면통과 줄자", "먼지 묻은 돋보기와 감정서", "액정 깨진 구형 노트북",
    "낡은 육법전서와 변호사 배지", "색바랜 칠판지우개와 분필", "흙 묻은 야구 글러브", "오래된 마이크와 대본"
]
HELPERS = [
    "신입 간호조무사", "공항 미화원", "접시 닦는 아르바이트생", "현장 안전 요원", "작품 운송 기사", "보안 요원",
    "법원 청소 아주머니", "기간제 교사", "볼보이 아르바이트생", "조명 막내 스태프"
]

def clean_text_for_tts(text):
    """TTS 발화시 중국어 발생 및 오류 방지를 위한 텍스트 정제"""
    text = text.replace("...", ".") # 말줄임표 제거
    text = text.replace("…", ".")   # 말줄임표 특수문자 제거
    text = text.replace('",', '"')  # 따옴표 뒤 쉼표 제거 (중국어 발생 원인 1위)
    text = text.replace('".', '"')  # 따옴표 뒤 마침표 제거
    text = text.replace("’", "'")   # 홑따옴표 정규화
    text = text.replace("”", '"')   # 쌍따옴표 정규화
    text = text.replace("“", '"')   # 쌍따옴표 정규화
    return text

def generate_random_script(theme, location, hero, villain, item, helper):
    """
    랜덤 요소를 조합하여 대본을 생성하는 함수
    """
    
    print(f"▶ [시스템] 랜덤 조합: {theme} 테마?")
    print(f"   - 장소: {location}")
    print(f"   - 정체: {hero}")
    
    print(f"🤖 모델 로딩 중: {MODEL_NAME}...")

    # 2. 프롬프트 작성 (데이터 분석 기반 로직 주입)
    prompt = f"""
    당신은 숏폼 드라마 시나리오 작가 'Grok'입니다.
    아래 [랜덤 설정]을 바탕으로, 시청자의 도파민을 자극하는 1,500자 분량의 대본을 작성하세요.

    [랜덤 설정]
    - (참고) 테마 느낌: {theme}
    - 배경 장소: {location}
    - 주인공(위장): 허름한 행색으로 등장하지만 사실은 '{hero}'
    - 빌런: 주인공을 무시하는 '{villain}' (권위적이고 오만함)
    - 핵심 아이템: 주인공의 전문성을 증명하는 '{item}'
    - 조력자: 주인공을 유일하게 돕는 '{helper}'

    [필수 작성 지침 - 엄격 준수]
    1. **문체**: 말줄임표(...)는 절대 사용하지 말고, 쉼표(,)로 대체하여 호흡을 빠르게 가져갈 것.
    3. **분량**: 공백 포함 약 1,500자 내외로 풍성하게 서술할 것.
    4. **플롯 (5단계)**:
       - 1. 무시: 주인공이 {item}을 들고 {location}에 등장하자 {villain}이 모욕하며 쫓아내려 함.
       - 2. 위기: {villain}이 주인공의 물건을 파손하거나 바닥에 던짐.
       - 3. 조력: {helper}가 나타나 주인공을 부축하고 대신 사과함. 빌런은 조력자까지 해고하려 함.
       - 4. 반전: 외부 세력(본사 임원, 경찰 등)이 등장해 주인공에게 90도로 인사함. 정체 발각.
       - 5. 참교육: 주인공은 '면허 박탈', '계약 해지', '업계 퇴출' 등 구체적이고 치명적인 처벌을 내림. 조력자는 파격 승진.
       - 쿠키: 사건이 끝난 줄 알았으나, 빌런의 추가 범죄(횡령, 밀수 등)가 드러나는 충격적인 2편 예고 멘트.

    [출력]
    서론이나 설명 없이 바로 대본 본문만 출력하세요.
    """

    try:
        print("✍️  대본지키미 Grok이 집필 중... (도파민 충전)")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        return clean_text_for_tts(response.text)
    except Exception as e:
        print(f"⚠️ 생성 실패 ({e}). gemini-1.5-pro로 재시도합니다.")
        try:
            response = client.models.generate_content(
                model='gemini-1.5-pro',
                contents=prompt
            )
            return clean_text_for_tts(response.text)
        except Exception as e2:
            return f"API 호출 중 에러 발생: {str(e2)}"

# ---------------------------------------------------------
# [실행]
# ---------------------------------------------------------
if __name__ == "__main__":
    print("="*60)
    print("🎬 [99-9-4] Gemini 시나리오(테마) 대본 자동 생성기")
    print("="*60)
    
    # 배치 모드 질문
    try:
        count_input = input("🔢 생성할 대본 편수를 입력하세요 (기본 1편): ").strip()
        count = int(count_input) if count_input.isdigit() else 1
    except:
        count = 1

    print(f"\n🚀 총 {count}편의 시나리오 대본을 생성합니다...")

    # 저장 폴더 생성
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    save_dir = DOWNLOADS_DIR / f"시나리오대본_모음_{timestamp}"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(count):
        # [완전 랜덤 믹스] 이번에는 고정된 시나리오 없이 마구잡이로 섞음
        theme = random.choice(THEMES)
        location = random.choice(LOCATIONS)
        hero = random.choice(HERO_IDENTITIES)
        villain = random.choice(VILLAIN_JOBS)
        item = random.choice(ITEMS)
        helper = random.choice(HELPERS)

        print(f"\n[{i+1}/{count}]")
        
        script = generate_random_script(theme, location, hero, villain, item, helper)
        
        # 파일 저장
        safe_theme = theme
        safe_loc = location.split(" ")[0]
        filename = f"{i+1:02d}_{safe_theme}_{safe_loc}.txt"
        save_path = save_dir / filename
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(script)
        
        # 첫 번째 대본은 기본 대본.txt로도 저장
        if i == 0:
            with open("대본.txt", "w", encoding="utf-8") as f:
                f.write(script)

        print(f"   ✅ 저장 완료: {save_path.name}")
        time.sleep(2) # API 부하 방지

    print("\n" + "="*60)
    print(f"🎉 모든 생성이 완료되었습니다!")
    print(f"📂 저장 폴더: {save_dir}")
    subprocess.run(["open", str(save_dir)])
