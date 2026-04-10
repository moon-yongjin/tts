import os
import json
import requests
import re
from pathlib import Path

# 설정
PROJ_ROOT = Path("/Users/a12/projects/tts")
CONFIG_PATH = PROJ_ROOT / "config.json"

# Config 로드
config = {}
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

# API Keys
HF_TOKEN = config.get("HuggingFace_API_KEY", "")
GEMINI_KEYS = [v for k, v in config.items() if "Gemini_API_KEY" in k and v]
GEMINI_KEY = GEMINI_KEYS[0] if GEMINI_KEYS else ""

OLLAMA_API = "http://localhost:11434/api/generate"

def ask_huggingface(prompt, model="meta-llama/Meta-Llama-3-70B-Instruct"):
    if not HF_TOKEN:
        raise ValueError("HuggingFace API Key가 config.json에 없습니다.")
    from huggingface_hub import InferenceClient
    client = InferenceClient(api_key=HF_TOKEN)
    messages = [{"role": "user", "content": prompt}]
    
    response = client.chat_completion(
        model=model,
        messages=messages,
        max_tokens=1500
    )
    return response.choices[0].message.content

def ask_gemini(prompt, model="gemini-2.0-flash"):
    if not GEMINI_KEY:
        raise ValueError("Gemini API Key가 config.json에 없습니다.")
    from google import genai
    client = genai.Client(api_key=GEMINI_KEY)
    response = client.models.generate_content(
        model=model, 
        contents=prompt
    )
    return response.text

def ask_ollama(prompt, model="deepseek-r1:latest"):
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(OLLAMA_API, json=payload, timeout=300)
    response.raise_for_status()
    return response.json().get('response', '')

def clean_text(text):
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    return text

def ask_llm(prompt, role="writer"):
    """
    역할에 따른 최적의 모델 라우팅 및 Fallback(우회) 처리
    """
    print(f"🚦 [LLM Router] '{role}' 역할 요청 접수됨.")

    if role == "writer":
        print("   -> 1순위 시도: HuggingFace API (Llama-3-70B)")
        try:
            return clean_text(ask_huggingface(prompt))
        except Exception as e:
            print(f"   -> ⚠️ HuggingFace 실패({e}). 2순위 Gemini로 우회합니다.")
            try:
                return clean_text(ask_gemini(prompt))
            except Exception as e2:
                print(f"   -> ⚠️ Gemini 실패({e2}). 3순위 Ollama로 우회합니다.")
                try:
                    return clean_text(ask_ollama(prompt, model="deepseek-r1:latest"))
                except Exception as e3:
                    return f"Error: 모든 LLM 호출 실패 ({e3})"

    elif role == "refiner":
        print("   -> 1순위 시도: Gemini API (최고의 한국어 교정)")
        try:
            return clean_text(ask_gemini(prompt))
        except Exception as e:
            print(f"   -> ⚠️ Gemini 실패({e}). 2순위 Ollama로 우회합니다.")
            try:
                return clean_text(ask_ollama(prompt, model="deepseek-r1:latest"))
            except Exception as e2:
                return f"Error: 모든 LLM 호출 실패 ({e2})"

    elif role == "visual_director":
        print("   -> 🎨 🚀 1순위 시도: HuggingFace Llama-3 (Authentic Visual Director)")
        system_prompt = """You are a Realistic Visual Director. 
Describe script scenes for AI generation accurately. 

### [Mandatory Ethnic Rule]
- **ALL characters MUST be described as 'Korean'** (e.g., 'Korean Grandpa::1.5', 'Korean young grandson::1.5'). Never omit 'Korean'.

### [Rules]
1. Focus ON Script: Describe characters, actions, and environment naturally.
2. Character/Object Consistency: Use 'Name(::weight)' (e.g., Korean Grandpa::1.5).
3. Shot: Mention shot type naturally (Close-up, Wide-shot).
4. No Truncation: Provide ALL scenes from the script.
5. No AI Jargon: Avoid words like 'Anamorphic', 'Volumetric'.

### [Format per Scene]
- Scene #: [Timeline]
- Visual Prompt: [Pure English Prompt with 'Korean' keyword]
- Korean Text: [Dialouge]

At the very end, provide a 'READY-TO-USE PROMPTS' section with a numbered list of English prompts only.
"""
        full_prompt = f"{system_prompt}\n\n[Original Korean Script]:\n{prompt}"
        try:
            return clean_text(ask_huggingface(full_prompt))
        except Exception as e:
            print(f"   -> ⚠️ HuggingFace 실패({e}). 2순위 Gemini로 우회합니다.")
            try:
                return clean_text(ask_gemini(full_prompt))
            except Exception as e2:
                return f"Error: 비주얼 디렉팅 호출 실패 ({e2})"

    elif role in ["director", "marketing", "brainstorm"]:
        print("   -> 1순위 시도: Local Ollama (비용 제로, 무제한)")
        try:
            return clean_text(ask_ollama(prompt, model="deepseek-r1:latest"))
        except Exception as e:
            print(f"   -> ⚠️ Ollama 실패({e}). 2순위 Gemini로 우회합니다.")
            try:
                return clean_text(ask_gemini(prompt))
            except Exception as e2:
                return f"Error: 간이 호출 실패 ({e2})"
            
    else:
        return clean_text(ask_ollama(prompt))

if __name__ == "__main__":
    print(ask_llm("안녕하세요! 짧은 인사말 하나만 작성해주세요.", role="writer"))
