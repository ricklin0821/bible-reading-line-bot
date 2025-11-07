# Rich Menu 部署 - 分步驟指南

## 🎯 最簡單的方法：逐步複製貼上

由於 Windows PowerShell 的編碼限制，請按照以下步驟**逐一複製貼上**到 PowerShell 執行。

---

## 步驟 1: 設定 Token

```powershell
$token = "bHPK8L8IgwjV5TcOA9Y4l3C+GZOH4TXmfGMt4OKnSxkxdgZNVhVGhFO8Gu0YlwLNKrpBNQFWWcRqwUdRGiPQWEzDJEIj9sKPBh0XQqZvPmZlUBDcGgLLKKLKKLKLKLKL"
```

> ⚠️ **重要**：請替換成您的完整 Channel Access Token

---

## 步驟 2: 創建 Rich Menu

複製以下**整段**指令到 PowerShell：

```powershell
$body = @'
{
  "size": {
    "width": 2500,
    "height": 1686
  },
  "selected": true,
  "name": "Bible Reading Bot Menu",
  "chatBarText": "Bible Menu",
  "areas": [
    {
      "bounds": {"x": 0, "y": 0, "width": 1250, "height": 562},
      "action": {"type": "message", "text": "Today Reading"}
    },
    {
      "bounds": {"x": 1250, "y": 0, "width": 1250, "height": 562},
      "action": {"type": "message", "text": "Devotional"}
    },
    {
      "bounds": {"x": 0, "y": 562, "width": 1250, "height": 562},
      "action": {"type": "message", "text": "Report"}
    },
    {
      "bounds": {"x": 1250, "y": 562, "width": 1250, "height": 562},
      "action": {"type": "message", "text": "Progress"}
    },
    {
      "bounds": {"x": 0, "y": 1124, "width": 1250, "height": 562},
      "action": {"type": "message", "text": "Leaderboard"}
    },
    {
      "bounds": {"x": 1250, "y": 1124, "width": 1250, "height": 562},
      "action": {"type": "message", "text": "Menu"}
    }
  ]
}
'@

$response = Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu" -Method Post -Headers @{"Authorization"="Bearer $token"; "Content-Type"="application/json"} -Body $body

$richMenuId = $response.richMenuId
Write-Host "Rich Menu ID: $richMenuId" -ForegroundColor Green
```

**預期輸出：**
```
Rich Menu ID: richmenu-xxxxxxxxxxxxxxxxxxxxx
```

> 📝 **記下這個 Rich Menu ID**，後續步驟會用到！

---

## 步驟 3: 上傳圖片

```powershell
$imageBytes = [System.IO.File]::ReadAllBytes("$PWD\rich_menu.png")
Invoke-RestMethod -Uri "https://api-data.line.me/v2/bot/richmenu/$richMenuId/content" -Method Post -Headers @{"Authorization"="Bearer $token"; "Content-Type"="image/png"} -Body $imageBytes

Write-Host "Image uploaded successfully!" -ForegroundColor Green
```

**預期輸出：**
```
Image uploaded successfully!
```

---

## 步驟 4: 設定為預設 Rich Menu

```powershell
Invoke-RestMethod -Uri "https://api.line.me/v2/bot/user/all/richmenu/$richMenuId" -Method Post -Headers @{"Authorization"="Bearer $token"}

Write-Host "Set as default Rich Menu successfully!" -ForegroundColor Green
```

**預期輸出：**
```
Set as default Rich Menu successfully!
```

---

## 步驟 5: 驗證部署

```powershell
$menus = Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu/list" -Headers @{"Authorization"="Bearer $token"}
$menus.richmenus | Format-Table richMenuId, name, chatBarText
```

**預期輸出：**
```
richMenuId                    name                    chatBarText
----------                    ----                    -----------
richmenu-xxxxxxxxxxxxx        Bible Reading Bot Menu  Bible Menu
```

---

