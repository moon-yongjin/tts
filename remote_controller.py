import asyncio
import json
import os
import websockets
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# --- CONFIGURATION ---
HTTP_PORT = 8000
WS_PORT = 8001
# ---------------------

class RemoteWhiskServer:
    def __init__(self):
        self.clients = set()
        self.prompt_queue = []
        self.is_running = False

    async def register(self, websocket):
        self.clients.add(websocket)
        print(f"📡 New client connected. Total: {len(self.clients)}")
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            print(f"🔌 Client disconnected. Remaining: {len(self.clients)}")

    async def send_command(self, action, data):
        if not self.clients:
            print("⚠️ No clients connected!")
            return
        
        message = json.dumps({"action": action, **data})
        # 모든 연결된 클라이언트에게 전송 (보통은 1개)
        await asyncio.gather(*[client.send(message) for client in self.clients])

    async def process_queue(self):
        if self.is_running or not self.prompt_queue:
            return
        
        self.is_running = True
        print(f"🚀 Starting automation for {len(self.prompt_queue)} prompts")
        
        total = len(self.prompt_queue)
        current = 0
        
        while self.prompt_queue:
            prompt = self.prompt_queue.pop(0)
            current += 1
            print(f"➡️ Sending prompt [{current}/{total}]: {prompt[:30]}...")
            
            # 클라이언트에게 입력 및 생성 명령 전송
            await self.send_command("EXECUTE_GENERATION", {
                "prompt": prompt,
                "current": current,
                "total": total
            })
            
            # 위스크 생성 시간을 고려한 대기 (클라이언트 대기 완료 신호를 받는 게 베스트지만 일단 시간으로)
            await asyncio.sleep(25) # 보수적으로 25초 대기
            
        self.is_running = False
        print("✅ Finished all prompts")

    def add_prompts(self, prompts):
        self.prompt_queue.extend(prompts)
        asyncio.run_coroutine_threadsafe(self.process_queue(), loop)

# 전역 루프 및 서버 인스턴스
rw_server = RemoteWhiskServer()
loop = None

class RemoteUIHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Whisk Pro Remote - 사령탑</title>
                <style>
                    body { font-family: 'Pretendard', sans-serif; padding: 50px; background: #0f172a; color: white; text-align: center; }
                    .container { max-width: 600px; margin: 0 auto; background: #1e293b; padding: 30px; border-radius: 16px; border: 1px solid #334155; }
                    textarea { width: 100%; height: 200px; margin: 20px 0; padding: 15px; border-radius: 8px; background: #0f172a; border: 1px solid #334155; color: white; box-sizing: border-box; }
                    button { width: 100%; padding: 15px; background: #6366f1; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; }
                    button:hover { background: #4f46e5; }
                    .info { font-size: 14px; color: #94a3b8; margin-top: 10px; text-align: left; }
                    .highlight { color: #818cf8; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 Whisk Pro Remote</h1>
                    <p>원격으로 친구의 컴퓨터를 조종합니다.</p>
                    
                    <div class="info">
                        <strong>방법:</strong><br>
                        1. 친구에게 확장 프로그램을 설치하게 하세요.<br>
                        2. 친구의 확장 프로그램 주소칸에 아래를 적으라고 하세요:<br>
                        <span class="highlight">ws://192.168.0.27:8001</span> (또는 가상주소)<br>
                        3. 여기에 대본을 넣고 전송을 누르세요.
                    </div>

                    <textarea id="script" placeholder="여기에 대본 내용을 입력하세요..."></textarea><br>
                    <button onclick="send()">대본 전송 및 자동화 시작</button>
                </div>
                <script>
                    async function send() {
                        const text = document.getElementById('script').value;
                        if(!text.trim()) return alert("대본을 입력해주세요!");
                        const res = await fetch('/upload-script', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ text })
                        });
                        const data = await res.json();
                        alert(data.count + "개의 프롬프트 전송 완료! 친구 컴이 움직이기 시작합니다.");
                    }
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/upload-script':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data)
                script_text = data.get('text', '')
                lines = script_text.split('\n')
                prompts = [l.strip() for l in lines if len(l.strip()) > 10 and not l.strip().startswith('"')]
                
                if prompts:
                    rw_server.add_prompts(prompts)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "count": len(prompts)}).encode())
                else:
                    self.send_error(400, "No valid prompts found")
            except Exception as e:
                self.send_error(500, str(e))
        else:
            super().do_POST()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run_http_server():
    try:
        server = HTTPServer(('0.0.0.0', HTTP_PORT), RemoteUIHandler)
        print(f"🌐 UI Server running on http://localhost:{HTTP_PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"❌ HTTP Server Error: {e}")

async def ws_main():
    server = await websockets.serve(rw_server.register, "0.0.0.0", WS_PORT)
    print(f"📡 WebSocket Command Server running on ws://localhost:{WS_PORT}")
    await server.wait_closed()

if __name__ == "__main__":
    # 1. 루프 설정
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 2. UI 서버 (HTTP) 실행
    threading.Thread(target=run_http_server, daemon=True).start()
    
    # 3. 명령 서버 (WebSocket) 실행
    try:
        loop.run_until_complete(ws_main())
    except KeyboardInterrupt:
        print("\n👋 Server shutting down...")
