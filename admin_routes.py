"""
管理後台 API 路由

提供管理後台所需的所有 API 端點，包括：
- 統計資料
- 使用者列表
- 使用者詳細資料
- 資料匯出
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import secrets
import csv
import io

from database import db, USERS_COLLECTION, BIBLE_PLANS_COLLECTION

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBasic()

# 簡單的密碼保護（建議在環境變數中設定）
import os
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "bible2025")

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """驗證管理員身份"""
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# --- 統計 API ---

@router.get("/stats/overview")
def get_overview_stats(admin: str = Depends(verify_admin)):
    """取得總覽統計資料"""
    users_ref = db.collection(USERS_COLLECTION)
    users = list(users_ref.stream())
    
    total_users = len(users)
    
    # 計算活躍使用者
    today = datetime.now().date()
    active_today = 0
    active_week = 0
    active_month = 0
    
    # 計畫分布
    plan_distribution = {"Canonical": 0, "Balanced": 0, "未選擇": 0}
    
    # 進度統計
    total_progress = 0
    progress_distribution = {
        "0-25%": 0,
        "25-50%": 0,
        "50-75%": 0,
        "75-100%": 0,
        "完成": 0
    }
    
    for user_doc in users:
        user_data = user_doc.to_dict()
        
        # 計畫分布
        plan_type = user_data.get('plan_type')
        if plan_type in plan_distribution:
            plan_distribution[plan_type] += 1
        else:
            plan_distribution["未選擇"] += 1
        
        # 進度統計
        current_day = user_data.get('current_day', 1)
        total_progress += current_day
        
        progress_percent = (current_day / 365) * 100
        if current_day >= 365:
            progress_distribution["完成"] += 1
        elif progress_percent >= 75:
            progress_distribution["75-100%"] += 1
        elif progress_percent >= 50:
            progress_distribution["50-75%"] += 1
        elif progress_percent >= 25:
            progress_distribution["25-50%"] += 1
        else:
            progress_distribution["0-25%"] += 1
        
        # 活躍度統計
        last_read_date = user_data.get('last_read_date')
        if last_read_date:
            if hasattr(last_read_date, 'date'):
                last_read_date = last_read_date.date()
            elif isinstance(last_read_date, datetime):
                last_read_date = last_read_date.date()
            
            if isinstance(last_read_date, date):
                days_diff = (today - last_read_date).days
                
                if days_diff == 0:
                    active_today += 1
                    active_week += 1
                    active_month += 1
                elif days_diff <= 7:
                    active_week += 1
                    active_month += 1
                elif days_diff <= 30:
                    active_month += 1
    
    avg_progress = total_progress / total_users if total_users > 0 else 0
    
    return {
        "total_users": total_users,
        "active_today": active_today,
        "active_week": active_week,
        "active_month": active_month,
        "plan_distribution": plan_distribution,
        "avg_progress": round(avg_progress, 1),
        "progress_distribution": progress_distribution
    }

# --- 使用者 API ---

@router.get("/users")
def get_all_users(
    search: str = None,
    sort_by: str = "current_day",
    order: str = "desc",
    admin: str = Depends(verify_admin)
):
    """取得所有使用者列表"""
    users_ref = db.collection(USERS_COLLECTION)
    users = list(users_ref.stream())
    
    users_list = []
    for user_doc in users:
        user_data = user_doc.to_dict()
        
        # 轉換日期
        last_read_date = user_data.get('last_read_date')
        if last_read_date and hasattr(last_read_date, 'date'):
            last_read_date = last_read_date.date().isoformat()
        elif isinstance(last_read_date, date):
            last_read_date = last_read_date.isoformat()
        else:
            last_read_date = None
        
        start_date = user_data.get('start_date')
        if start_date and hasattr(start_date, 'date'):
            start_date = start_date.date().isoformat()
        elif isinstance(start_date, date):
            start_date = start_date.isoformat()
        else:
            start_date = None
        
        user_info = {
            "id": user_doc.id,
            "line_user_id": user_data.get('line_user_id', 'Unknown'),
            "plan_type": user_data.get('plan_type', '未選擇'),
            "current_day": user_data.get('current_day', 1),
            "start_date": start_date,
            "last_read_date": last_read_date,
            "progress_percent": round((user_data.get('current_day', 1) / 365) * 100, 1)
        }
        
        # 搜尋過濾
        if search:
            if search.lower() not in user_info['line_user_id'].lower():
                continue
        
        users_list.append(user_info)
    
    # 排序
    reverse = (order == "desc")
    if sort_by in ["current_day", "progress_percent"]:
        users_list.sort(key=lambda x: x[sort_by], reverse=reverse)
    elif sort_by == "last_read_date":
        users_list.sort(key=lambda x: x[sort_by] or "", reverse=reverse)
    
    return {
        "total": len(users_list),
        "users": users_list
    }

@router.get("/users/{user_id}")
def get_user_detail(user_id: str, admin: str = Depends(verify_admin)):
    """取得使用者詳細資料"""
    users_ref = db.collection(USERS_COLLECTION)
    user_doc = users_ref.document(user_id).get()
    
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = user_doc.to_dict()
    
    # 轉換日期
    last_read_date = user_data.get('last_read_date')
    if last_read_date and hasattr(last_read_date, 'date'):
        last_read_date = last_read_date.date().isoformat()
    elif isinstance(last_read_date, date):
        last_read_date = last_read_date.isoformat()
    
    start_date = user_data.get('start_date')
    if start_date and hasattr(start_date, 'date'):
        start_date = start_date.date().isoformat()
    elif isinstance(start_date, date):
        start_date = start_date.isoformat()
    
    # 取得當前讀經計畫
    current_day = user_data.get('current_day', 1)
    plan_type = user_data.get('plan_type')
    current_reading = None
    
    if plan_type:
        plans_ref = db.collection(BIBLE_PLANS_COLLECTION)
        query = plans_ref.where('plan_type', '==', plan_type).where('day_number', '==', current_day).limit(1)
        docs = list(query.stream())
        if docs:
            plan_data = docs[0].to_dict()
            current_reading = plan_data.get('readings')
    
    return {
        "id": user_doc.id,
        "line_user_id": user_data.get('line_user_id'),
        "plan_type": plan_type,
        "current_day": current_day,
        "start_date": start_date,
        "last_read_date": last_read_date,
        "quiz_state": user_data.get('quiz_state', 'IDLE'),
        "progress_percent": round((current_day / 365) * 100, 1),
        "current_reading": current_reading
    }

# --- 匯出 API ---

@router.get("/export/users")
def export_users_csv(admin: str = Depends(verify_admin)):
    """匯出所有使用者資料為 CSV"""
    users_ref = db.collection(USERS_COLLECTION)
    users = list(users_ref.stream())
    
    # 建立 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 寫入標題
    writer.writerow([
        'LINE User ID',
        '讀經計畫',
        '當前天數',
        '進度百分比',
        '開始日期',
        '最後閱讀日期',
        '測驗狀態'
    ])
    
    # 寫入資料
    for user_doc in users:
        user_data = user_doc.to_dict()
        
        # 轉換日期
        last_read_date = user_data.get('last_read_date')
        if last_read_date and hasattr(last_read_date, 'date'):
            last_read_date = last_read_date.date().isoformat()
        elif isinstance(last_read_date, date):
            last_read_date = last_read_date.isoformat()
        else:
            last_read_date = ''
        
        start_date = user_data.get('start_date')
        if start_date and hasattr(start_date, 'date'):
            start_date = start_date.date().isoformat()
        elif isinstance(start_date, date):
            start_date = start_date.isoformat()
        else:
            start_date = ''
        
        current_day = user_data.get('current_day', 1)
        progress_percent = round((current_day / 365) * 100, 1)
        
        writer.writerow([
            user_data.get('line_user_id', ''),
            user_data.get('plan_type', '未選擇'),
            current_day,
            f"{progress_percent}%",
            start_date,
            last_read_date,
            user_data.get('quiz_state', 'IDLE')
        ])
    
    # 準備回應
    output.seek(0)
    return Response(
        content=output.getvalue().encode('utf-8-sig'),  # 使用 UTF-8 BOM 以支援 Excel
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=bible_bot_users_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

@router.get("/export/stats")
def export_stats_csv(admin: str = Depends(verify_admin)):
    """匯出統計資料為 CSV"""
    stats = get_overview_stats(admin)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 總覽統計
    writer.writerow(['統計項目', '數值'])
    writer.writerow(['總使用者數', stats['total_users']])
    writer.writerow(['今日活躍', stats['active_today']])
    writer.writerow(['本週活躍', stats['active_week']])
    writer.writerow(['本月活躍', stats['active_month']])
    writer.writerow(['平均進度（天）', stats['avg_progress']])
    writer.writerow([])
    
    # 計畫分布
    writer.writerow(['讀經計畫', '使用者數'])
    for plan, count in stats['plan_distribution'].items():
        writer.writerow([plan, count])
    writer.writerow([])
    
    # 進度分布
    writer.writerow(['進度區間', '使用者數'])
    for range_name, count in stats['progress_distribution'].items():
        writer.writerow([range_name, count])
    
    output.seek(0)
    return Response(
        content=output.getvalue().encode('utf-8-sig'),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=bible_bot_stats_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )

