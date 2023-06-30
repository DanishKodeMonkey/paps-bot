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
from discord import app_commands
from discord.ext import commands
from paps_bot.database import create_connection, event_table_SQL, player_table_SQL

"""
Bot shutdown state for graceful shutdown of bot.
"""
IS_SHUTTING_DOWN = False


# create the bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="$", intents=intents)
# get the bot logger
logger = logging.getLogger("discord")


def format_date(date_str, format_str):
    """Function to format EU date formats DD-MM-YYYY to SQL accepted time object"""
    try:
        logger.info("Attempting to format time: %s", date_str)
        date_obj = datetime.strptime(date_str, format_str)
        logger.info("Time successfully formatted: %s", date_obj.date())
        return date_obj.date()
    except ValueError as err:
        logger.error("Time formatting error detected: \n %s", err)
        return None


@bot.event
async def on_ready():
    """Executed when the bot joins the discord server"""
    logger.info("We have logged in as %s", bot.user)
    logger.info("Creating player table, if it does not exist already")
    player_table_SQL()
    logger.info("Done..")
    logger.info("Creating event table, if it does not exist already.")
    # Create table, if it does not already exist
    event_table_SQL()
    logger.info("Done...")

    try:
        synced = await bot.tree.sync()
        logger.info("synced %s command(s)" % (len(synced)))
    except psycopg2.DatabaseError as DBerr:
        logger.error("A database error has occured:\n %s", DBerr)
    except discord.DiscordException as Discerr:
        logger.error(f"A discord error has occured:\n{Discerr}")
    logger.info("========= Ready! =========")


@bot.event
async def on_shutdown():
    """Event handler on_shutdown listens for sigterm signals, and performs an action."""
    global IS_SHUTTING_DOWN
    IS_SHUTTING_DOWN = True
    logger.warning("Bot is shutting down...")
    conn = create_connection()
    conn.rollback()
    conn.close()
    await bot.logout()
    await bot.close()


@bot.event
async def on_guild_join():
    """Once a guild is joined, initiate the db if it does not already exist."""
    logger.info("Establishing connection to postgreSQL databse ...")
    conn = create_connection()
    logger.info("Creating new table...")
    event_table_SQL()
    player_table_SQL()
    logger.info("Done, now ready!")
    conn.close()


@bot.command()
async def bot_shutdown(ctx):
    """Just a command that can be executed to notify users that bot is shutting down."""
    if IS_SHUTTING_DOWN:
        await ctx.send("The bot is currently shutting down...")
        return

@bot.command()
async def sync(ctx):
    logger.info("Manual slash command sync executed...")
    try:
        synced = await bot.tree.sync()
        logger.info("synced %s command(s)" % (len(synced)))
        await ctx.send("Slash commands manually synced...")
    except psycopg2.DatabaseError as DBerr:
        logger.error("A database error has occured:\n %s", DBerr)
    except discord.DiscordException as Discerr:
        logger.error(f"A discord error has occured:\n{Discerr}")

"""============ Hurr hurr for fun commands: ============"""
@bot.tree.command(name="hello", description="Answers with an appropriate hello message")
async def hello(Interaction: discord.Interaction):
    """Funny function to say hello in various ways"""
    options = [
        f"Ahoy {Interaction.user.mention}!",
        f"Hello there, Choom {Interaction.user.mention}!",
        f"Sup,  {Interaction.user.mention}?",
        f"Good day to you, {Interaction.user.mention}!",
        f"Hooooi {Interaction.user.mention}!",
        f"{Interaction.user.mention}, Wha chu want?!",
        f"Howdy, {Interaction.user.mention}!",
    ]

    response = random.choice(options)
    logger.info("Sending message %s ...", response)
    await Interaction.response.send_message(response)

"""========== EVENT related commands ============"""

