# 自動部署與通知機制總覽

## 🎯 目標

建立完整的 CI/CD 流程，確保：
1. ✅ 每次推送程式碼到 GitHub 自動部署
2. ✅ 部署失敗時立即收到通知
3. ✅ 可以快速查看部署狀態和日誌
4. ✅ 出現問題時能快速回滾

---

## 📦 已建立的檔案

### 1. 核心設定檔案

| 檔案 | 用途 | 位置 |
|------|------|------|
| `cloudbuild.yaml` | Cloud Build 建置設定 | 專案根目錄 |
| `setup-notifications.sh` | 通知設定腳本 | 專案根目錄 |
| `check-status.sh` | 快速狀態檢查腳本 | 專案根目錄 |

### 2. 文件檔案

| 檔案 | 內容 | 位置 |
|------|------|------|
| `AUTO_DEPLOY_GUIDE.md` | 自動部署完整指南 | 專案根目錄 |
| `MONITORING_GUIDE.md` | 監控和日誌查詢指南 | 專案根目錄 |
| `AUTO_DEPLOY_SUMMARY.md` | 本文件（總覽） | 專案根目錄 |

---

## 🚀 快速開始（3 步驟）

### 步驟 1: 設定 Cloud Build 觸發器

**方法 A: 使用 Google Cloud Console（推薦）**

1. 前往 https://console.cloud.google.com/cloud-build/triggers?project=bible-bot-project
2. 點擊「**建立觸發器**」
3. 設定：
   - **名稱**：`bible-bot-auto-deploy`
   - **事件**：推送到分支
   - **來源**：`ricklin0821/bible-reading-line-bot`
   - **分支**：`^master$`
   - **建置設定**：Cloud Build 設定檔案 (`/cloudbuild.yaml`)
4. 點擊「**建立**」

**方法 B: 使用 gcloud CLI**

```bash
gcloud builds triggers create github \
  --name="bible-bot-auto-deploy" \
  --repo-name="bible-reading-line-bot" \
  --repo-owner="ricklin0821" \
  --branch-pattern="^master$" \
  --build-config="cloudbuild.yaml" \
  --region="asia-east1"
```

---

### 步驟 2: 設定失敗通知（選擇一種或多種）

#### 選項 A: Email 通知（最簡單）

1. 前往 https://console.cloud.google.com/cloud-build/settings/notifications?project=bible-bot-project
2. 點擊「**建立通知器**」
3. 選擇「**Email**」
4. 輸入您的 Email
5. 勾選「**建置失敗**」和「**建置逾時**」
6. 點擊「**儲存**」

✅ **完成！** 現在建置失敗時會收到 Email

---

#### 選項 B: LINE Notify 通知（推薦）

1. **取得 LINE Notify Token**：
   - 前往 https://notify-bot.line.me/
   - 登入並發行權杖
   - 選擇「1對1聊天」
   - 複製權杖

2. **執行設定腳本**：
   ```bash
   cd /path/to/bible-reading-line-bot
   ./setup-notifications.sh
   ```

3. **按照提示操作**：
   - 選擇「y」設定 LINE Notify
   - 貼上 LINE Notify Token
   - 等待 Cloud Function 部署完成

✅ **完成！** 現在建置失敗時會收到 LINE 通知

---

#### 選項 C: Slack 通知（適合團隊）

1. **建立 Slack Incoming Webhook**：
   - 前往 https://api.slack.com/messaging/webhooks
   - 建立 Slack App
   - 啟用 Incoming Webhooks
   - 選擇頻道並複製 Webhook URL

2. **執行設定腳本**：
   ```bash
   cd /path/to/bible-reading-line-bot
   ./setup-notifications.sh
   ```

3. **按照提示操作**：
   - 選擇「y」設定 Slack 通知
   - 貼上 Slack Webhook URL
   - 等待 Cloud Function 部署完成

✅ **完成！** 現在建置失敗時會發送到 Slack 頻道

