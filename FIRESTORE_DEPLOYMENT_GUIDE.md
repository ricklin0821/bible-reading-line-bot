# Firestore 遷移部署指南

## 📋 概述

本專案已從 SQLite 遷移至 Google Firestore，解決了 Cloud Run 容器重啟後資料遺失的問題。Firestore 是 Google 提供的 NoSQL 雲端資料庫，具有以下優勢:

- ✅ **資料持久化**: 資料儲存在雲端，不受容器重啟影響
- ✅ **免費額度**: 每日 50,000 次讀取、20,000 次寫入、20,000 次刪除
- ✅ **自動擴展**: 無需管理伺服器，自動處理流量變化
- ✅ **即時同步**: 支援即時資料更新

---

## 🔧 部署前準備

### 步驟 1: 啟用 Firestore API

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 選擇您的專案 (與 Cloud Run 相同的專案)
3. 在左側選單中，點選「Firestore」或搜尋「Firestore」
4. 點選「建立資料庫」
5. 選擇「Native mode」(原生模式)
6. 選擇資料庫位置 (建議選擇 `asia-east1` 台灣或 `asia-northeast1` 日本)
7. 點選「建立資料庫」

### 步驟 2: 設定 Cloud Run 服務帳戶權限

Cloud Run 預設使用 Compute Engine 預設服務帳戶，需要確保其具有 Firestore 存取權限:

