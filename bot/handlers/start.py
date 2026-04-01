import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import (
    WELCOME_STICKER, WELCOME_IMAGE, ANIME_API,
    START_TXT, GSTART_TXT, ABOUT_TXT, HELP_TXT, OWNER_ID
)
from bot.database.db import add_user, get_user
from bot.filters.fsub import check_fsub


def build_start_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 My URLs", callback_data="my_urls"),
            InlineKeyboardButton("➕ Add URL", callback_data="add_url_prompt"),
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="help"),
            InlineKeyboardButton("👾 About", callback_data="about"),
        ],
        [
            InlineKeyboardButton("📢 Channel 1", url="https://t.me/zerodev2"),
            InlineKeyboardButton("📢 Channel 2", url="https://t.me/mvxyoffcail"),
        ],
    ])


async def fetch_anime_image() -> str:
    """Fetch random anime girl wallpaper URL from API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(ANIME_API, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Try common response keys
                    for key in ("url", "image", "imageUrl", "img", "link"):
                        if key in data:
                            return data[key]
                    # If direct URL string
                    if isinstance(data, str):
                        return data
    except Exception:
        pass
    return WELCOME_IMAGE  # Fallback to static image


def register_start_handlers(app: Client):

    @app.on_message(filters.command("start") & filters.private)
    async def start_private(client: Client, message: Message):
        user = message.from_user

        # Save user to DB
        await add_user(user.id, user.first_name, user.username)

        # Force subscribe check
        if not await check_fsub(client, message):
            return

        # Send animated sticker
        sticker_msg = await message.reply_sticker(WELCOME_STICKER)

        # Wait 2 seconds then delete sticker
        await asyncio.sleep(2)
        await sticker_msg.delete()

        # Fetch anime image
        image_url = await fetch_anime_image()

        greeting = f"{'🌸'}"
        caption = START_TXT.format(user.first_name, greeting)

        await message.reply_photo(
            photo=image_url,
            caption=caption,
            reply_markup=build_start_buttons(),
            parse_mode="html",
        )

    @app.on_message(filters.command("start") & filters.group)
    async def start_group(client: Client, message: Message):
        user = message.from_user
        await add_user(user.id, user.first_name, user.username)

        greeting = "⚡"
        caption = GSTART_TXT.format(user.first_name, greeting)

        await message.reply_photo(
            photo=WELCOME_IMAGE,
            caption=caption,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Start in DM", url=f"https://t.me/{(await client.get_me()).username}?start=go")]
            ]),
            parse_mode="html",
        )

    @app.on_message(filters.command("help") & filters.private)
    async def help_cmd(client: Client, message: Message):
        if not await check_fsub(client, message):
            return
        await message.reply_photo(
            photo=WELCOME_IMAGE,
            caption=HELP_TXT,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="home")]
            ]),
            parse_mode="html",
        )

    @app.on_message(filters.command("about") & filters.private)
    async def about_cmd(client: Client, message: Message):
        if not await check_fsub(client, message):
            return
        me = await client.get_me()
        await message.reply_photo(
            photo=WELCOME_IMAGE,
            caption=ABOUT_TXT.format(me.first_name),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Home", callback_data="home")]
            ]),
            parse_mode="html",
        )

    # ─── Callback Queries ───

    @app.on_callback_query(filters.regex("^check_fsub$"))
    async def check_fsub_cb(client: Client, query: CallbackQuery):
        from bot.filters.fsub import check_fsub as _check
        # Re-check by simulating message
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
            await query.answer("✅ Access granted! Sending welcome...", show_alert=False)
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
                parse_mode="html",
            )

    @app.on_callback_query(filters.regex("^home$"))
    async def home_cb(client: Client, query: CallbackQuery):
        image_url = await fetch_anime_image()
        user = query.from_user
        await query.message.edit_media(
            media=__import__("pyrogram.types", fromlist=["InputMediaPhoto"]).InputMediaPhoto(
                media=image_url,
                caption=START_TXT.format(user.first_name, "🌸"),
                parse_mode="html",
            )
        )
        await query.message.edit_reply_markup(reply_markup=build_start_buttons())

    @app.on_callback_query(filters.regex("^help$"))
    async def help_cb(client: Client, query: CallbackQuery):
        await query.message.edit_caption(
            caption=HELP_TXT,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]]),
            parse_mode="html",
        )

    @app.on_callback_query(filters.regex("^about$"))
    async def about_cb(client: Client, query: CallbackQuery):
        me = await client.get_me()
        await query.message.edit_caption(
            caption=ABOUT_TXT.format(me.first_name),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]]),
            parse_mode="html",
        )
