#!/usr/bin/env python3
"""
獨立的 Firestore 資料匯入腳本

此腳本用於首次部署時手動匯入聖經經文和讀經計畫資料到 Firestore。
在本地執行此腳本，避免在 Cloud Run 中首次啟動時超時。

使用方法：
1. 確保已安裝 google-cloud-firestore 和 pandas
2. 設定 Google Cloud 認證（使用服務帳戶金鑰或 gcloud auth）
3. 執行: python3 import_data_to_firestore.py
"""

import pandas as pd
from google.cloud import firestore
import os

# 初始化 Firestore 客戶端
# 如果在本地執行，需要設定 GOOGLE_APPLICATION_CREDENTIALS 環境變數
# 或使用 gcloud auth application-default login
db = firestore.Client()

# 集合名稱
BIBLE_TEXT_COLLECTION = "bible_text"
BIBLE_PLANS_COLLECTION = "bible_plans"

def import_bible_text():
    """匯入聖經經文資料"""
    print("=" * 60)
    print("匯入聖經經文資料到 Firestore")
    print("=" * 60)
    
    bible_text_ref = db.collection(BIBLE_TEXT_COLLECTION)
    
    # 檢查是否已有資料
    existing_count = len(list(bible_text_ref.limit(1).stream()))
    
    if existing_count > 0:
        print(f"⚠️  Firestore 中已有聖經經文資料")
        response = input("是否要清除並重新匯入？(y/N): ")
        if response.lower() != 'y':
            print("跳過聖經經文匯入")
            return
        
        # 刪除現有資料
        print("正在刪除現有資料...")
        docs = bible_text_ref.stream()
        batch = db.batch()
        count = 0
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            if count >= 500:
                batch.commit()
                print(f"已刪除 {count} 筆資料...")
                batch = db.batch()
                count = 0
        if count > 0:
            batch.commit()
            print(f"已刪除 {count} 筆資料")
    
    # 讀取 CSV 資料
    print("\n讀取 data/bible_text.csv...")
    try:
        bible_df = pd.read_csv('data/bible_text.csv')
        total_verses = len(bible_df)
        print(f"✓ 讀取到 {total_verses} 節經文")
    except FileNotFoundError:
        print("❌ 錯誤: 找不到 data/bible_text.csv")
        return
    except Exception as e:
        print(f"❌ 讀取 CSV 時發生錯誤: {e}")
        return
    
    # 批次寫入 Firestore
    print(f"\n開始匯入 {total_verses} 節經文到 Firestore...")
    print("(這可能需要幾分鐘時間，請耐心等待...)")
    
    batch = db.batch()
    batch_count = 0
    total_imported = 0
    
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
        total_imported += 1
        
        if batch_count >= 500:
            batch.commit()
            print(f"  進度: {total_imported}/{total_verses} ({total_imported*100//total_verses}%)")
            batch = db.batch()
            batch_count = 0
    
    if batch_count > 0:
        batch.commit()
        print(f"  進度: {total_imported}/{total_verses} (100%)")
    
    print(f"✅ 成功匯入 {total_imported} 節經文到 Firestore")

