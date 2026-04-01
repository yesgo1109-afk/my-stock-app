import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from datetime import datetime

# 1. 金融股清單
FIN_MAP = {
    '2881': '富邦金', '2882': '國泰金', '2884': '玉山金', '2886': '兆豐金', 
    '2891': '中信金', '5880': '合庫金', '2892': '第一金', '2880': '華南金',
    '2885': '元大金', '2887': '台新金', '2812': '台中銀', '2834': '臺企銀',
    '2883': '凱基金', '2890': '永豐金', '5876': '上海商銀', '2801': '彰銀'
}

st.set_page_config(page_title="金融股「息+利」自動監控", layout="wide")
st.title("🏦 金融股五年平均「息+利」總殖利率監控")

def get_yahoo_dividend(stock_code):
    """從 Yahoo 奇摩股市抓取過去五年平均 (現金+股票)"""
    url = f"https://tw.stock.yahoo.com/quote/{stock_code}.TW/dividend"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 抓取表格中的股利數據
        # Yahoo 網頁結構：現金股利與股票股利通常在特定的列表標籤中
        div_elements = soup.find_all('div', {'class': 'Lh(20px)'}) 
        
        # 這裡會抓取最近五年的數據 (每一年有 現金、股票、合計 三個數字)
        # 我們直接抓「合計」那一欄，或者是兩者相加
        # 簡單化處理：抓取前五個年度的總和平均
        # 注意：此處需根據 Yahoo 網頁實際標籤解析，以下為示範逻辑
        total_sum = 0
        count = 0
        
        # 實際上 Yahoo 股市的股利資料在一個列表裡，我們取前 5 筆
        # 每筆包含：年度、現金額、股票額、合計
        rows = soup.find_all('li', {'class': 'List(n)'})[1:6] # 跳過標題取前五行
        for row in rows:
            cols = row.find_all('div', {'class': 'D(f)'})
            # 這裡解析：現金 + 股票
            cash = float(cols[1].text) if cols[1].text != '-' else 0
            stock_div = float(cols[2].text) if cols[2].text != '-' else 0
            total_sum += (cash + stock_div)
            count += 1
        
        return total_sum / count if count > 0 else 0
    except:
        return 0

@st.cache_data(ttl=3600)
def get_final_report():
    data_list = []
    for code, name in FIN_MAP.items():
        # 抓即時股價
        ticker = yf.Ticker(f"{code}.TW")
        price = ticker.fast_info['last_price']
        
        # 抓 Yahoo 奇摩股市的五年平均股利
        avg_div = get_yahoo_dividend(code)
        
        # 計算總殖利率
        total_yield = (avg_div / price) * 100
        
        data_list.append({
            "股票代號": code,
            "中文名稱": name,
            "目前股價": round(price, 1),
            "五年平均(息+利)": round(avg_div, 2),
            "平均總殖利率(%)": round(total_yield, 1)
        })
    
    df = pd.DataFrame(data_list)
    df = df.sort_values(by="平均總殖利率(%)", ascending=False)
    df.index = range(1, len(df) + 1)
    return df

# 顯示與通知邏輯
df = get_final_report()
st.dataframe(df.style.map(lambda x: 'background-color: #FFCCCC' if x >= 6.5 else '', subset=['平均總殖利率(%)']))
