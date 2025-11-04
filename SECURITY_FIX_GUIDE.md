# 資安修復指南

**修復日期**：2025-11-02  
**嚴重程度**：🚨 高風險  
**狀態**：⚠️ 需要立即處理

---

## 🚨 發現的資安問題

### 1. 管理員密碼寫死在程式碼中（已修復）

**原始問題**：
```python
# admin_routes.py 第 27 行
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "bible2025")
```

**風險**：
- ❌ 預設密碼 `bible2025` 已經公開在 GitHub 上
- ❌ 任何人都可以使用這個密碼登入管理後台
- ❌ 可以查看所有使用者資料、匯出資料、重置進度

**修復後**：
```python
# 管理員帳號密碼必須從環境變數設定，不提供預設值以確保安全
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise ValueError("⚠️ SECURITY: ADMIN_USERNAME and ADMIN_PASSWORD must be set in environment variables")
```

---

### 2. API 清除快取的密鑰寫死（已修復）

**原始問題**：
```python
# api_routes.py 第 214 行
if secret != "bible2025_clear_cache":
```

**風險**：
- ❌ 密鑰 `bible2025_clear_cache` 已經公開
- ❌ 任何人都可以清除 API 快取

**修復後**：
```python
CACHE_CLEAR_SECRET = os.environ.get("CACHE_CLEAR_SECRET")

if not CACHE_CLEAR_SECRET:
    raise HTTPException(status_code=500, detail="CACHE_CLEAR_SECRET not configured")

if secret != CACHE_CLEAR_SECRET:
    raise HTTPException(status_code=403, detail="Forbidden")
```

---

### 3. 缺少 .gitignore 檔案（已修復）

**問題**：
- ❌ 沒有 `.gitignore`，可能會意外上傳敏感檔案
- ❌ 已經上傳了 `__pycache__/`、`*.db`、`*.log` 等不必要的檔案

**修復**：
- ✅ 建立了完整的 `.gitignore` 檔案
- ✅ 包含 Python、環境變數、資料庫、日誌、憑證等

---

### 4. 上傳了不必要的檔案（需要清理）

**問題檔案**：
- `__pycache__/` - Python 快取檔案（應該被忽略）
- `bible_plan.db` - SQLite 資料庫（可能包含測試資料）
- `server.log` - 日誌檔案（可能包含敏感資訊）
- `*_backup.py` - 備份檔案（不應該上傳）

---

## ✅ 已完成的修復

1. ✅ 建立 `.gitignore` 檔案
2. ✅ 移除 `admin_routes.py` 中的預設密碼
3. ✅ 移除 `api_routes.py` 中的寫死密鑰
4. ✅ 建立 `.env.example` 範例檔案

---

## 🚀 立即需要執行的步驟

### 步驟 1：設定環境變數（Cloud Run）

前往 Cloud Run 設定頁面：
https://console.cloud.google.com/run/detail/asia-east1/bible-bot/variables-and-secrets?project=bible-bot-project

點擊「編輯和部署新修訂版本」，然後在「變數和密鑰」區段新增以下環境變數：

```
ADMIN_USERNAME=your_new_admin_username
ADMIN_PASSWORD=your_new_strong_password
CACHE_CLEAR_SECRET=your_cache_clear_secret
```

**重要**：
- 使用強密碼（至少 12 個字元，包含大小寫、數字、特殊符號）
- 不要使用 `bible2025` 或任何已經公開的密碼
- 建議使用密碼產生器

---

### 步驟 2：清理 Git 歷史記錄（重要！）

⚠️ **警告**：即使您現在修改了程式碼，舊的密碼仍然存在於 Git 歷史記錄中！

#### 選項 A：使用 BFG Repo-Cleaner（推薦）

```bash
# 1. 安裝 BFG Repo-Cleaner
# 下載：https://rtyley.github.io/bfg-repo-cleaner/

# 2. 建立密碼列表檔案
echo "bible2025" > passwords.txt
echo "bible2025_clear_cache" >> passwords.txt

# 3. 清理歷史記錄
java -jar bfg.jar --replace-text passwords.txt bible-reading-line-bot

# 4. 清理並強制推送
cd bible-reading-line-bot
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

#### 選項 B：重新建立儲存庫（最簡單但會失去歷史記錄）

```bash
# 1. 備份當前程式碼
cp -r bible-reading-line-bot bible-reading-line-bot-backup

# 2. 刪除 .git 目錄
cd bible-reading-line-bot
rm -rf .git

# 3. 重新初始化 Git
git init
git add .
git commit -m "Initial commit with security fixes"

