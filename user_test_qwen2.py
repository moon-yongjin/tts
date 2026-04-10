import torch
import os
import sys
from transformers import AutoModelForCausalLM, AutoTokenizer

# 1. 모델 로딩 (Flash-Attention 절대 안 씀)
model_id = "Qwen/Qwen2-7B-Instruct" 
print(f"📡 모델 로딩 시작: {model_id} (bfloat16 + cuda)...")
try:
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        torch_dtype=torch.bfloat16, 
        device_map="cuda" # CPU가 아니라 확실하게 GPU로 보냄
    )
except Exception as e:
    print(f"❌ 모델 로딩 실패: {e}")
    sys.exit(1)

# 2. 대본 로드 및 150토막 내기
script_path = "/workspace/대본.txt"
if os.path.exists(script_path):
    with open(script_path, "r", encoding="utf-8") as f:
        full_script = f.read().strip()
else:
    full_script = "부대표님의 1,500자 대본 예시입니다. 실제로 파일이 없어서 이 텍스트로 대체합니다."

chunks = [full_script[i:i+150] for i in range(0, len(full_script), 150)]

print(f"🚀 총 {len(chunks)}개 파트로 나눠서 광속 생성 시작!")

output_dir = "/workspace/output"
os.makedirs(output_dir, exist_ok=True)

for i, text in enumerate(chunks):
    print(f"🎙️ [{i+1}/{len(chunks)}] 처리 중: {text[:20]}...")
    try:
        inputs = tokenizer(text, return_tensors="pt").to("cuda")
        with torch.no_grad():
            # 생성 로직
            output = model.generate(**inputs, max_new_tokens=200) 
            response = tokenizer.decode(output[0], skip_special_tokens=True)
            
        # 결과 저장
        output_file = f"{output_dir}/part_{i+1:03d}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response)
        print(f"✅ [{i+1}/{len(chunks)}] 완료! -> {output_file}")
    except Exception as e:
        print(f"❌ [{i+1}/{len(chunks)}] 생성 중 오류: {e}")

print(f"🎉 모든 작업이 완료되었습니다! {output_dir}/ 확인하세요.")