@bot.tree.command(
    name="make-event-novote",
    description="Create an event using the given parameters, voiding the voting process.",
)
@app_commands.describe(
    game_type="Type of event - CPR or DND",
    game_date="Date of event - DD-MM-YYYY",
    game_time="Time of event - HH:MM",
    player_id="Players forced to attend?",
)
async def make_event_novote(
    Interaction: discord.Interaction, game_type: str, game_date: str, game_time: str, player_id:int
):
    """Bot command to insert a new event into paps_table table, voiding vote process."""
    try:
        logger.info(
            "\n============= Forced make-event command executed from discord! NO VOTE WILL BE MADE! =============\n Data received:\n %s \nType: %s, Date: %s, TIME: %s",
            Interaction.user,
            game_type,
            game_type,
            game_time,
            player_id,
        )
        # Some formatting of game_time, we will never set an event to a specific second
        # So in order for SQL to accept just HH:MM we need to add it to whatever is input
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
            f"""INSERT INTO event_table (game_type, game_date, game_time, player_id) VALUES ('{game_type}', '{game_date}', '{game_time}','{player_id}')"""
        )

        logger.info(
            "Attempting to add event to event_table:\n Type: %s, Date: %s, Time: %s, Attendee ids: %s",
            game_type,
            game_date,
            game_time,
            player_id,
        )
        conn.commit()
        cur.close()
        conn.close()
        embed = discord.Embed(
            title="Event created WITHOUT a vote", color=discord.Color.red()
        )
        embed.set_author(name=Interaction.user, icon_url=Interaction.user.avatar.url)
        embed.add_field(name="Event Type", value=game_type, inline=False)
        embed.add_field(name="Event Date", value=game_date, inline=False)
        embed.add_field(name="Event Time", value=game_time, inline=False)
        embed.add_field(name="Attendee IDs", value=player_id, inline=False)
        embed.set_footer(text="This event was forced, bypassing the vote.")
        await Interaction.response.send_message(embed=embed)
        logger.warning(
            "========= Event succesfully added! Connection closed... ========="
        )
    except (psycopg2.Error, discord.DiscordException) as err:
        await Interaction.channel.send(
            f"======== An error has occured: ======== \n{str(err)}"
        )
        logger.error(
            "======== Error occured: ======== \n %s \nConnection closed...", str(err)
        )


@bot.tree.command(name="make-event", description="Creates a new event")
@app_commands.describe(
    game_type="Type of event - CPR or DND",
    game_date="Date of event - DD-MM-YYYY",
    game_time="Time of event - HH:MM",
)
async def make_eventvote(
    Interaction: discord.Interaction, game_type: str, game_date: str, game_time: str
):
    """Function to insert a new event into paps_table table provided it passes a vote"""
    await Interaction.response.defer()
    try:
        logger.info(
            "\n============== make-event command executed from discord! ================ Data received:\n %s \nType: %s, Date: %s, TIME: %s",
            Interaction.user,
            game_type,
            game_date,
            game_time,
        )

        # Some formatting of date and time to acceptable SQL format
        logger.info("Adjusting time format for %s to HH:MM...", game_time)
        game_time = game_time + ":00"  # Required, add seconds as 00 to query
        game_time = time.fromisoformat(
            game_time
        )  # Convert above to time object to insert to query.
        game_date = format_date(
            game_date, "%d-%m-%Y"
        )  # Formart EU standard date format to SQL date format.
        logger.info("Now initiating vote!")

        # Below, the voting process starts!
        # Set up some settings:
        thumbs_up = "👍"
        thumbs_down = "👎"
        voting_period = 86400  # in seconds, 86400 seconds = 1 day
        count_limit_success = 1
        count_limit_fail = 1
        # Create a neat embed to send with the relevant information:
        embed = discord.Embed(
            title="New event vote created!", color=discord.Color.green()
        )
        embed.set_author(name=Interaction.user, icon_url=Interaction.user.avatar.url)
        embed.add_field(name="Event Type", value=game_type, inline=False)
        embed.add_field(name="Event Date", value=game_date, inline=False)
        embed.add_field(name="Event Time", value=game_time, inline=False)
        embed.set_footer(text="Vote using 👍 If you can attend, and 👎 if you cannot.")
        # Send event details to discord channel.
        logger.info("Vote ready! - Sending vote to Discord.")
        event_message = await Interaction.followup.send(embed=embed)

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

            # Below we listen for pass conditions, and react accordingly.
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
                    logger.warning(
                        "========== Event added succesfully, sending to discord! ========"
                    )
                    await Interaction.channel.send(
                        "The event has received enough votes, and was saved!"
                    )
                    break

                # Fail condition reaction(Too many down-votes)
                if thumbs_down_count >= count_limit_fail:
                    logger.warning(
                        "========== Vote failed, too many down-votes... =========="
                    )
                    await Interaction.channel.send(
                        "The event received too many down-votes, and will not be saved!"
                    )
                    break

        # Fail condition(Vote timeout)
        except asyncio.TimeoutError:
            logger.warning("======= The voting period has ended(Timeout) ========")
            await Interaction.channel.send("Voting period has ended")
    except psycopg2.Error as err:
        logger.error("======= An error has occured: =======\n %s", str(err))
        await Interaction.channel.send(f"An error has occured: {str(err)}")