1. 前往 [IAM & Admin](https://console.cloud.google.com/iam-admin/iam)
2. 找到格式為 `[PROJECT_NUMBER]-compute@developer.gserviceaccount.com` 的服務帳戶
3. 點選編輯 (鉛筆圖示)
4. 點選「新增其他角色」
5. 搜尋並新增以下角色:
   - **Cloud Datastore User** (雲端資料儲存庫使用者)
6. 點選「儲存」

> **注意**: 如果您的 Cloud Run 服務使用自訂服務帳戶，請對該帳戶進行相同設定。

---

## 🚀 部署步驟

### 方法 1: 使用 gcloud 指令部署 (推薦)

```bash
# 1. 確認您在專案目錄中
cd /path/to/bible-reading-line-bot

# 2. 設定 Google Cloud 專案 ID
gcloud config set project YOUR_PROJECT_ID

# 3. 建置並推送 Docker 映像
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/bible-bot:v5-firestore

# 4. 部署到 Cloud Run
gcloud run deploy bible-bot \
  --image gcr.io/YOUR_PROJECT_ID/bible-bot:v5-firestore \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars LINE_CHANNEL_ACCESS_TOKEN=YOUR_CHANNEL_ACCESS_TOKEN,LINE_CHANNEL_SECRET=YOUR_CHANNEL_SECRET
```

### 方法 2: 使用 Cloud Console 部署

1. 前往 [Cloud Run](https://console.cloud.google.com/run)
2. 點選您現有的服務 (例如 `bible-bot`)
3. 點選「編輯並部署新修訂版本」
4. 在「容器映像檔網址」中，點選「選取」
5. 選擇「Cloud Build」→ 建置新映像
6. 選擇來源: GitHub 倉庫 `ricksgemini0857/bible-reading-line-bot`
7. 分支: `master`
8. 建置類型: Dockerfile
9. 點選「建置」並等待完成
10. 確認環境變數已設定:
    - `LINE_CHANNEL_ACCESS_TOKEN`
    - `LINE_CHANNEL_SECRET`
11. 點選「部署」

---

## 🧪 測試部署

### 1. 測試 Webhook 連線

```bash
curl -X POST https://YOUR_CLOUD_RUN_URL/callback \
  -H "Content-Type: application/json" \
  -d '{"events":[]}'
```

應該回傳: `{"status": "ok"}`

### 2. 測試 LINE Bot 功能

1. 在 LINE 中封鎖並重新加入您的 Bot
2. Bot 應該發送歡迎訊息並顯示讀經計畫選項
3. 選擇一個讀經計畫 (例如「正典順序」)
4. 回覆「已讀」測試進度追蹤
5. 回答測驗題目

### 3. 驗證資料持久化

**重要測試**: 驗證資料是否真的持久化

```bash
# 1. 記錄當前使用者狀態 (透過 LINE Bot 互動)
# 2. 強制重新部署服務 (觸發容器重啟)
gcloud run services update bible-bot --region asia-east1

# 3. 等待部署完成後，再次與 Bot 互動
# 4. 確認使用者資料、讀經進度、測驗記錄都還在
```

如果資料持久化成功，Bot 應該:
- ✅ 記得您選擇的讀經計畫
- ✅ 記得您的閱讀進度 (天數)
- ✅ 不會要求您重新選擇計畫

---

## 📊 Firestore 資料結構

### 集合 (Collections)

1. **users** - 使用者資料
   - 文件 ID: LINE 使用者 ID
   - 欄位:
     - `line_user_id` (string): LINE 使用者 ID
     - `plan_type` (string): 讀經計畫類型 ("canonical" 或 "balanced")
     - `current_day` (number): 當前閱讀天數
     - `joined_at` (timestamp): 加入時間
     - `last_read_date` (timestamp): 最後閱讀日期

2. **bible_plans** - 讀經計畫
   - 文件 ID: 自動生成
   - 欄位:
     - `plan_type` (string): 計畫類型
     - `day` (number): 天數
     - `book_code` (string): 書卷代碼
     - `start_chapter` (number): 起始章節
     - `end_chapter` (number): 結束章節

3. **bible_texts** - 聖經經文
   - 文件 ID: 自動生成
   - 欄位:
     - `book_code` (string): 書卷代碼
     - `chapter` (number): 章節
     - `verse` (number): 節數
     - `text` (string): 經文內容

### 查看 Firestore 資料

1. 前往 [Firestore Console](https://console.cloud.google.com/firestore)
2. 選擇您的專案
3. 點選「資料」標籤
4. 您可以看到所有集合和文件

---

## 🔍 除錯與監控

### 查看 Cloud Run 日誌

```bash
# 即時查看日誌
gcloud run services logs tail bible-bot --region asia-east1

# 查看最近的錯誤
gcloud run services logs read bible-bot --region asia-east1 --limit 50
```

### 常見錯誤與解決方案

#### 錯誤 1: `Permission denied` 或 `403 Forbidden`

**原因**: Cloud Run 服務帳戶沒有 Firestore 存取權限

**解決方案**:
1. 前往 IAM & Admin
2. 為 Compute Engine 預設服務帳戶新增「Cloud Datastore User」角色
3. 重新部署服務

#### 錯誤 2: `Collection not found` 或資料為空

**原因**: 資料尚未初始化

**解決方案**:
- Firestore 會在首次寫入時自動建立集合
- 確認 `init_db()` 函數正確執行
- 檢查日誌中是否有「Initialized X bible plans」訊息

#### 錯誤 3: 使用者資料消失

**原因**: 可能是查詢邏輯錯誤或文件 ID 不一致

**解決方案**:
1. 前往 Firestore Console 檢查 `users` 集合
2. 確認文件 ID 是否為 LINE 使用者 ID
3. 檢查日誌中的查詢語句

---

## 💰 成本估算

### Firestore 免費額度 (每日)

- **讀取**: 50,000 次
- **寫入**: 20,000 次
- **刪除**: 20,000 次
- **儲存**: 1 GB

### 預估使用量 (100 位活躍使用者)

每位使用者每日操作:
- 讀取: 約 10 次 (查詢使用者、計畫、經文)
- 寫入: 約 2 次 (更新進度、測驗記錄)

**總計**:
- 讀取: 100 × 10 = 1,000 次/日 (遠低於 50,000 免費額度)
- 寫入: 100 × 2 = 200 次/日 (遠低於 20,000 免費額度)

> **結論**: 對於中小型使用量,完全在免費額度內,不會產生費用。

---

## 🔄 從 SQLite 遷移的主要變更

### 程式碼變更對照

| SQLite (舊版) | Firestore (新版) |
|--------------|-----------------|
| `db.query(User).filter(...).first()` | `get_user(line_user_id)` |
| `db.add(user); db.commit()` | `create_user(line_user_id, plan_type)` |
| `user.current_day += 1; db.commit()` | `update_user_progress(line_user_id, current_day)` |
| `db.query(BiblePlan).filter(...).all()` | `get_bible_plan(plan_type, day)` |

### 資料庫檔案

- ❌ 舊版: `bible_bot.db` (容器內,會遺失)
- ✅ 新版: Google Firestore (雲端,永久保存)

---

## 📚 參考資源

- [Firestore 官方文件](https://cloud.google.com/firestore/docs)
- [Cloud Run 官方文件](https://cloud.google.com/run/docs)
- [LINE Messaging API 文件](https://developers.line.biz/en/docs/messaging-api/)
- [專案 GitHub 倉庫](https://github.com/ricksgemini0857/bible-reading-line-bot)

---

## ❓ 常見問題

### Q1: 為什麼要從 SQLite 遷移到 Firestore?

**A**: Cloud Run 容器是無狀態的,每次重新部署或自動擴展時,容器內的 SQLite 資料庫檔案會遺失。Firestore 是雲端資料庫,資料永久保存。

### Q2: Firestore 會產生費用嗎?

**A**: Firestore 有慷慨的免費額度,對於中小型應用完全免費。只有在超過每日 50,000 次讀取或 20,000 次寫入時才會收費。

### Q3: 如何備份 Firestore 資料?

**A**: 
```bash
# 匯出整個資料庫
gcloud firestore export gs://YOUR_BUCKET_NAME/firestore-backup

# 匯入資料
gcloud firestore import gs://YOUR_BUCKET_NAME/firestore-backup
```

### Q4: 可以在本地開發時使用 Firestore 嗎?

**A**: 可以,有兩種方式:
1. 使用 Firestore Emulator (本地模擬器)
2. 直接連接到雲端 Firestore (需要服務帳戶金鑰)

---

## 🎉 完成!

恭喜您完成 Firestore 遷移! 現在您的 LINE Bot 資料會永久保存,不再受容器重啟影響。

如有任何問題,請參考日誌或聯繫開發者。

