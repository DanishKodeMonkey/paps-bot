"""
Discord bot for coordinating pen-and-paper-shenanigans
"""
import random
import logging
from datetime import time
from datetime import datetime
import asyncio
import psycopg2
import discord
from discord.ext import commands
from paps_bot.database import create_connection, create_table_sql


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


def format_date(date_str, format_str):
    """Function to format EU date formats DD-MM-YYYY to SQL accepted time object"""
    try:
        logger.info(f"Attempting to format time: {date_str}")
        date_obj = datetime.strptime(date_str, format_str)
        logger.info(f"Time succesfully formatted: {date_obj.date()}")
        return date_obj.date()
    except ValueError as Err:
        logger.error(f"Time formatting error detected: \n{Err}")
        return None


@bot.event
async def on_ready():
    """Executed when the bot joins the discord server"""
    logger.info("We have logged in as %s", bot.user)
    logger.info("Creating table, if it does not exist already.")
    """Create table, if it does not already exist"""
    create_table_sql()
    logger.info("========= Ready! =========")


@bot.command(
    name="make-event-novote",
    help="Creates an event using the given parameters:"
    "Table name: The table on the SQL server to send this to"
    "game type the game type to set CPR or DND"
    "game date The day of the event format DD-MM-YYYY"
    "gate time The time the event is set to occour HH:MM"
    "**Note:** Parameters are seperated by spaces",
)
async def make_event_novote(ctx, game_type, game_date, game_time):
    """Bot command to insert a new event into paps_table table, voiding vote process."""
    try:
        logger.info(
            f"\n============= Forced make-event command executed from discord! NO VOTE WILL BE MADE! =============\n Data received:\n {ctx}\nType:{game_type}, Date:{game_date}, TIME:{game_time}"
        )
        """
        Some formatting of game_time, we will never set an event to a specific second
        So in order for SQL to accept just HH:MM we need to add it to whatever is input
        """
        logger.info("Formatting game time to SQL acceptable HH:MM:SS format")
        game_time = game_time + ":00"  # Required, add seconds as 00 to query
        game_time = time.fromisoformat(
            game_time
        )  # Convert above to time object to insert to query.
        game_date = format_date(
            game_date, "%d-%m-%Y"
        )  # Formart EU standard date format to SQL date format.

        logger.info("Establishing connection to database...")
        conn = create_connection()
        cur = conn.cursor()
        logger.info("Connection established, cursor created...")

        logger.info("Sending SQL query to database...")
        cur.execute(
            f"""INSERT INTO paps_table (game_type, game_date, game_time) 
                    VALUES ('{game_type}', '{game_date}', '{game_time}')"""
        )

        logger.info(
            f"Attempting to add event to paps_table:\n Type: {game_type}, Date: {game_date}, Time: {game_time}"
        )
        conn.commit()
        cur.close()
        conn.close()

        await ctx.send("Event added to database paps_table")
        logger.warn("========= Event succesfully added! Connection closed... =========")
    except (psycopg2.Error, discord.DiscordException) as Err:
        await ctx.send(f"======== An error has occured: ======== \n{str(Err)}")
        logger.error(
            f"======== Error occured: ======== \n{str(Err)}\nConnection closed..."
        )


