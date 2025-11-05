# 讀經打卡排行榜計分系統設計文件

## 一、資料庫結構設計

### 1. User Collection 新增欄位

在現有的 `users` collection 中新增以下欄位：

```python
{
    # === 現有欄位 ===
    "line_user_id": str,
    "plan_type": str,
    "start_date": datetime,
    "current_day": int,
    "last_read_date": str,  # "YYYY-MM-DD" 格式
    "quiz_state": str,
    "quiz_data": str,
    "display_name": str,
    "contact_state": str,
    "contact_email": str,
    
    # === 新增：計分系統欄位 ===
    
    # 積分相關
    "total_score": int,  # 總積分（預設 0）
    "week_score": int,  # 本週積分（預設 0）
    "month_score": int,  # 本月積分（預設 0）
    
    # 連續天數相關
    "current_streak": int,  # 當前連續天數（預設 0）
    "longest_streak": int,  # 最長連續天數（預設 0）
    "last_streak_date": str,  # 最後連續日期 "YYYY-MM-DD"（用於判斷是否中斷）
    
    # 統計相關
    "total_reading_days": int,  # 總讀經天數（預設 0）
    "quiz_perfect_count": int,  # 測驗全對次數（預設 0）
    "quiz_total_count": int,  # 測驗總次數（預設 0）
    "week_reading_days": int,  # 本週讀經天數（預設 0）
    
    # 徽章相關
    "badges": list,  # 已獲得的徽章列表（預設 []）
    "milestone_achieved": dict,  # 已達成的里程碑（預設 {}）
    
    # 排行榜相關
    "show_in_leaderboard": bool,  # 是否顯示在排行榜（預設 True）
    "display_name_public": str,  # 公開顯示的名稱（預設使用 display_name）
    
    # 時間戳
    "joined_date": datetime,  # 加入日期
    "week_reset_date": str,  # 上次週重置日期 "YYYY-MM-DD"
    "month_reset_date": str,  # 上次月重置日期 "YYYY-MM-DD"
}
```

### 2. 徽章定義

```python
BADGES = {
    # 連續天數徽章
    "streak_7": {
        "emoji": "🌱",
        "name": "初心者",
        "description": "連續讀經 7 天",
        "score_reward": 50
    },
    "streak_30": {
        "emoji": "🌿",
        "name": "堅持者",
        "description": "連續讀經 30 天",
        "score_reward": 200
    },
    "streak_100": {
        "emoji": "🌳",
        "name": "忠心僕人",
        "description": "連續讀經 100 天",
        "score_reward": 1000
    },
    "streak_365": {
        "emoji": "👑",
        "name": "讀經勇士",
        "description": "完成全年讀經計畫",
        "score_reward": 3650
    },
    
    # 測驗徽章
    "quiz_perfect_100": {
        "emoji": "🎯",
        "name": "真理探索者",
        "description": "測驗累計 100 次全對",
        "score_reward": 500
    },
    
    # 書卷徽章
    "pentateuch": {
        "emoji": "📜",
        "name": "律法之光",
        "description": "完成摩西五經",
        "score_reward": 300
    },
    "gospels": {
        "emoji": "✝️",
        "name": "福音使者",
        "description": "完成四福音書",
        "score_reward": 300
    },
    
    # 特殊徽章
    "restart": {
        "emoji": "🔄",
        "name": "重新出發",
        "description": "中斷後重新開始讀經",
        "score_reward": 50
    }
}
```

### 3. 星級定義

```python
STAR_LEVELS = [
    {"min_score": 0, "max_score": 99, "stars": "⭐", "title": "初學者"},
    {"min_score": 100, "max_score": 499, "stars": "⭐⭐", "title": "學習者"},
    {"min_score": 500, "max_score": 1499, "stars": "⭐⭐⭐", "title": "追求者"},
    {"min_score": 1500, "max_score": 3649, "stars": "⭐⭐⭐⭐", "title": "忠心者"},
    {"min_score": 3650, "max_score": float('inf'), "stars": "⭐⭐⭐⭐⭐", "title": "勇士"}
]
```

## 二、計分規則

### 1. 基礎分數

```python
# 每日讀經基礎分
BASE_READING_SCORE = 10

# 測驗分數
QUIZ_PERFECT_SCORE = 5  # 全對
QUIZ_PARTIAL_SCORE = 3  # 部分錯誤

# 補讀分數
MAKEUP_1DAY_SCORE = 8  # 補讀前一天
MAKEUP_OLD_SCORE = 6   # 補讀超過 2 天前
```

### 2. 連續加成

```python
STREAK_BONUS = {
    (1, 6): 0,      # 1-6 天：無加成
    (7, 13): 2,     # 7-13 天：+2 分
    (14, 29): 3,    # 14-29 天：+3 分
    (30, 59): 5,    # 30-59 天：+5 分
    (60, 99): 7,    # 60-99 天：+7 分
    (100, float('inf')): 10  # 100+ 天：+10 分
}
```

### 3. 計分函數

```python
def calculate_score(user, is_makeup=False, days_ago=0, quiz_result="perfect"):
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
        current_streak = user.current_streak
        for (min_days, max_days), bonus in STREAK_BONUS.items():
            if min_days <= current_streak <= max_days:
                score += bonus
                break
    
    return score
```

## 三、排行榜查詢

### 1. 本週排行榜

