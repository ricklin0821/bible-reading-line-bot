# Rich Menu 部署指南

## 📋 概述

本指南說明如何部署 Rich Menu（圖文選單），以實現成本節省策略（Plan B）。

### 成本節省目標
- **原成本**: ~$40 USD/月（5次推播/天 × 10用戶 = 1,500推播/月）
- **新成本**: ~$3 USD/月（1次推播/天 × 10用戶 = 300推播/月）
- **節省**: 92% 成本降低

### 策略變更
- **推播頻率**: 從 5次/天 → 1次/天（僅保留早上 6:00）
- **互動模式**: 從主動推播 → 被動互動（透過 Rich Menu）
- **功能保留**: 所有功能仍可透過 Rich Menu 存取

---

## 🎨 Rich Menu 設計

### 圖片規格
- **尺寸**: 2500 × 1686 像素
- **格式**: PNG
- **檔案**: `rich_menu.png`

### 按鈕配置（6個按鈕，2×3 網格）

| 按鈕 | 功能 | 說明 |
|------|------|------|
| 📖 今日讀經 | 取得今日讀經計畫 | 顯示今日應讀的經文章節 |
| 🌅 荒漠甘泉 | 取得今日靈修內容 | 顯示今日荒漠甘泉靈修文章和圖片 |
| ✅ 回報讀經 | 回報完成讀經 | 記錄讀經完成，累積積分和連續天數 |
| 📊 我的進度 | 查看個人統計 | 顯示積分、連續天數、完成率等 |
| 🏆 排行榜 | 查看排行榜 | 顯示本週榜、連續榜、總榜、新星榜 |
| ⚙️ 選單 | 更多功能 | 隱私設定、每日金句、成就分享等 |

---

## 🚀 部署步驟

### 步驟 1: 上傳 Rich Menu 圖片

使用 LINE Messaging API 上傳圖片並創建 Rich Menu：

```bash
# 設定環境變數
export CHANNEL_ACCESS_TOKEN="你的_LINE_CHANNEL_ACCESS_TOKEN"

# 1. 創建 Rich Menu
curl -X POST https://api.line.me/v2/bot/richmenu \
-H "Authorization: Bearer $CHANNEL_ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "size": {
    "width": 2500,
    "height": 1686
  },
  "selected": true,
  "name": "Bible Reading Bot Menu",
  "chatBarText": "📖 聖經讀經選單",
  "areas": [
    {
      "bounds": {
        "x": 0,
        "y": 0,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "今日讀經"
      }
    },
    {
      "bounds": {
        "x": 1250,
        "y": 0,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "荒漠甘泉"
      }
    },
    {
      "bounds": {
        "x": 0,
        "y": 562,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "回報讀經"
      }
    },
    {
      "bounds": {
        "x": 1250,
        "y": 562,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "我的進度"
      }
    },
    {
      "bounds": {
        "x": 0,
        "y": 1124,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "排行榜"
      }
    },
    {
      "bounds": {
        "x": 1250,
        "y": 1124,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "選單"
      }
    }
  ]
}'

# 記下回傳的 richMenuId，例如: richmenu-xxxxxxxxxxxxx

# 2. 上傳圖片
curl -X POST https://api-data.line.me/v2/bot/richmenu/{richMenuId}/content \
-H "Authorization: Bearer $CHANNEL_ACCESS_TOKEN" \
-H "Content-Type: image/png" \
--data-binary @rich_menu.png

# 3. 設定為預設 Rich Menu（所有用戶）
curl -X POST https://api.line.me/v2/bot/user/all/richmenu/{richMenuId} \
-H "Authorization: Bearer $CHANNEL_ACCESS_TOKEN"
```

### 步驟 2: 刪除不必要的 Cloud Scheduler 任務

保留早上 6:00 的推播，刪除其他 4 個：

```bash
# 設定專案
gcloud config set project bible-bot-project

# 刪除中午 12:00 讀經推播
gcloud scheduler jobs delete bible-push-noon --location=asia-east1 --quiet

# 刪除中午 12:30 靈修推播
gcloud scheduler jobs delete daily-devotional-sender --location=asia-east1 --quiet

# 刪除傍晚 6:00 讀經推播
gcloud scheduler jobs delete bible-push-evening --location=asia-east1 --quiet

# 刪除晚上 11:00 讀經推播
gcloud scheduler jobs delete bible-push-night --location=asia-east1 --quiet

# 確認只剩下早上 6:00 的任務
gcloud scheduler jobs list --location=asia-east1
```

### 步驟 3: 更新 main.py 以處理 Rich Menu 訊息

Rich Menu 按鈕會發送文字訊息，需要在 `main.py` 的 `handle_message` 函數中處理：

