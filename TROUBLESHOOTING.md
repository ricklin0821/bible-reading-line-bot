# 聖經讀經 LINE Bot - 疑難排解指南

## 目錄
1. [重新部署](#重新部署)
2. [重置使用者狀態](#重置使用者狀態)
3. [常見問題](#常見問題)
4. [查看日誌](#查看日誌)

---

## 重新部署

當程式碼更新後，需要重新部署到 Google Cloud Run：

```bash
cd ~/bible-reading-line-bot
git pull origin master

# 替換 YOUR_PROJECT_ID 為您的 Google Cloud 專案 ID
PROJECT_ID="YOUR_PROJECT_ID"
IMAGE_NAME="gcr.io/${PROJECT_ID}/bible-bot:latest"

# 建構並部署
gcloud builds submit --tag $IMAGE_NAME .
gcloud run deploy bible-bot \
    --image $IMAGE_NAME \
    --platform managed \
    --region asia-east1 \
    --allow-unauthenticated \
    --quiet
```

---

## 重置使用者狀態

### 方法 1：使用 Admin API（推薦）

#### 重置測驗狀態

```bash
# 替換 YOUR_CLOUD_RUN_URL 和 YOUR_LINE_USER_ID
curl -X POST "https://YOUR_CLOUD_RUN_URL/admin/users/YOUR_LINE_USER_ID/reset-quiz" \
  -u admin:bible2025
```

#### 重置讀經進度（回到第 1 天）

```bash
curl -X POST "https://YOUR_CLOUD_RUN_URL/admin/users/YOUR_LINE_USER_ID/reset-progress" \
  -u admin:bible2025
```

### 方法 2：使用 Postman 或瀏覽器

1. 開啟 Postman 或任何 API 測試工具
2. 建立 POST 請求到：
   - 重置測驗：`https://YOUR_CLOUD_RUN_URL/admin/users/YOUR_LINE_USER_ID/reset-quiz`
   - 重置進度：`https://YOUR_CLOUD_RUN_URL/admin/users/YOUR_LINE_USER_ID/reset-progress`
3. 在 Authorization 標籤中選擇 "Basic Auth"
   - Username: `admin`
   - Password: `bible2025`
4. 發送請求

### 如何取得 LINE User ID

1. 查看 Cloud Run 日誌
2. 搜尋您的訊息，會看到類似：
   ```
   [DEBUG] User U67da4c26e3706928c2eb77c1fc89b3a9 sent message: ...
   ```
3. `U67da4c26e3706928c2eb77c1fc89b3a9` 就是您的 LINE User ID

---

## 常見問題

### Q1: Bot 沒有回應任何訊息

**可能原因：**
- 使用者狀態卡住（例如：測驗狀態異常）
- 程式執行錯誤

**解決方法：**
1. 查看 Cloud Run 日誌，尋找錯誤訊息
2. 使用 Admin API 重置測驗狀態
3. 重新部署最新版本

### Q2: 測驗答案一直顯示錯誤

**可能原因：**
- 答案比對邏輯問題
- 資料庫中的答案格式不正確

**解決方法：**
1. 查看日誌中的 `[DEBUG] Answer comparison` 訊息
2. 比對 `User answer (clean)` 和 `Correct answer (clean)`
3. 如果格式不同，可能需要調整答案比對邏輯

### Q3: 完成測驗後沒有顯示下一天的讀經計畫

**可能原因：**
- `get_reading_plan_message` 函數執行失敗
- 資料庫中沒有下一天的讀經計畫資料

**解決方法：**
1. 查看日誌中的 `[DEBUG] Next day readings` 訊息
2. 確認讀經計畫資料是否完整
3. 檢查 `[ERROR] Failed to generate next day plan` 錯誤訊息

### Q4: 如何測試 Bot 的互動功能

**新增的互動指令：**
- 發送「你好」、「哈囉」、「hi」→ Bot 會回覆問候語
- 發送「幫助」、「help」→ Bot 會顯示使用指南
- 發送「1」或「2」→ 選擇讀經計畫
- 發送「?」、「1」、「2」→ Bot 會回應

---

## 查看日誌

### 使用 Google Cloud Console

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 選擇您的專案
3. 導航到 **Cloud Run** > **bible-bot** > **日誌**
4. 使用篩選器搜尋：
   - `[DEBUG]` - 除錯訊息
   - `[ERROR]` - 錯誤訊息
   - `Answer comparison` - 答案比對過程

### 使用 gcloud CLI

```bash
# 查看最近的日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" \
  --limit 50 \
  --format="table(timestamp, textPayload)"

# 只查看 DEBUG 訊息
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'DEBUG'" \
  --limit 50 \
  --format="table(timestamp, textPayload)"

# 只查看 ERROR 訊息
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'ERROR'" \
  --limit 50 \
  --format="table(timestamp, textPayload)"
```

---

## 聯絡資訊

如果以上方法都無法解決問題，請：
1. 收集完整的錯誤日誌
2. 記錄重現問題的步驟
3. 聯繫開發者

---

**最後更新：** 2025-10-31
