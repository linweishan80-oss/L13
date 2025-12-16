import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 常數設定 ---
DB_NAME = "data.db"
TABLE_NAME = "weather"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_DIR, DB_NAME)

def get_data_from_db():
    """從資料庫讀取資料並回傳 DataFrame"""
    if not os.path.exists(DB_PATH):
        st.error(f"錯誤：找不到資料庫檔案 '{DB_NAME}'。")
        st.info("請先執行 `python weather_crawler.py` 來產生資料庫。")
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    try:
        # 使用 SQL alias 讓欄位名稱更友善
        query = f"SELECT location_name as '地區', temperature as '溫度 (°C)', last_updated as '最後更新時間' FROM {TABLE_NAME}"
        df = pd.read_sql(query, conn)
    except pd.io.sql.DatabaseError:
        st.error("資料庫結構有誤或為空。請嘗試重新執行 `python weather_crawler.py`。")
        return pd.DataFrame()
    finally:
        conn.close()
        
    return df

# --- Streamlit App 介面 ---
st.set_page_config(page_title="台灣天氣資訊", page_icon="🇹🇼")

st.title("🌦️ 台灣各縣市即時溫度")
st.markdown("資料來源：中央氣象署開放資料平臺")

st.info("這份資料是從 `data.db` 資料庫讀取的。如需更新，請重新執行 `python weather_crawler.py`。")

# 讀取並顯示資料
weather_df = get_data_from_db()

if not weather_df.empty:
    st.header("🌡️ 溫度資料表")
    st.dataframe(
        weather_df,
        use_container_width=True,
        hide_index=True,
    )