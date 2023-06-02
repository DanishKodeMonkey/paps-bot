"""
Discord bot for coordinating pen-and-paper-shenanigans
"""
import os
import sys
import discord

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def start(token:str) -> None:
    client.run(token)

@client.event
async def on_ready():
    """Executed when the bot joins the discord server"""
    print(f"We have logged in as {client.user}")

@client.event
async def on_message(message):
    """executed when a message is sent that the bot can read"""
    print("responding to message ...")
    if message.author == client.user:
        return

    if message.content.startswith("$hello"):
        await message.channel.send("Hello world! This is the dev version of paps-bot.")


