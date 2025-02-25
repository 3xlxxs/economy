from discord.ext import commands
from database import BALANCE, SHOP
from utils import avatar
import discord

ADMINS = [1088979737524830281, 1168852793138888715]

class debugCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="edit", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    @discord.option("пользователь", discord.User)
    @discord.option("сумма", int)
    async def _edit(self, ctx, пользователь: discord.User, сумма: int):
        if ctx.author.id not in ADMINS:
            await ctx.response.defer()
            return
        
        embed = discord.Embed(color=0x2b2d31)
        embed.set_thumbnail(url=avatar(пользователь))
        embed.add_field(name="Старый баланс", value=f"```{await BALANCE.get(пользователь.id)}```")

        await BALANCE.update(пользователь.id, сумма)

        embed.add_field(name="Новый баланс", value=f"```{await BALANCE.get(пользователь.id)}```")

        await ctx.respond(embed=embed, ephemeral=True)

    @commands.slash_command(name="market", description="admin command")
    @discord.option('роль', discord.Role)
    @discord.option('цена', int)
    async def market(self, ctx, роль, цена):
        if ctx.author.id not in ADMINS:
            await ctx.response.defer()
            return
        
        exists = await SHOP.get(роль.id)
        if not exists:
            await SHOP.add(роль.id, ctx.author.id, цена)
            return

        await ctx.respond("Привет", ephemeral=True)

def setup(bot):
    bot.add_cog(debugCog(bot))