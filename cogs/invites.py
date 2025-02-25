from database import INVITES, BALANCE
from discord.ext import commands
from utils import avatar
import discord
import json

invites = {}

class invitesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="referral", description="Управление реферальной ссылкой")
    @discord.option("пользователь", discord.SlashCommandOptionType.user, required=False)
    async def referral(self, ctx: discord.ApplicationContext, пользователь):
        user = пользователь or ctx.author

        embed = discord.Embed(color=0x2b2d31, title="Реферальная программа", thumbnail=avatar(user))

        invite = await INVITES.getById(user.id)

        if invite:
            code, users = invite
        else:
            if пользователь:
                embed.description = f"{user.mention} ещё **не участвует** в **реферальной программе**"
                await ctx.respond(embed=embed)
                return
            
            invite = await ctx.guild.text_channels[0].create_invite()
            code, users = invite.code, []
            await INVITES.update(user.id, code, json.dumps(users))

        users = json.loads(users)
        
        embed.add_field(name="Пользователь", value=f"{user.mention}")
        embed.add_field(name="Реферальная ссылка", value=f"```discord.gg/{code}```")
        embed.add_field(name="Приглашений", value=f"```{len(users)}```")
        embed.add_field(name="Всего выплачено", value=f"**```ansi\n{len(users)*10000} [0;2m[0;32m$[0m[0m\n```**", inline=False)

        embed.description = "**Приглашайте** друзей и получайте **10 000 $** за каждого **уникального пользователя**, присоединившегося по вашей **реферальной ссылке**"
       
        await ctx.respond(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Получаем актуальные приглашения перед проверкой
        new = await member.guild.invites()
        old = invites.get(member.guild.id, [])

        # Обновляем кэш приглашений для этого сервера
        invites[member.guild.id] = new

        # Ищем использованное приглашение
        for newInvite in new:
            for oldInvite in old:
                if newInvite.code == oldInvite.code:
                    if newInvite.uses > oldInvite.uses:
                        id, users = await INVITES.getByCode(newInvite.code)
                        user            = await member.guild.fetch_member(id)
                        users           = json.loads(users)

                        unique = not member.id in users
                        
                        if unique: 
                            users.append(member.id)
                            await INVITES.update(id, newInvite.code, json.dumps(users))
                            await BALANCE.update(id, 10000)

                        embed = discord.Embed(color=0x2b2d31, title="Реферальная программа", thumbnail=avatar(member), description=f"**Новый пользователь**" + ("" if unique else "\n-# **НЕ УНИКАЛЬНЫЙ**"))
                        embed.add_field(name="Пользователь", value=f"{member.mention}")
                        embed.add_field(name="Реферальная ссылка", value=f"```discord.gg/{newInvite.code}```")
                        embed.add_field(name="Приглашений", value=f"```ansi\n{len(users)} [0;2m[0;32m↑[0m{'1' if unique else '0'}[0m\n```")
                        embed.add_field(name="Выплата", value=f"**```ansi\n{'10000' if unique else '0'} [0;2m[0;32m$[0m[0m\n```**", inline=False)
                        await user.send(embed=embed)
                        return

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        guild_invites = await invite.guild.invites()
        invites[invite.guild.id] = guild_invites

        # if invite.inviter.id == self.bot.user.id: return
        # 
        # await invite.delete()
        # embed = discord.Embed(color=0x2b2d31, thumbnail=avatar(invite.inviter))
        # embed.description = f"{invite.inviter.mention}, ваша **ссылка приглашения** была **удалена.**\n**Используйте** команду **`/referral`** в <#1334138931364757577>\nВместо **ручного создания ссылок приглашения.**"
        # await invite.inviter.send(embed=embed)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        # Обновляем кэш при удалении приглашения
        guild_invites = await invite.guild.invites()
        invites[invite.guild.id] = guild_invites

#     @commands.slash_command(name="referral_info", description="Информация о рефералах")
#     async def referral_info(self, ctx: discord.ApplicationContext, member: discord.Member = None):
#         member = member or ctx.author
#         invite_data = await INVITES.get(member.id)
# 
#         if not invite_data:
#             embed = discord.Embed(
#                 color=0x2b2d31,
#                 title="Реферальная программа",
#                 description="У пользователя нет реферальной ссылки"
#             )
#             await ctx.respond(embed=embed)
#             return
# 
#         code, uses, users = invite_data
#         users_list = json.loads(users) if isinstance(users, str) else users
# 
#         description = f"- <@{member.id}>\n"
#         description += f"- discord.gg/{code}\n"
#         
#         if users_list:
#             description += "- Приглашённые:\n"
#             for idx, user_id in enumerate(users_list, 1):
#                 description += f"{idx}. <@{user_id}>\n"
#         else:
#             description += "- Пока никто не присоединился"
# 
#         embed = discord.Embed(
#             color=0x2b2d31,
#             title="Информация о рефералах",
#             description=description
#         )
#         embed.set_thumbnail(url=avatar(member))
#         
#         await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(invitesCog(bot))