---

### 步驟 3: 測試自動部署

1. **修改程式碼並推送**：
   ```bash
   # 修改任何檔案
   echo "# Test auto deploy" >> README.md
   
   # 提交並推送
   git add .
   git commit -m "Test: Auto deploy"
   git push origin master
   ```

2. **查看建置狀態**：
   - 前往 https://console.cloud.google.com/cloud-build/builds?project=bible-bot-project
   - 或執行：`gcloud builds list --limit=1`

3. **等待建置完成**（約 3-5 分鐘）

4. **檢查是否收到通知**（如果建置失敗）

✅ **完成！** 自動部署已設定完成

---

## 📊 日常使用

### 快速檢查狀態

```bash
cd /path/to/bible-reading-line-bot
./check-status.sh
```

這會顯示：
- ✅ 最近 5 次建置狀態
- ✅ Cloud Run 服務狀態
- ✅ 健康檢查結果
- ✅ 最近的錯誤（如果有）
- ✅ 快速連結

---

### 查看建置日誌

```bash
# 查看最近的建置
gcloud builds list --limit=5

# 即時查看建置日誌
gcloud builds log --stream

# 查看特定建置的日誌
gcloud builds log BUILD_ID
```

---

### 查看應用程式日誌

```bash
# 即時查看日誌
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot"

# 查看錯誤日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND severity>=ERROR" --limit=20

# 查看最近 50 條日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" --limit=50
```

---

### 手動觸發部署

```bash
# 觸發建置
gcloud builds triggers run bible-bot-auto-deploy --branch=master

# 或直接部署（不經過 Cloud Build）
gcloud run deploy bible-bot \
  --image gcr.io/bible-bot-project/bible-bot:latest \
  --region asia-east1 \
  --allow-unauthenticated
```

---

## 🔔 通知機制說明

### 通知類型

| 通知方式 | 設定難度 | 即時性 | 適用場景 |
|---------|---------|--------|---------|
| Email | ⭐ 簡單 | ⏱️ 1-2 分鐘 | 個人使用 |
| LINE Notify | ⭐⭐ 中等 | ⚡ 即時 | 個人使用，手機通知 |
| Slack | ⭐⭐ 中等 | ⚡ 即時 | 團隊協作 |
| Pub/Sub | ⭐⭐⭐ 複雜 | ⚡ 即時 | 自訂整合 |

### 通知內容

所有通知都會包含：
- ✅ 建置狀態（成功/失敗/逾時）
- ✅ 儲存庫名稱
- ✅ 分支名稱
- ✅ Commit SHA
- ✅ 建置 ID
- ✅ 日誌連結

### 通知觸發條件

預設只在以下情況發送通知：
- ❌ **建置失敗**
- ⏰ **建置逾時**

如果想要收到成功通知，可以修改：
- Email: 在通知設定中勾選「建置成功」
- LINE/Slack: 修改 Cloud Function 程式碼中的條件

---

## 🛠️ 自訂設定

### 修改建置流程

編輯 `cloudbuild.yaml`：

```yaml
steps:
  # 步驟 1: 建置
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/bible-bot-project/bible-bot:$SHORT_SHA', '.']
  
  # 步驟 2: 推送
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/bible-bot-project/bible-bot:$SHORT_SHA']
  
  # 步驟 3: 部署
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['run', 'deploy', 'bible-bot', '--image=gcr.io/bible-bot-project/bible-bot:$SHORT_SHA', '--region=asia-east1']
  
  # 步驟 4: 健康檢查
  - name: 'gcr.io/cloud-builders/curl'
    args: ['-f', 'https://bible-bot-741437082833.asia-east1.run.app/']
```

### 修改通知訊息

編輯 Cloud Function 程式碼（在 `setup-notifications.sh` 中）：

**LINE Notify**：
```python
message = f"""
🤖 Bible Bot 部署通知

狀態: {status}
分支: {branch}
Commit: {build_id[:7]}

查看詳情: {log_url}
"""
```

