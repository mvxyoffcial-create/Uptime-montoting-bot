# 🤖 MvxyUptimeBot — Mirror Nexus Uptime Monitor

> Built by [@Venuboyy](https://t.me/Venuboyy) | Powered by Pyrogram + MongoDB

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔗 URL Monitoring | Auto-pings your URLs every 5 minutes |
| 🎌 Anime Welcome | Random anime wallpaper on every /start |
| 🎭 Welcome Sticker | Animated sticker appears for 2s then auto-deletes |
| 🔒 Force Subscribe | Users must join @zerodev2 & @mvxyoffcail |
| 👤 /info | Shows user profile with photo, DC, username, link |
| 📊 /stats | Admin: total users & URLs |
| 📢 Broadcast | Admin: send any message to all users |
| 👑 Premium | Admin can grant premium (unlimited URLs) |
| 🆓 Free Tier | 5 URLs per free user |
| ⚡ 500 Workers | High throughput with Pyrogram |
| 🍃 MongoDB | Full user & URL persistence |
| 🤖 Auto-filter | Detects URLs sent to bot automatically |

---

## 🚀 Quick Start

### 1. Clone & configure

```bash
git clone https://github.com/yourrepo/MvxyUptimeBot
cd MvxyUptimeBot
cp .env.example .env
nano .env   # fill in your values
```

### 2. Install & run

```bash
pip install -r requirements.txt
python main.py
```

---

## 🐳 Docker

```bash
docker build -t mvxyuptimebot .
docker run --env-file .env mvxyuptimebot
```

---

## ☁️ Heroku

```bash
heroku create
heroku config:set API_ID=... API_HASH=... BOT_TOKEN=... MONGO_URI=... OWNER_ID=...
git push heroku main
heroku ps:scale worker=1
```

---

## ⚙️ Environment Variables

| Variable | Description |
|---|---|
| `API_ID` | Telegram API ID (my.telegram.org) |
| `API_HASH` | Telegram API Hash |
| `BOT_TOKEN` | BotFather token |
| `MONGO_URI` | MongoDB connection string |
| `DB_NAME` | Database name (default: MvxyUptimeBot) |
| `OWNER_ID` | Your Telegram user ID |

---

## 📋 Commands

### User Commands
| Command | Description |
|---|---|
| `/start` | Start the bot |
| `/add <url>` | Add a URL to monitor |
| `/urls` | List your monitored URLs |
| `/status` | View all URL statuses |
| `/ping <url>` | One-time ping test |
| `/remove <url>` | Remove a URL |
| `/info` | Your Telegram info + profile pic |
| `/help` | Help message |
| `/about` | About the bot |

### Admin Commands (OWNER_ID only)
| Command | Description |
|---|---|
| `/stats` | Bot statistics |
| `/broadcast` | Broadcast (reply to message) |
| `/premium <id> on\|off` | Grant/remove premium |
| `/users` | List all users |
| `/userinfo <id>` | Info about a specific user |

---

## 🏗️ Project Structure

```
MvxyUptimeBot/
├── main.py                    # Entry point
├── config.py                  # All settings & text strings
├── requirements.txt
├── Dockerfile
├── Procfile
├── .env.example
└── bot/
    ├── handlers/
    │   ├── start.py           # /start, welcome flow, callbacks
    │   ├── monitor.py         # URL add/remove/list/ping
    │   ├── admin.py           # stats, broadcast, premium
    │   └── info.py            # /info command
    ├── database/
    │   └── db.py              # MongoDB helpers
    ├── filters/
    │   └── fsub.py            # Force subscribe check
    └── utils/
        └── scheduler.py       # Background ping loop
```

---

## 👨‍💻 Developer

- **Owner:** [@Venuboyy](https://t.me/Venuboyy)
- **Channels:** [@zerodev2](https://t.me/zerodev2) | [@mvxyoffcail](https://t.me/mvxyoffcail)
