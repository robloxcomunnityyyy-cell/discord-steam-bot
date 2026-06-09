import os

print("NEW VERSION LOADED")

import discord
import requests
import asyncio
import json

from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "Discord Steam Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_web).start()

CHANNEL_ID = 856527775069503530

intents = discord.Intents.default()
client = discord.Client(intents=intents, heartbeat_timeout=60)

print("CLIENT CREATED", flush=True)

# -----------------------------
# EVENTS
# -----------------------------
@client.event
async def on_connect():
    print("ON_CONNECT FIRED", flush=True)

@client.event
async def on_error(event, *args, **kwargs):
    print("DISCORD ERROR:", event)

@client.event
async def on_resumed():
    print("ON_RESUMED FIRED")

# -----------------------------
# STORAGE
# -----------------------------
SEEN_FILE = "seen_deals.json"

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

seen_deals = load_seen()

# -----------------------------
# API
# -----------------------------
def get_deals():
    print("GET_DEALS FUNCTION STARTED")

    api_key = os.getenv("ITAD_API_KEY")

    headers = {"ITAD-API-Key": api_key}

    params = {
        "country": "US",
        "limit": 350
    }

    response = requests.get(
        "https://api.isthereanydeal.com/deals/v2",
        headers=headers,
        params=params
    )

    data = response.json()

    print("Deals received:", len(data["list"]))

    return data["list"]

# -----------------------------
# LOOP
# -----------------------------
async def deal_loop():
    await client.wait_until_ready()

    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            print("Checking deals...")

            deals = get_deals()

            for game in deals:
                deal_id = game["id"]

                if deal_id in seen_deals:
                    continue

                title = game["title"]
                price = float(game["deal"]["price"]["amount"])
                discount = float(game["deal"]["cut"])
                normal_price = game["deal"]["regular"]["amount"]

                print(title, "- Price:", price, "- Discount:", discount)

                # ✅ SAFE CHECK (free games)
                if price <= 0.01 or discount >= 97:

                    # ⚠️ FIXED LINK (NO BROKEN STEAM PAGES)
                    steam_url = game["deal"]["url"]

                    embed = discord.Embed(
                        title=f"🔥 {title} is FREE (-{round(discount)}%)",
                        url=steam_url,
                        description=f"~~${normal_price}~~ → **$0.00**"
                    )

                    embed.set_image(url=game.get("thumb", ""))

                    await channel.send(
                        content="@everyone",
                        embed=embed
                    )

                seen_deals.add(deal_id)

            save_seen(seen_deals)

        except Exception as e:
            print("ERROR:", e)

        print("Still alive 😅")
        await asyncio.sleep(300)

# -----------------------------
# READY
# -----------------------------
@client.event
async def on_ready():
    print("ON_READY FIRED", flush=True)

    channel = client.get_channel(CHANNEL_ID)

    await channel.send("🤖 BOT WORKS!")

    asyncio.create_task(deal_loop())

    print("BOT READY - DEAL LOOP STARTED")

# -----------------------------
# RUN
# -----------------------------
print("TOKEN EXISTS:", bool(os.getenv("TOKEN")), flush=True)
print("CHANNEL ID:", CHANNEL_ID, flush=True)

client.run(os.getenv("TOKEN"))
