"""
小組通知模組 (Group Notification)

負責處理小組成員完成讀經後的通知功能
"""

from datetime import datetime
from typing import List, Dict
from database import User
from group_manager import get_group_members
from linebot.v3.messaging import MessagingApi, PushMessageRequest, TextMessage


def notify_group_members(user_id: str, group_id: str, display_name: str, messaging_api: MessagingApi) -> int:
    """
    通知小組其他成員某位成員完成了讀經
    
    Args:
        user_id: 完成讀經的使用者 LINE ID
        group_id: 小組 ID
        display_name: 使用者顯示名稱
        messaging_api: LINE Messaging API 實例
    
    Returns:
        int: 成功發送通知的數量
    """
    # 取得小組成員
    members = get_group_members(group_id)
    
    if not members:
        print(f"⚠️ 小組 {group_id} 沒有成員")
        return 0
    
    # 準備通知訊息
    notification_text = f"🎉 小組通知\n\n{display_name} 剛剛完成了今日讀經！\n\n一起為他加油鼓勵吧！💪"
    
    # 發送通知給其他成員
    success_count = 0
    
    for member in members:
        member_user_id = member.get("user_id")
        notification_enabled = member.get("notification_enabled", True)
        
        # 跳過自己
        if member_user_id == user_id:
            continue
        
        # 跳過關閉通知的成員
        if not notification_enabled:
            print(f"⏭️ 跳過 {member.get('display_name')} (通知已關閉)")
            continue
        
        try:
            # 發送 Push Message
            messaging_api.push_message(
                PushMessageRequest(
                    to=member_user_id,
                    messages=[TextMessage(text=notification_text)]
                )
            )
            success_count += 1
            print(f"✅ 已通知 {member.get('display_name')}")
        except Exception as e:
            print(f"❌ 通知 {member.get('display_name')} 失敗: {e}")
    
    # 記錄到小組訊息
    save_group_message(
        group_id=group_id,
        user_id=user_id,
        display_name=display_name,
        message_type="reading_completed",
        content=f"{display_name} 完成了今日讀經"
    )
    
    print(f"📊 小組通知統計: 成功 {success_count}/{len(members)-1}")
    return success_count


def save_group_message(group_id: str, user_id: str, display_name: str, message_type: str, content: str):
    """
    儲存小組訊息到 Firestore
    
    Args:
        group_id: 小組 ID
        user_id: 發送者 LINE ID
        display_name: 發送者顯示名稱
        message_type: 訊息類型 (text, reading_completed, prayer_request, encouragement)
        content: 訊息內容
    """
    from database import db
    
    message_data = {
        "group_id": group_id,
        "user_id": user_id,
        "display_name": display_name,
        "message_type": message_type,
        "content": content,
        "created_at": datetime.now().isoformat()
    }
    
    # 儲存到 Firestore
    db.collection("group_messages").add(message_data)
    print(f"💾 已儲存小組訊息: {message_type}")


def get_group_messages(group_id: str, limit: int = 20) -> List[Dict]:
    """
    取得小組訊息歷史
    
    Args:
        group_id: 小組 ID
        limit: 取得訊息數量限制
    
    Returns:
        List[Dict]: 訊息列表
    """
    from database import db
    
    # 查詢小組訊息
    messages_ref = db.collection("group_messages")
    query = messages_ref.where("group_id", "==", group_id).order_by("created_at", direction="DESCENDING").limit(limit)
    
    messages = []
    for doc in query.stream():
        message_data = doc.to_dict()
        messages.append(message_data)
    
    # 反轉順序 (最舊的在前)
    messages.reverse()
    
    return messages


def format_group_messages(messages: List[Dict]) -> str:
    """
    格式化小組訊息為可讀的文字
    
    Args:
        messages: 訊息列表
    
    Returns:
        str: 格式化的訊息文字
    """
    if not messages:
        return "💬 小組留言板\n\n目前還沒有任何訊息\n\n發送「小組留言」開始與組員互動！"
    
    message_text = "💬 小組留言板\n\n"
    
    for msg in messages:
        display_name = msg.get("display_name", "未知")
        content = msg.get("content", "")
        message_type = msg.get("message_type", "text")
        created_at = msg.get("created_at", "")
        
        # 格式化時間
        try:
            dt = datetime.fromisoformat(created_at)
            time_str = dt.strftime("%m/%d %H:%M")
        except:
            time_str = ""
        
        # 根據訊息類型選擇圖示
        if message_type == "reading_completed":
            icon = "✅"
        elif message_type == "prayer_request":
            icon = "🙏"
        elif message_type == "encouragement":
            icon = "💪"
        else:
            icon = "💬"
        
        message_text += f"{icon} {display_name} ({time_str})\n{content}\n\n"
    
    message_text += "---\n發送「小組留言」繼續互動"
    
    return message_text
