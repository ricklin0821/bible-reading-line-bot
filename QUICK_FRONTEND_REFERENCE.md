# 前端修改快速參考

**5 分鐘快速上手指南**

---

## 📂 檔案位置

```
static/
├── index.html          👈 首頁（主要修改這個）
├── about.html          👈 關於頁面
└── admin/
    ├── login.html      👈 管理後台登入
    └── dashboard.html  👈 管理後台儀表板
```

---

## 🚀 快速流程

### 1. 修改首頁

```bash
# 1. 用編輯器開啟
code static/index.html

# 2. 本機預覽（可選）
cd static && python3 -m http.server 8000
# 瀏覽器開啟 http://localhost:8000/index.html

# 3. 修改內容並儲存

# 4. 提交並部署
git add static/index.html
git commit -m "Update homepage"
git push origin master

gcloud builds submit --tag gcr.io/bible-bot-project/bible-bot:latest
gcloud run deploy bible-bot \
  --image gcr.io/bible-bot-project/bible-bot:latest \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --quiet
```

---

## 🎨 常見修改

### 修改標題

**位置**：第 86-96 行

```html
<div class="header">
    <h1>📖 一年讀經計畫</h1>  <!-- 改這裡 -->
    <div class="subtitle">與神同行的屬靈之旅</div>  <!-- 改這裡 -->
</div>
```

### 修改顏色

**位置**：第 36 行（背景）

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

**常用顏色組合**：
- 紫色系：`#667eea` → `#764ba2`
- 綠色系：`#11998e` → `#38ef7d`
- 藍色系：`#2193b0` → `#6dd5ed`
- 橘色系：`#f46b45` → `#eea849`

### 新增區塊

在 `<div class="content-card">` 內新增：

```html
<div class="my-section">
    <h2>我的標題</h2>
    <p>我的內容...</p>
</div>
```

在 `<style>` 中新增樣式：

```css
.my-section {
    margin: 40px 0;
    padding: 30px;
    background: #f8f9fa;
    border-radius: 15px;
}

.my-section h2 {
    color: #667eea;
    margin-bottom: 20px;
}
```

---

## ⚠️ 注意事項

### ✅ 可以修改
- `static/` 資料夾中的所有 `.html` 檔案
- HTML 內容、CSS 樣式
- 文字、顏色、排版

### ❌ 不要修改
- `main.py`（LINE Bot 主程式）
- `database.py`（資料庫邏輯）
- JavaScript 中的 API 端點（如 `/preview/plan1`）
- JavaScript 功能邏輯（除非您熟悉 JS）

---

## 🆘 緊急救援

### 網站壞掉了？

```bash
# 回復到上一個版本
git revert HEAD
git push origin master

# 重新部署
gcloud builds submit --tag gcr.io/bible-bot-project/bible-bot:latest
gcloud run deploy bible-bot \
  --image gcr.io/bible-bot-project/bible-bot:latest \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated \
  --quiet
```

### 部署後沒有變化？

```bash
# 強制重新整理瀏覽器
# Windows: Ctrl + Shift + R
# Mac: Cmd + Shift + R

# 或使用無痕模式測試
```

---

## 📚 完整文件

詳細說明請參考：`FRONTEND_DEVELOPMENT_GUIDE.md`

---

**就是這麼簡單！** 🎉
