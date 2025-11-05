"""
計分系統核心模組
處理讀經打卡的計分、連續天數、徽章等邏輯
"""
from datetime import datetime, timedelta, date
from typing import Dict, List, Tuple, Optional
from database import UserObject

# === 計分常數 ===

# 基礎分數
BASE_READING_SCORE = 10  # 每日讀經基礎分
QUIZ_PERFECT_SCORE = 5   # 測驗全對
QUIZ_PARTIAL_SCORE = 3   # 測驗部分錯誤

# 補讀分數
MAKEUP_1DAY_SCORE = 8    # 補讀前一天
MAKEUP_OLD_SCORE = 6     # 補讀超過 2 天前

# 連續加成
STREAK_BONUS = {
    (1, 6): 0,
    (7, 13): 2,
    (14, 29): 3,
    (30, 59): 5,
    (60, 99): 7,
    (100, float('inf')): 10
}

# === 徽章定義 ===

BADGES = {
    # 連續天數徽章
    "streak_7": {
        "emoji": "🌱",
        "name": "初心者",
        "description": "連續讀經 7 天",
        "score_reward": 50,
        "check_field": "current_streak",
        "check_value": 7
    },
    "streak_30": {
        "emoji": "🌿",
        "name": "堅持者",
        "description": "連續讀經 30 天",
        "score_reward": 200,
        "check_field": "current_streak",
        "check_value": 30
    },
    "streak_100": {
        "emoji": "🌳",
        "name": "忠心僕人",
        "description": "連續讀經 100 天",
        "score_reward": 1000,
        "check_field": "current_streak",
        "check_value": 100
    },
    "streak_365": {
        "emoji": "👑",
        "name": "讀經勇士",
        "description": "完成全年讀經計畫",
        "score_reward": 3650,
        "check_field": "current_day",
        "check_value": 366  # 完成第 365 天後，current_day 會是 366
    },
    
    # 測驗徽章
    "quiz_perfect_100": {
        "emoji": "🎯",
        "name": "真理探索者",
        "description": "測驗累計 100 次全對",
        "score_reward": 500,
        "check_field": "quiz_perfect_count",
        "check_value": 100
    },
    
    # 特殊徽章
    "restart": {
        "emoji": "🔄",
        "name": "重新出發",
        "description": "中斷後重新開始讀經",
        "score_reward": 50,
        "check_field": None,  # 特殊邏輯
        "check_value": None
    }
}

# === 星級定義 ===

STAR_LEVELS = [
    {"min_score": 0, "max_score": 99, "stars": "⭐", "title": "初學者"},
    {"min_score": 100, "max_score": 499, "stars": "⭐⭐", "title": "學習者"},
    {"min_score": 500, "max_score": 1499, "stars": "⭐⭐⭐", "title": "追求者"},
    {"min_score": 1500, "max_score": 3649, "stars": "⭐⭐⭐⭐", "title": "忠心者"},
    {"min_score": 3650, "max_score": float('inf'), "stars": "⭐⭐⭐⭐⭐", "title": "勇士"}
]


# === 核心函數 ===

def calculate_score(user: UserObject, is_makeup: bool = False, days_ago: int = 0, 
                   quiz_result: str = "none") -> int:
    """
    計算獲得的分數
    
    Args:
        user: 使用者物件
        is_makeup: 是否為補讀
        days_ago: 補讀幾天前的（0 = 今天）
        quiz_result: 測驗結果 ("perfect", "partial", "none")
    
    Returns:
        int: 獲得的分數
    """
    score = 0
    
    # 1. 基礎分
    if is_makeup:
        if days_ago == 1:
            score += MAKEUP_1DAY_SCORE
        else:
            score += MAKEUP_OLD_SCORE
    else:
        score += BASE_READING_SCORE
    
    # 2. 測驗分
    if quiz_result == "perfect":
        score += QUIZ_PERFECT_SCORE
    elif quiz_result == "partial":
        score += QUIZ_PARTIAL_SCORE
    
    # 3. 連續加成（僅非補讀）
    if not is_makeup:
        current_streak = user.current_streak or 0
        for (min_days, max_days), bonus in STREAK_BONUS.items():
            if min_days <= current_streak <= max_days:
                score += bonus
                break
    
    return score


