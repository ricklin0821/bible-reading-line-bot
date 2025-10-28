from fastapi import APIRouter, HTTPException
from database import db, BIBLE_PLANS_COLLECTION, BIBLE_TEXT_COLLECTION
import re

router = APIRouter(prefix="/api", tags=["api"])

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

# --- 經文 API ---

@router.get("/verses")
def get_all_verses():
    """
    獲取所有經文資料 (用於前端快取)。
    
    Returns:
        {
            "verses": {
                "創1:1": {"book_abbr": "創", "chapter": 1, "verse": 1, "text": "..."},
                ...
            }
        }
    """
    # 從 Firestore 查詢所有經文
    verses_ref = db.collection(BIBLE_TEXT_COLLECTION)
    docs = verses_ref.stream()
    
    verses_dict = {}
    for doc in docs:
        data = doc.to_dict()
        book_abbr = data.get('book_abbr', '')
        chapter = data.get('chapter', 0)
        verse = data.get('verse', 0)
        
        key = f"{book_abbr}{chapter}:{verse}"
        verses_dict[key] = {
            "book_abbr": book_abbr,
            "book": data.get('book', ''),
            "chapter": chapter,
            "verse": verse,
            "text": data.get('text', '')
        }
    
    return {
        "verses": verses_dict
    }

@router.get("/verses/{reading_ref}")
def get_verses_by_reference(reading_ref: str):
    """
    根據經文範圍字串獲取經文。
    
    Args:
        reading_ref: 經文範圍，例如 '創1:1-3:24' 或 '創1-3' 或 '創1;創2;創3'
    
    Returns:
        {
            "verses": [
                {"book_abbr": "創", "chapter": 1, "verse": 1, "text": "..."},
                ...
            ]
        }
    """
    all_verses = []
    
    # 處理多個閱讀範圍 (以分號分隔)
    refs = reading_ref.split(';')
    
    for ref in refs:
        ref = ref.strip()
        if not ref:
            continue
        
        # 匹配書卷縮寫和章節範圍 (例如: 創1-3, 太1:1-2:23)
        match = re.match(r'([^\d]+)(\d+)(?::(\d+))?(?:-(\d+)(?::(\d+))?)?', ref)
        
        if not match:
            # 處理只有章節的情況 (例如: 創1)
            match_chap = re.match(r'([^\d]+)(\d+)', ref)
            if match_chap:
                book_abbr, chap = match_chap.groups()
                # 從 Firestore 查詢
                verses_ref = db.collection(BIBLE_TEXT_COLLECTION)
                query = verses_ref.where('book_abbr', '==', book_abbr).where('chapter', '==', int(chap))
                docs = query.stream()
                
                for doc in docs:
                    all_verses.append(doc.to_dict())
            continue
        
        book_abbr, start_chap_str, start_verse_str, end_chap_str, end_verse_str = match.groups()
        
        start_chap = int(start_chap_str)
        end_chap = int(end_chap_str) if end_chap_str else start_chap
        start_verse = int(start_verse_str) if start_verse_str else None
        end_verse = int(end_verse_str) if end_verse_str else None
        
        # 從 Firestore 查詢範圍內的經文
        verses_ref = db.collection(BIBLE_TEXT_COLLECTION)
        query = verses_ref.where('book_abbr', '==', book_abbr)
        docs = query.stream()
        
        for doc in docs:
            data = doc.to_dict()
            chapter = data.get('chapter')
            verse = data.get('verse')
            
            # 範圍篩選
            if chapter < start_chap or chapter > end_chap:
                continue
            
            if start_verse and chapter == start_chap and verse < start_verse:
                continue
            
            if end_verse and chapter == end_chap and verse > end_verse:
                continue
            
            all_verses.append(data)
    
    # 按章節和節數排序
    all_verses.sort(key=lambda x: (x.get('chapter', 0), x.get('verse', 0)))
    
    # 轉換為字典格式
    verses_list = []
    for verse in all_verses:
        verses_list.append({
            "book_abbr": verse.get('book_abbr', ''),
            "book": verse.get('book', ''),
            "chapter": verse.get('chapter', 0),
            "verse": verse.get('verse', 0),
            "text": verse.get('text', '')
        })
    
    return {
        "verses": verses_list
    }

@router.get("/stats")
def get_statistics():
    """
    獲取聖經統計資訊。
    
    Returns:
        {
            "total_verses": 31103,
            "total_books": 66,
            "total_chapters": 1189,
            "books": [...]
        }
    """
    # 從 Firestore 查詢所有經文
    verses_ref = db.collection(BIBLE_TEXT_COLLECTION)
    docs = verses_ref.stream()
    
    total_verses = 0
    books_dict = {}  # {book_abbr: {book: name, max_chapter: num}}
    
    for doc in docs:
        data = doc.to_dict()
        total_verses += 1
        
        book = data.get('book', '')
        book_abbr = data.get('book_abbr', '')
        chapter = data.get('chapter', 0)
        
        if book_abbr not in books_dict:
            books_dict[book_abbr] = {
                "book": book,
                "book_abbr": book_abbr,
                "max_chapter": chapter
            }
        else:
            if chapter > books_dict[book_abbr]["max_chapter"]:
                books_dict[book_abbr]["max_chapter"] = chapter
    
    books_list = []
    for book_abbr, book_data in books_dict.items():
        books_list.append({
            "book": book_data["book"],
            "book_abbr": book_abbr,
            "chapters": book_data["max_chapter"]
        })
    
    return {
        "total_verses": total_verses,
        "total_books": len(books_dict),
        "total_chapters": sum(b["chapters"] for b in books_list),
        "books": books_list
    }