# 4. 強制推送到 GitHub
git remote add origin https://github.com/ricklin0821/bible-reading-line-bot.git
git push -f origin master
```

---

### 步驟 3：清理不必要的檔案

```bash
cd bible-reading-line-bot

# 刪除快取檔案
git rm -r --cached __pycache__/
find . -type d -name "__pycache__" -exec rm -rf {} +

# 刪除資料庫檔案
git rm --cached bible_plan.db

# 刪除日誌檔案
git rm --cached server.log

# 刪除備份檔案
git rm --cached *_backup.py *_temp.py

# 提交變更
git commit -m "Remove unnecessary files from Git tracking"
git push origin master
```

---

### 步驟 4：部署修復後的版本

```bash
# 拉取最新程式碼
git pull origin master

# 建置並部署
gcloud builds submit --tag gcr.io/bible-bot-project/bible-bot:latest
gcloud run deploy bible-bot \
  --image gcr.io/bible-bot-project/bible-bot:latest \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --set-env-vars="ADMIN_USERNAME=your_new_admin_username,ADMIN_PASSWORD=your_new_strong_password,CACHE_CLEAR_SECRET=your_cache_clear_secret" \
  --quiet
```

---

### 步驟 5：驗證修復

#### 測試 1：管理後台登入

1. 前往 https://bible-bot-741437082833.asia-east1.run.app/admin
2. 嘗試使用舊密碼 `bible2025` 登入
3. **預期結果**：應該無法登入 ✅
4. 使用新密碼登入
5. **預期結果**：成功登入 ✅

#### 測試 2：API 快取清除

```bash
# 嘗試使用舊密鑰
curl -X POST "https://bible-bot-741437082833.asia-east1.run.app/api/cache/clear?secret=bible2025_clear_cache"
# 預期結果：403 Forbidden ✅

# 使用新密鑰
curl -X POST "https://bible-bot-741437082833.asia-east1.run.app/api/cache/clear?secret=your_new_secret"
# 預期結果：成功清除快取 ✅
```

---

## 📝 最佳實踐

### 1. 永遠不要在程式碼中寫死密碼

❌ **錯誤**：
```python
PASSWORD = "my_password"
API_KEY = "sk-1234567890"
```

✅ **正確**：
```python
import os
PASSWORD = os.environ.get("PASSWORD")
API_KEY = os.environ.get("API_KEY")

if not PASSWORD or not API_KEY:
    raise ValueError("Missing required environment variables")
```

---

### 2. 使用 .env 檔案（本機開發）

```bash
# .env 檔案（不要上傳到 Git！）
ADMIN_USERNAME=admin
ADMIN_PASSWORD=my_strong_password
CACHE_CLEAR_SECRET=my_cache_secret
```

```python
# 在程式碼中載入 .env
from dotenv import load_dotenv
load_dotenv()

import os
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
```

---

### 3. 使用 Secret Manager（生產環境）

Google Cloud Secret Manager 提供更安全的密鑰管理：

```bash
# 建立 secret
gcloud secrets create admin-password --data-file=-
# 輸入密碼後按 Ctrl+D

# 在 Cloud Run 中使用
gcloud run deploy bible-bot \
  --set-secrets="ADMIN_PASSWORD=admin-password:latest"
```

---

### 4. 定期更換密碼

- 每 3-6 個月更換一次管理員密碼
- 如果懷疑密碼洩露，立即更換
- 使用密碼管理器儲存密碼

---

### 5. 啟用 2FA（如果可能）

考慮使用更安全的驗證方式：
- OAuth 2.0
- JWT Token
- 多因素驗證（2FA）

---

## 🔍 檢查清單

部署前請確認：

- [ ] 已設定所有環境變數
- [ ] 已清理 Git 歷史記錄中的密碼
- [ ] 已刪除不必要的檔案
- [ ] 已建立 `.gitignore` 檔案
- [ ] 已測試管理後台登入
- [ ] 已測試 API 快取清除
- [ ] 已更新文件中的密碼說明

---

## 📞 需要協助？

如果在修復過程中遇到問題：

1. 檢查 Cloud Run 日誌：https://console.cloud.google.com/run/detail/asia-east1/bible-bot/logs
2. 確認環境變數是否正確設定
3. 確認 Git 歷史記錄是否已清理
4. 隨時告訴我！

---

## 🎉 修復完成後

完成所有步驟後，您的專案將會：

- ✅ 沒有密碼寫死在程式碼中
- ✅ 所有敏感資訊都使用環境變數
- ✅ Git 歷史記錄已清理
- ✅ 不必要的檔案已移除
- ✅ 有完整的 `.gitignore` 保護

**您的 Bible Bot 現在更安全了！** 🔒
