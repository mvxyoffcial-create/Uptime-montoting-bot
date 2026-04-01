import asyncio
import logging
from pyrogram import Client
from config import API_ID, API_HASH, BOT_TOKEN, WORKERS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MvxyUptimeBot")


def create_bot() -> Client:
    return Client(
        name="MvxyUptimeBot",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        workers=WORKERS,
    )


async def main():
    app = create_bot()

    # Register all handlers
    from bot.handlers.start import register_start_handlers
    from bot.handlers.monitor import register_monitor_handlers
    from bot.handlers.admin import register_admin_handlers
    from bot.handlers.info import register_info_handler
    from bot.handlers.premium import register_premium_handlers

    register_start_handlers(app)
    register_monitor_handlers(app)
    register_admin_handlers(app)
    register_info_handler(app)
    register_premium_handlers(app)

    # Start bot and scheduler together
    from bot.utils.scheduler import scheduler_loop

    async with app:
        me = await app.get_me()
        logger.info(f"✅ Bot started as @{me.username} (ID: {me.id})")
        logger.info(f"⚙️  Workers: {WORKERS}")

        # Run scheduler in background
        asyncio.create_task(scheduler_loop())

        # Keep alive
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