@bot.tree.command(name="list-events", description="List planned event(s)")
@app_commands.describe(
    game_id="ID of event - Unique ID",
    game_type="Type of event - CPR or DND",
    game_date="Date of event - DD-MM-YYYY",
    game_time="Time of event - HH:MM",
)
async def list_events(
    Interaction: discord.Interaction,
    *,
    game_id: str = None,
    game_type: str = None,
    game_date: str = None,
    game_time: str = None,
):
    """Function to fetch events, and send them to discord."""
    try:
        logger.info(
            "\n============== list-events command received from discord! ============\n %s \n Filtering by: %s",
            Interaction.user,
            game_id,
            game_type,
            game_date,
            game_time,
        )
        logger.info("Establishing connection to database...")
        conn = create_connection()
        logger.info("Connection established, creating SQL cursor...")
        cur = conn.cursor()

        # Base query to itterate upon
        query = (
            "SELECT game_id, game_type, game_date, game_time FROM paps_table WHERE TRUE"
        )
        logger.info("Established base query:\n %s", query)

        # Below we check if any filters were provided with the command, and act accordingly.
        logger.info("Fetching data...")
        try:
            if game_id is not None:
                query += " AND game_id = '%s'" % (game_id)
                logger.info("Sending query:\n %s", query)
                cur.execute(query)
            elif game_type is not None:
                game_type = game_type.lower()
                query += " AND game_type = '%s'" % (game_type)
                logger.info("Sending query:\n %s", query)
                cur.execute(query)
            elif game_date is not None:
                game_date = format_date(game_date, "%d-%m-%Y")
                if game_date:
                    query += " AND game_date = '%s'" % (game_date)
                    logger.info("Sending query:\n %s", query)
                    cur.execute(query)
            elif game_time is not None:
                query += " AND game_time = '%s'" % (str(game_time))
                logger.info("Sending query:\n %s", query)
                cur.execute(query)
            else:
                logger.warning("No valid filter applied...")
                query = (
                    "SELECT game_id, game_type, game_date, game_time FROM paps_table"
                )
                logger.info("Sending query:\n%s", query)
                cur.execute(query)

            rows = cur.fetchall()
        except (psycopg2.Error, discord.DiscordException) as err:
            await Interaction.channel.send(
                f"An error occurred while executing the query: {str(err)}"
            )
            return
        logger.info("Query sent! Fetch succesfull!")
        logger.info("Closing connection to database...")
        cur.close()
        conn.close()

        logger.info("Now processing fetch data...")
        logger.info("Creating discord embed object...")
        if rows:
            embed = discord.Embed(title="Events Results:", color=discord.Color.blue())
            embed.add_field(
                name="ID - Type - Date - Location", value="\u200b", inline=False
            )  # Header field
            for game_id, game_type, game_date, game_time in rows:
                row_info = f"{game_id} - {game_type} - {game_date} - {game_time}"  # Assemble SQL data
                embed.add_field(
                    name="\u200b", value=row_info, inline=False
                )  # Send SQL data
            logger.info("Discord embed created, data assembled, sending to discord...")
            await Interaction.response.send_message(embed=embed)
            logger.info("======== Discord message sent via Embed! ==========")
            """ OLD(await confirmation of to use embed)
        if rows:
            event_list = "\n".join(
                f"{game_id} - {game_type} - {game_date} - {game_time}"
                for game_id, game_type, game_date, game_time in rows
            )
            logger.info(
                "Processing succesfull! Final fetch:\n %s \n Sending to discord...",
                event_list,
            )
            await Interaction.response.send_message("Results:", ephemeral=True)
            await Interaction.channel.send(f"Current Events:\nID - TYPE - DATE - TIME\n{event_list}")
            logger.info("====== Discord message sent! =========")
            """
        else:
            logger.warning("========No events found from query...========")
            embed = embed = discord.Embed(
                title="Events Results:", color=discord.Color.red()
            )
            embed.add_field(name="No events found", value="There were no events found.")
            await Interaction.channel.send(embed=embed)
    except psycopg2.Error as err:
        logger.error("======== An error has occured: =======\n %s", str(err))
        await Interaction.channel.send(f"An error occurred: {str(err)}")