## ✅ 測試 Rich Menu

1. 開啟 LINE App
2. 找到您的 Bot 聊天室
3. 點擊左下角的**鍵盤圖示**
4. 應該會看到 6 個按鈕的 Rich Menu

---

## 🔧 如果出錯：刪除 Rich Menu 重新開始

```powershell
# 查看所有 Rich Menu
$menus = Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu/list" -Headers @{"Authorization"="Bearer $token"}
$menus.richmenus | Format-Table richMenuId, name

# 刪除指定的 Rich Menu（替換成實際的 ID）
Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu/richmenu-xxxxxxxxxxxxx" -Method Delete -Headers @{"Authorization"="Bearer $token"}
```

---

## 📋 按鈕觸發文字對應表

| Rich Menu 按鈕位置 | 觸發文字 | 需要對應的功能 |
|------------------|---------|--------------|
| 左上（📖） | "Today Reading" | 今日讀經 |
| 右上（🌅） | "Devotional" | 荒漠甘泉 |
| 左中（✅） | "Report" | 回報讀經 |
| 右中（📊） | "Progress" | 我的進度 |
| 左下（🏆） | "Leaderboard" | 排行榜 |
| 右下（⚙️） | "Menu" | 選單 |

---

## ⚠️ 重要：更新 main.py

Rich Menu 部署完成後，**必須更新 main.py** 才能讓按鈕正常運作！

請參考 `MAIN_PY_UPDATE_GUIDE.md` 中的詳細說明。

簡單來說，在 `handle_message` 函數中新增：

```python
if text in ["Today Reading", "今日讀經"]:
    send_daily_reading(user_id)
    return

elif text in ["Devotional", "荒漠甘泉"]:
    send_devotional(user_id)
    return

elif text in ["Report", "回報讀經"]:
    handle_reading_report(user_id)
    return

elif text in ["Progress", "我的進度"]:
    send_user_stats(user_id)
    return

elif text in ["Leaderboard", "排行榜"]:
    send_leaderboard_link(user_id)
    return

elif text in ["Menu", "選單"]:
    send_menu_options(user_id)
    return
```

---

## 🚀 更新後部署到 Cloud Run

```bash
# 提交變更
git add main.py
git commit -m "Add Rich Menu trigger text support"
git push origin master

# 部署到 Cloud Run
gcloud run deploy bible-bot --source . --region asia-east1 --project bible-bot-project
```

---

## 📊 完成後：刪除舊的 Scheduler 任務

確認 Rich Menu 功能正常後，執行：

```powershell
.\delete_schedulers.ps1
```

或手動刪除：

```bash
gcloud scheduler jobs delete bible-push-noon --location=asia-east1 --quiet
gcloud scheduler jobs delete daily-devotional-sender --location=asia-east1 --quiet
gcloud scheduler jobs delete bible-push-evening --location=asia-east1 --quiet
gcloud scheduler jobs delete bible-push-night --location=asia-east1 --quiet
```

---

## 💡 故障排除

### 問題：401 Unauthorized

**原因**：Token 錯誤或過期

**解決**：
1. 前往 [LINE Developers Console](https://developers.line.biz/console/)
2. 重新發行 Channel Access Token
3. 更新 `$token` 變數

### 問題：找不到 rich_menu.png

**原因**：圖片不在當前目錄

**解決**：
```powershell
# 檢查當前目錄
Get-Location

# 切換到專案目錄
cd C:\Users\rickl\OneDrive\Documents\bible-reading-line-bot

# 確認圖片存在
Test-Path rich_menu.png
```

### 問題：按鈕點擊沒反應

**原因**：main.py 尚未更新

**解決**：
1. 參考 `MAIN_PY_UPDATE_GUIDE.md` 更新 main.py
2. 重新部署到 Cloud Run

---

**最後更新**: 2025-11-07  
**版本**: 1.0  
**適用環境**: Windows PowerShell 5.1+
