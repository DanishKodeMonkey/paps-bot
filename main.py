"""
Main entrypoint
"""
import os
import paps_bot.paps_bot as paps_bot

def read_token_from_env_var() -> str:
    # make sure the discord token is available or exit
    token = os.environ.get("DISCORD_TOKEN", None)
    if not token:
        print("ERROR: Could not find env var DISCORD_TOKEN, exitting.")
        sys.exit(1)
    return token

# run the bot
if __name__ == "__main__":
    paps_bot.start(read_token_from_env_var())



