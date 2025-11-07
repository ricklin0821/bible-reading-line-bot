# Windows 部署指南

## 🪟 Windows 環境部署說明

本指南專為 Windows 用戶設計，提供在 Windows PowerShell 或 Git Bash 中部署 Rich Menu 的完整步驟。

---

## 📋 前置需求

### 必要工具

1. **PowerShell 5.1 或更高版本**（Windows 10/11 內建）
   - 檢查版本：`$PSVersionTable.PSVersion`

2. **Google Cloud SDK**（用於刪除 Scheduler 任務）
   - 下載：https://cloud.google.com/sdk/docs/install
   - 安裝後執行：`gcloud init`

3. **LINE Channel Access Token**
   - 前往 [LINE Developers Console](https://developers.line.biz/console/)
   - 選擇您的 Channel → Messaging API → Channel access token

### 可選工具

- **Git for Windows**（包含 Git Bash）
  - 下載：https://git-scm.com/download/win
  - 可執行 `.sh` 腳本

---

## 🚀 部署步驟

### 方法 1: 使用 PowerShell（推薦）

#### 步驟 1: 開啟 PowerShell

```powershell
# 以系統管理員身分開啟 PowerShell（可選）
# 或直接開啟一般 PowerShell
```

#### 步驟 2: 切換到專案目錄

```powershell
cd C:\Users\rickl\OneDrive\Documents\bible-reading-line-bot
```

#### 步驟 3: 允許執行腳本（首次執行需要）

```powershell
# 設定執行原則（選擇其中一個）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 或者只針對這次執行
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

#### 步驟 4: 部署 Rich Menu

```powershell
# 替換成您的 Channel Access Token
.\deploy_rich_menu.ps1 -Token "YOUR_CHANNEL_ACCESS_TOKEN"
```

**範例輸出：**
```
🚀 開始部署 Rich Menu...

📝 步驟 1: 創建 Rich Menu...
✅ Rich Menu 已創建: richmenu-xxxxxxxxxxxxx

📤 步驟 2: 上傳 Rich Menu 圖片...
✅ 圖片上傳成功

🔧 步驟 3: 設定為預設 Rich Menu...
✅ 已設定為預設 Rich Menu

🎉 Rich Menu 部署完成！
```

#### 步驟 5: 測試 Rich Menu

1. 開啟 LINE App
2. 找到您的 Bot 聊天室
3. 點擊左下角的鍵盤圖示
4. 應該會看到 6 個按鈕的 Rich Menu
5. 測試每個按鈕是否正常運作

#### 步驟 6: 刪除舊的 Scheduler 任務

**⚠️ 重要：請先確認 Rich Menu 功能正常後再執行此步驟！**

```powershell
.\delete_schedulers.ps1
```

系統會詢問確認：
```
⚠️  即將刪除 4 個任務（保留 bible-push-morning），是否繼續？ (y/N)
```

輸入 `y` 並按 Enter 確認。

---

### 方法 2: 使用 Git Bash

如果您已安裝 Git for Windows，可以使用 Git Bash 執行原始的 `.sh` 腳本：

#### 步驟 1: 開啟 Git Bash

在專案資料夾中右鍵 → "Git Bash Here"

#### 步驟 2: 執行部署腳本

```bash
# 部署 Rich Menu
bash deploy_rich_menu.sh YOUR_CHANNEL_ACCESS_TOKEN

# 刪除舊任務
bash delete_schedulers.sh
```

---

### 方法 3: 手動執行（使用 curl）

如果您安裝了 curl（Windows 10 1803+ 內建），也可以手動執行：

#### 3.1 創建 Rich Menu

```powershell
$token = "YOUR_CHANNEL_ACCESS_TOKEN"

curl -X POST https://api.line.me/v2/bot/richmenu `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d '{
    "size": {"width": 2500, "height": 1686},
    "selected": true,
    "name": "Bible Reading Bot Menu",
    "chatBarText": "📖 聖經讀經選單",
    "areas": [
      {"bounds": {"x": 0, "y": 0, "width": 1250, "height": 562}, "action": {"type": "message", "text": "今日讀經"}},
      {"bounds": {"x": 1250, "y": 0, "width": 1250, "height": 562}, "action": {"type": "message", "text": "荒漠甘泉"}},
      {"bounds": {"x": 0, "y": 562, "width": 1250, "height": 562}, "action": {"type": "message", "text": "回報讀經"}},
      {"bounds": {"x": 1250, "y": 562, "width": 1250, "height": 562}, "action": {"type": "message", "text": "我的進度"}},
      {"bounds": {"x": 0, "y": 1124, "width": 1250, "height": 562}, "action": {"type": "message", "text": "排行榜"}},
      {"bounds": {"x": 1250, "y": 1124, "width": 1250, "height": 562}, "action": {"type": "message", "text": "選單"}}
    ]
  }'
```

記下回傳的 `richMenuId`。

#### 3.2 上傳圖片

```powershell
$richMenuId = "richmenu-xxxxxxxxxxxxx"  # 替換成上一步的 ID

curl -X POST "https://api-data.line.me/v2/bot/richmenu/$richMenuId/content" `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: image/png" `
  --data-binary "@rich_menu.png"
```

#### 3.3 設定為預設 Rich Menu

```powershell
curl -X POST "https://api.line.me/v2/bot/user/all/richmenu/$richMenuId" `
  -H "Authorization: Bearer $token"
```

