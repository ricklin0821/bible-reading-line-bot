# main.py 更新指南

## 問題說明

由於 Windows PowerShell 的編碼問題，Rich Menu 按鈕使用**英文觸發文字**而非中文。

## 解決方案

在 `main.py` 中新增英文觸發文字的處理邏輯，同時保留原有的中文處理。

---

## 需要更新的程式碼

找到 `handle_message` 函數，新增以下處理邏輯：

```python
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理文字訊息"""
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    # ============================================
    # Rich Menu 按鈕處理 (英文觸發文字)
    # ============================================
    
    # 今日讀經
    if text in ["Today Reading", "今日讀經"]:
        send_daily_reading(user_id)
        return
    
    # 荒漠甘泉
    elif text in ["Devotional", "荒漠甘泉"]:
        send_devotional(user_id)
        return
    
    # 回報讀經
    elif text in ["Report", "回報讀經"]:
        handle_reading_report(user_id)
        return
    
    # 我的進度
    elif text in ["Progress", "我的進度"]:
        send_user_stats(user_id)
        return
    
    # 排行榜
    elif text in ["Leaderboard", "排行榜"]:
        send_leaderboard_link(user_id)
        return
    
    # 選單
    elif text in ["Menu", "選單"]:
        send_menu_options(user_id)
        return
    
    # ============================================
    # 原有的訊息處理邏輯
    # ============================================
    
    # ... 其他原有的程式碼 ...
```

---

## 按鈕對應表

| Rich Menu 按鈕 | 英文觸發文字 | 中文觸發文字 | 對應函數 |
|---------------|-------------|-------------|---------|
| 📖 (左上) | "Today Reading" | "今日讀經" | `send_daily_reading()` |
| 🌅 (右上) | "Devotional" | "荒漠甘泉" | `send_devotional()` |
| ✅ (左中) | "Report" | "回報讀經" | `handle_reading_report()` |
| 📊 (右中) | "Progress" | "我的進度" | `send_user_stats()` |
| 🏆 (左下) | "Leaderboard" | "排行榜" | `send_leaderboard_link()` |
| ⚙️ (右下) | "Menu" | "選單" | `send_menu_options()` |

---

## 完整範例

以下是完整的 `handle_message` 函數範例：

```python
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer
)
from linebot.v3.webhooks import MessageEvent
from linebot.v3.webhooks.models import TextMessageContent

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理文字訊息"""
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    # Rich Menu 按鈕處理（支援英文和中文）
    if text in ["Today Reading", "今日讀經"]:
        # 發送今日讀經計畫
        try:
            today = datetime.now(taipei_tz)
            day_of_year = today.timetuple().tm_yday
            
            # 取得今日讀經計畫
            plan = get_reading_plan(day_of_year)
            
            if plan:
                message = f"📖 今日讀經計畫（第 {day_of_year} 天）\n\n"
                message += f"📕 舊約：{plan['old_testament']}\n"
                message += f"📘 新約：{plan['new_testament']}\n"
                message += f"📗 詩篇：{plan['psalms']}\n"
                message += f"📙 箴言：{plan['proverbs']}\n\n"
                message += "✅ 完成後請點擊「回報讀經」記錄您的進度！"
                
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=message)]
                        )
                    )
            else:
                # 發送錯誤訊息
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text="抱歉，無法取得今日讀經計畫")]
                        )
                    )
        except Exception as e:
            print(f"Error in Today Reading: {e}")
        return
    
    elif text in ["Devotional", "荒漠甘泉"]:
        # 發送今日靈修內容
        try:
            today = datetime.now(taipei_tz)
            day_of_year = today.timetuple().tm_yday
            
            # 取得今日靈修內容
            devotional = get_devotional_content(day_of_year)
            
            if devotional:
                # 生成靈修圖片
                image_path = generate_devotional_image(devotional)
                
                # 上傳圖片並發送
                # ... (使用現有的圖片發送邏輯)
                pass
            else:
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text="抱歉，無法取得今日靈修內容")]
                        )
                    )
        except Exception as e:
            print(f"Error in Devotional: {e}")
        return
    
    elif text in ["Report", "回報讀經"]:
        # 處理讀經回報
        try:
            # 顯示回報選項
            # ... (使用現有的回報邏輯)
            pass
        except Exception as e:
            print(f"Error in Report: {e}")
        return
    
    elif text in ["Progress", "我的進度"]:
        # 發送個人統計
        try:
            # 取得用戶統計資料
            stats = get_user_stats(user_id)
            
            if stats:
                message = f"📊 您的讀經進度\n\n"
                message += f"🔥 連續天數：{stats.get('streak', 0)} 天\n"
                message += f"⭐ 總積分：{stats.get('total_points', 0)} 分\n"
                message += f"📅 本週完成：{stats.get('weekly_count', 0)} 次\n"
                message += f"📈 完成率：{stats.get('completion_rate', 0):.1f}%\n\n"
                message += "繼續加油！💪"
                
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=message)]
                        )
                    )
            else:
                with ApiClient(configuration) as api_client:
                    line_bot_api = MessagingApi(api_client)
                    line_bot_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text="尚無讀經記錄，快開始您的讀經計畫吧！")]
                        )
                    )
        except Exception as e:
            print(f"Error in Progress: {e}")
        return
    
    elif text in ["Leaderboard", "排行榜"]:
        # 發送排行榜連結
        try:
            leaderboard_url = "https://bible-bot-741437082833.asia-east1.run.app/leaderboard.html"
            message = f"🏆 查看排行榜\n\n{leaderboard_url}\n\n"
            message += "包含：本週榜、連續榜、總榜、新星榜"
            
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=message)]
                    )
                )
        except Exception as e:
            print(f"Error in Leaderboard: {e}")
        return
    
    elif text in ["Menu", "選單"]:
        # 顯示更多功能選單
        try:
            message = "⚙️ 更多功能\n\n"
            message += "📖 每日金句\n"
            message += "🎯 成就分享\n"
            message += "🔒 隱私設定\n"
            message += "❓ 使用說明\n\n"
            message += "請輸入功能名稱或使用下方選單"
            
            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=message)]
                    )
                )
        except Exception as e:
            print(f"Error in Menu: {e}")
        return
    
    # 原有的其他訊息處理邏輯
    # ... (保留原有程式碼)
```

