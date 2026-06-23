import os
import discord
import requests
import asyncio
import json
from flask import Flask
from threading import Thread

print("NEW VERSION LOADED")

# ---------------- Flask keep-alive ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Discord Steam Bot is running!"

Thread(target=lambda: app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 10000))
)).start()

# ---------------- Discord setup ----------------
CHANNEL_ID = 856527775069503530

intents = discord.Intents.default()
client = discord.Client(intents=intents, heartbeat_timeout=60)

# ---------------- Memory ----------------
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

# ---------------- API ----------------
def get_deals():
    api_key = os.getenv("ITAD_API_KEY")
    if not api_key:
        return []

    try:
        r = requests.post(
            "https://api.isthereanydeal.com/deals/v2",
            headers={"ITAD-API-Key": api_key},
            json={
                "country": "US",
                "offset": 0,
                "limit": 100
                # ⚠️ filters removed for stability first
            },
            timeout=20
        )

        print("STATUS:", r.status_code)

        data = r.json()
        return data.get("list", [])

    except Exception as e:
        print("API ERROR:", e)
        return []

# ---------------- Bot loop ----------------
async def deal_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            deals = get_deals()

            print("DEALS FOUND:", len(deals))

            new_count = 0

            for game in deals:

                deal_id = game.get("id")
                if not deal_id:
                    continue

                # prevent duplicates
                if deal_id in seen_deals:
                    continue

                discount = float(game["deal"]["cut"])

                # 🎯 your target rule
                if discount < 90:
                    continue

                title = game.get("title", "Unknown Game")
                price = game["deal"]["price"]["amount"]
                normal = game["deal"]["regular"]["amount"]
                url = game["deal"]["url"]

                embed = discord.Embed(
                    title=f"🔥 {title} is {round(discount)}% OFF",
                    url=url,
                    description=f"~~${normal}~~ → **${price}**"
                )

                img = game.get("assets", {}).get("boxart")
                if img:
                    embed.set_image(url=img)

                await channel.send(content="@everyone", embed=embed)

                seen_deals.add(deal_id)
                new_count += 1

            if new_count > 0:
                save_seen(seen_deals)
                print(f"Sent {new_count} deals")

        except Exception as e:
            print("LOOP ERROR:", e)

        await asyncio.sleep(180)

# ---------------- Events ----------------
@client.event
async def on_ready():
    print("ON_READY FIRED")

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🤖 BOT ONLINE!")

    asyncio.create_task(deal_loop())

# ---------------- Run ----------------
client.run(os.getenv("TOKEN"))
