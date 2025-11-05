"""
排行榜查詢模組
提供多維度排行榜查詢功能
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from google.cloud import firestore
from database import db, USERS_COLLECTION
from scoring import get_star_level


def get_weekly_leaderboard(limit: int = 10) -> List[Dict]:
    """
    獲取本週排行榜
    
    Args:
        limit: 返回的排名數量
    
    Returns:
        List[Dict]: 排行榜列表
    """
    users_ref = db.collection(USERS_COLLECTION)
    query = (users_ref
             .where(filter=firestore.FieldFilter('show_in_leaderboard', '==', True))
             .where(filter=firestore.FieldFilter('week_score', '>', 0))
             .order_by('week_score', direction=firestore.Query.DESCENDING)
             .limit(limit))
    
    docs = query.stream()
    leaderboard = []
    
    for i, doc in enumerate(docs, 1):
        user_data = doc.to_dict()
        star_level = get_star_level(user_data.get('total_score', 0))
        
        leaderboard.append({
            'rank': i,
            'display_name': user_data.get('display_name_public') or user_data.get('display_name') or '匿名使用者',
            'week_score': user_data.get('week_score', 0),
            'current_streak': user_data.get('current_streak', 0),
            'week_reading_days': user_data.get('week_reading_days', 0),
            'total_score': user_data.get('total_score', 0),
            'stars': star_level['stars'],
            'star_title': star_level['title']
        })
    
    return leaderboard


def get_streak_leaderboard(limit: int = 10) -> List[Dict]:
    """
    獲取連續天數排行榜
    
    Args:
        limit: 返回的排名數量
    
    Returns:
        List[Dict]: 排行榜列表
    """
    users_ref = db.collection(USERS_COLLECTION)
    query = (users_ref
             .where(filter=firestore.FieldFilter('show_in_leaderboard', '==', True))
             .where(filter=firestore.FieldFilter('current_streak', '>', 0))
             .order_by('current_streak', direction=firestore.Query.DESCENDING)
             .limit(limit))
    
    docs = query.stream()
    leaderboard = []
    
    for i, doc in enumerate(docs, 1):
        user_data = doc.to_dict()
        star_level = get_star_level(user_data.get('total_score', 0))
        
        leaderboard.append({
            'rank': i,
            'display_name': user_data.get('display_name_public') or user_data.get('display_name') or '匿名使用者',
            'current_streak': user_data.get('current_streak', 0),
            'longest_streak': user_data.get('longest_streak', 0),
            'total_score': user_data.get('total_score', 0),
            'stars': star_level['stars'],
            'star_title': star_level['title']
        })
    
    return leaderboard


def get_newcomer_leaderboard(limit: int = 5) -> List[Dict]:
    """
    獲取新星榜（加入未滿 30 天）
    
    Args:
        limit: 返回的排名數量
    
    Returns:
        List[Dict]: 新星排行榜列表
    """
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    users_ref = db.collection(USERS_COLLECTION)
    
    # 先查詢所有加入未滿 30 天且顯示在排行榜的使用者
    query = (users_ref
             .where(filter=firestore.FieldFilter('show_in_leaderboard', '==', True))
             .where(filter=firestore.FieldFilter('joined_date', '>=', thirty_days_ago)))
    
    docs = list(query.stream())
    
    # 手動排序（因為 Firestore 不支援多個不等式查詢）
    users_list = []
    for doc in docs:
        user_data = doc.to_dict()
        if user_data.get('week_score', 0) > 0:
            users_list.append(user_data)
    
    # 按 week_score 降序排序
    users_list.sort(key=lambda x: x.get('week_score', 0), reverse=True)
    
    leaderboard = []
    for i, user_data in enumerate(users_list[:limit], 1):
        star_level = get_star_level(user_data.get('total_score', 0))
        joined_date = user_data.get('joined_date')
        
        # 計算加入天數
        if isinstance(joined_date, datetime):
            days_since_joined = (datetime.now() - joined_date).days
        else:
            days_since_joined = 0
        
        leaderboard.append({
            'rank': i,
            'display_name': user_data.get('display_name_public') or user_data.get('display_name') or '匿名使用者',
            'week_score': user_data.get('week_score', 0),
            'current_streak': user_data.get('current_streak', 0),
            'days_since_joined': days_since_joined,
            'total_score': user_data.get('total_score', 0),
            'stars': star_level['stars'],
            'star_title': star_level['title']
        })
    
    return leaderboard


def get_total_leaderboard(limit: int = 20) -> List[Dict]:
    """
    獲取總積分排行榜
    
    Args:
        limit: 返回的排名數量
    
    Returns:
        List[Dict]: 排行榜列表
    """
    users_ref = db.collection(USERS_COLLECTION)
    query = (users_ref
             .where(filter=firestore.FieldFilter('show_in_leaderboard', '==', True))
             .where(filter=firestore.FieldFilter('total_score', '>', 0))
             .order_by('total_score', direction=firestore.Query.DESCENDING)
             .limit(limit))
    
    docs = query.stream()
    leaderboard = []
    
    for i, doc in enumerate(docs, 1):
        user_data = doc.to_dict()
        star_level = get_star_level(user_data.get('total_score', 0))
        
        leaderboard.append({
            'rank': i,
            'display_name': user_data.get('display_name_public') or user_data.get('display_name') or '匿名使用者',
            'total_score': user_data.get('total_score', 0),
            'current_streak': user_data.get('current_streak', 0),
            'total_reading_days': user_data.get('total_reading_days', 0),
            'stars': star_level['stars'],
            'star_title': star_level['title']
        })
    
    return leaderboard


def format_leaderboard_message(leaderboard: List[Dict], leaderboard_type: str, 
                               user_rank: Optional[int] = None, user_score: int = 0) -> str:
    """
    格式化排行榜訊息
    
    Args:
        leaderboard: 排行榜資料
        leaderboard_type: 排行榜類型 ("weekly", "streak", "newcomer", "total")
        user_rank: 使用者排名（可選）
        user_score: 使用者分數（可選）
    
    Returns:
        str: 格式化的排行榜訊息
    """
    # 標題
    titles = {
        "weekly": "🏆 本週讀經排行榜",
        "streak": "🔥 連續天數排行榜",
        "newcomer": "🌟 本週新星榜",
        "total": "👑 總積分排行榜"
    }
    
    title = titles.get(leaderboard_type, "排行榜")
    
    # 獲取當前週的日期範圍
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    date_range = f"（{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}）"
    
    if leaderboard_type in ["weekly", "newcomer"]:
        title += f" {date_range}"
    
    lines = [title, ""]
    
    # 排行榜內容
    if not leaderboard:
        lines.append("目前還沒有人上榜，快來成為第一名！💪")
    else:
        for entry in leaderboard:
            rank = entry['rank']
            name = entry['display_name']
            stars = entry['stars']
            
            # 排名圖示
            if rank == 1:
                rank_icon = "🥇"
            elif rank == 2:
                rank_icon = "🥈"
            elif rank == 3:
                rank_icon = "🥉"
            else:
                rank_icon = f"{rank}."
            
            # 根據排行榜類型顯示不同資訊
            if leaderboard_type == "weekly":
                score = entry['week_score']
                streak = entry['current_streak']
                days = entry['week_reading_days']
                line = f"{rank_icon} {name} {stars} {score}分\n   連續 {streak} 天 | 本週 {days}/7 天"
            
            elif leaderboard_type == "streak":
                streak = entry['current_streak']
                longest = entry['longest_streak']
                line = f"{rank_icon} {name} {stars}\n   連續 {streak} 天 | 最長 {longest} 天"
            
            elif leaderboard_type == "newcomer":
                score = entry['week_score']
                days = entry['days_since_joined']
                line = f"{rank_icon} {name} {stars} {score}分\n   加入 {days} 天"
            
            elif leaderboard_type == "total":
                score = entry['total_score']
                days = entry['total_reading_days']
                line = f"{rank_icon} {name} {stars} {score}分\n   累計 {days} 天"
            
            lines.append(line)
            lines.append("")
    
    # 使用者排名
    if user_rank:
        lines.append("━━━━━━━━━━━━━━━")
        if user_rank <= len(leaderboard):
            lines.append(f"您的排名：第 {user_rank} 名（{user_score} 分）")
        else:
            lines.append(f"您的排名：第 {user_rank} 名（{user_score} 分）")
            # 計算距離前 10 名的差距
            if leaderboard and len(leaderboard) >= 10:
                top10_score = leaderboard[9].get('week_score' if leaderboard_type == 'weekly' else 'total_score', 0)
                gap = top10_score - user_score
                if gap > 0:
                    lines.append(f"再努力 {gap} 分就能進入前 10！💪")
    
    return '\n'.join(lines)


def get_user_stats(user) -> Dict:
    """
    獲取使用者統計資料
    
    Args:
        user: 使用者物件
    
    Returns:
        Dict: 統計資料
    """
    total_score = user.total_score or 0
    star_level = get_star_level(total_score)
    
    # 計算測驗正確率
    quiz_total = user.quiz_total_count or 0
    quiz_perfect = user.quiz_perfect_count or 0
    accuracy = (quiz_perfect / quiz_total * 100) if quiz_total > 0 else 0
    
    return {
        'total_score': total_score,
        'week_score': user.week_score or 0,
        'month_score': user.month_score or 0,
        'current_streak': user.current_streak or 0,
        'longest_streak': user.longest_streak or 0,
        'total_reading_days': user.total_reading_days or 0,
        'week_reading_days': user.week_reading_days or 0,
        'quiz_perfect_count': quiz_perfect,
        'quiz_total_count': quiz_total,
        'quiz_accuracy': accuracy,
        'badges': user.badges or [],
        'stars': star_level['stars'],
        'star_title': star_level['title']
    }
