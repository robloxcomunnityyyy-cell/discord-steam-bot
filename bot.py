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

CHANNEL_ID = 856527775069503530  # your channel ID

intents = discord.Intents.default()
client = discord.Client(
    intents=intents,
    heartbeat_timeout=60
)

print("CLIENT CREATED", flush=True)

async def test_task():
    while True:
        print("BACKGROUND TASK RUNNING", flush=True)
        await asyncio.sleep(300)

@client.event
async def on_connect():
    print("ON_CONNECT FIRED", flush=True)

# -----------------------------
# Persistent storage (NO REPEATS EVER)
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
# GET DEALS
# -----------------------------
def get_deals():
    print("GET_DEALS FUNCTION STARTED")
    api_key = os.getenv("ITAD_API_KEY")

    print("API KEY LENGTH:", len(api_key))
    print("FIRST 5:", api_key[:5])
    print("API KEY EXISTS:", bool(api_key))

    headers = {
        "ITAD-API-Key": api_key
    }

    params = {
        "country": "US",
        "limit": 50
    }

    response = requests.get(
        "https://api.isthereanydeal.com/deals/v2",
        headers=headers,
        params=params
    )

    print("Status:", response.status_code)

    data = response.json()

    print("Deals received:", len(data["list"]))

    return data["list"]

# -----------------------------
# BOT START
# -----------------------------
@client.event
async def on_ready():
    asyncio.create_task(test_task())
    print("ON_READY FIRED", flush=True)

    channel = client.get_channel(CHANNEL_ID)

    print("CHANNEL =", channel)

    print("BOT READY - STARTING DEAL CHECK")

    deals = get_deals()

    for game in deals:
        price = game["deal"]["price"]["amount"]

        print(
            game["title"],
            "- Price:",
            price,
            "- Discount:",
            game["deal"]["cut"]
        )

        if price == 0:
            print("FREE GAME FOUND:", game["title"])

@client.event
async def on_resumed():
    print("ON_RESUMED FIRED")

@client.event
async def on_error(event, *args, **kwargs):
    print("DISCORD ERROR:", event)

print("TOKEN EXISTS:", bool(os.getenv("TOKEN")), flush=True)
print("CHANNEL ID:", CHANNEL_ID, flush=True)

client.run(os.getenv("TOKEN"))