@bot.tree.command(name="delete-event", description="Delete an event by event ID")
@app_commands.describe(game_id="ID of event to delete")
async def delete_event(Interaction: discord.Interaction, game_id: int):
    """A function to delete events from database by game_id"""
    try:
        logger.info(
            "\n============ delete-event command received from discord! ===========\n %s \n ID to delete: %s",
            Interaction.user,
            game_id,
        )
        logger.info("Establishing connection...")
        conn = create_connection()
        logger.info("Connection succesfull, creating SQL cursor...")
        cur = conn.cursor()

        query = "DELETE FROM paps_table WHERE game_id = %s" % (game_id)
        logger.info("Query created: \n %s", query)
        cur.execute(query, (game_id,))
        conn.commit()
        logger.info("Sending query...")
        if cur.rowcount > 0:
            logger.info("Event succesfully deleted!")
            embed = discord.Embed(title="Delete Event", color=discord.Color.red())
            embed.set_author(
                name=Interaction.user, icon_url=Interaction.user.avatar.url
            )
            embed.add_field(
                name="Following event id has been deleted", value=game_id, inline=False
            )
            await Interaction.response.send_message(embed=embed)
        else:
            logger.warning("No event found by ID: %s", game_id)
            embed = discord.Embed(title="Delete Event", color=discord.Color.red())
            embed.set_author(
                name=Interaction.user, icon_url=Interaction.user.avatar.url
            )
            embed.add_field(
                name="No event was found by that id", value=game_id, inline=False
            )
            await Interaction.channel.send(embed=embed)

        cur.close()
        conn.close()
    except psycopg2.Error as err:
        logger.error(f"========= An error has occured: =========\n{str(err)}")
        await Interaction.channel.send(f"An error has occured: {str(err)}")


