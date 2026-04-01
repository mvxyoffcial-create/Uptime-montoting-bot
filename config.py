import os
from dotenv import load_dotenv

load_dotenv()

# Bot credentials
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# MongoDB
MONGO_URI = os.environ.get("MONGO_URI", "")
DB_NAME = os.environ.get("DB_NAME", "MvxyUptimeBot")

# Admin
OWNER_ID = int(os.environ.get("OWNER_ID", 0))  # @Venuboyy

# Admin list (supports multiple admins)
_admin_ids = os.environ.get("ADMINS", str(os.environ.get("OWNER_ID", 0)))
ADMINS = [int(x.strip()) for x in _admin_ids.split(",") if x.strip().isdigit()]

# Premium logs channel (group/channel ID where premium actions are logged)
PREMIUM_LOGS = int(os.environ.get("PREMIUM_LOGS", 0)) or None

# Telegram Star premium plans: {stars: "duration_string"}
# Duration strings are parsed by get_seconds() in utils.py
STAR_PREMIUM_PLANS = {
    50:  "1 month",
    100: "3 month",
    200: "6 month",
    350: "1 year",
}

# Premium subscription image
SUBSCRIPTION_IMG = "https://i.ibb.co/gMrpRQWP/photo-2025-07-09-05-21-32-7524948058832896004.jpg"

# Force Subscribe Channels
FSUB_CHANNELS = [
    "@zerodev2",
    "@mvxyoffcail"
]

# Worker count
WORKERS = 500

# Welcome sticker
WELCOME_STICKER = "CAACAgIAAxkBAAEQZtFpgEdROhGouBVFD3e0K-YjmVHwsgACtCMAAphLKUjeub7NKlvk2TgE"

# Welcome image
WELCOME_IMAGE = [
    "https://i.ibb.co/Xf95qxtr/img-8108646188.jpg",
    "https://i.ibb.co/xthjWvZm/img-8108646188.jpg",
    "https://i.ibb.co/B2FZVtCT/img-8108646188.jpg"
]

# Anime wallpaper API (random girl wallpaper)
ANIME_API = "https://api.aniwallpaper.workers.dev/random?type=girl"

# Free user limit
FREE_LIMIT = 5

# Bot info strings
START_TXT = """<b>ʜᴇʏ, {}! {}</b>

ɪ'ᴍ ᴀɴ <b>ᴜᴘᴛɪᴍᴇ ᴍᴏɴɪᴛᴏʀɪɴɢ ʙᴏᴛ</b> ⏱️
ɪ ᴄᴀɴ ᴋᴇᴇᴘ ʏᴏᴜʀ ʙᴏᴛs ᴀɴᴅ ᴡᴇʙsɪᴛᴇs ᴀʟɪᴠᴇ 24/7 🌐

ᴊᴜsᴛ sᴇɴᴅ ᴍᴇ ʏᴏᴜʀ ʟɪɴᴋ — ᴀɴᴅ ɪ'ʟʟ ᴍᴏɴɪᴛᴏʀ ɪᴛ ғᴏʀ ʏᴏᴜ! 🚀"""

GSTART_TXT = """<b>ʜᴇʏ, {}! {}</b>

ɪ'ᴍ ᴀ ᴘᴏᴡᴇʀғᴜʟ <b>ᴜᴘᴛɪᴍᴇ ᴍᴏɴɪᴛᴏʀ</b> 🤖
ɪ ᴄᴀɴ ᴋᴇᴇᴘ ʙᴏᴛs ᴀɴᴅ ᴡᴇʙsɪᴛᴇs ᴏɴʟɪɴᴇ ᴀʟʟ ᴛʜᴇ ᴛɪᴍᴇ ⚡
ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴏʀ sᴇɴᴅ ᴀ ʟɪɴᴋ ᴛᴏ sᴛᴀʀᴛ 🔗"""

HELP_TXT = """<b>✨ ʜᴏᴡ ᴛᴏ ᴜsᴇ ᴜᴘᴛɪᴍᴇ ᴍᴏɴɪᴛᴏʀ ✨</b>

1️⃣ <b>sᴇɴᴅ ᴀ ʟɪɴᴋ:</b> sᴇɴᴅ ᴀɴʏ ᴡᴇʙsɪᴛᴇ ᴏʀ ʙᴏᴛ ᴜʀʟ 🌐  
2️⃣ <b>sᴛᴀʀᴛ ᴍᴏɴɪᴛᴏʀɪɴɢ:</b> ɪ ᴡɪʟʟ ᴋᴇᴇᴘ ɪᴛ ᴀʟɪᴠᴇ 🔄  
3️⃣ <b>ᴀᴜᴛᴏ ᴘɪɴɢ:</b> ɪ ᴘɪɴɢ ʏᴏᴜʀ sɪᴛᴇ ᴇᴠᴇʀʏ ғᴇᴡ ᴍɪɴᴜᴛᴇs ⏱️  
4️⃣ <b>sᴛᴀᴛᴜs:</b> ɢᴇᴛ ᴜᴘᴛɪᴍᴇ sᴛᴀᴛᴜs ᴀɴʏᴛɪᴍᴇ 📊  

📌 <b>ғᴇᴀᴛᴜʀᴇs:</b>
➤ 24/7 ᴜᴘᴛɪᴍᴇ ᴍᴏɴɪᴛᴏʀɪɴɢ 🌍  
➤ ᴀᴜᴛᴏ ᴘɪɴɢ sʏsᴛᴇᴍ 🔄  
➤ ғᴀsᴛ ᴀɴᴅ ʀᴇʟɪᴀʙʟᴇ ⚡  
➤ sᴇᴄᴜʀᴇ & ᴘʀɪᴠᴀᴛᴇ 🔒  

<b>🚀 sᴛᴀʀᴛ ᴍᴏɴɪᴛᴏʀɪɴɢ ɴᴏᴡ!</b>"""

ABOUT_TXT = """<b>╭────[ ᴍʏ ᴅᴇᴛᴀɪʟs ]────⍟ 

├⍟ Mʏ Nᴀᴍᴇ : {}
├⍟ Dᴇᴠᴇʟᴏᴘᴇʀ : <a href='https://t.me/Venuboyy'>ᴠᴇɴᴜʙᴏʏʏ</a> 👨‍💻
├⍟ Lɪʙʀᴀʀʏ : <a href='https://github.com/pyrogram/pyrogram'>ᴘʏʀᴏɢʀᴀᴍ</a> 📚
├⍟ Lᴀɴɢᴜᴀɢᴇ : <a href='https://www.python.org/'>ᴘʏᴛʜᴏɴ 𝟹</a> 🐍
├⍟ Dᴀᴛᴀʙᴀsᴇ : <a href='https://www.mongodb.com/'>ᴍᴏɴɢᴏ ᴅʙ</a> 🍃
├⍟ Bᴏᴛ Sᴇʀᴠᴇʀ : <a href='https://dashboard.heroku.com/'>ʜᴇʀᴏᴋᴜ</a> ☁️
├⍟ Fᴇᴀᴛᴜʀᴇ : ᴜᴘᴛɪᴍᴇ ᴍᴏɴɪᴛᴏʀɪɴɢ ⏱️
├⍟ Bᴜɪʟᴅ Sᴛᴀᴛᴜs : ᴠ𝟸.𝟶 [ ᴜʟᴛʀᴀ ] 🚀
├⍟ Oᴡɴᴇʀ : <a href='https://t.me/Venuboyy'>@Venuboyy</a> 👑
╰───────────────⍟</b>"""
