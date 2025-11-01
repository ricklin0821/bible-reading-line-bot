# Cloud Build 自動部署完整指南

## 📋 目錄

1. [設定 Cloud Build 觸發器](#設定-cloud-build-觸發器)
2. [設定部署失敗通知](#設定部署失敗通知)
3. [監控部署狀態](#監控部署狀態)
4. [故障排除](#故障排除)

---

## 🚀 設定 Cloud Build 觸發器

### 方法 1: 使用 Google Cloud Console（推薦）

#### 步驟 1: 前往 Cloud Build 觸發器頁面

https://console.cloud.google.com/cloud-build/triggers?project=bible-bot-project

#### 步驟 2: 建立觸發器

1. 點擊「**建立觸發器**」

2. **基本設定**：
   - **名稱**：`bible-bot-auto-deploy`
   - **說明**：`自動部署 Bible Reading LINE Bot`
   - **區域**：`asia-east1 (台灣)`

3. **事件設定**：
   - 選擇「**推送到分支**」
   - **來源**：選擇「**1st gen**」

4. **來源設定**：
   - **儲存庫**：選擇 `ricklin0821/bible-reading-line-bot`（需要先連結 GitHub）
   - **分支**：`^master$`（正規表示式，只匹配 master 分支）

5. **建置設定**：
   - **類型**：選擇「**Cloud Build 設定檔案**」
   - **位置**：`/cloudbuild.yaml`

6. **進階設定**（可選）：
   - **服務帳戶**：使用預設
   - **替代變數**：無需設定（已在 cloudbuild.yaml 中定義）

7. 點擊「**建立**」

#### 步驟 3: 連結 GitHub（如果尚未連結）

如果您尚未連結 GitHub：

1. 在建立觸發器時，點擊「**連結新的儲存庫**」
2. 選擇「**GitHub (Cloud Build GitHub App)**」
3. 點擊「**驗證**」並登入 GitHub
4. 授權 Google Cloud Build 存取您的儲存庫
5. 選擇 `ricklin0821/bible-reading-line-bot`
6. 點擊「**連結儲存庫**」

---

### 方法 2: 使用 gcloud CLI

```bash
# 建立觸發器
gcloud builds triggers create github \
  --name="bible-bot-auto-deploy" \
  --repo-name="bible-reading-line-bot" \
  --repo-owner="ricklin0821" \
  --branch-pattern="^master$" \
  --build-config="cloudbuild.yaml" \
  --region="asia-east1"
```

---

## 📧 設定部署失敗通知

我們提供 **4 種通知方式**，您可以選擇一種或多種：

### 方法 1: Email 通知（最簡單，推薦）

#### 步驟 1: 前往 Cloud Build 通知設定

https://console.cloud.google.com/cloud-build/settings/notifications?project=bible-bot-project

#### 步驟 2: 建立 Email 通知器

1. 點擊「**建立通知器**」
2. 選擇「**Email**」
3. **通知器名稱**：`Build Failure Email`
4. **收件者**：輸入您的 Email（例如：`ricksgemini0857@gmail.com`）
5. **通知條件**：
   - ✅ **建置失敗**（必選）
   - ✅ **建置逾時**（建議）
   - ⬜ **建置成功**（可選，如果想收到成功通知）
6. 點擊「**儲存**」

**優點**：
- ✅ 設定最簡單
- ✅ 不需要額外程式碼
- ✅ 直接收到 Email 通知

**缺點**：
- ❌ 可能有延遲（通常 1-2 分鐘）
- ❌ 無法自訂訊息格式

---

### 方法 2: Slack 通知（推薦給團隊）

#### 步驟 1: 建立 Slack Incoming Webhook

1. 前往 https://api.slack.com/messaging/webhooks
2. 點擊「**Create your Slack app**」
3. 選擇「**From scratch**」
4. 輸入 App 名稱：`Cloud Build Notifier`
5. 選擇您的 Workspace
6. 前往「**Incoming Webhooks**」
7. 啟用「**Activate Incoming Webhooks**」
8. 點擊「**Add New Webhook to Workspace**」
9. 選擇要接收通知的頻道
10. 複製 Webhook URL（格式：`https://hooks.slack.com/services/...`）

#### 步驟 2: 執行通知設定腳本

```bash
cd /home/ubuntu/bible-reading-line-bot
./setup-notifications.sh
```

按照提示：
1. 選擇「**y**」設定 Slack 通知
2. 貼上 Slack Webhook URL
3. 等待 Cloud Function 部署完成

**優點**：
- ✅ 即時通知
- ✅ 團隊成員都能看到
- ✅ 可以自訂訊息格式
- ✅ 支援豐富的格式（顏色、連結等）

**缺點**：
- ❌ 需要 Slack Workspace
- ❌ 需要部署 Cloud Function

---

### 方法 3: LINE Notify 通知（推薦給個人）

#### 步驟 1: 取得 LINE Notify Token

1. 前往 https://notify-bot.line.me/
2. 登入您的 LINE 帳號
3. 點擊右上角「**個人頁面**」
4. 點擊「**發行權杖**」
5. 輸入權杖名稱：`Cloud Build 通知`
6. 選擇要接收通知的聊天室（建議選擇「**1對1聊天**」）
7. 點擊「**發行**」
8. **立即複製權杖**（只會顯示一次！）

#### 步驟 2: 執行通知設定腳本

```bash
cd /home/ubuntu/bible-reading-line-bot
./setup-notifications.sh
```

按照提示：
1. 選擇「**y**」設定 LINE Notify
2. 貼上 LINE Notify Token
3. 等待 Cloud Function 部署完成

**優點**：
- ✅ 即時通知到 LINE
- ✅ 不需要額外 App
- ✅ 手機上直接收到
- ✅ 設定簡單

**缺點**：
- ❌ 需要 LINE 帳號
- ❌ 需要部署 Cloud Function

---

### 方法 4: Pub/Sub + 自訂處理（進階）

如果您想要更靈活的通知方式，可以使用 Pub/Sub：

```bash
cd /home/ubuntu/bible-reading-line-bot
./setup-notifications.sh
```

這會建立：
- Pub/Sub 主題：`cloud-build-notifications`
- Pub/Sub 訂閱：`cloud-build-notifications-sub`

然後您可以：
1. 使用 Cloud Function 處理訊息
2. 使用 Cloud Run 接收訊息
3. 使用本地程式訂閱訊息

**優點**：
- ✅ 最靈活
- ✅ 可以整合到任何系統
- ✅ 可以自訂任何邏輯

**缺點**：
- ❌ 需要寫程式
- ❌ 設定最複雜

---

## 📊 監控部署狀態

### 1. Cloud Build 儀表板

前往 Cloud Build 歷史記錄頁面：
https://console.cloud.google.com/cloud-build/builds?project=bible-bot-project

您可以看到：
- ✅ 所有建置的歷史記錄
- ✅ 建置狀態（成功/失敗/進行中）
- ✅ 建置時間
- ✅ 觸發來源（commit、分支）

### 2. 使用 gcloud CLI 查看建置狀態

```bash
# 查看最近的建置
gcloud builds list --limit=10

# 查看特定建置的詳細資訊
gcloud builds describe BUILD_ID

# 即時查看建置日誌
gcloud builds log --stream BUILD_ID
```

### 3. 查看 Cloud Run 部署狀態

```bash
# 查看服務狀態
gcloud run services describe bible-bot --region=asia-east1

# 查看最近的修訂版本
gcloud run revisions list --service=bible-bot --region=asia-east1

# 查看服務日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" --limit=50
```

### 4. 設定監控警示

前往 Cloud Monitoring：
https://console.cloud.google.com/monitoring?project=bible-bot-project

建立警示政策：
1. 點擊「**警示**」→「**建立政策**」
2. 選擇指標：
   - **Cloud Run**：錯誤率、延遲、請求數
   - **Cloud Build**：建置失敗率
3. 設定條件：例如「錯誤率 > 5%」
4. 設定通知頻道：Email、Slack、LINE 等
5. 儲存政策

---

## 🔍 故障排除

### 問題 1: 觸發器沒有自動執行

**可能原因**：
- GitHub 連結未正確設定
- 分支名稱不匹配
- Webhook 未正確設定

**解決方法**：

1. **檢查觸發器狀態**：
   ```bash
   gcloud builds triggers list
   ```

2. **檢查 GitHub Webhook**：
   - 前往 GitHub 儲存庫設定
   - 點擊「**Webhooks**」
   - 確認有 Google Cloud Build 的 Webhook
   - 檢查「**Recent Deliveries**」是否有錯誤

3. **手動測試觸發器**：
   ```bash
   gcloud builds triggers run bible-bot-auto-deploy --branch=master
   ```

4. **檢查權限**：
   - 確認 Cloud Build 服務帳戶有權限存取 Cloud Run
   - 前往 IAM 頁面檢查權限

---

### 問題 2: 建置失敗但沒有收到通知

**可能原因**：
- 通知設定未正確配置
- Email 被過濾到垃圾郵件
- Cloud Function 部署失敗

**解決方法**：

1. **檢查 Email 通知設定**：
   ```bash
   gcloud builds triggers describe bible-bot-auto-deploy
   ```

2. **檢查垃圾郵件資料夾**

3. **測試 Pub/Sub 通知**：
   ```bash
   # 發送測試訊息
   gcloud pubsub topics publish cloud-build-notifications \
     --message '{"status":"FAILURE","id":"test-build","logUrl":"https://console.cloud.google.com/cloud-build/builds"}'
   ```

4. **檢查 Cloud Function 日誌**：
   ```bash
   gcloud functions logs read cloud-build-slack-notifier --limit=50
   gcloud functions logs read cloud-build-line-notifier --limit=50
   ```

---

### 問題 3: 建置成功但部署失敗

**可能原因**：
- Cloud Run 配置錯誤
- 環境變數未設定
- 映像檔有問題

**解決方法**：

1. **檢查建置日誌**：
   ```bash
   gcloud builds log --stream
   ```

2. **檢查 Cloud Run 日誌**：
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot AND severity>=ERROR" --limit=50
   ```

3. **手動測試映像檔**：
   ```bash
   # 拉取映像檔
   docker pull gcr.io/bible-bot-project/bible-bot:latest
   
   # 本地測試
   docker run -p 8080:8080 gcr.io/bible-bot-project/bible-bot:latest
   ```

4. **檢查環境變數**：
   - 前往 Cloud Run 服務設定
   - 確認所有必要的環境變數都已設定

---

### 問題 4: 建置時間過長

**可能原因**：
- Docker 層未快取
- 機器類型太小
- 網路速度慢

**解決方法**：

1. **啟用 Docker 層快取**（已在 `cloudbuild.yaml` 中設定）

2. **使用更大的機器類型**：
   在 `cloudbuild.yaml` 中已設定：
   ```yaml
   options:
     machineType: 'E2_HIGHCPU_8'
   ```

3. **優化 Dockerfile**：
   - 將不常變動的指令放在前面
   - 使用 `.dockerignore` 排除不必要的檔案

---

## 📝 常用指令速查

### Cloud Build

```bash
# 查看建置歷史
gcloud builds list --limit=10

# 查看建置詳情
gcloud builds describe BUILD_ID

# 即時查看建置日誌
gcloud builds log --stream

# 手動觸發建置
gcloud builds triggers run bible-bot-auto-deploy --branch=master

# 取消建置
gcloud builds cancel BUILD_ID
```

### Cloud Run

```bash
# 查看服務狀態
gcloud run services describe bible-bot --region=asia-east1

# 查看修訂版本
gcloud run revisions list --service=bible-bot --region=asia-east1

# 查看服務日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" --limit=50

# 手動部署
gcloud run deploy bible-bot \
  --image gcr.io/bible-bot-project/bible-bot:latest \
  --region asia-east1 \
  --allow-unauthenticated
```

### Pub/Sub

```bash
# 查看主題
gcloud pubsub topics list

# 查看訂閱
gcloud pubsub subscriptions list

# 發送測試訊息
gcloud pubsub topics publish cloud-build-notifications --message "test"

# 拉取訊息
gcloud pubsub subscriptions pull cloud-build-notifications-sub --auto-ack
```

### Cloud Functions

```bash
# 查看函數
gcloud functions list

# 查看函數日誌
gcloud functions logs read FUNCTION_NAME --limit=50

# 刪除函數
gcloud functions delete FUNCTION_NAME
```

---

## 🎯 最佳實踐

### 1. 使用多種通知方式

建議同時設定：
- ✅ **Email 通知**（主要）
- ✅ **LINE Notify**（即時）
- ✅ **Slack 通知**（團隊協作）

### 2. 定期檢查建置狀態

每週檢查一次 Cloud Build 儀表板，確保：
- 建置成功率 > 95%
- 建置時間穩定
- 沒有異常錯誤

### 3. 設定監控警示

為關鍵指標設定警示：
- Cloud Run 錯誤率 > 5%
- Cloud Run 延遲 > 3 秒
- Cloud Build 失敗率 > 10%

### 4. 保留建置日誌

Cloud Build 預設保留 90 天的日誌，如需更長時間：
- 將日誌匯出到 Cloud Storage
- 使用 Cloud Logging 的日誌保留政策

### 5. 使用 Git Tag 進行版本管理

建議使用 Git Tag 標記重要版本：

```bash
# 建立標籤
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# 建立 Tag 觸發器
gcloud builds triggers create github \
  --name="bible-bot-release" \
  --repo-name="bible-reading-line-bot" \
  --repo-owner="ricklin0821" \
  --tag-pattern="^v.*" \
  --build-config="cloudbuild.yaml"
```

---

## 📚 相關資源

- [Cloud Build 官方文件](https://cloud.google.com/build/docs)
- [Cloud Run 官方文件](https://cloud.google.com/run/docs)
- [Pub/Sub 官方文件](https://cloud.google.com/pubsub/docs)
- [Cloud Functions 官方文件](https://cloud.google.com/functions/docs)
- [LINE Notify API](https://notify-bot.line.me/doc/)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)

---

## 🆘 需要協助？

如果遇到問題：

1. **查看日誌**：大部分問題都能從日誌中找到原因
2. **搜尋錯誤訊息**：Google 或 Stack Overflow
3. **檢查配置**：確認所有設定都正確
4. **測試各個步驟**：逐步排除問題

---

**祝您部署順利！** 🎉
