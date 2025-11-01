# 前端修改範例集

**實用的修改範例，直接複製貼上即可使用**

---

## 🎨 範例 1：新增特色區塊

### 效果
顯示 3 個特色卡片，包含圖示、標題和說明。

### 程式碼

**HTML**（插入到 `<div class="content-card">` 內）：

```html
<div class="features-section">
    <h2>✨ 為什麼選擇我們？</h2>
    <div class="feature-grid">
        <div class="feature-item">
            <div class="feature-icon">🎯</div>
            <h3>個人化計畫</h3>
            <p>根據您的進度自動調整讀經計畫</p>
        </div>
        <div class="feature-item">
            <div class="feature-icon">⏰</div>
            <h3>智能提醒</h3>
            <p>每日定時推送，不錯過任何一天</p>
        </div>
        <div class="feature-item">
            <div class="feature-icon">📝</div>
            <h3>互動測驗</h3>
            <p>加深記憶，鞏固學習成果</p>
        </div>
    </div>
</div>
```

**CSS**（插入到 `<style>` 標籤內）：

```css
.features-section {
    margin: 50px 0;
    padding: 40px 0;
    border-top: 2px solid #e9ecef;
}

.features-section h2 {
    color: #667eea;
    font-size: 2em;
    margin-bottom: 40px;
    text-align: center;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 30px;
    margin-top: 30px;
}

.feature-item {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 35px 25px;
    border-radius: 15px;
    text-align: center;
    transition: all 0.3s ease;
    border: 2px solid transparent;
}

.feature-item:hover {
    transform: translateY(-8px);
    box-shadow: 0 15px 35px rgba(102, 126, 234, 0.25);
    border-color: #667eea;
}

.feature-icon {
    font-size: 3.5em;
    margin-bottom: 20px;
    animation: bounce 2s infinite;
}

.feature-item h3 {
    color: #667eea;
    font-size: 1.3em;
    margin-bottom: 12px;
}

.feature-item p {
    color: #666;
    font-size: 0.95em;
    line-height: 1.6;
}

@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
}
```

---

## 📊 範例 2：新增統計數字區塊

### 效果
顯示使用者數量、完成天數等統計數字。

### 程式碼

**HTML**：

```html
<div class="stats-section">
    <h2>📈 我們的成果</h2>
    <div class="stats-grid">
        <div class="stat-item">
            <div class="stat-number">1,234</div>
            <div class="stat-label">活躍使用者</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">45,678</div>
            <div class="stat-label">完成天數</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">98%</div>
            <div class="stat-label">滿意度</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">365</div>
            <div class="stat-label">全年無休</div>
        </div>
    </div>
</div>
```

**CSS**：

```css
.stats-section {
    margin: 50px 0;
    padding: 50px 30px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    color: white;
}

.stats-section h2 {
    color: white;
    font-size: 2em;
    margin-bottom: 40px;
    text-align: center;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 30px;
}

.stat-item {
    text-align: center;
    padding: 20px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    backdrop-filter: blur(10px);
    transition: all 0.3s ease;
}

.stat-item:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: scale(1.05);
}

.stat-number {
    font-size: 3em;
    font-weight: bold;
    margin-bottom: 10px;
    color: #ffeaa7;
}

.stat-label {
    font-size: 1.1em;
    opacity: 0.9;
}
```

---

## 💬 範例 3：新增見證區塊

### 效果
顯示使用者見證卡片。

### 程式碼

**HTML**：

```html
<div class="testimonials-section">
    <h2>💬 使用者見證</h2>
    <div class="testimonials-grid">
        <div class="testimonial-card">
            <div class="testimonial-quote">"</div>
            <p class="testimonial-text">
                透過這個讀經計畫，我終於完成了一年讀完聖經的目標！
                每天的提醒和測驗讓我更深入理解神的話語。
            </p>
            <div class="testimonial-author">
                <div class="author-name">張小明</div>
                <div class="author-title">使用者</div>
            </div>
        </div>
        
        <div class="testimonial-card">
            <div class="testimonial-quote">"</div>
            <p class="testimonial-text">
                這個 LINE Bot 真的很方便！不用下載 App，
                直接在 LINE 就能讀經，還有互動測驗幫助記憶。
            </p>
            <div class="testimonial-author">
                <div class="author-name">李小華</div>
                <div class="author-title">使用者</div>
            </div>
        </div>
        
        <div class="testimonial-card">
            <div class="testimonial-quote">"</div>
            <p class="testimonial-text">
                感謝這個平台，讓我養成每天讀經的習慣。
                神的話語成為我生命中的力量和指引。
            </p>
            <div class="testimonial-author">
                <div class="author-name">王小美</div>
                <div class="author-title">使用者</div>
            </div>
        </div>
    </div>
</div>
```

