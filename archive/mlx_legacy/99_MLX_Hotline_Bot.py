import asyncio
import os
import json
import logging
import urllib.request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# [설정]
TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
CHAT_ID = "7793202015"
MLX_API = "http://127.0.0.1:8080/v1/chat/completions"
PROJ_ROOT = "/Users/a12/projects/tts"
CONFIG_PATH = os.path.join(PROJ_ROOT, "config.json")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Gemini API 설정 로드
GEMINI_API_KEY = "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA" # 기본값
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            if "Gemini_API_KEY" in config:
                GEMINI_API_KEY = config["Gemini_API_KEY"]
    except: pass

async def ask_mlx(prompt):
    """로컬 MLX 서버(Qwen)에 질문 전달 (무제한 일상 대화)"""
    payload = {
        "model": "mlx-community/Qwen2.5-1.5B-Instruct-4bit",
        "messages": [
            {"role": "system", "content": "너는 Antigravity라는 로컬 코딩 AI 조수야. 국장님을 대할 때 친근하고 단도직입적으로 지원해줘."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    req = urllib.request.Request(
        MLX_API, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        loop = asyncio.get_event_loop()
        def _call():
            with urllib.request.urlopen(req) as res:
                return json.loads(res.read().decode('utf-8'))
        response = await loop.run_in_executor(None, _call)
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"❌ 로컬 MLX 통신 실패: {e}"

async def ask_gemini(prompt):
    """제미나이 API를 통해 '진짜 안티그래비티(Agent)'와 대화"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": f"너는 Antigravity라는 코딩 어시스턴트이자 유저의 대장이야. 유저가 텔레그램을 통해 너에게 직접 오더를 내렸어. 간결하고 확실하게 대답해줘. 질문: {prompt}"}]}]
    }
    try:
        loop = asyncio.get_event_loop()
        def _call():
             req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
             with urllib.request.urlopen(req) as res:
                  return json.loads(res.read().decode('utf-8'))
        result = await loop.run_in_executor(None, _call)
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"❌ Gemini API 연동 에러: {e}"

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🔥 **[Local MLX] 전용 핫라인 연결되어있습니다!**\n\n"
        "1. **일반 대화**: 그냥 메세지를 치면 **로컬 MLX**가 답변합니다. (무제한 공짜)\n"
        "2. **에이전트 조종 (/ask)**: `/ask [질문]` 명령어를 쓰면 **진짜 저(Gemini)**와 연결됩니다.\n\n"
        "예시: `/ask 오늘 돌린 코드가 잘 나왔나 보고해`"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def ask_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """진짜 에이전트(나)와 Talk 하는 핸들러"""
    if not context.args:
        await update.message.reply_text("💡 사용법: `/ask 궁금한내용` 으로 저와 연결할 수 있습니다!")
        return
    
    user_query = " ".join(context.args)
    status_msg = await update.message.reply_text("🚀 Antigravity(Gemini)와 다이렉트 연결 중...")
    
    answer = await ask_gemini(user_query)
    
    # [로그 기록] 에이전트가 볼 수 있도록 workspace에 기록
    log_path = os.path.join(PROJ_ROOT, "telegram_commands.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] USER: {user_query}\nAGENT: {answer}\n---\n")
    
    await status_msg.edit_text(answer)

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text.startswith("/"): return
    
    if str(update.effective_chat.id) != CHAT_ID: return

    status_msg = await update.message.reply_text("🤖 MLX(로컬) 생각 중...")
    ans = await ask_mlx(user_text)
    await status_msg.edit_text(ans)

if __name__ == "__main__":
    import time
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("ask", ask_command_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))
    
    print("🚀 업데이트된 로컬 MLX 핫라인 봇 가동 대기 중...")
    app.run_polling()
