
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
            for i in range(min(3, len(plans_df))):
                row = plans_df[plans_df['plan_type'] == 'Canonical'].iloc[i]
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

