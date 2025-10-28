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

# 注意：Firestore 資料庫初始化會在應用啟動時自動執行（main.py 中的 init_db()）
# 不需要在 Docker 建置時執行，因為 Firestore 需要在運行時才能連接

# 啟動 Uvicorn 伺服器
# Cloud Run 會將流量導向 $PORT 環境變數指定的埠
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}

