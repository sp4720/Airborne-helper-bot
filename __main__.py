from lib2to3.fixes.fix_metaclass import find_metas

import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix = "!", intents = intents)

@bot.event
async def on_ready():
    print(f"目前登入身分 --> {bot.user}")
    print("指揮官，今天我們要空降哪裡呢?")
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.command()
async def airstrike(ctx):
    Sametime_button = Button(label = "同時起飛(指定時間)", style = discord.ButtonStyle.blurple, custom_id = "sametime")
    Sameplace_button = Button(label = "同地起飛(指定座標)", style = discord.ButtonStyle.blurple, custom_id = "sameplace")

    view = View()
    view.add_item(Sametime_button)
    view.add_item(Sameplace_button)

    await ctx.send("指揮官，要怎麼出擊呢?")

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data["custom_id"] == "sametime":
            await bot.load_extension("cogs.sametime")
            await interaction.response.send_message("載入同時起飛模組0u0b")
        elif interaction.data["custom_id"] == "sameplace":
            await bot.load_extension("cogs.sameplace")
            await interaction.response.send_message("<載入同地起飛模組>d0u0")


if __name__ == "__main__":
    bot.run("MTM2Njc3MzQyMzAwMjYxNTg0OA.GKJvaS.tDKpssinX_pPlwsp_aWflcxrzDhQrWQ3K953Ro")