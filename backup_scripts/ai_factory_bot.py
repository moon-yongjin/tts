import os
import logging
import asyncio
import subprocess
import time
import psutil
import gc
import re
import tempfile
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler, CallbackQueryHandler

# [설정]
TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
PROJ_ROOT = os.path.expanduser("~/projects/tts")
PYTHON_EXE = "/Users/a12/miniforge3/bin/python"
PATH_ENV = f"/opt/homebrew/bin:/Users/a12/miniforge3/bin:{os.environ.get('PATH', '')}"
BRIDGE_DIR = os.path.join(PROJ_ROOT, "bridge")
SESSION_FILE = os.path.join(PROJ_ROOT, "session.json")
OLLAMA_API = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "deepseek-r1:latest"

os.makedirs(BRIDGE_DIR, exist_ok=True)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# 세션 관리 (메모리 + 파일 권한 유지)
USER_SESSIONS = {}
if os.path.exists(SESSION_FILE):
    try:
        with open(SESSION_FILE, "r") as f:
            saved_chat_ids = json.load(f)
            for cid in saved_chat_ids: USER_SESSIONS[int(cid)] = {"status": "IDLE"}
    except: pass

STYLES = ["수묵화", "고전민화", "애니메이션", "김성모", "스케치", "컬러스케치"]
DIRECTIONS = {"1": "[대립/긴장] 빌런 교차", "2": "[미장센] 상징적 연출", "3": "[시점변화] POV/반응샷"}

def save_sessions():
    with open(SESSION_FILE, "w") as f:
        json.dump(list(USER_SESSIONS.keys()), f)

async def ask_ollama(prompt, model=DEFAULT_MODEL):
    """로컬 올라마 API 호출 (Curl fallback 포함)"""
    try:
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False})
        cmd = ["curl", "-s", "-X", "POST", OLLAMA_API, "-H", "Content-Type: application/json", "-d", payload]
        out = subprocess.check_output(cmd, timeout=35).decode()
        return json.loads(out).get("response", "응답 실패")
    except Exception as e:
        return f"Ollama 통신 실패: {e}"

