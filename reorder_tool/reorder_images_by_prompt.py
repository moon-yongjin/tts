import os
import shutil
import re
from difflib import SequenceMatcher

def fuzzy_ratio(a, b):
    return SequenceMatcher(None, a, b).ratio()

def clean_text(text):
    """지정한 텍스트에서 특수문자 및 불필요한 공백 제거"""
    text = re.sub(r'[^a-zA-Z0-9가-힣 ]', ' ', text)
    return ' '.join(text.split()).lower()

def reorder_images(prompt_file, image_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. 프롬프트 리스트 읽기
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_lines = [line.strip() for line in f.readlines() if line.strip()]

    # 프롬프트 데이터 파싱 (ID | 메모 | 프롬프트 형태 대응)
    parsed_prompts = []
    for line in prompt_lines:
        if '|' in line:
            parts = line.split('|')
            prompt_id = parts[0].strip() # '001', '01' 등
            actual_prompt = parts[-1].strip()
            parsed_prompts.append({'id': prompt_id, 'text': actual_prompt})
        else:
            parsed_prompts.append({'id': '?', 'text': line})

    # 2. 이미지 파일 리스트 확보
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]

    print(f"총 {len(parsed_prompts)}개의 프롬프트와 {len(image_files)}개의 이미지를 매칭합니다.")

    # 3. 모든 이미지에 대해 매칭 점수 계산
    # (image, prompt, score) 튜플 리스트 생성
    match_candidates = []
    
    print("이미지별 점수 계산 중...")
    for img_name in image_files:
        name_only = os.path.splitext(img_name)[0]
        stripped_name = re.sub(r'_\d{8,}.*', '', name_only) 
        stripped_name = re.sub(r'_\d+$', '', stripped_name)
        clean_img = clean_text(stripped_name)
        
        for idx, p_data in enumerate(parsed_prompts, 1):
            clean_p = clean_text(p_data['text'])
            score = fuzzy_ratio(clean_img[:60], clean_p[:60])
            if clean_img and (clean_img in clean_p or clean_p in clean_img):
                score += 1.2 # 강력 가중치 (텍스트 포함 시 우선)

            if score > 0.2: # 최소 임계값
                match_candidates.append((score, img_name, idx))

    # 4. 점수 높은 순으로 1:1 매칭 (Greedy)
    match_candidates.sort(key=lambda x: x[0], reverse=True)
    
    final_mapping = {} # {img_name: (prompt_idx, score)}
    used_images = set()
    used_prompts = set()
    
    for score, img_name, p_idx in match_candidates:
        if img_name not in used_images and p_idx not in used_prompts:
            final_mapping[img_name] = (p_idx, score)
            used_images.add(img_name)
            used_prompts.add(p_idx)

    # 5. 결과 정리
    matched_total = 0
    # 정렬을 위해 {idx: img_name} 사전을 만듭니다.
    results = {idx: name for name, (idx, s) in final_mapping.items()}
    
    for idx in range(1, len(parsed_prompts) + 1):
        if idx in results:
            img_name = results[idx]
            p_data = parsed_prompts[idx-1]
            p_id = p_data['id']
            
            src_path = os.path.join(image_dir, img_name)
            ext = os.path.splitext(img_name)[1]
            # 파일명: [라인번호]_[ID]_[원본]
            new_name = f"{idx:03d}_ID{p_id}_{img_name}"
            dst_path = os.path.join(output_dir, new_name)
            
            shutil.copy2(src_path, dst_path)
            matched_total += 1
            print(f"[{idx:03d}] {img_name} 매칭됨 (ID:{p_id})")

    # 매칭되지 않은 파일들은 'unmatched' 폴더로 (혹시 모르니)
    unmatched_dir = os.path.join(output_dir, "unmatched")
    for img_name in image_files:
        if img_name not in used_images:
            if not os.path.exists(unmatched_dir): os.makedirs(unmatched_dir)
            shutil.copy2(os.path.join(image_dir, img_name), os.path.join(unmatched_dir, img_name))

    print(f"\n✅ 완료: 총 {matched_total}개 이미지가 1:1 매칭되어 '{output_dir}'에 정리되었습니다.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("사용법: python reorder_images_by_prompt.py <프롬프트파일> <이미지폴더> <결과폴더>")
    else:
        reorder_images(sys.argv[1], sys.argv[2], sys.argv[3])
