import os
import discord
import asyncio

print("🚀 BOT FILE LOADED")

CHANNEL_ID = 856527775069503530

intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ---------------- LOOP TEST ----------------
async def loop_test():
    await client.wait_until_ready()

    print("🟢 LOOP STARTED (THIS MUST PRINT EVERY 10s CHECK)")

    channel = await client.fetch_channel(CHANNEL_ID)

    counter = 0

    while True:
        counter += 1

        print(f"🔁 LOOP RUNNING #{counter}")

        try:
            await channel.send(f"🤖 test message #{counter}")
            print("✅ MESSAGE SENT")
        except Exception as e:
            print("❌ SEND FAILED:", e)

        await asyncio.sleep(10)

# ---------------- EVENTS ----------------
@client.event
async def on_ready():
    print("🤖 ON_READY FIRED")
    print("USER:", client.user)

    asyncio.create_task(loop_test())

# ---------------- RUN ----------------
token = os.getenv("TOKEN")

if not token:
    print("❌ NO TOKEN FOUND")
else:
    client.run(token)
