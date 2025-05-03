from cgi import print_form
from lib2to3.fixes.fix_metaclass import find_metas
from operator import truediv

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
                view3 = View()
                view3.add_item(start_button)
                await interaction.followup.send("資料輸入完成!", view = view3, ephmeral = True)
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
            arrivetime = datetime.strptime(deptime_str, "%H:%M")

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
                view3 = View()
                view3.add_item(start_button)
                await interaction.followup.send("資料輸入完成!", view = view3, ephemeral = True)
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
                view3 = View()
                view3.add_item(start_button)
                await interaction.followup.send("資料輸入完成!", view = view3, ephemeral = True)
            else:
                interaction.followup.send("請繼續填寫座標資訊!", ephemeral = True)

        except Exception as e:
            await interaction.response.send_message(
                f"資料格式錯誤，請確認時間格式為HH:MM(英文逗號)，航速為整數。\n錯誤訊息:{str(e)}",
                ephemeral=True
            )

#時間轉換
def deltaformatted(tdelta):
    total_seconds = int(tdelta.total_seconds())
    hours = total_seconds //3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    formatted = f"{hours:02}:{minutes:02}:{seconds:02}"
    return formatted




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
        ys1 = round(ystp + dist)
        xs2 = xstp
        ys2 = round(ystp - dist)
    elif lne == 2:
        A = 1 + slp ** 2
        B = 2 * (slp * (inter - ystp) - xstp)
        C = (inter - ystp) ** 2 + xstp ** 2 - dist ** 2
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
        print(deptime, arrivetime, fspd, xstp, ystp, lne, slp, inter, xtar, ytar, xexact, yexact)
        status, xs, ys, dist, travel_time = fmode1(deptime, arrivetime, fspd, xstp, ystp, lne, slp, inter, xtar, ytar, xexact, yexact, tolerance=1e-6)
        travel_time_formatted = deltaformatted(travel_time)
    elif fmode == "sameplace":
        arrivetime = user_data[user_id]["sameplace_info"]["arrivetime"][0]
        fspd = user_data[user_id]["sameplace_info"]["fspd"]
        xdep = user_data[user_id]["sameplace_info"]["coor_dep_x"]
        ydep = user_data[user_id]["sameplace_info"]["coor_dep_y"]
        status, xs, ys, estdeptime, esttime, timecorr, dist = fmode2(xexact, yexact, xdep, ydep, xtar, ytar, slp, inter, arrivetime, fspd)
        esttime_formatted = deltaformatted(esttime)
        timecorr_formatted = deltaformatted(timecorr)

    if fmode == "sametime":
        result_text = (
            f"📍你的指定空降座標為:({xtar}, {ytar})\n"
            f"🛸你的指定跳板座標為:({xstp}, {ystp})，類型為:{step_type_o}\n"
            f"🚀你預定於{deptime.strftime("%H:%M")}出發，經過{dist}JM，並於({arrivetime.strftime("%H:%M")})抵達!\n"
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
        elif status == 2:
            result_text = (
                f"📍你的指定空降座標為:({xtar}, {ytar})\n"
                f"🛸你的指定跳板座標為:({xstp}, {ystp})，類型為:{step_type_o}\n"
                f"⏰你應該於({estdeptime.strftime("%H:%M:%S")})由({xdep},{ydep})出發，經過{dist}JM\n"
                f"⏱花費{esttime_formatted}，並在({arrivetime.strftime('%H:%M')})抵達!"
            )
        user_data[user_id]["status"]["result"] = result_text
        return result_text





#實際運行
@tree.command(name="airstrike", description = "執行空降")
async def airstrike(interaction: discord.Interaction):
    print("calling airstrike")
    user = interaction.user
    user_id = interaction.user.id
    name = user.nick or user.name

    #全域資料清空
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


    await interaction.response.send_message(f"{name}指揮官，空降行動開始!")

    coor_info_button = Button(label = "開始輸入座標!", style = discord.ButtonStyle.blurple, custom_id = "coor_info")
    Sametime_button = Button(label = "同時起飛(指定出發時間)", style = discord.ButtonStyle.blurple, custom_id = "sametime")
    Sameplace_button = Button(label = "同地起飛(指定起點座標)", style = discord.ButtonStyle.blurple, custom_id = "sameplace")

    view1 = View()
    view1.add_item(coor_info_button)
    view2 = View()
    view2.add_item(Sametime_button)
    view2.add_item(Sameplace_button)

    await interaction.followup.send("指揮官，要空降哪裡呢?", view = view1, ephemeral = True)
    await interaction.followup.send("請選擇空降方式：", view = view2, ephemeral = True)


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

        #elif custom_id == "create_event"




if __name__ == "__main__":
    bot.run("MTM2Njc3MzQyMzAwMjYxNTg0OA.GKJvaS.tDKpssinX_pPlwsp_aWflcxrzDhQrWQ3K953Ro")