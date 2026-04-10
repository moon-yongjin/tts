import asyncio
import os
import json
import logging
import urllib.request
import base64
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# [설정]
TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
CHAT_ID = "7793202015"

# 📡 Local API URLs
# 💡 LM Studio 서버가 가동되어 있어야 합니다. (Port: 1234)
LM_STUDIO_API = "http://localhost:1234/v1/chat/completions"
DRAWTHINGS_API = "http://127.0.0.1:7860/sdapi/v1/txt2img"

PROJ_ROOT = "/Users/a12/projects/tts"
CONFIG_PATH = os.path.join(PROJ_ROOT, "config.json")

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Gemini API 설정 로드 (백업용)
GEMINI_API_KEY = "AIzaSyDOtvWYJaFgSoOmDDQ77QO4i6RoFdWWuOA"
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            if "Gemini_API_KEY" in config: GEMINI_API_KEY = config["Gemini_API_KEY"]
    except: pass

# ---------------------------------------------------------
# 🧠 [1. 로컬 연산 엔진]
# ---------------------------------------------------------

async def ask_local_mlx(prompt, system_instruction="너는 Antigravity 계열의 AI 조수야. 간결하고 확실하게 대답해줘."):
    """로컬 LM Studio 서버를 이용한 연산 (검열 없음)"""
    payload = {
        "model": "qwen/qwen2.5-vl-7b", # LM Studio 로드된 모델 식별자 지정 (오류 대응)
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    req = urllib.request.Request(LM_STUDIO_API, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    try:
        loop = asyncio.get_event_loop()
        def _call():
             with urllib.request.urlopen(req) as res: return json.loads(res.read().decode('utf-8'))
        response = await loop.run_in_executor(None, _call)
        return response['choices'][0]['message']['content'].strip()
    except Exception as e: return f"❌ 로컬 MLX 통신 실패: {e}"

async def ask_gemini(prompt):
    """클라우드 Gemini 연동 (보안 필터링 적용됨)"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": f"너는 Antigravity 코딩 어시스턴트야. 질문: {prompt}"}]}]}
    try:
        loop = asyncio.get_event_loop()
        def _call():
             req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
             with urllib.request.urlopen(req) as res: return json.loads(res.read().decode('utf-8'))
        result = await loop.run_in_executor(None, _call)
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e: return f"❌ Gemini API 에러: {e}"

# ---------------------------------------------------------
# 🎨 [2. 로컬 이미지 가동 엔진 (DrawThings)]
# ---------------------------------------------------------

async def generate_local_image(prompt_text):
    """드로우띵 App 로컬 연동 및 생성"""
    # 💡 국장님 최적화 세팅 복제
    payload = {
        "prompt": f"Photorealistic, high-end cinematic, ultra-detailed textures, {prompt_text}",
        "negative_prompt": "cartoon, 3d, illustration, low quality, bad anatomy",
        "steps": 8,
        "width": 1024,
        "height": 1024, # 기본 1:1
        "guidance_scale": 1.0,
        "sampler": "Euler A AYS",
        "shift": 3.0,
        "sharpness": 5
    }
    
    try:
        loop = asyncio.get_event_loop()
        def _call():
             req = urllib.request.Request(DRAWTHINGS_API, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
             with urllib.request.urlopen(req) as res: return json.loads(res.read().decode('utf-8'))
        data = await loop.run_in_executor(None, _call)
        
        if "images" in data and len(data["images"]) > 0:
            return base64.b64decode(data["images"][0])
    except Exception as e:
        print(f"이미지 생성 에러: {e}")
    return None

# ---------------------------------------------------------
# 🤖 [3. 텔레그램 핸들러 및 라우팅]
# ---------------------------------------------------------

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome = (
        "🔥 **[로컬 마스터 에이전트] 가동 (LM Studio)**\n\n"
        "1. **일반 대화 / 그림 지시**: 그냥 입력하세요.\n"
        "   - *그림을 원하시면 '그려줘' 혹은 'Draw'를 붙이세요.*\n"
        "2. **코딩/시스템 질문 (/ask)**: 진짜 저(Gemini)와 연결됩니다.\n\n"
        "💡 로컬 LM Studio와 드로우띵을 사용하므로 **검열과 과금이 없습니다.**"
    )
    await update.message.reply_text(welcome, parse_mode='Markdown')

async def main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if user_text.startswith("/"): return
    if str(update.effective_chat.id) != CHAT_ID: return

    # 💡 1단계: 로컬 MLX를 통해 의도 분석 (그림 그리기인지, 단순 대화인지)
    classifer_prompt = f"""
    아래 유저의 메세지가 '이미지 생성(그림 그려달라는 오더)'인지 '단순 대화'인지 판단하세요.
    메시지: "{user_text}"
    
    출력 규격 한줄로:
    [IMAGE] 영어프롬프트내용 -> 만약 그림 그리기를 원한다면.
    [CHAT] 단순 답변 내용 -> 일반적인 대화라면.
    """
    
    analysis = await ask_local_mlx(classifer_prompt, system_instruction="너는 유저의 명령 유형을 분류하는 분류기야.")
    print(f"🔍 [의도 분석]: {analysis}")

    # 💡 2단계: 분기 처리
    if "[IMAGE]" in analysis or "그려줘" in user_text or "그려" in user_text:
        # 드로우띵 연동 (그림 그리기)
        status_msg = await update.message.reply_text("🎨 **로컬 DrawThings 연동 중... (검열 없음)**")
        
        # MLX에게 영어 프롬프트 조립을 맡김 (과금 방지)
        refiner = f"유저가 다음을 그리려 합니다: '{user_text}'. Stable Diffusion용 cinematic 영문 묘사 프롬프트 1줄만 출력하세요."
        english_prompt = await ask_local_mlx(refiner)
        print(f"📝 [영문 프롬프트]: {english_prompt}")
        
        # 이미지 생성 가동
        img_bytes = await generate_local_image(english_prompt)
        
        if img_bytes:
            await status_msg.delete()
            # 텔레그램 전송
            await context.bot.send_photo(chat_id=CHAT_ID, photo=img_bytes, caption=f"✅ 로컬 완성: {english_prompt[:100]}...")
        else:
            await status_msg.edit_text("❌ 로컬 이미지 생성에 실패했습니다 (서버 상태 확인 필요).")
            
    else:
        # 일반 대화 분기 -> 로컬 LM Studio 가동
        status_msg = await update.message.reply_text("🤖 LM Studio(로컬) 생각 중...")
        ans = await ask_local_mlx(user_text) # 함수명은 유지
        await status_msg.edit_text(ans)

async def ask_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """에이전트(Gemini) 직통 라인"""
    if not context.args:
         await update.message.reply_text("💡 사용법: `/ask [질문]`")
         return
    user_query = " ".join(context.args)
    status_msg = await update.message.reply_text("🚀 Antigravity(Gemini)와 연결 중...")
    answer = await ask_gemini(user_query)
    
    # 워크스페이스 대장에 기록
    with open(os.path.join(PROJ_ROOT, "telegram_commands.log"), "a", encoding="utf-8") as f:
         f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] USER: {user_query}\nAGENT: {answer}\n---\n")
         
    await status_msg.edit_text(answer)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("ask", ask_command_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_handler))
    
    print("🚀 [로컬 마스터 에이전트 봇] 가동 대기 중...")
    app.run_polling()
