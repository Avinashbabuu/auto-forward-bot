import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from pymongo import MongoClient
from config import TOKEN, MONGO_URI, DB_NAME, ADMIN_ID

bot = telebot.TeleBot(TOKEN)

# Database Setup
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db["users"]
channels = db["channels"]
filters = db["filters"]

# 📌 Reply Keyboard Menu
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Add Channel", "📜 Help")
    markup.add("📝 Manage Filters", "📡 Broadcast")
    markup.add("📊 Statistics")
    return markup

# 🎉 Welcome Message
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if users.find_one({"user_id": user_id}) is None:
        users.insert_one({"user_id": user_id})

    welcome_text = (
        "✨ *Welcome to Auto-Forward Bot!* ✨\n\n"
        "🔹 Use the menu below to get started."
    )
    
    bot.send_message(user_id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

# 📜 Help
@bot.message_handler(func=lambda message: message.text == "📜 Help")
def help_info(message):
    help_text = (
        "📌 *Bot Features:*\n\n"
        "✅ Auto Forward messages.\n"
        "✅ Add multiple channels.\n"
        "✅ Filter & Replace words.\n"
        "✅ Broadcast messages.\n"
        "✅ View user statistics."
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown", reply_markup=main_menu())

# ➕ Add Channel
@bot.message_handler(func=lambda message: message.text == "➕ Add Channel")
def ask_channel(message):
    bot.send_message(message.chat.id, "Send the channel username (Example: `@yourchannel`)", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_channel)

def save_channel(message):
    user_id = message.chat.id
    channel_id = message.text
    channels.insert_one({"user_id": user_id, "channel_id": channel_id})
    bot.send_message(user_id, f"✅ Channel `{channel_id}` added!", parse_mode="Markdown", reply_markup=main_menu())

# 🔍 Manage Filters
@bot.message_handler(func=lambda message: message.text == "📝 Manage Filters")
def manage_filters(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Add Filter", "❌ Remove Filter")
    markup.add("🔙 Back")
    bot.send_message(message.chat.id, "📝 *Manage Filters*", reply_markup=markup, parse_mode="Markdown")

# ➕ Add Filter
@bot.message_handler(func=lambda message: message.text == "➕ Add Filter")
def ask_filter(message):
    bot.send_message(message.chat.id, "Send the word and replacement (Example: `badword goodword`)", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_filter)

def save_filter(message):
    try:
        word, replacement = message.text.split()
        filters.insert_one({"word": word, "replacement": replacement})
        bot.send_message(message.chat.id, f"✅ Filter added: `{word}` → `{replacement}`", parse_mode="Markdown", reply_markup=main_menu())
    except:
        bot.send_message(message.chat.id, "❌ Invalid format! Example: `badword goodword`", parse_mode="Markdown")

# ❌ Remove Filter
@bot.message_handler(func=lambda message: message.text == "❌ Remove Filter")
def remove_filter(message):
    bot.send_message(message.chat.id, "Send the word to remove:", parse_mode="Markdown")
    bot.register_next_step_handler(message, delete_filter)

def delete_filter(message):
    word = message.text
    filters.delete_one({"word": word})
    bot.send_message(message.chat.id, f"✅ Filter `{word}` removed!", parse_mode="Markdown", reply_markup=main_menu())

# 📡 Broadcast Feature
@bot.message_handler(func=lambda message: message.text == "📡 Broadcast")
def ask_broadcast(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "Send the broadcast message:", parse_mode="Markdown")
        bot.register_next_step_handler(message, send_broadcast)

def send_broadcast(message):
    if message.chat.id == ADMIN_ID:
        text = message.text
        total_users = users.count_documents({})
        success, failed = 0, 0

        for user in users.find():
            try:
                bot.send_message(user["user_id"], text)
                success += 1
            except:
                failed += 1

        bot.send_message(message.chat.id, f"📢 Broadcast Sent!\n✅ Success: {success}\n❌ Failed: {failed}", reply_markup=main_menu())

# 📊 Statistics
@bot.message_handler(func=lambda message: message.text == "📊 Statistics")
def stats(message):
    total_users = users.count_documents({})
    total_channels = channels.count_documents({})
    bot.send_message(message.chat.id, f"📊 *Bot Statistics:*\n👤 Users: {total_users}\n📡 Channels: {total_channels}", parse_mode="Markdown", reply_markup=main_menu())

# 🔄 Forward Messages with Filtering
@bot.channel_post_handler()
def forward_messages(message):
    channel_id = message.chat.id
    registered_channels = channels.find({"channel_id": str(channel_id)})

    for entry in registered_channels:
        user_id = entry["user_id"]
        text = message.text
        for word in filters.find():
            text = text.replace(word["word"], word["replacement"])
        bot.send_message(user_id, text)

bot.polling()
