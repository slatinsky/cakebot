import asyncio
import os
from Responder import Responder

import discord
import nest_asyncio
import requests
from discord import app_commands
# from discord.ext import commands

import Utils
from Cakes import Cakes
from InventoryImporter import InventoryImporter
from utils import Config
# from utils import LogController

# log_controller = LogController.LogController()
# logger = log_controller.get_logger()


class Logger():
    def __init__(self):
        pass

    def info(self, message):
        print(message, flush=True)

    def debug(self, message):
        print(message, flush=True)

    def warn(self, message):
        print(message, flush=True)
    
    def error(self, message):
        print(message, flush=True)

logger = Logger()



nest_asyncio.apply()

logger.info("Starting up cakebot...")

if len(Config.ALLOWED_CHANNEL_IDS) == 0:
    logger.error("No allowed channel IDs found in config")
    exit()


# verify if API_KEY is valid
def verify_api_key():
    r = requests.get('https://api.hypixel.net/player?key=' + Config.API_KEY + '&uuid=' + Config.SLADA_UUID)
    if r.status_code == 200:
        return True
    else:
        return False





def get_commit_hash():
    return os.popen('git rev-parse --short HEAD').read().strip()


def get_commit_time():
    return os.popen('git show -s --format="%ci"').read().strip()


def get_commit_index():
    count = 100 + int(os.popen('git rev-list --count HEAD').read().strip())
    if git_unsaved_changes():
        return count + 1
    return count


def git_unsaved_changes():
    return len(os.popen('git diff-files').read().strip()) > 0


def git_are_changes_ready_to_commit():
    return os.system('git diff-index --quiet HEAD --') == 0


def git_get_commit_messages():
    changes = os.popen('git log --pretty=format:"%s"').read().strip().split('\n')
    for i in range(len(changes)):
        changes[i] = f"v{len(changes) - i + 100}: {changes[i]}"

    changes = '\n'.join(changes)
    return changes


if git_unsaved_changes():
    BETA = " BETA"
else:
    BETA = ""
VERSION_STRING = f"Bot version{BETA} {get_commit_index()} ({get_commit_hash()}, {get_commit_time()})"

logger.info(f"Running {VERSION_STRING}")

# make dir "auction" if not exists
if not os.path.exists('auction'):
    os.makedirs('auction')

cakes_obj = Cakes()
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
# bot = commands.Bot(intents=intents)
tree = app_commands.CommandTree(client)


@client.event
async def on_ready():  # This function will be run by the discord library when the bot has logged in
    await tree.sync()
    logger.info(f"Bot logged in as {client.user.name}")


@tree.command(name="col")
async def col(interaction, mc_name: str):
    """
    Displays information over specific player
    """
    with Responder(interaction) as responder:
        await responder.disallow_execute_check()
        await InventoryImporter().offer_cakes(mc_name, interaction)


@tree.command()
async def top(interaction):
    """
    Shows current top bidder leaderboard
    and players who currently sell the most amount of cakes in AH
    """
    with Responder(interaction) as responder:
        await responder.disallow_execute_check()
        await responder.append_header("Loading...")
        ttop = await cakes_obj.top(responder)
        await responder.replace_header("Top auctioneers:")
        await responder.append(ttop)


@tree.command()
async def undercuts(interaction, mc_name: str):
    """
    See auctions where given player was undercut
    """
    with Responder(interaction) as responder:
        await responder.disallow_execute_check()
        if mc_name is not None:
            await responder.append_header("Loading...")
            response_msg = await cakes_obj.analyze_undercuts(responder, mc_name)
            await responder.replace_header(f"Undercuts for {mc_name}:")
            await responder.append(f"```diff\n{response_msg}\n```")


@tree.command(name="bins")
async def bins(interaction, name_to_exclude: str = None):
    """
    Analysed current bin prices and show 5 cheapest bins
    """
    with Responder(interaction) as responder:
        await responder.disallow_execute_check()
        await responder.append_header("Loading...")
        bins_data = await cakes_obj.analyze_bin_prices(responder, name_to_exclude)
        await responder.replace_header("BIN Overview:")
        await responder.append(f"```diff\n{bins_data}\n```")


