"""
Discord bot for coordinating pen-and-paper-shenanigans
"""
import random
import logging
import psycopg2
from psycopg2 import sql
import discord
from discord.ext import commands
from paps_bot.database import create_connection, create_session_sql, create_table_sql
from datetime import time

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
    logger.info("Creating table, if it does not exist already.")
    """Create table, if it does not already exist"""
    create_table_sql()
    logger.info("Ready!")

@bot.command(
    name="make-event",
    help="Creates an event using the given parameters:"
    "Table name: The table on the SQL server to send this to"
    "game type the game type to set CPR or DND"
    "game date The day of the event format DD-MM-YYYY"
    "gate time The time the event is set to occour HH:MM"
    "**Note:** Parameters are seperated by spaces"
)
async def make_event(ctx, game_type, game_date, game_time):
    """Function to insert a new event into paps_table table"""
    try:
        logger.info(f"make-event command executed from discord! Data received:\n {ctx}\nType:{game_type}, Date:{game_date}, TIME:{game_time}")
        """
        Some formatting of game_time, we will never set an event to a specific second
        So in order for SQL to accept just HH:MM we need to add it to whatever is input
        """
        game_time = game_time + ":00" #Required, add seconds as 00 to query
        game_time = time.fromisoformat(game_time) #Convert above to time object to insert to query.
        
        logger.info("Establishing connection to database...")
        conn = create_connection()
        cur = conn.cursor()
        logger.info("Connection established, cursor created...")

        logger.info("Sending SQL query to database...")
        cur.execute(f"""INSERT INTO paps_table (game_type, game_date, game_time) 
                    VALUES ('{game_type}', '{game_date}', '{game_time}')""")
        
        logger.info(f"Attempting to add event to paps_table:\n Type: {game_type}, Date: {game_date}, Time: {game_time}")
        conn.commit()
        cur.close()
        conn.close()

        await ctx.send("Event added to database paps_table")
        logger.info("Event succesfully added! Connection closed...")
    except(psycopg2.Error, discord.DiscordException) as e:
        await ctx.send(f"An error has occured: {str(e)}")
        logger.info(f"Error occured: {str(e)}\nConnection closed...")

@bot.command(
        name="list-events",
        help="List all currently planned event"
        "\nFiltering options:"
        "\nYou can filter the list by using flags. Eg --game_date (MM/DD/YYYY)"
        "\nMake sure to use them in order:"
        "\n--game_id - Find a event by its unique id(int)"
        "\n--game_type - Find an event by its type(cpr=CyberPunk Red, dnd = Dungeons and Dragons)"
        "\n--game_date - Find an event by its date(MM/DD/YYYY)"
        "\n--game_time - Find an event by its time(HH:MM)"
        "\nIf no filters are used, all events will be listed."
             )
async def list_events(ctx, game_id=None, game_type=None, game_date=None, game_time=None):
    """Function to fetch all events, and return them to discord."""
    try:
        logger.info(f"list_events command executed from discord!\nData received:\n{ctx}, {game_type}, {game_date},{game_time},{game_id}")

        """Establish connection to database"""
        logger.info("Establishing connection to database...")
        conn = create_connection()
        cur = conn.cursor()
        logger.info("Connection established, cursor created...\nCOMMENCING OPERATION!")
        
        query = "SELECT game_id, game_type, game_date, game_time FROM paps_table"
    #FIX THIS ;_;
        if game_id:
            query += f" WHERE game_id = {game_id}"
        elif game_type:
            query += f" WHERE game_type = '{game_type}'"
        elif game_date:
            query += f" WHERE game_date = '{game_date}'"
        elif game_time:
            query += f" WHERE game_time = '{game_time}'"

        cur.execute(query)
        """Once data is acquired, assign to rows."""
        logger.info("Data succesfully fetched!")
        rows = cur.fetchall()

        """Data acquired, close connection"""
        logger.info("Closing connection...")
        cur.close()
        conn.close()

        """Process the data fetched from database, join data if filtered. Otherwise use as-is"""
        logger.info("Now processing fetched data...")
        if rows:
            event_list = "\n".join(f"{game_id} - {game_type} - {game_date} - {game_time}" 
                                   for game_id, game_type, game_date, game_time in rows)
            logger.info(f"Processing complete...\nattempting to send event_list to discord:\n{event_list}\nOperation sucessful!")
            await ctx.send(f"Current Events:\n{event_list}")
        else:
            logger.info("Processing failed, no events found in database...")
            await ctx.send("There were no events found.")
    except psycopg2.Error as e:
        logger.info(f"An error has occured: {str(e)}")
        await ctx.send(f"An error has occured: {str(e)}")


@bot.event
async def on_guild_join():
    """Once a guild is joined, initiate the db if it does not already exist."""
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