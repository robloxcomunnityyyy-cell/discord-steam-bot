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

Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))).start()

CHANNEL_ID = 856527775069503530

intents = discord.Intents.default()
client = discord.Client(intents=intents, heartbeat_timeout=60)

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

def get_deals():
    api_key = os.getenv("ITAD_API_KEY")
    if not api_key:
        return []

    r = requests.get(
        "https://api.isthereanydeal.com/deals/v2",
        headers={"ITAD-API-Key": api_key},
        params={"country": "US", "limit": 50}
    )

    return r.json().get("list", [])

async def deal_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            print("Checking deals...")

            deals = get_deals()

            for game in deals:

                if game.get("type") != "game":
                    continue

                deal_id = game["id"]
                if deal_id in seen_deals:
                    continue

                title = game["title"]
                price = float(game["deal"]["price"]["amount"])
                discount = float(game["deal"]["cut"])
                normal_price = game["deal"]["regular"]["amount"]

                print("FOUND:", title, price, discount, flush=True)

                print("DISCOUNT CHECK:", title, discount, flush=True)
                
                if discount < 70:
                    continue

                print("SENDING:", title, discount, flush=True)
                # ✅ SAFE OFFICIAL LINK (THIS IS THE IMPORTANT FIX)
                steam_url = game["deal"]["url"]

                embed = discord.Embed(
                    title=f"🔥 {title} is {round(discount)}% OFF",
                    url=steam_url,
                    description=f"~~${normal_price}~~ → **${price}**"
                )

                embed.set_image(url=game.get("assets", {}).get("boxart", ""))

                await channel.send(content="@everyone", embed=embed)

                seen_deals.add(deal_id)

            save_seen(seen_deals)

        except Exception as e:
            print("ERROR:", e)

        await asyncio.sleep(300)

@client.event
async def on_ready():
    print("ON_READY FIRED")
    channel = client.get_channel(CHANNEL_ID)
    await channel.send("🤖 BOT WORKS!")
    asyncio.create_task(deal_loop())

client.run(os.getenv("TOKEN"))
