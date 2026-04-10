import cv2
import json
import subprocess
from google import genai
from google.genai import types

def get_timestamps_from_visual(video_path):
    """영상 좌상단 제목 영역 변화 감지"""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print("❌ 영상을 열 수 없습니다.")
        return []
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    timestamps = [("00:00:00", "영상 시작")]
    last_frame_crop = None
    
    print("📸 영상 시각 분석 중 (제목 변화 감지)...")
    # 30초 단위로 체크하여 효율성 확보
    step = int(fps * 30)
    for frame_idx in range(0, total_frames, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret: break
        
        # 좌상단 제목 영역 크롭 (예시 좌표: y 50~150, x 50~600)
        # 실제 로직에서는 영상 해상도에 맞춰 조정될 수 있음
        crop = frame[50:150, 50:600]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        
        if last_frame_crop is not None:
            score = cv2.absdiff(gray, last_frame_crop).mean()
            if score > 15: # 변화 임계값 (상황에 따라 조정 가능)
                seconds = frame_idx // fps
                ts = f"{int(seconds//3600):02d}:{int((seconds%3600)//60):02d}:{int(seconds%60):02d}"
                timestamps.append((ts, f"제목 변화 감지 ({ts})"))
        
        last_frame_crop = gray
        
    cap.release()
    return timestamps

def refine_timestamps_with_gemini(api_key, transcript_sample, visual_ts):
    """시각 데이터와 자막 일부를 결합하여 Gemini로 정밀 목차 정제"""
    if not api_key: 
        print("⚠️ Gemini Key가 없어 시각 데이터만 사용합니다.")
        return visual_ts
        
    print("🧠 Gemini가 목차를 정밀하게 정제 중입니다...")
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
다음은 유튜브 영상의 시각적 제목 변화 시점과 자막 내용입니다.
이를 종합하여 '사연별'로 큼직하게 5~10개 내외의 목차를 정제해 주세요.

**시각 감지 시점:**
{json.dumps(visual_ts, ensure_ascii=False)}

**출력 형식 (JSON 배열):**
[ 
  {{"time": "00:00:00", "title": "사연 제목1"}},
  {{"time": "00:15:30", "title": "사연 제목2"}}
]

**자막 컨텍스트 요약 (일부):**
{transcript_sample}
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text.strip())
        return [(item['time'], item['title']) for item in data]
    except Exception as e:
        print(f"❌ Gemini 정제 실패: {e}")
        return visual_ts
