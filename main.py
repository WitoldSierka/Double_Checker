import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

last_images = []
history_range = 50
delete_message = True

TYPES_OF_INTEREST = ["image", "video"]

bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name}")


@bot.event
async def on_message(message):
    global last_images
    if message.author == bot.user:
        return
    temp = []
    async for mess in message.channel.history(limit=history_range, oldest_first=False):
        if mess.author == bot.user or message == mess:
            continue
        for old_att in mess.attachments:
            current_type = old_att.content_type.split('/')[0]
            #print(f"{current_type}: {att.filename}")
            if current_type in TYPES_OF_INTEREST:
                temp.append(old_att)

    last_images = temp

    for att in message.attachments:
        current_type = att.content_type.split('/')[0]
        if not current_type in TYPES_OF_INTEREST:
            continue
        if await is_repeated(att):
            if delete_message:
                await message.delete()
                await message.channel.send(f"{message.author.mention}, you sent a meme which was already posted in this channel.")
            else:
                await message.reply(f"{message.author.mention}, you sent a meme which was already posted in this channel.")
            break

    await bot.process_commands(message)

async def is_repeated(att):
    global last_images
    #compare with images in memory
    try:
        current_image = await att.read()
    except (discord.HTTPException, discord.Forbidden, discord.NotFound):
        print("Error reading current image")
        return False

    for image in last_images:
        #download the image to memory and compare bytes
        try:
            img_to_cmp = await image.read()
        except (discord.HTTPException, discord.Forbidden, discord.NotFound):
            print("Error reading last image")
            continue
        else:
            if img_to_cmp == current_image:
                return True

    return False

@bot.command()
async def del_msg_on(ctx):
    global delete_message
    delete_message = True
    await ctx.send("The bot will now remove messages with reposts.")

@bot.command()
async def del_msg_off(ctx):
    global delete_message
    delete_message = False
    await ctx.send("The bot will now only send a warning when a meme has been reposted.")

@bot.command()
async def manual(ctx):
    await ctx.send("This bot removes messages with reposted images or videos.\n"
                   "Warning-only mode can be toggled with the commands below:\n"
                   "!del_msg_on   - deletes message\n"
                   "!del_msg_off  - replies with a warning\n"
                   "!set_range    - set how many past messages the bot will check for reposts\n"
                   "!print_config - displays current settings")

@bot.command()
async def set_range(ctx, arg):
    global history_range
    try:
        new_range = int(arg)
    except ValueError:
        await ctx.send("Range must be a valid, positive integer.")
    else:
        if new_range > 0:
            history_range = new_range
        else:
            await ctx.send("Range must be a valid, positive integer.")

@bot.command()
async def print_config(ctx):
    global delete_message, history_range
    msg = "Current mode: " + "Message removal" if delete_message else "Send warning"
    await ctx.send(f"Current history range: {history_range}\n{msg}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)
