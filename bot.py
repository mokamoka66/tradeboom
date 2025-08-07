import telebot
from telebot import types
import sqlite3
import time
from datetime import datetime, timedelta

# Your provided data
TOKEN = "8284508405:AAFZS2a1HCcumV9Sq8zbEDIhfcDQsteCPGQ"
CHANNEL_ID = "@TRADEBOOM"  # Or numeric channel ID if private
WALLET_ADDRESS = "TMhsVFZS2Dy1GXDScJsWiYDrQgXeyKZJUc"
PRICE = 29  # $29
DAYS = 3  # 3 days
ADMIN_ID = YOUR_ADMIN_ID_HERE  # Replace with your Telegram ID

bot = telebot.TeleBot(TOKEN)

# Database setup
conn = sqlite3.connect('tradeboom.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS subscribers
             (user_id INTEGER PRIMARY KEY, 
             join_date TEXT, 
             expiry_date TEXT,
             paid INTEGER DEFAULT 0)''')
conn.commit()

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    c.execute("SELECT * FROM subscribers WHERE user_id=?", (user_id,))
    user = c.fetchone()
    
    if user and datetime.now() < datetime.strptime(user[2], '%Y-%m-%d %H:%M:%S') and user[3] == 1:
        bot.reply_to(message, "✅ Your TRADE&BOOM subscription is active!")
    else:
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("💳 Subscribe Now", callback_data="pay")
        markup.add(btn)
        
        bot.send_message(message.chat.id, 
                        f"""🚀 **Welcome to TRADE&BOOM** 🚀

💰 Subscription price: {PRICE}$ 
⏳ Duration: {DAYS} days

To access premium channel content, please subscribe using the button below:""",
                        reply_markup=markup,
                        parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == "pay")
def payment_request(call):
    bot.send_message(call.message.chat.id,
                    f"""⚡ **Complete Payment** ⚡

Please transfer {PRICE}$ USDT (TRC20) to the following address:

`{WALLET_ADDRESS}`

📌 **Important notes**:
1. Use only TRC20 network
2. Send payment receipt after transfer
3. You'll receive confirmation within 24 hours""",
                    parse_mode='Markdown')

@bot.message_handler(content_types=['text', 'photo', 'document'])
def confirm_payment(message):
    if message.photo or ('usdt' in message.text.lower() or 'trc20' in message.text.lower()):
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)  # Forward receipt to admin
        bot.reply_to(message, "Payment receipt received, under review...")

def check_expired_subs():
    while True:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute("SELECT user_id FROM subscribers WHERE expiry_date < ? AND paid = 1", (now,))
        expired = c.fetchall()
        
        for user in expired:
            try:
                bot.restrict_chat_member(CHANNEL_ID, user[0], 
                                       permissions=types.ChatPermissions(
                                           can_send_messages=False,
                                           can_send_media_messages=False,
                                           can_send_other_messages=False))
                bot.send_message(user[0], "Your TRADE&BOOM subscription has expired. Renew with /start")
            except Exception as e:
                print(f"Error: {e}")
        
        time.sleep(3600)  # Check every hour

if __name__ == '__main__':
    import threading
    threading.Thread(target=check_expired_subs).start()
    bot.polling()