import requests
import sqlite3
import os

# --- 常數設定 ---
API_KEY = "CWA-7CBFEDE7-EE71-435C-A4BF-4CB481238FB4"
# 改用新的 API 端點 (鄉鎮天氣預報)
API_URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091?Authorization={API_KEY}&format=JSON"
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
    print("正在從中央氣象署下載天氣預報資料...")
    try:
        # 禁用 SSL 憑證驗證
        response = requests.get(API_URL, verify=False)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            print("錯誤：API 回應失敗。")
            print("收到的原始資料：", data)
            return

        # --- 偵錯步驟：印出收到的完整資料 ---
        import json
        print("--- API 回傳的原始資料 ---")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("--- 偵錯結束 ---")
        # --- 偵錯步驟結束 ---
        
        # CWA API 可能有兩種結構，增加彈性以應對
        try:
            # 結構 1: records -> locations -> location
            locations = data['records']['locations'][0]['location']
        except KeyError:
            # 結構 2: records -> location
            locations = data['records']['location']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # init_db 已經 drop 過 table，這裡可以不用 delete
        print("正在更新資料庫...")

        for loc in locations:
            location_name = loc['locationName']
            weather_elements = loc['weatherElement']
            
            # 根據新的 JSON 結構提取資料
            # 我們取第一個時間段 (time[0]) 的預報
            wx_element = next((elem for elem in weather_elements if elem['elementName'] == 'Wx'), None)
            min_t_element = next((elem for elem in weather_elements if elem['elementName'] == 'MinT'), None)
            max_t_element = next((elem for elem in weather_elements if elem['elementName'] == 'MaxT'), None)

            if all((wx_element, min_t_element, max_t_element)):
                description = wx_element['time'][0]['elementValue'][0]['value']
                min_temp = min_t_element['time'][0]['elementValue'][0]['value']
                max_temp = max_t_element['time'][0]['elementValue'][0]['value']

                cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (location, min_temp, max_temp, description)
                VALUES (?, ?, ?, ?)
                """, (location_name, float(min_temp), float(max_temp), description))

        conn.commit()
        conn.close()
        print("資料成功存入資料庫！")

    except requests.exceptions.RequestException as e:
        print(f"網路錯誤：{e}")
    except (KeyError, TypeError, IndexError) as e:
        print(f"解析資料錯誤，請檢查 JSON 結構：{e}")
    except Exception as e:
        print(f"發生未預期錯誤：{e}")

if __name__ == "__main__":
    # 執行前先關閉 requests 的 InsecureRequestWarning 警告
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    
    init_db()
    fetch_and_store_data()
