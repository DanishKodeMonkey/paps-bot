"""
Discord bot for coordinating pen-and-paper-shenanigans
"""
import random
import logging
import psycopg2
import discord
from discord.ext import commands
from paps_bot.database import create_connection, create_session_sql, create_table_sql

# create the bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="$", intents=intents)
# get the bot logger
logger = logging.getLogger("discord")


def start(token: str) -> None:
    """Function to wake the bot"""
    logger.info("Starting paps-bot ...")
    bot.run(token)


@bot.event
async def on_ready():
    """Executed when the bot joins the discord server"""
    logger.info("We have logged in as %s", bot.user)


@bot.event
async def on_guild_join():
    """Once logged in, initiate the db if it does not already exist."""
    logger.info("Establishing connection to postgreSQL databse ...")
    conn = create_connection()
    create_table_sql(conn)
    conn.close()


@bot.command(name="hello", help="Answers with an appropriate hello message")
async def hello(ctx):
    """Funny function to say hello in various ways"""
    options = [
        f"Ahoy {ctx.message.author.mention}!",
        f"Hello there, Choom {ctx.message.author.mention}!",
        f"Sup,  {ctx.message.author.mention}?",
        f"Good day to you, {ctx.message.author.mention}!",
        f"Hooooi {ctx.message.author.mention}!",
        f"{ctx.message.author.mention}, Wha chu want?!",
        f"Howdy, {ctx.message.author.mention}!",
    ]

    response = random.choice(options)
    logger.info("Sending message %s ...", response)
    await ctx.send(response)


@bot.command(
    name="make-event",
    help="(TEST)Creates an session using the given parameters:"
    "Table name: The table on the SQL server to send this to"
    "game type the game type to set CPR or DND"
    "game date The day of the session format DD-MM-YYYY"
    "gate time The time the game is set to occour HH:MM"
    "**Note:** Parameters are seperated by spaces",
)
async def make_event(ctx, input_type, input_date, input_time):
    """Function to make an event"""
    print("Received data:")
    print(input_type, input_date, input_time)
    conn = create_connection()
    if conn is not None:
        try:
            create_session_sql(conn, input_type, input_date, input_time)
            conn.close()
        except psycopg2.Error as err:
            conn.close()

            await ctx.send(f"An exception has occured: {err}")
            return
    await ctx.send("Event sent")
