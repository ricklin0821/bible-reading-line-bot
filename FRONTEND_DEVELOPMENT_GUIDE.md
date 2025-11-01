# 前端開發指南 - 修改首頁和管理後台

**適用對象**：想要修改網站版面但不影響 LINE Bot 功能的開發者

---

## 📁 專案結構

```
bible-reading-line-bot/
├── static/                    # 所有前端檔案都在這裡
│   ├── index.html            # 🏠 首頁（主要修改這個）
│   ├── about.html            # ℹ️ 關於頁面
│   └── admin/                # 管理後台
│       ├── login.html        # 🔐 登入頁面
│       └── dashboard.html    # 📊 管理儀表板
├── main.py                   # ⚠️ 不要動！LINE Bot 主程式
├── database.py               # ⚠️ 不要動！資料庫邏輯
└── ...
```

**重點**：
- ✅ **可以修改**：`static/` 資料夾中的所有 `.html` 檔案
- ❌ **不要修改**：`main.py`、`database.py` 等 Python 檔案（除非您知道自己在做什麼）

---

## 🎯 快速開始：修改首頁

### 步驟 1：在本機開啟專案

```bash
# 進入專案目錄
cd /path/to/bible-reading-line-bot

# 用您喜歡的編輯器開啟
# 例如：VS Code
code static/index.html

# 或者：其他編輯器
# open static/index.html  # macOS
# start static/index.html  # Windows
```

### 步驟 2：本機預覽（可選）

**方法 1：直接用瀏覽器開啟**
```bash
# macOS
open static/index.html

# Windows
start static/index.html

# Linux
xdg-open static/index.html
```

**方法 2：啟動本機伺服器（推薦）**
```bash
# 使用 Python 內建伺服器
cd static
python3 -m http.server 8000

# 然後在瀏覽器開啟
# http://localhost:8000/index.html
```

### 步驟 3：修改內容

`index.html` 是一個**獨立的 HTML 檔案**，所有樣式都內嵌在 `<style>` 標籤中，所有 JavaScript 都在 `<script>` 標籤中。

**常見修改位置**：

#### 1. 修改標題和副標題（第 86-96 行）

```html
<div class="header">
    <h1>📖 一年讀經計畫</h1>  <!-- 修改這裡 -->
    <div class="subtitle">與神同行的屬靈之旅</div>  <!-- 修改這裡 -->
</div>
```

#### 2. 修改介紹文字（第 107-138 行）

```html
<div class="intro-section">
    <h2>為什麼需要讀經計畫？</h2>  <!-- 修改這裡 -->
    <p>
        聖經是神的話語，是我們生命的指引...  <!-- 修改這裡 -->
    </p>
    <!-- 更多內容... -->
</div>
```

#### 3. 修改顏色主題（第 28-40 行）

```css
body {
    font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);  /* 修改背景漸層 */
    min-height: 100vh;
    color: #333;  /* 修改文字顏色 */
    line-height: 1.8;
}
```

**常用顏色**：
- 主色調：`#667eea`（紫藍色）
- 次色調：`#764ba2`（深紫色）
- 強調色：`#fdcb6e`（金黃色）

#### 4. 新增區塊

在 `<div class="content-card">` 內新增任何內容：

```html
<div class="content-card">
    <!-- 現有內容... -->
    
    <!-- 新增您的區塊 -->
    <div class="my-new-section">
        <h2>我的新區塊</h2>
        <p>這是我新增的內容...</p>
    </div>
</div>
```

然後在 `<style>` 標籤中新增樣式：

```css
.my-new-section {
    margin: 40px 0;
    padding: 30px;
    background: #f8f9fa;
    border-radius: 15px;
}

.my-new-section h2 {
    color: #667eea;
    margin-bottom: 20px;
}
```

### 步驟 4：測試修改

1. **儲存檔案**
2. **重新整理瀏覽器**（如果使用本機伺服器）
3. **檢查效果**

### 步驟 5：部署到 Cloud Run