def get_streak_bonus(streak_days: int) -> int:
    """
    根據連續天數獲取加成分數
    
    Args:
        streak_days: 連續天數
    
    Returns:
        int: 加成分數
    """
    for (min_days, max_days), bonus in STREAK_BONUS.items():
        if min_days <= streak_days <= max_days:
            return bonus
    return 0


def update_streak(user: UserObject, reading_date: str) -> Tuple[int, bool]:
    """
    更新連續天數
    
    Args:
        user: 使用者物件
        reading_date: 讀經日期 "YYYY-MM-DD"
    
    Returns:
        Tuple[int, bool]: (新的連續天數, 是否獲得重新出發徽章)
    """
    last_streak_date = user.last_streak_date
    current_streak = user.current_streak or 0
    got_restart_badge = False
    
    # 如果是第一次讀經
    if last_streak_date is None:
        new_streak = 1
    else:
        # 計算日期差
        last_date = datetime.strptime(last_streak_date, '%Y-%m-%d').date()
        current_date = datetime.strptime(reading_date, '%Y-%m-%d').date()
        days_diff = (current_date - last_date).days
        
        if days_diff == 1:
            # 連續
            new_streak = current_streak + 1
        elif days_diff == 0:
            # 同一天（不應該發生，但保險起見）
            new_streak = current_streak
        else:
            # 中斷了
            if current_streak > 0:
                # 之前有連續記錄，給予重新出發徽章
                got_restart_badge = True
            new_streak = 1
    
    return new_streak, got_restart_badge


def check_new_badges(user: UserObject) -> List[Dict]:
    """
    檢查使用者是否達成新徽章
    
    Args:
        user: 使用者物件
    
    Returns:
        List[Dict]: 新獲得的徽章列表
    """
    new_badges = []
    current_badges = user.badges or []
    milestone_achieved = user.milestone_achieved or {}
    
    for badge_id, badge_info in BADGES.items():
        # 如果已經獲得過這個徽章，跳過
        if badge_id in milestone_achieved:
            continue
        
        # 檢查是否達成條件
        check_field = badge_info.get('check_field')
        check_value = badge_info.get('check_value')
        
        if check_field and check_value:
            user_value = getattr(user, check_field, 0) or 0
            if user_value >= check_value:
                new_badges.append({
                    'id': badge_id,
                    'emoji': badge_info['emoji'],
                    'name': badge_info['name'],
                    'description': badge_info['description'],
                    'score_reward': badge_info['score_reward']
                })
    
    return new_badges


def award_badge(user: UserObject, badge_id: str) -> int:
    """
    授予徽章並返回獎勵分數
    
    Args:
        user: 使用者物件
        badge_id: 徽章 ID
    
    Returns:
        int: 獎勵分數
    """
    badge_info = BADGES.get(badge_id)
    if not badge_info:
        return 0
    
    # 更新徽章列表
    current_badges = user.badges or []
    if badge_info['emoji'] not in current_badges:
        current_badges.append(badge_info['emoji'])
        user.badges = current_badges
    
    # 更新里程碑記錄
    milestone_achieved = user.milestone_achieved or {}
    milestone_achieved[badge_id] = datetime.now().strftime('%Y-%m-%d')
    user.milestone_achieved = milestone_achieved
    
    return badge_info['score_reward']


def get_star_level(total_score: int) -> Dict:
    """
    根據總積分獲取星級
    
    Args:
        total_score: 總積分
    
    Returns:
        Dict: 星級資訊
    """
    for level in STAR_LEVELS:
        if level['min_score'] <= total_score <= level['max_score']:
            return level
    
    return STAR_LEVELS[0]  # 預設返回第一級