---

## ✅ 驗證部署

### 1. 檢查 Rich Menu 是否生效

```powershell
$token = "YOUR_CHANNEL_ACCESS_TOKEN"
$headers = @{"Authorization" = "Bearer $token"}

# 查看所有 Rich Menu
Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu/list" -Headers $headers

# 查看預設 Rich Menu
Invoke-RestMethod -Uri "https://api.line.me/v2/bot/user/all/richmenu" -Headers $headers
```

### 2. 測試各按鈕功能

在 LINE App 中測試：

- [ ] 📖 今日讀經 → 應收到今日讀經計畫
- [ ] 🌅 荒漠甘泉 → 應收到今日靈修內容
- [ ] ✅ 回報讀經 → 應顯示回報選項
- [ ] 📊 我的進度 → 應顯示個人統計
- [ ] 🏆 排行榜 → 應收到排行榜連結
- [ ] ⚙️ 選單 → 應顯示更多功能

### 3. 確認 Scheduler 任務

```powershell
gcloud scheduler jobs list --location=asia-east1
```

應該只看到 1 個任務：`bible-push-morning`

---

## 🔧 故障排除

### 問題 1: PowerShell 無法執行腳本

**錯誤訊息：**
```
無法載入檔案，因為這個系統上已停用指令碼執行。
```

**解決方法：**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 問題 2: 找不到 gcloud 命令

**錯誤訊息：**
```
'gcloud' 不是內部或外部命令、可執行的程式或批次檔。
```

**解決方法：**
1. 安裝 Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. 重新開啟 PowerShell
3. 執行 `gcloud init` 進行初始化

### 問題 3: Rich Menu API 錯誤

**錯誤訊息：**
```
401 Unauthorized
```

**解決方法：**
- 確認 Channel Access Token 正確
- 確認 Token 沒有過期
- 前往 LINE Developers Console 重新發行 Token

### 問題 4: 圖片上傳失敗

**錯誤訊息：**
```
400 Bad Request
```

**解決方法：**
- 確認 `rich_menu.png` 存在於當前目錄
- 確認圖片尺寸為 2500×1686
- 確認圖片格式為 PNG
- 確認檔案大小不超過 1MB

---

## 📊 成本監控

### 查看 LINE API 使用量

1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 選擇您的 Channel
3. 點擊 "Messaging API" 分頁
4. 查看 "Message usage" 統計

### 預期使用量

**部署後（每月）：**
- Push messages: ~300 次（10用戶 × 1次/天 × 30天）
- Reply messages: ~1,000 次（免費）
- 預期費用: ~$0.30/月（扣除 200 次免費額度後）

### 查看 Google Cloud 費用

```powershell
# 查看當月費用
gcloud billing accounts list
gcloud billing projects describe bible-bot-project
```

或前往 [Google Cloud Console - Billing](https://console.cloud.google.com/billing)

---

## 🗑️ 回滾操作

如果需要刪除 Rich Menu 並恢復原狀：

### 刪除 Rich Menu

```powershell
$token = "YOUR_CHANNEL_ACCESS_TOKEN"
$richMenuId = "richmenu-xxxxxxxxxxxxx"  # 您的 Rich Menu ID

$headers = @{"Authorization" = "Bearer $token"}
Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu/$richMenuId" `
  -Method Delete `
  -Headers $headers
```

### 重新創建 Scheduler 任務

參考 `SCHEDULER_SETUP.md` 中的指令重新創建被刪除的任務。

---

## 📞 技術支援

### 相關資源

- [LINE Messaging API 文件](https://developers.line.biz/en/docs/messaging-api/)
- [Rich Menu 設計指南](https://developers.line.biz/en/docs/messaging-api/using-rich-menus/)
- [Google Cloud SDK 文件](https://cloud.google.com/sdk/docs)
- [PowerShell 文件](https://docs.microsoft.com/powershell/)

### 常用命令

```powershell
# 查看 PowerShell 版本
$PSVersionTable.PSVersion

# 查看 gcloud 版本
gcloud version

# 查看當前專案
gcloud config get-value project

# 登入 Google Cloud
gcloud auth login

# 查看所有 Rich Menu
$headers = @{"Authorization" = "Bearer YOUR_TOKEN"}
Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu/list" -Headers $headers
```

---

## 📝 檢查清單

### 部署前
- [ ] 已安裝 PowerShell 5.1+
- [ ] 已安裝 Google Cloud SDK
- [ ] 已取得 LINE Channel Access Token
- [ ] 已下載 `rich_menu.png` 到專案目錄
- [ ] 已下載 `deploy_rich_menu.ps1` 到專案目錄

### 部署中
- [ ] 成功創建 Rich Menu
- [ ] 成功上傳圖片
- [ ] 成功設定為預設 Rich Menu
- [ ] 在 LINE App 中看到 Rich Menu
- [ ] 測試所有按鈕功能正常

### 部署後
- [ ] 刪除 4 個舊的 Scheduler 任務
- [ ] 確認只剩 1 個 Scheduler 任務
- [ ] 監控 LINE API 使用量
- [ ] 監控 Google Cloud 費用
- [ ] 收集用戶反饋

---

**最後更新**: 2025-11-07  
**版本**: 1.0  
**適用系統**: Windows 10/11
