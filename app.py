import streamlit as st
import sqlite3
import pandas as pd
import os
import subprocess
import sys

# --- 常數設定 ---
DB_NAME = "data.db"
TABLE_NAME = "weather"
CRAWLER_SCRIPT = "weather_crawler.py"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, DB_NAME)

def get_data_from_db():
    """從資料庫讀取資料並回傳 DataFrame"""
    if not os.path.exists(DB_PATH):
        st.error(f"錯誤：找不到資料庫檔案 '{DB_NAME}'。")
        st.info(f"請點擊下方的「更新天氣資料」按鈕來產生資料庫。")
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    try:
        # 根據新的 schema 查詢資料，並使用別名
        query = f"SELECT location as '地區', min_temp as '最低溫 (°C)', max_temp as '最高溫 (°C)', description as '天氣狀況' FROM {TABLE_NAME}"
        df = pd.read_sql(query, conn)
        if df.empty:
            st.warning("資料庫是空的。請點擊按鈕更新資料。")
    except Exception as e:
        st.error(f"讀取資料庫時發生錯誤：{e}")
        st.info(f"請嘗試點擊下方的「更新天氣資料」按鈕。")
        return pd.DataFrame()
    finally:
        conn.close()
        
    return df

def run_crawler():
    """執行爬蟲腳本來更新資料"""
    st.info("正在執行爬蟲腳本 `weather_crawler.py`...")
    with st.spinner('正在從中央氣象署獲取最新資料，請稍候...'):
        try:
            # 使用與 Streamlit 相同環境的 Python 解譯器來執行爬蟲
            result = subprocess.run([sys.executable, CRAWLER_SCRIPT], capture_output=True, text=True, check=True)
            st.success("資料更新成功！")
            st.code(result.stdout)
        except subprocess.CalledProcessError as e:
            st.error("更新資料失敗！爬蟲腳本執行出錯。")
            st.code(e.stderr)
        except FileNotFoundError:
            st.error(f"錯誤：找不到爬蟲腳本 '{CRAWLER_SCRIPT}'。")


# --- Streamlit App 介面 ---
st.set_page_config(page_title="台灣天氣預報", page_icon="🌦️")

st.title("🌦️ 台灣一週天氣預報")
st.markdown("資料來源：[中央氣象署開放資料平臺](https://opendata.cwa.gov.tw/dataset/forecast/F-A0010-001)")

# 更新資料的按鈕
if st.button('更新天氣資料'):
    run_crawler()

# 讀取並顯示資料
weather_df = get_data_from_db()

if not weather_df.empty:
    st.header("📝 天氣預報總覽")
    st.dataframe(
        weather_df,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.markdown("---")
    st.write("目前沒有資料可顯示。")

st.info("此應用程式顯示從 `data.db` 資料庫讀取的天氣預報。點擊按鈕可獲取最新資料。")
