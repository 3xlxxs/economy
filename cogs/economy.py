from database import BALANCE, TIMELY
from discord.ui import Button, View
from discord.ext import commands
from utils import avatar
import discord
import time

class economyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="balance", description="Посмотреть баланс", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    @discord.option("пользователь", discord.User, required=False)
    async def balance(self, ctx, пользователь: discord.User = None):
        пользователь = пользователь or ctx.author
        embed = discord.Embed(title=f"Баланс — {пользователь.name}", color=0x2b2d31, thumbnail=avatar(пользователь))
        embed.add_field(name="> Монеты", value=f"```{await BALANCE.get(пользователь.id)}```")
        await ctx.respond(embed=embed)

    @commands.slash_command(name="timely", description="Ежедневная награда", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    async def timely(self, ctx):
        embed = discord.Embed(title="Временная награда", color=0x2b2d31, thumbnail=avatar(ctx.author))

        _user = ctx.author.id

        _time = int(time.time())
        _last = await TIMELY.get(_user)

        if _time - _last >= 43200:
            await TIMELY.update(_user, _time)

            await BALANCE.update(_user, 100)

            embed.description = f"{ctx.author.mention}, вы **забрали** свои **100 $**\nВозвращайтесь <t:{_time + 43200}:R>"
            await ctx.respond(embed=embed)
        else:
            embed.description = f"{ctx.author.mention}, вы **уже** забрали **временную** награду! Вы сможете **получить** следущую <t:{_last + 43200}:R>"
            await ctx.respond(embed=embed)

    @commands.slash_command(name="give", description="Передать монеты", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    @discord.option("пользователь", discord.User)
    @discord.option("сумма", int, min_value=1)
    async def give(self, ctx, пользователь: discord.User, сумма: int):
        embed = discord.Embed(title="Передача монет", thumbnail=avatar(ctx.author), color=0x2b2d31)

        if ctx.author.id == пользователь.id:
            embed.description = f"{ctx.author.mention}, действие с **самим собой** выполнить **невозможно**"
            await ctx.respond(embed=embed)
            return

        if await BALANCE.get(ctx.author.id) < сумма:
            embed.title = "Недостаточно средств!"
            embed.description = f"{ctx.author.mention}, У вас **недостаточно средств**\nНе хватает: **{сумма - await BALANCE.get(ctx.author.id)} $**"
            await ctx.respond(embed=embed)
            return

        confirm_button = Button(label="Подтвердить", style=discord.ButtonStyle.gray)
        cancel_button = Button(label="Отмена", style=discord.ButtonStyle.red)

        embed.description = f"{ctx.author.mention}, вы **уверены**, что хотите передать **{сумма} $** пользователю <@{пользователь.id}>"

        async def confirm_callback(interaction):
            if interaction.user.id != ctx.author.id:
                return
            if await BALANCE.get(ctx.author.id) < сумма:
                embed.title = "Недостаточно средств!"
                embed.description = f"{ctx.author.mention}, У вас **недостаточно средств**\nНе хватает: **{сумма - await BALANCE.get(ctx.author.id)} $**"
                await ctx.edit(embed=embed, view=None)
                return

            await BALANCE.update(ctx.author.id, -сумма)
            await BALANCE.update(пользователь.id, сумма)
            embed.description = f"{ctx.author.mention}, вы передали **{сумма} $** пользователю <@{пользователь.id}>"
            await ctx.edit(embed=embed, view=None)
            await interaction.response.defer()

        async def cancel_callback(interaction):
            if interaction.user.id != ctx.author.id:
                return
            embed.description = f"{ctx.author.mention}, вы **отказались** передавать **{сумма} $** пользователю <@{пользователь.id}>"
            await ctx.edit(embed=embed, view=None)
            await interaction.response.defer()

        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback

        view = View()
        view.add_item(confirm_button)
        view.add_item(cancel_button)

        await ctx.respond(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            await BALANCE.update(message.author.id, 1)
            await self.bot.process_commands(message)

def setup(bot):
    bot.add_cog(economyCog(bot))