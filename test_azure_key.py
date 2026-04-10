import azure.cognitiveservices.speech as speechsdk
import sys

SPEECH_KEY = "21HfTF65JeOoI5mqoW5NfPYZcmG114R7AFzrjbk5HLRE4fqIua7NJQQJ99CAACNns7RXJ3w3AAAYACOGMfRn"
SPEECH_REGION = "koreacentral"

speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
result = synthesizer.speak_text_async("테스트입니다.").get()

if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
    print("✅ Azure Key is VALID")
else:
    print(f"❌ Azure Key is INVALID: {result.reason}")
    if result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Error Code: {cancellation_details.error_code}")
        print(f"Error Details: {cancellation_details.error_details}")