```bash
# 1. 提交變更到 Git
git add static/index.html
git commit -m "Update homepage content"
git push origin master

# 2. 部署到 Cloud Run
gcloud builds submit --tag gcr.io/bible-bot-project/bible-bot:latest
gcloud run deploy bible-bot \
  --image gcr.io/bible-bot-project/bible-bot:latest \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --quiet
```

---

## 🎨 常見修改範例

### 範例 1：修改首頁標題

**修改前**：
```html
<h1>📖 一年讀經計畫</h1>
```

**修改後**：
```html
<h1>📖 與神同行 365 天</h1>
```

### 範例 2：新增一個特色區塊

在 `<div class="content-card">` 內新增：

```html
<div class="features-section">
    <h2>✨ 為什麼選擇我們？</h2>
    <div class="feature-grid">
        <div class="feature-item">
            <div class="feature-icon">🎯</div>
            <h3>個人化計畫</h3>
            <p>根據您的進度自動調整</p>
        </div>
        <div class="feature-item">
            <div class="feature-icon">⏰</div>
            <h3>智能提醒</h3>
            <p>每日定時推送，不錯過任何一天</p>
        </div>
        <div class="feature-item">
            <div class="feature-icon">📝</div>
            <h3>互動測驗</h3>
            <p>加深記憶，鞏固學習</p>
        </div>
    </div>
</div>
```

然後在 `<style>` 中新增樣式：

```css
.features-section {
    margin: 50px 0;
}

.features-section h2 {
    color: #667eea;
    font-size: 2em;
    margin-bottom: 30px;
    text-align: center;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 25px;
    margin-top: 30px;
}

.feature-item {
    background: #f8f9fa;
    padding: 30px;
    border-radius: 15px;
    text-align: center;
    transition: all 0.3s ease;
}

.feature-item:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
}

.feature-icon {
    font-size: 3em;
    margin-bottom: 15px;
}

.feature-item h3 {
    color: #667eea;
    margin-bottom: 10px;
}

.feature-item p {
    color: #666;
    font-size: 0.95em;
}
```

### 範例 3：修改顏色主題為綠色系

在 `<style>` 中修改：

```css
/* 原本的紫色系 */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* 改為綠色系 */
background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);

/* 同時修改其他地方的顏色 */
.intro-section h2 {
    color: #11998e;  /* 原本是 #667eea */
}

.plan-card {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}
```

---

## 📊 修改管理後台

### 檔案位置

- **登入頁面**：`static/admin/login.html`
- **儀表板**：`static/admin/dashboard.html`

### 修改方式

與首頁相同，直接編輯 HTML 檔案即可。

**範例：修改登入頁面標題**

```html
<!-- static/admin/login.html -->
<h1>📊 管理後台登入</h1>  <!-- 修改這裡 -->
```

---

## ⚠️ 注意事項

### 1. 不要修改 JavaScript 功能

`index.html` 中有一些 JavaScript 程式碼用於：
- 顯示讀經計畫預覽
- 處理彈出視窗
- 搜尋和篩選功能

**除非您熟悉 JavaScript，否則不要修改這些程式碼**。

### 2. 不要修改 API 端點

檔案中有一些 API 呼叫，例如：

```javascript
fetch('/preview/plan1')  // 不要修改這個 URL
```

這些是與後端（`main.py`）溝通的端點，修改會導致功能失效。

### 3. 保持響應式設計

現有的 CSS 已經包含響應式設計（RWD），確保在手機上也能正常顯示。

如果新增內容，建議使用：
```css
@media (max-width: 768px) {
    /* 手機版樣式 */
    .my-new-section {
        padding: 15px;
    }
}
```

### 4. 測試跨瀏覽器相容性

修改後建議在以下瀏覽器測試：
- ✅ Chrome
- ✅ Safari
- ✅ Firefox
- ✅ Edge

---

## 🚀 完整開發流程

### 1. 本機開發

```bash
# 1. 開啟專案
cd /path/to/bible-reading-line-bot

# 2. 啟動本機伺服器
cd static
python3 -m http.server 8000

# 3. 在瀏覽器開啟
# http://localhost:8000/index.html

# 4. 修改 index.html
# 5. 重新整理瀏覽器查看效果
# 6. 重複步驟 4-5 直到滿意
```

