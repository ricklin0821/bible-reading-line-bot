from fastapi import APIRouter, HTTPException
from database import db, BIBLE_PLANS_COLLECTION, BIBLE_TEXT_COLLECTION
import re
import time
from functools import lru_cache

router = APIRouter(prefix="/api", tags=["api"])

# 簡單的記憶體快取
_cache = {}
CACHE_TTL = 3600  # 快取 1 小時

def get_cached(key, fetch_func, ttl=CACHE_TTL):
    """通用快取函數"""
    now = time.time()
    
    if key in _cache:
        data, cached_time = _cache[key]
        if now - cached_time < ttl:
            return data
    
    # 快取過期或不存在，重新取得資料
    data = fetch_func()
    _cache[key] = (data, now)
    return data

# --- 讀經計畫 API ---

@router.get("/plans/{plan_type}")
def get_plan(plan_type: str):
    """
    獲取指定類型的讀經計畫 (365 天)。
    
    Args:
        plan_type: 'Canonical' 或 'Balanced'
    
    Returns:
        {
            "plan_type": "Canonical",
            "plans": {
                1: {"day_number": 1, "readings": "創1-3"},
                2: {"day_number": 2, "readings": "創4-6"},
                ...
            }
        }
    """
    if plan_type not in ["Canonical", "Balanced"]:
        raise HTTPException(status_code=400, detail="Invalid plan type")
    
    cache_key = f"plan_{plan_type}"
    
    def fetch_plan():
        # 從 Firestore 查詢讀經計畫
        plans_ref = db.collection(BIBLE_PLANS_COLLECTION)
        query = plans_ref.where('plan_type', '==', plan_type)
        docs = query.stream()
        
        plans_dict = {}
        for doc in docs:
            data = doc.to_dict()
            day_number = data.get('day_number')
            if day_number:
                plans_dict[day_number] = {
                    "day_number": day_number,
                    "readings": data.get('readings', '')
                }
        
        if not plans_dict:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        return {
            "plan_type": plan_type,
            "plans": plans_dict
        }
    
    return get_cached(cache_key, fetch_plan)

# --- 經文 API ---
# 注意：/api/verses 已被移除，因為它會讀取 31,000+ 筆資料
# 如果需要查詢經文，請使用 /api/verse/{reference} 查詢單一經文

@router.get("/verse/{reference}")
def get_verse(reference: str):
    """
    獲取單一經文。
    
    Args:
        reference: 經文參考 (例如: "創1:1", "約3:16")
    
    Returns:
        {
            "reference": "創1:1",
            "text": "起初　神創造天地。",
            "book_abbr": "創",
            "chapter": 1,
            "verse": 1
        }
    """
    cache_key = f"verse_{reference}"
    
    def fetch_verse():
        # 解析經文參考
        match = re.match(r'([^0-9]+)(\d+):(\d+)', reference)
        if not match:
            raise HTTPException(status_code=400, detail="Invalid reference format")
        
        book_abbr = match.group(1)
        chapter = int(match.group(2))
        verse = int(match.group(3))
        
        # 從 Firestore 查詢經文
        verses_ref = db.collection(BIBLE_TEXT_COLLECTION)
        query = verses_ref.where('book_abbr', '==', book_abbr) \
                         .where('chapter', '==', chapter) \
                         .where('verse', '==', verse)
        docs = list(query.stream())
        
        if not docs:
            raise HTTPException(status_code=404, detail="Verse not found")
        
        data = docs[0].to_dict()
        return {
            "reference": reference,
            "text": data.get('text', ''),
            "book_abbr": book_abbr,
            "chapter": chapter,
            "verse": verse
        }
    
    return get_cached(cache_key, fetch_verse)

@router.get("/verses/range")
def get_verses_range(book: str, chapter: int, start_verse: int = 1, end_verse: int = 999):
    """
    獲取一段經文範圍。
    
    Args:
        book: 書卷縮寫 (例如: "創", "約")
        chapter: 章數
        start_verse: 起始節數 (預設 1)
        end_verse: 結束節數 (預設 999)
    
    Returns:
        {
            "verses": [
                {"verse": 1, "text": "..."},
                {"verse": 2, "text": "..."},
                ...
            ]
        }
    """
    cache_key = f"verses_range_{book}_{chapter}_{start_verse}_{end_verse}"
    
    def fetch_verses():
        # 從 Firestore 查詢經文範圍
        verses_ref = db.collection(BIBLE_TEXT_COLLECTION)
        query = verses_ref.where('book_abbr', '==', book) \
                         .where('chapter', '==', chapter) \
                         .where('verse', '>=', start_verse) \
                         .where('verse', '<=', end_verse) \
                         .order_by('verse')
        docs = query.stream()
        
        verses_list = []
        for doc in docs:
            data = doc.to_dict()
            verses_list.append({
                "verse": data.get('verse'),
                "text": data.get('text', '')
            })
        
        return {"verses": verses_list}
    
    return get_cached(cache_key, fetch_verses)

# --- 統計 API ---

@router.get("/stats")
def get_stats():
    """
    獲取簡單的統計資料 (已快取)。
    
    Returns:
        {
            "total_verses": 31102,
            "total_plans": 730,
            "available_plan_types": ["Canonical", "Balanced"]
        }
    """
    cache_key = "stats"
    
    def fetch_stats():
        # 這些是固定值，可以直接返回
        return {
            "total_verses": 31102,
            "total_plans": 730,
            "available_plan_types": ["Canonical", "Balanced"]
        }
    
    # 快取 24 小時
    return get_cached(cache_key, fetch_stats, ttl=86400)

# --- 清除快取 API (僅供管理員使用) ---

@router.post("/cache/clear")
def clear_cache(secret: str):
    """
    清除所有 API 快取。
    
    Args:
        secret: 管理員密鑰（必須從環境變數 CACHE_CLEAR_SECRET 設定）
    """
    import os
    CACHE_CLEAR_SECRET = os.environ.get("CACHE_CLEAR_SECRET")
    
    if not CACHE_CLEAR_SECRET:
        raise HTTPException(status_code=500, detail="CACHE_CLEAR_SECRET not configured")
    
    if secret != CACHE_CLEAR_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    _cache.clear()
    return {"message": "Cache cleared successfully"}

