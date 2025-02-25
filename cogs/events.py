from database import DATABASE, INVITES, BALANCE
from discord.ext import commands, tasks
from threading import Thread
from keep_alive import run
from utils import avatar
from os import system
import discord
import time
import json

invites = {}
guilds = [1207101198369296434, 1325681966955237486, 1284340210011865180]

class eventsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if guild.id not in guilds:
            await guild.leave()

    @tasks.loop(seconds=60)
    async def _backup(self):
            embed = discord.Embed()
            embed.color = 0x2b2d31
            embed.description = f"### luna.db — резервная копия\n- Сохранено <t:{int(time.time())}:R>"
            await self.bot.get_channel(1342418457597313094).send(embed=embed, file=discord.File("luna.db"))


    @commands.Cog.listener()
    async def on_ready(self):
        print("COGS     : CONNECTED")
        await DATABASE.connect()
        print("DATABASE : CONNECTED")
        for guild in self.bot.guilds:
            invites[guild.id] = await guild.invites()
        print("INVITES  : CONNECTED")
        self._backup.start()
        print("BACKUP   : CONNECTED")
        await self.bot.wait_until_ready()
        print("BOT      : CONNECTED")

        Thread(target=run).start()

def setup(bot):
    bot.add_cog(eventsCog(bot))