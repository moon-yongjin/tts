import asyncio
import logging
from telegram import Bot
from telegram.error import TelegramError

# [설정]
TELEGRAM_TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def test_connection():
    bot = Bot(token=TELEGRAM_TOKEN)
    try:
        me = await bot.get_me()
        print(f"🤖 봇 연결 성공! 이름: {me.first_name} (@{me.username})")
        return True
    except TelegramError as e:
        print(f"❌ 봇 연결 실패: {e}")
        return False

async def send_message(text):
    bot = Bot(token=TELEGRAM_TOKEN)
    # 유저님의 전용 채팅방 ID를 찾아야 합니다. 일단은 봇에게 메시지를 보낸 이력이 있어야 ID를 딸 수 있습니다.
    try:
        updates = await bot.get_updates()
        if not updates:
            print("⚠️ 봇에게 먼저 메시지를 하나 보내주세요! (채팅방 ID를 찾기 위함)")
            return
        
        # 가장 최근 메시지를 보낸 유저에게 답장하는 방식으로 ID 획득
        chat_id = updates[-1].message.chat_id
        await bot.send_message(chat_id=chat_id, text=text)
        print(f"✅ 메시지 전송 완료! (ID: {chat_id})")
    except Exception as e:
        print(f"❌ 메시지 전송 실패: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
    # asyncio.run(send_message("안녕하세요! LoRA 학습 모니터링 봇입니다. 🤖"))
