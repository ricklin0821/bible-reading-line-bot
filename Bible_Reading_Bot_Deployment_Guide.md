# 一年讀經計畫 LINE Bot 系統部署與使用指南

**作者：** Manus AI

## 摘要

本文件提供「一年讀經計畫 LINE Bot 系統」的部署和使用指南。該系統基於 **FastAPI** 和 **SQLite** 資料庫，使用 **LINE Messaging API** 實現。它提供兩種讀經計畫選擇、每日經文推送、讀經回報以及經文填充題測驗等功能。**此外，系統還包含一個網頁介面，用於預覽和規劃讀經計畫。**

## 1. 系統架構與功能

本系統採用 Webhooks + 後端伺服器 + 資料庫的標準架構。

| 組件 | 技術/角色 | 說明 |
| :--- | :--- | :--- |
| **後端伺服器** | Python (FastAPI) | 處理所有業務邏輯、LINE Webhook 請求，並提供網頁預覽所需的 API 接口。 |
| **資料庫** | SQLite (SQLAlchemy ORM) | 儲存使用者資料、讀經計畫進度、和合本聖經經文。**注意：Cloud Run 部署使用 SQLite，資料會在容器重啟時丟失，建議正式環境升級為 Cloud SQL 等外部資料庫。** |
| **LINE Bot** | LINE Messaging API | 使用者介面，負責訊息收發與互動。 |
| **網頁介面** | HTML/CSS/JavaScript | 提供讀經計畫的預覽、選擇和經文詳情查看功能。 |
| **排程服務** | 外部 Cron Job/排程器 | 每日定時呼叫 `/schedule/daily_push` API，實現每日推送。 |

**核心功能：**

1.  **計畫選擇：** 提供「按卷順序計畫」和「平衡讀經計畫」兩種一年讀經選項。
2.  **每日推送：** 每日定時將當天的讀經範圍推送給使用者。
3.  **讀經回報與測驗：** 使用者回報讀經後，系統會隨機抽取 3 題經文填充題進行測驗。
4.  **測驗互動：** 答對給予高度肯定；第一次答錯提示經文；第二次答錯出示答案並鼓勵。
5.  **網頁預覽：** 透過網頁介面，使用者可以選擇計畫、開始日期，並瀏覽整年的讀經進度及經文內容。

## 2. 程式碼檔案清單

以下是構成系統的關鍵檔案：

| 檔案名稱 | 說明 |
| :--- | :--- |
| `main.py` | FastAPI 應用程式主入口，包含 LINE Webhook 處理、API 路由和靜態檔案服務。 |
| `api_routes.py` | 專門用於網頁預覽功能的 API 路由 (例如：獲取讀經計畫、獲取經文詳情)。 |
| `index.html` | 讀經計畫預覽網頁的前端介面 (HTML/CSS/JavaScript)。 |
| `database.py` | 定義資料庫連線、SQLAlchemy ORM 模型 (`User`, `BiblePlan`, `BibleText`) 和資料庫初始化/資料匯入邏輯。 |
| `quiz_generator.py` | 實現填充題生成 (`generate_quiz_for_user`) 和測驗答案處理 (`process_quiz_answer`) 的核心邏輯。 |
| `prepare_data.py` | 資料準備腳本，用於從原始資料中提取聖經經文，並生成兩種讀經計畫的每日進度表。 |
| `data/bible_text.csv` | 和合本聖經經文資料。 |
| `data/bible_plans.csv` | 兩種讀經計畫的每日經文範圍。 |
| `Dockerfile` | Docker 容器配置文件，用於 Cloud Run 部署。 |
| `requirements.txt` | Python 依賴項清單。 |

## 3. 部署步驟：使用 Google Cloud Run (最推薦)

本章節將指導您如何一步步將專案部署到 Google Cloud Run。

### 步驟 3.1：Google Cloud 帳號與專案準備

1.  **註冊 Google Cloud Platform (GCP)：** 訪問 [Google Cloud 網站]，註冊並啟用您的帳號。新用戶通常有免費試用額度。
2.  **建立 GCP 專案：** 在 GCP Console 中建立一個新的專案（例如：`bible-bot-project`）。
3.  **啟用 API：** 確保您的專案已啟用 **Cloud Run API** 和 **Cloud Build API**。
4.  **安裝 gcloud CLI：** 在您的電腦上安裝 [Google Cloud CLI (gcloud)]。

### 步驟 3.2：本地環境與程式碼準備

1.  **安裝 Git：** 確保您的電腦已安裝 Git。
2.  **下載專案程式碼：** 打開您的終端機或命令提示字元，將專案從 GitHub 克隆到您的電腦：
    ```bash
    git clone https://github.com/ricksgemini0857/bible-reading-line-bot.git
    cd bible-reading-line-bot
    ```
3.  **檢查部署檔案：** 確認專案根目錄下有 `Dockerfile` 和 `requirements.txt` 檔案。

### 步驟 3.3：LINE Bot 金鑰準備

