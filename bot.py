import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flyerapi import Flyer
import os

# ────────────────────────────────────────────────
BOT_TOKEN = os.getenv('BOT_TOKEN', '8539310713:AAHZm9V13F-rNyga2Jo5lV_VJYbwr9tMpiI')
FLYER_KEY  = os.getenv('FLYER_KEY',  'FL-QimvUK-noxElI-hXeODH-EhLLMN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1003013802890'))
# ────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
flyer = Flyer(FLYER_KEY)

async def is_subscribed(user_id: int) -> bool:
    try:
        result = await flyer.check(user_id)  # ← await здесь!
        logging.info(f"[FLYER] user={user_id} → {result}")
        
        if isinstance(result, bool):
            return result
        elif isinstance(result, dict):
            return result.get('skip', False) or result.get('success', False)
        return False
    except Exception as e:
        logging.error(f"[FLYER ERROR] {e}")
        return False

async def send_prompt(user_id: int, message_id: int | None = None):
    if await is_subscribed(user_id):
        text = "Привет! Подписка активна — добро пожаловать в канал 🎉"
        markup = None
    else:
        text = "Привет! Чтобы присоединиться, подпишись на обязательные каналы.\nНажми ниже после подписки."
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Проверить подписку ✅", callback_data=f"check_{user_id}")]
        ])
    
    try:
        if message_id:
            await bot.edit_message_text(
                text=text,
                chat_id=user_id,
                message_id=message_id,
                reply_markup=markup
            )
        else:
            await bot.send_message(user_id, text, reply_markup=markup)
    except Exception as e:
        if "message is not modified" in str(e).lower():
            logging.info("[TG] Сообщение не изменилось")
        else:
            logging.error(f"[TG ERROR] {e}")
            await bot.send_message(user_id, text, reply_markup=markup)

@dp.chat_join_request()
async def on_join_request(join: types.ChatJoinRequest):
    user_id = join.from_user.id
    username = join.from_user.username or join.from_user.first_name
    logging.info(f"[JOIN REQUEST] @{username} (id={user_id})")
    
    await send_prompt(user_id)

@dp.callback_query(lambda c: c.data.startswith('check_'))
async def on_check(callback: types.CallbackQuery):
    user_id = int(callback.data.split('_')[1])
    logging.info(f"[CHECK PRESSED] user={user_id}")
    
    await send_prompt(user_id, callback.message.message_id)
    
    if await is_subscribed(user_id):
        await callback.answer("Подписка пройдена! Заходи.", show_alert=True)
    else:
        await callback.answer("Ещё не все каналы. Подпишись и повтори.", show_alert=True)

async def main():
    logging.info("Привет-бот запущен — Flyer + async")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=['chat_join_request', 'callback_query'])

if __name__ == '__main__':
    asyncio.run(main())
