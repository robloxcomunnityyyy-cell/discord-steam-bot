import os
import discord
import requests
import asyncio
import json
from flask import Flask
from threading import Thread

print("BOT STARTING...")

# ---------------- KEEP ALIVE SERVER ----------------
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

Thread(target=lambda: app.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 10000))
)).start()

# ---------------- DISCORD ----------------
CHANNEL_ID = 856527775069503530

intents = discord.Intents.default()
client = discord.Client(intents=intents, heartbeat_timeout=60)

# ---------------- SEEN STORAGE ----------------
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

# ---------------- STORE FILTER ----------------
def is_allowed_store(game):
    """
    Only allow Steam and Epic Games Store deals
    """
    try:
        store = game.get("deal", {}).get("store", {}).get("name", "")
        store = store.lower()

        return (
            "steam" in store or
            "epic" in store
        )
    except:
        return False

# ---------------- API ----------------
def get_deals():
    api_key = os.getenv("ITAD_API_KEY")
    if not api_key:
        print("Missing ITAD API KEY")
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

        if r.status_code != 200:
            print("API ERROR:", r.status_code, r.text[:200])
            return []

        data = r.json()
        return data.get("list", [])

    except Exception as e:
        print("REQUEST ERROR:", e)
        return []

# ---------------- BOT LOOP ----------------
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

                # skip duplicates
                if deal_id in seen_deals:
                    continue

                # store filter (Steam + Epic only)
                if not is_allowed_store(game):
                    continue

                try:
                    discount = float(game["deal"]["cut"])
                except:
                    continue

                # 90%+ only
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

# ---------------- EVENTS ----------------
@client.event
async def on_ready():
    print("BOT ONLINE")

    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🤖 Bot is now online!")

    asyncio.create_task(deal_loop())

# ---------------- RUN ----------------
client.run(os.getenv("TOKEN"))