@bot.tree.command(name="edit-event", description="Edit event by event ID")
@app_commands.describe(
    game_id="Required, unique ID of event to edit",
    game_type="Game type to change event to",
    game_date="Date to change the event to",
    game_time="Time to change the event to",
)
async def edit_event(
    Interaction: discord.Interaction,
    game_id: int,
    game_type: str = None,
    game_date: str = None,
    game_time: str = None,
):
    """A function to edit existing events by id"""
    try:
        logger.info(
            "\n============ edit-event command received from discord! ===========\n %s \n Game ID to edit: %s \n %s, %s, %s",
            Interaction.user,
            game_id,
            game_type,
            game_date,
            game_time,
        )
        logger.info("Establishing connection to SQL database...")
        conn = create_connection()
        logger.info("Connection established, creating cursor...")
        cur = conn.cursor()

        query = "UPDATE paps_table SET"
        logger.info("Base query created: %s", query)
        if game_type:
            query += " game_type = '%s'," % (game_type)
            logger.info("Changing game type to: %s", game_type)
        elif game_date:
            query += " game_date = '%s'," % (game_date)
            logger.info("Changing game date to: %s", game_date)
        elif game_time:
            query += " game_time = '%s'," % (game_time)
            logger.info("Changing game time to: %s", game_time)
        else:
            Interaction.channel.send("No changes made...")

        # Remove the trailing comma from the query
        query = query.rstrip(",")

        query += " WHERE game_id = %s" % (game_id)
        cur.execute(query)
        logger.info("Final query:\n %s", query)
        logger.info("Sending query...")
        conn.commit()

        if cur.rowcount > 0:
            logger.info("======== Event ID: %s has been updated... ========", game_id)
            embed = discord.Embed(title="Edit Event", color=discord.Color.yellow())
            embed.set_author(
                name=Interaction.user, icon_url=Interaction.user.avatar.url
            )
            edit_field = f"{game_id} - {game_type} - {game_date} - {game_time}"
            embed.add_field(
                name="The following event has been edited",
                value=edit_field,
                inline=False,
            )
            await Interaction.response.send_message(embed=embed)
        else:
            logger.warning("========= No event found by ID:%s =========", game_id)
            embed = discord.Embed(title="Edit event", color=discord.Color.red())
            embed.set_author(
                name=Interaction.user, icon_url=Interaction.user.avatar.url
            )
            edit_field = f"{game_id} - {game_type} - {game_date} - {game_time}"
            embed.add_field(
                name="No event was found by game ID", value=game_id, inline=False
            )
            await Interaction.channel.send(embed=embed)

        logger.info("======= Closing connection... ========")
        cur.close()
        conn.close()
    except psycopg2.Error as err:
        logger.error("======== An error has occured: ========\n %s", str(err))
        await Interaction.channel.send(f"An error has occured: {str(err)}")

"""============= PLAYER related commands ============"""

@bot.tree.command(name="register-self", description="Register youself to the player list of RPG players!")
async def register_player(Interaction=discord.Interaction):
    """A function to register the user of the command, to the player_table table"""
    #Get the discord member ID and name, assign to variables.
    discord_id = Interaction.user.id
    discord_name = Interaction.user.name

    try:
        logger.info(f"============= register-self has been executed! Following data received: ==============\n {discord_name}, {discord_id}")
        #Establish connection
        logger.info("Establishing connection...")
        conn = create_connection()
        logger.info("Connection established, creating cursor...")
        cur = conn.cursor()
        logger.info("Cursor created, now ready!")

        # First, check if player is already registered:
        logger.info(f"Checking if discord id: {discord_id} is already registered...")
        cur.execute("SELECT player_id FROM player_table WHERE discord_id = %s", (str(discord_id),))
        existing_player = cur.fetchone()

        if existing_player:
            logger.warning(f"Discord id: {discord_id} already registered, cancelling.")
            await Interaction.channel.send("You are already registered as a player.")

        #Otherwise, continue operation:
        else:
            # Insert discord member ID and name into player_table, 
            # by extracting data from discord.Interaction.user from invoker
            logger.info("Creating SQL, and inserting values...")
            cur.execute("INSERT INTO player_table (discord_id, discord_name) VALUES (%s, %s) RETURNING player_id",
                        (str(discord_id), discord_name))
            conn.commit()

            # Renumber the player IDs to ensure sequence in player_id
            logger.info("Re-ordering players to sequencial player_ids")
            cur.execute("SELECT player_id FROM player_table ORDER BY player_id;")
            player_ids = [row[0] for row in cur.fetchall()]
            for i, p_id in enumerate(player_ids, start=1):
                cur.execute("UPDATE player_table SET player_id = %s WHERE player_id = %s;", (i, p_id))
            logger.info("SQL sent, fetching player id...")
            conn.commit()
            logger.info(f"Changes committed! Following player has been created:\nPlayer_table ID:\nDiscord user:\n{discord_name}\nDiscord ID:\n{discord_id}")
            logger.info("Creating cool discord embed to send!")
            embed = discord.Embed(title="Player registered:", 
                                    description="You have been successfully registered as a player for Pen and Paper Shennanigans!",
                                    color=discord.Color.green())
            embed.add_field(name="Discord name", value=discord_name, inline=False)
            await Interaction.response.send_message(embed=embed)
            


    except psycopg2.Error as err:
        logger.error("Error occured registering player: %s", str(err))
        await Interaction.channel.send("An error has occured while registering the player.")
    
    finally:
        logger.info("Closing cursor...")
        cur.close()
        logger.info("======== Closing connection... goodbye. ========")
        conn.close()

