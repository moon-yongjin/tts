import os

BASE_DIR = "/Users/a12/Downloads/LoRA_Datasets"

CHARACTERS = [
    {
        "folder": "DIL1",
        "trigger": "c1_dil1",
        "caption": "beautiful Korean woman in her late 30s, sharp cold features, arrogant face, medium bob hair style, wearing a Dongtan-missy style sexy outfit with an extremely deep plunging neckline, revealing deep cleavage, extremely large breasts, very voluptuous and curvy body, healthy glamorous and full figure"
    },
    {
        "folder": "DIL2",
        "trigger": "c2_dil2",
        "caption": "very beautiful young Korean woman in her late 20s, extremely pure and kind angelic face, innocent friendly expression, natural long hair, chubby and plump healthy body, soft and voluminous thick figure, very large breasts, curvy full figure, wearing a cozy and tight-fitting sexy casual outfit"
    },
    {
        "folder": "MIL",
        "trigger": "m1_mil",
        "caption": "beautiful Korean grandmother in her 60s, plain and modest natural grandmotherly face, salt and pepper hair in a simple natural style, humble and elegant appearance, wearing a modest and high-neck long-sleeve knit sweater, absolutely NO cleavage, NO skin exposure on chest, conservative clothing, but having an extremely voluminous and glamorous body, curvy full figure"
    }
]

def auto_caption_all():
    for char in CHARACTERS:
        target_dir = os.path.join(BASE_DIR, char['folder'])
        if not os.path.exists(target_dir):
            print(f"⚠️ 폴더 없음: {target_dir}")
            continue

        files = [f for f in os.listdir(target_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        print(f"📝 {char['folder']} ({len(files)}장) 캡셔닝 중...")

        for f in files:
            base_name = os.path.splitext(f)[0]
            txt_path = os.path.join(target_dir, f"{base_name}.txt")
            caption = f"{char['trigger']}, {char['caption']}"
            with open(txt_path, "w", encoding="utf-8") as tf:
                tf.write(caption)
    
    print(f"✅ 모든 캐릭터 데이터셋 캡셔닝 완료!")

if __name__ == "__main__":
    auto_caption_all()
