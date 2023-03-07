import os

import nest_asyncio
import requests
from discord.ext import commands

import Utils
from Cakes import Cakes
from InventoryImporter import InventoryImporter

nest_asyncio.apply()

if len(Utils.ALLOWED_CHANNEL_IDS) == 0:
    print("No allowed channel IDs found in config.ini")
    exit()


# verify if API_KEY is valid
def verify_api_key():
    r = requests.get('https://api.hypixel.net/player?key=' + Utils.API_KEY + '&uuid=' + Utils.SLADA_UUID)
    if r.status_code == 200:
        return True
    else:
        return False


if not verify_api_key():
    print("Invalid hypixel api_key")
    exit()
else:
    print("Hypixel api_key is valid")


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

print(VERSION_STRING)

# make dir "auction" if not exists
if not os.path.exists('auction'):
    os.makedirs('auction')

cakes_obj = Cakes()
bot = commands.Bot(command_prefix=Utils.COMMAND_PREFIX, help_command=None)


@bot.event
async def on_message(message):
    print(message.content)
    await bot.process_commands(message)


@bot.event
async def on_ready():  # This function will be run by the discord library when the bot has logged in
    print("Logged in as " + bot.user.name)


async def is_dm(ctx):
    # print(ctx.author.id)
    deny_author_ids = []  # copy author id from discord

    if ctx.author.id in deny_author_ids:
        return True  # do not allow commands from these users

    if ctx.message.channel.id not in Utils.ALLOWED_CHANNEL_IDS:
        print("not in allowed channel")
        return True  # not correct channel ID, ignore command

    if ctx.guild is None:
        await ctx.send("Don't be shy! Talk with me in bot-channel!")
        return True
    else:
        return False


@bot.command()
async def col(ctx, mc_name):
    if await is_dm(ctx):
        return
    msg = InventoryImporter().offer_cakes(mc_name)
    if len(msg) > 1995:
        await cakes_obj.split_and_send(ctx, msg.replace('```', ''))
    else:
        await ctx.send(msg)


@bot.command()
async def top(ctx):
    if await is_dm(ctx):
        return

    await ctx.send(cakes_obj.top(None))


@bot.command()
async def uc(ctx, mc_name=None):
    if await is_dm(ctx):
        return

    if mc_name is not None:
        await cakes_obj.analyze_undercuts(ctx, mc_name)
    else:
        await ctx.send(f"Invalid syntax, use {Utils.COMMAND_PREFIX}uc NAME")


@bot.command()
async def undercuts(ctx, mc_name=None):
    if await is_dm(ctx):
        return

    if mc_name is not None:
        await cakes_obj.analyze_undercuts(ctx, mc_name)
    else:
        await ctx.send(f"Invalid syntax, use {Utils.COMMAND_PREFIX}undercuts NAME")


@bot.command()
async def bins(ctx, mc_name=None):
    if await is_dm(ctx):
        return

    await cakes_obj.analyze_bin_prices(ctx, mc_name)


@bot.command()
async def soon(ctx):
    if await is_dm(ctx):
        return

    await cakes_obj.auctions_ending_soon(ctx)


@bot.command()
async def ah(ctx, name=None):
    if await is_dm(ctx):
        return

    if name is not None:
        await cakes_obj.auctions_ending_soon(ctx, name)
    else:
        await ctx.send(f"Invalid syntax, use {Utils.COMMAND_PREFIX}ah NAME")


@bot.command()
async def version(ctx, name=None):
    if await is_dm(ctx):
        return

    await ctx.send(VERSION_STRING)


@bot.command()
async def tb(ctx, name=None):
    if await is_dm(ctx):
        return

    if name is not None:
        await cakes_obj.auctions_ending_soon(ctx, None, name)
    else:
        await ctx.send(f"Invalid syntax, use !bids NAME")


@bot.command()
async def delcache(ctx, name=None):
    if await is_dm(ctx):
        return

    # if mcnames.db exists, delete it
    if os.path.exists("mcnames.db"):
        Utils.delete_database()
        if os.path.exists("mcnames.db"):
            await ctx.send("Failed to delete cache (mcnames.db)")
        else:
            await ctx.send(f"Deleted mcnames.db")
    else:
        await ctx.send("Cache (mcnames.db) does not exist!")


@bot.command()
async def help(ctx):
    if await is_dm(ctx):
        return
    print("printing help")

    help = f"""
Deprecation warning:
This cake bot is deprecated. That means, that I (Slada) am not playing the game anymore and I can't improve the bot. I will try to keep the bot online and do small bug fixes. I promise, that the bot will stay online at least till 2022-01-01.

Turquoise_Fish sadly isn't working on a replacement bot :(

Available commands:
```
{Utils.COMMAND_PREFIX}ah NAME
{Utils.COMMAND_PREFIX}tb NAME
{Utils.COMMAND_PREFIX}soon
{Utils.COMMAND_PREFIX}bins
{Utils.COMMAND_PREFIX}bins NAME_TO_EXCLUDE
{Utils.COMMAND_PREFIX}top
{Utils.COMMAND_PREFIX}col NAME
{Utils.COMMAND_PREFIX}help
{Utils.COMMAND_PREFIX}undercuts NAME
```

```{Utils.COMMAND_PREFIX}ah NAME```-it allows you to quickly optimize your auctions, because only cheapest bin sells.
-bins in cheapest bins column don't include your bins (same as {Utils.COMMAND_PREFIX}bins NAME_TO_EXCLUDE command)

```{Utils.COMMAND_PREFIX}tb NAME```- shows auctions where player NAME is top bidder

```{Utils.COMMAND_PREFIX}soon```-shows first 50 cakes ending soon

```{Utils.COMMAND_PREFIX}bins```-Analyses current bin prices
-Shows 5 cheapest bins
-Shows name of the cheapest bin auctioneer

```{Utils.COMMAND_PREFIX}bins NAME_TO_EXCLUDE```-Same as {Utils.COMMAND_PREFIX}bins without parameter, but it filters out you bins from specified player (you often don't need to see your bins)

```{Utils.COMMAND_PREFIX}top```-Shows current top bidder leaderboard
-Shows players who currently sells the most amount of cakes in AH

```{Utils.COMMAND_PREFIX}col NAME```-sky lea for cakes :)
-shows online status, profile name, coins in purse, ah bids, special auctions bought/sold, collected unique cakes in the inventory, missing cakes and amount of cakes needed to complete the bag.
-duplicate cakes in inventory are not shown.
-to refresh inventory api, tell the player you are inspecting to revisit you.
-shows pies too :)

```{Utils.COMMAND_PREFIX}help```-shows this message

```{Utils.COMMAND_PREFIX}undercuts NAME```-shows better BIN offers that your worst BIN offer

```{Utils.COMMAND_PREFIX}delcache```- deletes name cache
```{Utils.COMMAND_PREFIX}changelog```- see bot changes
"""
    await ctx.send(help)


@bot.command()
async def changelog(ctx, name=None):
    if await is_dm(ctx):
        return

    await ctx.send(git_get_commit_messages())


# Run the discord bot
bot.run(Utils.DISCORD_API_KEY)
