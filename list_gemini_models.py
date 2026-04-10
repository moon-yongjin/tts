import google.generativeai as genai
import os

API_KEY = "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"
genai.configure(api_key=API_KEY)

print("Available models:")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