@bot.tree.command(name="list-players", description="List all registered players")
async def list_players(Interaction=discord.Interaction):
    """A function for listing all registered players"""
    try:
        logger.info(f"========= list-players has been executed by {Interaction.user.name}! ========")
        logger.info("Establishing connection...")
        conn = create_connection()
        logger.info("Connection established, creating cursor...")
        cur = conn.cursor()
        logger.info("Cursor created, now ready!")

        logger.info("Fetching list of players from database...")
        cur.execute("SELECT player_id, discord_id, discord_name FROM player_table;")
        rows = cur.fetchall()

        if rows:
            logger.info("List fetched, now formatting to discord message.")
            header = "Player- ID - Discord ID - Discord Name"
            player_list = "\n".join(f"{row[0]} - {row[1]} - {row[2]}" for row in rows)
            message = f"{header}\n{player_list}"
            logger.info("Formatting complete, sending to discord...")
            await Interaction.response.send_message(message)
        else:
            logger.warning("No players found, cancelling...")
            await Interaction.channel.send("No players are currently registered.")
    
    except psycopg2.Error as err:
        logger.error("Error occured while executing SQL query: %s", str(err))
        await Interaction.channel.send("An error occured while listing the players")

    finally:
        logger.info("Closing cursor...")
        cur.close()
        logger.info("========= Closing connection... goodbye. ==========")
        conn.close()


