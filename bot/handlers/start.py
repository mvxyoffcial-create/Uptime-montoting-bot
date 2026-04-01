from pyrogram import enums
import asyncio
import aiohttp
import random
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import (
    WELCOME_STICKER, WELCOME_IMAGES, ANIME_API,
    START_TXT, GSTART_TXT, ABOUT_TXT, HELP_TXT, OWNER_ID
)
from bot.database.db import add_user, get_user
from bot.filters.fsub import check_fsub


def build_start_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
            InlineKeyboardButton("👾 About", callback_data="about"),
        ],
        [
            InlineKeyboardButton("💎 Premium", callback_data="premium_info"),
            InlineKeyboardButton("📊 My Plan", callback_data="myplan_cb"),
        ],
        [
            InlineKeyboardButton("📢 Channel 1", url="https://t.me/zerodev2"),
            InlineKeyboardButton("📢 Channel 2", url="https://t.me/mvxyoffcail"),
        ],
    ])


async def fetch_anime_image() -> str:
    """Fetch random anime image or fallback to random local images."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ANIME_API, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    for key in ("url", "image", "imageUrl", "img", "link"):
                        if key in data:
                            return data[key]

                    if isinstance(data, str):
                        return data

    except Exception:
        pass

    # 🔥 fallback to random local images
    return random.choice(WELCOME_IMAGES)


def get_random_welcome():
    return random.choice(WELCOME_IMAGES)


def register_start_handlers(app: Client):

    @app.on_message(filters.command("start") & filters.private)
    async def start_private(client: Client, message: Message):
        user = message.from_user

        await add_user(user.id, user.first_name, user.username)

        if not await check_fsub(client, message):
            return

        sticker_msg = await message.reply_sticker(WELCOME_STICKER)
        await asyncio.sleep(2)
        await sticker_msg.delete()

        image_url = await fetch_anime_image()

        greeting = "🌸"
        caption = START_TXT.format(user.first_name, greeting)

        await message.reply_photo(
            photo=image_url,
            caption=caption,
            reply_markup=build_start_buttons(),
            parse_mode=enums.ParseMode.HTML,
        )

    @app.on_message(filters.command("start") & filters.group)
    async def start_group(client: Client, message: Message):
        user = message.from_user
        await add_user(user.id, user.first_name, user.username)

        greeting = "⚡"
        caption = GSTART_TXT.format(user.first_name, greeting)

        await message.reply_photo(
            photo=get_random_welcome(),
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Start in DM", url=f"https://t.me/{(await client.get_me()).username}?start=go")]
            ]),
            parse_mode=enums.ParseMode.HTML,
        )

    @app.on_message(filters.command("help") & filters.private)
    async def help_cmd(client: Client, message: Message):
        if not await check_fsub(client, message):
            return

        await message.reply_photo(
            photo=get_random_welcome(),
            caption=HELP_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="home")]
            ]),
            parse_mode=enums.ParseMode.HTML,
        )

    @app.on_message(filters.command("about") & filters.private)
    async def about_cmd(client: Client, message: Message):
        if not await check_fsub(client, message):
            return

        me = await client.get_me()

        await message.reply_photo(
            photo=get_random_welcome(),
            caption=ABOUT_TXT.format(me.first_name),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="home")]
            ]),
            parse_mode=enums.ParseMode.HTML,
        )

    # ─── Callback Queries ───

    @app.on_callback_query(filters.regex("^check_fsub$"))
    async def check_fsub_cb(client: Client, query: CallbackQuery):
        user_id = query.from_user.id
        not_joined = []

        from config import FSUB_CHANNELS
        for channel in FSUB_CHANNELS:
            try:
                member = await client.get_chat_member(channel, user_id)
                if member.status.value in ("left", "banned", "kicked"):
                    not_joined.append(channel)
            except Exception:
                not_joined.append(channel)

        if not_joined:
            await query.answer("❌ You haven't joined all channels yet!", show_alert=True)
        else:
            await query.answer("✅ Access granted!", show_alert=False)
            await query.message.delete()

            user = query.from_user

            sticker_msg = await client.send_sticker(user_id, WELCOME_STICKER)
            await asyncio.sleep(2)
            await sticker_msg.delete()

            image_url = await fetch_anime_image()

            await client.send_photo(
                user_id,
                photo=image_url,
                caption=START_TXT.format(user.first_name, "🌸"),
                reply_markup=build_start_buttons(),
                parse_mode=enums.ParseMode.HTML,
            )

    @app.on_callback_query(filters.regex("^home$"))
    async def home_cb(client: Client, query: CallbackQuery):
        image_url = await fetch_anime_image()
        user = query.from_user

        await query.message.edit_media(
            media=__import__("pyrogram.types", fromlist=["InputMediaPhoto"]).InputMediaPhoto(
                media=image_url,
                caption=START_TXT.format(user.first_name, "🌸"),
                parse_mode=enums.ParseMode.HTML,
            )
        )

        await query.message.edit_reply_markup(reply_markup=build_start_buttons())

    @app.on_callback_query(filters.regex("^help$"))
    async def help_cb(client: Client, query: CallbackQuery):
        await query.message.edit_caption(
            caption=HELP_TXT,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]]),
            parse_mode=enums.ParseMode.HTML,
        )

    @app.on_callback_query(filters.regex("^about$"))
    async def about_cb(client: Client, query: CallbackQuery):
        me = await client.get_me()

        await query.message.edit_caption(
            caption=ABOUT_TXT.format(me.first_name),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📦 Source Code", url="https://github.com/Venuboyy")],
                [InlineKeyboardButton("🏠 Home", callback_data="home")],
            ]),
            parse_mode=enums.ParseMode.HTML,
        )

    @app.on_callback_query(filters.regex("^myplan_cb$"))
    async def myplan_cb(client: Client, query: CallbackQuery):
        import pytz, datetime
        user = query.from_user
        data = await get_user(user.id)

        IST = pytz.timezone("Asia/Kolkata")

        if data and data.get("expiry_time"):
            expiry = data["expiry_time"]
            expiry_str = expiry.astimezone(IST).strftime("%d-%m-%Y | %I:%M:%S %p")

            now = datetime.datetime.now(IST)
            delta = expiry.astimezone(IST) - now

            days = delta.days
            hours, rem = divmod(delta.seconds, 3600)
            minutes, _ = divmod(rem, 60)

            caption = (
                f"⚜️ <b>ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ᴅᴀᴛᴀ :</b>\n\n"
                f"👤 <b>ᴜꜱᴇʀ :</b> {user.mention}\n"
                f"⚡ <b>ᴜꜱᴇʀ ɪᴅ :</b> <code>{user.id}</code>\n"
                f"⏰ <b>ᴛɪᴍᴇ ʟᴇꜰᴛ :</b> {days}d {hours}h {minutes}m\n"
                f"⌛️ <b>ᴇxᴘɪʀʏ :</b> {expiry_str}"
            )

        else:
            caption = (
                f"<b>ʜᴇʏ {user.mention},\n\n"
                f"ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ.\n"
                f"ʙᴜʏ ᴘʟᴀɴ 🚀</b>"
            )

        await query.message.edit_caption(
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💎 Buy Premium", callback_data="premium_info")],
                [InlineKeyboardButton("🏠 Home", callback_data="home")],
            ]),
            parse_mode=enums.ParseMode.HTML,
        )