1.  **建立 LINE 官方帳號：** 在 [LINE Developers Console] 建立一個新的 Messaging API Channel。
2.  **取得金鑰：** 記下以下兩個金鑰，它們將作為環境變數使用：
    *   **Channel Access Token**
    *   **Channel Secret**

### 步驟 3.4：一鍵部署到 Cloud Run

請在您的終端機中執行以下指令。

1.  **登入 gcloud CLI：**
    ```bash
    gcloud auth login
    ```
    *   這會打開一個瀏覽器視窗，請登入您的 Google 帳號。

2.  **設定專案 ID：**
    ```bash
    # 將 [YOUR-PROJECT-ID] 替換為您在步驟 3.1 建立的專案 ID
    gcloud config set project [YOUR-PROJECT-ID]
    ```

3.  **構建並部署服務：**
    *   請將 `[YOUR-REGION]` 替換為您希望部署的區域（例如：`asia-east1`）。
    *   請將 `[YOUR-CHANNEL-ACCESS-TOKEN]` 和 `[YOUR-CHANNEL-SECRET]` 替換為您在步驟 3.3 取得的金鑰。

    ```bash
    # 構建 Docker 映像並上傳至 Google Container Registry
    gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/bible-bot

    # 部署到 Cloud Run
    gcloud run deploy bible-bot \
      --image gcr.io/$(gcloud config get-value project)/bible-bot \
      --platform managed \
      --region [YOUR-REGION] \
      --allow-unauthenticated \
      --set-env-vars LINE_CHANNEL_ACCESS_TOKEN="[YOUR-CHANNEL-ACCESS-TOKEN]",LINE_CHANNEL_SECRET="[YOUR-CHANNEL-SECRET]"
    ```
    *   **重要：** 部署時，請務必選擇 **`--allow-unauthenticated`** 允許未經驗證的存取，這樣 LINE Webhook 和網頁預覽才能正常運作。

4.  **獲取服務網址：** 部署完成後，終端機將會輸出一個 **Service URL**，這就是您的公開網址。
    *   **公開網址格式：** `https://[Cloud Run 服務網址]`

### 步驟 3.5：設定 LINE Webhook

1.  **複製 Webhook URL：** 將您在步驟 3.4 獲取的 **Service URL** 加上 `/webhook`，形成完整的 Webhook URL。
    *   **範例：** 如果您的 Service URL 是 `https://bible-bot-xxxxxxx-an.a.run.app`
    *   **完整的 Webhook URL 是：** `https://bible-bot-xxxxxxx-an.a.run.app/webhook`

2.  **設定 LINE Developers Console：**
    *   回到 [LINE Developers Console]，進入您的 Channel 設定頁面。
    *   在 **Messaging API** 設定中，找到 **Webhook URL** 欄位，貼上您完整的 Webhook URL。
    *   點擊 **Verify** 確認連線成功。
    *   確保 **Use webhook** 選項已開啟。

### 步驟 3.6：設定每日推送排程 (Cloud Scheduler)

由於 Cloud Run 會在沒有流量時縮減到零，傳統的 Cron Job 不適用。我們使用 **Google Cloud Scheduler** 來定時呼叫 API。

1.  **啟用 Cloud Scheduler API：** 在 GCP Console 中啟用 **Cloud Scheduler API**。
2.  **建立排程作業：** 在 Cloud Scheduler 介面中，建立一個新的作業：
    *   **頻率 (Frequency)：** 每天早上 6 點 (例如：`0 6 * * *`)
    *   **目標類型 (Target type)：** HTTP
    *   **URL：** 貼上您的服務網址加上 `/schedule/daily_push` (例如：`https://bible-bot-xxxxxxx-an.a.run.app/schedule/daily_push`)
    *   **HTTP 方法 (HTTP method)：** POST
    *   **重要：** 由於 Cloud Run 服務是公開的，您可能需要設定 **OIDC 令牌**以確保只有排程器可以呼叫此 API，但為簡化流程，您可以暫時跳過此步驟，或在 Cloud Run 服務設定中限制外部存取。

## 4. 使用者操作指南

### 4.1. 網頁預覽功能

使用者可以直接訪問您的 **Service URL**，在網頁上：
1.  **選擇**「按卷順序計畫」或「平衡讀經計畫」。
2.  **選擇**開始日期。
3.  點擊「**載入計畫**」按鈕，即可看到 365 天的讀經進度。
4.  點擊任一天的卡片，即可在下方查看該天的**完整經文內容**。

### 4.2. LINE Bot 互動

1.  **首次使用：** 加入 LINE 官方帳號，選擇讀經計畫。
2.  **每日讀經：** 收到每日推送的讀經範圍。
3.  **回報與測驗：** 讀完後回覆 `回報讀經` 或 `已讀完` 開始測驗。
    *   測驗結束後，系統會自動推進到下一天。

---

## 參考資料

[1] Google Cloud 網站. [https://cloud.google.com/](https://cloud.google.com/)
[2] Google Cloud CLI (gcloud) 安裝指南. [https://cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)
[3] LINE Developers Console. [https://developers.line.biz/console/](https://developers.line.biz/console/)
[4] Google Cloud Run 官方文檔. [https://cloud.google.com/run](https://cloud.google.com/run)
