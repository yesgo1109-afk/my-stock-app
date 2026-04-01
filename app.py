import streamlit as st
import pandas as pd
from FinMind.data import DataLoader
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import time

# 初始化資料庫
dl = DataLoader()

FIN_MAP = {
    '2801': '彰銀', '2809': '京城銀', '2812': '台中銀', '2834': '臺企銀',
    '2880': '華南金', '2881': '富邦金', '2882': '國泰金', '2883': '凱基金',
    '2884': '玉山金', '2885': '元大金', '2886': '兆豐金', '2887': '台新金',
    '2890': '永豐金', '2891': '中信金', '2892': '第一金', '5880': '合庫金'
}

st.set_page_config(page_title="台股金融股監控", layout="wide")
st.title("🏦 台股金融股五年「息+利」總殖利率監控")

# 增加進度條顯示
@st.cache_data(ttl=3600)
def get_fin_data():
    results = []
    this_year = datetime.now().year
    
    # 在網頁上顯示進度
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (code, name) in enumerate(FIN_MAP.items()):
        try:
            status_text.text(f"正在抓取：{name} ({code})...")
            
            # 抓取股價
            df_price = dl.taiwan_stock_daily(stock_id=code, start_date=f"{this_year}-01-01")
            if df_price.empty:
                continue
            current_price = df_price['close'].iloc[-1]
            
            # 抓取股利
            df_div = dl.taiwan_stock_dividend(stock_id=code, start_date=f"{this_year-6}-01-01")
            
            # 計算平均 (息+利)
            recent_divs = df_div.tail(5)
            avg_total = recent_divs['CashDividend'].mean() + recent_divs['StockDividend'].mean()
            
            total_yield = (avg_total / current_price) * 100
            
            results.append({
                "股票代號": code,
                "中文名稱": name,
                "目前股價": round(current_price, 1),
                "五年平均總股利(息+利)": round(avg_total, 1),
                "平均總殖利率(%)": round(total_yield, 1)
            })
            # 更新進度條
            progress_bar.progress((i + 1) / len(FIN_MAP))
            time.sleep(0.5) # 稍微停頓，避免抓太快被封鎖
        except:
            continue
            
    status_text.empty()
    progress_bar.empty()
    return pd.DataFrame(results)

# 顯示資料
with st.spinner('大數據計算中，請稍候...'):
    df = get_fin_data()

if not df.empty:
    df.index = df.index + 1
    st.subheader(f"📊 即時監控清單 (更新日期: {datetime.now().strftime('%Y-%m-%d')})")
    st.dataframe(df.style.map(lambda x: 'background-color: #FFCCCC' if x >= 6.5 else '', subset=['平均總殖利率(%)']), use_container_width=True)
    
    # 這裡可以保留之前的 Email 按鈕邏輯...
else:
    st.error("目前抓不到資料，請檢查網路連線或稍後再試。")
