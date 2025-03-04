from pyrogram import Client
import configparser

# Config Load
config = configparser.ConfigParser()
config.read("config.ini")

BOT_TOKEN = config["TELEGRAM"]["BOT_TOKEN"]
API_ID = config["TELEGRAM"]["API_ID"]
API_HASH = config["TELEGRAM"]["API_HASH"]

bot = Client("AutoForwardBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def get_channel_id(channel_username):
    async with bot:
        try:
            chat = await bot.get_chat(channel_username)
            return chat.id
        except Exception as e:
            return None
