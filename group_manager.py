"""
小組管理模組 (Group Manager)

負責處理小組的創建、加入、離開、隨機分配等功能
"""

from datetime import datetime
from typing import Dict, List, Optional
from database import db
import random
import string

# 小組設定
MAX_GROUP_MEMBERS = 6  # 每組最多 6 人


def generate_group_id() -> str:
    """生成唯一的小組 ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"group_{timestamp}_{random_suffix}"


def create_group() -> str:
    """
    創建新小組
    
    Returns:
        str: 新創建的小組 ID
    """
    group_id = generate_group_id()
    
    group_data = {
        "group_id": group_id,
        "created_at": datetime.now().isoformat(),
        "member_count": 0,
        "max_members": MAX_GROUP_MEMBERS,
        "is_full": False,
        "members": []
    }
    
    # 儲存到 Firestore
    db.collection("groups").document(group_id).set(group_data)
    
    print(f"✅ 創建新小組: {group_id}")
    return group_id


def find_available_group() -> Optional[str]:
    """
    尋找未滿的小組
    
    Returns:
        Optional[str]: 可加入的小組 ID，如果沒有則返回 None
    """
    # 查詢未滿的小組
    groups_ref = db.collection("groups")
    query = groups_ref.where("is_full", "==", False).limit(10)
    
    available_groups = []
    for doc in query.stream():
        group_data = doc.to_dict()
        if group_data["member_count"] < MAX_GROUP_MEMBERS:
            available_groups.append(group_data["group_id"])
    
    if available_groups:
        # 隨機選擇一個小組
        return random.choice(available_groups)
    
    return None


def add_member_to_group(group_id: str, user_id: str, display_name: str) -> bool:
    """
    將使用者加入小組
    
    Args:
        group_id: 小組 ID
        user_id: 使用者 LINE ID
        display_name: 使用者顯示名稱
    
    Returns:
        bool: 是否成功加入
    """
    group_ref = db.collection("groups").document(group_id)
    group_doc = group_ref.get()
    
    if not group_doc.exists:
        print(f"❌ 小組不存在: {group_id}")
        return False
    
    group_data = group_doc.to_dict()
    
    # 檢查是否已滿
    if group_data["member_count"] >= MAX_GROUP_MEMBERS:
        print(f"❌ 小組已滿: {group_id}")
        return False
    
    # 檢查是否已在小組中
    for member in group_data["members"]:
        if member["user_id"] == user_id:
            print(f"⚠️ 使用者已在小組中: {user_id}")
            return False
    
    # 新增成員
    new_member = {
        "user_id": user_id,
        "display_name": display_name,
        "joined_at": datetime.now().isoformat(),
        "notification_enabled": True
    }
    
    group_data["members"].append(new_member)
    group_data["member_count"] = len(group_data["members"])
    group_data["is_full"] = group_data["member_count"] >= MAX_GROUP_MEMBERS
    
    # 更新 Firestore
    group_ref.set(group_data)
    
    # 更新使用者資料
    from database import User
    User.update(user_id, {
        "group_id": group_id,
        "group_notification_enabled": True,
        "joined_group_at": datetime.now().isoformat()
    })
    
    print(f"✅ 使用者 {display_name} 加入小組 {group_id}")
    return True


def remove_member_from_group(user_id: str) -> bool:
    """
    將使用者從小組中移除
    
    Args:
        user_id: 使用者 LINE ID
    
    Returns:
        bool: 是否成功移除
    """
    from database import User
    user_obj = User.get_by_line_id(user_id)
    user = user_obj.to_dict() if user_obj else None
    
    if not user or not user.get("group_id"):
        print(f"⚠️ 使用者不在任何小組中: {user_id}")
        return False
    
    group_id = user["group_id"]
    group_ref = db.collection("groups").document(group_id)
    group_doc = group_ref.get()
    
    if not group_doc.exists:
        print(f"❌ 小組不存在: {group_id}")
        return False
    
    group_data = group_doc.to_dict()
    
    # 移除成員
    group_data["members"] = [m for m in group_data["members"] if m["user_id"] != user_id]
    group_data["member_count"] = len(group_data["members"])
    group_data["is_full"] = False
    
    # 如果小組沒有成員了，刪除小組
    if group_data["member_count"] == 0:
        group_ref.delete()
        print(f"🗑️ 刪除空小組: {group_id}")
    else:
        group_ref.set(group_data)
    
    # 更新使用者資料
    User.update(user_id, {
        "group_id": None,
        "group_notification_enabled": False,
        "joined_group_at": None
    })
    
    print(f"✅ 使用者 {user_id} 離開小組 {group_id}")
    return True


def join_random_group(user_id: str, display_name: str) -> Dict:
    """
    加入隨機小組（如果沒有可用小組則創建新的）
    
    Args:
        user_id: 使用者 LINE ID
        display_name: 使用者顯示名稱
    
    Returns:
        Dict: 包含 group_id 和 is_new_group 的字典
    """
    # 先檢查使用者是否已在小組中
    from database import User
    user_obj = User.get_by_line_id(user_id)
    user = user_obj.to_dict() if user_obj else None
    
    if user and user.get("group_id"):
        print(f"⚠️ 使用者已在小組中: {user.get('group_id')}")
        return {
            "success": False,
            "message": "您已經在小組中了！",
            "group_id": user.get("group_id")
        }
    
    # 尋找可用小組
    group_id = find_available_group()
    is_new_group = False
    
    if not group_id:
        # 沒有可用小組，創建新的
        group_id = create_group()
        is_new_group = True
    
    # 加入小組
    success = add_member_to_group(group_id, user_id, display_name)
    
    if success:
        return {
            "success": True,
            "group_id": group_id,
            "is_new_group": is_new_group
        }
    else:
        return {
            "success": False,
            "message": "加入小組失敗，請稍後再試"
        }


def switch_group(user_id: str, display_name: str) -> Dict:
    """
    換組（離開目前小組並加入新的隨機小組）
    
    Args:
        user_id: 使用者 LINE ID
        display_name: 使用者顯示名稱
    
    Returns:
        Dict: 包含新 group_id 的字典
    """
    # 先離開目前小組
    remove_member_from_group(user_id)
    
    # 加入新的隨機小組
    return join_random_group(user_id, display_name)


def get_group_info(group_id: str) -> Optional[Dict]:
    """
    取得小組資訊
    
    Args:
        group_id: 小組 ID
    
    Returns:
        Optional[Dict]: 小組資料，如果不存在則返回 None
    """
    group_ref = db.collection("groups").document(group_id)
    group_doc = group_ref.get()
    
    if not group_doc.exists:
        return None
    
    return group_doc.to_dict()


def get_group_members(group_id: str) -> List[Dict]:
    """
    取得小組成員列表
    
    Args:
        group_id: 小組 ID
    
    Returns:
        List[Dict]: 成員列表
    """
    group_info = get_group_info(group_id)
    
    if not group_info:
        return []
    
    return group_info.get("members", [])


def toggle_notification(user_id: str, enabled: bool) -> bool:
    """
    切換小組通知開關
    
    Args:
        user_id: 使用者 LINE ID
        enabled: 是否啟用通知
    
    Returns:
        bool: 是否成功切換
    """
    from database import User
    user_obj = User.get_by_line_id(user_id)
    user = user_obj.to_dict() if user_obj else None
    
    if not user or not user.get("group_id"):
        print(f"⚠️ 使用者不在任何小組中: {user_id}")
        return False
    
    group_id = user["group_id"]
    
    # 更新使用者的通知設定
    User.update(user_id, {
        "group_notification_enabled": enabled
    })
    
    # 更新小組中的成員資料
    group_ref = db.collection("groups").document(group_id)
    group_doc = group_ref.get()
    
    if group_doc.exists:
        group_data = group_doc.to_dict()
        
        for member in group_data["members"]:
            if member["user_id"] == user_id:
                member["notification_enabled"] = enabled
                break
        
        group_ref.set(group_data)
    
    print(f"✅ 使用者 {user_id} 通知設定: {enabled}")
    return True


def format_group_info_message(group_id: str) -> str:
    """
    格式化小組資訊訊息
    
    Args:
        group_id: 小組 ID
    
    Returns:
        str: 格式化的訊息文字
    """
    group_info = get_group_info(group_id)
    
    if not group_info:
        return "❌ 找不到小組資訊"
    
    members = group_info.get("members", [])
    member_count = len(members)
    max_members = group_info.get("max_members", MAX_GROUP_MEMBERS)
    
    message = f"👥 小組資訊\n\n"
    message += f"📊 人數：{member_count}/{max_members}\n\n"
    message += f"👤 成員列表：\n"
    
    for i, member in enumerate(members, 1):
        name = member.get("display_name", "未知")
        notification = "🔔" if member.get("notification_enabled", True) else "🔕"
        message += f"{i}. {name} {notification}\n"
    
    message += f"\n💡 提示：\n"
    message += f"• 發送「小組留言」進入留言模式\n"
    message += f"• 發送「換組」可以隨機換到新小組\n"
    message += f"• 發送「小組通知關閉」可關閉通知"
    
    return message
