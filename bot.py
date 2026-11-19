import os
import telebot
import sqlite3
import datetime

# Токен от BotFather
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Норма сообщений в неделю
WEEKLY_NORM = 150
WARN_THRESHOLD = 100  # Порог для варна

# Настройка базы данных
DB_NAME = 'chat_stats.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages 
                 (user_id INTEGER, user_name TEXT, date TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Функция для вычисления периода: последние 7 дней
def get_week_period():
    now = datetime.datetime.now()
    start_date = now - datetime.timedelta(days=7)
    return start_date, now

# Обработка всех текстовых сообщений в чате
@bot.message_handler(content_types=['text'])
def handle_message(message):
    if message.chat.type in ['group', 'supergroup']:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        user_name = message.from_user.first_name
        if message.from_user.last_name:
            user_name += " " + message.from_user.last_name
            
        c.execute("INSERT INTO messages (user_id, user_name, date) VALUES (?, ?, ?)",
                  (message.from_user.id, user_name, datetime.datetime.now()))
        conn.commit()
        conn.close()

# Команда для проверки статистики
@bot.message_handler(commands=['stats'])
def send_stats(message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    start_date, end_date = get_week_period()
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Считаем сообщения за последние 7 дней
    c.execute("SELECT COUNT(*) FROM messages WHERE user_id = ? AND date BETWEEN ? AND ?",
              (user_id, start_date, end_date))
    count = c.fetchone()[0]
    
    conn.close()
    
    # Формируем текст ответа
    response_text = f"👋 Привет, {user_name}!\n\n"
    response_text += f"📊 *Твоя статистика за последние 7 дней:*\n"
    response_text += f"Сообщений: *{count}*\n\n"
    response_text += f"📌 *Норма в чате:* {WEEKLY_NORM} сообщений в неделю\n\n"
    response_text += f"⚠️ *Правило варна:*\n"
    response_text += f"Если к воскресенью количество сообщений меньше {WARN_THRESHOLD}, "
    response_text += f"то выдается варн, так как в день чистки много добирать нельзя.\n\n"
    response_text += f"💬 Общаемся охотнее, друзья! 🤗"
    
    bot.reply_to(message, response_text, parse_mode='Markdown')

if __name__ == '__main__':
    print("Бот запущен...")
    bot.infinity_polling()
