import asyncio
import os
import time
import logging
from telegram import Bot
from telegram.error import TelegramError

# [설정]
TELEGRAM_TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"
OUTPUT_DIR = "/Users/a12/projects/tts/kohya_ss/training/idol/model"
CHECKPOINT_INTERVAL = 300  # 5분마다 상태 체크

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def send_msg(text):
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        # 유저 ID를 찾기 위해 최근 업데이트 확인
        updates = await bot.get_updates()
        if updates:
            chat_id = updates[-1].message.chat_id
            await bot.send_message(chat_id=chat_id, text=text)
            print(f"✅ 알림 전송: {text}")
        else:
            print("⚠️ 봇에게 메시지를 먼저 보내주세요 (ID 확인용)")
    except Exception as e:
        print(f"❌ 알림 전송 실패: {e}")

async def monitor_training():
    print("🚀 LoRA 학습 모니터링 시작...")
    await send_msg("🤖 LoRA 학습 모니터링 봇이 가동되었습니다. (쿼터 걱정 없는 무설정 버전)")
    
    last_files = set(os.listdir(OUTPUT_DIR)) if os.path.exists(OUTPUT_DIR) else set()
    
    while True:
        if os.path.exists(OUTPUT_DIR):
            current_files = set(os.listdir(OUTPUT_DIR))
            new_files = current_files - last_files
            
            for file in new_files:
                if file.endswith(".safetensors"):
                    await send_msg(f"✨ 새로운 모델 생성 완료: {file}")
            
            last_files = current_files
        
        # 여기서 학습 프로세스가 살아있는지 체크하는 로직 추가 가능 (PID 체크)
        await asyncio.sleep(CHECKPOINT_INTERVAL)

if __name__ == "__main__":
    asyncio.run(monitor_training())
