#!/bin/bash
# 刪除不必要的 Cloud Scheduler 任務
# 保留早上 6:00 的推播，刪除其他 4 個

set -e

PROJECT_ID="bible-bot-project"
LOCATION="asia-east1"

echo "🗑️  開始刪除不必要的 Cloud Scheduler 任務..."
echo "📍 專案: $PROJECT_ID"
echo "📍 區域: $LOCATION"
echo ""

# 設定專案
gcloud config set project $PROJECT_ID

echo "📋 目前的 Scheduler 任務:"
gcloud scheduler jobs list --location=$LOCATION
echo ""

# 確認
read -p "⚠️  即將刪除 4 個任務（保留 bible-push-morning），是否繼續？ (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 1
fi

echo ""
echo "🗑️  開始刪除任務..."
echo ""

# 刪除中午 12:00 讀經推播
echo "1/4 刪除 bible-push-noon..."
if gcloud scheduler jobs delete bible-push-noon --location=$LOCATION --quiet 2>/dev/null; then
    echo "✅ bible-push-noon 已刪除"
else
    echo "⚠️  bible-push-noon 不存在或已刪除"
fi
echo ""

# 刪除中午 12:30 靈修推播
echo "2/4 刪除 daily-devotional-sender..."
if gcloud scheduler jobs delete daily-devotional-sender --location=$LOCATION --quiet 2>/dev/null; then
    echo "✅ daily-devotional-sender 已刪除"
else
    echo "⚠️  daily-devotional-sender 不存在或已刪除"
fi
echo ""

# 刪除傍晚 6:00 讀經推播
echo "3/4 刪除 bible-push-evening..."
if gcloud scheduler jobs delete bible-push-evening --location=$LOCATION --quiet 2>/dev/null; then
    echo "✅ bible-push-evening 已刪除"
else
    echo "⚠️  bible-push-evening 不存在或已刪除"
fi
echo ""

# 刪除晚上 11:00 讀經推播
echo "4/4 刪除 bible-push-night..."
if gcloud scheduler jobs delete bible-push-night --location=$LOCATION --quiet 2>/dev/null; then
    echo "✅ bible-push-night 已刪除"
else
    echo "⚠️  bible-push-night 不存在或已刪除"
fi
echo ""

echo "✅ 刪除完成！"
echo ""
echo "📋 剩餘的 Scheduler 任務:"
gcloud scheduler jobs list --location=$LOCATION
echo ""

echo "💰 預期成本節省:"
echo "   原本: 5 jobs × $0.04 = $0.20/月"
echo "   現在: 1 job × $0.04 = $0.04/月"
echo "   節省: $0.16/月（Cloud Scheduler）"
echo ""
echo "   原本: ~1,500 推播/月 × $0.003 = $4.50/月"
echo "   現在: ~300 推播/月 × $0.003 = $0.90/月"
echo "   節省: $3.60/月（LINE API）"
echo ""
echo "   總節省: $3.76/月（94% 降低）"
echo ""
echo "💡 提醒: 請確保 Rich Menu 已部署，讓用戶可以主動取得內容"
