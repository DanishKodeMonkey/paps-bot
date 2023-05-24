"""
Discord bot for coordinating pen-and-paper-shenanigans
"""
import os
import sys
import discord

TOKEN = os.environ.get("DISCORD_TOKEN", None)
if not TOKEN:
    print("ERROR: Could not find env var DISCORD_TOKEN, exitting.")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    """Executed when the bot joins the discord server"""
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    """executed when a message is sent that the bot can read"""
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")


client.run(TOKEN)
