# cogs/games.py
from discord.ui import Button, View, Select
from discord.ext import commands
from database import BALANCE
from utils import avatar
import asyncio
import discord
import random

TIMEOUT = 180

class gamesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Камень/Ножницы/Бумага", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    @discord.option("ставка", discord.SlashCommandOptionType.integer, min_value=10)
    @discord.option("пользователь", discord.SlashCommandOptionType.user, required=False)
    async def rps(self, ctx, ставка, пользователь):
        embed = discord.Embed(title="Камень, Ножницы, Бумага", color=0x2b2d31)

        userBalance = await BALANCE.get(ctx.author.id)
        if userBalance < ставка:
            embed.title = "Недостаточно средств!"
            embed.description = f"{ctx.author.mention}, у вас **недостаточно средств**\nНе хватает: **{ставка - userBalance} $**"
            await ctx.respond(embed=embed)
            return
    
        opponent = пользователь or None
        if opponent:
            opponentBalance = await BALANCE.get(opponent.id)
            if opponent.id == ctx.author.id:
                embed.description = f"{ctx.author.mention}, действие с **самим собой** выполнить **невозможно**"
                await ctx.respond(embed=embed)
                return
    
            if opponentBalance < ставка:
                embed.title = "Недостаточно средств!"
                embed.description = f"{ctx.author.mention}, у <@{opponent.id}> **недостаточно средств**\nНе хватает: **{ставка - opponentBalance} $**"
                embed.set_thumbnail(avatar(opponent))
                await ctx.respond(embed=embed, ephemeral=True)
                return

        async def _timeout(_view, userIds=[discord.Member.id]):
            for id in userIds:
                await BALANCE.update(id, ставка)

            _view.disable_all_items()
            await ctx.edit(view=_view)

        async def handler(interaction, userMove, opponentMove):
            embed.title = "Камень, Ножницы, Бумага"
    
            if userMove == opponentMove:
                embed.thumbnail = avatar(ctx.author)
                embed.description = f"Между {ctx.author.mention} и <@{interaction.user.id}> **ничья**"
                await BALANCE.update(ctx.author.id, ставка)
                
                await BALANCE.update(interaction.user.id, ставка)
            elif (userMove == "r" and opponentMove == "s") or (userMove == "s" and opponentMove == "p") or (userMove == "p" and opponentMove == "r"):
                embed.thumbnail = avatar(ctx.author)
                embed.description = f"{ctx.author.mention} победил <@{interaction.user.id}> и выиграл **{ставка} $**"
                
                await BALANCE.update(ctx.author.id, ставка * 2)
            else:
                embed.thumbnail = avatar(interaction.user)
                embed.description = f"<@{interaction.user.id}> победил {ctx.author.mention} и выиграл **{ставка} $**"

                await BALANCE.update(interaction.user.id, ставка * 2)
    
            await ctx.edit(embed=embed, view=None)
    
        async def userChoiceCallback(interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.defer()
                return
            
            userBalance = await BALANCE.get(ctx.author.id)
            if userBalance < ставка:
                embed.title = "Недостаточно средств!"
                embed.description = f"{ctx.author.mention}, у вас **недостаточно средств**\nНе хватает: **{ставка - userBalance} $**"
                await ctx.edit(embed=embed)
                return

            await BALANCE.update(ctx.author.id, -ставка)

            nonlocal _view
            _view.stop()
    
            userMove = userChoice.values[0]
    
            if opponent:
                embed.thumbnail = avatar(interaction.user)
    
                async def acceptCallback(interaction):
                    if interaction.user.id != opponent.id:
                        await interaction.response.defer()
                        return
                    
                    opponentBalance = await BALANCE.get(opponent.id)
                    if opponentBalance < ставка:
                        embed.title = "Недостаточно средств!"
                        embed.description = f"{interaction.user.mention}, у <@{opponent.id}> **недостаточно средств**\nНе хватает: **{ставка - opponentBalance} $**"
                        await ctx.edit(embed=embed)
                        return
                    
                    nonlocal _view
                    _view.stop()
    
                    opponentChoice = Select(
                        placeholder="Выберите ход",
                        options=[
                            discord.SelectOption(label="Камень", value="r"),
                            discord.SelectOption(label="Ножницы", value="s"),
                            discord.SelectOption(label="Бумага", value="p")
                        ]
                    )
    
                    async def opponentChoiceCallback(interaction2):
                        if interaction2.user.id != interaction.user.id:
                            await interaction2.response.defer()
                            return
                        
                        nonlocal _view
                        _view.stop()
    
                        await handler(interaction2, userMove, opponentChoice.values[0])
                        await interaction2.response.defer()
    
                    opponentChoice.callback = opponentChoiceCallback
                    _view = View(timeout=TIMEOUT)
                    _view.add_item(opponentChoice)
                    _view.on_timeout = lambda: _timeout(_view, [ctx.author.id, opponent.id])
    
                    await BALANCE.update(interaction.user.id, -ставка)
    
                    embed.description = f"{interaction.user.mention}, **выберите** камень, ножницы или бумага"
                    await ctx.edit(embed=embed, view=_view)
                    await interaction.response.defer()
    
                async def rejectCallback(interaction):
                    if interaction.user.id != opponent.id:
                        await interaction.response.defer()
                        return
                    
                    nonlocal _view
                    _view.stop()

                    await BALANCE.update(ctx.author.id, ставка)

                    embed.description = f"{ctx.author.mention}, {interaction.user.mention} **отклонил** ваше **предложение**"
                    await ctx.edit(embed=embed, view=None)
                    await interaction.response.defer()
    
                accept = Button(label="Принять")
                reject = Button(label="Отклонить")
                accept.callback = acceptCallback
                reject.callback = rejectCallback
    
                _view = View(timeout=TIMEOUT)
                _view.add_item(accept)
                _view.add_item(reject)
                _view.on_timeout = lambda: _timeout(_view, [ctx.author.id])
    
                embed.thumbnail = avatar(ctx.author)
                embed.description = f"{ctx.author.mention} хочет **сразиться** с вами на **{ставка} $**"
                await ctx.edit(content=f"{opponent.mention}", embed=embed, view=_view)
                await interaction.response.defer()
            else:
                async def joinCallback(interaction):
                    if interaction.user.id == ctx.author.id:
                        await interaction.response.defer()
                        return
                    
                    nonlocal _view
                    _view.stop()
    
                    opponentBalance = await BALANCE.get(interaction.user.id)
                    if opponentBalance < ставка:
                        embed.title = "Недостаточно средств!"
                        embed.description = f"<@{interaction.user.id}>, у вас **недостаточно средств**\nНе хватает: **{ставка - opponentBalance} $**"
                        embed.set_thumbnail(avatar(interaction.user))
                        await interaction.respond(embed=embed, ephemeral=True)
                        return
    
                    opponentChoice = Select(
                        placeholder="Выберите ход",
                        options=[
                            discord.SelectOption(label="Камень", value="r"),
                            discord.SelectOption(label="Ножницы", value="s"),
                            discord.SelectOption(label="Бумага", value="p")
                        ]
                    )
    
                    async def opponentChoiceCallback(interaction2):
                        if interaction2.user.id != interaction.user.id:
                            await interaction2.response.defer()
                            return
                        
                        nonlocal _view
                        _view.stop()
    
                        await handler(interaction2, userMove, opponentChoice.values[0])
                        await interaction2.response.defer()
    
                    opponentChoice.callback = opponentChoiceCallback
                    _view = View(timeout=TIMEOUT)
                    _view.add_item(opponentChoice)
                    _view.on_timeout = lambda: _timeout(_view, [ctx.author.id, interaction.user.id])
    
                    await BALANCE.update(interaction.user.id, -ставка)
    
                    embed.thumbnail = avatar(interaction.user)
                    embed.description = f"{interaction.user.mention}, **выберите** камень, ножницы или бумага"
                    await ctx.edit(embed=embed, view=_view)
                    await interaction.response.defer()
    
                join = Button(label="Присоединиться", style=discord.ButtonStyle.gray)
                join.callback = joinCallback
    
                _view = View(timeout=TIMEOUT)
                _view.add_item(join)
                _view.on_timeout = lambda: _timeout(_view, [ctx.author.id])
    
                embed.description = f"{ctx.author.mention} создал игру в камень, ножницы, бумага на **{ставка} $**"
                await ctx.edit(embed=embed, view=_view)
                await interaction.response.defer()
    
        userChoice = Select(
            placeholder="Выберите ход",
            options=[
                discord.SelectOption(label="Камень", value="r"),
                discord.SelectOption(label="Ножницы", value="s"),
                discord.SelectOption(label="Бумага", value="p")
            ]
        )
    
        userChoice.callback = userChoiceCallback

        _view = View(timeout=TIMEOUT)
        _view.add_item(userChoice)
        _view.on_timeout = lambda: _timeout(_view, [])
    
        embed.thumbnail = avatar(ctx.author)
        embed.description = f"{ctx.author.mention}, **выберите** камень, ножницы или бумага"

        await ctx.respond(embed=embed, view=_view)

    @commands.slash_command(name="duel", description="Дуэль", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    @discord.option("ставка", discord.SlashCommandOptionType.integer, min_value=10)
    @discord.option("пользователь", discord.SlashCommandOptionType.user, required=False)
    async def duel(self, ctx, ставка, пользователь):
        embed = discord.Embed(title="Дуэли", color=0x2b2d31)
        embed.set_thumbnail(url=avatar(ctx.author))

        async def _timeout(__view__, userIds=[discord.Member.id]):
            for id in userIds:
                await BALANCE.update(id, ставка)

            __view__.disable_all_items()
            await ctx.edit(view=__view__)

        async def handler(interaction):
            embed.title = "Дуэли"
            embed.description = f"{ctx.author.mention} сражается с {interaction.user.mention}"
            embed.set_image(url="https://cdn.discordapp.com/attachments/1308357961684615199/1335610676072284341/SPOILER_3xlxxs.gif?ex=67b53b1f&is=67b3e99f&hm=9659c565c00e3a0d93e8dafd1c5eba7001c2a332aa79a38776ebdaa84579e672&")
            embed.set_thumbnail(url=None)

            await ctx.edit(embed=embed, view=None)
            await asyncio.sleep(3)
    
            winner = random.choice([ctx.author, interaction.user])
            await BALANCE.update(winner.id, ставка * 2)
    
            embed.title = "Дуэли"
            embed.description = f"{winner.mention} победил {interaction.user.mention if winner == ctx.author else ctx.author.mention} и выиграл **{ставка} $**"
            embed.set_thumbnail(url=avatar(winner))
            embed.set_image(url=None)
    
            await ctx.edit(embed=embed, view=None)

        userBalance = await BALANCE.get(ctx.author.id)
        if userBalance < ставка:
            embed.title = "Недостаточно средств!"
            embed.description = f"{ctx.author.mention}, у вас **недостаточно средств**\nНе хватает: **{ставка - userBalance} $**"
            await ctx.respond(embed=embed)
            return

        opponent = пользователь or None
        if opponent:
            opponentBalance = await BALANCE.get(opponent.id)
            if opponent.id == ctx.author.id:
                embed.description = f"{ctx.author.mention}, действие с **самим собой** выполнить **невозможно**"
                await ctx.respond(embed=embed)
                return
    
            if opponentBalance < ставка:
                embed.title = "Недостаточно средств!"
                embed.description = f"{ctx.author.mention}, у <@{opponent.id}> **недостаточно средств**\nНе хватает: **{ставка - opponentBalance} $**"
                embed.set_thumbnail(avatar(opponent))
                await ctx.respond(embed=embed, ephemeral=True)
                return

            async def acceptCallback(interaction):
                if interaction.user.id != opponent.id:
                    await interaction.response.defer()
                    return
                
                nonlocal _view
                _view.stop()

                opponentBalance = await BALANCE.get(opponent.id)
                if opponentBalance < ставка:
                    embed.title = "Недостаточно средств!"
                    embed.description = f"<@{opponent.id}>, у вас **недостаточно средств**\nНе хватает: **{ставка - opponentBalance} $**"
                    embed.set_thumbnail(avatar(opponent))
                    await ctx.edit(embed=embed, ephemeral=True)
                    return

                await handler(interaction)

            async def rejectCallback(interaction):
                if interaction.user.id != opponent.id:
                    await interaction.response.defer()
                    return
                
                nonlocal _view
                _view.stop()

            accept = Button(label="Принять", style=discord.ButtonStyle.green)
            accept.callback = acceptCallback

            reject = Button(label="Отклонить", style=discord.ButtonStyle.red)
            reject.callback = rejectCallback

            _view = View()

            _view.add_item(accept)
            _view.add_item(reject)

            _view.on_timeout = lambda: _timeout(_view, [ctx.author.id, opponent.id])

            embed.description = f"{ctx.author.mention} хочет **сразиться** с вами на **{ставка} $**"
            await ctx.respond(f"{opponent.mention}", embed=embed, view=_view)
        else:
            await BALANCE.update(ctx.author.id, -ставка)
    
            async def joinCallback(interaction):
                if interaction.user.id == ctx.author.id:
                    await interaction.response.defer()
                    return
                
                nonlocal _view
                _view.stop()
    
                opponentBalance = await BALANCE.get(interaction.user.id)
                if opponentBalance < ставка:
                    embed.title = "Недостаточно средств!"
                    embed.description = f"<@{interaction.user.id}>, у вас **недостаточно средств**\nНе хватает: **{ставка - opponentBalance} $**"
                    await interaction.respond(embed=embed, ephemeral=True)
                    return
    
                await BALANCE.update(interaction.user.id, -ставка)
    
                await handler(interaction)
            
            embed.title = "Дуэли"
            embed.description = f"{ctx.author.mention} создал дуэль на **{ставка} $**"
            
            join = Button(label="Присоединиться", style=discord.ButtonStyle.gray)
            join.callback = joinCallback
    
            _view = View(timeout=TIMEOUT)
            _view.add_item(join)
            _view.on_timeout = lambda: _timeout(_view, [ctx.author.id])
    
            await ctx.respond(embed=embed, view=_view)

def setup(bot):
    bot.add_cog(gamesCog(bot))