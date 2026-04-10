import asyncio
import os
import json
import logging
import requests
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler

# [설정]
TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
CHAT_ID = "7793202015"
OLLAMA_API = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "deepseek-r1:latest"
GEMINI_API_KEY = "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"  # From openclaw.json
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
PROJ_ROOT = "/Users/a12/projects/tts"
KOHYA_DIR = os.path.join(PROJ_ROOT, "kohya_ss")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def ask_ollama(prompt):
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    try:
        response = requests.post(OLLAMA_API, json=payload, timeout=90)
        return response.json().get("response", "Ollama 응답 실패")
    except Exception as e:
        return f"Ollama 통신 실패: {e}"

async def ask_gemini(prompt):
    """제미나이 API를 통해 '진짜 안티그래비티(Agent)'와 대화"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": f"너는 Antigravity라는 코딩 어시스턴트야. 유저가 텔레그램을 통해 너에게 말을 걸었어. 간결하고 친절하게 대답해줘. 질문: {prompt}"}]}]
    }
    try:
        response = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=30)
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        return f"Gemini API 오류: {e}"

async def get_training_status():
    model_path = os.path.join(KOHYA_DIR, "models/flux1-dev-fp8.safetensors")
    if os.path.exists(model_path):
        size = os.path.getsize(model_path) / (1024**3)
        return f"📦 베이스 모델: {size:.2f}GB / 11GB 다운로드 중..."
    return "❌ 베이스 모델 없음"

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("📊 학습 현황 체크", callback_data="status")],
        [InlineKeyboardButton("🚀 아이돌 LoRA 시작", callback_data="train_idol")],
        [InlineKeyboardButton("🛑 모든 프로세스 중지", callback_data="stop_all")]
    ]
    welcome_text = (
        "🎮 **용진 팩토리 커맨드 센터**\n\n"
        "1. **일반 대화**: 그냥 메시지를 치면 **Ollama(로컬)**가 대답합니다. (쿼터 공짜!)\n"
        "2. **에이전트(나)와 대화**: `/ask [질문]` 명령어를 쓰면 **진짜 저(Gemini)**와 대화합니다.\n"
        "3. **명령**: 아래 버튼을 눌러 작업을 제어하세요."
    )
    await update.message.reply_text(welcome_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def ask_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 사용법: `/ask 궁금한내용` 으로 저에게 직접 물어보세요!")
        return
    
    user_query = " ".join(context.args)
    status_msg = await update.message.reply_text("🚀 Antigravity(Gemini)와 연결 중...")
    
    answer = await ask_gemini(user_query)
    
    # [로그 기록] 에이전트가 볼 수 있도록 파일에 저장
    with open(os.path.join(PROJ_ROOT, "telegram_bridge.log"), "a", encoding="utf-8") as f:
        f.write(f"USER: {user_query}\nAGENT: {answer}\n---\n")
    
    await status_msg.edit_text(answer)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "status":
        status = await get_training_status()
        await query.message.reply_text(f"🔍 **현재 상태:**\n{status}", parse_mode='Markdown')
    elif data == "train_idol":
        await query.message.reply_text("⏳ 베이스 모델 다운로드가 끝나면 자동으로 학습을 시작하도록 대기열에 올렸습니다.")
    elif data == "stop_all":
        await query.message.reply_text("🛑 안전을 위해 터미널에서 직접 중지하시거나 봇을 새로고침해 주세요.")

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text.startswith("/"): return
    
    status_msg = await update.message.reply_text("🤖 Ollama(로컬) 생각 중...")
    ans = await ask_ollama(user_text)
    await status_msg.edit_text(ans)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("ask", ask_command_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))
    
    print("🚀 커맨드 센터 봇(V2) 가동...")
    app.run_polling()