@bot.command(
    name="make-event",
    help="\nCreates an event using the given parameters USING A VOTE:"
    "\nSyntax: make-event (Type) (Date) (Time) seperated by spaces"
    "\nType - CPR or DND"
    "\nDate - DD-MM-YYYY"
    "\nTime - HH:MM",
)
async def make_eventvote(ctx, game_type, game_date, game_time):
    """Function to insert a new event into paps_table table provided it passes a vote"""
    try:
        logger.info(
            f"\n============== make-event command executed from discord! ================ Data received:\n {ctx}\nType:{game_type}, Date:{game_date}, TIME:{game_time}"
        )

        """
        Some formatting of date and time to acceptable SQL format
        """
        logger.info(f"Adjusting time format for {game_time} to HH:MM...")
        game_time = game_time + ":00"  # Required, add seconds as 00 to query
        game_time = time.fromisoformat(
            game_time
        )  # Convert above to time object to insert to query.
        game_date = format_date(
            game_date, "%d-%m-%Y"
        )  # Formart EU standard date format to SQL date format.
        logger.info("Now initiating vote!")

        """Below, the voting process starts!"""
        # Set up some settings:
        thumbs_up = "👍"
        thumbs_down = "👎"
        voting_period = 86400  # in seconds, 86400 seconds = 1 day
        count_limit_success = 2
        count_limit_fail = 1
        # Create a neat embed to send with the relevant information:
        embed = discord.Embed(
            title="New event vote created!", color=discord.Color.green()
        )
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.add_field(name="Event Type", value=game_type, inline=False)
        embed.add_field(name="Event Date", value=game_date, inline=False)
        embed.add_field(name="Event Time", value=game_time, inline=False)
        embed.set_footer(text="Vote using 👍 If you can attend, and 👎 if you cannot.")
        # Send event details to discord channel.
        logger.info("Vote ready! - Sending vote to Discord.")
        event_message = await ctx.send(embed=embed)

        # Add thumbs-up and thumbs-down reactions to the message.
        await event_message.add_reaction(thumbs_up)
        await event_message.add_reaction(thumbs_down)

        # Set up event handlers to listen for reactions to the message, making sure to ignore the bots "vote".
        def check(reaction, user):
            return (
                user != bot.user
                and reaction.message.id == event_message.id
                and str(reaction.emoji) in [thumbs_up, thumbs_down]
            )

        try:
            logger.info("Now listening for votes.... fetching coffee while I wait.")
            # Vote counters here
            thumbs_up_count = 0
            thumbs_down_count = 0

            """Below we listen for pass conditions, and react accordingly."""
            while True:
                reaction, _ = await bot.wait_for(
                    "reaction_add", timeout=voting_period, check=check
                )
                # Itteration counters for the emojis
                if reaction.emoji == thumbs_up:
                    thumbs_up_count += 1
                elif reaction.emoji == thumbs_down:
                    thumbs_down_count += 1

                # Pass condition reaction(Enough up-votes)
                if thumbs_up_count >= count_limit_success:
                    logger.info("Vote passed! Processing event to database...")
                    conn = create_connection()
                    cur = conn.cursor()

                    cur.execute(
                        "INSERT INTO paps_table (game_type, game_date, game_time) VALUES (%s, %s, %s)",
                        (game_type, game_date, game_time),
                    )
                    conn.commit()

                    cur.close()
                    conn.close()
                    logger.warn(
                        "========== Event added succesfully, sending to discord! ========"
                    )
                    await ctx.send(
                        "The event has received enough votes, and was saved!"
                    )
                    break

                # Fail condition reaction(Too many down-votes)
                if thumbs_down_count >= count_limit_fail:
                    logger.warn(
                        "========== Vote failed, too many down-votes... =========="
                    )
                    await ctx.send(
                        "The event received too many down-votes, and will not be saved!"
                    )
                    break

        # Fail condition(Vote timeout)
        except asyncio.TimeoutError:
            logger.warn("======= The voting period has ended(Timeout) ========")
            await ctx.send("Voting period has ended")
    except psycopg2.Error as Err:
        logger.error(f"======= An error has occured: =======\n{str(Err)}")
        await ctx.send(f"An error has occured: {str(Err)}")


@bot.command(
    name="list-events",
    help="List all currently planned event"
    "\nFiltering options:"
    "\nYou can filter the list by using flags. Eg --game_date=MM/DD/YYYY"
    "\n--game_id - Find a event by its unique id"
    "\n--game_type - Find an event by its type(cpr=CyberPunk Red, dnd = Dungeons and Dragons)"
    "\n--game_date - Find an event by its date(MM/DD/YYYY)"
    "\n--game_time - Find an event by its time(HH:MM)"
    "\nIf no filters are used, all events will be listed.",
)
async def list_events(ctx, *, args=None):
    """Function to fetch events, and send them to discord."""
    try:
        logger.info(
            f"\n============== list-events command received from discord! ============\n {ctx}\n Filtering by: {args}"
        )
        logger.info("Establishing connection to database...")
        conn = create_connection()
        logger.info("Connection established, creating SQL cursor...")
        cur = conn.cursor()

        # Base query to itterate upon
        query = (
            "SELECT game_id, game_type, game_date, game_time FROM paps_table WHERE TRUE"
        )
        logger.info(f"Established base query:\n{query}")

        """Below we check if any filters were provided with the command, and act accordingly."""
        logger.info("Fetching data...")
        try:
            if args is not None:
                args_list = args.split()
                for arg in args_list:
                    if arg.startswith("--game_id"):
                        game_id = arg.split("=")[1]
                        query += " AND game_id = %s"
                        logger.info(f"Sending query:\n{query}")
                        cur.execute(query, (game_id,))
                    elif arg.startswith("--game_type"):
                        game_type = arg.split("=")[1]
                        query += " AND game_type = %s"
                        logger.info(f"Sending query:\n{query}")
                        cur.execute(query, (game_type,))
                    elif arg.startswith("--game_date"):
                        game_date = arg.split("=")[1]
                        game_date = format_date(game_date, "%d-%m-%Y")
                        if game_date:
                            query += " AND game_date = %s"
                            logger.info(f"Sending query:\n{query}")
                            cur.execute(query, (game_date,))
                    elif arg.startswith("--game_time"):
                        game_time = arg.split("=")[1]
                        query += " AND game_time = %s"
                        logger.info(f"Sending query:\n{query}")
                        cur.execute(query, (game_time,))
            else:
                logger.warn("No valid filter applied...")
                query = (
                    "SELECT game_id, game_type, game_date, game_time FROM paps_table"
                )
                logger.info(f"Sending query:\n{query}")
                cur.execute(query)

            rows = cur.fetchall()
        except (psycopg2.Error, Exception) as Err:
            await ctx.send(f"An error occurred while executing the query: {str(Err)}")
            return
        logger.info("Query sent! Fetch succesfull!")
        logger.info("Closing connection to database...")
        cur.close()
        conn.close()

        logger.info("Now processing fetch data...")
        if rows:
            event_list = "\n".join(
                f"{game_id} - {game_type} - {game_date} - {game_time}"
                for game_id, game_type, game_date, game_time in rows
            )
            logger.info(
                f"Processing succesfull! Final fetch:\n{event_list}\n Sending to discord..."
            )
            await ctx.send(f"Current Events:\nID - TYPE - DATE - TIME\n{event_list}")
            logger.info("====== Discord message sent! =========")
        else:
            logger.warn("========No events found from query...========")
            await ctx.send("There are no events.")
    except psycopg2.Error as Err:
        logger.error(f"======== An error has occured: =======\n{str(Err)}")
        await ctx.send(f"An error occurred: {str(Err)}")


