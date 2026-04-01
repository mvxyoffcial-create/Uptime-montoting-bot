import pytz
import asyncio
import datetime

from pyrogram import Client, filters
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

# LabeledPrice does not exist in pyrogram 2.0.106 — define it locally
from collections import namedtuple
LabeledPrice = namedtuple("LabeledPrice", ["label", "amount"])

from script import script
from config import ADMINS, PREMIUM_LOGS, STAR_PREMIUM_PLANS, SUBSCRIPTION_IMG, WELCOME_IMAGE
from utils import get_seconds, temp
from bot.database.db import (
    db,
    get_user, update_user, remove_premium_access, get_all_users,
    set_premium,
)

# ── helpers ──────────────────────────────────────────────────────────────────

IST = pytz.timezone("Asia/Kolkata")


def _fmt_expiry(expiry_dt) -> str:
    return expiry_dt.astimezone(IST).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")


def _fmt_expiry_short(expiry_dt) -> str:
    return expiry_dt.astimezone(IST).strftime("%d-%m-%Y | %I:%M:%S %p")


def _time_left_str(expiry_dt) -> str:
    now = datetime.datetime.now(IST)
    delta = expiry_dt.astimezone(IST) - now
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    return f"{days} ᴅᴀʏꜱ, {hours} ʜᴏᴜʀꜱ, {minutes} ᴍɪɴᴜᴛᴇꜱ"


def _plan_buttons() -> InlineKeyboardMarkup:
    rows = []
    labels = {50: "1 ᴍᴏɴᴛʜ", 100: "3 ᴍᴏɴᴛʜꜱ", 200: "6 ᴍᴏɴᴛʜꜱ", 350: "1 ʏᴇᴀʀ"}
    for stars, duration in labels.items():
        rows.append([InlineKeyboardButton(
            f"⭐ {stars} ꜱᴛᴀʀꜱ → {duration}",
            callback_data=f"buy_{stars}"
        )])
    rows.append([InlineKeyboardButton("🚫 ᴄʟᴏꜱᴇ", callback_data="close_data")])
    return InlineKeyboardMarkup(rows)


# ── successful_payment filter ─────────────────────────────────────────────────

def _successful_payment_filter(_, __, message: Message) -> bool:
    try:
        return hasattr(message, "successful_payment") and message.successful_payment is not None
    except AttributeError:
        return False


successful_payment = filters.create(_successful_payment_filter)


# ── register ──────────────────────────────────────────────────────────────────

