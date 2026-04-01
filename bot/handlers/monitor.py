from pyrogram import enums
import aiohttp
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from bot.database.db import (
    add_url, get_user_urls, get_url_count,
    remove_url, update_url_ping, pause_url, resume_url,
    is_premium
)
from bot.filters.fsub import check_fsub
from config import FREE_LIMIT, WELCOME_IMAGE, OWNER_ID

# Track users waiting to add URL
pending_add: dict = {}


def url_list_keyboard(urls: list, page: int = 0) -> InlineKeyboardMarkup:
    """Build paginated inline keyboard for URL list."""
    per_page = 5
    start = page * per_page
    end = start + per_page
    sliced = urls[start:end]

    rows = []
    for u in sliced:
        uid = str(u["_id"])
        label = u.get("label", u["url"])[:30]
        status_icon = "🟢" if u.get("last_status_code") in range(200, 400) else ("🔴" if u.get("last_status_code") else "⚪")
        rows.append([InlineKeyboardButton(f"{status_icon} {label}", callback_data=f"url_detail:{uid}")])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"url_page:{page-1}"))
    if end < len(urls):
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"url_page:{page+1}"))
    if nav:
        rows.append(nav)

    rows.append([
        InlineKeyboardButton("➕ Add URL", callback_data="add_url_prompt"),
        InlineKeyboardButton("🏠 Home", callback_data="home"),
    ])
    return InlineKeyboardMarkup(rows)


async def ping_url(url: str) -> tuple:
    """Ping a URL and return (status_code, response_time_ms)."""
    start = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as resp:
                elapsed = int((time.time() - start) * 1000)
                return resp.status, elapsed
    except Exception:
        return None, None


