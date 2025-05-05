from cgi import print_form
from lib2to3.fixes.fix_metaclass import find_metas
from operator import truediv

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, Modal, TextInput, View, Button
import math
from datetime import datetime, timedelta, timezone, date
from zoneinfo import ZoneInfo
import asyncio
import re
from dotenv import load_dotenv
import os

# 加載指定的 .env 檔案 token.env
load_dotenv('token.env')

# 測試是否成功加載
token = os.getenv("DISCORD_TOKEN")
if token:
    print("Token loaded successfully!")
else:
    print("Failed to load token.")

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
bot = commands.Bot(command_prefix = "/", intents = intents)
tree = bot.tree

#全域資料儲存
user_data = {
    "coor_info": {
        "coor_tar_x":0,
        "coor_tar_y":0,
        "coor_step_x":0,
        "coor_step_y":0,
        "coor_steptype":0
    },

    "sametime_info": {
        "deptime":[],
        "arrivetime":[],
        "fspd":0
    },

    "sameplace_info": {
        "coor_dep_x":0,
        "coor_dep_y":0,
        "arrivetime":[],
        "fspd":0
    },

    "status":{
        "coor_info_done": False,
        "timeplace_info_done": False,
        "fmode": "default",
        "result": "result"
    }
}

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f"已同步{len(synced)}個指令")
    except Exception as e:
        print(f"同步指令失敗:{e}")

    print(f"目前登入身分 --> {bot.user}")
    print("指揮官，空降行動開始，祝您武運昌隆!")

    await bot.change_presence(
        status = discord.Status.online,
        activity = discord.Game(name = "/airstrike 啟動空襲!")
    )


#目標地點/空降地點表單
class GetcoorinfoModal(Modal):
    def __init__(self, user_id):
        self.user_id = user_id
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
            user_id = interaction.user.id
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

            user_data[user_id]["coor_info"]["coor_tar_x"] = xtar
            user_data[user_id]["coor_info"]["coor_tar_y"] = ytar
            user_data[user_id]["coor_info"]["coor_step_x"] = xstp
            user_data[user_id]["coor_info"]["coor_step_y"] = ystp
            user_data[user_id]["coor_info"]["coor_steptype"] = step_type
            user_data[user_id]["status"]["coor_info_done"] = True

            await interaction.response.send_message(
                f"座標獲取成功!"
                f"空降目標座標:({xtar}, {ytar})\n"
                f"跳板座標:({xstp}, {ystp})\n"
                f"跳板類型為{step_type_str}",
                ephemeral = True
            )
            #雙表單完成檢查
            if user_data[user_id]["status"]["coor_info_done"] and (user_data[user_id]["status"]["timeplace_info_done"]):
                start_button = Button(label = "開始計算", style = discord.ButtonStyle.green, custom_id = "start_calc")
                view2 = View()
                view2.add_item(start_button)
                await interaction.followup.send("資料輸入完成!", view = view2, ephmeral = True)
            else:
                await interaction.followup.send("請繼續填寫同時/同地起飛資訊!", ephemeral = True)

        except Exception as e:
            await interaction.response.send_message(
                f"資料格式錯誤，請確認座標格式為X,Y(英文逗號)，跳板類型為1或2。\n錯誤訊息:{str(e)}",
                ephemeral = True
            )


