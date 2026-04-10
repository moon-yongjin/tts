import os
import sys
import threading
import time
from datetime import datetime
from google import genai
from google.oauth2 import service_account
from google.genai import types

# [맥 터미널 한글 깨짐 방지]
if sys.platform == "darwin":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')

# --- [초기 설정] ---
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "쇼츠_대본_완성")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# API 키 및 서비스 계정 설정 (기존 tts/core_v2 폴더 내 키 재사용)
CREDENTIALS_PATH = "/Users/a12/projects/tts/core_v2/service_account.json"

try:
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    client = genai.Client(
        vertexai=True, 
        project="ttss-483505", 
        location="us-central1", 
        credentials=credentials
    )
except Exception as e:
    print(f"❌ Gemini API 설정 오류 (service_account.json 확인 필요): {e}")
    sys.exit(1)

# --- [로딩 애니메이션] ---
class Loader:
    def __init__(self, desc="처리 중..."):
        self.desc = desc
        self.done = False
        self.t = threading.Thread(target=self.animate)

    def animate(self):
        for c in ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']:
            if self.done: break
            sys.stdout.write(f'\r{c} {self.desc}')
            sys.stdout.flush()
            time.sleep(0.1)

    def start(self): self.t.start()
    def stop(self):
        self.done = True
        self.t.join()
        sys.stdout.write('\r' + ' ' * (len(self.desc) + 2) + '\r')
        sys.stdout.flush()

# --- [메인 로직] ---
def generate_blind_story(fact_text):
    prompt = f"""
    당신은 100만 유튜버의 쇼츠(Shorts) 대본 작가입니다.
    다음 제공되는 '진짜 팩트(사건)'를 바탕으로, 시청자가 끝까지 볼 수밖에 없는 "블라인드 스토리텔링" 형식의 유튜브 쇼츠 대본을 작성해주세요.

    [작성 규칙]
    1. 후킹 (0~3초): 가장 충격적인 내용으로 시청자의 시선을 끕니다. (예: "친구를 3시간 때려놓고도 당당히 방송에 나온 연예인이 있다?")
    2. 전개 (3~40초): 사람의 실명을 절대 노출하지 말고, 익명(B양, 걸그룹 출신 C양 등)을 사용하여 악행, 논란, 비화 등을 몰아치듯 매우 빠르고 자극적인 톤으로 설명하세요.
    3. AI 프롬프트 지시어 삽입: 대본 중간중간 화면에 띄울 AI 이미지 프롬프트를 괄호 안에 영문으로 넣어주세요. (예: [Image prompt: "A gloomy high school hallway, dark cinematic lighting, ultra realistic"])
    4. 반전 및 실명 공개 (40~50초): 영상 끝부분에 가서야 그 끔찍한/충격적인 사건의 주인공이 누구인지 실명을 벼락같이 공개하세요.
    5. 마지막 스크랩 안내 (50~60초): 실명 공개 후, "(인물이름)의 결정적 증거 사진입니다!" 라는 멘트와 함께, [여기에 실제 언론 스크랩 사진/영상 삽입] 이라는 지시어를 꼭 넣어주세요.
    6. 대본 형식으로 인트로/아웃트로 구분 없이 내레이션이 바로 읽을 수 있는 구어체로 작성해주세요.

    [제공된 팩트/사건 (나무위키 또는 기사 내용)]:
    {fact_text}
    """

    loader = Loader("Gemini 2.0이 쇼츠 대본을 미친 듯이 뽑아내고 있습니다...")
    loader.start()
    
    try:
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001",
            contents=prompt
        )
        loader.stop()
        return response.text.strip()
    except Exception as e:
        loader.stop()
        print(f"❌ AI 생성 실패: {e}")
        return None

# --- [데이터 분석: 실시간 유튜브 핫이슈 추천] ---
def get_recommendations():
    print("🔍 유튜브에서 실시간 핫이슈를 검색 중입니다...")
    try:
        # 연예계 핫이슈, 충격 사건 관련 검색어로 상위 검색 결과 10개 추출
        search_query = "연예계 핫이슈 충격 사건 사고"
        ydl_opts = {
            'extract_flat': True,
            'playlistend': 10,
            'quiet': True,
        }
        
        titles = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{search_query}", download=False)
            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        titles.append(f"- {entry.get('title')} (https://www.youtube.com/watch?v={entry.get('id')})")
        
        if not titles:
            return None

        # 검색된 제목들을 Gemini에게 전달하여 최적의 3가지 선정
        prompt = f"""
        다음은 현재 유튜브에서 검색된 최근 연예계 관련 이슈 제목들입니다.
        이 중에서 '이름을 숨겼다가 마지막에 터뜨리는' 블라인드 쇼츠로 만들었을 때 가장 조회수가 잘 나올 것 같은 파격적인 주제 3가지를 엄선해주세요.

        [검색된 리스트]:
        {"\n".join(titles)}

        [출력 형식]:
        1. (인물/사건명): (왜 이 주제가 흥미로운지 한 줄 요약) | [URL: 유튜브링크]
        2. (인물/사건명): (왜 이 주제가 흥미로운지 한 줄 요약) | [URL: 유튜브링크]
        3. (인물/사건명): (왜 이 주제가 흥미로운지 한 줄 요약) | [URL: 유튜브링크]
        """
        
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"⚠️ 추천 검색 중 오류: {e}")
        return None

