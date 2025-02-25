from discord.ext import commands
from dotenv import load_dotenv
import discord
import os

load_dotenv()
bot = commands.Bot(command_prefix=",", intents=discord.Intents.all())

@bot.slash_command(name="add", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
async def add(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Добавить бота", url="https://discord.com/oauth2/authorize?client_id=1208714902873837638"))
    await ctx.respond(view=view)

for cog in os.listdir("./cogs"):
    if cog.endswith(".py"):
        try:
            c = cog[:-3]
            bot.load_extension(f"cogs.{c}")
            print(f"COG      : SUCCESS @ COG {c}")
        except Exception as e:
            print(f"COG      : FAILURE @ COG {c} : {e}")

try:
    bot.run(os.getenv("TOKEN"))
except Exception as e:
    input(e)
