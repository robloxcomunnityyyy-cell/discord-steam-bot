import os
import discord
import requests
import asyncio
import json
from flask import Flask
from threading import Thread

print("🚀 BOT STARTING...")

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
MIN_DISCOUNT = 90
ALLOWED_STORES = ["steam", "epic"]

# ---------------- API ----------------
def get_deals():
    api_key = os.getenv("ITAD_API_KEY")

    if not api_key:
        print("❌ Missing API key")
        return []

    try:
        r = requests.get(
            "https://api.isthereanydeal.com/deals/v2",
            headers={"ITAD-API-Key": api_key},
            params={
                "country": "US",
                "limit": 100,
                "offset": 0
            },
            timeout=20
        )

        print("STATUS:", r.status_code)

        if r.status_code != 200:
            print("API ERROR:", r.text[:300])
            return []

        data = r.json()
        deals = data.get("list", [])

        print("DEALS FOUND:", len(deals))

        return deals

    except Exception as e:
        print("REQUEST ERROR:", e)
        return []

# ---------------- FILTER HELPERS ----------------
def get_discount(game):
    try:
        return float(game["deal"]["cut"])
    except:
        return 0


def get_store_text(game):
    try:
        return str(game["deal"]["store"]).lower()
    except:
        return ""

# ---------------- LOOP ----------------
seen = set()

async def loop():
    await client.wait_until_ready()
    channel = await client.fetch_channel(CHANNEL_ID)

    while True:
        print("\n🔁 NEW CYCLE")

        deals = get_deals()

        sent = 0

        for game in deals:
            deal_id = game.get("id")
            if not deal_id:
                continue

            if deal_id in seen:
                continue

            discount = get_discount(game)

            if discount < MIN_DISCOUNT:
                continue

            store_text = get_store_text(game)

            if not any(s in store_text for s in ALLOWED_STORES):
                print("🚫 STORE SKIP:", store_text)
                continue

            title = game.get("title", "Unknown")

            price = game.get("deal", {}).get("price", {}).get("amount", "0")
            normal = game.get("deal", {}).get("regular", {}).get("amount", "0")
            url = game.get("deal", {}).get("url", "")

            print(f"🔥 FOUND: {title} ({discount}%)")

            embed = discord.Embed(
                title=f"🔥 {title} - {round(discount)}% OFF",
                url=url,
                description=f"~~${normal}~~ → **${price}**"
            )

            await channel.send(content="@everyone", embed=embed)

            seen.add(deal_id)
            sent += 1

        print(f"✔ SENT THIS CYCLE: {sent}")

        await asyncio.sleep(180)

# ---------------- EVENTS ----------------
@client.event
async def on_ready():
    print("🤖 BOT ONLINE:", client.user)

    asyncio.create_task(loop())

# ---------------- RUN ----------------
client.run(os.getenv("TOKEN"))
