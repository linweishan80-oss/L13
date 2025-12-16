import requests
import sqlite3
import os
import re
import json

# --- 常數設定 ---
# 使用使用者提供的 API 金鑰和資料集
API_KEY = "CWA-1FFDDAEC-161F-46A3-BE71-93C32C52829F"
API_URL = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-A0010-001?Authorization={API_KEY}&downloadType=WEB&format=JSON"
DB_NAME = "data.db"
TABLE_NAME = "weather"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, DB_NAME)

def init_db():
    """初始化資料庫，刪除舊表並建立新表"""
    print("正在初始化資料庫...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    cursor.execute(f"""
    CREATE TABLE {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT,
        min_temp REAL,
        max_temp REAL,
        description TEXT
    )
    """)
    conn.commit()
    conn.close()
    print("資料庫初始化完成。")

def fetch_and_store_data():
    """從 API 下載資料並存入資料庫"""
    print(f"正在從 CWA 開放資料平台下載資料 (F-A0010-001)...")
    try:
        # 警告：在生產環境中不建議禁用 SSL 驗證。此處為了解決本地憑證問題而使用。
        # 禁用 SSL 驗證會產生警告，以下程式碼可以將其隱藏
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        # 禁用 SSL 憑證驗證 (verify=False)
        response = requests.get(API_URL, verify=False)
        response.raise_for_status()  # 如果請求失敗 (如 404, 500)，會拋出異常
        data = response.json()

        # 根據新的 API 結構，更新資料路徑
        locations = data['cwaopendata']['resources']['resource']['data']['agrWeatherForecasts']['weatherForecasts']['location']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        print("正在解析資料並存入資料庫...")
        for loc in locations:
            location_name = loc.get('locationName', '未知地區')
            
            try:
                # 新結構直接提供每日預報，我們取第一筆 (today)
                weather_elements = loc['weatherElements']
                description = weather_elements['Wx']['daily'][0]['weather']
                min_temp = weather_elements['MinT']['daily'][0]['temperature']
                max_temp = weather_elements['MaxT']['daily'][0]['temperature']

                # 插入資料庫
                cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (location, min_temp, max_temp, description)
                VALUES (?, ?, ?, ?)
                """, (location_name, float(min_temp), float(max_temp), description))

            except (KeyError, IndexError) as e:
                print(f"警告：在 '{location_name}' 解析資料時發生錯誤，已跳過。錯誤：{e}")
                continue
        
        conn.commit()
        conn.close()
        print("資料成功存入資料庫！")

    except requests.exceptions.RequestException as e:
        print(f"網路錯誤：{e}")
    except (KeyError, TypeError, IndexError) as e:
        print(f"解析資料錯誤，請檢查 JSON 結構：{e}")
        # 如果解析出錯，印出原始資料以供偵錯
        print("收到的原始資料：", json.dumps(data, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"發生未預期錯誤：{e}")

if __name__ == "__main__":
    init_db()
    fetch_and_store_data()