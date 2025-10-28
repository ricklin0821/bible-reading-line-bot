# Firestore 資料匯入指南

## 📋 重要說明

由於聖經經文資料量龐大（31,000+ 節經文），如果在 Cloud Run 容器首次啟動時匯入，會導致超時錯誤。因此，**必須先在本地手動匯入資料到 Firestore**，然後再部署 Cloud Run 服務。

---

## 🔧 步驟 1: 設定 Google Cloud 認證

### 方法 A: 使用 gcloud CLI（推薦）

```bash
# 登入 Google Cloud
gcloud auth application-default login

# 設定專案 ID
gcloud config set project YOUR_PROJECT_ID
```

### 方法 B: 使用服務帳戶金鑰

1. 前往 [Google Cloud Console - 服務帳戶](https://console.cloud.google.com/iam-admin/serviceaccounts)
2. 選擇或建立一個服務帳戶
3. 點選「金鑰」→「新增金鑰」→「JSON」
4. 下載金鑰檔案（例如：`service-account-key.json`）
5. 設定環境變數：

```bash
# Windows (CMD)
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service-account-key.json

# Windows (PowerShell)
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\service-account-key.json"

# Linux / Mac
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

---

## 🚀 步驟 2: 執行資料匯入腳本

### 2.1 確保已安裝依賴套件

```bash
pip install google-cloud-firestore pandas
```

### 2.2 執行匯入腳本

```bash
# 進入專案目錄
cd bible-reading-line-bot

# 執行匯入腳本
python3 import_data_to_firestore.py
```

### 2.3 匯入過程

腳本會詢問您是否繼續，輸入 `y` 確認：

```
============================================================
Firestore 資料匯入工具
============================================================

此工具將匯入以下資料到 Firestore:
  1. 聖經經文 (約 31,000+ 節)
  2. 讀經計畫 (兩種計畫，共 730 筆)

⚠️  注意: 匯入過程可能需要數分鐘，請確保網路連線穩定

是否繼續？(y/N): y
```

匯入過程會顯示進度：

```
============================================================
匯入聖經經文資料到 Firestore
============================================================

讀取 data/bible_text.csv...
✓ 讀取到 31102 節經文

開始匯入 31102 節經文到 Firestore...
(這可能需要幾分鐘時間，請耐心等待...)
  進度: 500/31102 (1%)
  進度: 1000/31102 (3%)
  進度: 1500/31102 (4%)
  ...
  進度: 31102/31102 (100%)
✅ 成功匯入 31102 節經文到 Firestore

============================================================
匯入讀經計畫資料到 Firestore
============================================================

讀取 data/bible_plans.csv...
✓ 讀取到 730 筆讀經計畫

開始匯入 730 筆讀經計畫到 Firestore...
  進度: 500/730 (68%)
  進度: 730/730 (100%)
✅ 成功匯入 730 筆讀經計畫到 Firestore

============================================================
驗證 Firestore 資料
============================================================
✓ 聖經經文集合存在，樣本數據: 10 筆
  範例: 創1:1 - 起初　神創造天地。...
✓ 讀經計畫集合存在，樣本數據: 10 筆
  範例: Day 1 (Canonical) - 創1-3

============================================================
✅ 資料匯入完成！
============================================================

現在可以部署您的 LINE Bot 到 Cloud Run 了。
```

---

## ✅ 步驟 3: 驗證資料已成功匯入

### 方法 A: 使用 Firestore Console

1. 前往 [Firestore Console](https://console.cloud.google.com/firestore)
2. 選擇您的專案
3. 點選「資料」標籤
4. 確認以下集合存在且有資料：
   - `bible_text` - 應該有 31,000+ 筆文檔
   - `bible_plans` - 應該有 730 筆文檔

### 方法 B: 使用匯入腳本的驗證功能

匯入完成後，腳本會自動執行驗證並顯示樣本資料。

---

## 🔄 步驟 4: 部署到 Cloud Run

資料匯入完成後，就可以安全地部署 Cloud Run 服務了：

```bash
# 1. 更新程式碼
git pull origin master

# 2. 建置映像
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/bible-bot:v5-firestore

# 3. 部署服務
gcloud run deploy bible-bot \
  --image gcr.io/YOUR_PROJECT_ID/bible-bot:v5-firestore \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars LINE_CHANNEL_ACCESS_TOKEN=YOUR_TOKEN,LINE_CHANNEL_SECRET=YOUR_SECRET
```

部署後，Cloud Run 容器啟動時會檢查 Firestore 中是否已有資料，發現資料已存在後會跳過匯入，直接啟動服務。

---

## 🐛 常見問題

### Q1: 匯入時出現 "Permission denied" 錯誤

**原因**: 服務帳戶沒有 Firestore 寫入權限

**解決方案**:
1. 前往 [IAM & Admin](https://console.cloud.google.com/iam-admin/iam)
2. 找到您使用的服務帳戶
3. 新增「Cloud Datastore User」或「Cloud Datastore Owner」角色

### Q2: 匯入時出現 "File not found: data/bible_text.csv"

**原因**: 未在專案目錄中執行腳本

**解決方案**:
```bash
cd bible-reading-line-bot
python3 import_data_to_firestore.py
```

### Q3: 匯入過程中斷或失敗

**解決方案**:
1. 重新執行腳本
2. 腳本會詢問是否清除現有資料並重新匯入
3. 輸入 `y` 確認重新匯入

### Q4: 想要重新匯入資料

**解決方案**:
1. 直接執行 `python3 import_data_to_firestore.py`
2. 腳本會偵測到現有資料並詢問是否重新匯入
3. 輸入 `y` 確認

---

## 💰 成本估算

### 資料匯入成本

- **一次性寫入**: 約 31,730 次寫入
- **Firestore 免費額度**: 每日 20,000 次寫入
- **預估成本**: 首次匯入會超過免費額度，可能產生少量費用（約 $0.06 USD）

### 後續運行成本

匯入完成後，日常使用完全在免費額度內（參考主要部署指南）。

---

## 📝 注意事項

1. **只需匯入一次**: 資料匯入到 Firestore 後會永久保存，不需要重複匯入
2. **網路穩定性**: 匯入過程需要穩定的網路連線，建議在網路良好的環境下執行
3. **執行時間**: 完整匯入約需 3-5 分鐘，請耐心等待
4. **資料驗證**: 匯入完成後務必檢查 Firestore Console 確認資料正確

---

## 🎉 完成！

資料匯入完成後，您的 LINE Bot 就可以正常運作了！所有使用者資料、讀經進度都會持久化儲存在 Firestore 中，不會因為容器重啟而遺失。