def register_monitor_handlers(app: Client):

    @app.on_message(filters.command("add") & filters.private)
    async def add_cmd(client: Client, message: Message):
        if not await check_fsub(client, message):
            return

        user_id = message.from_user.id
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            pending_add[user_id] = True
            await message.reply(
                "📎 <b>Send me the URL you want to monitor:</b>\n\n"
                "Example: <code>https://mybot.example.com</code>",
                parse_mode=enums.ParseMode.HTML
            )
            return

        url = args[1].strip()
        await _process_add_url(client, message, user_id, url)

    @app.on_message(filters.private & filters.text & ~filters.command([
        "start", "help", "about", "add", "remove", "urls", "status",
        "ping", "info", "broadcast", "stats", "premium", "pause", "resume"
    ]))
    async def auto_filter_url(client: Client, message: Message):
        """Auto-filter: if user sends a URL-like text, offer to add it."""
        user_id = message.from_user.id
        text = message.text.strip()

        # Check if pending add
        if user_id in pending_add and pending_add.get(user_id):
            del pending_add[user_id]
            if text.startswith("http://") or text.startswith("https://"):
                await _process_add_url(client, message, user_id, text)
            else:
                await message.reply("❌ Invalid URL. Please send a valid URL starting with <code>http://</code> or <code>https://</code>.", parse_mode=enums.ParseMode.HTML)
            return

        # Auto-detect URL in message
        if text.startswith("http://") or text.startswith("https://"):
            if not await check_fsub(client, message):
                return
            await message.reply(
                f"🔗 <b>URL Detected!</b>\n\n"
                f"<code>{text}</code>\n\n"
                f"➤ Tap <b>✅ Add & Monitor</b> to start monitoring\n"
                f"➤ Tap <b>📊 My URLs</b> to view your list\n"
                f"➤ Tap <b>🏓 Ping</b> to test it once",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Add & Monitor", callback_data=f"confirm_add:{text}"),
                        InlineKeyboardButton("🏓 Ping Only", callback_data=f"ping_only:{text}"),
                    ],
                    [
                        InlineKeyboardButton("📊 My URLs", callback_data="my_urls"),
                        InlineKeyboardButton("❌ Cancel", callback_data="cancel_add"),
                    ]
                ]),
                parse_mode=enums.ParseMode.HTML
            )

    @app.on_message(filters.command("urls") & filters.private)
    async def urls_cmd(client: Client, message: Message):
        if not await check_fsub(client, message):
            return
        user_id = message.from_user.id
        urls = await get_user_urls(user_id)
        if not urls:
            await message.reply(
                "📭 <b>You have no monitored URLs yet.</b>\n\nSend a URL or use /add to start!",
                parse_mode=enums.ParseMode.HTML
            )
            return
        await message.reply_photo(
            photo=WELCOME_IMAGE,
            caption=f"📊 <b>Your Monitored URLs</b> — {len(urls)} total",
            reply_markup=url_list_keyboard(urls),
            parse_mode=enums.ParseMode.HTML
        )

    @app.on_message(filters.command("status") & filters.private)
    async def status_cmd(client: Client, message: Message):
        if not await check_fsub(client, message):
            return
        user_id = message.from_user.id
        urls = await get_user_urls(user_id)
        if not urls:
            await message.reply("📭 No URLs being monitored.", parse_mode=enums.ParseMode.HTML)
            return

        lines = ["📊 <b>Uptime Status</b>\n"]
        for u in urls:
            code = u.get("last_status_code")
            ping_ms = u.get("last_ping_ms")
            icon = "🟢" if code and 200 <= code < 400 else ("🔴" if code else "⚪")
            label = u.get("label", u["url"])[:40]
            ping_str = f"{ping_ms}ms" if ping_ms else "—"
            code_str = str(code) if code else "—"
            lines.append(f"{icon} <b>{label}</b>\n   ↳ Status: <code>{code_str}</code> | Ping: <code>{ping_str}</code>")

        await message.reply("\n\n".join(lines), parse_mode=enums.ParseMode.HTML)

    @app.on_message(filters.command("ping") & filters.private)
    async def ping_cmd(client: Client, message: Message):
        if not await check_fsub(client, message):
            return
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply("Usage: /ping <url>", parse_mode=enums.ParseMode.HTML)
            return
        url = args[1].strip()
        wait_msg = await message.reply(f"⏳ Pinging <code>{url}</code>...", parse_mode=enums.ParseMode.HTML)
        code, ms = await ping_url(url)
        if code:
            icon = "🟢" if 200 <= code < 400 else "🔴"
            await wait_msg.edit_text(
                f"{icon} <b>Ping Result</b>\n\n"
                f"🔗 URL: <code>{url}</code>\n"
                f"📶 Status: <code>{code}</code>\n"
                f"⚡ Response: <code>{ms}ms</code>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await wait_msg.edit_text(
                f"🔴 <b>Failed to reach</b> <code>{url}</code>\n\nThe URL is unreachable or timed out.",
                parse_mode=enums.ParseMode.HTML
            )

    @app.on_message(filters.command("remove") & filters.private)
    async def remove_cmd(client: Client, message: Message):
        if not await check_fsub(client, message):
            return
        user_id = message.from_user.id
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply("Usage: /remove <url>", parse_mode=enums.ParseMode.HTML)
            return
        url = args[1].strip()
        await remove_url_by_url(user_id, url)
        await message.reply(f"✅ <b>Removed:</b> <code>{url}</code>", parse_mode=enums.ParseMode.HTML)

    # ─── Callbacks ───

    @app.on_callback_query(filters.regex("^my_urls$"))
    async def my_urls_cb(client: Client, query: CallbackQuery):
        user_id = query.from_user.id
        urls = await get_user_urls(user_id)
        if not urls:
            await query.answer("No URLs yet!", show_alert=True)
            return
        await query.message.edit_caption(
            caption=f"📊 <b>Your Monitored URLs</b> — {len(urls)} total",
            reply_markup=url_list_keyboard(urls),
            parse_mode=enums.ParseMode.HTML
        )

    @app.on_callback_query(filters.regex(r"^url_page:(\d+)$"))
    async def url_page_cb(client: Client, query: CallbackQuery):
        page = int(query.data.split(":")[1])
        user_id = query.from_user.id
        urls = await get_user_urls(user_id)
        await query.message.edit_reply_markup(reply_markup=url_list_keyboard(urls, page))

    @app.on_callback_query(filters.regex(r"^url_detail:(.+)$"))
    async def url_detail_cb(client: Client, query: CallbackQuery):
        url_id = query.data.split(":", 1)[1]
        user_id = query.from_user.id
        urls = await get_user_urls(user_id)
        target = next((u for u in urls if str(u["_id"]) == url_id), None)
        if not target:
            await query.answer("URL not found.", show_alert=True)
            return

        code = target.get("last_status_code")
        ms = target.get("last_ping_ms")
        icon = "🟢" if code and 200 <= code < 400 else ("🔴" if code else "⚪")
        last_ping = target.get("last_ping")
        last_ping_str = last_ping.strftime("%Y-%m-%d %H:%M UTC") if last_ping else "Never"

        text = (
            f"{icon} <b>URL Details</b>\n\n"
            f"🔗 <b>URL:</b> <code>{target['url']}</code>\n"
            f"🏷 <b>Label:</b> {target.get('label', '—')}\n"
            f"📶 <b>Status:</b> <code>{code or '—'}</code>\n"
            f"⚡ <b>Ping:</b> <code>{ms or '—'}ms</code>\n"
            f"🕐 <b>Last Check:</b> {last_ping_str}\n"
            f"⚙️ <b>State:</b> {target.get('status', 'active').capitalize()}"
        )

        is_paused = target.get("status") == "paused"
        toggle_label = "▶️ Resume" if is_paused else "⏸ Pause"
        toggle_cb = f"resume_url:{url_id}" if is_paused else f"pause_url:{url_id}"

        await query.message.edit_caption(
            caption=text,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(toggle_label, callback_data=toggle_cb),
                    InlineKeyboardButton("🗑 Delete", callback_data=f"delete_url:{url_id}"),
                ],
                [InlineKeyboardButton("🔙 Back", callback_data="my_urls")]
            ]),
            parse_mode=enums.ParseMode.HTML
        )

    @app.on_callback_query(filters.regex(r"^pause_url:(.+)$"))
    async def pause_url_cb(client: Client, query: CallbackQuery):
        url_id = query.data.split(":", 1)[1]
        await pause_url(query.from_user.id, url_id)
        await query.answer("⏸ URL paused.")
        await url_detail_cb(client, query)

    @app.on_callback_query(filters.regex(r"^resume_url:(.+)$"))
    async def resume_url_cb(client: Client, query: CallbackQuery):
        url_id = query.data.split(":", 1)[1]
        await resume_url(query.from_user.id, url_id)
        await query.answer("▶️ URL resumed.")
        await url_detail_cb(client, query)

    @app.on_callback_query(filters.regex(r"^delete_url:(.+)$"))
    async def delete_url_cb(client: Client, query: CallbackQuery):
        url_id = query.data.split(":", 1)[1]
        await remove_url(query.from_user.id, url_id)
        await query.answer("🗑 URL deleted.")
        urls = await get_user_urls(query.from_user.id)
        if not urls:
            await query.message.edit_caption(
                caption="📭 <b>No monitored URLs.</b>\n\nSend a URL or use /add to start!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add URL", callback_data="add_url_prompt"),
                     InlineKeyboardButton("🏠 Home", callback_data="home")]
                ]),
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await query.message.edit_reply_markup(reply_markup=url_list_keyboard(urls))

    @app.on_callback_query(filters.regex("^add_url_prompt$"))
    async def add_url_prompt_cb(client: Client, query: CallbackQuery):
        pending_add[query.from_user.id] = True
        await query.message.edit_caption(
            caption="📎 <b>Send me the URL to monitor:</b>\n\nExample: <code>https://yourbot.example.com</code>",
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_add")]])
        )

    @app.on_callback_query(filters.regex(r"^confirm_add:(.+)$"))
    async def confirm_add_cb(client: Client, query: CallbackQuery):
        url = query.data.split(":", 1)[1]
        user_id = query.from_user.id
        await _process_add_url_cb(client, query, user_id, url)

    @app.on_callback_query(filters.regex(r"^ping_only:(.+)$"))
    async def ping_only_cb(client: Client, query: CallbackQuery):
        url = query.data.split(":", 1)[1]
        await query.answer("⏳ Pinging...")
        code, ms = await ping_url(url)
        if code:
            icon = "🟢" if 200 <= code < 400 else "🔴"
            text = (
                f"{icon} <b>Ping Result</b>\n\n"
                f"🔗 <code>{url}</code>\n"
                f"📶 Status: <code>{code}</code>\n"
                f"⚡ Response: <code>{ms}ms</code>"
            )
        else:
            text = f"🔴 <b>Unreachable</b>\n\n<code>{url}</code>\n\nFailed to connect or timed out."
        await query.message.edit_text(
            text,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Add & Monitor", callback_data=f"confirm_add:{url}")],
                [InlineKeyboardButton("❌ Close", callback_data="cancel_add")],
            ])
        )

    @app.on_callback_query(filters.regex("^cancel_add$"))
    async def cancel_add_cb(client: Client, query: CallbackQuery):
        pending_add.pop(query.from_user.id, None)
        await query.answer("Cancelled.")
        await query.message.edit_caption(
            caption="❌ Cancelled.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Home", callback_data="home")]])
        )


