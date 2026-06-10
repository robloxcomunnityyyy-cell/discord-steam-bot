import os
print("NEW VERSION LOADED")

import discord
import requests
import asyncio
import json
from flask import Flask
from threading import Thread

# ---------------- FLASK KEEP-ALIVE ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Discord Steam Bot is running!"

Thread(
    target=lambda: app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
).start()

# ---------------- DISCORD SETUP ----------------
CHANNEL_ID = 856527775069503530

intents = discord.Intents.default()
client = discord.Client(intents=intents, heartbeat_timeout=60)

# ---------------- DEAL MEMORY ----------------
SEEN_FILE = "seen_deals.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

seen_deals = load_seen()

# ---------------- API ----------------
def get_deals():
    api_key = os.getenv("ITAD_API_KEY")
    if not api_key:
        print("Missing ITAD API key")
        return []

    try:
        r = requests.get(
            "https://api.isthereanydeal.com/deals/v2",
            headers={"ITAD-API-Key": api_key},
            params={"country": "US", "limit": 50},
            timeout=15
        )
        return r.json().get("list", [])
    except Exception as e:
        print("API ERROR:", e)
        return []

# ---------------- DEAL LOOP ----------------
async def deal_loop():
    await client.wait_until_ready()

    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel not found!")
        return

    while not client.is_closed():
        try:
            deals = get_deals()
            print("DEALS FOUND:", len(deals), flush=True)

            for game in deals:

                if game.get("type") != "game":
                    continue

                deal_id = game["id"]

                if deal_id in seen_deals:
                    continue

                discount = float(game["deal"]["cut"])
                if discount < 10:
                    continue

                seen_deals.add(deal_id)

                title = game["title"]
                price = game["deal"]["price"]["amount"]
                normal = game["deal"]["regular"]["amount"]
                url = game["deal"]["url"]

                embed = discord.Embed(
                    title=f"🔥 {title} is {round(discount)}% OFF",
                    url=url,
                    description=f"~~${normal}~~ → **${price}**"
                )

                embed.set_image(url=game.get("assets", {}).get("boxart", ""))

                await channel.send(content="@everyone", embed=embed)

            save_seen(seen_deals)

        except Exception as e:
            print("LOOP ERROR:", e)

        await asyncio.sleep(300)

# ---------------- EVENTS ----------------
@client.event
async def on_ready():
    print("ON_READY FIRED")

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🤖 BOT WORKS!")

    asyncio.create_task(deal_loop())

# ---------------- RUN BOT ----------------
client.run(os.getenv("TOKEN"))
