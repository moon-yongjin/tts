from gradio_client import Client
import os

HF_TOKEN = "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"

spaces = [
    "FrameAI4687/Omni-Video-Factory",
    "chujie87/Text-Behind-Video",
    "Lightricks/LTX-Video",
    "Kwai-VGI/LivePortrait",
    "ByteDance/AnimateDiff-Lightning"
]

def inspect_spaces():
    for space in spaces:
        print(f"\n" + "="*50)
        print(f"🔍 Inspecting Space: {space}")
        print("="*50)
        try:
            client = Client(space, token=HF_TOKEN)
            api_info = client.view_api(return_format="dict")
            
            # Print simplified API info
            for name, endpoint in api_info.get("named_endpoints", {}).items():
                print(f"\n📌 Endpoint: {name}")
                print(f"   Inputs: {len(endpoint.get('parameters', []))}")
                for param in endpoint.get('parameters', []):
                    print(f"     - {param.get('label') or param.get('name')} ({param.get('type')})")
            
            for i, endpoint in enumerate(api_info.get("unnamed_endpoints", [])):
                print(f"\n📌 Unnamed Endpoint {i}")
                print(f"   Inputs: {len(endpoint.get('parameters', []))}")

        except Exception as e:
            print(f"❌ Failed to inspect {space}: {e}")

if __name__ == "__main__":
    inspect_spaces()
