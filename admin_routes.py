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

# 管理員帳號密碼必須從環境變數設定，不提供預設值以確保安全
import os
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise ValueError("⚠️ SECURITY: ADMIN_USERNAME and ADMIN_PASSWORD must be set in environment variables. Do not use default values!")

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
            "display_name": user_data.get('display_name', '未設定'),
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
        "display_name": user_data.get('display_name', '未設定'),
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
        '使用者名稱',
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
            user_data.get('display_name', '未設定'),
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



# --- 使用者管理 API ---

@router.post("/users/{line_user_id}/reset-quiz")
def reset_user_quiz(line_user_id: str, admin: str = Depends(verify_admin)):
    """重置使用者的測驗狀態"""
    from database import User
    
    user = User.get_by_line_user_id(line_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.quiz_state = "IDLE"
    user.quiz_data = "{}"
    user.save()
    
    return {
        "success": True,
        "message": f"已重置使用者 {line_user_id} 的測驗狀態",
        "user": {
            "line_user_id": user.line_user_id,
            "quiz_state": user.quiz_state,
            "current_day": user.current_day
        }
    }

@router.post("/users/{line_user_id}/reset-progress")
def reset_user_progress(line_user_id: str, admin: str = Depends(verify_admin)):
    """重置使用者的讀經進度"""
    from database import User
    
    user = User.get_by_line_user_id(line_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.current_day = 1
    user.last_read_date = None
    user.quiz_state = "IDLE"
    user.quiz_data = "{}"
    user.save()
    
    return {
        "success": True,
        "message": f"已重置使用者 {line_user_id} 的讀經進度",
        "user": {
            "line_user_id": user.line_user_id,
            "current_day": user.current_day,
            "quiz_state": user.quiz_state
        }
    }


# --- 小組管理 API ---

@router.get("/groups")
def get_all_groups(admin: str = Depends(verify_admin)):
    """取得所有小組列表"""
    groups_ref = db.collection("groups")
    groups = list(groups_ref.stream())
    
    groups_list = []
    for group_doc in groups:
        group_data = group_doc.to_dict()
        
        # 轉換創建時間
        created_at = group_data.get('created_at', '')
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        
        group_info = {
            "group_id": group_data.get('group_id'),
            "member_count": group_data.get('member_count', 0),
            "max_members": group_data.get('max_members', 6),
            "is_full": group_data.get('is_full', False),
            "created_at": created_at,
            "members": group_data.get('members', [])
        }
        
        groups_list.append(group_info)
    
    # 按成員數量排序
    groups_list.sort(key=lambda x: x['member_count'], reverse=True)
    
    return {
        "total": len(groups_list),
        "groups": groups_list
    }

@router.get("/groups/{group_id}")
def get_group_detail(group_id: str, admin: str = Depends(verify_admin)):
    """取得小組詳細資料"""
    groups_ref = db.collection("groups")
    group_doc = groups_ref.document(group_id).get()
    
    if not group_doc.exists:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group_data = group_doc.to_dict()
    
    # 轉換創建時間
    created_at = group_data.get('created_at', '')
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    
    # 取得小組留言（先查詢所有，再在程式中排序以避免需要索引）
    messages_ref = db.collection("group_messages")
    query = messages_ref.where("group_id", "==", group_id)
    
    messages = []
    for msg_doc in query.stream():
        msg_data = msg_doc.to_dict()
        created_at_msg = msg_data.get('created_at', '')
        
        messages.append({
            "display_name": msg_data.get('display_name', '未知'),
            "content": msg_data.get('content', ''),
            "message_type": msg_data.get('message_type', 'text'),
            "created_at": created_at_msg,
            "created_at_iso": created_at_msg.isoformat() if isinstance(created_at_msg, datetime) else created_at_msg
        })
    
    # 在程式中排序並限制數量
    messages.sort(key=lambda x: x['created_at'] if isinstance(x['created_at'], datetime) else datetime.min, reverse=True)
    messages = messages[:20]
    
    # 轉換時間格式
    for msg in messages:
        if isinstance(msg['created_at'], datetime):
            msg['created_at'] = msg['created_at'].isoformat()
        else:
            msg['created_at'] = msg.get('created_at_iso', '')
        msg.pop('created_at_iso', None)
    
    return {
        "group_id": group_data.get('group_id'),
        "member_count": group_data.get('member_count', 0),
        "max_members": group_data.get('max_members', 6),
        "is_full": group_data.get('is_full', False),
        "created_at": created_at,
        "members": group_data.get('members', []),
        "messages": messages
    }

@router.get("/groups/stats/overview")
def get_groups_stats(admin: str = Depends(verify_admin)):
    """取得小組統計資料"""
    groups_ref = db.collection("groups")
    groups = list(groups_ref.stream())
    
    total_groups = len(groups)
    total_members = 0
    full_groups = 0
    
    member_distribution = {
        "1": 0,
        "2": 0,
        "3": 0,
        "4": 0,
        "5": 0,
        "6": 0
    }
    
    for group_doc in groups:
        group_data = group_doc.to_dict()
        member_count = group_data.get('member_count', 0)
        total_members += member_count
        
        if group_data.get('is_full', False):
            full_groups += 1
        
        if str(member_count) in member_distribution:
            member_distribution[str(member_count)] += 1
    
    avg_members = total_members / total_groups if total_groups > 0 else 0
    
    # 取得小組留言總數
    messages_ref = db.collection("group_messages")
    total_messages = len(list(messages_ref.stream()))
    
    return {
        "total_groups": total_groups,
        "total_members": total_members,
        "full_groups": full_groups,
        "avg_members_per_group": round(avg_members, 1),
        "member_distribution": member_distribution,
        "total_messages": total_messages
    }

@router.get("/export/groups")
def export_groups_csv(admin: str = Depends(verify_admin)):
    """匯出所有小組資料為 CSV"""
    groups_ref = db.collection("groups")
    groups = list(groups_ref.stream())
    
    # 建立 CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 寫入標題
    writer.writerow([
        '小組 ID',
        '成員數量',
        '最大成員數',
        '是否已滿',
        '創建時間',
        '成員列表'
    ])
    
    # 寫入資料
    for group_doc in groups:
        group_data = group_doc.to_dict()
        
        # 轉換創建時間
        created_at = group_data.get('created_at', '')
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        
        # 成員列表
        members = group_data.get('members', [])
        member_names = ', '.join([m.get('display_name', '未知') for m in members])
        
        writer.writerow([
            group_data.get('group_id', ''),
            group_data.get('member_count', 0),
            group_data.get('max_members', 6),
            '是' if group_data.get('is_full', False) else '否',
            created_at,
            member_names
        ])
    
    # 準備回應
    output.seek(0)
    return Response(
        content=output.getvalue().encode('utf-8-sig'),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=bible_bot_groups_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )
