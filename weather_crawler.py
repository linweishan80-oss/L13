import requests
import sqlite3
import os

# --- 常數設定 ---
API_KEY = "CWA-7CBFEDE7-EE71-435C-A4BF-4CB481238FB4"
API_URL = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001?Authorization={API_KEY}"
DB_NAME = "data.db"
TABLE_NAME = "weather"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, DB_NAME)

def init_db():
    """初始化資料庫，建立資料表"""
    print("正在初始化資料庫...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_name TEXT NOT NULL UNIQUE,
        temperature REAL NOT NULL,
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()
    print("資料庫初始化完成。")

def fetch_and_store_data():
    """從 API 下載資料並存入資料庫"""
    print("正在從中央氣象署下載資料...")
    try:
        response = requests.get(API_URL, verify=False)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            print("錯誤：API 回應失敗。")
            return
        
        locations = data['records']['Station']
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 清空舊資料
        cursor.execute(f"DELETE FROM {TABLE_NAME}")
        print("正在更新資料庫...")

        for loc in locations:
            # 防護措施：確保測站資料中存在 'weatherElement'
            if 'weatherElement' in loc:
                temp_element = next((elem for elem in loc['weatherElement'] if elem['elementName'] == 'TEMP'), None)
                
                if temp_element:
                    temperature = float(temp_element['elementValue']['value'])
                    # 過濾無效的溫度值
                    if temperature < -90:
                        continue
                    
                    location_name = loc['locationName']
                    
                    cursor.execute(f"""
                    INSERT OR IGNORE INTO {TABLE_NAME} (location_name, temperature)
                    VALUES (?, ?)
                    """, (location_name, temperature))

        conn.commit()
        conn.close()
        print("資料成功存入資料庫！")

    except requests.exceptions.RequestException as e:
        print(f"網路錯誤：{e}")
    except (KeyError, TypeError) as e:
        print(f"解析資料錯誤：{e}")
    except Exception as e:
        print(f"發生未預期錯誤：{e}")

if __name__ == "__main__":
    init_db()
    fetch_and_store_data()
