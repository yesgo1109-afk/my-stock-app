import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os

# 配置金融股清單
FIN_MAP = {
    '2801.TW': '彰銀', '2809.TW': '京城銀', '2812.TW': '台中銀', '2834.TW': '臺企銀',
    '2880.TW': '華南金', '2881.TW': '富邦金', '2882.TW': '國泰金', '2883.TW': '凱基金',
    '2884.TW': '玉山金', '2885.TW': '元大金', '2886.TW': '兆豐金', '2887.TW': '台新金',
    '2890.TW': '永豐金', '2891.TW': '中信金', '2892.TW': '第一金', '5880.TW': '合庫金'
}

try:
    st.set_page_config(page_title="金融股殖利率監控", layout="wide")
    st.title("🏦 金融股五年平均「息+利」總殖利率監控")
except:
    pass

@st.cache_data(ttl=3600)
def get_auto_split_data():
    results = []
    for code, name in FIN_MAP.items():
        try:
            ticker = yf.Ticker(code)
            # 抓取即時股價
            price = ticker.fast_info['last_price']
            
            # 獲取所有除權息動作
            actions = ticker.actions
            if actions.empty:
                continue
                
            # 分離現金與股票
            # yfinance 中，Stock Splits 通常代表配股比例
            # Dividends 代表現金股利
            divs = actions[actions['Dividends'] > 0]['Dividends'].tail(5)
            splits = actions[actions['Stock Splits'] > 0]['Stock Splits'].tail(5)
            
            # 計算五年平均 (如果該股不配股，則補 0)
            avg_cash = divs.mean() if not divs.empty else 0
            
            # 台灣配股轉換邏輯：yfinance 的 Split 1.1 代表配 1 元股票 (10%)
            # 我們將其轉換回台灣人習慣的「每股配幾元」
            avg_stock_val = 0
            if not splits.empty:
                # 假設配股是以 10 元面額計，1.05 代表配 0.5 元股票
                avg_stock_val = (splits.mean() - 1) * 10 
            
            total_div = avg_cash + avg_stock_val
            total_yield = (total_div / price) * 100
            
            results.append({
                "股票代號": code.replace('.TW', ''),
                "中文名稱": name,
                "目前股價": round(price, 1),
                "五年平均股息(現金)": round(avg_cash, 2),
                "五年平均股利(股票)": round(avg_stock_val, 2),
                "總殖利率(%)": round(total_yield, 2)
            })
        except:
            continue
    return pd.DataFrame(results)

df = get_auto_split_data()

# --- 顯示介面 ---
if 'st' in globals() and not df.empty:
    df.index = df.index + 1
    st.write(f"數據自動解析時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 呈現表格並標色
    st.dataframe(
        df.style.map(lambda x: 'background-color: #FFCCCC' if x >= 6.5 else '', subset=['總殖利率(%)']),
        use_container_width=True
    )

# --- 自動通知邏輯 (GitHub Actions) ---
target_stocks = df[df['總殖利率(%)'] >= 6.5]

def send_email(target_df):
    user = os.getenv("MAIL_USER")
    password = os.getenv("MAIL_PASSWORD")
    to = os.getenv("MAIL_TO")
    
    if user and password:
        content = f"📢 偵測到總殖利率達標標的：\n\n{target_df.to_string()}"
        msg = MIMEText(content)
        msg['Subject'] = f'【理財通知】{len(target_df)} 檔金融股殖利率達標！'
        msg['From'] = user
        msg['To'] = to
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
            server.send_message(msg)
        return True
    return False

if os.getenv("GITHUB_ACTIONS") == "true" and not target_stocks.empty:
    send_email(target_stocks)