def download_and_transcribe(url):
    """추천받은 영상의 내용을 기반으로 팩트 추출"""
    loader = Loader("해당 영상의 대본에서 팩트를 추출하고 있습니다...")
    loader.start()
    
    try:
        # 1. 임시 오디오 다운로드
        audio_path = "temp_recommend.m4a"
        ydl_opts = {
            'format': 'm4a/bestaudio/best',
            'outtmpl': audio_path,
            'quiet': True,
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'm4a'}]
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # 2. Gemini로 전사 (Transcript 추출)
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
            
        trans_prompt = "이 영상의 내용을 바탕으로 어떤 사건인지 팩트 위주로 요약해주세요."
        response = client.models.generate_content(
            model="publishers/google/models/gemini-2.0-flash-001",
            contents=[trans_prompt, types.Part.from_bytes(data=audio_bytes, mime_type="audio/mp4")]
        )
        
        loader.stop()
        if os.path.exists(audio_path): os.remove(audio_path)
        return response.text.strip()
    except Exception as e:
        loader.stop()
        print(f"❌ 팩트 추출 실패: {e}")
        return None

def main():
    print("==================================================")
    print("🎬 [리얼타임 블라인드 쇼츠 생성기 v2.0] 가동")
    print("==================================================")
    
    # 실시간 추천 가져오기
    recc_text = get_recommendations()
    
    if recc_text:
        print("\n🔥 [오늘의 실시간 유튜브 핫이슈 추천 3가지]")
        print(recc_text)
        print("--------------------------------------------------")
        print("👉 위 번호(1~3)를 입력하면 해당 영상을 분석하여 대본을 씁니다.")
        print("👉 혹은 직접 팩트(나무위키 등)를 아래에 붙여넣기 하세요.")
    else:
        print("👉 나무위키나 기사에서 복사한 팩트(진실)를 아래에 붙여넣기 하세요.")
    
    print("👉 입력을 마치려면 새로운 줄에서 '끝' 또는 '엔터키 두번(빈 줄)'을 입력하세요.")
    print("--------------------------------------------------\n")

    lines = []
    while True:
        try:
            line = input()
            if line.strip().lower() in ['끝', 'exit', 'quit']: break
            if line == "" and (len(lines) > 0 and lines[-1] == ""): break
            lines.append(line)
        except EOFError: break
    
    input_text = "\n".join(lines).strip()

    if not input_text:
        print("❌ 입력된 내용이 없습니다. 프로그램 종료.")
        sys.exit()

    # 입력이 숫자(1, 2, 3)인 경우
    if input_text in ["1", "2", "3"] and recc_text:
        # URL 추출 로직
        try:
            target_line = [l for l in recc_text.split("\n") if l.startswith(input_text)][0]
            url = target_line.split("[URL: ")[1].split("]")[0]
            print(f"\n🚀 선택하신 이슈({url})를 실시간 분석합니다...")
            fact_text = download_and_transcribe(url)
            if not fact_text:
                print("❌ 영상 분석에 실패했습니다.")
                sys.exit()
        except:
            print("❌ 번호 인식 오류. 직접 입력 모드로 전환합니다.")
            fact_text = input_text
    else:
        fact_text = input_text

    print("\n--------------------------------------------------")
    print("🚀 스토리를 쫀득하게 각색하고 있습니다! (약 5~10초 소요)")
    
    script_result = generate_blind_story(fact_text)
    
    if script_result:
        timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
        filename = f"블라인드_쇼츠_대본_{timestamp}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, "w", encoding='utf-8') as f:
            f.write("# [생성된 블라인드 쇼츠 대본]\n\n")
            f.write(script_result)
            f.write("\n\n---\n[입력/선택 데이터]\n")
            f.write(fact_text[:1000])
        
        print("\n\n==================================================")
        print(script_result)
        print("==================================================")
        print(f"🎉 완벽하게 각색되었습니다!")
        print(f"💾 대본 저장 위치: {filepath}")
        print("==================================================")

if __name__ == "__main__":
    main()