**CSS**：

```css
.testimonials-section {
    margin: 50px 0;
    padding: 40px 0;
}

.testimonials-section h2 {
    color: #667eea;
    font-size: 2em;
    margin-bottom: 40px;
    text-align: center;
}

.testimonials-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 30px;
}

.testimonial-card {
    background: #f8f9fa;
    padding: 35px;
    border-radius: 15px;
    position: relative;
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.08);
    transition: all 0.3s ease;
}

.testimonial-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
}

.testimonial-quote {
    font-size: 5em;
    color: #667eea;
    opacity: 0.2;
    position: absolute;
    top: 10px;
    left: 20px;
    font-family: Georgia, serif;
}

.testimonial-text {
    font-size: 1em;
    line-height: 1.8;
    color: #555;
    margin-bottom: 25px;
    position: relative;
    z-index: 1;
}

.testimonial-author {
    border-top: 2px solid #e9ecef;
    padding-top: 20px;
}

.author-name {
    font-weight: bold;
    color: #667eea;
    font-size: 1.1em;
    margin-bottom: 5px;
}

.author-title {
    color: #999;
    font-size: 0.9em;
}
```

---

## 🎯 範例 4：新增 FAQ 常見問題

### 效果
可展開/收合的常見問題區塊。

### 程式碼

**HTML**：

```html
<div class="faq-section">
    <h2>❓ 常見問題</h2>
    <div class="faq-container">
        <div class="faq-item">
            <div class="faq-question" onclick="toggleFAQ(this)">
                <span>如何開始使用讀經計畫？</span>
                <span class="faq-icon">+</span>
            </div>
            <div class="faq-answer">
                只需要加入我們的 LINE Bot，選擇適合您的讀經計畫，
                系統就會每天自動推送當天的讀經進度給您。
            </div>
        </div>
        
        <div class="faq-item">
            <div class="faq-question" onclick="toggleFAQ(this)">
                <span>如果錯過了某一天怎麼辦？</span>
                <span class="faq-icon">+</span>
            </div>
            <div class="faq-answer">
                沒關係！系統會保留您的進度，您可以隨時補上錯過的部分。
                我們的目標是幫助您養成習慣，而不是給您壓力。
            </div>
        </div>
        
        <div class="faq-item">
            <div class="faq-question" onclick="toggleFAQ(this)">
                <span>測驗題目會很難嗎？</span>
                <span class="faq-icon">+</span>
            </div>
            <div class="faq-answer">
                測驗題目都是基於當天的讀經內容，主要是幫助您加深記憶。
                題目設計簡單易懂，不會給您太大壓力。
            </div>
        </div>
        
        <div class="faq-item">
            <div class="faq-question" onclick="toggleFAQ(this)">
                <span>可以更改讀經計畫嗎？</span>
                <span class="faq-icon">+</span>
            </div>
            <div class="faq-answer">
                可以！您可以隨時在 LINE Bot 中切換不同的讀經計畫，
                系統會自動調整您的進度。
            </div>
        </div>
    </div>
</div>
```

**CSS**：

```css
.faq-section {
    margin: 50px 0;
    padding: 40px 0;
    border-top: 2px solid #e9ecef;
}

.faq-section h2 {
    color: #667eea;
    font-size: 2em;
    margin-bottom: 40px;
    text-align: center;
}

.faq-container {
    max-width: 800px;
    margin: 0 auto;
}

.faq-item {
    margin-bottom: 15px;
    border: 2px solid #e9ecef;
    border-radius: 10px;
    overflow: hidden;
    transition: all 0.3s ease;
}

.faq-item:hover {
    border-color: #667eea;
}

.faq-question {
    background: #f8f9fa;
    padding: 20px 25px;
    cursor: pointer;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    color: #333;
    transition: all 0.3s ease;
}

.faq-question:hover {
    background: #667eea;
    color: white;
}

.faq-question:hover .faq-icon {
    color: white;
}

.faq-icon {
    font-size: 1.5em;
    color: #667eea;
    font-weight: bold;
    transition: all 0.3s ease;
}

.faq-answer {
    max-height: 0;
    overflow: hidden;
    padding: 0 25px;
    background: white;
    color: #555;
    line-height: 1.8;
    transition: all 0.3s ease;
}

.faq-item.active .faq-answer {
    max-height: 200px;
    padding: 20px 25px;
}

.faq-item.active .faq-icon {
    transform: rotate(45deg);
}
```

