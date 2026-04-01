import streamlit as st
import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# 1. 定義完整的金融股清單 (代號: 中文名稱)
FIN_MAP = {
    '2801.TW': '彰銀', '2809.TW': '京城銀', '2812.TW': '台中銀', '2834.TW': '臺企銀',
    '2836.TW': '萬企', '2838.TW': '聯邦銀', '2851.TW': '中再保', '2855.TW': '寶來證',
    '2880.TW': '華南金', '2881.TW': '富邦金', '2882.TW': '國泰金', '2883.TW': '凱基金',
    '2884.TW': '玉山金', '2885.TW': '元大金', '2886.TW': '兆豐金', '2887.TW': '台新金',
    '2888.TW': '新光金', '2889.TW': '國票金', '2890.TW': '永豐金', '2891.TW': '中信金',
    '2892.TW': '第一金', '2897.TW': '王道銀', '5876.TW': '上海商銀', '5880.TW': '合庫金',
    '6005.TW': '群益證'
}

st.set_page_config(page_title="金融股總殖利率監控", layout="wide")
st.title("🏦 金融股五年平均「息+利」總殖利率監控")
st.write(f"更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def get_stock_data():
    data_list = []
    for code, name in FIN_MAP.items():
        try:
            ticker = yf.Ticker(code)
            # 獲取收盤價
            price = ticker.fast_info['last_price']
            
            # 獲取配息紀錄 (yfinance 的 actions 包含 Dividends)
            # 這裡的 Dividends 通常已經是 yfinance 整合過的每股配發總價值
            divs = ticker.actions['Dividends']
            
            # 取最近五年的數據
            last_5_year_divs = divs.tail(5)
            avg_total_div = last_5_year_divs.mean()
            
            # 計算總殖利率 (息+利)
            total_yield = (avg_total_div / price) * 100
            
            data_list.append({
                "股票代號": code.replace('.TW', ''),
                "中文名稱": name,
                "目前股價": round(price, 1),
                "五年平均總股利(息+利)": round(avg_total_div, 1),
                "平均總殖利率(%)": round(total_yield, 1)
            })
        except:
            continue
    
    df = pd.DataFrame(data_list)
    if not df.empty:
        df.index = df.index + 1
    return df

df = get_stock_data()

def highlight_yield(val):
    return 'background-color: #FFCCCC' if val >= 6.5 else ''

st.subheader("即時監控列表 (總殖利率 $\ge$ 6.5% 將以紅色標示)")

if not df.empty:
    st.dataframe(df.style.map(highlight_yield, subset=['平均總殖利率(%)']))

    # Email 通知邏輯
    target_stocks = df[df['平均總殖利率(%)'] >= 6.5]
    if not target_stocks.empty:
        st.success(f"📢 發現 {len(target_stocks)} 個符合 6.5% 門檻的標的！")
        if st.button("點此發送測試 Email"):
            try:
                mail_user = st.secrets["email"]["user"]
                mail_password = st.secrets["email"]["password"]
                mail_to = st.secrets["email"]["to"]
                
                content = "符合 6.5% 總殖利率標的清單：\n\n" + target_stocks.to_string()
                msg = MIMEText(content)
                msg['Subject'] = '【台股通知】高殖利率金融股提醒'
                msg['From'] = mail_user
                msg['To'] = mail_to
                
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(mail_user, mail_password)
                    server.send_message(msg)
                st.info("Email 已成功發送！")
            except Exception as e:
                st.error(f"發送失敗：{e}")
else:
    st.warning("數據抓取中或暫時無資料...")
