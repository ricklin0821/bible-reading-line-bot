# 部署指令

## 重新部署到 Google Cloud Run

請按照以下步驟重新部署 Bible Bot：

### 1. 拉取最新程式碼

```bash
cd ~/bible-reading-line-bot
git pull origin master
```

### 2. 建構 Docker 映像檔

請將 `YOUR_PROJECT_ID` 替換為您的 Google Cloud 專案 ID：

```bash
# 設定專案 ID
PROJECT_ID="YOUR_PROJECT_ID"
IMAGE_NAME="gcr.io/${PROJECT_ID}/bible-bot:latest"

# 建構映像檔
gcloud builds submit --tag $IMAGE_NAME .
```

### 3. 部署到 Cloud Run

```bash
gcloud run deploy bible-bot \
    --image $IMAGE_NAME \
    --platform managed \
    --region asia-east1 \
    --allow-unauthenticated \
    --quiet
```

**注意：** 環境變數應該已經在之前的部署中設定好了，如果需要更新環境變數，請使用以下指令：

```bash
gcloud run deploy bible-bot \
    --image $IMAGE_NAME \
    --platform managed \
    --region asia-east1 \
    --allow-unauthenticated \
    --update-env-vars LINE_CHANNEL_ACCESS_TOKEN="您的TOKEN",LINE_CHANNEL_SECRET="您的SECRET",ADMIN_USERNAME="admin",ADMIN_PASSWORD="bible2025" \
    --quiet
```

### 4. 測試功能

部署完成後，請測試以下功能：

1. **選擇讀經計畫**：發送「1」或「2」給 LINE Bot
2. **回報已完成讀經**：點擊「✅ 回報已完成讀經」按鈕

### 5. 查看日誌（如果有錯誤）

如果測試過程中遇到錯誤，請查看 Cloud Run 的日誌：

- **方法 1**：透過 [Google Cloud Console](https://console.cloud.google.com/run) 查看日誌
- **方法 2**：使用指令查看日誌（需要安裝 gcloud CLI）：

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'DEBUG|Error'" --limit 50 --format="table(timestamp, textPayload)"
```

## 最新修改

### 2024-10-31 修正內容

1. **修正「分享經文」按鈕 URI 編碼問題**
   - 使用 `urllib.parse.quote` 正確編碼中文字元
   - 解決 LINE API 回傳 `Invalid action URI` 錯誤

2. **加入測驗產生除錯日誌**
   - 在 `quiz_generator.py` 中加入詳細的除錯訊息
   - 追蹤讀經範圍解析和經文查詢過程

3. **加強錯誤處理**
   - 在 `main.py` 中加入詳細的錯誤訊息
   - 當測驗產生失敗時，Bot 會回覆具體的錯誤原因

## 疑難排解

如果「回報已完成讀經」功能仍然無法產生測驗，可能的原因：

1. **Firestore 資料庫中沒有聖經經文資料**
   - 檢查 `bible_text` collection 是否有資料
   - 確認資料匯入是否成功

2. **讀經計畫資料不存在**
   - 檢查 `bible_plans` collection 是否有資料
   - 確認 `plan_type` 和 `day_number` 是否正確

3. **使用者資料異常**
   - 檢查使用者的 `plan_type` 和 `current_day` 是否正確設定

請將 Bot 回覆的錯誤訊息和日誌提供給開發人員，以便進一步診斷問題。
