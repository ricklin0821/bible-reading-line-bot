"""
Firestore 資料庫層
遷移自 SQLAlchemy/SQLite，現在使用 Google Cloud Firestore
"""
import pandas as pd
from google.cloud import firestore
from datetime import date, datetime
import json
from typing import Optional, List, Dict, Any

# 初始化 Firestore 客戶端
db = firestore.Client()

# 集合名稱
USERS_COLLECTION = "users"
BIBLE_PLANS_COLLECTION = "bible_plans"
BIBLE_TEXT_COLLECTION = "bible_text"

# --- User 類別 (Firestore 版本) ---

class User:
    """使用者類別 - Firestore 版本"""
    
    @staticmethod
    def get_by_line_id(line_user_id: str) -> Optional[Dict[str, Any]]:
        """根據 LINE User ID 查詢使用者"""
        users_ref = db.collection(USERS_COLLECTION)
        query = users_ref.where(filter=firestore.FieldFilter('line_user_id', '==', line_user_id)).limit(1)
        docs = list(query.stream())
        
        if docs:
            user_data = docs[0].to_dict()
            user_data['_id'] = docs[0].id  # 保存文檔 ID
            return user_data
        return None
    
    @staticmethod
    def create(line_user_id: str, plan_type: str = None) -> Dict[str, Any]:
        """建立新使用者"""
        users_ref = db.collection(USERS_COLLECTION)
        
        user_data = {
            'line_user_id': line_user_id,
            'plan_type': plan_type,
            'start_date': date.today(),
            'current_day': 1,
            'last_read_date': None,
            'quiz_state': 'IDLE',
            'quiz_data': '{}'
        }
        
        doc_ref = users_ref.document()
        doc_ref.set(user_data)
        
        user_data['_id'] = doc_ref.id
        return user_data
    
    @staticmethod
    def update(line_user_id: str, **kwargs) -> bool:
        """更新使用者資料"""
        user = User.get_by_line_id(line_user_id)
        if not user:
            return False
        
        users_ref = db.collection(USERS_COLLECTION)
        doc_ref = users_ref.document(user['_id'])
        
        # 處理 date 物件轉換
        update_data = {}
        for key, value in kwargs.items():
            if isinstance(value, date) and not isinstance(value, datetime):
                update_data[key] = value
            else:
                update_data[key] = value
        
        doc_ref.update(update_data)
        return True
    
    @staticmethod
    def get_all() -> List[Dict[str, Any]]:
        """取得所有使用者"""
        users_ref = db.collection(USERS_COLLECTION)
        docs = users_ref.stream()
        
        users = []
        for doc in docs:
            user_data = doc.to_dict()
            user_data['_id'] = doc.id
            users.append(user_data)
        
        return users

# --- BiblePlan 類別 (Firestore 版本) ---

class BiblePlan:
    """讀經計畫類別 - Firestore 版本"""
    
    @staticmethod
    def get_by_day(plan_type: str, day_number: int) -> Optional[Dict[str, Any]]:
        """根據計畫類型和天數查詢讀經計畫"""
        plans_ref = db.collection(BIBLE_PLANS_COLLECTION)
        query = plans_ref.where(
            filter=firestore.FieldFilter('plan_type', '==', plan_type)
        ).where(
            filter=firestore.FieldFilter('day_number', '==', day_number)
        ).limit(1)
        
        docs = list(query.stream())
        
        if docs:
            plan_data = docs[0].to_dict()
            plan_data['_id'] = docs[0].id
            return plan_data
        return None
    
    @staticmethod
    def get_all_by_type(plan_type: str) -> List[Dict[str, Any]]:
        """取得特定類型的所有讀經計畫"""
        plans_ref = db.collection(BIBLE_PLANS_COLLECTION)
        query = plans_ref.where(filter=firestore.FieldFilter('plan_type', '==', plan_type))
        docs = query.stream()
        
        plans = []
        for doc in docs:
            plan_data = doc.to_dict()
            plan_data['_id'] = doc.id
            plans.append(plan_data)
        
        return plans

# --- BibleText 類別 (Firestore 版本) ---

