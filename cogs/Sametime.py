from discord.ext import commands
import math
from datetime import datetime, timedelta


class SametimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

@commands.command()
async def Sametime(self, ctx):
    await ctx.send("選擇同時起飛(指定時間)模式!")

async def setup(bot):
    await bot.add_cog(SametimeCog(bot))