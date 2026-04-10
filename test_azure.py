import azure.cognitiveservices.speech as speechsdk
import os
import sys

# Load key from config
try:
    import json
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    KEY = config.get("Azure_Speech_Key")
    REGION = config.get("Azure_Region")
except:
    KEY = "21HfTF65JeOoI5mqoW5NfPYZcmG114R7AFzrjbk5HLRE4fqIua7NJQQJ99CAACNns7RXJ3w3AAAYACOGMfRn"
    REGION = "koreacentral"

# Output path in Downloads
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
output_path = os.path.join(DOWNLOADS_DIR, "test_azure_output.mp3")

print(f"Generating to: {output_path}")

speech_config = speechsdk.SpeechConfig(subscription=KEY, region=REGION)
speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Audio48Khz192KBitRateMonoMp3)
audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)

synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

# SSML Test
ssml_text = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ko-KR"><voice name="ko-KR-JiMinNeural"><prosody rate="-10.00%" pitch="-5.00%">테스트 음성입니다.</prosody></voice></speak>'

result = synthesizer.speak_ssml_async(ssml_text).get()

if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print(f"✅ Azure TTS File Saved! Size: {os.path.getsize(output_path)} bytes")
elif result.reason == speechsdk.ResultReason.Canceled:
    cancellation_details = result.cancellation_details
    print("❌ Azure TTS Failed!")
    print(f"Reason: {cancellation_details.reason}")
    print(f"Error Details: {cancellation_details.error_details}")