async def _process_add_url(client, message: Message, user_id: int, url: str):
    """Core logic for adding a URL via message."""
    from bot.database.db import remove_url_by_url

    if not (url.startswith("http://") or url.startswith("https://")):
        await message.reply("❌ URL must start with <code>http://</code> or <code>https://</code>", parse_mode=enums.ParseMode.HTML)
        return

    premium = await is_premium(user_id)
    count = await get_url_count(user_id)
    if not premium and count >= FREE_LIMIT:
        await message.reply(
            f"🔒 <b>Free limit reached!</b>\n\n"
            f"Free users can monitor up to <b>{FREE_LIMIT} URLs</b>.\n"
            f"Contact <a href='https://t.me/Venuboyy'>@Venuboyy</a> to upgrade to Premium for unlimited URLs! 👑",
            parse_mode=enums.ParseMode.HTML
        )
        return

    wait = await message.reply(f"⏳ Checking URL <code>{url}</code>...", parse_mode=enums.ParseMode.HTML)
    code, ms = await ping_url(url)

    await add_url(user_id, url)
    icon = "🟢" if code and 200 <= code < 400 else ("🔴" if code else "⚪")
    await wait.edit_text(
        f"{icon} <b>URL Added!</b>\n\n"
        f"🔗 <code>{url}</code>\n"
        f"📶 Status: <code>{code or 'unreachable'}</code>\n"
        f"⚡ Ping: <code>{ms or '—'}ms</code>\n\n"
        f"✅ I'll keep pinging this every few minutes.",
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 My URLs", callback_data="my_urls")]
        ])
    )


async def _process_add_url_cb(client, query: CallbackQuery, user_id: int, url: str):
    """Core logic for adding a URL via callback."""
    premium = await is_premium(user_id)
    count = await get_url_count(user_id)
    if not premium and count >= FREE_LIMIT:
        await query.answer(f"Free limit reached! Max {FREE_LIMIT} URLs for free users.", show_alert=True)
        return

    await query.answer("⏳ Adding URL...")
    code, ms = await ping_url(url)
    await add_url(user_id, url)
    icon = "🟢" if code and 200 <= code < 400 else ("🔴" if code else "⚪")
    await query.message.edit_caption(
        caption=(
            f"{icon} <b>URL Added!</b>\n\n"
            f"🔗 <code>{url}</code>\n"
            f"📶 Status: <code>{code or 'unreachable'}</code>\n"
            f"⚡ Ping: <code>{ms or '—'}ms</code>\n\n"
            f"✅ I'll keep pinging this every few minutes."
        ),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 My URLs", callback_data="my_urls")]
        ]),
        parse_mode=enums.ParseMode.HTML
    )
