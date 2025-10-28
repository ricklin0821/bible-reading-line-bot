# 📖 聖經讀經計畫 LINE Bot

一個功能完整的 LINE Bot，提供一年期聖經讀經計畫、每日進度追蹤、填空測驗和每日推送通知功能。使用中文和合本聖經經文，支援兩種讀經計畫（正典順序和均衡計畫）。

## ✨ 主要功能

- 📅 **兩種讀經計畫**
  - **正典順序**: 按照聖經書卷順序閱讀（創世記 → 啟示錄）
  - **均衡計畫**: 舊約與新約交替閱讀，保持平衡

- 📊 **進度追蹤**
  - 記錄每日閱讀進度
  - 顯示當前閱讀天數和進度百分比
  - 持久化儲存，不受服務重啟影響

- 🎯 **填空測驗**
  - 根據當日閱讀內容自動生成測驗題目
  - 智能答案驗證（支援模糊匹配）
  - 無論答對答錯都給予鼓勵

- 💬 **互動式介面**
  - 美化的 FlexMessage 訊息
  - 快速回覆按鈕
  - 直覺的使用者體驗

- 🔔 **每日推送通知** (可選)
  - 自動提醒每日讀經
  - 推送當日閱讀範圍

- 🌐 **網頁預覽**
  - 線上查看完整讀經計畫
  - 無需登入即可瀏覽

## 🏗️ 技術架構

### 後端框架
- **FastAPI**: 現代化的 Python Web 框架
- **LINE Messaging API**: LINE Bot SDK v3
- **Google Firestore**: NoSQL 雲端資料庫（資料持久化）
- **Pandas**: 資料處理與分析

### 部署平台
- **Google Cloud Run**: 無伺服器容器部署
- **Docker**: 容器化應用
- **GitHub**: 版本控制與 CI/CD

### 資料儲存
- **Firestore Collections**:
  - `users`: 使用者資料與進度
  - `bible_plans`: 讀經計畫資料
  - `bible_texts`: 聖經經文資料

## 🚀 快速開始

### 前置需求

