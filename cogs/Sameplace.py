from discord.ext import commands
import math
from datetime import datetime, timedelta


class SameplaceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@commands.command()
async def Sameplace(self, ctx):
    await ctx.send("選擇同地起飛(指定座標)模式!")

async def setup(bot):
    await bot.add_cog(SameplaceCog(bot))