async def run_step(step_name, script_path, update: Update, args=None, env_vars=None):
    prompt_msg = await (update.message.reply_text if update.message else update.callback_query.message.reply_text)(f"🚀 [{step_name}] 작업 중...")
    
    cmd_parts = [f"export PATH='{PATH_ENV}'", f"cd {PROJ_ROOT}"]
    if env_vars:
        for k, v in env_vars.items(): cmd_parts.append(f"export {k}={v}")
    
    python_cmd = f"{PYTHON_EXE} {script_path}"
    if args: python_cmd += " " + " ".join([f"'{a}'" for a in args])
    cmd_parts.append(python_cmd)
    
    process = await asyncio.create_subprocess_shell(" && ".join(cmd_parts), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    out, err = stdout.decode('utf-8', 'ignore').strip(), stderr.decode('utf-8', 'ignore').strip()
    
    if process.returncode == 0:
        await prompt_msg.edit_text(f"✅ [{step_name}] 완료")
        # 로그에서 결과물 경로 추출 (07_master에서 ✨ 완성! 결과물: /path/... 로 출력됨)
        match = re.search(r"(결과물|파일 위치):\s*([^\s\n]+)", out)
        return True, match.group(2) if match else None
    else:
        await prompt_msg.edit_text(f"❌ [{step_name}] 실패\n{err[:200]}")
        return False, None

def get_latest_video():
    """Download 폴더 내의 모든 하위 폴더에서 가장 최신 MP4 탐색"""
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    latest_file = None
    latest_time = 0
    
    for root, dirs, files in os.walk(downloads):
        if "무협_생성_" in root:
            for f in files:
                if f.lower().endswith(".mp4"):
                    fpath = os.path.join(root, f)
                    ftime = os.path.getmtime(fpath)
                    if ftime > latest_time:
                        latest_time = ftime
                        latest_file = fpath
    return latest_file

async def check_bridge_requests(context: ContextTypes.DEFAULT_TYPE):
    req_path = os.path.join(BRIDGE_DIR, "request.json")
    res_path = os.path.join(BRIDGE_DIR, "result.json")
    while True:
        if os.path.exists(req_path):
            try:
                with open(req_path, "r") as f: req = json.load(f)
                rid, cmd = req.get("id"), req.get("cmd")
                for cid in list(USER_SESSIONS.keys()):
                    kb = [[InlineKeyboardButton("✅ 승인", callback_data=f"br_app_{rid}"), 
                           InlineKeyboardButton("❌ 거절", callback_data=f"br_rej_{rid}")]]
                    await context.bot.send_message(chat_id=cid, text=f"🛡️ **원격 명령 승인 요청**\n`{cmd}`", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
                while os.path.exists(req_path): await asyncio.sleep(2)
            except: pass
        await asyncio.sleep(3)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data, chat_id = query.data, update.effective_chat.id

    if data.startswith("br_"):
        act, rid = ("app" if "app" in data else "rej"), data.split("_")[-1]
        req_p, res_p = os.path.join(BRIDGE_DIR, "request.json"), os.path.join(BRIDGE_DIR, "result.json")
        if act == "app" and os.path.exists(req_p):
            with open(req_p, "r") as f: cmd = json.load(f).get("cmd")
            await query.edit_message_text(f"🏃 실행: `{cmd}`")
            p = await asyncio.create_subprocess_shell(f"export PATH='{PATH_ENV}' && cd {PROJ_ROOT} && {cmd}", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            so, se = await p.communicate()
            with open(res_p, "w") as f: json.dump({"id":rid, "out":so.decode(), "err":se.decode(), "code":p.returncode}, f)
            os.remove(req_p)
            await query.message.reply_text(f"✅ 완료 (ID: {rid})")
        else:
            if os.path.exists(req_p): os.remove(req_p)
            await query.edit_message_text("❌ 거절됨")

    elif chat_id in USER_SESSIONS:
        if data.startswith("style_"):
            USER_SESSIONS[chat_id]["style"] = data.split("_")[1]
            kb = [[InlineKeyboardButton(v, callback_data=f"dir_{k}")] for k, v in DIRECTIONS.items()]
            await query.edit_message_text(f"📽️ 연출 스타일 선택", reply_markup=InlineKeyboardMarkup(kb))
        elif data.startswith("dir_"):
            style, direct = USER_SESSIONS[chat_id]["style"], data.split("_")[1]
            await query.edit_message_text(f"🎬 최종 생성 중... (화풍: {style})")
            suc, _ = await run_step("이미지", "core_v2/02_visual_director_v2.py", update, args=[style, direct])
            if suc:
                suc, fpath = await run_step("마우리", "core_v2/07_master_integration.py", update)
                if not fpath: fpath = get_latest_video()
                if fpath and os.path.exists(fpath):
                    size = os.path.getsize(fpath)/(1024**2)
                    if size > 50: await query.message.reply_text(f"⚠️ 50MB 초과 (직접 확인): {fpath}")
                    else:
                        with open(fpath, 'rb') as f: await query.message.reply_document(f, caption="✅ 영상 배달 완료!")
                else: await query.message.reply_text("❓ 결과물을 찾지 못했습니다.")
            del USER_SESSIONS[chat_id]

async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id, text = update.effective_chat.id, update.message.text
    if chat_id not in USER_SESSIONS:
        USER_SESSIONS[chat_id] = {"status": "IDLE"}
        save_sessions()

    if len(text) > 40:
        await update.message.reply_text("📝 긴 글 감지. 영상 제작을 시작합니다.")
        USER_SESSIONS[chat_id].update({"status": "PROD", "script": text})
        suc, _ = await run_step("TTS", "core_v2/01_muhyup_factory_v2.py", update)
        if suc:
            kb = [[InlineKeyboardButton(s, callback_data=f"style_{s}")] for s in STYLES]
            await update.message.reply_text("🎨 화풍 선택", reply_markup=InlineKeyboardMarkup(kb))
    else:
        ans = await ask_ollama(text)
        await update.message.reply_text(f"🤖 **Ollama:**\n{ans}", parse_mode='Markdown')

async def post_init(app):
    asyncio.get_event_loop().create_task(check_bridge_requests(app))

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("AI Factory v2.4 Online")))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_handler))
    app.run_polling()
