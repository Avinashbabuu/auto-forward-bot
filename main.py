import json
import configparser
from pyrogram import Client, filters
from filters import apply_filters, load_data, save_data
from helpers import get_channel_id
from pyrogram.types import ReplyKeyboardMarkup

# Load config
config = configparser.ConfigParser()
config.read("config.ini")

BOT_TOKEN = config["TELEGRAM"]["BOT_TOKEN"]
API_ID = config["TELEGRAM"]["API_ID"]
API_HASH = config["TELEGRAM"]["API_HASH"]

bot = Client("AutoForwardBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Start Command
@bot.on_message(filters.command("start"))
async def start(bot, message):
    await message.reply_text(
        "**Welcome to Auto Forward Bot!**\n\n"
        "Use the buttons to set up your bot.",
        reply_markup=ReplyKeyboardMarkup(
            [["Set Source", "Set Destination"], ["Start Forwarding", "Stop Forwarding"], ["Add Filter", "Remove Filter"], ["Remove Channel"]],
            resize_keyboard=True
        )
    )

# Set Source Channel
@bot.on_message(filters.text & filters.regex("Set Source"))
async def set_source(bot, message):
    await message.reply_text("Send the Source Channel Username or Link:")
    
    @bot.on_message(filters.text)
    async def source_username(bot, message):
        channel_id = await get_channel_id(message.text)
        if channel_id:
            data = load_data()
            data["source_channel"] = channel_id
            save_data(data)
            await message.reply_text(f"✅ Source Channel Set: `{message.text}` (ID: {channel_id})")
        else:
            await message.reply_text("❌ Invalid Channel Username or Link!")

async def is_admin(bot, chat_id):
    try:
        member = await bot.get_chat_member(chat_id, bot.me.id)
        return member.status in ["administrator", "creator"]
    except Exception as e:
        return False  # Agar error aaye toh assume kare ki bot admin nahi hai

@bot.on_message(filters.text & filters.regex("Set Destination"))
async def set_destination(bot, message):
    await message.reply_text("Send the Destination Channel Username or Link:")
    
    @bot.on_message(filters.text)
    async def destination_username(bot, message):
        channel_id = await get_channel_id(message.text)
        if channel_id:
            if await is_admin(bot, channel_id):  # Check if bot is admin
                data = load_data()
                data["destination_channel"] = channel_id
                save_data(data)
                await message.reply_text(f"✅ Destination Channel Set: `{message.text}` (ID: {channel_id})")
            else:
                await message.reply_text("❌ Bot is not an admin in the destination channel!")
        else:
            await message.reply_text("❌ Invalid Channel Username or Link!")

# Start Forwarding
@bot.on_message(filters.text & filters.regex("Start Forwarding"))
async def start_forwarding(bot, message):
    data = load_data()
    data["forwarding"] = True
    save_data(data)
    await message.reply_text("✅ Forwarding Started!")

# Stop Forwarding
@bot.on_message(filters.text & filters.regex("Stop Forwarding"))
async def stop_forwarding(bot, message):
    data = load_data()
    data["forwarding"] = False
    save_data(data)
    await message.reply_text("❌ Forwarding Stopped!")

# Remove Destination Channel
@bot.on_message(filters.text & filters.regex("Remove Channel"))
async def remove_channel(bot, message):
    data = load_data()
    data.pop("destination_channel", None)
    save_data(data)
    await message.reply_text("✅ Destination Channel Removed!")

# Forward Messages with Filters
@bot.on_message(filters.chat(lambda _, __, message: load_data().get("source_channel") == message.chat.id))
async def forward_message(bot, message):
    data = load_data()
    if data.get("destination_channel") and data.get("forwarding", False):
        filtered_text = apply_filters(message.text)
        await bot.send_message(data["destination_channel"], filtered_text)

# Add Word to Filter
@bot.on_message(filters.text & filters.regex("Add Filter"))
async def add_filter(bot, message):
    await message.reply_text("Send the word to filter:")
    @bot.on_message(filters.text)
    async def filter_word(bot, message):
        data = load_data()
        data["filters"].append(message.text)
        save_data(data)
        await message.reply_text(f"✅ Word Added to Filter: `{message.text}`")

# Remove Word from Filter
@bot.on_message(filters.text & filters.regex("Remove Filter"))
async def remove_filter(bot, message):
    await message.reply_text("Send the word to remove from filter:")
    @bot.on_message(filters.text)
    async def remove_word(bot, message):
        data = load_data()
        if message.text in data["filters"]:
            data["filters"].remove(message.text)
            save_data(data)
            await message.reply_text(f"✅ Word Removed: `{message.text}`")
        else:
            await message.reply_text("❌ Word Not Found in Filters!")

# Run Bot
bot.run()
