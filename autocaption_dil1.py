import os

DATASET_DIR = "/Users/a12/Downloads/LoRA_Datasets/DIL1"
TRIGGER_WORD = "c1_dil1" # 유니크한 트리거 단어
CORE_CAPTION = "beautiful Korean woman in her late 30s, sharp cold features, arrogant face, medium bob hair style, wearing a Dongtan-missy style sexy outfit with an extremely deep plunging neckline, revealing deep cleavage, extremely large breasts, very voluptuous and curvy body, healthy glamorous and full figure"

def auto_caption():
    if not os.path.exists(DATASET_DIR):
        print(f"❌ 폴더 없음: {DATASET_DIR}")
        return

    files = [f for f in os.listdir(DATASET_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    print(f"📝 {len(files)}장 캡셔닝 시작...")

    for f in files:
        base_name = os.path.splitext(f)[0]
        txt_path = os.path.join(DATASET_DIR, f"{base_name}.txt")
        
        # 파일명에서 배경이나 특징을 추측할 수 있는 로직이 있다면 추가 가능 (현재는 공통 앵커 위주)
        caption = f"{TRIGGER_WORD}, {CORE_CAPTION}"
        
        with open(txt_path, "w", encoding="utf-8") as tf:
            tf.write(caption)
            
    print(f"✅ 캡셔닝 완료!")

if __name__ == "__main__":
    auto_caption()