---

## 部署步驟

### 1. 更新 main.py

```bash
# 編輯 main.py
nano main.py

# 或使用您喜歡的編輯器
code main.py
```

### 2. 測試本地

```bash
# 本地測試（如果有設定）
python main.py
```

### 3. 提交到 Git

```bash
git add main.py
git commit -m "Add English trigger text support for Rich Menu"
git push origin master
```

### 4. 部署到 Cloud Run

```bash
gcloud run deploy bible-bot \
  --source . \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --project bible-bot-project
```

---

## 測試檢查清單

部署後請測試以下功能：

- [ ] 點擊 Rich Menu「📖」按鈕 → 收到今日讀經計畫
- [ ] 點擊 Rich Menu「🌅」按鈕 → 收到荒漠甘泉內容
- [ ] 點擊 Rich Menu「✅」按鈕 → 顯示回報選項
- [ ] 點擊 Rich Menu「📊」按鈕 → 顯示個人統計
- [ ] 點擊 Rich Menu「🏆」按鈕 → 收到排行榜連結
- [ ] 點擊 Rich Menu「⚙️」按鈕 → 顯示更多功能
- [ ] 輸入中文「今日讀經」→ 同樣功能正常
- [ ] 輸入中文「荒漠甘泉」→ 同樣功能正常

---

## 故障排除

### 問題：點擊按鈕沒有反應

**檢查：**
1. Cloud Run 日誌：`gcloud run logs read bible-bot --region=asia-east1`
2. 確認 main.py 已更新並部署
3. 確認函數名稱正確

### 問題：收到「無法處理」的訊息

**檢查：**
1. 確認觸發文字拼寫正確（區分大小寫）
2. 確認 `text.strip()` 有正確去除空白
3. 檢查 if-elif 邏輯順序

### 問題：中文觸發文字不工作

**檢查：**
1. 確認 `in ["English", "中文"]` 語法正確
2. 確認中文字元編碼為 UTF-8
3. 測試直接輸入中文是否有效

---

## 後續優化建議

1. **統一觸發文字**
   - 考慮只使用中文或只使用英文
   - 可以在部署 Rich Menu 時使用中文（需要在 Linux/Mac 環境）

2. **使用 Postback Action**
   - 改用 `postback` 而非 `message` action
   - 避免觸發文字顯示在聊天室中

3. **多語言支援**
   - 根據用戶語言設定顯示不同 Rich Menu
   - 支援英文和中文介面

---

**最後更新**: 2025-11-07  
**版本**: 1.0
