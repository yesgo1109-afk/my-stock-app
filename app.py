# 在原本的顯示表格代碼下方加入
target_stocks = df[df['平均總殖利率(%)'] >= 6.5]

# 如果有達標，且是在自動執行環境下（GitHub Actions）
if not target_stocks.empty:
    import os
    # 檢查是否有設定環境變數
    mail_user = os.getenv("MAIL_USER")
    mail_password = os.getenv("MAIL_PASSWORD")
    mail_to = os.getenv("MAIL_TO")
    
    if mail_user and mail_password:
        content = f"📢 發現符合 6.5% 門檻的標的：\n\n{target_stocks.to_string()}\n\n查詢網址：https://share.streamlit.io/你的帳號/你的專案"
        msg = MIMEText(content)
        msg['Subject'] = f'【殖利率達標通知】{datetime.now().strftime("%Y-%m-%d")}'
        msg['From'] = mail_user
        msg['To'] = mail_to
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(mail_user, mail_password)
            server.send_message(msg)
