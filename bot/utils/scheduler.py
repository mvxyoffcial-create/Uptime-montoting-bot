import asyncio
import aiohttp
import time
import logging

from bot.database.db import get_all_active_urls, update_url_ping

logger = logging.getLogger(__name__)

PING_INTERVAL = 300  # seconds between full ping cycles (5 minutes)
CONCURRENCY = 50     # how many URLs to ping simultaneously


async def ping_one(session: aiohttp.ClientSession, url_doc: dict) -> None:
    """Ping a single URL and update its DB record."""
    url = url_doc["url"]
    url_id = url_doc["_id"]
    start = time.time()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10), allow_redirects=True) as resp:
            elapsed = int((time.time() - start) * 1000)
            await update_url_ping(url_id, resp.status, elapsed)
    except Exception as e:
        logger.debug(f"Ping failed for {url}: {e}")
        await update_url_ping(url_id, None, None)


async def ping_all_urls():
    """Ping all active URLs with concurrency control."""
    urls = await get_all_active_urls()
    if not urls:
        return

    sem = asyncio.Semaphore(CONCURRENCY)

    async def bounded_ping(session, url_doc):
        async with sem:
            await ping_one(session, url_doc)

    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [bounded_ping(session, u) for u in urls]
        await asyncio.gather(*tasks, return_exceptions=True)

    logger.info(f"[Scheduler] Pinged {len(urls)} URLs.")


async def scheduler_loop():
    """Continuously ping all URLs every PING_INTERVAL seconds."""
    logger.info("[Scheduler] Starting ping scheduler...")
    while True:
        try:
            await ping_all_urls()
        except Exception as e:
            logger.error(f"[Scheduler] Error: {e}")
        await asyncio.sleep(PING_INTERVAL)
