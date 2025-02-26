import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from config import TOKEN, MONGO_URI, DB_NAME, ADMIN_ID

bot = telebot.TeleBot(TOKEN)

# Database Setup
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db["users"]
channels = db["channels"]
filters = db["filters"]

# Start Command with Welcome Message
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if users.find_one({"user_id": user_id}) is None:
        users.insert_one({"user_id": user_id})
    
    welcome_text = (
        "✨ *Welcome to Auto-Forward Bot!* ✨\n\n"
        "This bot automatically forwards messages from any channel to your channel, "
        "filters words, and has a broadcasting feature.\n\n"
        "🔹 Use the menu below to get started."
    )
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("➕ Add Channel", callback_data="add_channel"),
        InlineKeyboardButton("📜 Help", callback_data="help"),
        InlineKeyboardButton("📊 Statistics", callback_data="stats")
    )
    
    bot.send_message(user_id, welcome_text, reply_markup=markup, parse_mode="Markdown")

# Help Button
@bot.callback_query_handler(func=lambda call: call.data == "help")
def help_info(call):
    help_text = (
        "📌 *Bot Features:*\n\n"
        "✅ Auto Forward messages from any channel.\n"
        "✅ Add multiple channels for forwarding.\n"
        "✅ Filter & Replace words in forwarded messages.\n"
        "✅ Broadcast messages to all users.\n"
        "✅ Check statistics of users and broadcasts.\n\n"
        "🔹 *Commands:*\n"
        "➖ `/add_channel @channelusername` - Add channel for forwarding\n"
        "➖ `/set_filter badword replacement` - Set a word filter\n"
        "➖ `/broadcast message` - Send a broadcast\n"
        "➖ `/stats` - Check bot statistics\n"
    )
    
    bot.send_message(call.message.chat.id, help_text, parse_mode="Markdown")

# Add Channel for Forwarding
@bot.message_handler(commands=['add_channel'])
def add_channel(message):
    try:
        _, channel_id = message.text.split()
        user_id = message.chat.id
        channels.insert_one({"user_id": user_id, "channel_id": channel_id})
        bot.send_message(user_id, f"✅ Channel {channel_id} added successfully!")
    except:
        bot.send_message(message.chat.id, "❌ Usage: `/add_channel @channelusername`", parse_mode="Markdown")

# Forward Messages
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

# Set Filter Words
@bot.message_handler(commands=['set_filter'])
def set_filter(message):
    try:
        _, word, replacement = message.text.split()
        filters.insert_one({"word": word, "replacement": replacement})
        bot.send_message(message.chat.id, f"✅ Filter set: `{word}` → `{replacement}`", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Usage: `/set_filter badword replacement`", parse_mode="Markdown")

# Broadcast Feature
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.chat.id == ADMIN_ID:  
        text = message.text.replace("/broadcast ", "")
        total_users = users.count_documents({})
        success, failed = 0, 0

        for user in users.find():
            try:
                bot.send_message(user["user_id"], text)
                success += 1
            except:
                failed += 1

        bot.send_message(message.chat.id, f"📢 Broadcast Sent!\n✅ Success: {success}\n❌ Failed: {failed}")

# Statistics
@bot.message_handler(commands=['stats'])
def stats(message):
    total_users = users.count_documents({})
    total_channels = channels.count_documents({})
    bot.send_message(message.chat.id, f"📊 *Bot Statistics:*\n👤 Users: {total_users}\n📡 Channels: {total_channels}", parse_mode="Markdown")

bot.polling()
