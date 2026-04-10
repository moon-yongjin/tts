import json
import os
import sys
import datetime
from google import genai
from google.genai import types

# Path setup
BASE_DIR = "/Users/a12/projects/tts"
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "google_ai_images")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_google_image(prompt, model_id="imagen-4.0-generate-001", aspect_ratio="1:1"):
    config = load_config()
    api_key = config.get("Gemini_API_KEY")
    
    # Ensure model_id has 'models/' prefix if not present
    if not model_id.startswith("models/"):
        model_full_id = f"models/{model_id}"
    else:
        model_full_id = model_id
        
    client = genai.Client(api_key=api_key)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize prompt for filename
    sanitized_prompt = "".join([c if c.isalnum() else "_" for c in prompt[:50]])
    filename = f"{timestamp}_{sanitized_prompt}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)

    print(f"🚀 Generating image with model: {model_full_id}")
    print(f"📝 Prompt: {prompt}")

    try:
        # Try generate_images (Imagen path)
        response = client.models.generate_images(
            model=model_full_id,
            prompt=prompt,
            config={
                'number_of_images': 1,
                'aspect_ratio': aspect_ratio,
                'output_mime_type': 'image/png'
            }
        )
        
        if response.generated_images:
            image_data = response.generated_images[0].image_bytes
            with open(filepath, "wb") as f:
                f.write(image_data)
            print(f"✅ Success! Image saved to: {filepath}")
            return filepath
        else:
            print("⚠️ No images generated.")
            return None

    except Exception as e:
        print(f"❌ Error with {model_full_id}: {e}")
        # Try fallback to 2.0-flash-exp-image-generation if available
        if "imagen" in model_id.lower():
            print("🔄 Attempting fallback to gemini-2.0-flash-exp-image-generation...")
            return generate_google_image_fallback(prompt)
        return None

def generate_google_image_fallback(prompt):
    config = load_config()
    api_key = config.get("Gemini_API_KEY")
    client = genai.Client(api_key=api_key)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(OUTPUT_DIR, f"{timestamp}_fallback.png")

    try:
        # Some versions of Gemini can generate images via generate_images too
        response = client.models.generate_images(
            model="gemini-2.0-flash-exp-image-generation",
            prompt=prompt,
            config={'number_of_images': 1}
        )
        if response.generated_images:
            with open(filepath, "wb") as f:
                f.write(response.generated_images[0].image_bytes)
            print(f"✅ Fallback success! Image saved to: {filepath}")
            return filepath
        
        print("⚠️ Fallback didn't produce an image.")
        return None
    except Exception as e:
        print(f"❌ Fallback failed: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python prompt_to_image.py \"your prompt here\" [aspect_ratio]")
        sys.exit(1)
    
    user_prompt = sys.argv[1]
    user_aspect_ratio = sys.argv[2] if len(sys.argv) > 2 else "1:1"
    
    generate_google_image(user_prompt, aspect_ratio=user_aspect_ratio)
