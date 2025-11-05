"""
資料遷移腳本：為現有使用者添加計分系統欄位
執行方式：python3.11 migrate_scoring.py
"""
from datetime import datetime
from database import db, USERS_COLLECTION


def migrate_existing_users():
    """為現有使用者添加計分系統欄位"""
    print("開始資料遷移...")
    
    users_ref = db.collection(USERS_COLLECTION)
    docs = list(users_ref.stream())
    
    print(f"找到 {len(docs)} 位使用者")
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    default_values = {
        'total_score': 0,
        'week_score': 0,
        'month_score': 0,
        'current_streak': 0,
        'longest_streak': 0,
        'last_streak_date': None,
        'total_reading_days': 0,
        'quiz_perfect_count': 0,
        'quiz_total_count': 0,
        'week_reading_days': 0,
        'badges': [],
        'milestone_achieved': {},
        'show_in_leaderboard': True,
        'display_name_public': None,
        'joined_date': datetime.now(),
        'week_reset_date': today_str,
        'month_reset_date': today_str
    }
    
    updated_count = 0
    
    for doc in docs:
        user_data = doc.to_dict()
        update_data = {}
        
        # 只添加不存在的欄位
        for key, value in default_values.items():
            if key not in user_data or user_data.get(key) is None:
                update_data[key] = value
        
        # 如果 display_name_public 為 None，使用 display_name
        if 'display_name_public' not in user_data or user_data.get('display_name_public') is None:
            display_name = user_data.get('display_name', '匿名使用者')
            update_data['display_name_public'] = display_name if display_name else '匿名使用者'
        
        # 如果 joined_date 不存在，使用 start_date
        if 'joined_date' not in user_data or user_data.get('joined_date') is None:
            start_date = user_data.get('start_date')
            if start_date:
                update_data['joined_date'] = start_date
            else:
                update_data['joined_date'] = datetime.now()
        
        if update_data:
            doc.reference.update(update_data)
            updated_count += 1
            print(f"✓ 已更新使用者: {doc.id} ({user_data.get('display_name', '未知')})")
            print(f"  新增欄位: {', '.join(update_data.keys())}")
    
    print(f"\n遷移完成！共更新 {updated_count} 位使用者")
    
    if updated_count == 0:
        print("所有使用者都已經有計分系統欄位了")


if __name__ == "__main__":
    migrate_existing_users()
