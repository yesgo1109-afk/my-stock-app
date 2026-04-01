import streamlit as st
import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# 1. 設定金融股清單 (可自行增加代號)
FIN_STOCKS = [
    '2881.TW', '2882.TW', '2884.TW', '2886.TW', '2891.TW', 
    '2892.TW', '5880.TW', '2880.TW', '2885.TW', '2887.TW'
]

st.set_page_config(page_title="金融股殖利率監控", layout="wide")
st.title("🏦 金融股五年平均殖利率監控系統")
st.write(f"更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def get_stock_data():
    data_list = []
    for code in FIN_STOCKS:
        try:
            ticker = yf.Ticker(code)
            # 獲取今日收盤價
            price = ticker.fast_info['last_price']
            # 獲取股利歷史 (yfinance 的 Dividends 已包含現金與股票股利總和)
            divs = ticker.actions['Dividends']
            # 取最近五年的平均值 (大數法則)
            avg_div = divs.tail(5).mean()
            # 計算殖利率
            yield_rate = (avg_div / price) * 100
            
            data_list.append({
                "股票代號": code,
                "目前股價": round(price, 2),
                "五年平均股利": round(avg_div, 2),
                "平均殖利率(%)": round(yield_rate, 2)
            })
        except:
            continue
    return pd.DataFrame(data_list)

# 執行計算
df = get_stock_data()

# 2. 網頁顯示與標示
def highlight_yield(val):
    color = 'background-color: #FFCCCC' if val >= 6.5 else ''
    return color

st.subheader("即時監控列表 (殖利率 > 6.5% 將以紅色標示)")
st.dataframe(df.style.applymap(highlight_yield, subset=['平均殖利率(%)']))

# 3. Email 通知邏輯 (僅在有符合標的時執行)
target_stocks = df[df['平均殖利率(%)'] >= 6.5]

if not target_stocks.empty:
    st.success(f"發現 {len(target_stocks)} 個符合條件的標的！")
    
    # 這裡可以加入發送 Email 的按鈕或設定排程自動執行
    if st.button("手動測試發送 Email 通知"):
        try:
            content = "符合 6.5% 殖利率標的：\n\n" + target_stocks.to_string(index=False)
            msg = MIMEText(content)
            msg['Subject'] = '【台股通知】高殖利率金融股提醒'
            msg['From'] = '你的Gmail帳號@gmail.com'
            msg['To'] = '收件人Email@gmail.com'
            
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login('你的Gmail帳號', '你的16位數應用程式密碼')
                server.send_message(msg)
            st.info("Email 已成功發送！")
        except Exception as e:
            st.error(f"發送失敗：{e}")