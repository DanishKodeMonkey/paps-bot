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
import asyncio

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
    name="make-eventvote",
    help="Creates an event using the given parameters USING A VOTE:"
    "Table name: The table on the SQL server to send this to"
    "game type the game type to set CPR or DND"
    "game date The day of the event format DD-MM-YYYY"
    "gate time The time the event is set to occour HH:MM"
    "**Note:** Parameters are seperated by spaces"
)
async def make_eventvote(ctx, game_type, game_date, game_time):
    """Function to insert a new event into paps_table table"""
    try:
        logger.info(f"make-eventvote command executed from discord! Data received:\n {ctx}\nType:{game_type}, Date:{game_date}, TIME:{game_time}")

        """
        Some formatting of game_time, we will never set an event to a specific second
        So in order for SQL to accept just HH:MM we need to add it to whatever is input
        """
        logger.info(f"Adjusting time format for {game_time} to HH:MM...")
        game_time = game_time + ":00" #Required, add seconds as 00 to query
        game_time = time.fromisoformat(game_time) #Convert above to time object to insert to query.
        logger.info("Now initiating vote!")
        
        """Below, the voting process starts!"""
        #Set up some settings:
        thumbs_up = '👍'
        thumbs_down = '👎'
        voting_period = 86_400  # in seconds
        count_limit_success = 3
        count_limit_fail = 2
        # Send event details to discord channel.
        event_message = await ctx.send(f"New event submitted for vote!:\nGame type:{game_type}\nDate: {game_date}\n Time: {game_time}\nVote with {thumbs_up} or {thumbs_down}.")

        # Add thumbs-up and thumbs-down reactions to the message.
        await event_message.add_reaction(thumbs_up)
        await event_message.add_reaction(thumbs_down)

        # Set up event handlers to listen for reactions to the message.
        def check(reaction, user):
            return user!= bot.user and reaction.message.id == event_message.id and str(reaction.emoji) in [thumbs_up, thumbs_down]
        
        try:
            # Vote counters here
            thumbs_up_count = 0
            thumbs_down_count = 0

            while True:
                    reaction, _ = await bot.wait_for('reaction_add', timeout= voting_period, check=check)
                    if reaction.emoji == thumbs_up:
                        thumbs_up_count += 1
                    elif reaction.emoji == thumbs_down:
                        thumbs_down_count += 1

                    if thumbs_up_count >= count_limit_success:
                        conn = create_connection()
                        cur = conn.cursor()

                        cur.execute("INSERT INTO paps_table (game_type, game_date, game_time) VALUES (%s, %s, %s)", (game_type, game_date, game_time))
                        conn.commit()

                        cur.close()
                        conn.close()

                        await ctx.send("The event has received enough votes, and was saved!")
                        break
                    
                    if thumbs_down_count >= count_limit_fail:
                        await ctx.send("The event received too many down-votes, and will not be saved!")
                        break
                
                    if thumbs_up_count < count_limit_success and thumbs_down_count < count_limit_fail:
                        await ctx.send("Not enough votes. Event not saved.")
                
                    await ctx.send("The voting period has ended.")
        
        except asyncio.timeoutError:
            await ctx.send("Voting period haas ended")
    except psycopg2.Error as e:
        await ctx.send(f"An error has occured: {str(e)}")


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
        conn = create_connection()
        cur = conn.cursor()
#THIS JUST WONT WORK REEE
        query = "SELECT game_id, game_type, game_date, game_time FROM paps_table WHERE TRUE"

        try:
            if game_id:
                query += " AND game_id = %s"
                cur.execute(query, (game_id,))
            if game_type:
                query += " AND game_type = %s"
                cur.execute(query, (game_type,))
            if game_date:
                query += " AND game_date = %s"
                cur.execute(query, (game_date,))
            if game_time:
                query += " AND game_time = %s"
                cur.execute(query, (game_time,))

            rows = cur.fetchall()
        except (psycopg2.Error, Exception) as e:
            await ctx.send(f"An error occurred while executing the query: {str(e)}")
            return

        cur.close()
        conn.close()

        if rows:
            event_list = "\n".join(f"{row[0]} - {row[1]} - {row[2]} - {row[3]}" for row in rows)
            await ctx.send(f"Current Events:\nID - TYPE - DATE - TIME\n{event_list}")
        else:
            await ctx.send("There are no events.")
    except psycopg2.Error as e:
        await ctx.send(f"An error occurred: {str(e)}")

@bot.command(
        name="delete-event"
        help="\nDelete an event by game_id"
)
async def delete_event(ctx, game_id: int):
    try:
        conn = create_connection()
        cur = conn.cursor()

        query = "DELETE FROM paps_table WHERE id = %s"
        cur.execute(query, (game_id,))
        conn.commit()
    
        if cur.rowcount > 0:
            await ctx.send(f"Event with ID {game_id} has been deleted.")
        else:
            await ctx.send(f"No event found with ID: {game_id}.")
    
        cur.close()
        conn.close()
    except psycopg2.Error as e:
        await ctx.ssend(f"An error has occured: {str(e)}")
    
bot.command(
    name="edit-event"
    help="Edit an event by game_id"
    "\n Syntax: edit-event game_id --flag value"
    "\n usable flags:"
    "\n --game_type"
    "\n --game_date"
    "\n --game_time"
)
async def edit_event(ctx, game_id: int, game_type=None, game_date=None, game_time=None):
    try:
        conn = create_connection()
        cur = conn.cursor()

        query = "UPDATE paps_table SET"

        if game_type: 
            query += " game_type = %s,"
        if game_date: 
            query += " game_date = %s,"
        if game_time: 
            query += " game_type = %s,"

        # Remove the trailing comma from the query
        query = query.rstrip(',')

        query +=" WHERE id = %s"
        cur.execute(query, (game_type, game_date, game_time, game_id))

        conn.commit()

        if cur.rowcount >0:
            await ctx.send(f"Event with ID:{game_id} has been updated.")
        else:
            await ctx.send(f"No event found with ID: {game_id}.")
        
        cur.close()
        conn.close()
    except psycopg2.Error as e:
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