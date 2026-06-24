import os
import discord
import requests
import asyncio
import json
from flask import Flask
from threading import Thread

print("🚀 BOT STARTING (STABLE MODE)")

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

# ---------------- API ----------------
ITAD_API_KEY = os.getenv("ITAD_API_KEY")

def get_deals():
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
            print("❌ API ERROR:", r.text[:200])
            return []

        data = r.json()
        deals = data.get("list", [])

        print("📦 DEALS FOUND:", len(deals))

        return deals

    except Exception as e:
        print("❌ REQUEST ERROR:", e)
        return []

# ---------------- LOOP ----------------
async def deal_loop():
    await client.wait_until_ready()

    print("\n🟢 LOOP STARTED")

    while True:
        deals = get_deals()

        print("\n🔍 SAMPLE DATA CHECK:")

        for i, game in enumerate(deals[:3]):
            print(f"\nGAME {i}: {game.get('title')}")

        await asyncio.sleep(180)

# ---------------- EVENTS ----------------
@client.event
async def setup_hook():
    print("🧠 SETUP_HOOK RUNNING")

    asyncio.create_task(deal_loop())

@client.event
async def on_ready():
    print("🤖 ON_READY FIRED")
    print("USER:", client.user)

# ---------------- RUN ----------------
client.run(os.getenv("TOKEN"))
