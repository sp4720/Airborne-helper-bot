import discord
from discord.ext import commands
from discord.ui import Select, Modal, TextInput, View
import math
from datetime import datetime, timedelta

class GetinfoModal(Modal):
    def __init__(self):
        super().__init__(title = "請輸入座標、曲率航速以及預計到達時間：")
        self.x_target = TextInput(
            label = "請輸入空降目標座標(X, Y):",
            placeholder = "0, 0"
            style = discord.TextStyle.short,
            required = True
        )
        self

class SametimeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
#點擊按鈕後運行
    @commands.command()
    async def sametime_action(self, interaction: discord.Interaction):
        await interaction.followup.send("選擇同時起飛(指定時間)模式!")

async def setup(bot):
    await bot.add_cog(SametimeCog(bot))