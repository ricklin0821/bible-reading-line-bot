"""
測試 Firestore 連接
"""
print("Step 1: Starting script...")

try:
    print("Step 2: Importing datetime...")
    from datetime import datetime
    print("  ✓ datetime imported")
except Exception as e:
    print(f"  ✗ Failed to import datetime: {e}")
    exit(1)

try:
    print("Step 3: Importing database...")
    from database import db, USERS_COLLECTION
    print(f"  ✓ database imported")
    print(f"  Collection name: {USERS_COLLECTION}")
except Exception as e:
    print(f"  ✗ Failed to import database: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

try:
    print("Step 4: Querying Firestore...")
    users_ref = db.collection(USERS_COLLECTION)
    docs = list(users_ref.stream())
    print(f"  ✓ Found {len(docs)} users")
    
    if len(docs) > 0:
        print("\nFirst user:")
        first_user = docs[0].to_dict()
        print(f"  ID: {docs[0].id}")
        print(f"  Fields: {', '.join(first_user.keys())}")
        print(f"  Display name: {first_user.get('display_name', 'N/A')}")
    
except Exception as e:
    print(f"  ✗ Failed to query Firestore: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✓ All tests passed!")
