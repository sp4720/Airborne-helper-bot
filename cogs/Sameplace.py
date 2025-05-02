import discord
from discord.ext import commands
from discord.ui import Select, Modal, TextInput, View
import math
from datetime import datetime, timedelta


class SameplaceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
#點擊按鈕後運行
    @commands.command()
    async def sameplace_action(self, interaction: discord.Interaction):
        await interaction.followup.send("選擇同地起飛(指定座標)模式!")

async def setup(bot):
    await bot.add_cog(SameplaceCog(bot))