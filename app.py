import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os
import time

# 1. 配置 16 檔金融股
FIN_MAP = {
    '2801.TW': '彰銀', '2809.TW': '京城銀', '2812.TW': '台中銀', '2834.TW': '臺企銀',
    '2880.TW': '華南金', '2881.TW': '富邦金', '2882.TW': '國泰金', '2883.TW': '凱基金',
    '2884.TW': '玉山金', '2885.TW': '元大金', '2886.TW': '兆豐金', '2887.TW': '台新金',
    '2890.TW': '永豐金', '2891.TW': '中信金', '2892.TW': '第一金', '5880.TW': '合庫金'
}

# 網頁基礎設定
try:
    st.set_page_config(page_title="金融股殖利率監控", layout="wide")
except:
    pass

st.title("🏦 金融股五年平均「息+利」總殖利率監控 (6.5% 門檻)")

# 設定快取：1 小時內重複打開網頁不需要重新抓取，直接顯示結果
@st.cache_data(ttl=3600)
def get_data_65():
    results = []
    # 建立一個文字提示區域
    status_text = st.empty()
    
    for i, (code, name) in enumerate(FIN_MAP.items()):
        try:
            # 顯示目前抓取進度給使用者看 (反饋機制)
            status_text.text(f"⏳ 正在同步第 {i+1}/16 檔：{name} ({code})...")
            
            ticker = yf.Ticker(code)
            price = ticker.fast_info['last_price']
            actions = ticker.actions
            
            if not actions.empty:
                # 抓取最近 5 次現金股息
                div_series = actions[actions['Dividends'] > 0]['Dividends']
                avg_cash = div_series.tail(5).mean() if not div_series.empty else 0
                
                # 抓取最近 5 次股票股利 (還原台灣 1 元配股格式)
                split_series = actions[actions['Stock Splits'] > 0]['Stock Splits']
                avg_stock = (split_series.tail(5).mean() - 1) * 10 if not split_series.empty else 0
                
                total_yield = ((avg_cash + avg_stock) / price) * 100
                
                results.append({
                    "股票代號": code.replace('.TW', ''),
                    "中文名稱": name,
                    "目前股價": round(price, 2),
                    "五年平均現金": round(avg_cash, 2),
                    "五年平均配股": round(avg_stock, 2),
                    "總殖利率(%)": round(total_yield, 2)
                })
            # 每一檔抓完稍微停 0.3 秒，避免被 Yahoo 視為惡意攻擊
            time.sleep(0.3)
        except Exception as e:
            continue
            
    status_text.empty() # 抓完後清除提示文字
    return pd.DataFrame(results)

# 執行抓取
with st.spinner('數據計算中，請稍候...'):
    df = get_data_65()

# --- 顯示結果 ---
if not df.empty:
    st.write(f"✅ 數據更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 門檻設定為 4
    threshold = 4
    
    # 表格美化：高於 6.5% 的格子會變成粉紅色
    def highlight_target(val):
        return 'background-color: #FFCCCC' if val >= threshold else ''
    
    st.dataframe(
        df.style.map(highlight_target, subset=['總殖利率(%)']),
        use_container_width=True
    )
    
    # 找出達標股票
    target_stocks = df[df['總殖利率(%)'] >= threshold]
    
    if not target_stocks.empty:
        st.success(f"🔥 發現 {len(target_stocks)} 檔標的總殖利率超過 {threshold}%！")
    else:
        st.info(f"目前沒有標的高於 {threshold}%。")

    # --- GitHub Actions 自動發信 (背景執行) ---
    if os.getenv("GITHUB_ACTIONS") == "true" and not target_stocks.empty:
        user = os.getenv("MAIL_USER")
        password = os.getenv("MAIL_PASSWORD")
        to = os.getenv("MAIL_TO")
        
        if user and password:
            content = f"📢 金融股達標通知：\n\n{target_stocks.to_string()}\n\n計算公式：(5年平均現金+5年平均配股)/目前股價"
            msg = MIMEText(content)
            msg['Subject'] = f'【殖利率監控】{len(target_stocks)} 檔金融股已達標！'
            msg['From'] = user
            msg['To'] = to
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(user, password)
                server.send_message(msg)
else:
    st.error("連線超時或抓不到數據，請點擊網頁右上角選單選擇 'Clear cache' 後再試一次。")
