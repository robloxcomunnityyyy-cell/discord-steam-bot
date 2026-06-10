import os
print("NEW VERSION LOADED")

import discord
import asyncio
import json
import aiohttp
from flask import Flask
from threading import Thread

# ---------------- Flask keepalive ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Discord Steam Bot is running!"

Thread(
    target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
).start()

# ---------------- CONFIG ----------------
CHANNEL_ID = 856527775069503530
API_URL = "https://api.isthereanydeal.com/deals/v2"

SEEN_FILE = "seen_deals.json"

intents = discord.Intents.default()
client = discord.Client(intents=intents, heartbeat_timeout=60)

# ---------------- STATE ----------------
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

# ---------------- FETCH DEALS (NON-BLOCKING) ----------------
async def get_deals(session):
    api_key = os.getenv("ITAD_API_KEY")
    if not api_key:
        return []

    headers = {"ITAD-API-Key": api_key}
    params = {"country": "US", "limit": 50}

    try:
        async with session.get(API_URL, headers=headers, params=params, timeout=30) as r:
            data = await r.json()
            return data.get("list", [])
    except Exception as e:
        print("API ERROR:", e)
        return []

# ---------------- MAIN LOOP ----------------
async def deal_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    async with aiohttp.ClientSession() as session:
        while not client.is_closed():
            try:
                deals = await get_deals(session)

                print("DEALS FOUND:", len(deals))

                new_count = 0

                for game in deals:
                    deal_id = game.get("id")
                    if not deal_id:
                        continue

                    # already seen → skip
                    if deal_id in seen_deals:
                        continue

                    seen_deals.add(deal_id)

                    if game.get("type") != "game":
                        continue

                    discount = float(game["deal"]["cut"])
                    if discount < 10:   # <-- change threshold here
                        continue

                    title = game["title"]
                    price = game["deal"]["price"]["amount"]
                    normal = game["deal"]["regular"]["amount"]
                    url = game["deal"]["url"]

                    embed = discord.Embed(
                        title=f"🔥 {title} is {round(discount)}% OFF",
                        url=url,
                        description=f"~~${normal}~~ → **${price}**"
                    )

                    boxart = game.get("assets", {}).get("boxart")
                    if boxart:
                        embed.set_image(url=boxart)

                    await channel.send(content="@everyone", embed=embed)
                    new_count += 1

                if new_count > 0:
                    print(f"Sent {new_count} new deals")

                save_seen(seen_deals)

            except Exception as e:
                print("LOOP ERROR:", e)

            # IMPORTANT: 5 minute interval
            await asyncio.sleep(300)

# ---------------- READY ----------------
@client.event
async def on_ready():
    print("ON_READY FIRED")

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🤖 Bot is online!")

    asyncio.create_task(deal_loop())

client.run(os.getenv("TOKEN"))
