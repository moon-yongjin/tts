from gradio_client import Client

SPACE_ID = "FrameAI4687/Omni-Video-Factory"
HF_TOKEN = "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"

def main():
    print(f"🔍 [HF Inspector] Connecting to {SPACE_ID}...")
    try:
        client = Client(SPACE_ID, token=HF_TOKEN)
        print("\n=== API View ===")
        print(client.view_api())
        print("===============\n")
    except Exception as e:
        print(f"❌ Error connecting to HF Space: {e}")

if __name__ == "__main__":
    main()
