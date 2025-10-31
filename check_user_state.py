#!/usr/bin/env python3
"""
使用者狀態檢查和重置工具
用於診斷和修復卡住的使用者狀態
"""

from database import User
import json
from datetime import date

def check_user_state(line_user_id: str):
    """檢查使用者的當前狀態"""
    user = User.get_by_line_user_id(line_user_id)
    
    if not user:
        print(f"❌ 找不到使用者：{line_user_id}")
        return None
    
    print(f"\n{'='*60}")
    print(f"使用者狀態檢查")
    print(f"{'='*60}")
    print(f"LINE User ID: {user.line_user_id}")
    print(f"顯示名稱: {user.display_name or '(未設定)'}")
    print(f"讀經計畫類型: {user.plan_type}")
    print(f"當前天數: {user.current_day}")
    print(f"最後讀經日期: {user.last_read_date}")
    print(f"測驗狀態: {user.quiz_state}")
    print(f"聯繫狀態: {user.contact_state}")
    
    # 解析 quiz_data
    try:
        quiz_data = json.loads(user.quiz_data)
        if quiz_data:
            print(f"\n測驗資料:")
            print(f"  當前題目索引: {quiz_data.get('current_question_index', 'N/A')}")
            print(f"  總題數: {len(quiz_data.get('questions', []))}")
            if 'questions' in quiz_data and quiz_data['questions']:
                current_idx = quiz_data.get('current_question_index', 0)
                if current_idx < len(quiz_data['questions']):
                    current_q = quiz_data['questions'][current_idx]
                    print(f"  當前題目: {current_q.get('ref', 'N/A')}")
                    print(f"  答題次數: {current_q.get('attempts', 0)}")
    except:
        print(f"測驗資料: (無效的 JSON)")
    
    print(f"{'='*60}\n")
    
    return user

def reset_user_quiz_state(line_user_id: str):
    """重置使用者的測驗狀態"""
    user = User.get_by_line_user_id(line_user_id)
    
    if not user:
        print(f"❌ 找不到使用者：{line_user_id}")
        return False
    
    print(f"正在重置使用者 {line_user_id} 的測驗狀態...")
    
    user.quiz_state = "IDLE"
    user.quiz_data = "{}"
    user.save()
    
    print(f"✅ 測驗狀態已重置")
    return True

def reset_user_reading_progress(line_user_id: str):
    """重置使用者的讀經進度（回到第一天）"""
    user = User.get_by_line_user_id(line_user_id)
    
    if not user:
        print(f"❌ 找不到使用者：{line_user_id}")
        return False
    
    print(f"正在重置使用者 {line_user_id} 的讀經進度...")
    
    user.current_day = 1
    user.last_read_date = None
    user.quiz_state = "IDLE"
    user.quiz_data = "{}"
    user.save()
    
    print(f"✅ 讀經進度已重置到第 1 天")
    return True

def list_all_users():
    """列出所有使用者"""
    users = User.get_all()
    
    print(f"\n{'='*60}")
    print(f"所有使用者列表 (共 {len(users)} 位)")
    print(f"{'='*60}")
    
    for user in users:
        print(f"LINE ID: {user.line_user_id}")
        print(f"  名稱: {user.display_name or '(未設定)'}")
        print(f"  計畫: {user.plan_type} - 第 {user.current_day} 天")
        print(f"  測驗狀態: {user.quiz_state}")
        print(f"  最後讀經: {user.last_read_date}")
        print()
    
    print(f"{'='*60}\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方式:")
        print("  檢查使用者狀態: python3 check_user_state.py check <LINE_USER_ID>")
        print("  重置測驗狀態: python3 check_user_state.py reset-quiz <LINE_USER_ID>")
        print("  重置讀經進度: python3 check_user_state.py reset-progress <LINE_USER_ID>")
        print("  列出所有使用者: python3 check_user_state.py list")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_all_users()
    elif command == "check" and len(sys.argv) >= 3:
        user_id = sys.argv[2]
        check_user_state(user_id)
    elif command == "reset-quiz" and len(sys.argv) >= 3:
        user_id = sys.argv[2]
        check_user_state(user_id)
        confirm = input("\n確定要重置測驗狀態嗎？(yes/no): ")
        if confirm.lower() == "yes":
            reset_user_quiz_state(user_id)
            print("\n重置後的狀態:")
            check_user_state(user_id)
    elif command == "reset-progress" and len(sys.argv) >= 3:
        user_id = sys.argv[2]
        check_user_state(user_id)
        confirm = input("\n確定要重置讀經進度嗎？(yes/no): ")
        if confirm.lower() == "yes":
            reset_user_reading_progress(user_id)
            print("\n重置後的狀態:")
            check_user_state(user_id)
    else:
        print("❌ 無效的指令")
        sys.exit(1)
