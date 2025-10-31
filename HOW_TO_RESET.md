# 如何重置使用者測驗狀態

## 方法 1：使用自動化腳本（最簡單）⭐

### 步驟：

1. **取得您的 LINE User ID**
   
   從 Cloud Run 日誌中找到您的 User ID，格式類似：`U67da4c26e3706928c2eb77c1fc89b3a9`

2. **執行重置腳本**

   ```bash
   cd ~/bible-reading-line-bot
   git pull origin master
   ./reset_user.sh U67da4c26e3706928c2eb77c1fc89b3a9
   ```
   
   （請將 `U67da4c26e3706928c2eb77c1fc89b3a9` 替換為您的實際 User ID）

3. **選擇操作**
   
   腳本會詢問您要執行的操作：
   - 選項 1：只重置測驗狀態（保留讀經進度）
   - 選項 2：重置讀經進度（回到第 1 天）

---

## 方法 2：使用 curl 指令

### 重置測驗狀態（保留讀經進度）

```bash
# 1. 取得 Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe bible-bot --region asia-east1 --format='value(status.url)')

# 2. 重置測驗狀態
curl -X POST "${CLOUD_RUN_URL}/admin/users/YOUR_LINE_USER_ID/reset-quiz" \
  -u admin:bible2025
```

### 重置讀經進度（回到第 1 天）

```bash
# 1. 取得 Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe bible-bot --region asia-east1 --format='value(status.url)')

# 2. 重置讀經進度
curl -X POST "${CLOUD_RUN_URL}/admin/users/YOUR_LINE_USER_ID/reset-progress" \
  -u admin:bible2025
```

---

## 方法 3：使用網頁瀏覽器

1. **開啟瀏覽器**，前往以下 URL（替換 `YOUR_CLOUD_RUN_URL` 和 `YOUR_LINE_USER_ID`）：

   **重置測驗狀態：**
   ```
   https://YOUR_CLOUD_RUN_URL/admin/users/YOUR_LINE_USER_ID/reset-quiz
   ```

   **重置讀經進度：**
   ```
   https://YOUR_CLOUD_RUN_URL/admin/users/YOUR_LINE_USER_ID/reset-progress
   ```

2. **輸入帳號密碼**（瀏覽器會彈出登入視窗）：
   - Username: `admin`
   - Password: `bible2025`

3. **查看結果**，應該會顯示 JSON 格式的成功訊息。

---

## 如何取得 LINE User ID

### 方法 1：從 Cloud Run 日誌查看

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 選擇您的專案
3. 導航到 **Cloud Run** > **bible-bot** > **日誌**
4. 搜尋您最近發送的訊息
5. 找到類似以下的日誌：
   ```
   [DEBUG] User U67da4c26e3706928c2eb77c1fc89b3a9 sent message: ...
   ```
6. `U67da4c26e3706928c2eb77c1fc89b3a9` 就是您的 LINE User ID

### 方法 2：使用 gcloud CLI

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'User U'" \
  --limit 10 \
  --format="value(textPayload)"
```

---

## 如何取得 Cloud Run URL

```bash
gcloud run services describe bible-bot \
  --region asia-east1 \
  --format='value(status.url)'
```

輸出範例：`https://bible-bot-xxxxx-de.a.run.app`

---

## 常見問題

### Q: 執行腳本時顯示「Permission denied」

**解決方法：**
```bash
chmod +x reset_user.sh
```

### Q: 顯示「無法取得 Cloud Run URL」

**可能原因：**
1. 未安裝 gcloud CLI
2. 未登入 Google Cloud
3. 服務名稱或區域不正確

**解決方法：**
```bash
# 登入 Google Cloud
gcloud auth login

# 設定專案
gcloud config set project YOUR_PROJECT_ID

# 確認服務存在
gcloud run services list --region asia-east1
```

### Q: curl 指令顯示 401 Unauthorized

**原因：** 帳號密碼錯誤

**解決方法：** 確認使用正確的帳號密碼：
- Username: `admin`
- Password: `bible2025`

### Q: 重置後 Bot 還是沒有回應

**可能原因：**
1. 需要重新部署最新版本
2. 程式執行錯誤

**解決方法：**
1. 重新部署（參考 `DEPLOY.md`）
2. 查看 Cloud Run 日誌尋找錯誤訊息
3. 再次嘗試重置

---

## 完整操作流程（從頭到尾）

```bash
# 1. 更新程式碼
cd ~/bible-reading-line-bot
git pull origin master

# 2. 重新部署
PROJECT_ID="YOUR_PROJECT_ID"
IMAGE_NAME="gcr.io/${PROJECT_ID}/bible-bot:latest"
gcloud builds submit --tag $IMAGE_NAME .
gcloud run deploy bible-bot --image $IMAGE_NAME --platform managed --region asia-east1 --allow-unauthenticated --quiet

# 3. 取得 Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe bible-bot --region asia-east1 --format='value(status.url)')
echo "Cloud Run URL: $CLOUD_RUN_URL"

# 4. 從日誌取得 LINE User ID（發送一則訊息給 Bot 後執行）
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'User U'" \
  --limit 5 \
  --format="value(textPayload)"

# 5. 重置測驗狀態（替換 YOUR_LINE_USER_ID）
curl -X POST "${CLOUD_RUN_URL}/admin/users/YOUR_LINE_USER_ID/reset-quiz" -u admin:bible2025

# 6. 測試 Bot
# 在 LINE 中發送訊息給 Bot，應該會正常回應
```

---

**最後更新：** 2025-10-31