#同時出發所需資訊表單
class SametimeinfoModal(Modal):
    def __init__(self, used_id):
        self.user_id = used_id
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

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id

            deptime_str = self.deptime.value
            deptime = datetime.strptime(deptime_str, "%H:%M")

            arrivetime_str = self.arrivetime.value
            arrivetime = datetime.strptime(arrivetime_str, "%H:%M")

            fspd = int(self.fspd.value.strip())

            user_data[user_id]["sametime_info"]["deptime"].append(deptime)
            user_data[user_id]["sametime_info"]["arrivetime"].append(arrivetime)
            user_data[user_id]["sametime_info"]["fspd"] = fspd
            user_data[user_id]["status"]["timeplace_info_done"] = True
            user_data[user_id]["status"]["fmode"] = "sametime"

            await interaction.response.send_message(
                f"資訊獲取獲取成功!\n"
                f"預計出發時間為:({deptime.strftime("%H:%M")})\n"
                f"抵達目標時間為:({arrivetime.strftime("%H:%M")})\n"
                f"艦隊曲率航速為:{fspd}",
                ephemeral=True
            )
            #雙表單完成檢查
            if user_data[user_id]["status"]["coor_info_done"] and (user_data[user_id]["status"]["timeplace_info_done"]):
                start_button = Button(label = "開始計算", style = discord.ButtonStyle.green, custom_id = "start_calc")
                view2 = View()
                view2.add_item(start_button)
                await interaction.followup.send("資料輸入完成!", view = view2, ephemeral = True)
            else:
                interaction.followup.send("請繼續填寫座標資訊!", ephemeral = True)

        except Exception as e:
            await interaction.response.send_message(
                f"資料格式錯誤，請確認時間格式為HH:MM(英文逗號)，航速為整數。\n錯誤訊息:{str(e)}",
                ephemeral=True
            )

