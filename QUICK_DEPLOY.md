# 快速部署指南

## 🚀 最簡單的部署方式

### 使用 Google Cloud Shell（推薦，無需本地安裝）

1. **開啟 Cloud Shell**
   - 前往 https://console.cloud.google.com
   - 點擊右上角的 **Cloud Shell** 圖示（>_）

2. **執行以下指令**（複製貼上即可）
   ```bash
   # 設定專案
   gcloud config set project bible-bot-project
   
   # 克隆最新程式碼
   rm -rf bible-reading-line-bot
   git clone https://github.com/ricklin0821/bible-reading-line-bot.git
   cd bible-reading-line-bot
   
   # 建置並部署（一行指令完成）
   gcloud builds submit --tag gcr.io/bible-bot-project/bible-bot:latest . && \
   gcloud run deploy bible-bot \
     --image gcr.io/bible-bot-project/bible-bot:latest \
     --platform managed \
     --region asia-east1 \
     --allow-unauthenticated \
     --quiet
   ```

3. **等待完成**
   - 建置時間：約 2-3 分鐘
   - 看到 "Service [bible-bot] revision [xxx] has been deployed" 表示成功

---

## 🔧 設定自動部署（一次設定，永久自動）

### 步驟 1: 啟用 Cloud Build API

```bash
gcloud services enable cloudbuild.googleapis.com
```

### 步驟 2: 連結 GitHub 儲存庫

1. 前往 https://console.cloud.google.com/cloud-build/triggers
2. 點擊「**連結儲存庫**」
3. 選擇「**GitHub**」
4. 授權並選擇 `ricklin0821/bible-reading-line-bot`

### 步驟 3: 建立觸發器

1. 點擊「**建立觸發器**」
2. 設定如下：
   - **名稱**：`auto-deploy-on-push`
   - **事件**：推送到分支
   - **來源**：`ricklin0821/bible-reading-line-bot`
   - **分支**：`^master$`
   - **建置設定**：Cloud Build 設定檔 (yaml 或 json)
   - **Cloud Build 設定檔位置**：`/cloudbuild.yaml`
3. 點擊「**建立**」

### 完成！

從現在開始，每次推送程式碼到 GitHub master 分支，就會自動建置並部署到 Cloud Run！

---

## ✅ 驗證部署成功

### 1. 檢查服務狀態

前往 https://console.cloud.google.com/run/detail/asia-east1/bible-bot

應該看到：
- ✅ 狀態：正常
- ✅ 最新修訂版本正在接收流量

### 2. 測試新使用者註冊

1. 使用**新的 LINE 帳號**（或請朋友幫忙測試）
2. 加入 Bot：https://line.me/R/ti/p/@993uocot
3. 應該會收到：
   - ✅ 歡迎訊息
   - ✅ 計畫選擇按鈕（順序讀經 / 平衡讀經）

### 3. 檢查管理後台

1. 前往 https://bible-bot-741437082833.asia-east1.run.app/admin
2. 登入：`admin` / `bible2025`
3. 應該看到：
   - ✅ 新使用者出現在列表中
   - ✅ `start_date` 欄位有正確的日期時間

### 4. 查看日誌（如果有問題）

```bash
# 查看最新 50 條日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" \
  --limit 50 \
  --format "table(timestamp, textPayload)"

# 查看錯誤日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND severity>=ERROR" \
  --limit 20
```

---

## 🐛 故障排除

### 問題 1: 建置失敗

**錯誤訊息**：`ERROR: failed to solve: process "/bin/sh -c pip install..."`

**解決方法**：
```bash
# 檢查 requirements.txt 是否正確
cat requirements.txt

# 確認 Dockerfile 沒有語法錯誤
cat Dockerfile
```

### 問題 2: 部署成功但 Bot 無回應

**檢查項目**：
1. LINE Webhook URL 是否正確設定
2. 環境變數是否正確（LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET）
3. 查看 Cloud Run 日誌

**查看日誌**：
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" --limit 100
```

### 問題 3: 新使用者仍無法註冊

**檢查項目**：
1. 確認程式碼已更新（檢查 GitHub 最新 commit）
2. 確認部署的映像檔是最新的
3. 查看錯誤日誌

**強制重新部署**：
```bash
cd bible-reading-line-bot
git pull origin master
gcloud builds submit --tag gcr.io/bible-bot-project/bible-bot:latest .
gcloud run deploy bible-bot --image gcr.io/bible-bot-project/bible-bot:latest --platform managed --region asia-east1 --allow-unauthenticated --quiet
```

---

## 📝 本次修復內容

### 修復的錯誤
```
TypeError: ('Cannot convert to a Firestore Value', datetime.date(2025, 11, 1), 'Invalid type', <class 'datetime.date'>)
```

### 修改的檔案
- `database.py` (1 處)
- `main.py` (6 處)

### 修改內容
將所有 `date.today()` 改為 `datetime.now()` 或 `datetime.now().date()`，確保 Firestore 可以正確儲存日期時間欄位。

### Git Commit
- **Commit ID**: `b9746ac`
- **Commit Message**: "Fix: Convert date.today() to datetime.now() for Firestore compatibility"

---

## 📞 需要協助？

如果部署過程中遇到問題：

1. **查看詳細部署指南**：`DEPLOYMENT_GUIDE.md`
2. **檢查 Cloud Build 日誌**：https://console.cloud.google.com/cloud-build/builds
3. **檢查 Cloud Run 日誌**：https://console.cloud.google.com/run/detail/asia-east1/bible-bot/logs
4. **檢查 GitHub Issues**：https://github.com/ricklin0821/bible-reading-line-bot/issues

---

**祝部署順利！🎉**
