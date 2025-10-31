from database import BibleText, BiblePlan

# 測試查詢單章經文
print("=== 測試查詢創世記第1章 ===")
verses = BibleText.get_verses_by_reference("創", 1)
print(f"查詢結果數量: {len(verses)}")
if verses:
    print(f"第一節: {verses[0]}")
    print(f"最後一節: {verses[-1]}")
else:
    print("❌ 沒有查詢到任何經文")

print("\n=== 測試查詢章節範圍 (創1-3) ===")
verses_range = BibleText.get_verses_in_range("創", 1, 3)
print(f"查詢結果數量: {len(verses_range)}")
if verses_range:
    print(f"第一節: {verses_range[0]}")
    print(f"最後一節: {verses_range[-1]}")
else:
    print("❌ 沒有查詢到任何經文")

print("\n=== 測試查詢讀經計畫 ===")
plan = BiblePlan.get_by_day("Canonical", 1)
if plan:
    print(f"計畫類型: {plan['plan_type']}")
    print(f"天數: {plan['day_number']}")
    print(f"讀經範圍: {plan['readings']}")
else:
    print("❌ 沒有查詢到讀經計畫")
