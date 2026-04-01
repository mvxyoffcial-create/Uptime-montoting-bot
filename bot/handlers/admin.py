import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from config import OWNER_ID
from bot.database.db import (
    get_user_count, get_all_users, set_premium,
    get_user, get_url_count
)
from bot.database.db import urls_col


def owner_only(func):
    """Decorator: restricts command to OWNER_ID only."""
    async def wrapper(client, message):
        if message.from_user.id != OWNER_ID:
            await message.reply("⛔ <b>Admin only command.</b>", parse_mode="html")
            return
        return await func(client, message)
    wrapper.__name__ = func.__name__
    return wrapper


def register_admin_handlers(app: Client):

    @app.on_message(filters.command("stats") & filters.private)
    @owner_only
    async def stats_cmd(client: Client, message: Message):
        total_users = await get_user_count()
        total_urls = await urls_col.count_documents({})
        active_urls = await urls_col.count_documents({"status": "active"})
        paused_urls = await urls_col.count_documents({"status": "paused"})

        text = (
            "📊 <b>Bot Statistics</b>\n\n"
            f"👥 <b>Total Users:</b> <code>{total_users}</code>\n"
            f"🔗 <b>Total URLs:</b> <code>{total_urls}</code>\n"
            f"🟢 <b>Active:</b> <code>{active_urls}</code>\n"
            f"⏸ <b>Paused:</b> <code>{paused_urls}</code>\n"
        )
        await message.reply(text, parse_mode="html")

    @app.on_message(filters.command("broadcast") & filters.private)
    @owner_only
    async def broadcast_cmd(client: Client, message: Message):
        if not message.reply_to_message:
            await message.reply(
                "📢 <b>Broadcast Usage:</b>\n\n"
                "Reply to any message with /broadcast to send it to all users.\n\n"
                "Supports: text, photo, video, document, sticker, animation",
                parse_mode="html"
            )
            return

        users = await get_all_users()
        total = len(users)
        sent = 0
        failed = 0

        status_msg = await message.reply(f"📤 Broadcasting to <b>{total}</b> users...", parse_mode="html")
        msg = message.reply_to_message

        for user in users:
            try:
                await msg.copy(user["user_id"])
                sent += 1
                await asyncio.sleep(0.05)  # 20 msgs/sec rate
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await msg.copy(user["user_id"])
                    sent += 1
                except Exception:
                    failed += 1
            except (UserIsBlocked, InputUserDeactivated):
                failed += 1
            except Exception:
                failed += 1

        await status_msg.edit_text(
            f"✅ <b>Broadcast Complete!</b>\n\n"
            f"📤 Sent: <code>{sent}</code>\n"
            f"❌ Failed: <code>{failed}</code>\n"
            f"👥 Total: <code>{total}</code>",
            parse_mode="html"
        )

    @app.on_message(filters.command("premium") & filters.private)
    @owner_only
    async def premium_cmd(client: Client, message: Message):
        """Usage: /premium <user_id> on|off"""
        args = message.text.split()
        if len(args) < 3:
            await message.reply(
                "👑 <b>Premium Management</b>\n\n"
                "Usage: <code>/premium &lt;user_id&gt; on|off</code>\n\n"
                "Example: <code>/premium 123456789 on</code>",
                parse_mode="html"
            )
            return

        try:
            target_id = int(args[1])
        except ValueError:
            await message.reply("❌ Invalid user ID.", parse_mode="html")
            return

        action = args[2].lower()
        if action not in ("on", "off"):
            await message.reply("❌ Use <code>on</code> or <code>off</code>.", parse_mode="html")
            return

        status = action == "on"
        await set_premium(target_id, status)

        label = "granted ✅" if status else "removed ❌"
        await message.reply(
            f"👑 <b>Premium {label}</b> for user <code>{target_id}</code>",
            parse_mode="html"
        )

        # Notify the user
        try:
            notif = (
                "🎉 <b>Premium Activated!</b>\n\nYou now have <b>unlimited URL monitoring</b>! 🚀"
                if status else
                "ℹ️ Your premium access has been removed. You are now on the free plan (5 URLs max)."
            )
            await client.send_message(target_id, notif, parse_mode="html")
        except Exception:
            pass

    @app.on_message(filters.command("users") & filters.private)
    @owner_only
    async def users_cmd(client: Client, message: Message):
        """List recent users."""
        users = await get_all_users()
        count = len(users)
        if not users:
            await message.reply("No users yet.", parse_mode="html")
            return

        lines = [f"👥 <b>All Users ({count})</b>\n"]
        for u in users[:30]:  # Show max 30
            uname = f"@{u['username']}" if u.get("username") else "—"
            premium = "👑" if u.get("is_premium") else ""
            lines.append(f"• <code>{u['user_id']}</code> — {u.get('first_name', '?')} {uname} {premium}")

        if count > 30:
            lines.append(f"\n...and {count - 30} more.")

        await message.reply("\n".join(lines), parse_mode="html")

    @app.on_message(filters.command("userinfo") & filters.private)
    @owner_only
    async def userinfo_cmd(client: Client, message: Message):
        """Admin: get info about a specific user."""
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply("Usage: /userinfo <user_id>", parse_mode="html")
            return
        try:
            uid = int(args[1])
        except ValueError:
            await message.reply("❌ Invalid user ID.", parse_mode="html")
            return

        user = await get_user(uid)
        if not user:
            await message.reply("User not found in DB.", parse_mode="html")
            return

        url_count = await get_url_count(uid)
        text = (
            f"👤 <b>User Info</b>\n\n"
            f"🆔 ID: <code>{uid}</code>\n"
            f"📛 Name: {user.get('first_name', '—')}\n"
            f"🔗 Username: @{user.get('username', '—')}\n"
            f"👑 Premium: {'Yes ✅' if user.get('is_premium') else 'No ❌'}\n"
            f"🔗 URLs: <code>{url_count}</code>\n"
            f"📅 Joined: {user.get('joined', '—')}"
        )
        await message.reply(text, parse_mode="html")