@tree.command()
async def soon(interaction):
    """
    Show all cake auctions that are ending soon
    """
    with Responder(interaction) as responder:
        await responder.disallow_execute_check()
        await responder.append_header("Loading...")
        soon_data = await cakes_obj.auctions_ending_soon(responder)
        await responder.replace_header("Auctions ending soon:")
        await responder.append(f"```diff\n{soon_data}```")


@tree.command()
async def ah(interaction, mc_name: str):
    """
    Show Cake Auctions for given player name
    """
    
    with Responder(interaction) as responder:
        await responder.disallow_execute_check()
        if mc_name is not None:
            await responder.append_header("Loading...")
            ah_data = await cakes_obj.auctions_ending_soon(responder, mc_name)
            await responder.replace_header(f"AH data for {mc_name}:")
            await responder.append(f"```diff\n{ah_data}```")

        else:
            await responder.send("Invalid syntax, use /ah NAME")


@tree.command()
async def tb(interaction, mc_name: str):
    """
    Show auctions where given player is top bidder
    """
        
    with Responder(interaction) as responder:
        await responder.disallow_execute_check()
        await responder.append_header("Loading...")

        if mc_name is not None:
            tb_data = await cakes_obj.auctions_ending_soon(responder, None, mc_name)
            await responder.replace_header(f"Top bidder overview for {mc_name}:")
            await responder.append(f"```diff\n{tb_data}```")
        else:
            await responder.replace_header("Invalid syntax, use /tb NAME")


@tree.command()
async def delcache(interaction):
    """
    Used to refresh cached mc names
    """
    with Responder(interaction) as responder:
        await responder.disallow_execute_check()
        Utils.delete_database()
        await responder.append("Deleted mcnames database - minecraft names will be fresh again")


@tree.command()
async def version(interaction):
    """
    Get the current version of this bot
    """
    with Responder(interaction) as responder:
        await responder.disallow_execute_check()
        version_embed = discord.Embed(description=VERSION_STRING, title="Bot Version")
        await interaction.response.send_message(embed=version_embed)


@tree.command()
async def info(interaction):
    """
    See what this bot is able to do and how
    """
    with Responder(interaction) as responder:
        await responder.disallow_execute_check()
        deprecation_message = f"""
The bot is currently maintained and worked on by <@188690150975471616> and <@434468647994523650>, for any questions/improvements message/ping us!
    """
        deprecation_embed = discord.Embed(description=deprecation_message, title="Status of this bot")

        commands_message = f"""Available commands:
```
/ah NAME
/tb NAME
/soon
/bins
/bins NAME_TO_EXCLUDE
/top
/col NAME
/info
/undercuts NAME
```
"""
        commands_embed = discord.Embed(description=commands_message, title="Commands")
        await interaction.response.send_message(embeds=[deprecation_embed, commands_embed])


@tree.command()
async def changelog(interaction):
    """
    See what has changed in this bot latest
    """
    with Responder(interaction) as responder:
        await responder.disallow_execute_check()
        await responder.append("last 10 commits:\n" + git_get_commit_messages())




async def async_test():
    r = Responder(None)
    await r.append("test")
    await r.append("test2")
    await r.append("test3")
    await r.append("""```bash
ls -la

lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum
lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum
lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum
lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum
lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum
lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum
lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum
lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua ut enim ad minim veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur excepteur sint occaecat cupidatat non proident sunt in culpa qui officia deserunt mollit anim id est laborum
```""")
    await r.split()


if __name__ == "__main__":
    # asyncio.run(async_test())

    if not verify_api_key():
        logger.error("Invalid Hypixel API key!")
        exit()
    else:
        logger.info("Hypixel API key is valid")

    # Run the discord bot
    client.run(Config.DISCORD_API_KEY)