```python
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理文字訊息"""
    user_id = event.source.user_id
    text = event.message.text.strip()
    
    # Rich Menu 按鈕處理
    if text == "今日讀經":
        # 呼叫現有的今日讀經邏輯
        send_daily_reading(user_id)
        return
    
    elif text == "荒漠甘泉":
        # 呼叫現有的靈修內容邏輯
        send_devotional(user_id)
        return
    
    elif text == "回報讀經":
        # 呼叫現有的回報邏輯
        handle_reading_report(user_id)
        return
    
    elif text == "我的進度":
        # 呼叫現有的進度查詢邏輯
        send_user_stats(user_id)
        return
    
    elif text == "排行榜":
        # 發送排行榜連結
        send_leaderboard_link(user_id)
        return
    
    elif text == "選單":
        # 顯示更多功能選單
        send_menu_options(user_id)
        return
    
    # 原有的訊息處理邏輯...
```

### 步驟 4: 部署到 Cloud Run

```bash
# 確保在專案目錄
cd /home/ubuntu/bible-reading-line-bot

# 提交變更
git add .
git commit -m "Update message handler for Rich Menu integration"
git push origin master

# 重新部署到 Cloud Run
gcloud run deploy bible-bot \
  --source . \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --project bible-bot-project \
  --service-account 741437082833-compute@developer.gserviceaccount.com
```

---

## ✅ 驗證部署

### 1. 檢查 Rich Menu 是否生效
- 開啟 LINE Bot 聊天室
- 點擊左下角的鍵盤圖示
- 應該會看到 6 個按鈕的圖文選單

### 2. 測試各按鈕功能
- 點擊「今日讀經」→ 應收到今日讀經計畫
- 點擊「荒漠甘泉」→ 應收到今日靈修內容
- 點擊「回報讀經」→ 應顯示回報選項
- 點擊「我的進度」→ 應顯示個人統計
- 點擊「排行榜」→ 應收到排行榜連結
- 點擊「選單」→ 應顯示更多功能

### 3. 確認 Cloud Scheduler 任務
```bash
gcloud scheduler jobs list --location=asia-east1
```
應該只看到 1 個任務：`bible-push-morning`

### 4. 監控成本
- 前往 [LINE Developers Console](https://developers.line.biz/console/)
- 查看 Messaging API 的使用量
- 預期每月推播數量：約 300 次（10用戶 × 30天 × 1次/天）

---

## 📊 成本比較

### 部署前（Plan A）
| 項目 | 數量 | 單價 | 月費 |
|------|------|------|------|
| Cloud Scheduler | 5 jobs | $0.04/job | $0.20 |
| LINE 推播 | 1,500 次 | $0.003/次 | $45.00 |
| **總計** | - | - | **$45.20** |

### 部署後（Plan B）
| 項目 | 數量 | 單價 | 月費 |
|------|------|------|------|
| Cloud Scheduler | 1 job | $0.04/job | $0.04 |
| LINE 推播 | 300 次 | $0.003/次 | $0.90 |
| LINE 回覆 | ~1,000 次 | $0.00/次 | $0.00 |
| **總計** | - | - | **$0.94** |

**節省**: $44.26/月（97.9% 降低）

> 💡 **注意**: LINE 回覆訊息（Reply API）是免費的，只有主動推播（Push API）才收費！

---

## 🔧 故障排除

### Rich Menu 沒有顯示
1. 確認 Rich Menu 已成功創建（檢查 API 回應）
2. 確認圖片已成功上傳（檢查 HTTP 200 狀態）
3. 確認已設定為預設 Rich Menu
4. 嘗試重新加入 Bot 或重啟 LINE App

### 按鈕點擊沒有反應
1. 檢查 `main.py` 是否正確處理文字訊息
2. 檢查 Cloud Run 日誌：`gcloud run logs read bible-bot --region=asia-east1`
3. 確認 Webhook URL 設定正確

### 成本沒有降低
1. 確認舊的 Scheduler 任務已刪除
2. 檢查 LINE Developers Console 的推播統計
3. 等待 24-48 小時讓變更生效

---

## 📝 後續優化建議

1. **監控用戶互動率**
   - 追蹤 Rich Menu 按鈕點擊次數
   - 比較主動推播 vs 被動互動的效果

2. **優化早晨推播內容**
   - 加入 Quick Reply 按鈕
   - 提供當日重點預覽
   - 增加互動誘因

3. **定期更新 Rich Menu**
   - 根據節日或特殊活動調整按鈕
   - A/B 測試不同的按鈕配置

4. **收集用戶反饋**
   - 詢問用戶對新互動模式的滿意度
   - 根據反饋調整功能

---

## 📞 支援

如有問題，請檢查：
- [LINE Messaging API 文件](https://developers.line.biz/en/docs/messaging-api/)
- [Rich Menu 設計指南](https://developers.line.biz/en/docs/messaging-api/using-rich-menus/)
- [Google Cloud Run 文件](https://cloud.google.com/run/docs)

---

**最後更新**: 2025-11-07
**版本**: 1.0
