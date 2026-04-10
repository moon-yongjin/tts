import json
from google import genai
from google.genai import types
import os
import sys
import time
import random
from pathlib import Path
import subprocess

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
DOWNLOADS_DIR = Path.home() / "Downloads"

# [틱톡 숏폼 소재 리스트 - 완전 랜덤용]
HERO_IDENTITIES = [
    "세계적인 슈퍼요트 엔진 설계자이자 그룹 의장", "무형문화재 도예 장인", "미슐랭 3스타 셰프들의 스승", "국가비밀정보국 은퇴 요원", 
    "글로벌 패션 그룹의 실소유주", "전설적인 투자 분석가", "대한민국 최고의 한복 명장", "유명 아이돌들의 보컬 트레이너",
    "대기업 회장의 숨겨진 멘토", "천재적인 해킹 실력을 가진 화이트 해커", "전설의 강력계 형사", "국보급 문화재 복원 전문가"
]
VILLAIN_JOBS = [
    "마리나 클럽 총괄 매니저", "명품 그릇 백화점 지점장", "프랜차이즈 레스토랑 점장", "부패한 지역 건설사 사장", 
    "갑질하는 명품 브랜드 매니저", "사기꾼 투자 자문가", "전통 시장을 무시하는 건물주 아들", "오만한 엔터테인먼트 실장",
    "허세 부리는 스타트업 대표", "개인정보를 파는 악덕 센터장", "뒷돈 받는 비리 경찰", "문화재 밀반출을 시도하는 골동품상"
]
LOCATIONS = [
    "강남 프라이빗 마리나 클럽", "청담동 명품 리빙관", "오픈 키친 레스토랑", "재개발 예정 지역 사무소", 
    "압구정 명품 플래그십 스토어", "여의도 증권가 VIP 라운지", "북촌 한옥 마을 공방", "청담동 연예 기획사 연습실",
    "판교 테크노밸리 공유 오피스", "구로 디지털 단지 서버실", "종로 경찰서 강력반 사무실", "인사동 고미술 거리"
]
ITEMS = [
    "낡은 엔진 렌치와 수첩", "투박한 흙이 묻은 빚은 도자기", "오래된 식칼 세트", "낡은 군번줄과 훈장", 
    "직접 바느질한 자투리 천 조각", "너덜너덜한 수기 가계부", "색바랜 바늘쌈지", "손때 묻은 악보",
    "오래된 만년필", "구형 노트북과 USB", "낡은 수갑", "깨진 기와 조각"
]
HELPER_ROLES = [
    "신입 사원", "알바생", "막내 작가", "인턴 비서", 
    "수습 기자", "편의점 알바", "청소 반장님", "경비 아저씨",
    "배달 기사", "지나가던 학생", "동네 주민", "양심적인 내부 고발자"
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

def generate_tiktok_script(hero_identity, villain_job, location, item, helper_role="신입 사원"):
    """
    데이터 기반 권선징악 숏폼 대본 생성 함수
    """
    
    # 프롬프트 엔지니어링: 분석된 17개 대본의 로직을 시스템에 주입
    target_model = 'gemini-2.0-flash'
    print(f"🤖 모델 로딩 중: {target_model}...")

    prompt = f"""
    당신은 숏폼 드라마 대본 전문 작가입니다. 
    아래 [변수]와 [제작 지침]을 완벽히 준수하여 1,500자 분량의 대본을 작성하세요.

    [변수]
    - 주인공(숨겨진 정체): {hero_identity} (처음엔 허름한 행색으로 위장)
    - 빌런(악역): {villain_job} (오만하고 능력 없는 인물)
    - 장소: {location}
    - 핵심 소재: {item} (주인공의 전문성을 보여주는 도구)
    - 조력자: {helper_role} (빌런에게 당하면서도 주인공을 돕는 인물)

    [제작 지침 - 엄수할 것]
    1. **분량**: 공백 포함 약 1,500자로 길고 디테일하게 작성할 것.
    2. **문체**: 현장감 넘치는 묘사와 대사를 적절히 배합.
    3. **기호 규칙**: 
       - 말줄임표(...)는 절대 사용하지 말고, 쉼표(,)로 대체할 것.
    4. **플롯 구조 (5단계 공식)**:
       - 1단계(무시): 허름한 주인공이 {location}에 등장, {item}을 확인하려 함.
       - 2단계(위기): {villain_job}이 등장하여 모욕을 주고 물건을 파손함.
       - 3단계(조력): {helper_role}이 나타나 주인공을 돕다가 해고 위협을 당함.
       - 4단계(반전): 외부 세력(본사 임원/경찰 등)이 등장하여 주인공의 정체({hero_identity})가 밝혀짐. 
       - 5단계(응징): {villain_job}은 '면허 박탈'이나 '업계 영구 퇴출' 등 현실적이고 처참한 최후를 맞음. {helper_role}은 파격 승진.

    [출력 예시]
    (서론 잡설 없이 바로 대본 본문만 출력하세요)
    """

    try:
        print("✍️  사이다 숏폼 대본 집필 중... (도파민 주의)")
        response = client.models.generate_content(
            model=target_model,
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
            return f"에러 발생: {str(e2)}"

# ---------------------------------------------------------
# [실행]
# ---------------------------------------------------------
if __name__ == "__main__":
    print("="*60)
    print("⚡ [99-9-3] Gemini 틱톡/숏폼 대본 자동 생성기")
    print("="*60)

    if len(sys.argv) > 5:
        # 인자가 있으면 1편만 실행
        hero = sys.argv[1]
        villain = sys.argv[2]
        loc = sys.argv[3]
        item = sys.argv[4]
        helper = sys.argv[5]
        
        script = generate_tiktok_script(hero, villain, loc, item, helper)
        print(script)
        
    else:
        # 대화형 배치 모드
        try:
            count_input = input("🔢 생성할 대본 편수를 입력하세요 (기본 1편): ").strip()
            count = int(count_input) if count_input.isdigit() else 1
        except:
            count = 1

        print(f"\n🚀 총 {count}편의 사이다 숏폼 드라마를 생성합니다...")

        # 저장 폴더 생성
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_dir = DOWNLOADS_DIR / f"틱톡대본_모음_{timestamp}"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        for i in range(count):
            # [완전 랜덤 믹스]
            hero = random.choice(HERO_IDENTITIES)
            villain = random.choice(VILLAIN_JOBS)
            loc = random.choice(LOCATIONS)
            item = random.choice(ITEMS)
            helper = random.choice(HELPER_ROLES)

            print(f"\n[{i+1}/{count}] 🎬 설정: {hero} vs {villain} (@{loc})")
            
            script = generate_tiktok_script(hero, villain, loc, item, helper)
            
            # 파일 저장
            safe_title = f"{hero.split(' ')[0]}_{villain.split(' ')[0]}_{loc.split(' ')[0]}"
            safe_title = safe_title.replace("/", "").replace(":", "")
            filename = f"{i+1:02d}_{safe_title}.txt"
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
