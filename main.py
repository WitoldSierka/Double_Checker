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

#images gallery
last_images = []

TYPES_OF_INTEREST = ["image", "video"]
#audio?

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
    async for mess in message.channel.history(limit=30, oldest_first=False):
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
            #print("This image has already been posted before")
            await message.channel.send(f"{message.author.mention}, you sent {att.filename} of type {att.content_type}"
                                       ", which was already posted in this channel.")
            break

    #this line apparently stops the bot from tripping over itself
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



bot.run(token, log_handler=handler, log_level=logging.DEBUG)