def add_reading_score(user: UserObject, reading_date: str, is_makeup: bool = False, 
                     days_ago: int = 0, quiz_result: str = "none") -> Dict:
    """
    完成讀經後添加分數（主要函數）
    
    Args:
        user: 使用者物件
        reading_date: 讀經日期 "YYYY-MM-DD"
        is_makeup: 是否為補讀
        days_ago: 補讀幾天前的
        quiz_result: 測驗結果 ("perfect", "partial", "none")
    
    Returns:
        Dict: 包含分數變化和新徽章的資訊
    """
    result = {
        'score_earned': 0,
        'streak_bonus': 0,
        'new_badges': [],
        'total_badge_reward': 0,
        'new_streak': 0,
        'messages': []
    }
    
    # 1. 更新連續天數（僅非補讀）
    if not is_makeup:
        new_streak, got_restart_badge = update_streak(user, reading_date)
        user.current_streak = new_streak
        user.last_streak_date = reading_date
        result['new_streak'] = new_streak
        
        # 更新最長連續天數
        longest_streak = user.longest_streak or 0
        if new_streak > longest_streak:
            user.longest_streak = new_streak
        
        # 重新出發徽章
        if got_restart_badge and 'restart' not in (user.milestone_achieved or {}):
            reward = award_badge(user, 'restart')
            result['total_badge_reward'] += reward
            result['new_badges'].append(BADGES['restart'])
            result['messages'].append(f"🔄 獲得「{BADGES['restart']['name']}」徽章！+{reward} 分")
    
    # 2. 計算分數
    score = calculate_score(user, is_makeup, days_ago, quiz_result)
    result['score_earned'] = score
    result['streak_bonus'] = get_streak_bonus(user.current_streak or 0) if not is_makeup else 0
    
    # 3. 更新統計
    user.total_reading_days = (user.total_reading_days or 0) + 1
    user.week_reading_days = (user.week_reading_days or 0) + 1
    
    if quiz_result == "perfect":
        user.quiz_perfect_count = (user.quiz_perfect_count or 0) + 1
    if quiz_result in ["perfect", "partial"]:
        user.quiz_total_count = (user.quiz_total_count or 0) + 1
    
    # 4. 更新積分
    user.total_score = (user.total_score or 0) + score
    user.week_score = (user.week_score or 0) + score
    user.month_score = (user.month_score or 0) + score
    
    # 5. 檢查新徽章
    new_badges = check_new_badges(user)
    for badge in new_badges:
        reward = award_badge(user, badge['id'])
        result['total_badge_reward'] += reward
        result['new_badges'].append(badge)
        result['messages'].append(f"{badge['emoji']} 獲得「{badge['name']}」徽章！+{reward} 分")
        
        # 將徽章獎勵加入總分
        user.total_score = (user.total_score or 0) + reward
        user.week_score = (user.week_score or 0) + reward
        user.month_score = (user.month_score or 0) + reward
    
    # 6. 儲存變更
    user.save()
    
    return result


def get_user_rank(user: UserObject, leaderboard_type: str = "weekly") -> Optional[int]:
    """
    獲取使用者在排行榜中的排名
    
    Args:
        user: 使用者物件
        leaderboard_type: 排行榜類型 ("weekly", "streak", "total")
    
    Returns:
        Optional[int]: 排名（1-based），如果不在榜上則返回 None
    """
    from google.cloud import firestore
    from database import db, USERS_COLLECTION
    
    users_ref = db.collection(USERS_COLLECTION)
    
    # 根據類型選擇排序欄位
    if leaderboard_type == "weekly":
        order_field = "week_score"
        user_score = user.week_score or 0
    elif leaderboard_type == "streak":
        order_field = "current_streak"
        user_score = user.current_streak or 0
    elif leaderboard_type == "total":
        order_field = "total_score"
        user_score = user.total_score or 0
    else:
        return None
    
    # 查詢比使用者分數高的人數
    query = (users_ref
             .where(filter=firestore.FieldFilter('show_in_leaderboard', '==', True))
             .where(filter=firestore.FieldFilter(order_field, '>', user_score)))
    
    higher_count = len(list(query.stream()))
    
    return higher_count + 1


def format_score_message(result: Dict) -> str:
    """
    格式化計分結果訊息
    
    Args:
        result: add_reading_score 返回的結果
    
    Returns:
        str: 格式化的訊息
    """
    messages = []
    
    # 基本分數
    base_score = result['score_earned'] - result['streak_bonus']
    messages.append(f"📊 今日獲得：{result['score_earned']} 分")
    
    # 分數明細
    details = []
    if base_score > 0:
        details.append(f"基礎 {base_score}")
    if result['streak_bonus'] > 0:
        details.append(f"連續加成 {result['streak_bonus']}")
    
    if details:
        messages.append(f"（{' + '.join(details)}）")
    
    # 連續天數
    if result['new_streak'] > 0:
        messages.append(f"\n🔥 連續讀經：{result['new_streak']} 天")
    
    # 新徽章
    if result['new_badges']:
        messages.append("\n")
        messages.extend(result['messages'])
    
    return '\n'.join(messages)
