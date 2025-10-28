#!/usr/bin/env python3
"""
只匯入讀經計畫的簡化腳本
使用環境變數中的認證
"""

import pandas as pd
from google.cloud import firestore
import os

# 設定專案 ID
os.environ['GOOGLE_CLOUD_PROJECT'] = 'bible-bot-project'

try:
    # 初始化 Firestore 客戶端
    db = firestore.Client(project='bible-bot-project')
    
    print("=" * 60)
    print("匯入讀經計畫資料到 Firestore")
    print("=" * 60)
    
    bible_plans_ref = db.collection("bible_plans")
    
    # 刪除現有的讀經計畫資料
    print("\n正在刪除現有的讀經計畫資料...")
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
    plans_df = pd.read_csv('data/bible_plans.csv')
    total_plans = len(plans_df)
    print(f"✓ 讀取到 {total_plans} 筆讀經計畫")
    
    # 顯示前 5 筆以確認順序
    print("\n前 5 天的讀經計畫:")
    for i in range(min(5, len(plans_df))):
        row = plans_df.iloc[i]
        print(f"  Day {row['day_number']}: {row['readings']}")
    
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
    
    print(f"\n✅ 成功匯入 {total_imported} 筆讀經計畫到 Firestore")
    
    # 驗證資料
    print("\n驗證匯入的資料...")
    canonical_day1 = bible_plans_ref.where('plan_type', '==', 'Canonical').where('day_number', '==', 1).limit(1).stream()
    for doc in canonical_day1:
        data = doc.to_dict()
        print(f"✓ 按卷順序計畫 Day 1: {data.get('readings')}")
        if data.get('readings').startswith('創'):
            print("✅ 讀經計畫順序正確！（從創世記開始）")
        else:
            print("⚠️  讀經計畫順序可能有誤")
    
    print("\n" + "=" * 60)
    print("匯入完成！")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

