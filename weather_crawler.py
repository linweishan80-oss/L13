import requests
import sqlite3
import os

# --- 常數設定 ---
API_KEY = "CWA-7CBFEDE7-EE71-435C-A4BF-4CB481238FB4"
# 使用者要求的 API (一般天氣預報-一週天氣預報)
API_URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-A0010-001?Authorization={API_KEY}&format=JSON"
DB_NAME = "data.db"
TABLE_NAME = "weather"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, DB_NAME)

def init_db():
    """初始化資料庫，建立符合要求的資料表"""
    print("正在初始化資料庫...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 根據使用者要求建立資料表
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
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
            return
        
        locations = data['records']['location']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 清空舊資料，以確保每次都是最新的預報
        cursor.execute(f"DELETE FROM {TABLE_NAME}")
        print("正在更新資料庫...")

        for loc in locations:
            location_name = loc['locationName']
            weather_elements = loc['weatherElement']
            
            # 從 weatherElement 中提取所需資料
            min_temp = next((elem['time'][0]['parameter']['parameterName'] for elem in weather_elements if elem['elementName'] == 'MinT'), None)
            max_temp = next((elem['time'][0]['parameter']['parameterName'] for elem in weather_elements if elem['elementName'] == 'MaxT'), None)
            description = next((elem['time'][0]['parameter']['parameterName'] for elem in weather_elements if elem['elementName'] == 'Wx'), None)

            if all((min_temp, max_temp, description)):
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