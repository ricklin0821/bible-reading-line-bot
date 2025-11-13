"""
管理後台 API 路由

提供管理後台所需的所有 API 端點，包括：
- 統計資料
- 使用者列表
- 使用者詳細資料
- 資料匯出
- 小組管理
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from datetime import datetime, timedelta, date, timezone
from typing import List, Dict, Any
import secrets
import csv
import io
import os
from google.cloud import firestore

from database import db, USERS_COLLECTION, BIBLE_PLANS_COLLECTION, User
import group_manager

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBasic()

# 管理員帳號密碼
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise ValueError("ADMIN_USERNAME and ADMIN_PASSWORD must be set in environment variables.")

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
    
    today = datetime.now(timezone.utc).date()
    active_today = 0
    active_week = 0
    active_month = 0
    
    plan_distribution = {"Canonical": 0, "Balanced": 0, "未選擇": 0}
    
    total_progress = 0
    progress_distribution = { "0-25%": 0, "25-50%": 0, "50-75%": 0, "75-100%": 0, "完成": 0 }
    
    for user_doc in users:
        user_data = user_doc.to_dict()
        
        plan_type = user_data.get('plan_type')
        if plan_type in plan_distribution:
            plan_distribution[plan_type] += 1
        else:
            plan_distribution["未選擇"] += 1
        
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
        
        last_read_date_obj = user_data.get('last_read_date')
        if last_read_date_obj:
            if isinstance(last_read_date_obj, datetime):
                last_read_date_val = last_read_date_obj.date()
            elif isinstance(last_read_date_obj, date):
                last_read_date_val = last_read_date_obj
            else:
                continue

            days_diff = (today - last_read_date_val).days
            if days_diff == 0:
                active_today += 1
            if days_diff <= 7:
                active_week += 1
            if days_diff <= 30:
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
def get_all_users(search: str = None, sort_by: str = "current_day", order: str = "desc", admin: str = Depends(verify_admin)):
    """取得所有使用者列表"""
    users_ref = db.collection(USERS_COLLECTION)
    users = list(users_ref.stream())
    
    users_list = []
    for user_doc in users:
        user_data = user_doc.to_dict()
        
        last_read_date = user_data.get('last_read_date')
        if isinstance(last_read_date, datetime):
            last_read_date = last_read_date.isoformat()
        
        start_date = user_data.get('start_date')
        if isinstance(start_date, datetime):
            start_date = start_date.isoformat()

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
        
        if search and search.lower() not in user_info['display_name'].lower() and search.lower() not in user_info['line_user_id'].lower():
            continue
        
        users_list.append(user_info)
    
    reverse = (order == "desc")
    users_list.sort(key=lambda x: str(x.get(sort_by, '')), reverse=reverse)
    
    return {
        "total": len(users_list),
        "users": users_list
    }

@router.get("/users/{user_id}")
def get_user_detail(user_id: str, admin: str = Depends(verify_admin)):
    """取得使用者詳細資料"""
    user_doc = db.collection(USERS_COLLECTION).document(user_id).get()
    
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = user_doc.to_dict()
    
    # ... (Date conversion logic as before) ...
    
    return {
        "id": user_doc.id,
        **user_data
    }

# --- 匯出 API ---
@router.get("/export/users")
def export_users_csv(admin: str = Depends(verify_admin)):
    """匯出所有使用者資料為 CSV"""
    users = list(db.collection(USERS_COLLECTION).stream())
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['LINE User ID', '使用者名稱', '讀經計畫', '當前天數', '進度百分比', '開始日期', '最後閱讀日期'])
    
    for user_doc in users:
        user_data = user_doc.to_dict()
        writer.writerow([
            user_data.get('line_user_id', ''),
            user_data.get('display_name', '未設定'),
            user_data.get('plan_type', '未選擇'),
            user_data.get('current_day', 1),
            f"{round((user_data.get('current_day', 1) / 365) * 100, 1)}%",
            user_data.get('start_date', ''),
            user_data.get('last_read_date', '')
        ])
    
    output.seek(0)
    return Response(content=output.getvalue().encode('utf-8-sig'), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=users.csv"})

# --- 使用者管理 API ---
@router.post("/users/{line_user_id}/reset-quiz")
def reset_user_quiz(line_user_id: str, admin: str = Depends(verify_admin)):
    """重置使用者的測驗狀態"""
    user = User.get_by_line_id(line_user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.quiz_state = "IDLE"
    user.quiz_data = "{}"
    user.save()
    return {"success": True, "message": "User quiz state has been reset."}

# --- 小組管理 API (Corrected Version) ---

@router.get("/stats/groups")
def get_group_stats(admin: str = Depends(verify_admin)):
    """取得小組統計資料"""
    groups_ref = db.collection("groups")
    groups_stream = groups_ref.stream()
    
    total_groups = 0
    total_members = 0
    
    all_groups = list(groups_stream)
    total_groups = len(all_groups)
    
    for group_doc in all_groups:
        group_data = group_doc.to_dict()
        total_members += group_data.get('member_count', 0)
        
    avg_members_per_group = round(total_members / total_groups, 1) if total_groups > 0 else 0
    
    # Count all messages in the 'group_messages' collection group
    messages_query = db.collection_group('group_messages').stream()
    messages_count = len(list(messages_query))

    return {
        "total_groups": total_groups,
        "total_members": total_members,
        "avg_members_per_group": avg_members_per_group,
        "total_messages": messages_count,
    }


@router.get("/groups")
def get_all_groups(admin: str = Depends(verify_admin)):
    """取得所有小組列表"""
    groups_ref = db.collection("groups")
    groups = list(groups_ref.stream())
    
    groups_list = []
    for group_doc in groups:
        group_data = group_doc.to_dict()
        
        if 'group_name' not in group_data:
            new_group_name = group_manager.generate_group_name()
            group_data['group_name'] = new_group_name
            db.collection("groups").document(group_doc.id).update({"group_name": new_group_name})
        
        created_at = group_data.get('created_at', '')
        if isinstance(created_at, datetime):
            created_at = created_at.isoformat()
        
        group_info = {
            "group_id": group_data.get('group_id'),
            "group_name": group_data.get('group_name', group_data.get('group_id')),
            "member_count": group_data.get('member_count', 0),
            "max_members": group_data.get('max_members', 6),
            "is_full": group_data.get('is_full', False),
            "created_at": created_at,
            "members": group_data.get('members', [])
        }
        groups_list.append(group_info)
        
    groups_list.sort(key=lambda x: x.get('member_count', 0), reverse=True)
    
    return {"groups": groups_list}

@router.get("/groups/{group_id}")
def get_group_detail(group_id: str, admin: str = Depends(verify_admin)):
    """取得小組詳細資料"""
    # Correctly query for the group document using a 'where' clause
    group_query = db.collection("groups").where("group_id", "==", group_id).limit(1)
    group_stream = list(group_query.stream())
    
    if not group_stream:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group_doc = group_stream[0]
    group_data = group_doc.to_dict()

    # Auto-generate group name if missing
    if 'group_name' not in group_data:
        new_group_name = group_manager.generate_group_name()
        group_data['group_name'] = new_group_name
        # Use the correct document reference to update
        db.collection("groups").document(group_doc.id).update({"group_name": new_group_name})

    # --- Hydrate Member Data ---
    hydrated_members = []
    member_list = group_data.get('members', [])
    member_ids = [member.get('user_id') for member in member_list if member.get('user_id')]

    if member_ids:
        # Create a map of original member data
        member_data_map = {m.get('user_id'): m for m in member_list}

        # Fetch user profiles from 'users' collection
        user_profiles = {}
        id_chunks = [member_ids[i:i + 30] for i in range(0, len(member_ids), 30)]
        for chunk in id_chunks:
            users_query = db.collection(USERS_COLLECTION).where("line_user_id", "in", chunk).stream()
            for user in users_query:
                user_data = user.to_dict()
                user_profiles[user_data.get("line_user_id")] = user_data.get("display_name", "未知用戶")
        
        # Combine data
        for user_id, original_member_data in member_data_map.items():
            joined_at = original_member_data.get('joined_at', datetime.min)
            if isinstance(joined_at, datetime):
                joined_at = joined_at.isoformat()

            hydrated_members.append({
                "user_id": user_id,
                "display_name": user_profiles.get(user_id, "未知用戶"),
                "notification_enabled": original_member_data.get('notification_enabled', False),
                "joined_at": joined_at
            })
    group_data['members'] = hydrated_members
    # --- End of Hydration ---

    created_at = group_data.get('created_at', '')
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    
    # Fetch recent messages
    messages_ref = db.collection('group_messages').where('group_id', '==', group_id).order_by('created_at', direction=firestore.Query.DESCENDING).limit(20)
    messages_stream = messages_ref.stream()
    
    final_messages = []
    for msg in messages_stream:
        msg_data = msg.to_dict()
        final_messages.append({
            "display_name": msg_data.get('display_name', '未知'),
            "content": msg_data.get('content', ''),
            "message_type": msg_data.get('message_type', 'text'),
            "created_at": msg_data.get("created_at")
        })

    group_data['created_at'] = created_at
    group_data['messages'] = final_messages
    return group_data

@router.get("/all-group-messages")
def get_all_group_messages(admin: str = Depends(verify_admin)):
    """取得所有小組的所有留言"""
    try:
        # Removed .order_by() to avoid index dependency, will sort in Python
        messages_ref = db.collection_group('group_messages').limit(500)
        messages_stream = list(messages_ref.stream())

        group_ids = set()
        raw_messages_with_group_id = [] # Store messages temporarily to get all group_ids first
        for msg in messages_stream:
            msg_data = msg.to_dict()
            group_id = msg_data.get('group_id')
            if group_id: # Only process messages with a valid group_id
                group_ids.add(group_id)
                raw_messages_with_group_id.append(msg_data) # Store original message data

        group_name_cache = {}
        # Fetch group names in chunks
        group_id_chunks = [list(group_ids)[i:i + 30] for i in range(0, len(group_ids), 30)]

        for chunk in group_id_chunks:
            if not chunk:
                continue
            group_docs = db.collection("groups").where("group_id", "in", chunk).stream()
            for group_doc in group_docs:
                group_data = group_doc.to_dict()
                group_id = group_data.get("group_id")
                if 'group_name' not in group_data:
                    new_group_name = group_manager.generate_group_name()
                    group_data['group_name'] = new_group_name
                    db.collection("groups").document(group_doc.id).update({"group_name": new_group_name})
                group_name_cache[group_id] = group_data.get("group_name", group_id)

        # Sort messages in Python after fetching
        # Ensure 'created_at' is a comparable type (e.g., string or datetime)
        def get_sort_key(msg_data):
            created_at = msg_data.get('created_at')
            if isinstance(created_at, datetime):
                return created_at.isoformat()
            return str(created_at or '') # Ensure it's a string for comparison

        raw_messages_with_group_id.sort(key=get_sort_key, reverse=True)

        all_messages = []
        for msg_data in raw_messages_with_group_id:
            group_id = msg_data.get('group_id')
            
            all_messages.append({
                "group_id": group_id,
                "group_name": group_name_cache.get(group_id, "未知小組"),
                "display_name": msg_data.get('display_name', '未知'),
                "content": msg_data.get('content', ''),
                "message_type": msg_data.get('message_type', 'text'),
                "timestamp": msg_data.get("created_at") # Map 'created_at' to 'timestamp' for the frontend
            })
            
        return all_messages

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
