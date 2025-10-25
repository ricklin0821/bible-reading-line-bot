# 一年讀經計畫 LINE Bot 系統部署與使用指南

**作者：** Manus AI

## 摘要

本文件提供「一年讀經計畫 LINE Bot 系統」的部署和使用指南。該系統基於 **FastAPI** 和 **SQLite** 資料庫，使用 **LINE Messaging API** 實現。它提供兩種讀經計畫選擇、每日經文推送、讀經回報以及經文填充題測驗等功能。**此外，系統還包含一個網頁介面，用於預覽和規劃讀經計畫。**

## 1. 系統架構與功能

本系統採用 Webhooks + 後端伺服器 + 資料庫的標準架構。

| 組件 | 技術/角色 | 說明 |
| :--- | :--- | :--- |
| **後端伺服器** | Python (FastAPI) | 處理所有業務邏輯、LINE Webhook 請求，並提供網頁預覽所需的 API 接口。 |
| **資料庫** | SQLite (SQLAlchemy ORM) | 儲存使用者資料、讀經計畫進度、和合本聖經經文。 |
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

## 3. 部署步驟

### 步驟 3.1：環境準備 (與先前相同)

1.  **安裝 Python 依賴項：**
    ```bash
    pip3 install fastapi uvicorn python-multipart sqlalchemy line-bot-sdk pandas
    ```

2.  **準備資料：**
    ```bash
    # 確保您已經克隆了包含 bibleText.js 的倉庫 (例如 xuan9/ChineseBibleSearchJS)
    # 如果沒有，請先執行: gh repo clone xuan9/ChineseBibleSearchJS
    python3 prepare_data.py
    ```

3.  **初始化資料庫：**
    ```bash
    python3 database.py
    ```

### 步驟 3.2：LINE Bot 設定 (與先前相同)

1.  **建立 LINE 官方帳號：** 在 [LINE Developers Console] 建立一個新的 Messaging API Channel.
2.  **取得金鑰：** 記下以下資訊：
    *   **Channel Access Token**
    *   **Channel Secret**
3.  **設定環境變數：** 在您的伺服器環境中設定以下變數：
    ```bash
    export LINE_CHANNEL_ACCESS_TOKEN="您的 Channel Access Token"
    export LINE_CHANNEL_SECRET="您的 Channel Secret"
    ```

### 步驟 3.3：選擇部署平台與啟動伺服器

由於本專案是後端應用程式，您需要選擇一個適合運行 Python 應用程式的雲平台進行部署。

**推薦的部署平台：**
*   **Google Cloud Run (推薦，有慷慨的免費額度)**：適合容器化部署，無需管理伺服器。
*   **雲伺服器 (VPS/VM)：** AWS EC2, Google Compute Engine, Azure Virtual Machines (適合有 Linux 基礎的用戶，需要手動配置 Nginx/Apache 反向代理)。
*   **PaaS 平台：** Heroku, Render (提供簡化的部署流程，但可能有免費方案限制)。

---

#### **A. Google Cloud Run 部署指南 (推薦)**

Cloud Run 部署需要 Docker 容器化。

1.  **創建 Dockerfile：** 在您的專案根目錄 (即 `bible-reading-line-bot/`) 創建一個名為 `Dockerfile` 的檔案，內容如下：
    ```dockerfile
    # 使用 Python 官方映像作為基礎
    FROM python:3.11-slim

    # 設定工作目錄
    WORKDIR /app

    # 複製依賴檔案
    COPY requirements.txt .

    # 安裝依賴
    RUN pip install --no-cache-dir -r requirements.txt

    # 複製專案檔案 (包括程式碼和資料)
    COPY . .

    # 執行資料準備和資料庫初始化
    RUN python3 prepare_data.py && python3 database.py

    # 啟動 Uvicorn 伺服器
    # Cloud Run 會將流量導向 $PORT 環境變數指定的埠
    CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
    ```

2.  **創建 requirements.txt：** 在專案根目錄創建 `requirements.txt`，列出所有 Python 依賴：
    ```text
    fastapi
    uvicorn
    python-multipart
    sqlalchemy
    line-bot-sdk
    pandas
    ```

3.  **部署至 Cloud Run：**
    *   **安裝 gcloud CLI** 並登入您的 Google Cloud 帳號。
    *   **構建並推送 Docker 映像：**
        ```bash
        gcloud builds submit --tag gcr.io/[PROJECT-ID]/bible-bot
        ```
    *   **部署到 Cloud Run：**
        ```bash
        gcloud run deploy bible-bot --image gcr.io/[PROJECT-ID]/bible-bot \
          --platform managed \
          --region [YOUR-REGION] \
          --allow-unauthenticated \
          --set-env-vars LINE_CHANNEL_ACCESS_TOKEN="您的 Token",LINE_CHANNEL_SECRET="您的 Secret"
        ```
        *   將 `[PROJECT-ID]` 替換為您的 Google Cloud 專案 ID。
        *   將 `[YOUR-REGION]` 替換為您選擇的區域 (例如 `asia-east1`)。
        *   **重要：** 記得在部署時設定 LINE 的環境變數。

