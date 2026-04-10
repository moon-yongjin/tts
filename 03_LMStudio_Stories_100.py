import urllib.request
import json
import time
import os

# [설정]
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "qwen/qwen2.5-vl-7b"
OUTPUT_FILE = "/Users/a12/projects/tts/시니어_사연_100선.md"

def generate_batch_lmstudio(start_idx, count=10):
    """LM Studio API를 호출하여 배치 단위로 사연 생성"""
    prompt = f"""당신은 감동적이고 극적인 한국 시니어(50대~70대) 사연 전문 작가입니다.
이번 차례에는 **{start_idx}번부터 {start_idx + count - 1}번까지 총 {count}개**의 서로 다른 사연 아이디어를 생성해주세요.

각 사연은 반드시 아래 형식을 정확히 지켜야 합니다:
### [번호]. [제목]
* 주제: [사연의 핵심 주제 한 줄]
* 줄거리:
  - [줄거리 1번째 줄]
  - [줄거리 2번째 줄]
  - [줄거리 3번째 줄]

[안내]:
1. 성공/역전, 배신/복수, 황혼 로맨스, 가족 헌신/화해, 조용한 치유 등의 다양한 테마를 섞어주세요.
2. 앞서 나온 플롯과 절대 겹치지 않게 개성 있는 요소를 넣어주세요.
3. 마크다운(`*`, `-`) 서식을 반드시 지켜주세요.

지금 바로 {count}개의 사연을 생성합니다. 형식 외에 잡담이나 서론은 출력하지 마세요."""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a helpful story writer assistant who strictly follows formatting constraints."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(LM_STUDIO_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=180) as response:
            res_body = response.read().decode("utf-8")
            data = json.loads(res_body)
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"  ❌ LM Studio 호출 오류: {e}")
    return ""

if __name__ == "__main__":
    print(f"👵 [LM Studio - {MODEL_NAME}] 기반 '시니어 사연 베스트 100선' 생성을 시작합니다.")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# 👵 시니어 사연 베스트 100선 (주제 및 3줄 요약)\n\n")
        f.write("로컬 AI (`" + MODEL_NAME + "`)를 활용해 연쇄 반복 가동하여 생성된 100가지 시나리오 피칭 리스트입니다.\n\n---\n\n")

    # 10개씩 10번 반복 = 100개
    for i in range(10):
        start_id = (i * 10) + 1
        print(f"🚀 [{i+1}/10] {start_id}번~{start_id+9}번 생성 중...")
        
        batch_text = generate_batch_lmstudio(start_id, count=10)
        
        if batch_text.strip():
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(batch_text)
                f.write("\n\n---\n\n")
            print(f"  ✅ [{i+1}/10] 완료 및 저장!")
            time.sleep(1) # 부하 조절
        else:
            print(f"  ❌ [{i+1}/10] 생성 실패, 다시 시도합니다.")

    print(f"\n✨ [생성 완료] 100선 리스트업 끝!")
    print(f"📍 문서 위치: {OUTPUT_FILE}")