#同地出發資訊表單
class SameplaceinfoModal(Modal):
    def __init__(self, user_id):
        self.user_id = user_id
        super().__init__(title = "請輸入出發地點、到達時間以及曲率航速：")
        self.coor_dep = TextInput(
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

        self.add_item(self.coor_dep)
        self.add_item(self.arrivetime)
        self.add_item(self.fspd)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
            xcoor_dep_str, ycoor_dep_str = re.split(r"[,\s]+", self.coor_dep.value)
            xdep = int(xcoor_dep_str.strip())
            ydep = int(ycoor_dep_str.strip())

            arrivetime_str = self.arrivetime.value
            arrivetime = datetime.strptime(arrivetime_str, "%H:%M")

            fspd = int(self.fspd.value.strip())

            user_data[user_id]["sameplace_info"]["coor_dep_x"] = xdep
            user_data[user_id]["sameplace_info"]["coor_dep_y"] = ydep
            user_data[user_id]["sameplace_info"]["arrivetime"].append(arrivetime)
            user_data[user_id]["sameplace_info"]["fspd"] = fspd
            user_data[user_id]["status"]["timeplace_info_done"] = True
            user_data[user_id]["status"]["fmode"] = "sameplace"

            await interaction.response.send_message(
                f"資訊獲取獲取成功!"
                f"預計出發座標為:({xdep}, {ydep})\n"
                f"出發時間為:({arrivetime.strftime("%H:%M")})\n"
                f"艦隊曲率航速為:{fspd}",
                ephemeral=True
            )
            #雙表單完成檢查
            if user_data[user_id]["status"]["coor_info_done"] and (user_data[user_id]["status"]["timeplace_info_done"]):
                start_button = Button(label = "開始計算", style = discord.ButtonStyle.green, custom_id = "start_calc")
                view2 = View()
                view2.add_item(start_button)
                await interaction.followup.send("資料輸入完成!", view = view2, ephemeral = True)
            else:
                interaction.followup.send("請繼續填寫座標資訊!", ephemeral = True)

        except Exception as e:
            await interaction.response.send_message(
                f"資料格式錯誤，請確認時間格式為HH:MM(英文逗號)，航速為整數。\n錯誤訊息:{str(e)}",
                ephemeral=True
            )

#打包所需資訊
class PackinfoModal(Modal):
    def __init__(self, user: discord.User | discord.Member, user_data: dict):
        self.user = user
        self.user_data = user_data
        super().__init__(title = "請輸入艦隊以及指揮官名稱：")
        self.commander_name = TextInput(
            label = "請填寫指揮官名稱:",
            placeholder = "可留空，默認使用伺服器暱稱",
            style = discord.TextStyle.short,
            required = False
        )

        self.fleet_name = TextInput(
            label = "請填寫艦隊名稱:",
            placeholder = "可留空",
            style = discord.TextStyle.short,
            required = False
        )
        self.add_item(self.commander_name)
        self.add_item(self.fleet_name)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            input_commander_name = self.commander_name.value.strip() if self.commander_name.value else ""
            final_commander_name = input_commander_name or self.user.display_name
            final_fleet_name = self.fleet_name.value.strip() if self.fleet_name.value else ""

            user_id = self.user.id
            result_text = self.user_data[user_id]["status"]["result"]

            await interaction.response.send_message(f"指揮官{final_commander_name}，您的艦隊{final_fleet_name}的空襲資訊如下:\n{result_text}")

        except Exception as e:
            await interaction.response.send_message(f"資料格式錯誤，請確認。\n錯誤訊息:{str(e)}")


async def Getjoinfspd(interaction: discord.Interaction):
    user_id = interaction.user.id
    user_display_name = interaction.user.name or interaction.user.nick
    channel_id = interaction.channel.id

    await interaction.followup.send(f"指揮官{user_display_name}，您的艦隊曲率航速是多少呢?(請輸入整數並在60秒內回答)", ephemeral = True)

    def check(m: discord.message):
        return m.author.id == user_id and m.channel.id == channel_id
    try:
        fspd = await bot.wait_for("message", check = check, timeout = 60)
        fspd_content = int(fspd.content)
        await fspd.delete()
        await interaction.followup.send(f"您的航速為:{fspd_content}。", ephemeral = True)

        fmode = user_data[user_id]["status"]["fmode"]

        if fmode == "sametime":
            user_data[user_id]["sametime_info"]["fspd"] = fspd_content
        elif fmode == "sameplace":
            user_data[user_id]["sameplace_info"]["fspd"] = fspd_content

        result_text = calculate_airstrike(user_id)
        await interaction.followup.send(result_text, ephemeral=True)
        pack_button = Button(label="整理結果並公開發表", style=discord.ButtonStyle.green, custom_id = "pack_result", row = 0)
        view4 = View()
        view4.add_item(pack_button)
        await interaction.followup.send("指揮官，您還可以:", view=view4, ephemeral=True)


    except Exception as e:
        await interaction.followup.send(f"超時未回覆或發生錯誤\n{e}")

#時間轉換
def deltaformatted(tdelta):
    total_seconds = int(tdelta.total_seconds())
    hours = total_seconds //3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    formatted = f"{hours:02}:{minutes:02}:{seconds:02}"
    return formatted


#清空資訊
def reset_user_data(user_id):
    user_data[user_id] = {
        "coor_info": {
            "coor_tar_x": 0,
            "coor_tar_y": 0,
            "coor_step_x": 0,
            "coor_step_y": 0,
            "coor_steptype": 0
        },

        "sametime_info": {
            "deptime": [],
            "arrivetime": [],
            "fspd": 0
        },

        "sameplace_info": {
            "coor_dep_x": 0,
            "coor_dep_y": 0,
            "arrivetime": [],
            "fspd": 0
        },

        "status":{
          "coor_info_done": False,
          "timeplace_info_done": False,
            "fmode": "default",
            "result": "result"
        }
    }

#計算過程

#取得跳板角位置
def exactcoor(xtar, ytar, xstp, ystp, step_type):
    xcor = int(xstp % 10)
    ycor = int(ystp % 10)
    if step_type == 1:
        coords = {
            "xtl": int(xstp - xcor),
            "ytl": int(ystp + 10 - ycor),
            "xtr": int(xstp + 10 - xcor),
            "ytr": int(ystp + 10 - ycor),
            "xbl": int(xstp - xcor),
            "ybl": int(ystp - ycor),
            "xbr": int(xstp + 10 - xcor),
            "ybr": int(ystp - ycor)
        }
    else:
        coords = {
            "xtl": int(xstp - 10),
            "ytl": int(ystp + 10),
            "xtr": int(xstp + 10),
            "ytr": int(ystp + 10),
            "xbl": int(xstp - 10),
            "ybl": int(ystp - 10),
            "xbr": int(xstp + 10),
            "ybr": int(ystp - 10)
        }
    dist = {
        "dtl": float(math.sqrt((coords["xtl"] - xtar) ** 2 + (coords["ytl"] - ytar) ** 2)),
        "dtr": float(math.sqrt((coords["xtr"] - xtar) ** 2 + (coords["ytr"] - ytar) ** 2)),
        "dbl": float(math.sqrt((coords["xbl"] - xtar) ** 2 + (coords["ybl"] - ytar) ** 2)),
        "dbr": float(math.sqrt((coords["xbr"] - xtar) ** 2 + (coords["ybr"] - ytar) ** 2))
    }

    result = min(dist, key=dist.get)
    if result == "dtl":
        return coords["xtl"], coords["ytl"]
    elif result == "dtr":
        return coords["xtr"], coords["ytr"]
    elif result == "dbl":
        return coords["xbl"], coords["ybl"]
    else:
        return coords["xbr"], coords["ybr"]

#計算跳板與空降目標連線公式
def get_line_info(xtar, ytar, xexact, yexact):
    if xtar == xexact:
        c = round(xtar)
        return 1, 0, c
    else:
        m_raw = float((yexact - ytar) / (xexact - xtar))
        b_raw = float(ytar - m_raw * xtar)
        m = round(m_raw, 5)
        b = round(b_raw, 5)
        return 2, m, b

#計算同時起飛
def fmode1(deptime, arrivetime, fspd, xstp, ystp, lne, slp, inter, xtar, ytar, xexact, yexact, tolerance=1e-6):
    time = arrivetime - deptime
    if time.total_seconds() < 0:
        time += timedelta(seconds=86400)
    dist = round((0.0001 * fspd) * time.total_seconds(), 5)
    # 得出半徑dist 開始求交點
    if lne == 1:
        xs1 = xstp
        ys1 = round(ytar + dist)
        xs2 = xstp
        ys2 = round(ytar - dist)
    elif lne == 2:
        A = 1 + slp ** 2
        B = 2 * (slp * (inter - ytar) - xtar)
        C = (inter - ytar) ** 2 + xtar ** 2 - dist ** 2
        discriminant = B ** 2 - 4 * A * C
        print(discriminant)
        sqrt_D = math.sqrt(discriminant)
        xs1 = (-B + sqrt_D) / (2 * A)
        xs2 = (-B - sqrt_D) / (2 * A)
        ys1 = slp * xs1 + inter
        ys2 = slp * xs2 + inter

        # print(dist, time.total_seconds(),xexact, yexact, xs1, ys1, xs2, ys2)
    # 得到兩個座標 用向量求何者為同向
    vec = {
        "v0": (xtar - xexact, ytar - yexact),
        "v1": (xs1 - xtar, ys1 - ytar),
        "v2": (xs2 - xtar, ys2 - ytar)
    }
    mag1 = math.hypot(vec["v1"][0], vec["v1"][1])
    mag2 = math.hypot(vec["v2"][0], vec["v2"][1])
    if mag1 == 0 or mag2 == 0:
        return 1, 0, 0, 0
    dot1 = vec["v0"][0] * vec["v1"][0] + vec["v0"][1] * vec["v1"][1]
    dot2 = vec["v0"][0] * vec["v2"][0] + vec["v0"][1] * vec["v2"][1]
    cos_theta1 = dot1 / (mag1 * mag2)
    cos_theta2 = dot2 / (mag1 * mag2)
    print(cos_theta1, cos_theta2)
    if cos_theta1 > 0:
        return 2, round(xs1), round(ys1), dist, time
    elif cos_theta2 > 0:
        return 3, round(xs2), round(ys2), dist, time
    else:
        return 4, 0, 0, 0

# 同地起飛（指定地點起飛）
def fmode2(xexact, yexact, xdep, ydep, xtar, ytar, slp, inter, arrivetime, fspd):
    # 求出發點到跳板的直線以及交點
    if xdep == xexact == xtar:
        disttotar = 0
        xclosest = xdep
        yclosest = ydep

    else:
        slp2_raw = (yexact - ydep) / (xexact - xdep)
        inter2_raw = (yexact - slp2_raw * xexact)
        slp2 = round(slp2_raw, 5)
        inter2 = round(inter2_raw, 5)

        slp_dist_raw = (-1 / slp2)
        inter_dist_raw = (ytar - slp_dist_raw * xtar)
        slp_dist = round(slp_dist_raw, 5)
        inter_dist = round(inter_dist_raw, 5)

        xclosest = (inter_dist - inter2) / (slp2 - slp_dist)
        yclosest = (slp2 * xclosest + inter2)

    # 檢查是否距離超過5jm 如果超過就改為計算出發點最近的交點
        disttotar = math.sqrt((xtar - xclosest) ** 2 + (ytar - yclosest) ** 2)

    if disttotar > 5:
        slp_corr_raw = (-1 / slp)
        inter_corr_raw = (ydep - slp_corr_raw * xdep)
        slp_corr = round(slp_corr_raw, 5)
        inter_corr = round(inter_corr_raw)
        xcorr = (inter_corr - inter) / (slp - slp_corr)
        ycorr = slp * xcorr + inter
        dist = math.sqrt((xcorr - xdep) ** 2 + (ycorr - ydep) ** 2)
        time = round(dist / (fspd * 0.0001))
        timeobj = timedelta(seconds=time)
        estdepobj = arrivetime - timeobj

        if estdepobj.day != arrivetime.day:
            estdepobj += timedelta(seconds=86400)
        dist_corr = math.sqrt((xcorr - xdep) ** 2 + (ycorr - ydep) ** 2)
        timecorr = timedelta(seconds=dist_corr / fspd * 0.0001)
        round(dist)
        return 1, xcorr, ycorr, estdepobj, timeobj, timecorr, dist

    else:
        if xdep == xexact == xtar:
            dist = abs(ytar - ydep)
        else:
            dist = math.sqrt((xtar - xdep) ** 2 + (ytar - ydep) ** 2)

        time = round(dist / (fspd * 0.0001))
        timeobj = timedelta(seconds=time)
        estdepobj = arrivetime - timeobj
        if estdepobj.day != arrivetime.day:
            estdepobj += timedelta(seconds=86400)
        round(dist)
        nocorr = timedelta(hours = 0, minutes = 0, seconds = 0)
        return 2, xdep, ydep, estdepobj, timeobj, nocorr, dist


def calculate_airstrike(user_id:int) -> str:
    xtar = user_data[user_id]["coor_info"]["coor_tar_x"]
    ytar = user_data[user_id]["coor_info"]["coor_tar_y"]
    xstp = user_data[user_id]["coor_info"]["coor_step_x"]
    ystp = user_data[user_id]["coor_info"]["coor_step_y"]
    step_type = user_data[user_id]["coor_info"]["coor_steptype"]
    fmode = user_data[user_id]["status"]["fmode"]
    #print(f"{xtar} {ytar} {xstp} {ystp} {step_type} {fmode}")
    if step_type == 1:
        step_type_o = "哨站"
    elif step_type == 2:
        step_type_o = "平台"

    xexact, yexact = exactcoor(xtar, ytar, xstp, ystp, step_type)

    lne, slp, inter = get_line_info(xtar, ytar, xexact, yexact)
    if fmode == "sametime":
        deptime = user_data[user_id]["sametime_info"]["deptime"][0]
        arrivetime = user_data[user_id]["sametime_info"]["arrivetime"][0]
        fspd = user_data[user_id]["sametime_info"]["fspd"]
        #print(deptime, arrivetime, fspd, xstp, ystp, lne, slp, inter, xtar, ytar, xexact, yexact)
        status, xs, ys, dist, travel_time = fmode1(deptime, arrivetime, fspd, xstp, ystp, lne, slp, inter, xtar, ytar, xexact, yexact, tolerance=1e-6)
        travel_time_formatted = deltaformatted(travel_time)
    elif fmode == "sameplace":
        arrivetime = user_data[user_id]["sameplace_info"]["arrivetime"][0]
        fspd = user_data[user_id]["sameplace_info"]["fspd"]
        xdep = user_data[user_id]["sameplace_info"]["coor_dep_x"]
        ydep = user_data[user_id]["sameplace_info"]["coor_dep_y"]
        status, xs, ys, estdeptime, esttime, timecorr, dist = fmode2(xexact, yexact, xdep, ydep, xtar, ytar, slp, inter, arrivetime, fspd)
        user_data[user_id]["sameplace_info"]["coor_dep_x"] = xs
        user_data[user_id]["sameplace_info"]["coor_dep_y"] = ys
        esttime_formatted = deltaformatted(esttime)
        timecorr_formatted = deltaformatted(timecorr)

    if fmode == "sametime":
        result_text = (
            f"📍你的指定空降座標為:({xtar}, {ytar})\n"
            f"🛸你的指定跳板座標為:({xstp}, {ystp})，類型為:{step_type_o}\n"
            f"🚀你預定於{deptime.strftime("%H:%M")}出發，經過{dist}JM，並於{arrivetime.strftime("%H:%M")}抵達!\n"
            f"📍你應該由({xs}, {ys})出發，共花費{travel_time_formatted}\n"
        )
        user_data[user_id]["status"]["result"] = result_text
        return result_text

    elif fmode == "sameplace":
        if status == 1:
            result_text = (
                f"📍你的指定空降座標為:({xtar}, {ytar})\n"
                f"🛸你的指定跳板座標為:({xstp}, {ystp})，類型為:{step_type_o}\n"
                f"📏由你的指定出發位置出發會偏離空降目標點超過5JM，我們將幫你計算最近的推薦出發點!\n"
                f"📍你應該改由({xs}, {ys})出發，從你的指定出發座標出發前往新出發座標共花費({timecorr_formatted})\n"
                f"⏰到達建議出發地點後，你應該於({estdeptime.strftime("%H:%M:%S")})出發，經過{dist}JM\n"
                f"⏰花費{esttime_formatted}，並在({arrivetime.strftime('%H:%M')})抵達!"
            )
            user_data[user_id]["status"]["result"] = result_text
            return result_text

        elif status == 2:
            result_text = (
                f"📍你的指定空降座標為:({xtar}, {ytar})\n"
                f"🛸你的指定跳板座標為:({xstp}, {ystp})，類型為:{step_type_o}\n"
                f"⏰你應該於({estdeptime.strftime("%H:%M:%S")})由({xdep},{ydep})出發，經過{dist}JM\n"
                f"⏱花費{esttime_formatted}，並在({arrivetime.strftime('%H:%M')})抵達!"
            )
        user_data[user_id]["status"]["result"] = result_text
        return result_text

#創建活動
async def create_event(interaction: discord.Interaction):
    guild = interaction.guild
    channel = interaction.channel
    user_id = interaction.user.id
    start_time = datetime.now(timezone.utc)

    xtar = user_data[user_id]["coor_info"]["coor_tar_x"]
    ytar = user_data[user_id]["coor_info"]["coor_tar_y"]
    xstp = user_data[user_id]["coor_info"]["coor_step_x"]
    ystp = user_data[user_id]["coor_info"]["coor_step_y"]
    stp_type = user_data[user_id]["coor_info"]["coor_steptype"]
    fmode =  user_data[user_id]["status"]["fmode"]

    if fmode == "sametime":
        end_time = user_data[user_id]["sametime_info"]["arrivetime"][0]
        fmode_str = "同時起飛"
    elif fmode == "sameplace":
        end_time = user_data[user_id]["sameplace_info"]["arrivetime"][0]
        fmode_str = "同地起飛"

    taiwan_tz = ZoneInfo("Asia/Taipei")
    local_end_time = datetime.combine(date.today(), end_time.time()).replace(tzinfo=taiwan_tz)
    real_end_time = local_end_time.astimezone(timezone.utc)
    if real_end_time < datetime.now(timezone.utc):
        real_end_time += timedelta(days=1)
    real_end_time_str = real_end_time.strftime("%Y/%m/%d")


    if stp_type == 1:
        stp_type_str = "哨站"
    elif stp_type == 2:
        stp_type_str = "平台"

    if fmode == "sametime":
        f_assigned = user_data[user_id]["sametime_info"]["deptime"][0]
        f_assigned_str = f"出發時間為:{f_assigned.strftime('%H:%M')})"
    elif fmode == "sameplace":
        f_assigned_x = user_data[user_id]["sameplace_info"]["coor_dep_x"]
        f_assigned_y = user_data[user_id]["sameplace_info"]["coor_dep_y"]
        f_assigned_str = f"出發地點為:({f_assigned_x}, {f_assigned_y})"

    current_time = datetime.now(timezone.utc)
    start_time = current_time + timedelta(minutes=1)

    event = await guild.create_scheduled_event(
        name = f"空降活動-{real_end_time_str}",
        start_time = start_time,
        end_time = real_end_time,
        description = f"""目標座標:({xtar}, {ytar})
跳板座標:({xstp}, {ystp})
跳板類型:{stp_type_str}
空降抵達時間:{end_time.strftime("%H:%M")}
飛行類型:{fmode_str}
{f_assigned_str}""",
        entity_type = discord.EntityType.external,
        location = channel.name,
        privacy_level = discord.PrivacyLevel.guild_only
    )



#實際運行
@tree.command(name="airstrike", description = "執行空降")
async def airstrike(interaction: discord.Interaction):
    print("calling airstrike")
    user = interaction.user
    user_id = interaction.user.id
    name = user.nick or user.name

    #全域資料清空
    reset_user_data(user_id)

    await interaction.response.send_message(f"{name}指揮官，空降行動開始!")

    coor_info_button = Button(label = "開始輸入座標!", style = discord.ButtonStyle.blurple, custom_id = "coor_info", row = 0)
    Sametime_button = Button(label = "同時起飛(指定出發時間)", style = discord.ButtonStyle.blurple, custom_id = "sametime", row = 1)
    Sameplace_button = Button(label = "同地起飛(指定起點座標)", style = discord.ButtonStyle.blurple, custom_id = "sameplace", row = 1)

    view1 = View()
    view1.add_item(coor_info_button)
    view1.add_item(Sametime_button)
    view1.add_item(Sameplace_button)

    await interaction.followup.send("指揮官，要空降哪裡呢?\n請輸入座標後選擇模式:", view = view1, ephemeral = True)


@tree.command(name="joinairstrike", description = "加入空降行動")
async def joinairstrike(interaction: discord.Interaction):
    try:
        guild = interaction.guild
        user_id = interaction.user.id
        reset_user_data(user_id)
        await interaction.response.defer(ephemeral = True)

        events = await guild.fetch_scheduled_events()
        if not events:
            await interaction.followup.send("目前沒有任何空降活動", ephemeral=True)
            return

        event = events[0]
        desc = event.description or ""

        #print(f"活動名稱: {event.name}")
        #print(f"活動描述: {event.description}")
        #print(f"活動開始時間: {event.start_time}")
        #print(f"活動結束時間: {event.end_time}")


        if "目標座標" not in desc:
            await interaction.followup.send("活動描述格式不完整。", ephemeral=True)
            return

        target_match = re.search(r"目標座標:\((\d+),\s*(\d+)\)", desc)
        if target_match:
            xtar = int(target_match.group(1))
            ytar = int(target_match.group(2))

        step_match = re.search(r"跳板座標:\((\d+),\s*(\d+)\)", desc)
        if step_match:
            xstp = int(step_match.group(1))
            ystp = int(step_match.group(2))

        step_type_match = re.search(r"跳板類型:(\d+|哨站|平台)", desc)
        if step_type_match:
            stp_type_raw = step_type_match.group(1)
            if stp_type_raw == "1" or stp_type_raw == "哨站":
                stp_type = 1
            elif stp_type_raw == "2" or stp_type_raw == "平台":
                stp_type = 2

        fmode = None

        flight_type_match = re.search(r"飛行類型:(.+)", desc)
        if flight_type_match:
            flight_type = flight_type_match.group(1).strip()
            if flight_type == "同時起飛":
                fmode = 1
            elif flight_type == "同地起飛":
                fmode = 2

        if fmode == 1:
            dep_time_match = re.search(r"出發時間為:(\d{2}:\d{2})", desc)
            if dep_time_match:
                deptime_str = dep_time_match.group(1)
                local_dep_time = datetime.combine(date.today(), datetime.strptime(deptime_str, "%H:%M").time())
                utc_dep_time = local_dep_time.astimezone(timezone(timedelta(hours = 8)))

        elif fmode == 2:
            dep_place_match = re.search(r"出發地點為:\((\d+),\s*(\d+)\)", desc)
            if dep_place_match:
                xdep = int(dep_place_match.group(1))
                ydep = int(dep_place_match.group(2))

        arrive_time_match = re.search(r"空降抵達時間:(\d{2}:\d{2})", desc)
        if arrive_time_match:
            arrivetime_str = arrive_time_match.group(1)
            local_arrive_time = datetime.combine(date.today(), datetime.strptime(arrivetime_str, "%H:%M").time())
            utc_arrive_time = local_arrive_time.astimezone(timezone(timedelta(hours = 8)))

        #print(f"{xtar} {ytar} {xstp} {ystp} {stp_type} {fmode}")

        print("tag000")

        user_data[user_id]["coor_info"]["coor_tar_x"] = xtar
        user_data[user_id]["coor_info"]["coor_tar_y"] = ytar
        user_data[user_id]["coor_info"]["coor_step_x"] = xstp
        user_data[user_id]["coor_info"]["coor_step_y"] = ystp
        user_data[user_id]["coor_info"]["coor_steptype"] = stp_type
        if fmode == 1:
            user_data[user_id]["status"]["fmode"] = "sametime"
        elif fmode == 2:
            user_data[user_id]["status"]["fmode"] = "sameplace"

        print("tag001")

        if fmode == 1:
            user_data[user_id]["sametime_info"]["deptime"].append(utc_dep_time)
            user_data[user_id]["sametime_info"]["arrivetime"].append(utc_arrive_time)

        elif fmode == 2:
            user_data[user_id]["sameplace_info"]["arrivetime"].append(utc_arrive_time)
            user_data[user_id]["sameplace_info"]["coor_dep_x"] = xdep
            user_data[user_id]["sameplace_info"]["coor_dep_y"] = ydep

        print("tag002")

        await interaction.followup.send(f"正在加入:{event.name}", ephemeral=True)
        await Getjoinfspd(interaction)

        print("tag003")

        # 如果已經回應過一次，使用 followup 發送錯誤訊息
    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"錯誤：{e}", ephemeral=True)
        else:
            await interaction.followup.send(f"錯誤：{e}", ephemeral=True)






