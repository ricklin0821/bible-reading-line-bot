import requests
import os
from datetime import date

# --- 環境變數設定 ---
# 實際部署時，請將此處替換為您的伺服器地址
SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:8000")

def trigger_daily_push():
    """
    手動觸發每日推送排程的函數。
    在實際部署中，這個 API 端點會被外部的排程服務 (如 Cron Job, Celery Beat, 或雲服務的排程器) 定時呼叫。
    """
    endpoint = f"{SERVER_URL}/schedule/daily_push"
    print(f"Attempting to trigger daily push at {endpoint}...")
    
    try:
        # 這裡假設服務運行在本地，且不需要認證
        response = requests.post(endpoint)
        response.raise_for_status() # 如果響應狀態碼不是 200，則拋出異常
        
        result = response.json()
        print(f"Daily push successful. Status: {result.get('status')}, Pushed count: {result.get('pushed_count')}")
        
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to the server at {SERVER_URL}. Please ensure the FastAPI application is running.")
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP request failed with status code {e.response.status_code}. Response: {e.response.text}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # 僅作為測試用途，實際部署時請使用外部排程
    # trigger_daily_push()
    print("Scheduler script created. In a real environment, this script or a similar mechanism would be run daily.")
    print("The necessary API endpoint is already implemented in main.py at /schedule/daily_push.")