**JavaScript**（插入到 `<script>` 標籤內）：

```javascript
function toggleFAQ(element) {
    const faqItem = element.parentElement;
    const isActive = faqItem.classList.contains('active');
    
    // 關閉所有其他 FAQ
    document.querySelectorAll('.faq-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 切換當前 FAQ
    if (!isActive) {
        faqItem.classList.add('active');
    }
}
```

---

## 🌈 範例 5：修改顏色主題

### 綠色主題

```css
/* 背景漸層 */
body {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

/* 標題顏色 */
.intro-section h2,
.plan-section h2,
.features-section h2 {
    color: #11998e;
}

/* 卡片背景 */
.plan-card {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

/* 按鈕顏色 */
.action-btn {
    background: #11998e;
}

.action-btn:hover {
    background: #0d7a6f;
}
```

### 藍色主題

```css
/* 背景漸層 */
body {
    background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%);
}

/* 標題顏色 */
.intro-section h2,
.plan-section h2,
.features-section h2 {
    color: #2193b0;
}

/* 卡片背景 */
.plan-card {
    background: linear-gradient(135deg, #2193b0 0%, #6dd5ed 100%);
}

/* 按鈕顏色 */
.action-btn {
    background: #2193b0;
}

.action-btn:hover {
    background: #1a7590;
}
```

### 橘色主題

```css
/* 背景漸層 */
body {
    background: linear-gradient(135deg, #f46b45 0%, #eea849 100%);
}

/* 標題顏色 */
.intro-section h2,
.plan-section h2,
.features-section h2 {
    color: #f46b45;
}

/* 卡片背景 */
.plan-card {
    background: linear-gradient(135deg, #f46b45 0%, #eea849 100%);
}

/* 按鈕顏色 */
.action-btn {
    background: #f46b45;
}

.action-btn:hover {
    background: #d95a38;
}
```

---

## 📱 範例 6：新增社群媒體連結

### 程式碼

**HTML**（插入到頁尾）：

```html
<div class="social-section">
    <h3>🌐 關注我們</h3>
    <div class="social-links">
        <a href="https://www.facebook.com/your-page" class="social-link" target="_blank">
            <span class="social-icon">📘</span>
            <span>Facebook</span>
        </a>
        <a href="https://www.instagram.com/your-account" class="social-link" target="_blank">
            <span class="social-icon">📷</span>
            <span>Instagram</span>
        </a>
        <a href="https://www.youtube.com/your-channel" class="social-link" target="_blank">
            <span class="social-icon">📺</span>
            <span>YouTube</span>
        </a>
        <a href="mailto:contact@example.com" class="social-link">
            <span class="social-icon">✉️</span>
            <span>Email</span>
        </a>
    </div>
</div>
```

**CSS**：

```css
.social-section {
    margin: 50px 0;
    padding: 40px 30px;
    background: #f8f9fa;
    border-radius: 15px;
    text-align: center;
}

.social-section h3 {
    color: #667eea;
    font-size: 1.8em;
    margin-bottom: 30px;
}

.social-links {
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
}

.social-link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 15px 30px;
    background: white;
    border-radius: 25px;
    text-decoration: none;
    color: #333;
    font-weight: 600;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
}

.social-link:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    color: #667eea;
}

.social-icon {
    font-size: 1.5em;
}
```

---

## 🎉 使用方式

1. **選擇範例**：從上面選擇您想要的範例
2. **複製程式碼**：複製 HTML 和 CSS 程式碼
3. **貼上到檔案**：
   - HTML → 貼到 `<div class="content-card">` 內
   - CSS → 貼到 `<style>` 標籤內
   - JavaScript → 貼到 `<script>` 標籤內
4. **儲存並測試**：儲存檔案，重新整理瀏覽器查看效果
5. **部署上線**：滿意後提交並部署

---

**提示**：您可以混合使用多個範例，打造獨一無二的首頁！🚀