processing_users = set()

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data["custom_id"]
        user_id = interaction.user.id

        if custom_id == "coor_info":
            await interaction.response.send_modal(GetcoorinfoModal(user_id))

        elif custom_id == "sametime":
            await interaction.response.send_modal(SametimeinfoModal(user_id))

        elif custom_id == "sameplace":
            await interaction.response.send_modal(SameplaceinfoModal(user_id))

        elif custom_id == "start_calc":
            if user_id in processing_users:
                await interaction.response.send_message("資訊計算中，指揮官請稍候......", ephemeral = True)

            processing_users.add(user_id)
            await interaction.response.defer(ephemeral=True)
            result_text = calculate_airstrike(user_id)
            await interaction.followup.send(result_text, ephemeral=True)
            processing_users.remove(user_id)
            pack_button = Button(label = "整理結果並公開發表", style = discord.ButtonStyle.green, custom_id = "pack_result", row = 0)
            event_button = Button(label = "創建為伺服器活動", style = discord.ButtonStyle.green, custom_id = "create_event", row = 0)
            view3 = View()
            view3.add_item(pack_button)
            view3.add_item(event_button)
            await interaction.followup.send("指揮官，您還可以:", view = view3, ephemeral = True )

        elif custom_id == "pack_result":
            await interaction.response.send_modal(PackinfoModal(user = interaction.user, user_data = user_data))

        elif custom_id == "create_event":
            await create_event(interaction)
            await interaction.response.send_message("活動創立完成!")




if __name__ == "__main__":
    bot.run(token)