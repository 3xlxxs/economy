from database import ROLES, BALANCE
from discord.ext import commands
from discord.ui import View, Button, Modal, InputText
from utils import avatar
import discord
import re

class rolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    role = discord.SlashCommandGroup(name="role", description="Личные роли")

    @role.command(name="create", description="Создать личную роль")
    @discord.option("название", str)
    @discord.option("цвет", str)
    async def _create(self, ctx, название: str, цвет: str):
        embed = discord.Embed(title="Создание личной роли", color=0x2b2d31, thumbnail=avatar(ctx.author))
        balance = await BALANCE.get(ctx.author.id)

        if await ROLES.get(ctx.author.id):
            embed.description = f"{ctx.author.mention}, у вас уже есть **личная роль**"
            await ctx.respond(embed=embed)
            return

        if balance < 1000:
            embed.title = "Недостаточно средств!"
            embed.description = f"{ctx.author.mention}, У вас **недостаточно средств**\nНе хватает: **{1000 - balance} $**"
            await ctx.respond(embed=embed)
            return

        if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', цвет):
            embed.description = f"{ctx.author.mention}, вы **неверно** указали **цвет** роли.\nВыберите подходящий **[HEX цвет](https://htmlcolorcodes.com/)**"
            await ctx.respond(embed=embed)
            return

        цвет = цвет.replace("#", "")
        role = await ctx.guild.create_role(name=название, color=discord.Color(value=int(цвет, 16)))
        await ctx.author.add_roles(role)
        await ROLES.update(ctx.author.id, role.id)
        await BALANCE.update(ctx.author.id, -1000)
        embed.description = f"{ctx.author.mention}, вы успешно **создали** личную роль {role.mention}"
        await ctx.respond(embed=embed)

    @role.command(name="manage", description="Управление ролью")
    async def _manage(self, ctx):
        embed = discord.Embed(title="Управление личной ролью", color=0x2b2d31, thumbnail=avatar(ctx.author))

        exists = await ROLES.get(ctx.author.id)
        if not exists:
            embed.description = f"{ctx.author.mention}, у вас **нет** личной роли"
            await ctx.respond(embed=embed)
            return

        role = ctx.guild.get_role(exists)
        if role is None: return

        # class default(discord.ui.View):
        #     def __init__(self):
        #         super().__init__(timeout=180)
        #     
        #     @discord.ui.button(label = "Изменить название")
        #     async def change_name(self, button: discord.ui.Button, interaction: discord.Interaction):
        #         if interaction.user != ctx.author:
        #             await interaction.response.defer()
        #             return
        # 
        #         async def modalCallback(interaction):
        #             name = interaction.data['components'][0]['components'][0]['value']
        #             await role.edit(name=name)
        # 
        #             embed.description = f"{ctx.author.mention}, вы успешно **изменили** название роли на **{name}**"
        # 
        #             await ctx.edit()
        #             await interaction.respond(embed=embed, ephemeral=True, delete_after=5)
        # 
        #         _modal = Modal(
        #             InputText(
        #                 label="Название",
        #             ),
        #             title="Личные роли"
        #         )
        #         _modal.callback = modalCallback
        # 
        #         await interaction.response.send_modal(_modal)

        async def default():
            view = View(timeout=180, disable_on_timeout=True)
            embed.description = f"{ctx.author.mention}, выберите **действие** с ролью {role.mention}"

            async def nameCallback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.defer()
                    return

                async def modalCallback(interaction):
                    name = interaction.data['components'][0]['components'][0]['value']
                    await role.edit(name=name)

                    async def backCallback(interaction):
                        await interaction.response.defer()
                        if interaction.user.id != ctx.author.id:
                            return
                        
                        newEmbed, newView = await default()
                        await ctx.edit(embed=newEmbed, view=newView)

                    embed.description = f"{ctx.author.mention}, вы успешно **изменили** название роли на **{name}**"
                    
                    back = Button(label="Назад")
                    back.callback = backCallback

                    view.clear_items()
                    view.add_item(back)

                    await ctx.edit(embed=embed, view=view)
                    await interaction.response.defer()

                _modal = Modal(
                    InputText(
                        label="Название",
                    ),
                    title="Личные роли"
                )
                _modal.callback = modalCallback

                await interaction.response.send_modal(_modal)

            async def colorCallback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.defer()
                    return

                async def modalCallback(interaction):
                    color = interaction.data['components'][0]['components'][0]['value']

                    async def backCallback(interaction):
                        await interaction.response.defer()
                        if interaction.user.id != ctx.author.id:
                            return
                        
                        newEmbed, newView = await default()
                        await ctx.edit(embed=newEmbed, view=newView)

                    back = Button(label="Назад")
                    back.callback = backCallback

                    view.clear_items()
                    view.add_item(back)

                    if not re.match(r'^#(?:[0-9a-fA-F]{3}){1,2}$', color):
                        embed.description = f"{ctx.author.mention}, вы **неверно** указали **цвет** роли.\nВыберите подходящий **[HEX цвет](https://htmlcolorcodes.com/)**"
                        await ctx.edit(embed=embed, view=view)
                        await interaction.response.defer()
                        return

                    embed.description = f"{ctx.author.mention}, вы успешно **изменили** цвет роли на **{color}**"

                    await role.edit(color=discord.Color(value=int(color.replace("#", ""), 16)))
                    await ctx.edit(embed=embed, view=view)
                    await interaction.response.defer()

                _modal = Modal(
                    InputText(
                        label="Цвет",
                        placeholder="HEX Цвет — #RRGGBB"
                    ),
                    title="Личные роли"
                )
                _modal.callback = modalCallback

                await interaction.response.send_modal(_modal)

            # async def deleteCallback(interaction):
            #     await interaction.response.defer()
            #     await role.delete()
            #     await Roles.update(ctx.author.id, None)
            #     await update_embed_and_view(f"{ctx.author.mention}, вы успешно **удалили** свою личную роль **{role.name}**", True)

            # Создание кнопок
            nameButton = Button(label="Изменить название")
            nameButton.callback = nameCallback

            colorButton = Button(label="Изменить цвет")
            colorButton.callback = colorCallback

            # deleteButton = Button(label="Удалить", style=discord.ButtonStyle.danger)
            # deleteButton.callback = delete_role

            # Добавление кнопок в представление
            view.add_item(nameButton)
            view.add_item(colorButton)
            # view.add_item(delete_button)

            return embed, view

        embed, view = await default()

        await ctx.respond(embed=embed, view=view)

def setup(bot):
    bot.add_cog(rolesCog(bot))