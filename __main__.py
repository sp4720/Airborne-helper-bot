from lib2to3.fixes.fix_metaclass import find_metas

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, Modal, TextInput, View, Button
import math
from datetime import datetime, timedelta
import asyncio
import re


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = "/", intents = intents)

@bot.event
async def on_ready():
    print(f"目前登入身分 --> {bot.user}")
    print("指揮官，空降行動開始，祝您武運昌隆!")


#目標地點/空降地點表單
class GetcoorinfoModal(Modal):
    def __init__(self):
        super().__init__(title = "請輸入空降目標座標 、跳板目標座標以及跳板類型：")
        self.coor_target = TextInput(
            label = "請輸入空降目標座標:",
            placeholder = "X, Y",
            style = discord.TextStyle.short,
            required = True
        )

        self.coor_step = TextInput(
            label = "請輸入跳板目標座標:",
            placeholder = "X, Y",
            style = discord.TextStyle.short,
            required = True
        )

        self.step_select = TextInput(
            label = "請輸入跳板類型:",
            placeholder = "(哨站請輸入1，平台請輸入2)",
            style = discord.TextStyle.short,
            required = True
        )


        self.add_item(self.coor_target)
        self.add_item(self.coor_step)
        self.add_item(self.step_select)

    async def on_submit(self, interaction: discord.Interaction):
        try:

            xtar_str, ytar_str = re.split(r"[,\s]+", self.coor_target.value)
            xtar = int(xtar_str.strip())
            ytar = int(ytar_str.strip())

            xstp_str, ystp_str = re.split(r"[,\s]+", self.coor_step.value)
            xstp = int(xstp_str.strip())
            ystp = int(ystp_str.strip())

            step_type = int(self.step_select.value.strip())
            if step_type == 1:
                step_type_str = "哨站"
            elif step_type == 2:
                step_type_str = "平台"
            else:
                step_type_str = "你應該輸入錯囉"

            await interaction.response.send_message(
                f"座標獲取成功!"
                f"空降目標座標:({xtar}, {ytar})\n"
                f"跳板座標:({xstp}, {ystp})\n"
                f"跳板類型為{step_type_str}",
                ephemeral = True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"資料格式錯誤，請確認座標格式為X,Y(英文逗號)，跳板類型為1或2。\n錯誤訊息:{str(e)}",
                ephemeral = True
            )


#同時出發所需資訊表單
class SametimeinfoModal(Modal):
    def __init__(self):
        super().__init__(title = "請輸入出發時間、到達時間以及曲率航速：")
        self.deptime = TextInput(
            label = "請輸入預計出發的時間(24小時制):",
            placeholder = "HH:MM",
            style = discord.TextStyle.short,
            required = True
        )

        self.arrivetime = TextInput(
            label = "請輸入預計到達空降目標的時間(24小時制):",
            placeholder = "HH:MM",
            style = discord.TextStyle.short,
            required = True
        )

        self.fspd = TextInput(
            label = "請輸入艦隊的曲率航速:",
            placeholder = "0000",
            style = discord.TextStyle.short,
            required = True
        )

        self.add_item(self.deptime)
        self.add_item(self.arrivetime)
        self.add_item(self.fspd)

#同地出發資訊表單
class SameplaceinfoModal(Modal):
    def __init__(self):
        super().__init__(title = "請輸入出發地點、到達時間以及曲率航速：")
        self.deptime = TextInput(
            label = "請輸入預計出發的地點:",
            placeholder = "X, Y",
            style = discord.TextStyle.short,
            required = True
        )

        self.arrivetime = TextInput(
            label = "請輸入預計到達空降目標的時間(24小時制):",
            placeholder = "HH:MM",
            style = discord.TextStyle.short,
            required = True
        )

        self.fspd = TextInput(
            label = "請輸入艦隊的曲率航速:",
            placeholder = "0000",
            style = discord.TextStyle.short,
            required = True
        )

        self.add_item(self.deptime)
        self.add_item(self.arrivetime)
        self.add_item(self.fspd)








@bot.command()
async def airstrike(ctx):
    print("calling airstrike")
    await ctx.send("指揮官，空降行動開始!")
    coor_info_button = Button(label = "開始輸入座標!", style = discord.ButtonStyle.blurple, custom_id = "coor_info")
    view = View()
    view.add_item(coor_info_button)

    Sametime_button = Button(label = "同時起飛(指定時間)", style = discord.ButtonStyle.blurple, custom_id = "sametime")
    Sameplace_button = Button(label = "同地起飛(指定座標)", style = discord.ButtonStyle.blurple, custom_id = "sameplace")
    view2 = View()
    view2.add_item(Sametime_button)
    view2.add_item(Sameplace_button)

    await ctx.send("指揮官，要空降哪裡呢?", view = view)
    await ctx.send("請選擇空降方式：", view = view2)







@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data["custom_id"]

        if custom_id == "coor_info":
            await interaction.response.send_modal(GetcoorinfoModal())
        elif custom_id == "sametime":
            await interaction.response.send_modal(SametimeinfoModal())
        elif custom_id == "sameplace":
            if interaction.data["custom_id"] == "sameplace":
                await interaction.response.send_modal(SameplaceinfoModal())



if __name__ == "__main__":
    bot.run("MTM2Njc3MzQyMzAwMjYxNTg0OA.GKJvaS.tDKpssinX_pPlwsp_aWflcxrzDhQrWQ3K953Ro")