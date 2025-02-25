from discord.ui import Modal, InputText
from discord.ext import commands
from utils import avatar
import discord
import asyncio
import time

class otherCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="remind", description="Напомнить позже", integration_types={discord.IntegrationType.user_install, discord.IntegrationType.guild_install})
    async def _remind(self, ctx):
        async def modalCallback(interaction):
            reason = interaction.data['components'][0]['components'][0]['value']
            seconds = int(interaction.data['components'][1]['components'][0]['value'])
            minutes = int(interaction.data['components'][2]['components'][0]['value']) * 60
            hours   = int(interaction.data['components'][3]['components'][0]['value']) * 3600

            embed = discord.Embed(
                color=0x2b2d31,
                title="Напомнить позже",
                description=f"**Хорошо,** {ctx.author.mention}, я напомню вам **{reason}** <t:{int(time.time() + seconds+minutes+hours)}:R>",
                thumbnail=avatar(ctx.author)
            )

            await interaction.respond(embed=embed, ephemeral=True, delete_after=15)

            await asyncio.sleep(int(seconds+minutes+hours))

            await ctx.respond(f"{ctx.author.mention}, напоминаю **{reason}**")


        _modal = Modal(
            InputText(
                label="Зачем?",
                placeholder="использовать /timely"
            ),
            InputText(
                label="Через сколько? (СЕКУНД)",
                value="0"
            ),
            InputText(
                label="Через сколько? (МИНУТ)",
                value="0"
            ),
            InputText(
                label="Через сколько? (ЧАСОВ)",
                value="0"
            ),
            title="Напоминание"
        )
        _modal.callback = modalCallback

        await ctx.response.send_modal(_modal)

def setup(bot):
    bot.add_cog(otherCog(bot))