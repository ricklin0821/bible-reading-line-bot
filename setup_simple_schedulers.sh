#!/bin/bash
# 簡化版排程設定 - 只保留 2 個任務
# 1. 每天晚上 11 點提醒讀經
# 2. 每天中午 12:30 發送荒漠甘泉圖片

set -e

PROJECT_ID="bible-bot-project"
LOCATION="asia-east1"
SERVICE_URL="https://bible-bot-741437082833.asia-east1.run.app"
SERVICE_ACCOUNT="741437082833-compute@developer.gserviceaccount.com"

echo "🚀 設定簡化版 Cloud Scheduler 任務..."
echo "📍 專案: $PROJECT_ID"
echo "📍 區域: $LOCATION"
echo "📍 服務: $SERVICE_URL"
echo ""

# 設定專案
gcloud config set project $PROJECT_ID

echo "📋 目前的 Scheduler 任務:"
gcloud scheduler jobs list --location=$LOCATION || true
echo ""

# 確認
read -p "⚠️  即將刪除所有舊任務並創建 2 個新任務，是否繼續？ (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 1
fi

echo ""
echo "🗑️  刪除所有舊任務..."
echo ""

# 刪除所有可能存在的舊任務
for job in bible-push-morning bible-push-noon bible-push-evening bible-push-night daily-devotional-sender; do
    echo "檢查並刪除: $job"
    gcloud scheduler jobs delete $job --location=$LOCATION --quiet 2>/dev/null || echo "  ⚠️  $job 不存在或已刪除"
done

echo ""
echo "✅ 舊任務已清理"
echo ""

# ========================================
# 任務 1: 每天晚上 11 點提醒讀經
# ========================================
echo "📝 創建任務 1/2: 每天晚上 11 點提醒讀經..."

gcloud scheduler jobs create http bible-push-night \
  --location=$LOCATION \
  --schedule="0 23 * * *" \
  --time-zone="Asia/Taipei" \
  --uri="$SERVICE_URL/trigger/send-reading-plan" \
  --http-method=POST \
  --oidc-service-account-email=$SERVICE_ACCOUNT \
  --oidc-token-audience=$SERVICE_URL

echo "✅ 任務 1 已創建: bible-push-night (每天 23:00)"
echo ""

# ========================================
# 任務 2: 每天中午 12:30 發送荒漠甘泉圖片
# ========================================
echo "📝 創建任務 2/2: 每天中午 12:30 發送荒漠甘泉圖片..."

gcloud scheduler jobs create http daily-devotional-sender \
  --location=$LOCATION \
  --schedule="30 12 * * *" \
  --time-zone="Asia/Taipei" \
  --uri="$SERVICE_URL/trigger/send-devotional-image" \
  --http-method=POST \
  --oidc-service-account-email=$SERVICE_ACCOUNT \
  --oidc-token-audience=$SERVICE_URL

echo "✅ 任務 2 已創建: daily-devotional-sender (每天 12:30)"
echo ""

echo "🎉 所有任務已創建完成！"
echo ""
echo "📋 最終的 Scheduler 任務列表:"
gcloud scheduler jobs list --location=$LOCATION
echo ""

echo "💰 預期成本:"
echo "   Cloud Scheduler: 2 jobs × \$0.04 = \$0.08/月"
echo "   LINE Push API: ~10用戶 × 2次/天 × 30天 = 600次/月"
echo "   LINE Push API 費用: (600 - 200免費) × \$0.003 = \$1.20/月"
echo "   總計: ~\$1.28/月"
echo ""
echo "💡 提醒:"
echo "   1. 請在 LINE 官方後台自行設定 Rich Menu"
echo "   2. 晚上 11 點會發送讀經提醒"
echo "   3. 中午 12:30 會發送荒漠甘泉圖片"
echo "   4. 用戶可以隨時透過 Rich Menu 主動查詢"
