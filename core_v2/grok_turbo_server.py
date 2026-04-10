import asyncio
import os
import base64
import json
import websockets
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# 설정
INPUT_DIR = os.path.expanduser("~/Downloads/Grok_Video_Input")
PROMPT = "."  # 국장님 요청: 최소 프롬프트
PORT = 8765

os.makedirs(INPUT_DIR, exist_ok=True)

class GrokPushHandler(FileSystemEventHandler):
    def __init__(self, server):
        self.server = server

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            print(f"📂 New Image Detected: {os.path.basename(event.src_path)}")
            asyncio.run_coroutine_threadsafe(self.server.push_to_extension(event.src_path), self.server.loop)

class GrokTurboServer:
    def __init__(self):
        self.clients = set()
        self.loop = None

    async def register(self, websocket):
        self.clients.add(websocket)
        print("🔌 Extension Connected via WebSocket")
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            print("🔌 Extension Disconnected")

    async def push_to_extension(self, image_path):
        if not self.clients:
            print("⚠️ No extension connected. Skipping push.")
            return

        try:
            with open(image_path, "rb") as f:
                encoded_image = base64.b64encode(f.read()).decode('utf-8')
            
            message = {
                "action": "PUSH_VIDEO_TASK",
                "filename": os.path.basename(image_path),
                "imageData": f"data:image/png;base64,{encoded_image}",
                "prompt": PROMPT
            }
            
            payload = json.dumps(message)
            for client in self.clients:
                await client.send(payload)
            print(f"🚀 Pushed task to extension: {os.path.basename(image_path)}")
        except Exception as e:
            print(f"❌ Push Error: {e}")

    async def start(self):
        self.loop = asyncio.get_running_loop()
        handler = GrokPushHandler(self)
        observer = Observer()
        observer.schedule(handler, INPUT_DIR, recursive=False)
        observer.start()
        
        print(f"🛰️ Grok Turbo Server started on ws://localhost:{PORT}")
        print(f"📂 Watching folder: {INPUT_DIR}")
        
        async with websockets.serve(self.register, "localhost", PORT):
            await asyncio.Future()  # Run forever

if __name__ == "__main__":
    server = GrokTurboServer()
    asyncio.run(server.start())
