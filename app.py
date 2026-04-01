import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# 1. 初始化資料庫 (免帳號即可抓取基本資料)
dl = DataLoader()

FIN_MAP = {
    '2801': '彰銀', '2809': '京城銀', '2812': '台中銀', '2834': '臺企銀',
    '2880': '華南金', '2881': '富邦金', '2882': '國泰金', '2883': '凱基金',
    '2884': '玉山金', '2885': '元大金', '2886': '兆豐金', '2887': '台新金',
    '2890': '永豐金', '2891': '中信金', '2892': '第一金', '5880': '合庫金'
}

st.set_page_config(page_title="台股金融股監控", layout="wide")
st.title("🏦 台股金融股五年「息+利」總殖利率監控")

@st.cache_data(ttl=3600) # 快取一小時，避免重複抓取被封鎖
def get_fin_data():
    results = []
    this_year = datetime.now().year
    
    for code, name in FIN_MAP.items():
        try:
            # 抓取股價 (今日)
            df_price = dl.taiwan_stock_daily(stock_id=code, start_date=f"{this_year}-01-01")
            current_price = df_price['close'].iloc[-1]
            
            # 抓取股利 (過去五年)
            df_div = dl.taiwan_stock_dividend(stock_id=code, start_date=f"{this_year-6}-01-01")
            
            # 過濾並計算 (CashDividend 現金股息 + StockDividend 股票股利)
            # 僅取最近 5 年的紀錄
            recent_divs = df_div.tail(5)
            avg_cash = recent_divs['CashDividend'].mean()
            avg_stock = recent_divs['StockDividend'].mean()
            avg_total = avg_cash + avg_stock
            
            total_yield = (avg_total / current_price) * 100
            
            results.append({
                "股票代號": code,
                "中文名稱": name,
                "目前股價": round(current_price, 1),
                "五年平均總股利(息+利)": round(avg_total, 1),
                "平均總殖利率(%)": round(total_yield, 1)
            })
        except:
            continue
    return pd.DataFrame(results)

df = get_fin_data()

# 顯示與通知邏輯 (與之前相同)
if not df.empty:
    df.index = df.index + 1
    st.dataframe(df.style.map(lambda x: 'background-color: #FFCCCC' if x >= 6.5 else '', subset=['平均總殖利率(%)']))
    
    # 這裡放 Email 通知按鈕邏輯... (同前一版)
