# 簡化版排程設定 (PowerShell 版本)
# 只保留 2 個任務：
# 1. 每天晚上 11 點提醒讀經
# 2. 每天中午 12:30 發送荒漠甘泉圖片

$ErrorActionPreference = "Stop"

$PROJECT_ID = "bible-bot-project"
$LOCATION = "asia-east1"
$SERVICE_URL = "https://bible-bot-741437082833.asia-east1.run.app"
$SERVICE_ACCOUNT = "741437082833-compute@developer.gserviceaccount.com"

Write-Host "🚀 設定簡化版 Cloud Scheduler 任務..." -ForegroundColor Cyan
Write-Host "📍 專案: $PROJECT_ID" -ForegroundColor Gray
Write-Host "📍 區域: $LOCATION" -ForegroundColor Gray
Write-Host "📍 服務: $SERVICE_URL" -ForegroundColor Gray
Write-Host ""

# 檢查 gcloud 是否安裝
try {
    $null = Get-Command gcloud -ErrorAction Stop
} catch {
    Write-Host "❌ 錯誤: 找不到 gcloud 命令" -ForegroundColor Red
    Write-Host "請先安裝 Google Cloud SDK: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# 設定專案
Write-Host "🔧 設定專案..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

Write-Host ""
Write-Host "📋 目前的 Scheduler 任務:" -ForegroundColor Cyan
gcloud scheduler jobs list --location=$LOCATION 2>$null
Write-Host ""

# 確認
$confirmation = Read-Host "⚠️  即將刪除所有舊任務並創建 2 個新任務，是否繼續？ (y/N)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "❌ 已取消" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "🗑️  刪除所有舊任務..." -ForegroundColor Cyan
Write-Host ""

# 刪除所有可能存在的舊任務
$oldJobs = @("bible-push-morning", "bible-push-noon", "bible-push-evening", "bible-push-night", "daily-devotional-sender")

foreach ($job in $oldJobs) {
    Write-Host "檢查並刪除: $job" -ForegroundColor Yellow
    try {
        gcloud scheduler jobs delete $job --location=$LOCATION --quiet 2>$null
        Write-Host "  ✅ $job 已刪除" -ForegroundColor Green
    } catch {
        Write-Host "  ⚠️  $job 不存在或已刪除" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✅ 舊任務已清理" -ForegroundColor Green
Write-Host ""

# ========================================
# 任務 1: 每天晚上 11 點提醒讀經
# ========================================
Write-Host "📝 創建任務 1/2: 每天晚上 11 點提醒讀經..." -ForegroundColor Yellow

gcloud scheduler jobs create http bible-push-night `
  --location=$LOCATION `
  --schedule="0 23 * * *" `
  --time-zone="Asia/Taipei" `
  --uri="$SERVICE_URL/trigger/send-reading-plan" `
  --http-method=POST `
  --oidc-service-account-email=$SERVICE_ACCOUNT `
  --oidc-token-audience=$SERVICE_URL

Write-Host "✅ 任務 1 已創建: bible-push-night (每天 23:00)" -ForegroundColor Green
Write-Host ""

# ========================================
# 任務 2: 每天中午 12:30 發送荒漠甘泉圖片
# ========================================
Write-Host "📝 創建任務 2/2: 每天中午 12:30 發送荒漠甘泉圖片..." -ForegroundColor Yellow

gcloud scheduler jobs create http daily-devotional-sender `
  --location=$LOCATION `
  --schedule="30 12 * * *" `
  --time-zone="Asia/Taipei" `
  --uri="$SERVICE_URL/trigger/send-devotional-image" `
  --http-method=POST `
  --oidc-service-account-email=$SERVICE_ACCOUNT `
  --oidc-token-audience=$SERVICE_URL

Write-Host "✅ 任務 2 已創建: daily-devotional-sender (每天 12:30)" -ForegroundColor Green
Write-Host ""

Write-Host "🎉 所有任務已創建完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 最終的 Scheduler 任務列表:" -ForegroundColor Cyan
gcloud scheduler jobs list --location=$LOCATION
Write-Host ""

Write-Host "💰 預期成本:" -ForegroundColor Green
Write-Host "   Cloud Scheduler: 2 jobs × `$0.04 = `$0.08/月"
Write-Host "   LINE Push API: ~10用戶 × 2次/天 × 30天 = 600次/月"
Write-Host "   LINE Push API 費用: (600 - 200免費) × `$0.003 = `$1.20/月"
Write-Host "   總計: ~`$1.28/月"
Write-Host ""
Write-Host "💡 提醒:" -ForegroundColor Yellow
Write-Host "   1. 請在 LINE 官方後台自行設定 Rich Menu"
Write-Host "   2. 晚上 11 點會發送讀經提醒"
Write-Host "   3. 中午 12:30 會發送荒漠甘泉圖片"
Write-Host "   4. 用戶可以隨時透過 Rich Menu 主動查詢"
