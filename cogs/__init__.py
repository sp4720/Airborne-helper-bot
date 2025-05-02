from discord.ext import commands

class __init__Cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(__init__Cog(bot))