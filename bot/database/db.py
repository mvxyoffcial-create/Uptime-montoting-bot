from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, DB_NAME
import datetime

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

users_col = db["users"]
urls_col = db["monitored_urls"]


# ─────────────── USER METHODS ───────────────

async def add_user(user_id: int, first_name: str, username: str = None):
    user = await users_col.find_one({"user_id": user_id})
    if not user:
        await users_col.insert_one({
            "user_id": user_id,
            "first_name": first_name,
            "username": username,
            "is_premium": False,
            "joined": datetime.datetime.utcnow(),
        })


async def get_user(user_id: int):
    return await users_col.find_one({"user_id": user_id})


async def get_all_users():
    return await users_col.find().to_list(length=None)


async def get_user_count():
    return await users_col.count_documents({})


async def set_premium(user_id: int, status: bool):
    await users_col.update_one({"user_id": user_id}, {"$set": {"is_premium": status}})


async def is_premium(user_id: int) -> bool:
    user = await get_user(user_id)
    return user.get("is_premium", False) if user else False


# ─────────────── URL / MONITOR METHODS ───────────────

async def add_url(user_id: int, url: str, label: str = None):
    await urls_col.insert_one({
        "user_id": user_id,
        "url": url,
        "label": label or url,
        "status": "active",
        "last_ping": None,
        "last_status_code": None,
        "added": datetime.datetime.utcnow(),
    })


async def get_user_urls(user_id: int):
    return await urls_col.find({"user_id": user_id}).to_list(length=None)


async def get_url_count(user_id: int) -> int:
    return await urls_col.count_documents({"user_id": user_id})


async def remove_url(user_id: int, url_id: str):
    from bson import ObjectId
    await urls_col.delete_one({"_id": ObjectId(url_id), "user_id": user_id})


async def remove_url_by_url(user_id: int, url: str):
    await urls_col.delete_one({"user_id": user_id, "url": url})


async def update_url_ping(url_id, status_code, ping_time):
    from bson import ObjectId
    await urls_col.update_one(
        {"_id": ObjectId(url_id)},
        {"$set": {
            "last_ping": datetime.datetime.utcnow(),
            "last_status_code": status_code,
            "last_ping_ms": ping_time
        }}
    )


async def get_all_active_urls():
    return await urls_col.find({"status": "active"}).to_list(length=None)


async def pause_url(user_id: int, url_id: str):
    from bson import ObjectId
    await urls_col.update_one(
        {"_id": ObjectId(url_id), "user_id": user_id},
        {"$set": {"status": "paused"}}
    )


async def resume_url(user_id: int, url_id: str):
    from bson import ObjectId
    await urls_col.update_one(
        {"_id": ObjectId(url_id), "user_id": user_id},
        {"$set": {"status": "active"}}
    )


# ─────────────── PREMIUM METHODS ───────────────

async def update_user(user_data: dict):
    """Upsert user premium data (expects dict with 'id' key)."""
    user_id = user_data["id"]
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {k: v for k, v in user_data.items() if k != "id"}},
        upsert=True,
    )


async def remove_premium_access(user_id: int) -> bool:
    """Remove expiry_time. Returns True if user had premium."""
    result = await users_col.update_one(
        {"user_id": user_id, "expiry_time": {"$exists": True}},
        {"$unset": {"expiry_time": ""}, "$set": {"is_premium": False}},
    )
    return result.modified_count > 0


async def get_all_users():
    """Async generator yielding all user dicts with 'id' key for compat."""
    async for user in users_col.find():
        yield {"id": user["user_id"], **user}
