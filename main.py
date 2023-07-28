import os

import discord
import nest_asyncio
import requests
from discord import app_commands
# from discord.ext import commands

import Utils
from Cakes import Cakes
from InventoryImporter import InventoryImporter
from utils import Config
from utils import LogController

log_controller = LogController.LogController()
logger = log_controller.get_logger()

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


if not verify_api_key():
    logger.error("Invalid Hypixel API key!")
    exit()
else:
    logger.info("Hypixel API key is valid")


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


async def disallow_execute(interaction):
    deny_author_ids = []  # copy author id from discord

    if interaction.user.id in deny_author_ids:
        await interaction.response.send_message("You are not allowed to use this bot.", ephemeral=True)
        return True  # do not allow commands from these users

    if interaction.channel_id not in Config.ALLOWED_CHANNEL_IDS:
        await interaction.response.send_message("This channel is not allowed for this bot.", ephemeral=True)
        return True  # not correct channel ID, ignore command

    if interaction.guild is None:
        await interaction.send("Don't be shy! Talk with me in bot-channel!")
        return True
    else:
        return False


@tree.command(name="col")
async def col(interaction, mc_name: str):
    """
    Displays information over specific player
    """
    if await disallow_execute(interaction):
        return True

    await InventoryImporter().offer_cakes(mc_name, interaction)


@tree.command()
async def top(interaction):
    """
    Shows current top bidder leaderboard
    and players who currently sell the most amount of cakes in AH
    """
    if await disallow_execute(interaction):
        return
    await interaction.response.send_message("Loading...")

    await interaction.edit_original_response(content=cakes_obj.top())


@tree.command()
async def undercuts(interaction, mc_name: str):
    """
    See auctions where given player was undercut
    """
    if await disallow_execute(interaction):
        return

    if mc_name is not None:
        await interaction.response.send_message("Loading...")

        response_msg = await cakes_obj.analyze_undercuts(interaction, mc_name)

        await interaction.edit_original_response(content=response_msg)


@tree.command(name="bins")
async def bins(interaction, name_to_exclude: str = None):
    """
    Analysed current bin prices and show 5 cheapest bins
    """
    if await disallow_execute(interaction):
        return
    await interaction.response.send_message("Loading...")

    bins_data = await cakes_obj.analyze_bin_prices(interaction, name_to_exclude)
    bins_msg = Utils.split_message(bins_data)
    for msg in bins_msg:
        await interaction.channel.send(f"```diff\n{msg}```")
    await interaction.edit_original_response(content="BIN Overview:")


@tree.command()
async def soon(interaction):
    """
    Show all cake auctions that are ending soon
    """
    if await disallow_execute(interaction):
        return

    await interaction.response.send_message("Loading...")

    soon_data = await cakes_obj.auctions_ending_soon(interaction)
    soon_msg = Utils.split_message(msg=soon_data)
    await interaction.edit_original_response(content=soon_msg[0])
    soon_msg.pop(0)
    for msg in soon_msg:
        await interaction.channel.send(f"```diff\n{msg}```")


@tree.command()
async def ah(interaction, mc_name: str):
    """
    Show Cake Auctions for given player name
    """
    if await disallow_execute(interaction):
        return

    if mc_name is not None:
        await interaction.response.send_message("Loading...")
        ah_data = await cakes_obj.auctions_ending_soon(interaction, mc_name)
        ah_msgs = Utils.split_message(ah_data)
        for msg in ah_msgs:
            await interaction.channel.send(f"```diff\n{msg}```")
        await interaction.edit_original_response(content=f"AH data for {mc_name}:")

    else:
        await interaction.response.send_message(f"Invalid syntax, use /ah NAME")


@tree.command()
async def tb(interaction, mc_name: str):
    """
    Show auctions where given player is top bidder
    """
    if await disallow_execute(interaction):
        return

    await interaction.response.send_message("Loading...")

    if mc_name is not None:
        tb_data = await cakes_obj.auctions_ending_soon(interaction, None, mc_name)
        await interaction.edit_original_response(content=f"```diff\n{tb_data}```")
    else:
        await interaction.response.send_message(f"Invalid syntax, use /tb NAME")


@tree.command()
async def delcache(interaction):
    """
    Used to refresh cached mc names
    """
    if await disallow_execute(interaction):
        return

    # if mcnames.db exists, delete it
    if os.path.exists("mcnames.db"):
        Utils.delete_database()
        if os.path.exists("mcnames.db"):
            await interaction.response.send_message("Failed to delete cache (mcnames.db)")
        else:
            await interaction.response.send_message(f"Deleted mcnames.db")
    else:
        await interaction.response.send_message("Cache (mcnames.db) does not exist!")


@tree.command()
async def version(interaction):
    version_embed = discord.Embed(description=VERSION_STRING, title="Bot Version")

    await interaction.response.send_message(embed=version_embed)


@tree.command()
async def info(interaction):
    """
    See what this bot is able to do and how
    """
    if await disallow_execute(interaction):
        return

    deprecation_message = f"""
This cake bot is deprecated. That means, that I (Slada) am not playing the game anymore and I can't improve the bot. I will try to keep the bot online and do small bug fixes. I promise, that the bot will stay online at least till 2022-01-01.

Turquoise_Fish sadly isn't working on a replacement bot :(

The bot is currently maintained and worked on by <@188690150975471616>, for any questions/improvements message/ping me!
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
    if await disallow_execute(interaction):
        return

    await interaction.response.send_message(git_get_commit_messages())


# Run the discord bot
client.run(Config.DISCORD_API_KEY, log_handler=None)
