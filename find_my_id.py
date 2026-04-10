import asyncio
import sys
from telegram import Bot
from telegram.error import TelegramError

TOKEN = "8515076340:AAHp4TH200xUzO5i9MeSbBSeX9K2hlJbg80"

async def get_chat_id():
    bot = Bot(token=TOKEN)
    print("🛰️ [수신 대기 중] 텔레그램 앱에서 @yongjin_factory_bot 에게 '안녕' 이라고 아무거나 보내주세요...")
    
    # 마지막 업데이트 ID 저장 (새 메시지만 받기 위함)
    last_update_id = 0
    updates = await bot.get_updates(offset=-1)
    if updates:
        last_update_id = updates[0].update_id

    while True:
        try:
            updates = await bot.get_updates(offset=last_update_id + 1, timeout=10)
            for update in updates:
                if update.message:
                    chat_id = update.message.chat_id
                    user_name = update.message.from_user.first_name
                    print(f"\n✨ 연결 성공!")
                    print(f"👤 사용자: {user_name}")
                    print(f"🆔 Chat ID: {chat_id}")
                    print(f"💬 메시지: {update.message.text}")
                    
                    await bot.send_message(chat_id=chat_id, text=f"✅ {user_name}님, 연결에 성공했습니다! 이제 제가 이쪽으로 알림을 보내드릴게요.")
                    return chat_id
            await asyncio.sleep(1)
        except Exception as e:
            print(f"❌ 대기 중 오류: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(get_chat_id())
    except KeyboardInterrupt:
        print("\n👋 종료됨")