@bot.command(
    name="delete-event",
    help="\nDelete an event by id"
    "\n Syntax: delete-event (ID)"
    "\n HINT: Use list-events to list all events and get IDs",
)
async def delete_event(ctx, game_id: int):
    """A function to delete events from database by game_id"""
    try:
        logger.info(
            f"\n============ delete-event command received from discord! ===========\n {ctx}\n ID to delete: {game_id}"
        )
        logger.info("Establishing connection...")
        conn = create_connection()
        logger.info("Connection succesfull, creating SQL cursor...")
        cur = conn.cursor()

        query = "DELETE FROM paps_table WHERE game_id = %s"
        logger.info(f"Query created: \n{query}")
        cur.execute(query, (game_id,))
        conn.commit()
        logger.info("Sending query...")
        if cur.rowcount > 0:
            logger.info("Event succesfully deleted!")
            await ctx.send(f"Event with ID {game_id} has been deleted.")
        else:
            logger.warn(f"No event found by ID: {game_id}")
            await ctx.send(f"No event found with ID: {game_id}.")

        cur.close()
        conn.close()
    except psycopg2.Error as Err:
        await ctx.ssend(f"An error has occured: {str(Err)}")


bot.command(
    name="edit-event",
    help="Edit an event by game_id"
    "\n Syntax: edit-event game_id --flag value"
    "\n usable flags:"
    "\n --game_type"
    "\n --game_date"
    "\n --game_time",
)


async def edit_event(ctx, game_id: int, game_type=None, game_date=None, game_time=None):
    """A function to edit existing events by id"""
    try:
        logger.info(
            f"\n============ edit-event command received from discord! ===========\n {ctx}\n Game ID to edit: {game_id}\n {game_type}, {game_date}, {game_time}"
        )
        logger.info("Establishing connection to SQL database...")
        conn = create_connection()
        logger.info("Connection established, creating cursor...")
        cur = conn.cursor()

        query = "UPDATE paps_table SET"
        logger.info(f"Base query created: {query}")
        if game_type:
            query += " game_type = %s,"
            logger.info(f"Changing game type to: {game_type}")
        if game_date:
            query += " game_date = %s,"
            logger.info(f"Changing game date to: {game_date}")
        if game_time:
            query += " game_type = %s,"
            logger.info(f"Changing game time to: {game_time}")

        # Remove the trailing comma from the query
        query = query.rstrip(",")

        query += " WHERE id = %s"
        cur.execute(query, (game_type, game_date, game_time, game_id))
        logger.info(f"Finaly query:\n {query}")
        logger.info("Sending query...")
        conn.commit()

        if cur.rowcount > 0:
            logger.info(f"======== Event ID:{game_id} has been updated... ========")
            await ctx.send(f"Event with ID:{game_id} has been updated.")
        else:
            logger.warn(f"========= No event found by ID:{game_id} =========")
            await ctx.send(f"No event found with ID: {game_id}.")

        logger.info("======= Closing connection... ========")
        cur.close()
        conn.close()
    except psycopg2.Error as Err:
        logger.error(f"======== An error has occured: ========\n{str(Err)}")
        await ctx.send(f"An error has occured: {str(Err)}")


@bot.event
async def on_guild_join():
    """Once a guild is joined, initiate the db if it does not already exist."""
    logger.info("Establishing connection to postgreSQL databse ...")
    conn = create_connection()
    logger.info("Creating new table...")
    create_table_sql(conn)
    logger.info("Done, now ready!")
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