class BibleText:
    """聖經經文類別 - Firestore 版本"""
    
    @staticmethod
    def get_verse(book_abbr: str, chapter: int, verse: int) -> Optional[Dict[str, Any]]:
        """查詢單節經文"""
        texts_ref = db.collection(BIBLE_TEXT_COLLECTION)
        query = texts_ref.where(
            filter=firestore.FieldFilter('book_abbr', '==', book_abbr)
        ).where(
            filter=firestore.FieldFilter('chapter', '==', chapter)
        ).where(
            filter=firestore.FieldFilter('verse', '==', verse)
        ).limit(1)
        
        docs = list(query.stream())
        
        if docs:
            verse_data = docs[0].to_dict()
            verse_data['_id'] = docs[0].id
            return verse_data
        return None
    
    @staticmethod
    def get_verses_by_reference(book_abbr: str, chapter: int) -> List[Dict[str, Any]]:
        """查詢整章經文"""
        texts_ref = db.collection(BIBLE_TEXT_COLLECTION)
        query = texts_ref.where(
            filter=firestore.FieldFilter('book_abbr', '==', book_abbr)
        ).where(
            filter=firestore.FieldFilter('chapter', '==', chapter)
        ).order_by('verse')
        
        docs = query.stream()
        
        verses = []
        for doc in docs:
            verse_data = doc.to_dict()
            verse_data['_id'] = doc.id
            verses.append(verse_data)
        
        return verses
    
    @staticmethod
    def get_verses_in_range(book_abbr: str, start_chap: int, end_chap: int, 
                           start_verse: Optional[int] = None, 
                           end_verse: Optional[int] = None) -> List[Dict[str, Any]]:
        """查詢經文範圍"""
        texts_ref = db.collection(BIBLE_TEXT_COLLECTION)
        
        # 基本查詢：書卷和章節範圍
        query = texts_ref.where(
            filter=firestore.FieldFilter('book_abbr', '==', book_abbr)
        ).where(
            filter=firestore.FieldFilter('chapter', '>=', start_chap)
        ).where(
            filter=firestore.FieldFilter('chapter', '<=', end_chap)
        ).order_by('chapter').order_by('verse')
        
        docs = query.stream()
        
        verses = []
        for doc in docs:
            verse_data = doc.to_dict()
            verse_data['_id'] = doc.id
            
            # 過濾節數範圍
            if start_verse and verse_data['chapter'] == start_chap and verse_data['verse'] < start_verse:
                continue
            if end_verse and verse_data['chapter'] == end_chap and verse_data['verse'] > end_verse:
                continue
            
            verses.append(verse_data)
        
        return verses
    
    @staticmethod
    def search_text(keyword: str, limit: int = 100) -> List[Dict[str, Any]]:
        """搜尋包含關鍵字的經文 (注意：Firestore 不支援全文搜尋，這裡只能做簡單的前綴匹配)"""
        # Firestore 的限制：無法直接做 LIKE 查詢
        # 這裡返回所有經文，在應用層過濾
        texts_ref = db.collection(BIBLE_TEXT_COLLECTION)
        docs = texts_ref.limit(limit).stream()
        
        verses = []
        for doc in docs:
            verse_data = doc.to_dict()
            if keyword in verse_data.get('text', ''):
                verse_data['_id'] = doc.id
                verses.append(verse_data)
        
        return verses

# --- 資料庫初始化函數 ---

