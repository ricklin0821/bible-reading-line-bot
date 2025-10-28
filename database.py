import pandas as pd
from google.cloud import firestore
from datetime import date, datetime
import os

# 初始化 Firestore 客戶端
db = firestore.Client()

# --- Firestore 集合名稱 ---
USERS_COLLECTION = "users"
BIBLE_PLANS_COLLECTION = "bible_plans"
BIBLE_TEXT_COLLECTION = "bible_text"

# --- 輔助函數 ---

def date_to_firestore(d):
    """將 Python date 轉換為 Firestore Timestamp"""
    if d is None:
        return None
    if isinstance(d, datetime):
        return d
    if isinstance(d, date):
        # 將 date 轉換為 datetime（設定時間為 00:00:00）
        return datetime.combine(d, datetime.min.time())
    return d

def firestore_to_date(timestamp):
    """將 Firestore Timestamp 轉換為 Python date"""
    if timestamp is None:
        return None
    if isinstance(timestamp, date):
        return timestamp
    if hasattr(timestamp, 'date'):
        return timestamp.date()
    return timestamp

def user_doc_to_dict(doc):
    """將 Firestore 使用者文檔轉換為字典"""
    if not doc.exists:
        return None
    data = doc.to_dict()
    data['id'] = doc.id
    # 將 Firestore 的 Timestamp 轉換為 Python date
    data['start_date'] = firestore_to_date(data.get('start_date'))
    data['last_read_date'] = firestore_to_date(data.get('last_read_date'))
    return data

# --- 使用者操作 ---

class User:
    """使用者類別，模擬 ORM 模型"""
    def __init__(self, line_user_id, plan_type=None, start_date=None, current_day=1, 
                 last_read_date=None, quiz_state="IDLE", quiz_data="{}", display_name=None):
        self.line_user_id = line_user_id
        self.plan_type = plan_type
        self.start_date = start_date
        self.current_day = current_day
        self.last_read_date = last_read_date
        self.quiz_state = quiz_state
        self.quiz_data = quiz_data
        self.display_name = display_name
    
    @staticmethod
    def get_by_line_user_id(line_user_id):
        """根據 LINE 使用者 ID 獲取使用者"""
        users_ref = db.collection(USERS_COLLECTION)
        query = users_ref.where('line_user_id', '==', line_user_id).limit(1)
        docs = query.stream()
        
        for doc in docs:
            data = user_doc_to_dict(doc)
            user = User(
                line_user_id=data['line_user_id'],
                plan_type=data.get('plan_type'),
                start_date=data.get('start_date'),
                current_day=data.get('current_day', 1),
                last_read_date=data.get('last_read_date'),
                quiz_state=data.get('quiz_state', 'IDLE'),
                quiz_data=data.get('quiz_data', '{}'),
                display_name=data.get('display_name')
            )
            user._doc_id = doc.id
            return user
        return None
    
    def save(self):
        """儲存或更新使用者到 Firestore"""
        users_ref = db.collection(USERS_COLLECTION)
        
        user_data = {
            'line_user_id': self.line_user_id,
            'plan_type': self.plan_type,
            'start_date': date_to_firestore(self.start_date),
            'current_day': self.current_day,
            'last_read_date': date_to_firestore(self.last_read_date),
            'quiz_state': self.quiz_state,
            'quiz_data': self.quiz_data,
            'display_name': self.display_name
        }
        
        if hasattr(self, '_doc_id'):
            # 更新現有文檔
            users_ref.document(self._doc_id).set(user_data)
        else:
            # 創建新文檔
            doc_ref = users_ref.add(user_data)
            self._doc_id = doc_ref[1].id

# --- 讀經計畫操作 ---

class BiblePlan:
    """讀經計畫類別"""
    @staticmethod
    def get_by_plan_and_day(plan_type, day_number):
        """根據計畫類型和天數獲取讀經計畫"""
        plans_ref = db.collection(BIBLE_PLANS_COLLECTION)
        query = plans_ref.where('plan_type', '==', plan_type).where('day_number', '==', day_number).limit(1)
        docs = query.stream()
        
        for doc in docs:
            data = doc.to_dict()
            return data.get('readings')
        return None

# --- 聖經經文操作 ---

class BibleText:
    """聖經經文類別"""
    @staticmethod
    def get_verses_by_reference(book_abbr, chapter):
        """根據書卷縮寫和章節獲取經文"""
        texts_ref = db.collection(BIBLE_TEXT_COLLECTION)
        query = texts_ref.where('book_abbr', '==', book_abbr).where('chapter', '==', chapter)
        docs = query.stream()
        
        verses = []
        for doc in docs:
            data = doc.to_dict()
            verses.append(data)
        
        # 按節數排序
        verses.sort(key=lambda x: x.get('verse', 0))
        return verses
    
    @staticmethod
    def get_verse(book_abbr, chapter, verse):
        """根據書卷、章節、節數獲取單節經文"""
        texts_ref = db.collection(BIBLE_TEXT_COLLECTION)
        query = texts_ref.where('book_abbr', '==', book_abbr).where('chapter', '==', chapter).where('verse', '==', verse).limit(1)
        docs = query.stream()
        
        for doc in docs:
            return doc.to_dict()
        return None
    
    @staticmethod
    def get_verses_in_range(book_abbr, start_chapter, end_chapter, start_verse=None, end_verse=None):
        """獲取範圍內的經文"""
        texts_ref = db.collection(BIBLE_TEXT_COLLECTION)
        query = texts_ref.where('book_abbr', '==', book_abbr)
        
        # 獲取所有符合条件的經文
        docs = query.stream()
        verses = []
        
        for doc in docs:
            data = doc.to_dict()
            chapter = data.get('chapter')
            verse = data.get('verse')
            
            # 範圍篩選
            if chapter < start_chapter or chapter > end_chapter:
                continue
            
            if start_verse and chapter == start_chapter and verse < start_verse:
                continue
            
            if end_verse and chapter == end_chapter and verse > end_verse:
                continue
            
            verses.append(data)
        
        # 按章節和節數排序
        verses.sort(key=lambda x: (x.get('chapter', 0), x.get('verse', 0)))
        return verses

# --- 資料庫初始化與資料匯入 ---

def init_db():
    """初始化 Firestore 並匯入資料"""
    print("Initializing Firestore database...")
    
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
    
    # 檢查是否已匯入讀經計畫資料
    bible_plans_ref = db.collection(BIBLE_PLANS_COLLECTION)
    bible_plans_count = len(list(bible_plans_ref.limit(1).stream()))
    
    print(f"Current BiblePlan count: {bible_plans_count}")
    
    if bible_plans_count == 0:
        print("Importing Bible plans data to Firestore...")
        try:
            plans_df = pd.read_csv('data/bible_plans.csv')
            print(f"Read {len(plans_df)} plan entries from CSV.")
            
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
            
            print(f"Successfully imported {len(plans_df)} plan entries to Firestore.")
        except FileNotFoundError as e:
            print(f"Error: data/bible_plans.csv not found - {e}")
        except Exception as e:
            print(f"Error importing Bible plans: {e}")
    else:
        print("Bible plans data already exists in Firestore, skipping import.")
    
    print("Firestore database initialization complete.")

# 依賴項函數（保持與原有接口一致）
def get_db():
    """返回 Firestore 客戶端（用於保持接口一致性）"""
    yield db

if __name__ == "__main__":
    init_db()

