import requests
import json
import sys

def ask_ollama(model, prompt):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json().get('response', 'No response from model.')
    except Exception as e:
        return f"Error connecting to Ollama: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 ask_ollama.py <model> <prompt>")
        sys.exit(1)
    
    model_name = sys.argv[1]
    user_prompt = " ".join(sys.argv[2:])
    
    result = ask_ollama(model_name, user_prompt)
    print(result)
