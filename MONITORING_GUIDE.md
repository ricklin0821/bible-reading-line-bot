# 監控和日誌查詢指南

## 📋 目錄

1. [快速檢查部署狀態](#快速檢查部署狀態)
2. [查看建置日誌](#查看建置日誌)
3. [查看應用程式日誌](#查看應用程式日誌)
4. [常見錯誤排查](#常見錯誤排查)
5. [監控儀表板](#監控儀表板)

---

## 🚀 快速檢查部署狀態

### 一鍵檢查腳本

建立快速檢查腳本：

```bash
#!/bin/bash
# check-status.sh - 快速檢查部署狀態

echo "========================================="
echo "📊 Bible Bot 部署狀態檢查"
echo "========================================="
echo ""

# 1. 檢查最近的建置
echo "1️⃣  最近 5 次建置："
echo "---"
gcloud builds list --limit=5 --format="table(id,status,createTime,duration)"
echo ""

# 2. 檢查 Cloud Run 服務狀態
echo "2️⃣  Cloud Run 服務狀態："
echo "---"
gcloud run services describe bible-bot --region=asia-east1 --format="value(status.url,status.conditions[0].status,status.latestReadyRevisionName)"
echo ""

# 3. 檢查最近的錯誤
echo "3️⃣  最近 10 個錯誤："
echo "---"
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND severity>=ERROR" --limit=10 --format="table(timestamp,severity,textPayload)"
echo ""

echo "========================================="
echo "✅ 檢查完成"
echo "========================================="
```

儲存為 `check-status.sh` 並執行：

```bash
chmod +x check-status.sh
./check-status.sh
```

---

## 📝 查看建置日誌

### 1. 查看最近的建置

```bash
# 列出最近 10 次建置
gcloud builds list --limit=10
```

輸出範例：
```
ID                                    CREATE_TIME                DURATION  SOURCE                                                                                  STATUS
a1b2c3d4-e5f6-7890-abcd-ef1234567890  2025-11-01T10:30:00+00:00  3M45S     ricklin0821/bible-reading-line-bot@master (abc123)                                      SUCCESS
```

### 2. 查看特定建置的詳細資訊

```bash
# 使用建置 ID 查看詳情
gcloud builds describe BUILD_ID
```

### 3. 即時查看建置日誌

```bash
# 即時串流最新建置的日誌
gcloud builds log --stream

# 查看特定建置的日誌
gcloud builds log BUILD_ID
```

### 4. 查看建置失敗的原因

```bash
# 只顯示失敗的建置
gcloud builds list --filter="status=FAILURE" --limit=5

# 查看失敗建置的日誌
gcloud builds log FAILED_BUILD_ID
```

### 5. 使用 Cloud Console 查看

前往 Cloud Build 歷史記錄：
https://console.cloud.google.com/cloud-build/builds?project=bible-bot-project

優點：
- ✅ 視覺化介面
- ✅ 可以看到每個步驟的執行時間
- ✅ 可以下載完整日誌
- ✅ 可以重新執行建置

---

## 📊 查看應用程式日誌

### 1. 查看 Cloud Run 即時日誌

```bash
# 即時串流日誌
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot"

# 只看錯誤
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND severity>=ERROR"
```

### 2. 查看歷史日誌

```bash
# 查看最近 50 條日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" --limit=50

# 查看最近 1 小時的日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND timestamp>=2025-11-01T09:00:00Z" --limit=100

# 查看特定時間範圍的日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND timestamp>='2025-11-01T00:00:00Z' AND timestamp<'2025-11-01T23:59:59Z'" --limit=1000
```

### 3. 查看特定類型的日誌

```bash
# 查看錯誤日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND severity>=ERROR" --limit=50

# 查看警告日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND severity=WARNING" --limit=50

# 查看包含特定關鍵字的日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'Firestore'" --limit=50
```

### 4. 匯出日誌到檔案

```bash
# 匯出為 JSON
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" --limit=1000 --format=json > logs.json

# 匯出為 CSV
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" --limit=1000 --format="csv(timestamp,severity,textPayload)" > logs.csv

# 匯出為純文字
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" --limit=1000 --format="value(textPayload)" > logs.txt
```

### 5. 使用 Cloud Console 查看

前往 Cloud Run 日誌頁面：
https://console.cloud.google.com/run/detail/asia-east1/bible-bot/logs?project=bible-bot-project

優點：
- ✅ 視覺化介面
- ✅ 可以按時間、嚴重性篩選
- ✅ 可以搜尋關鍵字
- ✅ 可以查看請求追蹤

---

## 🔍 常見錯誤排查

### 錯誤 1: 新使用者無法註冊

**症狀**：
- 使用者加入 Bot 後沒有反應
- 日誌中出現 Firestore 錯誤

**查詢日誌**：
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'date.today'" --limit=10
```

**解決方法**：
- 檢查是否已修復 `date.today()` 問題
- 確認已重新部署最新版本

---

### 錯誤 2: 測驗生成失敗

**症狀**：
- 使用者點擊「完成讀經」後出現錯誤
- 日誌中出現「The query requires an index」

**查詢日誌**：
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'index'" --limit=10
```

**解決方法**：
- 檢查 Firestore 索引是否已建立完成
- 前往 https://console.cloud.google.com/firestore/indexes?project=bible-bot-project

---

### 錯誤 3: LINE Webhook 驗證失敗

**症狀**：
- 使用者發送訊息沒有回應
- 日誌中出現 400 或 401 錯誤

**查詢日誌**：
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND (textPayload=~'400' OR textPayload=~'401')" --limit=10
```

**解決方法**：
- 檢查 LINE Channel Secret 是否正確
- 檢查 LINE Channel Access Token 是否正確
- 確認 Webhook URL 設定正確

---

### 錯誤 4: Firestore 連線失敗

**症狀**：
- 所有功能都無法使用
- 日誌中出現「Firestore connection failed」

**查詢日誌**：
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'Firestore'" --limit=10
```

**解決方法**：
- 檢查服務帳戶權限
- 確認 Firestore 資料庫狀態正常
- 檢查網路連線

---

### 錯誤 5: 記憶體不足（OOM）

**症狀**：
- 服務突然重啟
- 日誌中出現「Memory limit exceeded」

**查詢日誌**：
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'memory'" --limit=10
```

**解決方法**：
- 增加 Cloud Run 記憶體限制
- 優化程式碼，減少記憶體使用

---

## 📈 監控儀表板

### 1. Cloud Run 內建監控

前往 Cloud Run 監控頁面：
https://console.cloud.google.com/run/detail/asia-east1/bible-bot/metrics?project=bible-bot-project

可以看到：
- **請求數**：每秒請求數（RPS）
- **延遲**：P50、P95、P99 延遲
- **錯誤率**：4xx、5xx 錯誤率
- **CPU 使用率**：容器 CPU 使用情況
- **記憶體使用率**：容器記憶體使用情況
- **實例數**：運行中的實例數量

### 2. 建立自訂儀表板

前往 Cloud Monitoring：
https://console.cloud.google.com/monitoring/dashboards?project=bible-bot-project

#### 步驟 1: 建立新儀表板

1. 點擊「**建立儀表板**」
2. 輸入名稱：`Bible Bot 監控`
3. 點擊「**新增圖表**」

#### 步驟 2: 新增關鍵指標

**圖表 1: 請求數**
- **資源類型**：Cloud Run Revision
- **指標**：`Request count`
- **篩選器**：`service_name = bible-bot`
- **聚合**：Sum

**圖表 2: 錯誤率**
- **資源類型**：Cloud Run Revision
- **指標**：`Request count`
- **篩選器**：`service_name = bible-bot AND response_code_class = 5xx`
- **聚合**：Rate

**圖表 3: 延遲**
- **資源類型**：Cloud Run Revision
- **指標**：`Request latencies`
- **篩選器**：`service_name = bible-bot`
- **聚合**：99th percentile

**圖表 4: 記憶體使用率**
- **資源類型**：Cloud Run Revision
- **指標**：`Memory utilization`
- **篩選器**：`service_name = bible-bot`
- **聚合**：Mean

**圖表 5: CPU 使用率**
- **資源類型**：Cloud Run Revision
- **指標**：`CPU utilization`
- **篩選器**：`service_name = bible-bot`
- **聚合**：Mean

**圖表 6: 實例數**
- **資源類型**：Cloud Run Revision
- **指標**：`Instance count`
- **篩選器**：`service_name = bible-bot`
- **聚合**：Mean

### 3. 設定警示

#### 警示 1: 錯誤率過高

1. 前往「**警示**」→「**建立政策**」
2. **條件**：
   - **資源類型**：Cloud Run Revision
   - **指標**：Request count
   - **篩選器**：`service_name = bible-bot AND response_code_class = 5xx`
   - **條件**：Any time series violates
   - **閾值**：> 10（10 個錯誤）
   - **持續時間**：1 分鐘
3. **通知頻道**：Email、Slack、LINE
4. **名稱**：`Bible Bot - 錯誤率過高`

#### 警示 2: 延遲過高

1. **條件**：
   - **資源類型**：Cloud Run Revision
   - **指標**：Request latencies
   - **篩選器**：`service_name = bible-bot`
   - **條件**：99th percentile > 3000ms
   - **持續時間**：5 分鐘
2. **通知頻道**：Email
3. **名稱**：`Bible Bot - 延遲過高`

#### 警示 3: 服務停機

1. **條件**：
   - **資源類型**：Cloud Run Revision
   - **指標**：Request count
   - **篩選器**：`service_name = bible-bot`
   - **條件**：Absent for 5 minutes
2. **通知頻道**：Email、LINE
3. **名稱**：`Bible Bot - 服務停機`

---

## 📊 日誌查詢範例

### 查詢 1: 查看特定使用者的操作

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'USER_ID'" --limit=50
```

### 查詢 2: 查看 LINE Webhook 請求

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'webhook'" --limit=50
```

### 查詢 3: 查看 Firestore 查詢

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'Firestore'" --limit=50
```

### 查詢 4: 查看測驗生成

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND textPayload=~'quiz'" --limit=50
```

### 查詢 5: 查看錯誤堆疊追蹤

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND severity=ERROR" --limit=10 --format="value(textPayload)"
```

---

## 🔧 進階技巧

### 1. 使用日誌探索器

前往日誌探索器：
https://console.cloud.google.com/logs/query?project=bible-bot-project

**優點**：
- ✅ 強大的查詢語法
- ✅ 視覺化時間軸
- ✅ 可以儲存查詢
- ✅ 可以建立警示

**常用查詢**：

```
# 查看所有錯誤
resource.type="cloud_run_revision"
resource.labels.service_name="bible-bot"
severity>=ERROR

# 查看特定時間範圍
resource.type="cloud_run_revision"
resource.labels.service_name="bible-bot"
timestamp>="2025-11-01T00:00:00Z"
timestamp<"2025-11-01T23:59:59Z"

# 查看包含特定關鍵字
resource.type="cloud_run_revision"
resource.labels.service_name="bible-bot"
textPayload=~"Firestore"

# 查看特定 HTTP 狀態碼
resource.type="cloud_run_revision"
resource.labels.service_name="bible-bot"
httpRequest.status=500
```

### 2. 匯出日誌到 BigQuery

如果需要長期保存日誌或進行複雜分析：

1. 前往「**日誌路由器**」
2. 點擊「**建立接收器**」
3. **接收器名稱**：`bible-bot-logs-to-bigquery`
4. **接收器目的地**：BigQuery dataset
5. **篩選器**：
   ```
   resource.type="cloud_run_revision"
   resource.labels.service_name="bible-bot"
   ```
6. 點擊「**建立接收器**」

然後可以使用 BigQuery SQL 查詢：

```sql
SELECT
  timestamp,
  severity,
  textPayload
FROM
  `bible-bot-project.logs.cloud_run_revision_*`
WHERE
  resource.labels.service_name = 'bible-bot'
  AND severity = 'ERROR'
ORDER BY
  timestamp DESC
LIMIT 100
```

### 3. 設定日誌保留政策

預設日誌保留 30 天，如需更長時間：

1. 前往「**日誌儲存空間**」
2. 選擇 `_Default` bucket
3. 點擊「**編輯**」
4. 設定「**保留期限**」：例如 90 天
5. 點擊「**更新**」

---

## 📱 手機監控

### 使用 Google Cloud App

1. 下載「**Google Cloud**」App（iOS/Android）
2. 登入您的 Google 帳號
3. 選擇專案：`bible-bot-project`
4. 可以查看：
   - Cloud Run 服務狀態
   - Cloud Build 建置歷史
   - 警示通知
   - 日誌（基本）

### 使用 LINE Notify

設定 LINE Notify 後，所有警示都會發送到您的 LINE：
- ✅ 建置失敗通知
- ✅ 服務錯誤警示
- ✅ 效能警示

---

## 📝 監控檢查清單

### 每日檢查

- [ ] 查看 Cloud Run 服務狀態
- [ ] 檢查是否有錯誤日誌
- [ ] 確認使用者可以正常使用

### 每週檢查

- [ ] 查看 Cloud Build 建置歷史
- [ ] 檢查效能指標（延遲、錯誤率）
- [ ] 查看資源使用情況（CPU、記憶體）
- [ ] 檢查 Firestore 使用量

### 每月檢查

- [ ] 審查警示政策
- [ ] 檢查日誌保留設定
- [ ] 優化效能瓶頸
- [ ] 更新文件

---

## 🆘 緊急情況處理

### 服務完全停機

1. **立即回滾到上一個版本**：
   ```bash
   # 查看修訂版本
   gcloud run revisions list --service=bible-bot --region=asia-east1
   
   # 回滾到上一個版本
   gcloud run services update-traffic bible-bot \
     --to-revisions=PREVIOUS_REVISION=100 \
     --region=asia-east1
   ```

2. **查看錯誤日誌**：
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND severity=ERROR" --limit=50
   ```

3. **通知使用者**（如果需要）

### 大量錯誤

1. **暫時停止自動部署**：
   - 前往 Cloud Build 觸發器
   - 停用觸發器

2. **分析錯誤原因**：
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND severity=ERROR" --limit=100 --format="value(textPayload)"
   ```

3. **修復並測試**

4. **重新啟用自動部署**

---

**記得定期檢查監控！** 📊