@bot.tree.command(name="remove-player", description="Remove player by id from player list")
async def remove_player(Interaction=discord.Interaction, player_id:int=None):
    """A function to remove a player by id from database"""
    try:
        logger.info(f"========= delete-players has been executed by {Interaction.user.name}! ========")
        logger.info("Establishing connection...")
        conn = create_connection()
        logger.info("Connection established, creating cursor...")
        cur = conn.cursor()
        logger.info("Cursor created, now ready!")

        #Check if the player exist.
        logger.info("Checking if the player exist...")
        cur.execute("SELECT * FROM player_table WHERE player_id = %s;", (player_id,))
        #Assign data to player for use later
        player = cur.fetchone()
        logger.info(f"Player found:\n{player}")
        if not player:
        # Player does not exist
            logger.warning("No player found, responding...")
            embed = discord.Embed(title="Player removal", color=discord.Color.red())
            embed.set_author(
                            name=Interaction.user, icon_url=Interaction.user.avatar.url
                            )
            embed.add_field(name="Player ID", value="No player was found by that ID")
            logger.info("Embed created... sending...")
            await Interaction.channel.send(embed=embed)
        
        #Store the player data before deletion(for confirmation)
        logger.info("Storing player information for confirmation...")
        deleted_player_id = player[0]
        deleted_discord_name = player[2]

    
        #Delete the player
        logger.info(f"Removing {player} from database...")
        cur.execute("DELETE FROM player_table WHERE player_id = %s", (player_id,))
        conn.commit()

        #Confirm deletion with cool embed
        logger.info("Player removed, creating discord embed...")
        embed = discord.Embed(title="Player removal", color=discord.Color.red())
        embed.set_author(
                        name=Interaction.user, icon_url=Interaction.user.avatar.url
                        )
        embed.add_field(name="Player ID", value=deleted_player_id)
        embed.add_field(name="Discord Name", value=deleted_discord_name)
        logger.info("Embed created... sending...")
        await Interaction.response.send_message(embed=embed)

        #Renumber the player_table
        logger.info("Now renumering existing players in player_table")
            # First, fetch all the players, ordered by player_id
        logger.info("Fetching all players from player_table...")
        cur.execute("SELECT player_id FROM player_table ORDER BY player_id;")
            # Fetch the data, and toss them in a list by row.
        logger.info("Sorting all players, assigning to new id where needed...")
        player_ids = [row[0] for row in cur.fetchall()]
            # iterate over each player_id, numbering them, starting from 1.
        for i, p_id in enumerate(player_ids, start=1):
            # Update the player_table table, setting the player_id to the new index value 'i' 
            # where player_id matches existing player_id'p_id'
            logger.info("Updating player_table with new player_ids")
            cur.execute("UPDATE player_table SET player_id = %s WHERE player_id = %s;", (i,p_id))
        conn.commit()
        logger.info("Operation complete...")

    except psycopg2.Error as err:
        await Interaction.channel.send("An error occured while handling the player removal")
        logger.error("An error has occured while executing SQL query:\n%s", str(err))
    
    finally:
        logger.info("Closing cursor...")
        cur.close()
        logger.info("========= Closing connection... goodbye. ==========")
        conn.close()

"""Cross-table commands - attendance"""
@bot.tree.command(name="attend-event", description="Register your attendance for an event")
async def attend_event(Interaction=discord.Interaction, event_id:int=None):
    """A function to register attendance to an event"""
    try:
        # Log in to databasse
        logger.info(f"========= attend-event has been executed by {Interaction.user.name}! ========")
        logger.info("Establishing connection...")
        conn = create_connection()
        logger.info("Connection established, creating cursor...")
        cur = conn.cursor()
        logger.info("Cursor created, now ready!")

        # Check if the event exist in the event_table
        cur.execute("SELECT * FROM event_table WHERE event_id = %s;",(event_id,))
        event = cur.fetchone()

        if not event:
            await Interaction.followup.send_message("Event not found.")
        
        # Get the users player_id from the player_list table
        user_id = Interaction.user.id
        cur.execute("SELECT player_id FROM player_list WHERE discord_id = %s;", (user_id,))
        player = cur.fetchone()

        if not player:
            await Interaction.followup.send_message("Player not found. Please register first.")

        player_id = player[0]

        #Register the users player_id to the player_id row in event_table
        cur.execute("UPDATE event_table SET player_id = %s WHERE event_id = %s;", (player_id, event_id))
        conn.commit()
        await Interaction.response.send_message(f"Player ID {player_id} has registered attendance for event ID {event_id}")
    
    except psycopg2.Error as DBerr:
        logger.error(f"Database error detected:\n{DBerr}")
        await Interaction.followup.send("A database error occured...")
    except discord.DiscordException as DiscErr:
        logger.error(f"A discord error has occured:\n{DiscErr}")
        await Interaction.followup.send("A discord error has occured...")
    
    finally:
        logger.info("Closing cursor...")
        cur.close()
        logger.info("========= Closing connection... goodbye. ==========")
        conn.close()

"""============= Utility functions ==============="""
def start(token: str) -> None:
    """Function to wake the bot"""
    logger.info("Starting paps-bot ...")
    bot.run(token)
