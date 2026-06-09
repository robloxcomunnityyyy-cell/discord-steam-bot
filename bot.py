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
    print("DISCORD ERROR:", event, flush=True)

@client.event
async def on_resumed():
    print("ON_RESUMED FIRED", flush=True)

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
    print("GET_DEALS FUNCTION STARTED", flush=True)

    api_key = os.getenv("ITAD_API_KEY")

    if not api_key:
        print("ERROR: Missing API key", flush=True)
        return []

    headers = {
    "ITAD-API-Key": api_key
}

    params = {
        "country": "US",
        "limit": 350
    }

    response = requests.get(
        "https://api.isthereanydeal.com/deals/v2",
        headers=headers,
        params=params
    )

    print("STATUS:", response.status_code, flush=True)
    print("RAW TEXT:", response.text[:300], flush=True)

    try:
        data = response.json()
    except Exception as e:
        print("JSON ERROR:", e, flush=True)
        return []

    print("RAW KEYS:", data.keys() if isinstance(data, dict) else "NOT A DICT", flush=True)

    deals = data.get("list") or data.get("data") or []

    print("Deals received:", len(deals), flush=True)

    return deals
# -----------------------------
# LOOP
# -----------------------------
async def deal_loop():
    await client.wait_until_ready()

    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            print("Checking deals...", flush=True)

            deals = get_deals()

            for game in deals:
                deal_id = game["id"]

                if deal_id in seen_deals:
                    continue

                title = game["title"]
                price = float(game["deal"]["price"]["amount"])
                discount = float(game["deal"]["cut"])
                normal_price = game["deal"]["regular"]["amount"]

                print("FOUND:", title, price, discount, flush=True)
                print(title, "- Price:", price, "- Discount:", discount, flush=True)

                # SAFE CHECK
                if discount >= 10:

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
            print("ERROR:", e, flush=True)

        print("Still alive 😅", flush=True)
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

    print("STARTING DEAL LOOP...", flush=True)

# -----------------------------
# RUN
# -----------------------------
print("TOKEN EXISTS:", bool(os.getenv("TOKEN")), flush=True)
print("CHANNEL ID:", CHANNEL_ID, flush=True)

client.run(os.getenv("TOKEN"))