def register_premium_handlers(app: Client):

    # ── /remove_premium ───────────────────────────────────────────────────────
    @app.on_message(filters.command("remove_premium") & filters.user(ADMINS))
    async def remove_premium_cmd(client: Client, message: Message):
        if len(message.command) != 2:
            await message.reply("ᴜꜱᴀɢᴇ : /remove_premium user_id")
            return
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        if await remove_premium_access(user_id):
            await message.reply("ᴜꜱᴇʀ ʀᴇᴍᴏᴠᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ !")
            await client.send_message(
                chat_id=user_id,
                text=script.PREMIUM_END_TEXT.format(user.mention),
                parse_mode="html",
            )
        else:
            await message.reply(
                "ᴜɴᴀʙʟᴇ ᴛᴏ ʀᴇᴍᴏᴠᴇ ᴜꜱᴇʀ !\n"
                "ᴀʀᴇ ʏᴏᴜ ꜱᴜʀᴇ, ɪᴛ ᴡᴀꜱ ᴀ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ɪᴅ ?"
            )

    # ── /myplan ───────────────────────────────────────────────────────────────
    @app.on_message(filters.command("myplan") & filters.private)
    async def myplan_cmd(client: Client, message: Message):
        try:
            user = message.from_user.mention
            user_id = message.from_user.id
            data = await get_user(user_id)

            if data and data.get("expiry_time"):
                expiry = data["expiry_time"]
                caption = (
                    f"⚜️ <b>ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ᴅᴀᴛᴀ :</b>\n\n"
                    f"👤 <b>ᴜꜱᴇʀ :</b> {user}\n"
                    f"⚡ <b>ᴜꜱᴇʀ ɪᴅ :</b> <code>{user_id}</code>\n"
                    f"⏰ <b>ᴛɪᴍᴇ ʟᴇꜰᴛ :</b> {_time_left_str(expiry)}\n"
                    f"⌛️ <b>ᴇxᴘɪʀʏ ᴅᴀᴛᴇ :</b> {_fmt_expiry(expiry)}"
                )
                await message.reply_photo(
                    photo=SUBSCRIPTION_IMG,
                    caption=caption,
                    parse_mode="html",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("🔥 ᴇxᴛᴇɴᴅ ᴘʟᴀɴ", callback_data="premium_info")]]
                    ),
                )
            else:
                await message.reply_photo(
                    photo=SUBSCRIPTION_IMG,
                    caption=(
                        f"<b>ʜᴇʏ {user},\n\n"
                        f"ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀɴ ᴀᴄᴛɪᴠᴇ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴ.\n"
                        f"ʙᴜʏ ᴏᴜʀ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ ᴛᴏ ᴇɴᴊᴏʏ ᴘʀᴇᴍɪᴜᴍ ʙᴇɴᴇꜰɪᴛꜱ.</b>"
                    ),
                    parse_mode="html",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("💎 ᴄʜᴇᴄᴋᴏᴜᴛ ᴘʀᴇᴍɪᴜᴍ ᴘʟᴀɴꜱ", callback_data="premium_info")]]
                    ),
                )
        except Exception as e:
            print(f"[myplan] {e}")

    # ── /get_premium (admin) ──────────────────────────────────────────────────
    @app.on_message(filters.command("get_premium") & filters.user(ADMINS))
    async def get_premium_cmd(client: Client, message: Message):
        if len(message.command) != 2:
            await message.reply("ᴜꜱᴀɢᴇ : /get_premium user_id")
            return
        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        data = await get_user(user_id)
        if data and data.get("expiry_time"):
            expiry = data["expiry_time"]
            await message.reply(
                f"⚜️ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀ ᴅᴀᴛᴀ :\n\n"
                f"👤 ᴜꜱᴇʀ : {user.mention}\n"
                f"⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n"
                f"⏰ ᴛɪᴍᴇ ʟᴇꜰᴛ : {_time_left_str(expiry)}\n"
                f"⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {_fmt_expiry(expiry)}",
                parse_mode="html",
            )
        else:
            await message.reply("ɴᴏ ᴘʀᴇᴍɪᴜᴍ ᴅᴀᴛᴀ ꜰᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ !")

    # ── /add_premium (admin) ──────────────────────────────────────────────────
    @app.on_message(filters.command("add_premium") & filters.user(ADMINS))
    async def add_premium_cmd(client: Client, message: Message):
        if len(message.command) != 4:
            await message.reply(
                "📌 ᴜsᴀɢᴇ: <code>/add_premium user_id amount unit</code>\n"
                "📅 ᴇxᴀᴍᴘʟᴇ: <code>/add_premium 123456 1 month</code>\n"
                "🧭 ᴀᴄᴄᴇᴘᴛᴇᴅ: <code>day hour min month year</code>",
                parse_mode="html",
            )
            return

        user_id = int(message.command[1])
        user = await client.get_users(user_id)
        time_str = message.command[2] + " " + message.command[3]
        seconds = await get_seconds(time_str)

        if seconds <= 0:
            await message.reply(
                "❌ ɪɴᴠᴀʟɪᴅ ᴛɪᴍᴇ ꜰᴏʀᴍᴀᴛ ❗\n"
                "🕒 ᴜꜱᴇ: <code>1 day</code>, <code>1 hour</code>, <code>1 min</code>, "
                "<code>1 month</code>, or <code>1 year</code>",
                parse_mode="html",
            )
            return

        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        await update_user({"id": user_id, "expiry_time": expiry_time, "is_premium": True})
        data = await get_user(user_id)
        expiry = data["expiry_time"]

        now_ist = datetime.datetime.now(IST).strftime("%d-%m-%Y\n⏱️ ᴊᴏɪɴɪɴɢ ᴛɪᴍᴇ : %I:%M:%S %p")
        expiry_str = _fmt_expiry(expiry)

        await message.reply(
            f"ᴘʀᴇᴍɪᴜᴍ ᴀᴅᴅᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ✅\n\n"
            f"👤 ᴜꜱᴇʀ : {user.mention}\n"
            f"⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n"
            f"⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time_str}</code>\n\n"
            f"⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {now_ist}\n\n"
            f"⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str}",
            parse_mode="html",
            disable_web_page_preview=True,
        )
        await client.send_message(
            user_id,
            f"👋 ʜᴇʏ {user.mention},\n"
            f"ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴘᴜʀᴄʜᴀꜱɪɴɢ ᴘʀᴇᴍɪᴜᴍ. ᴇɴᴊᴏʏ !! ✨🎉\n\n"
            f"⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time_str}</code>\n"
            f"⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {now_ist}\n\n"
            f"⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str}",
            parse_mode="html",
            disable_web_page_preview=True,
        )
        if PREMIUM_LOGS:
            await client.send_message(
                PREMIUM_LOGS,
                f"#Added_Premium\n\n"
                f"👤 ᴜꜱᴇʀ : {user.mention}\n"
                f"⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n"
                f"⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time_str}</code>\n\n"
                f"⏳ ᴊᴏɪɴɪɴɢ ᴅᴀᴛᴇ : {now_ist}\n\n"
                f"⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str}",
                parse_mode="html",
                disable_web_page_preview=True,
            )

    # ── /premium_users (admin) ────────────────────────────────────────────────
    @app.on_message(filters.command("premium_users") & filters.user(ADMINS))
    async def premium_users_cmd(client: Client, message: Message):
        aa = await message.reply("<i>ꜰᴇᴛᴄʜɪɴɢ...</i>", parse_mode="html")
        text = "⚜️ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ ʟɪꜱᴛ :\n\n"
        count = 1
        async for user_doc in get_all_users():
            data = await get_user(user_doc["id"])
            if not (data and data.get("expiry_time")):
                continue
            expiry = data["expiry_time"]
            try:
                tg_user = await client.get_users(user_doc["id"])
                mention = tg_user.mention
            except Exception:
                mention = str(user_doc["id"])
            text += (
                f"{count}. {mention}\n"
                f"👤 ᴜꜱᴇʀ ɪᴅ : {user_doc['id']}\n"
                f"⏳ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {_fmt_expiry(expiry)}\n"
                f"⏰ ᴛɪᴍᴇ ʟᴇꜰᴛ : {_time_left_str(expiry)}\n\n"
            )
            count += 1

        if count == 1:
            await aa.edit_text("ɴᴏ ᴘʀᴇᴍɪᴜᴍ ᴜꜱᴇʀꜱ ꜰᴏᴜɴᴅ.")
            return
        try:
            await aa.edit_text(text, parse_mode="html")
        except MessageTooLong:
            with open("usersplan.txt", "w+") as f:
                f.write(text)
            await message.reply_document("usersplan.txt", caption="Premium Users List")

    # ── /plan ─────────────────────────────────────────────────────────────────
    @app.on_message(filters.command("plan") & filters.private)
    async def plan_cmd(client: Client, message: Message):
        user_id = message.from_user.id
        users = message.from_user.mention
        msg = await message.reply_photo(
            photo=SUBSCRIPTION_IMG,
            caption=script.BPREMIUM_TXT,
            parse_mode="html",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("• ʙᴜʏ ᴘʀᴇᴍɪᴜᴍ •", callback_data="buy_info")],
                [InlineKeyboardButton("🚫 ᴄʟᴏꜱᴇ 🚫", callback_data="close_data")],
            ]),
        )
        if PREMIUM_LOGS:
            await client.send_message(
                PREMIUM_LOGS,
                f"<b><u>🚫 ᴛʜɪs ᴜꜱᴇʀ ᴛʀɪᴇᴅ /plan</u> {temp.B_LINK}\n\n"
                f"- ɪᴅ - <code>{user_id}</code>\n- ɴᴀᴍᴇ - {users}</b>",
                parse_mode="html",
            )
        await asyncio.sleep(300)
        try:
            await msg.delete()
            await message.delete()
        except Exception:
            pass

    # ── callback: premium_info / buy_info ─────────────────────────────────────
    @app.on_callback_query(filters.regex("^(premium_info|buy_info)$"))
    async def premium_info_cb(client: Client, query: CallbackQuery):
        await query.answer()
        await query.message.reply_photo(
            photo=SUBSCRIPTION_IMG,
            caption=script.BPREMIUM_TXT,
            parse_mode="html",
            reply_markup=_plan_buttons(),
        )

    # ── callback: buy_{stars} → send invoice ─────────────────────────────────
    @app.on_callback_query(filters.regex(r"^buy_\d+$"))
    async def premium_buy_cb(client: Client, query: CallbackQuery):
        try:
            amount = int(query.data.split("_")[1])
            if amount not in STAR_PREMIUM_PLANS:
                await query.answer("⚠️ Invalid Premium Package.", show_alert=True)
                return
            await client.send_invoice(
                chat_id=query.message.chat.id,
                title="Premium Subscription",
                description=f"Pay {amount} Stars & Get Premium for {STAR_PREMIUM_PLANS[amount]}",
                payload=f"renamepremium_{amount}",
                currency="XTR",
                prices=[LabeledPrice(label="Premium Subscription", amount=amount)],
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("ᴄᴀɴᴄᴇʟ 🚫", callback_data="close_data")]]
                ),
            )
            await query.answer()
        except Exception as e:
            print(f"[buy_invoice] {e}")
            await query.answer("🚫 Error processing payment. Try again.", show_alert=True)

    # ── callback: close_data ──────────────────────────────────────────────────
    @app.on_callback_query(filters.regex("^close_data$"))
    async def close_data_cb(client: Client, query: CallbackQuery):
        await query.message.delete()

    # ── successful_payment handler ────────────────────────────────────────────
    @app.on_message(successful_payment & filters.private)
    async def successful_payment_handler(client: Client, message: Message):
        try:
            user_id = message.from_user.id
            payload = message.successful_payment.invoice_payload

            # Extract amount from payload
            if payload.startswith("renamepremium_"):
                amount = int(payload.split("_")[1])
            else:
                amount = int(message.successful_payment.total_amount)

            if amount not in STAR_PREMIUM_PLANS:
                await message.reply("⚠️ Invalid Premium Package.")
                return

            time_str = STAR_PREMIUM_PLANS[amount]
            seconds = await get_seconds(time_str)
            if seconds <= 0:
                await message.reply("⚠️ Invalid premium time.")
                return

            expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
            await update_user({"id": user_id, "expiry_time": expiry_time, "is_premium": True})

            data = await get_user(user_id)
            expiry = data["expiry_time"]
            expiry_str = _fmt_expiry_short(expiry)
            now_ist = datetime.datetime.now(IST).strftime("%d-%m-%Y | %I:%M:%S %p")

            await message.reply(
                f"✅ <b>ᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴘᴜʀᴄʜᴀꜱɪɴɢ ᴘʀᴇᴍɪᴜᴍ ᴜꜱɪɴɢ ꜱᴛᴀʀꜱ!</b>\n\n"
                f"⭐ ꜱᴛᴀʀꜱ ᴘᴀɪᴅ : {amount}\n"
                f"⏰ ꜱᴜʙꜱᴄʀɪᴘᴛɪᴏɴ : {time_str}\n"
                f"⌛️ ᴇxᴘɪʀᴇꜱ : {expiry_str}",
                parse_mode="html",
                disable_web_page_preview=True,
            )

            if PREMIUM_LOGS:
                await client.send_message(
                    PREMIUM_LOGS,
                    f"#Purchase_Premium_With_Star\n\n"
                    f"👤 ᴜꜱᴇʀ : {message.from_user.mention}\n"
                    f"⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n"
                    f"⭐ ꜱᴛᴀʀ ᴘᴀʏ : {amount}\n"
                    f"⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : {time_str}\n"
                    f"⏳ ᴊᴏɪɴɪɴɢ : {now_ist}\n"
                    f"⌛️ ᴇxᴘɪʀʏ : {expiry_str}",
                    parse_mode="html",
                    disable_web_page_preview=True,
                )

        except Exception as e:
            print(f"[successful_payment] {e}")
            await message.reply("✅ Payment received! Contact @Venuboyy if premium is not activated.")
