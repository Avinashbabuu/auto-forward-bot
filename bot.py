import telebot
from pymongo import MongoClient
from config import TOKEN, MONGO_URI, DB_NAME

bot = telebot.TeleBot(TOKEN)

# Database Setup
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users = db["users"]
channels = db["channels"]
filters = db["filters"]

# User Registration
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if users.find_one({"user_id": user_id}) is None:
        users.insert_one({"user_id": user_id})
    bot.send_message(user_id, "Welcome to the Auto Forward Bot!")

# Add Channel for Forwarding
@bot.message_handler(commands=['add_channel'])
def add_channel(message):
    try:
        _, channel_id = message.text.split()
        user_id = message.chat.id
        channels.insert_one({"user_id": user_id, "channel_id": channel_id})
        bot.send_message(user_id, f"Channel {channel_id} added successfully!")
    except:
        bot.send_message(message.chat.id, "Usage: /add_channel @channelusername")

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

# Broadcast Feature
@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.chat.id == YOUR_ADMIN_ID:  # Replace with your ID
        text = message.text.replace("/broadcast ", "")
        total_users = users.count_documents({})
        success, failed = 0, 0

        for user in users.find():
            try:
                bot.send_message(user["user_id"], text)
                success += 1
            except:
                failed += 1

        bot.send_message(message.chat.id, f"Broadcast Sent!\nSuccess: {success}\nFailed: {failed}")

bot.polling()
