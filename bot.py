import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatJoinRequest
import os
from flyerapi import Flyer

# ────────────────────────────────────────────────
#                НАСТРОЙКИ
# ────────────────────────────────────────────────

BOT_TOKEN = os.getenv('BOT_TOKEN', '8539310713:AAHZm9V13F-rNyga2Jo5lV_VJYbwr9tMpiI')
FLYER_KEY  = os.getenv('FLYER_KEY',  'FL-QimvUK-noxElI-hXeODH-EhLLMN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID', '-1003013802890'))

# ────────────────────────────────────────────────

bot = telebot.TeleBot(BOT_TOKEN)
flyer = Flyer(FLYER_KEY)

def is_subscribed(user_id):
    try:
        result = flyer.check(user_id)
        print(f"[FLYER] user={user_id} → {result}")
        
        # Возможные варианты возвращаемого значения
        if isinstance(result, bool):
            return result
        elif isinstance(result, dict):
            return result.get('skip', False) or result.get('success', False) or result.get('subscribed', False)
        else:
            return False
    except Exception as e:
        print(f"[FLYER ERROR] {e}")
        return False


def send_welcome_with_check(user_id, message_id=None):
    if is_subscribed(user_id):
        text = "Привет! Подписка проверена — добро пожаловать в канал 🎉"
        markup = None
    else:
        text = "Привет! Чтобы попасть в канал, нужно подписаться на обязательные каналы.\n\nПосле подписки нажми кнопку ниже."
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(InlineKeyboardButton("Проверить подписку ✅", callback_data=f"check_{user_id}"))
    
    try:
        if message_id:
            bot.edit_message_text(
                text=text,
                chat_id=user_id,
                message_id=message_id,
                reply_markup=markup
            )
        else:
            bot.send_message(user_id, text, reply_markup=markup)
    except telebot.apihelper.ApiTelegramException as e:
        if "message is not modified" in str(e).lower():
            print("[TG] Сообщение не изменилось — пропускаем")
        else:
            print(f"[TG EDIT ERROR] {e}")
            # На всякий случай новое сообщение
            bot.send_message(user_id, text, reply_markup=markup)


@bot.chat_join_request_handler()
def on_join_request(join_request: ChatJoinRequest):
    user_id = join_request.from_user.id
    username = join_request.from_user.username or join_request.from_user.first_name
    print(f"[JOIN REQUEST] @{username} (id={user_id})")
    
    send_welcome_with_check(user_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('check_'))
def on_check_button(call):
    user_id = int(call.data.split('_')[1])
    print(f"[CHECK PRESSED] user={user_id}")
    
    send_welcome_with_check(user_id, call.message.message_id)
    
    if is_subscribed(user_id):
        bot.answer_callback_query(call.id, "Подписка пройдена! Добро пожаловать.", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "Ещё не все каналы подписаны. Подпишитесь и попробуйте снова.", show_alert=True)


if __name__ == '__main__':
    print("Привет-бот запущен — Flyer check + приветствие")
    bot.infinity_polling(
        allowed_updates=['chat_join_request', 'callback_query'],
        timeout=20
    )
