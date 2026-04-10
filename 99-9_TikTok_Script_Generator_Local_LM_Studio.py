import sys
import os
import urllib.request
import json
import random
import time
import subprocess
from pathlib import Path

# ⚠️ LM Studio 서버가 기동되어 있어야 작동합니다 (Port: 1234)
API_URL = "http://localhost:1234/v1/chat/completions"
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
    text = text.replace("...", ".")
    text = text.replace("…", ".")
    text = text.replace('",', '"')
    text = text.replace('".', '"')
    text = text.replace("’", "'")
    text = text.replace("”", '"')
    text = text.replace("“", '"')
    return text

def generate_tiktok_script(hero_identity, villain_job, location, item, helper_role="신입 사원"):
    print(f"🤖 로컬 모델 활용 중: LM Studio / OpenAI Compatible...")
    prompt = f"""당신은 사이다 숏폼 드라마 대본 전문 작가입니다. 아래 [변수]와 [제작 지침]을 완벽히 준수하여 대본을 작성하세요.

[변수]
- 주인공(숨겨진 정체): {hero_identity} (처음엔 허름한 행색으로 위장)
- 빌런(악역): {villain_job} (오만하고 능력 없는 인물)
- 장소: {location}
- 핵심 소재: {item}
- 조력자: {helper_role}

[제작 지침]
1. 분량: 공백 포함 최소 1,000자 이상 디테일하게 작성.
2. 플롯 (5단계): 무시 ➡️ 위기 ➡️ 조력 ➡️ 반전 ➡️ 응징.
3. 기호 규칙: 따옴표 뒤 쉼표나 마침표 금지. 말줄임표(...) 금지.
"""

    payload = {
        "model": "qwen/qwen2.5-vl-7b", # LM Studio 로드된 모델 식별자 지정 (오류 대응)
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    
    req = urllib.request.Request(
        API_URL, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            response = json.loads(res.read().decode('utf-8'))
            return clean_text_for_tts(response['choices'][0]['message']['content'])
    except Exception as e:
        return f"로컬 서버 호출 에러: {e}"

if __name__ == "__main__":
    print("="*60)
    print("⚡ [99-9-Local] Local LM Studio 틱톡/숏폼 대본 자동 생성기")
    print("="*60)

    try:
        count_input = input("🔢 생성할 대본 편수를 입력하세요 (기본 1편): ").strip()
        count = int(count_input) if count_input.isdigit() else 1
    except:
        count = 1

    print(f"\n🚀 총 {count}편의 사이다 숏폼 드라마를 생성합니다...")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    save_dir = DOWNLOADS_DIR / f"로컬대본_모음_{timestamp}"
    save_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(count):
        hero = random.choice(HERO_IDENTITIES)
        villain = random.choice(VILLAIN_JOBS)
        loc = random.choice(LOCATIONS)
        item = random.choice(ITEMS)
        helper = random.choice(HELPER_ROLES)

        print(f"\n[{i+1}/{count}] 🎬 설정: {hero} vs {villain} (@{loc})")
        
        script = generate_tiktok_script(hero, villain, loc, item, helper)
        
        safe_title = f"{hero.split(' ')[0]}_{villain.split(' ')[0]}_{loc.split(' ')[0]}"
        filename = f"{i+1:02d}_{safe_title}.txt"
        save_path = save_dir / filename
        
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(script)
        
        if i == 0:
            # 1-3-92 스크립트가 로드할 수 있도록 대본.txt 갱신
            with open("대본.txt", "w", encoding="utf-8") as f:
                f.write(script)

        print(f"   ✅ 저장 완료: {save_path.name}")
        time.sleep(1)

    print("\n" + "="*60)
    print(f"🎉 모든 생성이 완료되었습니다!")
    print(f"📂 저장 폴더: {save_dir}")
    subprocess.run(["open", str(save_dir)])
