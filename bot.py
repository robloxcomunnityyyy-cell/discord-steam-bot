import os
import discord
import requests
import asyncio
import json
from flask import Flask
from threading import Thread
import traceback

print("🚀 BOT FILE LOADED")

# ---------------- KEEP ALIVE ----------------
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

# ---------------- STORAGE ----------------
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
    store = game.get("deal", {}).get("store", {}).get("name", "")
    store = store.lower()

    allowed = ("steam" in store) or ("epic" in store)

    if not allowed:
        print(f"🚫 SKIP STORE: {store}")

    return allowed

# ---------------- API ----------------
def get_deals():
    api_key = os.getenv("ITAD_API_KEY")

    if not api_key:
        print("❌ Missing API key")
        return []

    print("📡 REQUESTING API...")

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

        print(f"📡 STATUS CODE: {r.status_code}")

        if r.status_code != 200:
            print("❌ API ERROR RESPONSE:")
            print(r.text[:300])
            return []

        data = r.json()
        deals = data.get("list", [])

        print(f"📦 RAW DEALS RECEIVED: {len(deals)}")

        return deals

    except Exception as e:
        print("❌ REQUEST FAILED:")
        print(e)
        return []

# ---------------- LOOP ----------------
async def deal_loop():
    await client.wait_until_ready()

    print("🟢 LOOP INITIALIZED")

    channel = client.get_channel(CHANNEL_ID)

    if not channel:
        print("❌ CHANNEL NOT FOUND")
        return

    while not client.is_closed():
        try:
            print("\n🔁 NEW CYCLE STARTED")

            deals = get_deals()

            print(f"📊 DEALS FOUND THIS CYCLE: {len(deals)}")

            new_count = 0

            for i, game in enumerate(deals):

                deal_id = game.get("id")

                if not deal_id:
                    print(f"⚠️ SKIP NO ID [{i}]")
                    continue

                if deal_id in seen_deals:
                    print(f"🔁 ALREADY SEEN: {deal_id}")
                    continue

                if not is_allowed_store(game):
                    continue

                try:
                    discount = float(game["deal"]["cut"])
                except:
                    print("⚠️ BAD DISCOUNT DATA")
                    continue

                print(f"🎮 {game.get('title')} - {discount}%")

                if discount < 90:
                    print("❌ BELOW THRESHOLD")
                    continue

                title = game.get("title", "Unknown")
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

                print(f"✅ SENT: {title}")

                seen_deals.add(deal_id)
                new_count += 1

            if new_count > 0:
                save_seen(seen_deals)
                print(f"💾 SAVED {new_count} NEW DEALS")

            print("💤 CYCLE COMPLETE - SLEEPING 180s")

        except Exception:
            print("❌ LOOP CRASHED:")
            traceback.print_exc()

        await asyncio.sleep(180)

# ---------------- EVENTS ----------------
@client.event
async def on_ready():
    print("🤖 DISCORD CONNECTED")
    print(f"Bot: {client.user}")

    channel = client.get_channel(CHANNEL_ID)

    if channel:
        await channel.send("🤖 Bot online!")

    client.loop.create_task(deal_loop())

# ---------------- RUN ----------------
client.run(os.getenv("TOKEN"))