**Slack**：
```python
message = {
    'text': f'Bible Bot 部署 {status}',
    'attachments': [{
        'color': color,
        'fields': [
            {'title': 'Branch', 'value': branch},
            {'title': 'Build ID', 'value': build_id},
        ]
    }]
}
```

---

## 📈 監控建議

### 每日檢查

```bash
# 執行快速檢查
./check-status.sh
```

### 每週檢查

1. 查看 Cloud Build 成功率
2. 檢查 Cloud Run 效能指標
3. 查看錯誤日誌趨勢

### 每月檢查

1. 審查警示政策
2. 優化建置時間
3. 更新文件

---

## 🚨 故障排除

### 問題 1: 觸發器沒有執行

**檢查步驟**：

1. 確認觸發器已啟用：
   ```bash
   gcloud builds triggers list
   ```

2. 檢查 GitHub Webhook：
   - 前往 GitHub 儲存庫設定
   - 檢查 Webhooks 狀態

3. 手動測試觸發器：
   ```bash
   gcloud builds triggers run bible-bot-auto-deploy --branch=master
   ```

---

### 問題 2: 建置失敗

**檢查步驟**：

1. 查看建置日誌：
   ```bash
   gcloud builds log BUILD_ID
   ```

2. 常見原因：
   - Dockerfile 錯誤
   - 依賴套件安裝失敗
   - 測試失敗
   - 權限不足

3. 本地測試：
   ```bash
   docker build -t bible-bot:test .
   docker run -p 8080:8080 bible-bot:test
   ```

---

### 問題 3: 沒有收到通知

**檢查步驟**：

1. 檢查 Email 垃圾郵件

2. 測試 Cloud Function：
   ```bash
   gcloud pubsub topics publish cloud-build-notifications \
     --message '{"status":"FAILURE","id":"test"}'
   ```

3. 查看 Cloud Function 日誌：
   ```bash
   gcloud functions logs read cloud-build-line-notifier --limit=20
   ```

---

### 問題 4: 部署成功但服務異常

**檢查步驟**：

1. 查看 Cloud Run 日誌：
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND severity>=ERROR" --limit=20
   ```

2. 檢查環境變數：
   - 前往 Cloud Run 服務設定
   - 確認所有環境變數都已設定

3. 回滾到上一個版本：
   ```bash
   gcloud run revisions list --service=bible-bot --region=asia-east1
   gcloud run services update-traffic bible-bot \
     --to-revisions=PREVIOUS_REVISION=100 \
     --region=asia-east1
   ```

---

## 📚 相關文件

| 文件 | 內容 |
|------|------|
| [AUTO_DEPLOY_GUIDE.md](./AUTO_DEPLOY_GUIDE.md) | 詳細的自動部署設定指南 |
| [MONITORING_GUIDE.md](./MONITORING_GUIDE.md) | 監控和日誌查詢指南 |
| [FIRESTORE_INDEX_GUIDE.md](./FIRESTORE_INDEX_GUIDE.md) | Firestore 索引建立指南 |
| [QUICK_DEPLOY.md](./QUICK_DEPLOY.md) | 快速部署指南 |
| [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) | 完整部署指南 |

---

## 🎯 下一步

1. ✅ 設定 Cloud Build 觸發器
2. ✅ 設定至少一種通知方式
3. ✅ 測試自動部署
4. ✅ 設定監控警示
5. ✅ 定期檢查狀態

---

## 📞 需要協助？

如果遇到問題：

1. **查看文件**：詳細的設定步驟都在 `AUTO_DEPLOY_GUIDE.md`
2. **查看日誌**：大部分問題都能從日誌中找到原因
3. **執行檢查腳本**：`./check-status.sh`
4. **查看 Cloud Console**：視覺化介面更容易理解

---

**祝您部署順利！** 🚀
