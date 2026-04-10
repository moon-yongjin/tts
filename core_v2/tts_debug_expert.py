import sys
from pathlib import Path

# Add project root to path for imports
PROJ_ROOT = Path("/Users/a12/projects/tts")
sys.path.append(str(PROJ_ROOT))

from Ollama_Studio.llm_router import ask_llm

prompt = """
[MISSION: DEBUG CORE TTS CLIPPING ISSUE IN KOREAN]
The user is experiencing a clipping issue with a TTS model (Qwen-TTS based). 
Specifically, sentences ending with '~다' or similar polite endings are being cut off prematurely at the end of audio segments.

[CODE CONTEXT]
The current script uses:
1. re.findall(r'[^.!?,\s][^.!?,\n]*[.!?,\n]*', line) for chunking.
2. A silence trimmer as follows:
def trim_silence(audio, threshold=-50.0, padding_ms=150):
    start_trim = detect_leading_silence(audio, silence_threshold=threshold)
    end_trim = detect_leading_silence(audio.reverse(), silence_threshold=threshold)
    duration = len(audio)
    trimmed = audio[start_trim:max(start_trim+1, duration-end_trim)]
    silence = AudioSegment.silent(duration=padding_ms)
    return silence + trimmed.fade_out(100) + silence

[OBSERVATION]
The user says "it's not cutting after the period, but something triggers when it ends with '~다' and it clips the ending."

[QUESTIONS]
1. Is this a known issue with Qwen-TTS or similar zero-shot models handling Korean sentence endings?
2. Does ending a chunk with '~다' (without a period) cause the model to end the generation abruptly compared to when it has a period?
3. How should I adjust the padding or text normalization to prevent this 'swallowing' of the final syllable?
4. Is the audio trimming logic above too aggressive for Korean speech cadences?

Please provide a technical explanation and a specific recommendation.
"""

try:
    response = ask_llm(prompt, role="expert")
    print(response)
except Exception as e:
    print(f"Error: {e}")
