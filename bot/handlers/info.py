from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from bot.filters.fsub import check_fsub


def register_info_handler(app: Client):

    @app.on_message(filters.command("info") & filters.private)
    async def info_cmd(client: Client, message: Message):
        if not await check_fsub(client, message):
            return

        user = message.from_user

        first_name = user.first_name or "None"
        last_name = user.last_name or "None"
        user_id = user.id
        username = f"@{user.username}" if user.username else "None"
        user_link = f"<a href='tg://user?id={user_id}'>Click Here</a>"

        # Get DC ID
        try:
            full = await client.get_chat(user_id)
            dc_id = getattr(full, "dc_id", "Unknown")
        except Exception:
            dc_id = "Unknown"

        caption = (
            f"➲<b>First Name:</b> {first_name}\n"
            f"➲<b>Last Name:</b> {last_name}\n"
            f"➲<b>Telegram ID:</b> <code>{user_id}</code>\n\n"
            f"➲<b>Data Centre:</b> {dc_id}\n\n"
            f"➲<b>User Name:</b> {username}\n"
            f"➲<b>User Link:</b> {user_link}"
        )

        # Try to get profile photo
        try:
            photos = await client.get_profile_photos(user_id, limit=1)
            if photos:
                await message.reply_photo(
                    photo=photos[0].file_id,
                    caption=caption,
                    parse_mode="html",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("👤 Profile", url=f"tg://user?id={user_id}")]
                    ])
                )
                return
        except Exception:
            pass

        # No profile photo fallback
        await message.reply(
            caption,
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("👤 Profile", url=f"tg://user?id={user_id}")]
            ])
        )
