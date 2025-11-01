# 部署指南

## 修復內容

已修復新使用者註冊時的 Firestore 資料類型錯誤：

### 修改檔案
1. **database.py** (第 91 行)
   - 修改前：`'start_date': date.today()`
   - 修改後：`'start_date': datetime.now()`

2. **main.py** (6 處)
   - 第 524 行：`user.start_date = datetime.now()`
   - 第 570 行：`datetime.now().date().isoformat()`
   - 第 637 行：`datetime.now().date().isoformat()`
   - 第 718 行：`datetime.now().date().isoformat()`
   - 第 774 行：`today = datetime.now().date()`
   - 第 791 行：`yesterday = datetime.now().date() - timedelta(days=1)`

### 問題說明
Firestore 不支援 Python 的 `datetime.date` 物件，只支援 `datetime.datetime` 物件。新使用者註冊時會觸發 `User.create()` 函數，其中的 `start_date` 欄位使用了 `date.today()`，導致 TypeError。

## 手動部署步驟

### 方法 1: 使用 Google Cloud Console (推薦)

1. 前往 [Google Cloud Console - Cloud Build](https://console.cloud.google.com/cloud-build)
2. 選擇專案：`bible-bot-project`
3. 點擊「建立觸發器」或使用現有觸發器
4. 手動執行建置：
   ```bash
   gcloud builds submit --tag gcr.io/bible-bot-project/bible-bot:latest .
   ```
5. 部署到 Cloud Run：
   ```bash
   gcloud run deploy bible-bot \
     --image gcr.io/bible-bot-project/bible-bot:latest \
     --platform managed \
     --region asia-east1 \
     --allow-unauthenticated \
     --quiet
   ```

### 方法 2: 使用 Cloud Shell

1. 前往 [Google Cloud Console](https://console.cloud.google.com)
2. 點擊右上角的 Cloud Shell 圖示啟動終端機
3. 執行以下指令：
   ```bash
   # 克隆最新的程式碼
   git clone https://github.com/ricklin0821/bible-reading-line-bot.git
   cd bible-reading-line-bot
   
   # 建置並部署
   gcloud builds submit --tag gcr.io/bible-bot-project/bible-bot:latest .
   gcloud run deploy bible-bot \
     --image gcr.io/bible-bot-project/bible-bot:latest \
     --platform managed \
     --region asia-east1 \
     --allow-unauthenticated \
     --quiet
   ```

### 方法 3: 設定自動部署 (一勞永逸)

1. 前往 [Cloud Build 觸發器](https://console.cloud.google.com/cloud-build/triggers)
2. 點擊「建立觸發器」
3. 設定：
   - **名稱**：`bible-bot-auto-deploy`
   - **事件**：推送到分支
   - **來源**：連結 GitHub 儲存庫 `ricklin0821/bible-reading-line-bot`
   - **分支**：`^master$`
   - **建置設定**：Cloud Build 設定檔 (yaml 或 json)
   - **Cloud Build 設定檔位置**：`/cloudbuild.yaml`
4. 建立 `cloudbuild.yaml` 檔案（如果尚未存在）：
   ```yaml
   steps:
     # 建置 Docker 映像檔
     - name: 'gcr.io/cloud-builders/docker'
       args: ['build', '-t', 'gcr.io/bible-bot-project/bible-bot:latest', '.']
     
     # 推送映像檔到 Container Registry
     - name: 'gcr.io/cloud-builders/docker'
       args: ['push', 'gcr.io/bible-bot-project/bible-bot:latest']
     
     # 部署到 Cloud Run
     - name: 'gcr.io/cloud-builders/gcloud'
       args:
         - 'run'
         - 'deploy'
         - 'bible-bot'
         - '--image=gcr.io/bible-bot-project/bible-bot:latest'
         - '--platform=managed'
         - '--region=asia-east1'
         - '--allow-unauthenticated'
         - '--quiet'
   
   images:
     - 'gcr.io/bible-bot-project/bible-bot:latest'
   ```

## 驗證部署

部署完成後，請執行以下驗證步驟：

1. **檢查服務狀態**
   - 前往 [Cloud Run 控制台](https://console.cloud.google.com/run)
   - 確認 `bible-bot` 服務狀態為「正常」

2. **檢查日誌**
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" --limit 50
   ```

3. **測試新使用者註冊**
   - 使用新的 LINE 帳號加入 Bot (@993uocot)
   - 確認收到歡迎訊息和計畫選擇按鈕
   - 檢查 Firestore 中是否成功建立使用者記錄

4. **檢查管理後台**
   - 前往 https://bible-bot-741437082833.asia-east1.run.app/admin
   - 登入 (admin / bible2025)
   - 確認新使用者出現在列表中

## 故障排除

### 如果部署失敗

1. 檢查 Cloud Build 日誌：
   ```bash
   gcloud builds list --limit=5
   gcloud builds log [BUILD_ID]
   ```

2. 檢查 Cloud Run 日誌：
   ```bash
   gcloud logging read "resource.type=cloud_run_revision" --limit 100
   ```

3. 確認環境變數已正確設定：
   - LINE_CHANNEL_ACCESS_TOKEN
   - LINE_CHANNEL_SECRET
   - GOOGLE_APPLICATION_CREDENTIALS

### 如果新使用者仍無法註冊

1. 檢查 Firestore 權限設定
2. 確認程式碼已正確更新（檢查 GitHub commit）
3. 查看即時日誌以找出錯誤訊息

## Git Commit 資訊

- **Commit ID**: b9746ac
- **Commit Message**: Fix: Convert date.today() to datetime.now() for Firestore compatibility
- **修改檔案**: database.py, main.py
- **推送時間**: 2025-11-01

## 聯絡資訊

如有問題，請檢查：
- GitHub Issues: https://github.com/ricklin0821/bible-reading-line-bot/issues
- Cloud Run 日誌: https://console.cloud.google.com/run/detail/asia-east1/bible-bot/logs
