import discord

def avatar(user: discord.Member):
    return user.avatar.url if user.avatar else user.default_avatar.url