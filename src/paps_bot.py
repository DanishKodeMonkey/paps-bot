import os
import sys
import discord

TOKEN = os.environ.get("DISCORD_TOKEN", None)
if not TOKEN:
    sys.exit(1, "ERROR: Could not find env var DISCORD_TOKEN, exitting.")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")


client.run(TOKEN)
