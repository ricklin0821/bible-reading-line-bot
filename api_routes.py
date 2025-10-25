from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, BiblePlan, BibleText
import re

router = APIRouter(prefix="/api", tags=["api"])

# --- 讀經計畫 API ---

@router.get("/plans/{plan_type}")
def get_plan(plan_type: str, db: Session = Depends(get_db)):
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
    
    plans = db.query(BiblePlan).filter(BiblePlan.plan_type == plan_type).all()
    
    if not plans:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    # 轉換為字典格式，以日期為鍵
    plans_dict = {}
    for plan in plans:
        plans_dict[plan.day_number] = {
            "day_number": plan.day_number,
            "readings": plan.readings
        }
    
    return {
        "plan_type": plan_type,
        "plans": plans_dict
    }

# --- 經文 API ---

@router.get("/verses")
def get_all_verses(db: Session = Depends(get_db)):
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
    verses = db.query(BibleText).all()
    
    verses_dict = {}
    for verse in verses:
        key = f"{verse.book_abbr}{verse.chapter}:{verse.verse}"
        verses_dict[key] = {
            "book_abbr": verse.book_abbr,
            "book": verse.book,
            "chapter": verse.chapter,
            "verse": verse.verse,
            "text": verse.text
        }
    
    return {
        "verses": verses_dict
    }

@router.get("/verses/{reading_ref}")
def get_verses_by_reference(reading_ref: str, db: Session = Depends(get_db)):
    """
    根據經文範圍字串獲取經文。
    
    Args:
        reading_ref: 經文範圍，例如 '創1:1-3:24' 或 '創1-3' 或 '創1,創2,創3'
    
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
                verses = db.query(BibleText).filter(
                    BibleText.book_abbr == book_abbr,
                    BibleText.chapter == int(chap)
                ).order_by(BibleText.verse).all()
                all_verses.extend(verses)
            continue
        
        book_abbr, start_chap_str, start_verse_str, end_chap_str, end_verse_str = match.groups()
        
        start_chap = int(start_chap_str)
        end_chap = int(end_chap_str) if end_chap_str else start_chap
        start_verse = int(start_verse_str) if start_verse_str else 1
        
        # 複雜的經文範圍查詢
        query = db.query(BibleText).filter(BibleText.book_abbr == book_abbr)
        
        if start_chap == end_chap:
            # 單章範圍
            query = query.filter(BibleText.chapter == start_chap)
            
            if start_verse_str:
                # 節範圍
                end_verse = int(end_verse_str) if end_verse_str else 999 # 假設一個很大的數
                query = query.filter(BibleText.verse.between(start_verse, end_verse))
        else:
            # 跨章範圍
            query = query.filter(BibleText.chapter.between(start_chap, end_chap))
            
            # 處理起始節和結束節
            if start_verse_str:
                # 排除起始章中在起始節之前的節
                query = query.filter(
                    (BibleText.chapter > start_chap) | 
                    ((BibleText.chapter == start_chap) & (BibleText.verse >= start_verse))
                )
            
            if end_verse_str:
                end_verse = int(end_verse_str)
                # 排除結束章中在結束節之後的節
                query = query.filter(
                    (BibleText.chapter < end_chap) |
                    ((BibleText.chapter == end_chap) & (BibleText.verse <= end_verse))
                )
        
        verses = query.order_by(BibleText.chapter, BibleText.verse).all()
        all_verses.extend(verses)
    
    # 轉換為字典格式
    verses_list = []
    for verse in all_verses:
        verses_list.append({
            "book_abbr": verse.book_abbr,
            "book": verse.book,
            "chapter": verse.chapter,
            "verse": verse.verse,
            "text": verse.text
        })
    
    return {
        "verses": verses_list
    }

@router.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
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
    # 統計總經節數
    total_verses = db.query(BibleText).count()
    
    # 統計書卷數
    books = db.query(BibleText.book).distinct().count()
    
    # 統計章節數
    chapters = db.query(BibleText.chapter).distinct().count()
    
    # 獲取各書卷的章節數
    book_stats = db.query(
        BibleText.book,
        BibleText.book_abbr,
        db.func.max(BibleText.chapter).label('max_chapter')
    ).group_by(BibleText.book, BibleText.book_abbr).all()
    
    books_list = []
    for book, book_abbr, max_chapter in book_stats:
        books_list.append({
            "book": book,
            "book_abbr": book_abbr,
            "chapters": max_chapter
        })
    
    return {
        "total_verses": total_verses,
        "total_books": books,
        "total_chapters": chapters,
        "books": books_list
    }
