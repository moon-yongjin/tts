import os
import sys
import re
import json
from pathlib import Path
from llm_router import ask_llm

# [설정]
PROJ_ROOT = Path("/Users/a12/projects/tts/Ollama_Studio")

def generate_visual_prompts(file_path):
    if not os.path.exists(file_path):
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return

    print(f"🎨 [Visual Architect] 허깅페이스 Llama-3 PRO 엔진이 비주얼 연출을 기획 중입니다...")
    
    with open(file_path, "r", encoding="utf-8") as f:
        script_content = f.read()

    # 라우터 호출 (비주얼 디렉터 역할)
    visual_plan = ask_llm(script_content, role="visual_director")
    
    if visual_plan and "Error" not in visual_plan:
        output_file = Path(file_path).parent / "visual_concept_report.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# 🎬 Automated Visual Concept Report\n\n")
            f.write(f"### [Input Script Source]: {Path(file_path).name}\n\n")
            f.write(visual_plan)
        
        # [추가] 기계가 읽을 수 있는 프롬프트 데이터(JSON) 추출 및 저장
        json_output = Path(file_path).parent / "scene_prompts.json"
        prompts = []
        
        # 'READY-TO-USE' 섹션 유연하게 찾기
        try:
            target_section = "READY-TO-USE"
            if target_section in visual_plan:
                parts = visual_plan.split(target_section)[-1].strip().split("\n")
                for line in parts:
                    clean_line = line.strip()
                    # "1. Prompt text" 또는 "1) Prompt text" 또는 "**Scene 1** Prompt" 등 다양하게 대응
                    match = re.search(r'^\d+[\.\)]\s*(.*)', clean_line) # 매칭이 아닌 검색으로 유연하게
                    if match:
                        prompts.append(match.group(1).strip())
                    elif clean_line and not clean_line.startswith("-") and not clean_line.startswith("#") and len(clean_line) > 20:
                        # 숫자 리스트는 아니지만 내용이 길면 프롬프트로 간주 (fallback)
                        prompts.append(clean_line)
            
            if prompts:
                with open(json_output, "w", encoding="utf-8") as f:
                    json.dump(prompts, f, ensure_ascii=False, indent=2)
                print(f"📦 [Visual Architect] 자동화용 데이터 저장 완료: {json_output}")
        except Exception as e:
            print(f"⚠️ [Visual Architect] 프롬프트 추출 중 경고: {e}")

        print(f"✅ [Visual Architect] 비주얼 연출 설계도가 생성되었습니다: {output_file}")
        return visual_plan
    else:
        print(f"❌ [Visual Architect] 기획 실패: {visual_plan}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        generate_visual_prompts(sys.argv[1])
    else:
        print("사용법: python visual_concept_agent.py [대본파일.txt]")
