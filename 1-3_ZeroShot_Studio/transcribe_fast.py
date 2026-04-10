import sys
import os
import mlx_whisper

def fast_transcribe(audio_path):
    print(f"🎙️ Testing: {audio_path}")
    if not os.path.exists(audio_path):
        print("❌ Error: File not found")
        return
    
    model = "mlx-community/whisper-large-v3-turbo"
    result = mlx_whisper.transcribe(audio_path, path_or_hf_repo=model, language="ko")
    print("\n--- TRANSCRIPT WITH TIMESTAMPS ---")
    for segment in result["segments"]:
        print(f"[{segment['start']:.2f} - {segment['end']:.2f}] {segment['text']}")
    print("--------------------------------\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fast_transcribe(sys.argv[1])
