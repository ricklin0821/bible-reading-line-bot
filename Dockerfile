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

# 執行資料庫初始化
# 注意：prepare_data.py 已在本地執行，CSV 檔案已包含在專案中，無需在 Docker 構建時重新生成。
# 注意：SQLite 資料庫檔案 (bible_plan.db) 會在容器構建時生成，
# 但在 Cloud Run 中，如果容器重新啟動，這個檔案會丟失。
# 對於正式環境，建議使用外部資料庫 (如 Cloud SQL)。
# 對於測試和低頻率使用，可以接受。
RUN python3 database.py

# 啟動 Uvicorn 伺服器
# Cloud Run 會將流量導向 $PORT 環境變數指定的埠
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}

