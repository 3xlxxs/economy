from discord.ui import Button, View
from database import SHOP, BALANCE
from discord.ext import commands
from utils import avatar
import discord

class shopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="shop", description="Магазин ролей")
    async def shop(self, ctx):
        shop_items = await SHOP._all()

        itemsPerPage = 5

        pages = (len(shop_items) + itemsPerPage - 1) // itemsPerPage
        page = 0

        async def _embed(page):
            embed = discord.Embed(title="Магазин", color=0x2b2d31)
            embed.set_thumbnail(url=avatar(ctx.author))

            display = shop_items[page * itemsPerPage: (page + 1) * itemsPerPage]

            exists = []
            for roleId, userId, price, purchases in display:
                role = ctx.guild.get_role(roleId)
                if role:
                    exists.append([roleId, userId, price, purchases, role])

            if exists:
                embed.description = "\n\n".join(
                    f"**{index + 1})** Роль: **{role.mention}**\n"
                    f"- Продавец: **{ctx.guild.get_member(userId).mention if ctx.guild.get_member(userId) else 'Неизвестно'}**\n"
                    f"- Цена: **{price} $**\n"
                    f"- Куплена раз: **{purchases}**"
                    for index, [roleId, userId, price, purchases, role] in enumerate(exists)
                )
            else:
                embed.description = "Магазин **пустой!**"

            embed.set_footer(text=f"Страница {page + 1}/{pages if pages > 0 else 1}")
            return embed, exists

        async def _update(view, page):
            view.clear_items()
            embed, roles = await _embed(page)

            for i in range(itemsPerPage):
                if i < len(roles):
                    button = Button(label=f"🛒 {i + 1}")
                    data = roles[i]
                    button.callback = lambda interaction, data=data: _buy(interaction, data, view, page)
                else:
                    button = Button(label=f"🛒 {i + 1}", disabled=True)

                view.add_item(button)

            prev = Button(label="Назад")
            prev.callback = lambda interaction: _page(interaction, -1, page, view)

            next = Button(label="Вперёд")
            next.callback = lambda interaction: _page(interaction, 1, page, view)

            view.add_item(prev)
            view.add_item(next)

            await ctx.edit(embed=embed, view=view)

        async def _page(interaction, delta, current_page, view):
            nonlocal page
            if interaction.user.id != ctx.author.id:
                await interaction.response.defer()
                return

            page = (current_page + delta) % (pages if pages > 0 else 1)
            if page != current_page:
                await _update(view, page)
            await interaction.response.defer()

        async def _buy(interaction: discord.Interaction, data, view, current_page):
            if interaction.user.id != ctx.author.id:
                await interaction.response.defer()
                return
            
            embed = discord.Embed(title="Магазин", color=0x2b2d31, thumbnail=avatar(ctx.author))

            exists = await SHOP.get(data[0])
            if not exists:
                await interaction.respond("hi")
                await _update(view, current_page)
                return

            userId, price, _ = exists
            role: discord.Role = ctx.guild.get_role(data[0])
            if not role:
                await interaction.respond("hi2")
                await SHOP.rem(role)
                await _update(view, current_page)
                return

            balance = await BALANCE.get(interaction.user.id)
            if balance < price:
                embed = discord.Embed(color=0x2b2d31)
                embed.set_thumbnail(url=avatar(interaction.user))
                embed.title = "Недостаточно средств!"
                embed.description = f"{interaction.user.mention}, У вас **недостаточно средств**\nНе хватает: **{price - balance} $**"
                await interaction.respond(embed=embed, ephemeral=True)
                return
            
            async def confirmCallback(interaction: discord.Interaction):
                if balance < price:
                    embed.title = "Недостаточно средств!"
                    embed.description = f"{interaction.user.mention}, У вас **недостаточно средств**\nНе хватает: **{price - balance} $**"
                    await interaction.edit(embed=embed, view=None)
                    return
                
                await ctx.author.add_roles(role)
                
                await BALANCE.update(ctx.author.id, -price)
                await BALANCE.update(userId, price)
                await SHOP.increment_purchase(data[0])

                embed.description = f"{ctx.author.mention}, вы **успешно** приобрели роль {role.mention} за **{price} $**"
                await interaction.edit(embed=embed, view=None)

            async def cancelCallback(interaction: discord.Interaction):
                embed.description = f"{ctx.author.mention}, вы **отменили** покупку роли"
                await interaction.edit(embed=embed, view=None)

            embed.description = f"{ctx.author.mention}, вы **уверены** что хотите приобрести роль {role.mention} за **{price} $** ?"

            confirm = Button(label=f"Подтвердить", style=discord.ButtonStyle.green)
            confirm.callback = confirmCallback

            cancel  = Button(label=f"Отменить", style=discord.ButtonStyle.danger)
            cancel.callback = cancelCallback

            view = View()
            view.add_item(confirm)
            view.add_item(cancel)

            await interaction.respond(embed=embed, view=view, ephemeral=True)

        view = View(timeout=180)

        message = await ctx.respond(embed=(await _embed(0))[0], view=view)

        await _update(view, page=0)

def setup(bot):
    bot.add_cog(shopCog(bot))