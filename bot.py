import discord
import requests
import asyncio
import json
import os

TOKEN = "MTUxMDI5NzEwNjgzMTkwMDg3Ng.Go-Zf3.lGMawsi8hmj447WaPPA-u28XDPmvNVkc9LQIp0"
CHANNEL_ID = 856527775069503530  # replace this

intents = discord.Intents.default()
client = discord.Client(intents=intents)

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
    url = "https://www.cheapshark.com/api/1.0/deals?storeID=1&upperPrice=50"
    return requests.get(url).json()

# -----------------------------
# BOT START
# -----------------------------
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)

    while True:
        try:
            deals = get_deals()

            for game in deals:
                deal_id = game["dealID"]  # better unique ID

                if deal_id in seen_deals:
                    continue

                title = game["title"]
                savings = float(game["savings"])
                normal_price = game["normalPrice"]
                sale_price = game["salePrice"]
                app_id = game["steamAppID"]

                if not app_id or app_id == "0":
                    continue

                steam_url = f"https://store.steampowered.com/app/{app_id}/"

                # only good deals
                if savings >= 70:
                    embed = discord.Embed(
                        title=f"{title} is now -{round(savings)}%",
                        url=steam_url,
                        description=(
                            f"💰 ~~${normal_price}~~ → **${sale_price}**\n"
                            f"🔥 Huge Steam discount!"
                        )
                    )

                    embed.set_image(url=game["thumb"])

                    await channel.send(
                        content="@everyone",
                        embed=embed
                    )

                # mark as seen no matter what (prevents spam forever)
                seen_deals.add(deal_id)

            save_seen(seen_deals)

        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(300)  # 5 minutes

client.run(TOKEN)