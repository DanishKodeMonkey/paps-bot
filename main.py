"""
Main entrypoint for the bot
"""
import os
import sys
from paps_bot import paps_bot


def read_token_from_env_var() -> str:
    """
    Read the discord token from an env var, and quit if the token is not present.
    """
    token = os.environ.get("DISCORD_TOKEN", None)
    if not token:
        print("ERROR: Could not find env var DISCORD_TOKEN, exitting.")
        sys.exit(1)
    return token


DISCORD_TOKEN = read_token_from_env_var()


# run the bot
if __name__ == "__main__":
    paps_bot.start(token=DISCORD_TOKEN)
