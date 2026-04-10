from google import genai
import sys

key = "AIzaSyC9nFI69pzQqH5x60_I1qslUUUeTV58nAk"

try:
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents="Hello, this is a test."
    )
    print("✅ SUCCESS: The key works for Gemini API!")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ FAILURE: The key did not work for Gemini API.")
    print(f"Error: {e}")
