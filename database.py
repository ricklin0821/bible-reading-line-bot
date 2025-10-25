import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Date, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date

# SQLite 資料庫檔案路徑
SQLALCHEMY_DATABASE_URL = "sqlite:///./bible_plan.db"

# 創建 SQLAlchemy 引擎
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- ORM 模型定義 ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    line_user_id = Column(String, unique=True, index=True, nullable=False)
    plan_type = Column(String, default=None)  # 'Canonical' 或 'Balanced'
    start_date = Column(Date, default=date.today)
    current_day = Column(Integer, default=1)
    last_read_date = Column(Date, default=None)
    quiz_state = Column(String, default="IDLE") # IDLE, WAITING_ANSWER, QUIZ_COMPLETED
    quiz_data = Column(Text, default="{}") # 儲存當前測驗的 JSON 數據

class BiblePlan(Base):
    __tablename__ = "bible_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_type = Column(String, nullable=False)
    day_number = Column(Integer, nullable=False)
    readings = Column(String, nullable=False)

class BibleText(Base):
    __tablename__ = "bible_text"

    id = Column(Integer, primary_key=True, index=True)
    book_abbr = Column(String, nullable=False) # 書卷縮寫 (例如: 創)
    book = Column(String, nullable=False)      # 書卷全名 (例如: 創世記)
    chapter = Column(Integer, nullable=False)
    verse = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

# --- 資料庫初始化與資料匯入 ---

def init_db():
    # 創建所有表格
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    # 檢查是否已匯入資料
    if db.query(BibleText).count() == 0:
        print("Importing Bible text data...")
        try:
            # 讀取 CSV 檔案
            bible_df = pd.read_csv('data/bible_text.csv')
            # 將 DataFrame 寫入資料庫
            bible_df.to_sql(BibleText.__tablename__, engine, if_exists='append', index=False)
            print(f"Successfully imported {len(bible_df)} verses.")
        except FileNotFoundError:
            print("Error: data/bible_text.csv not found. Please run prepare_data.py first.")
        except Exception as e:
            print(f"Error importing Bible text: {e}")

    if db.query(BiblePlan).count() == 0:
        print("Importing Bible plans data...")
        try:
            # 讀取 CSV 檔案
            plans_df = pd.read_csv('data/bible_plans.csv')
            # 將 DataFrame 寫入資料庫
            plans_df.to_sql(BiblePlan.__tablename__, engine, if_exists='append', index=False)
            print(f"Successfully imported {len(plans_df)} plan entries.")
        except FileNotFoundError:
            print("Error: data/bible_plans.csv not found. Please run prepare_data.py first.")
        except Exception as e:
            print(f"Error importing Bible plans: {e}")
            
    db.close()

# 依賴項函數
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
