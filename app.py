import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os

# 1. 配置金融股清單
FIN_MAP = {
    '2801.TW': '彰銀', '2809.TW': '京城銀', '2812.TW': '台中銀', '2834.TW': '臺企銀',
    '2880.TW': '華南金', '2881.TW': '富邦金', '2882.TW': '國泰金', '2883.TW': '凱基金',
    '2884.TW': '玉山金', '2885.TW': '元大金', '2886.TW': '兆豐金', '2887.TW': '台新金',
    '2890.TW': '永豐金', '2891.TW': '中信金', '2892.TW': '第一金', '5880.TW': '合庫金'
}

# 網頁基本設定 (僅在 Streamlit 執行時有效)
try:
    st.set_page_config(page_title="金融股殖利率監控", layout="wide")
    st.title("🏦 金融股五年平均「息+利」總殖利率監控")
except:
    pass # 讓 GitHub Actions 也能執行

def get_data():
    results = []
    for code, name in FIN_MAP.items():
        try:
            ticker = yf.Ticker(code)
            price = ticker.fast_info['last_price']
            div_history = ticker.actions['Dividends']
            
            if len(div_history) >= 5:
                avg_div = div_history.tail(5).mean()
                total_yield = (avg_div / price) * 100
                results.append({
                    "股票代號": code.replace('.TW', ''),
                    "中文名稱": name,
                    "目前股價": round(price, 1),
                    "五年平均總股利": round(avg_div, 2),
                    "平均總殖利率(%)": round(total_yield, 2)
                })
        except:
            continue
    return pd.DataFrame(results)

# 執行抓取
df = get_data()

# --- 邏輯 A: 網頁顯示 (Streamlit) ---
if 'st' in globals() and not df.empty:
    df.index = df.index + 1
    def make_red(val):
        return 'background-color: #FFCCCC' if val >= 6.5 else ''
    st.dataframe(df.style.map(make_red, subset=['平均總殖利率(%)']), use_container_width=True)

# --- 邏輯 B: 自動通知 (GitHub Actions 或手動點擊) ---
target_stocks = df[df['平均總殖利率(%)'] >= 6.5]

def send_email(target_df):
    # 優先嘗試從 GitHub Secrets 讀取，若無則從 Streamlit Secrets 讀取
    user = os.getenv("MAIL_USER") or st.secrets["email"]["user"]
    password = os.getenv("MAIL_PASSWORD") or st.secrets["email"]["password"]
    to = os.getenv("MAIL_TO") or st.secrets["email"]["to"]
    
    if user and password:
        content = f"📢 偵測到高殖利率標的：\n\n{target_df.to_string()}\n\n時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
        msg = MIMEText(content)
        msg['Subject'] = f'【台股通知】{len(target_df)} 檔金融股達標！'
        msg['From'] = user
        msg['To'] = to
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(user, password)
            server.send_message(msg)
        return True
    return False

# 如果是在 GitHub Actions 執行環境，且有達標標的，則直接發信
if os.getenv("GITHUB_ACTIONS") == "true" and not target_stocks.empty:
    send_email(target_stocks)

# 網頁上的手動測試按鈕
if not target_stocks.empty and 'st' in globals():
    if st.button("發送測試 Email 通知"):
        if send_email(target_stocks):
            st.success("Email 已成功發送！")
