# 一年讀經計畫 LINE Bot 系統部署與使用指南

**作者：** Manus AI

## 摘要

本文件提供「一年讀經計畫 LINE Bot 系統」的部署和使用指南。該系統基於 **FastAPI** 和 **SQLite** 資料庫，使用 **LINE Messaging API** 實現。它提供兩種讀經計畫選擇、每日經文推送、讀經回報以及經文填充題測驗等功能。

## 1. 系統架構與功能

本系統採用 Webhooks + 後端伺服器 + 資料庫的標準架構。

| 組件 | 技術/角色 | 說明 |
| :--- | :--- | :--- |
| **後端伺服器** | Python (FastAPI) | 處理所有業務邏輯、LINE Webhook 請求。 |
| **資料庫** | SQLite (SQLAlchemy ORM) | 儲存使用者資料、讀經計畫進度、和合本聖經經文。 |
| **LINE Bot** | LINE Messaging API | 使用者介面，負責訊息收發與互動。 |
| **排程服務** | 外部 Cron Job/排程器 | 每日定時呼叫 `/schedule/daily_push` API，實現每日推送。 |

**核心功能：**

1.  **計畫選擇：** 提供「按卷順序計畫」和「平衡讀經計畫」兩種一年讀經選項。
2.  **每日推送：** 每日定時將當天的讀經範圍推送給使用者。
3.  **讀經回報與測驗：** 使用者回報讀經後，系統會隨機抽取 3 題經文填充題進行測驗。
4.  **測驗互動：** 答對給予高度肯定；第一次答錯提示經文；第二次答錯出示答案並鼓勵。

## 2. 程式碼檔案清單

以下是構成系統的關鍵檔案：

| 檔案名稱 | 說明 |
| :--- | :--- |
| `main.py` | FastAPI 應用程式主入口，包含 LINE Webhook 處理、事件處理器和 `/schedule/daily_push` API。 |
| `database.py` | 定義資料庫連線、SQLAlchemy ORM 模型 (`User`, `BiblePlan`, `BibleText`) 和資料庫初始化/資料匯入邏輯。 |
| `quiz_generator.py` | 實現填充題生成 (`generate_quiz_for_user`) 和測驗答案處理 (`process_quiz_answer`) 的核心邏輯。 |
| `prepare_data.py` | 資料準備腳本，用於從原始資料中提取聖經經文，並生成兩種讀經計畫的每日進度表 (`data/bible_text.csv` 和 `data/bible_plans.csv`)。 |
| `data/bible_text.csv` | 和合本聖經經文資料。 |
| `data/bible_plans.csv` | 兩種讀經計畫的每日經文範圍。 |

## 3. 部署步驟

### 步驟 3.1：環境準備

1.  **安裝 Python 依賴項：**
    ```bash
    pip3 install fastapi uvicorn python-multipart sqlalchemy line-bot-sdk pandas
    ```

2.  **準備資料：**
    執行資料準備腳本，它會創建 `data` 目錄並生成所需的 CSV 檔案。
    ```bash
    # 確保您已經克隆了包含 bibleText.js 的倉庫 (例如 xuan9/ChineseBibleSearchJS)
    # 如果沒有，請先執行: gh repo clone xuan9/ChineseBibleSearchJS
    python3 prepare_data.py
    ```

3.  **初始化資料庫：**
    執行 `database.py` 腳本，將 CSV 資料匯入 SQLite 資料庫 (`bible_plan.db`)。
    ```bash
    python3 database.py
    ```

### 步驟 3.2：LINE Bot 設定

1.  **建立 LINE 官方帳號：** 在 [LINE Developers Console] 建立一個新的 Messaging API Channel。
2.  **取得金鑰：** 記下以下資訊：
    *   **Channel Access Token**
    *   **Channel Secret**
3.  **設定環境變數：** 在您的伺服器環境中設定以下變數：
    ```bash
    export LINE_CHANNEL_ACCESS_TOKEN="您的 Channel Access Token"
    export LINE_CHANNEL_SECRET="您的 Channel Secret"
    ```

### 步驟 3.3：啟動伺服器

使用 Uvicorn 啟動 FastAPI 應用程式。建議使用 `nohup` 或 Supervisor 等工具在背景運行。

```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 &
```

### 步驟 3.4：設定 Webhook

1.  **取得伺服器 URL：** 確保您的伺服器有一個公開可訪問的 URL (例如：`https://your-server.com`)。
2.  **設定 Webhook URL：** 在 LINE Developers Console 的 Channel 設定頁面中，將 **Webhook URL** 設置為：
    ```
    https://your-server.com/webhook
    ```
3.  **啟用 Webhook：** 確保 Webhook 功能已開啟。

### 步驟 3.5：設定每日推送排程

您需要設定一個外部排程服務，每日定時 (例如：每天早上 6 點) 呼叫伺服器上的 `/schedule/daily_push` API。

**範例 (使用 Linux Cron Job)：**

編輯您的 Cron 表：
```bash
crontab -e
```

加入以下行 (假設您的伺服器 URL 是 `http://localhost:8000`，請替換為實際的公開 URL)：
```cron
# 每天早上 6 點執行一次每日推送
0 6 * * * curl -X POST http://localhost:8000/schedule/daily_push
```

## 4. 使用者操作指南

### 4.1. 首次使用

1.  使用者加入您的 LINE 官方帳號。
2.  Bot 會自動發送歡迎訊息，並提示使用者選擇讀經計畫：
    *   **1. 按卷順序計畫**
    *   **2. 平衡讀經計畫**
3.  使用者點擊對應的按鈕或回覆數字，即可開始讀經計畫。Bot 會立即發送第一天的讀經範圍。

### 4.2. 每日讀經與回報

1.  **每日推送：** 每天早上 6 點 (或您設定的時間)，Bot 會推送當天的讀經範圍。
2.  **讀經回報：** 當使用者讀完經文後，可以發送以下任一文字：
    *   `已讀完`
    *   `回報讀經`
    *   `開始測驗`
3.  **測驗流程：**
    *   Bot 隨機出 3 題經文填充題。
    *   **答對：** 收到高度肯定訊息，並進入下一題。
    *   **第一次答錯：** 收到鼓勵，並提示完整的經文，要求重新回答。
    *   **第二次答錯：** 收到鼓勵，Bot 會直接出示正確答案，並自動進入下一題 (或結束測驗)。
4.  **完成：** 3 題測驗全部結束後，Bot 會發送恭喜訊息，並自動將使用者的進度推進到下一天，同時發送下一天的讀經範圍。

---

## 參考資料

[1] LINE Developers Console. [https://developers.line.biz/console/](https://developers.line.biz/console/)
[2] FastAPI 官方文檔. [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
[3] LINE Bot SDK for Python. [https://github.com/line/line-bot-sdk-python](https://github.com/line/line-bot-sdk-python)
[4] SQLAlchemy 官方文檔. [https://www.sqlalchemy.org/](https://www.sqlalchemy.org/)
