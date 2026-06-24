import os
import discord
import requests
import asyncio
import json
from flask import Flask
from threading import Thread

print("🚀 BOT STARTING (DEBUG MODE)")

# ---------------- KEEP ALIVE ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

Thread(
    target=lambda: app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    ),
    daemon=True
).start()

# ---------------- DISCORD ----------------
CHANNEL_ID = 856527775069503530

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ---------------- CONFIG ----------------
ITAD_API_KEY = os.getenv("ITAD_API_KEY")

# ---------------- API ----------------
def get_deals():
    if not ITAD_API_KEY:
        print("❌ Missing ITAD API key")
        return []

    try:
        r = requests.get(
            "https://api.isthereanydeal.com/deals/v2",
            headers={"ITAD-API-Key": ITAD_API_KEY},
            params={
                "country": "US",
                "limit": 20,
                "offset": 0
            },
            timeout=20
        )

        print("\n📡 STATUS:", r.status_code)

        if r.status_code != 200:
            print("❌ API ERROR:")
            print(r.text[:500])
            return []

        data = r.json()
        deals = data.get("list", [])

        print(f"📦 DEALS FOUND: {len(deals)}")

        return deals

    except Exception as e:
        print("❌ REQUEST FAILED:", e)
        return []

# ---------------- LOOP (DEBUG ONLY) ----------------
async def loop():
    await client.wait_until_ready()

    print("\n🟢 LOOP STARTED")

    while True:
        try:
            deals = get_deals()

            print("\n🔍 SHOWING RAW SAMPLE (FIRST 3 ITEMS):")

            for i, game in enumerate(deals[:3]):
                print("\n-------------------------")
                print(f"GAME #{i}")
                print(json.dumps(game, indent=2)[:2000])  # safe trimmed output

            print("\n💤 WAITING 180s...\n")

        except Exception as e:
            print("❌ LOOP ERROR:", e)

        await asyncio.sleep(180)

# ---------------- EVENTS ----------------
@client.event
async def on_ready():
    print("\n🤖 DISCORD CONNECTED")
    print(f"USER: {client.user}")

    asyncio.create_task(loop())

# ---------------- RUN ----------------
client.run(os.getenv("TOKEN"))
