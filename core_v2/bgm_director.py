import os
import re
import json
from openai import OpenAI

# [Settings] 
# Use OPENAI_API_KEY from environment
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = None # Use default OpenAI URL

class BGMusicProducer:
    """
    AI BGM Producer that converts story/video context into professional ACE-Step prompts.
    Optimized for 'Addictive, Catchy, Rhythmic' shorts music and 'K-Funk' fusion.
    """
    def __init__(self, model="gpt-4o"):
        if not API_KEY:
            # Fallback or error handling if key is missing
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        self.client = OpenAI(api_key=API_KEY)
        self.model = model

    def compose_prompt(self, video_context, target_mood="Cheerful and Addictive"):
        """
        Generates ACE-Step Tags and XML-structured Lyrics based on context.
        """
        system_prompt = """
        You are a professional Music Producer specializing in viral 'Shorts' background music and 'K-Fusion' (mixing Korean traditional elements with modern genres).
        Your task is to generate optimal prompts for the ACE-Step music generation model.

        Guidelines:
        1. ACE-Step works best with comma-separated 'Tags' and XML-structured 'Lyrics'.
        2. 'K-Funk' Specialty: Blend high-energy Funk (Slap bass, Horns) with Korean instruments (Gayageum plucking, Haegeum melodies, Kkwaenggwari rhythms).
        3. Focus on 'Addictive', 'Catchy', 'Minimalist but Rhythmic' sounds.
        4. For Shorts, a tempo of 85 BPM or 128 BPM is generally best.
        5. ALWAYS include [instrumental] and set [VOCALS: None] to avoid human voices unless specified.
        6. Use specialized instruments like 'Toy Piano Synth', 'Plucked Strings', 'Marimba', 'Retro Lead', 'Gayageum', 'Haegeum'.

        Output Format (JSON):
        {
          "tags": "comma, separated, tags, here",
          "xml_lyrics": "<SONG_PROMPT>...</SONG_PROMPT> [instrumental]",
          "explanation": "Why you chose this style and how you mixed Korean elements"
        }
        """

        user_input = f"Video Context: {video_context}\nTarget Mood: {target_mood}\nRequested Style Reference: Funk, Soul, Slap Bass, Horns with K-Elements"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"❌ Producer Error: {e}")
            return None

if __name__ == "__main__":
    producer = BGMusicProducer()
    context = "A funny Joseon-era story about a nobleman being fooled by a merchant. Bright and slightly ironic."
    result = producer.compose_prompt(context, "Addictive and Quirky")
    
    if result:
        print("🎵 AI Producer's Composition:")
        print(f"Tags: {result['tags']}")
        print(f"XML: {result['xml_lyrics']}")
        print(f"Logic: {result['explanation']}")