def init_db():
    """初始化 Firestore 資料庫，如果資料不存在則匯入"""
    print("Initializing Firestore database...")
    
    # 檢查讀經計畫版本
    PLAN_VERSION = "v2_correct_order"  # 版本標記
    version_ref = db.collection('_metadata').document('plan_version')
    version_doc = version_ref.get()
    
    current_version = version_doc.to_dict().get('version') if version_doc.exists else None
    
    # 檢查是否已匯入聖經經文資料
    bible_text_ref = db.collection(BIBLE_TEXT_COLLECTION)
    bible_text_count = len(list(bible_text_ref.limit(1).stream()))
    
    print(f"Current BibleText count: {bible_text_count}")
    
    if bible_text_count == 0:
        print("Importing Bible text data to Firestore...")
        try:
            bible_df = pd.read_csv('data/bible_text.csv')
            print(f"Read {len(bible_df)} verses from CSV.")
            
            # 批次寫入 Firestore（每批 500 筆）
            batch = db.batch()
            batch_count = 0
            
            for index, row in bible_df.iterrows():
                doc_ref = bible_text_ref.document()
                batch.set(doc_ref, {
                    'book_abbr': row['book_abbr'],
                    'book': row['book'],
                    'chapter': int(row['chapter']),
                    'verse': int(row['verse']),
                    'text': row['text']
                })
                batch_count += 1
                
                if batch_count >= 500:
                    batch.commit()
                    print(f"Committed {batch_count} verses to Firestore.")
                    batch = db.batch()
                    batch_count = 0
            
            if batch_count > 0:
                batch.commit()
                print(f"Committed final {batch_count} verses to Firestore.")
            
            print(f"Successfully imported {len(bible_df)} verses to Firestore.")
        except FileNotFoundError as e:
            print(f"Error: data/bible_text.csv not found - {e}")
        except Exception as e:
            print(f"Error importing Bible text: {e}")
    else:
        print("Bible text data already exists in Firestore, skipping import.")
    
    # 檢查讀經計畫版本並決定是否需要更新
    bible_plans_ref = db.collection(BIBLE_PLANS_COLLECTION)
    need_update = False
    
    if current_version != PLAN_VERSION:
        print(f"Reading plan version mismatch (current: {current_version}, required: {PLAN_VERSION})")
        print("Will update reading plans...")
        need_update = True
    else:
        bible_plans_count = len(list(bible_plans_ref.limit(1).stream()))
        if bible_plans_count == 0:
            print("No reading plans found in Firestore.")
            need_update = True
    
    if need_update:
        print("Updating Bible plans data in Firestore...")
        try:
            # 刪除舊的讀經計畫
            print("Deleting old reading plans...")
            docs = bible_plans_ref.stream()
            delete_batch = db.batch()
            delete_count = 0
            for doc in docs:
                delete_batch.delete(doc.reference)
                delete_count += 1
                if delete_count >= 500:
                    delete_batch.commit()
                    print(f"Deleted {delete_count} old plans...")
                    delete_batch = db.batch()
                    delete_count = 0
            if delete_count > 0:
                delete_batch.commit()
                print(f"Deleted {delete_count} old plans")
            
            # 匯入新的讀經計畫
            plans_df = pd.read_csv('data/bible_plans.csv')
            print(f"Read {len(plans_df)} plan entries from CSV.")
            
            # 顯示前 3 天以確認順序
            print("First 3 days of Canonical plan:")
            canonical_plans = plans_df[plans_df['plan_type'] == 'Canonical'].head(3)
            for _, row in canonical_plans.iterrows():
                print(f"  Day {row['day_number']}: {row['readings']}")
            
            # 批次寫入 Firestore
            batch = db.batch()
            batch_count = 0
            
            for index, row in plans_df.iterrows():
                doc_ref = bible_plans_ref.document()
                batch.set(doc_ref, {
                    'plan_type': row['plan_type'],
                    'day_number': int(row['day_number']),
                    'readings': row['readings']
                })
                batch_count += 1
                
                if batch_count >= 500:
                    batch.commit()
                    print(f"Committed {batch_count} plan entries to Firestore.")
                    batch = db.batch()
                    batch_count = 0
            
            if batch_count > 0:
                batch.commit()
                print(f"Committed final {batch_count} plan entries to Firestore.")
            
            # 更新版本標記
            version_ref.set({'version': PLAN_VERSION, 'updated_at': firestore.SERVER_TIMESTAMP})
            
            print(f"✅ Successfully updated {len(plans_df)} plan entries to Firestore (version: {PLAN_VERSION})")
        except FileNotFoundError as e:
            print(f"Error: data/bible_plans.csv not found - {e}")
        except Exception as e:
            print(f"Error updating Bible plans: {e}")
    else:
        print(f"Reading plans are up to date (version: {PLAN_VERSION}), skipping update.")
    
    print("Firestore database initialization complete.")

