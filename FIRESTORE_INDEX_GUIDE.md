# Firestore 索引建立指南

## 🚨 問題說明

當新使用者點擊「完成讀經」時，出現以下錯誤：

```
400 The query requires an index. You can create it here: https://console.firebase.google.com/v1/r/project/bible-bot-project/firestore/indexes?create_composite=...
```

這是因為 Firestore 查詢使用了多個 `where` 條件，需要建立**複合索引**。

---

## ✅ 解決方案（3 種方法）

### 方法 1: 點擊錯誤訊息中的連結（最快，推薦）

1. **直接點擊錯誤訊息中的連結**：
   ```
   https://console.firebase.google.com/v1/r/project/bible-bot-project/firestore/indexes?create_composite=ClRwcm9qZWN0cy9iaWJsZS1ib3QtcHJvamVjdC9kYXRhYmFzZXMvKGRlZmF1bHQpL2NvbGxlY3Rpb25Hcm91cHMvYmlibGVfdGV4dC9pbmRleGVzL18QARoNCglib29rX2FiYnIQARoLCgdjaGFwdGVyEAEaDAoIX19uYW1lX18QAQ
   ```

2. **點擊「建立索引」按鈕**

3. **等待索引建立完成**（通常需要 2-5 分鐘）

4. **完成！** 索引建立後，測驗生成功能就能正常運作

---

### 方法 2: 手動在 Firebase Console 建立索引

1. **前往 Firestore 索引頁面**
   - https://console.firebase.google.com/project/bible-bot-project/firestore/indexes

2. **點擊「建立索引」**

3. **設定索引**：
   - **集合 ID**：`bible_text`
   - **欄位 1**：`book_abbr` (遞增)
   - **欄位 2**：`chapter` (遞增)
   - **查詢範圍**：Collection

4. **點擊「建立」**

5. **等待索引建立完成**（狀態從「正在建立」變為「已啟用」）

---

### 方法 3: 使用 Firebase CLI 部署索引（自動化）

#### 步驟 1: 安裝 Firebase CLI

```bash
npm install -g firebase-tools
```

#### 步驟 2: 登入 Firebase

```bash
firebase login
```

#### 步驟 3: 初始化 Firebase 專案

```bash
cd bible-reading-line-bot
firebase init firestore
```

選擇：
- **選擇專案**：`bible-bot-project`
- **Firestore Rules 檔案**：按 Enter（使用預設）
- **Firestore Indexes 檔案**：按 Enter（使用預設）

#### 步驟 4: 部署索引

```bash
firebase deploy --only firestore:indexes
```

#### 步驟 5: 等待完成

索引建立需要 2-5 分鐘，可以在 Firebase Console 查看進度。

---

## 📋 需要建立的索引

### 索引 1: book_abbr + chapter

用於查詢整章經文（`get_verses_by_reference`）

- **集合**：`bible_text`
- **欄位**：
  1. `book_abbr` (遞增)
  2. `chapter` (遞增)

### 索引 2: book_abbr + chapter + verse

用於查詢經文範圍（`get_verses_in_range`）

- **集合**：`bible_text`
- **欄位**：
  1. `book_abbr` (遞增)
  2. `chapter` (遞增)
  3. `verse` (遞增)

---

## 🔍 為什麼需要複合索引？

Firestore 的查詢規則：
- **單一 `where` 條件**：不需要索引
- **多個 `where` 條件**：需要複合索引
- **`where` + `order_by`**：需要複合索引

我們的查詢使用了兩個 `where` 條件：

```python
query = texts_ref.where(
    filter=firestore.FieldFilter('book_abbr', '==', book_abbr)
).where(
    filter=firestore.FieldFilter('chapter', '==', chapter)
)
```

因此需要建立 `book_abbr + chapter` 的複合索引。

---

## ✅ 驗證索引建立成功

### 1. 檢查索引狀態

前往 https://console.firebase.google.com/project/bible-bot-project/firestore/indexes

確認索引狀態為「**已啟用**」（綠色勾勾）

### 2. 測試測驗生成

1. 使用 LINE Bot 點擊「✅ 回報已完成讀經」
2. 應該會顯示測驗題目（填空題或選擇題）
3. 不再出現「抱歉，生成測驗時發生錯誤」

### 3. 檢查日誌

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bible-bot" --limit 20
```

應該看到測驗生成成功的日誌，而不是索引錯誤。

---

## 🚀 索引建立時間

- **小型資料集**（< 10,000 筆）：2-5 分鐘
- **中型資料集**（10,000 - 100,000 筆）：5-15 分鐘
- **大型資料集**（> 100,000 筆）：15-60 分鐘

我們的聖經經文資料約 **31,000 筆**，預計需要 **5-10 分鐘**。

---

## 📝 索引定義檔案

已建立 `firestore.indexes.json` 檔案，內容如下：

```json
{
  "indexes": [
    {
      "collectionGroup": "bible_text",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "book_abbr",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "chapter",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "verse",
          "order": "ASCENDING"
        }
      ]
    },
    {
      "collectionGroup": "bible_text",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "book_abbr",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "chapter",
          "order": "ASCENDING"
        }
      ]
    }
  ]
}
```

---

## 🔄 未來避免此問題

### 方法 1: 在初始化時自動建立索引

在 `database.py` 的 `init_db()` 函數中加入索引建立邏輯（需要 Firebase Admin SDK）

### 方法 2: 使用 CI/CD 自動部署索引

在 `cloudbuild.yaml` 中加入索引部署步驟：

```yaml
- name: 'gcr.io/$PROJECT_ID/firebase'
  args: ['deploy', '--only', 'firestore:indexes']
```

### 方法 3: 文件化所有需要的索引

在專案文件中列出所有需要的索引，新環境部署時先建立索引。

---

## 📞 需要協助？

如果索引建立失敗或遇到問題：

1. **檢查 Firebase Console**：https://console.firebase.google.com/project/bible-bot-project/firestore/indexes
2. **查看錯誤訊息**：索引建立失敗時會顯示原因
3. **重新建立索引**：刪除失敗的索引，重新建立

---

**建議使用方法 1（點擊連結）**，最快速且不需要額外設定！
