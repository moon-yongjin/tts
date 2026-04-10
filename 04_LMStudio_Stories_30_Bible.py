import urllib.request
import json
import time

# [설정]
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "qwen/qwen2.5-vl-7b"
OUTPUT_FILE = "/Users/a12/projects/tts/쇼츠_사연_30선_바이블.md"

def generate_batch_bible(start_idx, count=10):
    """지침 가이드를 엄수하여 숏폼 서사 명세 생성"""
    prompt = f"""당신은 제공된 '쇼츠 감성 서사 제작 바이블' 수칙을 100% 준수하는 전문 피디(PD)입니다.
수칙에 정의된 **8가지 서사 공식 중 몇 가지를 로테이션 적용**하여, **{start_idx}번부터 {start_idx + count - 1}번까지 총 {count}개**의 정밀 사연 기획안을 작성해주세요.

각 기획안은 반드시 아래 표준 규격을 한 치의 오차도 없이 지켜야 합니다:

### [번호]. [제목]
*   **공식**: 공식 [번호] [공식이름] (예: 공식1 오해 / 공식2 버팀 등)
*   **타겟**: 시니어 / 2030 (둘 중 하나 선택)
*   **오프닝 훅**: `[장소 또는 상황]` + `[예상 밖의 행동이나 결과]` ➡ `[그리고 인생이 바뀌었다 등 결과]`
*   **줄거리 (5단계 뼈대 적용)**:
    -   **[선행]**: (작고 즉흥적인 행동)
    -   **[손해]**: (주인공에게 따르는 작거나 큰 불이익)
    -   **[반전]**: (뜻밖의 방식으로 연결되는 교차점)
    -   **[여운]**: (설명이나 교훈 배제한 감정선 한 줄 마무리)

[안내 및 금지사항]:
1. 감정을 "슬펐다", "감동이다" 등 형용사로 직접 설명하지 마세요.
2. 교훈("착하게 살자")을 말하지 마세요.
3. 선행의 스케일이 너무 크면 안 됩니다. 담백하게 작성하세요.
4. 타겟에 맞춘 문장 호흡(2030은 짧게 끊기, 시니어는 부드럽게 잇기)을 줄거리에 녹여주세요.

지금 바로 {count}개를 생성하세요. 서론이나 잡담은 출력하지 마세요."""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a visual story planner who strictly structures output with Markdown formats."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8
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
        print(f"  ❌ LM Studio 가이드 호출 오류: {e}")
    return ""

if __name__ == "__main__":
    print(f"🎬 [LM Studio - {MODEL_NAME}] 기반 가이드라인 30선 제작을 시작합니다.")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("# 📜 쇼츠 감성 서사 공식 30선 (가이드 바이블 적용)\n\n")
        f.write("사용자님의 ‘서사 제작 로직’을 100% 대입하여 오프닝 훅, 5단계 뼈대, 8대 공식으로 기획한 리스트입니다.\n\n---\n\n")

    # 10개씩 3번 반복 = 30개
    for i in range(3):
        start_id = (i * 10) + 1
        print(f"🚀 [{i+1}/3] {start_id}번~{start_id+9}번 생성 중...")
        
        batch_text = generate_batch_bible(start_id, count=10)
        
        if batch_text.strip():
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(batch_text)
                f.write("\n\n---\n\n")
            print(f"  ✅ [{i+1}/3] 저장 완료!")
            time.sleep(1)
        else:
            print(f"  ❌ [{i+1}/3] 생성 실패.")

    print(f"\n✨ [생성 완료] 가이드 30선 배송 완료!")
    print(f"📍 문서 위치: {OUTPUT_FILE}")
