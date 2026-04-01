from pyrogram import enums
from pyrogram import Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import FSUB_CHANNELS, OWNER_ID


async def check_fsub(client: Client, message: Message) -> bool:
    """Returns True if user is subscribed to all required channels."""
    user_id = message.from_user.id

    # Owner always passes
    if user_id == OWNER_ID:
        return True

    not_joined = []
    for channel in FSUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status.value in ("left", "banned", "kicked"):
                not_joined.append(channel)
        except Exception:
            not_joined.append(channel)

    if not_joined:
        buttons = []
        for ch in not_joined:
            name = ch.replace("@", "")
            buttons.append([InlineKeyboardButton(f"📢 Join {ch}", url=f"https://t.me/{name}")])
        buttons.append([InlineKeyboardButton("✅ I've Joined", callback_data="check_fsub")])

        await message.reply_photo(
            photo="https://i.ibb.co/pr2H8cwT/img-8312532076.jpg",
            caption=(
                "🔒 <b>Access Restricted!</b>\n\n"
                "You must join our channels to use this bot.\n\n"
                "👇 Click below to join, then tap <b>I've Joined</b>."
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=enums.ParseMode.HTML,
        )
        return False

    return True
