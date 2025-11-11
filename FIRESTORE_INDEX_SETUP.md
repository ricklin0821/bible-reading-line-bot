# Firestore 索引建立指南

## 問題說明

小組管理頁面的「查看詳情」功能需要查詢小組留言，使用了以下 Firestore 查詢：

```python
messages_ref.where("group_id", "==", group_id).order_by("created_at", direction="DESCENDING")
```

這個查詢需要建立 **複合索引（Composite Index）**，包含以下欄位：
- `group_id` (Ascending)
- `created_at` (Descending)

---

## 方案一：使用錯誤訊息中的連結（推薦）

### 步驟

1. **觸發錯誤**
   - 訪問小組管理頁面：https://bible-bot-741437082833.asia-east1.run.app/admin/groups-management
   - 點擊任一小組的「查看詳情」按鈕
   - 系統會返回錯誤

2. **查看日誌**
   - 前往 Google Cloud Console 日誌頁面
   - 找到錯誤訊息中的索引建立連結
   - 連結格式類似：
     ```
     https://console.firebase.google.com/v1/r/project/bible-bot-project/firestore/indexes?create_composite=...
     ```

3. **點擊連結建立索引**
   - 點擊錯誤訊息中的連結
   - Firebase Console 會自動填入所需的索引設定
   - 點擊「建立索引」按鈕
   - 等待索引建立完成（通常需要 2-5 分鐘）

---

## 方案二：手動建立索引

### 步驟

1. **前往 Firebase Console**
   - 訪問：https://console.firebase.google.com/project/bible-bot-project/firestore/indexes

2. **建立複合索引**
   - 點擊「建立索引」按鈕
   - 選擇集合：`group_messages`
   - 添加欄位：
     - 欄位 1：`group_id`，排序：**Ascending**
     - 欄位 2：`created_at`，排序：**Descending**
   - 查詢範圍：**Collection**
   - 點擊「建立」

3. **等待索引建立**
   - 索引狀態會顯示為「正在建立」
   - 通常需要 2-5 分鐘
   - 建立完成後狀態會變為「已啟用」

---

## 方案三：使用 Firebase CLI（進階）

如果您想要自動化管理索引，可以使用 Firebase CLI：

### 1. 創建索引配置檔案

在專案根目錄創建 `firestore.indexes.json`：

```json
{
  "indexes": [
    {
      "collectionGroup": "group_messages",
      "queryScope": "COLLECTION",
      "fields": [
        {
          "fieldPath": "group_id",
          "order": "ASCENDING"
        },
        {
          "fieldPath": "created_at",
          "order": "DESCENDING"
        }
      ]
    }
  ],
  "fieldOverrides": []
}
```

### 2. 部署索引

```bash
# 安裝 Firebase CLI（如果還沒安裝）
npm install -g firebase-tools

# 登入 Firebase
firebase login

# 初始化專案（如果還沒初始化）
firebase init firestore

# 部署索引
firebase deploy --only firestore:indexes
```

---

## 驗證索引是否生效

### 方法 1：在 Firebase Console 檢查

1. 前往：https://console.firebase.google.com/project/bible-bot-project/firestore/indexes
2. 確認索引狀態為「已啟用」

### 方法 2：測試功能

1. 訪問小組管理頁面
2. 點擊「查看詳情」
3. 如果能正常顯示留言記錄，表示索引已生效

---

## 索引建立完成後

索引建立完成後，需要：

1. **恢復資料庫排序查詢**（已在程式碼中完成）
   - 使用 `order_by()` 在資料庫層級排序
   - 比在程式中排序效能更好

2. **重新部署應用程式**
   ```powershell
   git pull origin master
   gcloud run deploy bible-bot --source . --region asia-east1 --project bible-bot-project --allow-unauthenticated
   ```

---

## 常見問題

### Q: 索引建立需要多久？
A: 通常 2-5 分鐘，如果資料量大可能需要更長時間。

### Q: 索引會產生額外費用嗎？
A: Firestore 的索引本身不收費，但會佔用儲存空間。對於小型專案影響很小。

### Q: 可以刪除索引嗎？
A: 可以，在 Firebase Console 的索引頁面點擊刪除即可。但刪除後相關查詢會失敗。

### Q: 為什麼需要索引？
A: Firestore 的設計理念是「讀取快速」，所有查詢都需要有對應的索引。單一欄位查詢會自動建立索引，但多欄位查詢（複合查詢）需要手動建立。

---

## 參考資料

- [Firestore 索引官方文件](https://firebase.google.com/docs/firestore/query-data/indexing)
- [Firebase CLI 文件](https://firebase.google.com/docs/cli)
