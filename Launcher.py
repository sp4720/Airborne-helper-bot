import os
import requests
import shutil
import subprocess
import time

GITHUB_API = "https://api.github.com/repos/sp4720/Airborne-helper-bot/releases/latest"
BOT_EXE = "bot.exe"
TMP_EXE = "bot_new.exe"
VERSION_FILE = "version.txt"

def get_local_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()
    return "0.0.0"

def get_latest_release_info():
    response = requests.get(GITHUB_API)
    #print("GITHUB回應", response.text)
    if response.status_code == 200:
        try:
            data = response.json()
            version = data["tag_name"]
            download_url = None
            for asset in data["assets"]:
                if asset["name"] == BOT_EXE:
                    download_url = asset["browser_download_url"]
            return version, download_url
        except Exception as e:
            print("解析Json失敗", e)
            return None, None
    else:
        print(f"無法取得Github release (狀態碼{response.status_code})")
        return None, None

def  download_file(url, filename):
    with requests.get(url, stream = True) as r:
        with open(filename, "wb") as f:
            shutil.copyfileobj(r.raw, f)

def replace_bot():
    if os.path.exists(BOT_EXE):
        os.remove(BOT_EXE)
        os.rename(TMP_EXE, BOT_EXE)

def save_version(version):
    with open(VERSION_FILE, "w") as f:
        f.write(version)

def main():
    print("版本檢查中......")

    local_version = get_local_version()
    latest_version, download_url = get_latest_release_info()

    if not latest_version:
        print("無法取得最新版本資訊，掠過更新。")
    elif local_version == latest_version:
        print(f"當前為最新版本{local_version}，無須更新。")
    else:
        print(f"發現更新版本{latest_version}，當前版本為{local_version}")
        print("下載中......")
        download_file(download_url, TMP_EXE)
        print("替換舊檔中......")
        replace_bot()
        save_version(latest_version)

    print("啟動空降小幫手......")
    subprocess.Popen([BOT_EXE])
    time.sleep(2)

if __name__ ==  "__main__":
    main()

