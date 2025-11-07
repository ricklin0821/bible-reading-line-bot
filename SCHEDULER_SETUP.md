# 設定每日自動發送荒漠甘泉圖片

## 方案：使用 Cloud Scheduler + HTTP 端點

### 步驟 1：在 main.py 中添加觸發端點

已在 `main.py` 中添加 `/trigger/daily-devotional` 端點。

### 步驟 2：設定 Cloud Scheduler

執行以下命令創建 Cloud Scheduler Job：

```bash
# 創建 Cloud Scheduler Job
gcloud scheduler jobs create http daily-devotional-sender \
    --location=asia-east1 \
    --schedule="30 12 * * *" \
    --time-zone="Asia/Taipei" \
    --uri="https://bible-bot-741437082833.asia-east1.run.app/trigger/daily-devotional" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --oidc-service-account-email="YOUR_SERVICE_ACCOUNT@YOUR_PROJECT.iam.gserviceaccount.com" \
    --oidc-token-audience="https://bible-bot-741437082833.asia-east1.run.app"
```

**說明：**
- `--schedule="30 12 * * *"` - 每天中午 12:30 執行
- `--time-zone="Asia/Taipei"` - 台北時區
- `--uri` - Cloud Run 服務的 URL
- `--oidc-service-account-email` - 需要替換為您的服務帳號

### 步驟 3：測試

手動觸發測試：

```bash
gcloud scheduler jobs run daily-devotional-sender --location=asia-east1
```

或使用 curl 測試：

```bash
curl -X POST https://bible-bot-741437082833.asia-east1.run.app/trigger/daily-devotional \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

### 步驟 4：查看日誌

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" --limit=50
```

## 注意事項

1. **服務帳號權限**：確保服務帳號有權限調用 Cloud Run
2. **Cloud Run 驗證**：端點需要驗證，使用 OIDC token
3. **費用**：Cloud Scheduler 每月前 3 個 job 免費
4. **時區**：確認時區設定正確（Asia/Taipei）

## 替代方案：使用環境變數控制

如果不想使用 Cloud Scheduler，可以：
1. 使用外部 cron 服務（如 cron-job.org）
2. 使用 GitHub Actions 定時觸發
3. 使用其他第三方排程服務