def import_bible_plans():
    """匯入讀經計畫資料"""
    print("\n" + "=" * 60)
    print("匯入讀經計畫資料到 Firestore")
    print("=" * 60)
    
    bible_plans_ref = db.collection(BIBLE_PLANS_COLLECTION)
    
    # 檢查是否已有資料
    existing_count = len(list(bible_plans_ref.limit(1).stream()))
    
    if existing_count > 0:
        print(f"⚠️  Firestore 中已有讀經計畫資料")
        response = input("是否要清除並重新匯入？(y/N): ")
        if response.lower() != 'y':
            print("跳過讀經計畫匯入")
            return
        
        # 刪除現有資料
        print("正在刪除現有資料...")
        docs = bible_plans_ref.stream()
        batch = db.batch()
        count = 0
        for doc in docs:
            batch.delete(doc.reference)
            count += 1
            if count >= 500:
                batch.commit()
                print(f"已刪除 {count} 筆資料...")
                batch = db.batch()
                count = 0
        if count > 0:
            batch.commit()
            print(f"已刪除 {count} 筆資料")
    
    # 讀取 CSV 資料
    print("\n讀取 data/bible_plans.csv...")
    try:
        plans_df = pd.read_csv('data/bible_plans.csv')
        total_plans = len(plans_df)
        print(f"✓ 讀取到 {total_plans} 筆讀經計畫")
    except FileNotFoundError:
        print("❌ 錯誤: 找不到 data/bible_plans.csv")
        return
    except Exception as e:
        print(f"❌ 讀取 CSV 時發生錯誤: {e}")
        return
    
    # 批次寫入 Firestore
    print(f"\n開始匯入 {total_plans} 筆讀經計畫到 Firestore...")
    
    batch = db.batch()
    batch_count = 0
    total_imported = 0
    
    for index, row in plans_df.iterrows():
        doc_ref = bible_plans_ref.document()
        batch.set(doc_ref, {
            'plan_type': row['plan_type'],
            'day_number': int(row['day_number']),
            'readings': row['readings']
        })
        batch_count += 1
        total_imported += 1
        
        if batch_count >= 500:
            batch.commit()
            print(f"  進度: {total_imported}/{total_plans} ({total_imported*100//total_plans}%)")
            batch = db.batch()
            batch_count = 0
    
    if batch_count > 0:
        batch.commit()
        print(f"  進度: {total_imported}/{total_plans} (100%)")
    
    print(f"✅ 成功匯入 {total_imported} 筆讀經計畫到 Firestore")

def verify_data():
    """驗證匯入的資料"""
    print("\n" + "=" * 60)
    print("驗證 Firestore 資料")
    print("=" * 60)
    
    # 檢查聖經經文數量
    bible_text_ref = db.collection(BIBLE_TEXT_COLLECTION)
    # 注意：count() 在某些情況下可能不準確，這裡用 limit 來估算
    sample_docs = list(bible_text_ref.limit(10).stream())
    if sample_docs:
        print(f"✓ 聖經經文集合存在，樣本數據: {len(sample_docs)} 筆")
        # 顯示第一筆資料
        first_doc = sample_docs[0].to_dict()
        print(f"  範例: {first_doc.get('book_abbr')}{first_doc.get('chapter')}:{first_doc.get('verse')} - {first_doc.get('text')[:30]}...")
    else:
        print("❌ 聖經經文集合為空")
    
    # 檢查讀經計畫數量
    bible_plans_ref = db.collection(BIBLE_PLANS_COLLECTION)
    sample_plans = list(bible_plans_ref.limit(10).stream())
    if sample_plans:
        print(f"✓ 讀經計畫集合存在，樣本數據: {len(sample_plans)} 筆")
        # 顯示第一筆資料
        first_plan = sample_plans[0].to_dict()
        print(f"  範例: Day {first_plan.get('day_number')} ({first_plan.get('plan_type')}) - {first_plan.get('readings')}")
    else:
        print("❌ 讀經計畫集合為空")

def main():
    """主函數"""
    print("\n" + "=" * 60)
    print("Firestore 資料匯入工具")
    print("=" * 60)
    print()
    print("此工具將匯入以下資料到 Firestore:")
    print("  1. 聖經經文 (約 31,000+ 節)")
    print("  2. 讀經計畫 (兩種計畫，共 730 筆)")
    print()
    print("⚠️  注意: 匯入過程可能需要數分鐘，請確保網路連線穩定")
    print()
    
    response = input("是否繼續？(y/N): ")
    if response.lower() != 'y':
        print("已取消")
        return
    
    try:
        # 匯入聖經經文
        import_bible_text()
        
        # 匯入讀經計畫
        import_bible_plans()
        
        # 驗證資料
        verify_data()
        
        print("\n" + "=" * 60)
        print("✅ 資料匯入完成！")
        print("=" * 60)
        print("\n現在可以部署您的 LINE Bot 到 Cloud Run 了。")
        
    except Exception as e:
        print(f"\n❌ 匯入過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