1. **LINE Developers 帳號**
   - 前往 [LINE Developers Console](https://developers.line.biz/console/)
   - 建立 Messaging API Channel
   - 取得 Channel Access Token 和 Channel Secret

2. **Google Cloud 帳號**
   - 建立 Google Cloud 專案
   - 啟用 Cloud Run API
   - 啟用 Firestore API
   - 安裝 [gcloud CLI](https://cloud.google.com/sdk/docs/install)

### 一鍵部署

```bash
# 1. Clone 專案
git clone https://github.com/ricksgemini0857/bible-reading-line-bot.git
cd bible-reading-line-bot

# 2. 設定環境變數
export LINE_CHANNEL_ACCESS_TOKEN="your_channel_access_token"
export LINE_CHANNEL_SECRET="your_channel_secret"

# 3. 執行部署腳本
./deploy_firestore.sh
```

部署腳本會自動完成:
- ✅ 檢查必要工具
- ✅ 啟用 Firestore API
- ✅ 建置 Docker 映像
- ✅ 部署到 Cloud Run
- ✅ 測試 Webhook 連線

### 手動部署

詳細步驟請參考 [Firestore 部署指南](FIRESTORE_DEPLOYMENT_GUIDE.md)

## 📚 使用說明

### 使用者操作流程

1. **加入 Bot**
   - 掃描 QR Code 或搜尋 LINE ID 加入 Bot
   - Bot 會發送歡迎訊息並顯示讀經計畫選項

2. **選擇讀經計畫**
   - 點選「正典順序」或「均衡計畫」
   - Bot 會顯示第一天的閱讀範圍

3. **每日閱讀**
   - 閱讀當日指定的聖經章節
   - 完成後回覆「已讀」或點選快速回覆按鈕

4. **回答測驗**
   - Bot 會根據當日閱讀內容出一題填空題
   - 輸入答案後 Bot 會給予回饋和鼓勵

5. **查看進度**
   - 回覆「進度」查看當前閱讀進度
   - 顯示已完成天數和百分比

### 支援的指令

| 指令 | 說明 |
|------|------|
| `已讀` | 標記當日閱讀完成 |
| `進度` | 查看當前閱讀進度 |
| `計畫` | 重新選擇讀經計畫 |
| `幫助` | 顯示使用說明 |

## 🗂️ 專案結構

```
bible-reading-line-bot/
├── main.py                          # FastAPI 主程式 + LINE Bot Webhook
├── database.py                      # Firestore 資料庫操作
├── quiz_generator.py                # 測驗生成與答案驗證
├── api_routes.py                    # Web API 路由
├── index.html                       # 網頁預覽介面
├── Dockerfile                       # Docker 容器設定
├── requirements.txt                 # Python 依賴套件
├── deploy_firestore.sh              # 一鍵部署腳本
├── FIRESTORE_DEPLOYMENT_GUIDE.md    # Firestore 部署指南
├── Bible_Reading_Bot_Deployment_Guide.md  # 詳細部署教學
├── data/
│   ├── bible_text.csv              # 中文和合本聖經經文
│   └── bible_plans.csv             # 讀經計畫資料
└── static/                          # 靜態資源 (如有)
```

## 🔧 開發指南

### 本地開發環境設定

```bash
# 1. 建立虛擬環境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 設定環境變數
export LINE_CHANNEL_ACCESS_TOKEN="your_token"
export LINE_CHANNEL_SECRET="your_secret"

# 4. 啟動開發伺服器
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 使用 Firestore Emulator (本地測試)

```bash
# 安裝 Firebase CLI
npm install -g firebase-tools

# 啟動 Firestore Emulator
firebase emulators:start --only firestore

# 設定環境變數指向 Emulator
export FIRESTORE_EMULATOR_HOST="localhost:8080"
```

### 測試 Webhook

使用 ngrok 建立本地隧道:

```bash
# 安裝 ngrok
# 下載: https://ngrok.com/download

# 啟動隧道
ngrok http 8000

# 將 ngrok URL 設定到 LINE Developers Console
# Webhook URL: https://your-ngrok-url.ngrok.io/callback
```

## 📊 資料庫結構

### Firestore Collections

#### `users` Collection
```json
{
  "line_user_id": "U1234567890abcdef",
  "plan_type": "canonical",
  "current_day": 15,
  "joined_at": "2025-01-01T00:00:00Z",
  "last_read_date": "2025-01-15T10:30:00Z"
}
```

#### `bible_plans` Collection
```json
{
  "plan_type": "canonical",
  "day": 1,
  "book_code": "GEN",
  "start_chapter": 1,
  "end_chapter": 3
}
```

#### `bible_texts` Collection
```json
{
  "book_code": "GEN",
  "chapter": 1,
  "verse": 1,
  "text": "起初　神創造天地。"
}
```

## 🔐 環境變數

| 變數名稱 | 說明 | 必要性 |
|---------|------|--------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Bot Channel Access Token | 必要 |
| `LINE_CHANNEL_SECRET` | LINE Bot Channel Secret | 必要 |
| `FIRESTORE_EMULATOR_HOST` | Firestore Emulator 位址 (僅本地開發) | 可選 |

## 💰 成本估算

### Google Cloud 免費額度

- **Cloud Run**: 每月 200 萬次請求免費
- **Firestore**: 
  - 每日 50,000 次讀取
  - 每日 20,000 次寫入
  - 1 GB 儲存空間

### 預估使用量 (100 位活躍使用者)

| 服務 | 每日使用量 | 免費額度 | 是否收費 |
|------|-----------|---------|---------|
| Cloud Run 請求 | ~1,000 次 | 66,666 次/日 | ❌ 免費 |
| Firestore 讀取 | ~1,000 次 | 50,000 次/日 | ❌ 免費 |
| Firestore 寫入 | ~200 次 | 20,000 次/日 | ❌ 免費 |

> **結論**: 對於中小型使用量，完全在免費額度內，不會產生費用。

## 🐛 疑難排解

### 常見問題

#### Q1: Bot 沒有回應?

**檢查清單**:
1. ✅ Webhook URL 是否正確設定在 LINE Developers Console
2. ✅ Cloud Run 服務是否正常運行
3. ✅ 環境變數是否正確設定
4. ✅ 查看 Cloud Run 日誌: `gcloud run services logs tail bible-bot --region asia-east1`

#### Q2: 資料在容器重啟後遺失?

**原因**: 可能還在使用 SQLite 版本

**解決方案**: 確認已部署 Firestore 版本 (v5-firestore)

#### Q3: Firestore 權限錯誤?

**解決方案**:
1. 前往 IAM & Admin
2. 為 Compute Engine 預設服務帳戶新增「Cloud Datastore User」角色
3. 重新部署服務

### 查看日誌

```bash
# 即時日誌
gcloud run services logs tail bible-bot --region asia-east1

# 最近 50 筆日誌
gcloud run services logs read bible-bot --region asia-east1 --limit 50

# 過濾錯誤日誌
gcloud run services logs read bible-bot --region asia-east1 --filter="severity>=ERROR"
```

## 📖 文件

- [Firestore 部署指南](FIRESTORE_DEPLOYMENT_GUIDE.md) - Firestore 遷移與部署詳細說明
- [完整部署教學](Bible_Reading_Bot_Deployment_Guide.md) - 從零開始的完整部署指南

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

### 開發流程

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 📝 授權

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 🙏 致謝

- **中文和合本聖經**: 經文資料來源
- **LINE Messaging API**: 提供強大的 Bot 開發平台
- **Google Cloud**: 提供可靠的雲端服務
- **FastAPI**: 優秀的 Python Web 框架

## 📧 聯絡方式

- GitHub: [@ricksgemini0857](https://github.com/ricksgemini0857)
- 專案連結: [https://github.com/ricksgemini0857/bible-reading-line-bot](https://github.com/ricksgemini0857/bible-reading-line-bot)

---

**⭐ 如果這個專案對您有幫助，請給個星星支持！**

