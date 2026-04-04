import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os
import time

# 1. 配置 15 檔金融股
FIN_MAP = {
    '2801.TW': '彰銀', '2812.TW': '台中銀', '2834.TW': '臺企銀',
    '2880.TW': '華南金', '2881.TW': '富邦金', '2882.TW': '國泰金', '2883.TW': '凱基金',
    '2884.TW': '玉山金', '2885.TW': '元大金', '2886.TW': '兆豐金', '2887.TW': '台新金',
    '2890.TW': '永豐金', '2891.TW': '中信金', '2892.TW': '第一金', '5880.TW': '合庫金'
}

# 網頁基礎設定
try:
    st.set_page_config(page_title="金融股殖利率監控", layout="wide")
except:
    pass

st.title("🏦 金融股五年平均「息+利」總殖利率監控")

# 設定快取：1 小時
@st.cache_data(ttl=3600)
def get_data_65():
    results = []
    status_text = st.empty()
    
    for i, (code, name) in enumerate(FIN_MAP.items()):
        try:
            status_text.text(f"⏳ 正在同步第 {i+1}/15 檔：{name} ({code})...")
            ticker = yf.Ticker(code)
            price = ticker.fast_info['last_price']
            actions = ticker.actions
            
            if not actions.empty:
                div_series = actions[actions['Dividends'] > 0]['Dividends']
                avg_cash = div_series.tail(5).mean() if not div_series.empty else 0
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
            time.sleep(0.3)
        except Exception:
            continue
            
    status_text.empty()
    return pd.DataFrame(results)

# 執行數據抓取
df = get_data_65()

# 設定門檻
threshold = 5.5

# --- 1. 網頁顯示邏輯 ---
if not df.empty:
    st.write(f"✅ 數據更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 排序從 1 開始
    df_display = df.copy()
    df_display.index = range(1, len(df_display) + 1)

    # 數值格式化：小數點後兩位
    format_dict = {
        "目前股價": "{:.2f}",
        "五年平均現金": "{:.2f}",
        "五年平均配股": "{:.2f}",
        "總殖利率(%)": "{:.2f}",
    }

    # 欄位寬度設定
    column_config = {
        "股票代號":    st.column_config.TextColumn("股票代號",    width=80),
        "中文名稱":    st.column_config.TextColumn("中文名稱",    width=80),
        "目前股價":    st.column_config.NumberColumn("目前股價",   width=90,  format="%.2f"),
        "五年平均現金": st.column_config.NumberColumn("五年平均現金", width=110, format="%.2f"),
        "五年平均配股": st.column_config.NumberColumn("五年平均配股", width=110, format="%.2f"),
        "總殖利率(%)": st.column_config.NumberColumn("總殖利率(%)", width=100, format="%.2f"),
    }

    st.dataframe(
        df_display.style.map(
            lambda x: 'background-color: #FFCCCC' if isinstance(x, float) and x >= threshold else '',
            subset=['總殖利率(%)']
        ).format(format_dict),
        column_config=column_config,
        use_container_width=False,  # 關閉自動撐滿，讓欄寬生效
    )

    target_stocks = df[df['總殖利率(%)'] >= threshold]
    if not target_stocks.empty:
        st.success(f"🔥 發現 {len(target_stocks)} 檔標的總殖利率超過 {threshold}%！")

else:
    st.error("暫時抓不到數據，請稍後再試。")

# --- 2. GitHub Actions 自動發信邏輯 ---
if os.getenv("GITHUB_ACTIONS") == "true":
    print("--- 偵測到環境為 GitHub Actions，準備執行發信檢查 ---")
    if not df.empty:
        targets = df[df['總殖利率(%)'] >= threshold]
        if not targets.empty:
            user = os.getenv("MAIL_USER")
            password = os.getenv("MAIL_PASSWORD")
            to = os.getenv("MAIL_TO")
            
            if user and password:
                try:
                    content = f"📢 金融股達標通知：\n\n{targets.to_string()}\n\n計算公式：(5年平均現金+5年平均配股)/目前股價"
                    msg = MIMEText(content)
                    msg['Subject'] = f'【殖利率監控】{len(targets)} 檔金融股已達標！'
                    msg['From'] = user
                    msg['To'] = to
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(user, password)
                        server.send_message(msg)
                    print("✅ 郵件發送成功！")
                except Exception as e:
                    print(f"❌ 郵件發送失敗: {e}")
            else:
                print("❌ 錯誤：未設定 MAIL_USER 或 MAIL_PASSWORD")
        else:
            print("ℹ️ 目前沒有股票達標，不發送信件。")