4.  **獲取服務網址：** 部署完成後，Cloud Run 會提供一個公開的 HTTPS 服務網址，這就是您用於 Webhook 和網頁預覽的 `https://[您的伺服器網址]`。

---

#### **B. VPS/VM 部署指南 (傳統方式)**

1.  **安裝 Uvicorn：** 確保已安裝 `uvicorn` (在 3.1 步驟已包含)。
2.  **啟動 FastAPI 應用程式：** 建議使用 `nohup` 或 Supervisor 等工具在背景運行。

```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 &
```
**網頁預覽存取：** 伺服器啟動後，您需要將您的公開域名或 IP 地址指向這個服務。
*   **公開網址格式：** `https://[您的伺服器網址]/`
*   **Webhook 網址格式：** `https://[您的伺服器網址]/webhook`

請確保您的伺服器防火牆和反向代理（如 Nginx/Apache）已配置正確，將外部流量導向到 Uvicorn 運行的 8000 埠。

由於本專案是後端應用程式，您需要選擇一個適合運行 Python 應用程式的雲平台進行部署。

**推薦的部署平台：**
*   **雲伺服器 (VPS/VM)：** AWS EC2, Google Compute Engine, Azure Virtual Machines (適合有 Linux 基礎的用戶，需要手動配置 Nginx/Apache 反向代理)。
*   **容器化平台：** Google Cloud Run, Azure Container Apps, AWS ECS/Fargate (適合使用 Docker 容器部署)。
*   **PaaS 平台：** Heroku, Render (提供簡化的部署流程，但可能有免費方案限制)。

**啟動伺服器 (適用於 VPS/VM 部署)：**

1.  **安裝 Uvicorn：** 確保已安裝 `uvicorn` (在 3.1 步驟已包含)。
2.  **啟動 FastAPI 應用程式：** 建議使用 `nohup` 或 Supervisor 等工具在背景運行。

```bash
nohup uvicorn main:app --host 0.0.0.0 --port 8000 &
```
**網頁預覽存取：** 伺服器啟動後，您需要將您的公開域名或 IP 地址指向這個服務。
*   **公開網址格式：** `https://[您的伺服器網址]/`
*   **Webhook 網址格式：** `https://[您的伺服器網址]/webhook`

請確保您的伺服器防火牆和反向代理（如 Nginx/Apache）已配置正確，將外部流量導向到 Uvicorn 運行的 8000 埠。

### 步驟 3.4：設定 Webhook (與先前相同)

1.  **取得伺服器 URL：** 確保您的伺服器有一個公開可訪問的 URL (例如：`https://your-server.com`)。
2.  **設定 Webhook URL：** 在 LINE Developers Console 的 Channel 設定頁面中，將 **Webhook URL** 設置為：
    ```
    https://your-server.com/webhook
    ```
3.  **啟用 Webhook：** 確保 Webhook 功能已開啟。

### 步驟 3.5：設定每日推送排程 (與先前相同)

您需要設定一個外部排程服務，每日定時 (例如：每天早上 6 點) 呼叫伺服器上的 `/schedule/daily_push` API。

**範例 (使用 Linux Cron Job)：**
```cron
# 每天早上 6 點執行一次每日推送
0 6 * * * curl -X POST http://localhost:8000/schedule/daily_push
```

## 4. 使用者操作指南

### 4.1. 網頁預覽功能

使用者可以直接訪問您的伺服器 URL，在網頁上：
1.  **選擇**「按卷順序計畫」或「平衡讀經計畫」。
2.  **選擇**開始日期。
3.  點擊「**載入計畫**」按鈕，即可看到 365 天的讀經進度。
4.  點擊任一天的卡片，即可在下方查看該天的**完整經文內容**。

### 4.2. LINE Bot 互動 (與先前相同)

1.  **首次使用：** 加入 LINE 官方帳號，選擇讀經計畫。
2.  **每日讀經：** 收到每日推送的讀經範圍。
3.  **回報與測驗：** 讀完後回覆 `回報讀經` 或 `已讀完` 開始測驗。
    *   測驗結束後，系統會自動推進到下一天。

---

## 參考資料

[1] LINE Developers Console. [https://developers.line.biz/console/](https://developers.line.biz/console/)
[2] FastAPI 官方文檔. [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
[3] LINE Bot SDK for Python. [https://github.com/line/line-bot-sdk-python](https://github.com/line/line-bot-sdk-python)
[4] SQLAlchemy 官方文檔. [https://www.sqlalchemy.org/](https://www.sqlalchemy.org/)
