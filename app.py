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

def get_real_data():
    results = []
    for code, name in FIN_MAP.items():
        try:
            ticker = yf.Ticker(code)
            price = ticker.fast_info['last_price']
            actions = ticker.actions
            
            if not actions.empty:
                # 1. 抓取現金股息 (五年平均)
                divs = actions[actions['Dividends'] > 0]['Dividends'].tail(5)
                avg_cash = divs.mean() if not divs.empty else 0
                
                # 2. 抓取股票股利 (將 Split 1.1 這種紀錄還原成台灣的 1 元配股)
                splits = actions[actions['Stock Splits'] > 0]['Stock Splits'].tail(5)
                avg_stock_val = (splits.mean() - 1) * 10 if not splits.empty else 0
                
                # 3. 計算總殖利率
                total_yield = ((avg_cash + avg_stock_val) / price) * 100
                
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

df = get_real_data()

# --- 網頁顯示邏輯 ---
if 'st' in globals() and not df.empty:
    df.index = df.index + 1
    st.write(f"數據最後更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.dataframe(
        df.style.map(lambda x: 'background-color: #FFCCCC' if x >= 6.5 else '', subset=['總殖利率(%)']),
        use_container_width=True
    )

# --- 自動發信邏輯 (僅當達標且在 GitHub Actions 執行時) ---
target_stocks = df[df['總殖利率(%)'] >= 4]

if os.getenv("GITHUB_ACTIONS") == "true" and not target_stocks.empty:
    user = os.getenv("MAIL_USER")
    password = os.getenv("MAIL_PASSWORD")
    to = os.getenv("MAIL_TO")
    
    if user and password:
        content = f"📢 偵測到總殖利率達標標的：\n\n{target_stocks.to_string()}\n\n計算方式：(5年平均現金 + 5年平均配股) / 即時股價"
        msg = MIMEText(content)
        msg['Subject'] = f'【殖利率達標】共有 {len(target_stocks)} 檔金融股超過 4%！'
        msg['From'] = user
        msg['To'] = to
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
            server.send_message(msg)
