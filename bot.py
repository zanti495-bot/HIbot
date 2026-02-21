import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatJoinRequest
import requests
import json
import traceback

# Твои данные
BOT_TOKEN = '8539310713:AAHZm9V13F-rNyga2Jo5lV_VJYbwr9tMpiI'
SUBGRAM_API_KEY = '48d15f529d10ac12165349a2c5325e06dec90cfed1b3a39466f80036c1671fe6'
CHANNEL_ID = -1003013802890

SUBGRAM_URL = 'https://api.subgram.org/get-sponsors'

bot = telebot.TeleBot(BOT_TOKEN)

def check_subscription(user_id):
    headers = {
        'Auth': SUBGRAM_API_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        'user_id': user_id,
        'chat_id': CHANNEL_ID,
        'get_links': 1,
        'language_code': 'ru',
    }
    
    try:
        print(f"[DEBUG] Запрос SubGram → user={user_id} chat={CHANNEL_ID}")
        response = requests.post(SUBGRAM_URL, headers=headers, json=data, timeout=10)
        
        print(f"[DEBUG] Статус: {response.status_code} | Ответ: {response.text}")
        
        if response.status_code != 200:
            return False, []
        
        result = response.json()
        status = result.get('status')
        
        if status == 'ok':
            return True, []
        elif status == 'warning':
            sponsors = result.get('additional', {}).get('sponsors', [])
            return False, sponsors
        else:
            return False, []
            
    except Exception as e:
        print(f"[ERROR SubGram] {str(e)}")
        traceback.print_exc()
        return False, []

# Новый обработчик — именно для заявок на вступление
@bot.chat_join_request_handler()
def handle_join_request(join_request: ChatJoinRequest):
    try:
        user = join_request.from_user
        user_id = user.id
        username = user.username or user.first_name
        chat_id = join_request.chat.id
        
        print(f"[JOIN REQUEST] Поступила заявка от @{username} (id={user_id}) в канал {chat_id}")
        
        is_subscribed, sponsors = check_subscription(user_id)
        
        if is_subscribed:
            print(f"[OK] {user_id} уже подписан на всё → пишем приветствие")
            bot.send_message(
                user_id,
                "Вы подписаны на все необходимые каналы. Заявка отправлена администратору на одобрение!"
            )
        else:
            print(f"[NEED SUB] {user_id} — требуется подписка на {len(sponsors)} каналов")
            markup = InlineKeyboardMarkup(row_width=1)
            
            for sp in sponsors:
                text = sp.get('button_text', f"Подписаться на {sp.get('resource_name', 'канал')}")
                link = sp.get('link')
                if link:
                    markup.add(InlineKeyboardButton(text, url=link))
            
            markup.add(InlineKeyboardButton(
                "Я ответил ✅",
                callback_data=f"check_{user_id}"
            ))
            
            bot.send_message(
                user_id,
                "Чтобы получить рецепт, ответьте всего на пару вопросов!\n\n"
                "После ответа нажмите кнопку ниже — я отправлю вам рецепт.",
                reply_markup=markup
            )
            
    except Exception as e:
        print(f"[CRASH в join_request] {str(e)}")
        traceback.print_exc()

# Обработчик проверки (callback)
@bot.callback_query_handler(func=lambda call: call.data.startswith('check_'))
def handle_check(call):
    try:
        user_id = int(call.data.split('_')[1])
        print(f"[CHECK] Пользователь {call.from_user.id} нажал проверить (для {user_id})")
        
        is_sub, _ = check_subscription(user_id)
        
        if is_sub:
            bot.edit_message_text(
                "Подписка подтверждена! Теперь ждите, администратор одобрит заявку.",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id
            )
            bot.answer_callback_query(call.id, "Всё хорошо!")
        else:
            bot.answer_callback_query(call.id, "Ещё не все каналы. Подпишитесь и нажмите снова.", show_alert=True)
            
    except Exception as e:
        print(f"[CALLBACK ERROR] {str(e)}")
        bot.answer_callback_query(call.id, "Ошибка. Попробуйте позже.")

# Для теста от админа
@bot.message_handler(commands=['testsub'])
def test(message):
    if message.from_user.id == 7656060949:
        is_ok, spons = check_subscription(message.from_user.id)
        text = f"Тест SubGram API:\nПодписан: {is_ok}\nСпонсоров: {len(spons)}\n\n{json.dumps(spons, indent=2, ensure_ascii=False)}"
        bot.reply_to(message, text)

# Запуск с нужными allowed_updates
if __name__ == '__main__':
    print(f"Бот запущен | CHANNEL={CHANNEL_ID} | API_KEY (начало): {SUBGRAM_API_KEY[:8]}...")
    print("Ожидаю заявки (chat_join_request)...")
    bot.infinity_polling(
        allowed_updates=['chat_join_request', 'callback_query', 'message'],
        timeout=20,
        long_polling_timeout=10
    )