### 2. 提交變更

```bash
# 1. 檢查變更
git status
git diff static/index.html

# 2. 提交
git add static/index.html
git commit -m "Update homepage: add new features section"

# 3. 推送到 GitHub
git push origin master
```

### 3. 部署到 Cloud Run

```bash
# 建置並部署
gcloud builds submit --tag gcr.io/bible-bot-project/bible-bot:latest
gcloud run deploy bible-bot \
  --image gcr.io/bible-bot-project/bible-bot:latest \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --quiet
```

### 4. 驗證部署

前往您的網站：
https://bible-bot-741437082833.asia-east1.run.app/

檢查修改是否生效。

---

## 🎓 進階技巧

### 1. 使用外部 CSS 檔案

如果 `index.html` 變得太大，可以將 CSS 分離：

**建立 `static/styles.css`**：
```css
/* 將 <style> 標籤中的內容移到這裡 */
body {
    font-family: 'Noto Sans TC', sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
/* ... */
```

**在 `index.html` 中引用**：
```html
<head>
    <!-- 其他 meta 標籤... -->
    <link rel="stylesheet" href="/static/styles.css">
</head>
```

### 2. 使用外部 JavaScript 檔案

**建立 `static/script.js`**：
```javascript
// 將 <script> 標籤中的內容移到這裡
function showPlanPreview(planType) {
    // ...
}
```

**在 `index.html` 中引用**：
```html
<body>
    <!-- 內容... -->
    <script src="/static/script.js"></script>
</body>
```

### 3. 新增圖片

**放置圖片**：
```bash
# 將圖片放到 static 資料夾
cp my-image.png static/
```

**在 HTML 中使用**：
```html
<img src="/static/my-image.png" alt="描述">
```

---

## 📝 常見問題

### Q1: 修改後本機看到效果，但部署後沒有變化？

**A**: 可能是瀏覽器快取問題。

**解決方法**：
1. 強制重新整理：`Ctrl + Shift + R`（Windows）或 `Cmd + Shift + R`（Mac）
2. 清除瀏覽器快取
3. 使用無痕模式測試

### Q2: 修改後網站壞掉了怎麼辦？

**A**: 使用 Git 回復到之前的版本。

```bash
# 查看最近的 commit
git log --oneline

# 回復到上一個版本
git revert HEAD

# 或者直接重置（小心使用！）
git reset --hard HEAD~1

# 重新部署
gcloud builds submit --tag gcr.io/bible-bot-project/bible-bot:latest
gcloud run deploy bible-bot \
  --image gcr.io/bible-bot-project/bible-bot:latest \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --quiet
```

### Q3: 可以使用 Bootstrap 或 Tailwind CSS 嗎？

**A**: 可以！只需要在 `<head>` 中引入 CDN：

**Bootstrap**：
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
```

**Tailwind CSS**：
```html
<script src="https://cdn.tailwindcss.com"></script>
```

### Q4: 修改會影響 LINE Bot 功能嗎？

**A**: **不會**！只要您只修改 `static/` 資料夾中的檔案，LINE Bot 功能完全不受影響。

LINE Bot 的邏輯都在 `main.py` 中，與前端頁面是分開的。

---

## 🎉 總結

### 修改首頁的完整流程

1. **開啟檔案**：`static/index.html`
2. **本機預覽**：`python3 -m http.server 8000`
3. **修改內容**：編輯 HTML、CSS
4. **測試效果**：重新整理瀏覽器
5. **提交變更**：`git add` → `git commit` → `git push`
6. **部署上線**：`gcloud builds submit` → `gcloud run deploy`
7. **驗證結果**：開啟網站檢查

### 安全原則

- ✅ **可以修改**：`static/` 中的所有 HTML、CSS、JavaScript
- ❌ **不要修改**：`main.py`、`database.py`、API 端點
- ⚠️ **小心修改**：JavaScript 功能邏輯

---

**祝您開發順利！** 🚀

如果遇到問題，隨時查看這份指南或詢問協助。