```python
def get_weekly_leaderboard(limit=10):
    """
    獲取本週排行榜
    
    Returns:
        list: 排行榜列表
    """
    users_ref = db.collection(USERS_COLLECTION)
    query = (users_ref
             .where(filter=firestore.FieldFilter('show_in_leaderboard', '==', True))
             .order_by('week_score', direction=firestore.Query.DESCENDING)
             .limit(limit))
    
    docs = query.stream()
    leaderboard = []
    
    for i, doc in enumerate(docs, 1):
        user_data = doc.to_dict()
        leaderboard.append({
            'rank': i,
            'display_name': user_data.get('display_name_public', '匿名使用者'),
            'week_score': user_data.get('week_score', 0),
            'current_streak': user_data.get('current_streak', 0),
            'week_reading_days': user_data.get('week_reading_days', 0),
            'total_score': user_data.get('total_score', 0)
        })
    
    return leaderboard
```

### 2. 連續天數排行榜

```python
def get_streak_leaderboard(limit=10):
    """獲取連續天數排行榜"""
    users_ref = db.collection(USERS_COLLECTION)
    query = (users_ref
             .where(filter=firestore.FieldFilter('show_in_leaderboard', '==', True))
             .order_by('current_streak', direction=firestore.Query.DESCENDING)
             .limit(limit))
    
    docs = query.stream()
    leaderboard = []
    
    for i, doc in enumerate(docs, 1):
        user_data = doc.to_dict()
        leaderboard.append({
            'rank': i,
            'display_name': user_data.get('display_name_public', '匿名使用者'),
            'current_streak': user_data.get('current_streak', 0),
            'total_score': user_data.get('total_score', 0)
        })
    
    return leaderboard
```

### 3. 新星榜

```python
def get_newcomer_leaderboard(limit=5):
    """
    獲取新星榜（加入未滿 30 天）
    
    Returns:
        list: 新星排行榜列表
    """
    from datetime import datetime, timedelta
    
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    users_ref = db.collection(USERS_COLLECTION)
    query = (users_ref
             .where(filter=firestore.FieldFilter('show_in_leaderboard', '==', True))
             .where(filter=firestore.FieldFilter('joined_date', '>=', thirty_days_ago))
             .order_by('joined_date')
             .order_by('week_score', direction=firestore.Query.DESCENDING)
             .limit(limit))
    
    docs = query.stream()
    leaderboard = []
    
    for i, doc in enumerate(docs, 1):
        user_data = doc.to_dict()
        leaderboard.append({
            'rank': i,
            'display_name': user_data.get('display_name_public', '匿名使用者'),
            'week_score': user_data.get('week_score', 0),
            'current_streak': user_data.get('current_streak', 0),
            'joined_date': user_data.get('joined_date')
        })
    
    return leaderboard
```

## 四、週期性重置

### 1. 週重置（每週一 00:00）

```python
def reset_weekly_scores():
    """重置所有使用者的週積分和週讀經天數"""
    from datetime import datetime
    
    users_ref = db.collection(USERS_COLLECTION)
    docs = users_ref.stream()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    for doc in docs:
        doc.reference.update({
            'week_score': 0,
            'week_reading_days': 0,
            'week_reset_date': today
        })
```

### 2. 月重置（每月 1 日 00:00）

```python
def reset_monthly_scores():
    """重置所有使用者的月積分"""
    from datetime import datetime
    
    users_ref = db.collection(USERS_COLLECTION)
    docs = users_ref.stream()
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    for doc in docs:
        doc.reference.update({
            'month_score': 0,
            'month_reset_date': today
        })
```

## 五、資料遷移

### 為現有使用者添加新欄位

```python
def migrate_existing_users():
    """為現有使用者添加計分系統欄位"""
    from datetime import datetime
    
    users_ref = db.collection(USERS_COLLECTION)
    docs = users_ref.stream()
    
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
        'week_reset_date': datetime.now().strftime('%Y-%m-%d'),
        'month_reset_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    for doc in docs:
        user_data = doc.to_dict()
        update_data = {}
        
        # 只添加不存在的欄位
        for key, value in default_values.items():
            if key not in user_data:
                update_data[key] = value
        
        # 如果 display_name_public 為 None，使用 display_name
        if 'display_name_public' not in user_data or user_data.get('display_name_public') is None:
            update_data['display_name_public'] = user_data.get('display_name', '匿名使用者')
        
        if update_data:
            doc.reference.update(update_data)
            print(f"Updated user: {doc.id}")
```

## 六、實作優先順序

### Phase 1: 核心計分系統
1. 更新 User.create() 添加新欄位
2. 實作 calculate_score() 函數
3. 實作連續天數計算
4. 整合到完成讀經流程

### Phase 2: 排行榜查詢
1. 實作本週排行榜
2. 實作連續天數排行榜
3. 實作新星榜
4. 添加查詢指令

### Phase 3: 個人儀表板
1. 設計 FlexMessage
2. 實作個人數據展示
3. 添加查詢指令

### Phase 4: 徽章系統
1. 實作里程碑檢測
2. 實作徽章授予
3. 實作徽章展示

### Phase 5: 週期性重置
1. 設定 Cloud Scheduler
2. 實作重置函數
3. 測試重置邏輯

### Phase 6: 資料遷移與測試
1. 執行資料遷移
2. 全面測試
3. 部署上線
