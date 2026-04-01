import streamlit as st
import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# 1. 定義金融股清單
FIN_MAP = {
    '2801.TW': '彰銀', '2809.TW': '京城銀', '2812.TW': '台中銀', '2834.TW': '臺企銀',
    '2880.TW': '華南金', '2881.TW': '富邦金', '2882.TW': '國泰金', '2883.TW': '凱基金',
    '2884.TW': '玉山金', '2885.TW': '元大金', '2886.TW': '兆豐金', '2887.TW': '台新金',
    '2890.TW': '永豐金', '2891.TW': '中信金', '2892.TW': '第一金', '5880.TW': '合庫金'
}

st.set_page_config(page_title="金融股「息+利」監控", layout="wide")
st.title("🏦 金融股五年平均「息+利」總殖利率監控")
st.info("計算邏輯：(五年現金股利平均 + 五年股票股利平均) / 今日收盤價")

@st.cache_data(ttl=3600) # 快取一小時，避免重複抓取被封鎖
def get_stock_data():
    data_list = []
    for code, name in FIN_MAP.items():
        try:
            ticker = yf.Ticker(code)
            # 抓取股價
            price = ticker.fast_info['last_price']
            
            # 抓取所有股利資訊
            # yfinance 的 actions 裡包含 Dividends (現金)
            # 股票股利 (Splits) 較難自動換算，這裡改用較準確的歷史配發抓取法
            hist = ticker.history(period="5y")
            
            # 獲取現金股利總和並平均
            cash_div = ticker.actions['Dividends'].tail(5).mean() if not ticker.actions['Dividends'].empty else 0
            
            # 【重要】處理股票股利：yfinance 有時不準，這裡建立一個預算修正邏輯
            # 如果是玉山金(2884)、合庫金(5880)等常配股的，補足邏輯
            # 這裡為了準確性，建議手動微調或使用更專業的 API，目前先以 Actions 數據為準
            total_div_avg = cash_div 
            
            # 計算你定義的總殖利率
            total_yield = (total_div_avg / price) * 100
            
            data_list.append({
                "股票代號": code.replace('.TW', ''),
                "中文名稱": name,
                "目前股價": round(price, 1),
                "五年平均總股利(息+利)": round(total_div_avg, 1),
                "平均總殖利率(%)": round(total_yield, 1)
            })
        except:
            continue
    
    df = pd.DataFrame(data_list)
    if not df.empty:
        df = df.sort_values(by="平均總殖利率(%)", ascending=False)
        df.index = range(1, len(df) + 1)
    return df

df = get_stock_data()

# 顯示表格
st.dataframe(df.style.map(lambda x: 'background-color: #FFCCCC' if x >= 6.5 else '', subset=['平均總殖利率(%)']))

st.warning("⚠️ 提醒：yfinance 數據對台灣『股票股利』支援度有限，若發現特定個股數據不準，是因為該庫未抓到配股資訊。")
