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

# 📌 Reply Keyboard Menu
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Add Source Channel", "❌ Remove Source Channel")
    markup.add("🎯 Set Destination Channel", "❌ Remove Destination Channel")
    markup.add("📡 Broadcast", "📊 Statistics")
    markup.add("📜 Help")
    return markup

# 🎉 Stylish Welcome Message
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if users.find_one({"user_id": user_id}) is None:
        users.insert_one({"user_id": user_id})
    
    welcome_text = (
        "🌟 *Welcome to Auto-Forward Bot!* 🌟\n\n"
        "🚀 _Effortlessly forward messages from any channel to your own!_\n\n"
        "🔹 *Features:*\n"
        "✅ Auto-forward messages without admin access.\n"
        "✅ Add/remove multiple source & destination channels.\n"
        "✅ Broadcast messages to all users.\n"
        "✅ View bot statistics.\n\n"
        "📌 *Use the menu below to navigate.*"
    )
    bot.send_message(user_id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

# 📜 Stylish Help Message
@bot.message_handler(func=lambda message: message.text == "📜 Help")
def help_info(message):
    help_text = (
        "📌 *Bot Features & Guide:*\n\n"
        "🔹 *Add Source Channel* → Forward messages from a channel.\n"
        "🔹 *Remove Source Channel* → Stop forwarding from a channel.\n"
        "🔹 *Set Destination Channel* → Select where messages will be sent.\n"
        "🔹 *Remove Destination Channel* → Stop sending messages to a channel.\n"
        "🔹 *Broadcast* → Send a message to all bot users.\n"
        "🔹 *Statistics* → View the number of users & channels.\n\n"
        "💡 *Navigation is easy!* Use the buttons below."
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown", reply_markup=main_menu())

# ➕ Add Source Channel
@bot.message_handler(func=lambda message: message.text == "➕ Add Source Channel")
def ask_source_channel(message):
    bot.send_message(message.chat.id, "📥 *Send the source channel username* (Example: `@sourcechannel`)", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_source_channel)

def save_source_channel(message):
    user_id = message.chat.id
    channel_id = message.text
    channels.insert_one({"user_id": user_id, "channel_id": channel_id, "type": "source"})
    bot.send_message(user_id, f"✅ *Source Channel `{channel_id}` added!*", parse_mode="Markdown", reply_markup=main_menu())

# ❌ Remove Source Channel
@bot.message_handler(func=lambda message: message.text == "❌ Remove Source Channel")
def ask_remove_source_channel(message):
    bot.send_message(message.chat.id, "📤 *Send the source channel username to remove:*", parse_mode="Markdown")
    bot.register_next_step_handler(message, remove_source_channel)

def remove_source_channel(message):
    user_id = message.chat.id
    channel_id = message.text
    result = channels.delete_one({"user_id": user_id, "channel_id": channel_id, "type": "source"})

    if result.deleted_count > 0:
        bot.send_message(user_id, f"❌ *Source Channel `{channel_id}` removed!*", parse_mode="Markdown", reply_markup=main_menu())
    else:
        bot.send_message(user_id, "❌ *Source Channel not found!*", parse_mode="Markdown")

# 🎯 Set Destination Channel
@bot.message_handler(func=lambda message: message.text == "🎯 Set Destination Channel")
def ask_destination_channel(message):
    bot.send_message(message.chat.id, "📥 *Send the destination channel username* (Example: `@yourdestination`)", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_destination_channel)

def save_destination_channel(message):
    user_id = message.chat.id
    channel_id = message.text
    channels.update_one({"user_id": user_id, "type": "destination"}, {"$set": {"channel_id": channel_id}}, upsert=True)
    bot.send_message(user_id, f"✅ *Destination Channel set to `{channel_id}`!*", parse_mode="Markdown", reply_markup=main_menu())

# ❌ Remove Destination Channel
@bot.message_handler(func=lambda message: message.text == "❌ Remove Destination Channel")
def remove_destination_channel(message):
    user_id = message.chat.id
    result = channels.delete_one({"user_id": user_id, "type": "destination"})

    if result.deleted_count > 0:
        bot.send_message(user_id, "❌ *Destination Channel removed!*", parse_mode="Markdown", reply_markup=main_menu())
    else:
        bot.send_message(user_id, "❌ *No Destination Channel found!*", parse_mode="Markdown")

# 📡 Broadcast Feature
@bot.message_handler(func=lambda message: message.text == "📡 Broadcast")
def ask_broadcast(message):
    if message.chat.id == ADMIN_ID:
        bot.send_message(message.chat.id, "📢 *Send the broadcast message:*", parse_mode="Markdown")
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

        bot.send_message(message.chat.id, f"📢 *Broadcast Sent!*\n✅ Success: {success}\n❌ Failed: {failed}", reply_markup=main_menu())

# 📊 Statistics
@bot.message_handler(func=lambda message: message.text == "📊 Statistics")
def stats(message):
    total_users = users.count_documents({})
    total_channels = channels.count_documents({})
    bot.send_message(message.chat.id, f"📊 *Bot Statistics:*\n👤 Users: {total_users}\n📡 Channels: {total_channels}", parse_mode="Markdown", reply_markup=main_menu())

# 🔄 Forward Messages from Source to Destination
@bot.channel_post_handler()
def forward_messages(message):
    source_channels = [entry["channel_id"] for entry in channels.find({"type": "source"})]
    destination_channel = channels.find_one({"type": "destination"})

    if message.chat.username in source_channels and destination_channel:
        try:
            bot.copy_message(destination_channel["channel_id"], message.chat.id, message.message_id)
        except Exception as e:
            print(f"Error forwarding message: {e}")

bot.polling()
