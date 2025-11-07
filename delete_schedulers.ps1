# 刪除不必要的 Cloud Scheduler 任務 (Windows PowerShell 版本)
# 保留早上 6:00 的推播，刪除其他 4 個
# 使用方式: .\delete_schedulers.ps1

$ErrorActionPreference = "Stop"

$PROJECT_ID = "bible-bot-project"
$LOCATION = "asia-east1"

Write-Host "🗑️  開始刪除不必要的 Cloud Scheduler 任務..." -ForegroundColor Cyan
Write-Host "📍 專案: $PROJECT_ID" -ForegroundColor Gray
Write-Host "📍 區域: $LOCATION" -ForegroundColor Gray
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
gcloud scheduler jobs list --location=$LOCATION
Write-Host ""

# 確認
$confirmation = Read-Host "⚠️  即將刪除 4 個任務（保留 bible-push-morning），是否繼續？ (y/N)"
if ($confirmation -ne 'y' -and $confirmation -ne 'Y') {
    Write-Host "❌ 已取消" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "🗑️  開始刪除任務..." -ForegroundColor Cyan
Write-Host ""

# 刪除中午 12:00 讀經推播
Write-Host "1/4 刪除 bible-push-noon..." -ForegroundColor Yellow
try {
    gcloud scheduler jobs delete bible-push-noon --location=$LOCATION --quiet 2>$null
    Write-Host "✅ bible-push-noon 已刪除" -ForegroundColor Green
} catch {
    Write-Host "⚠️  bible-push-noon 不存在或已刪除" -ForegroundColor Yellow
}
Write-Host ""

# 刪除中午 12:30 靈修推播
Write-Host "2/4 刪除 daily-devotional-sender..." -ForegroundColor Yellow
try {
    gcloud scheduler jobs delete daily-devotional-sender --location=$LOCATION --quiet 2>$null
    Write-Host "✅ daily-devotional-sender 已刪除" -ForegroundColor Green
} catch {
    Write-Host "⚠️  daily-devotional-sender 不存在或已刪除" -ForegroundColor Yellow
}
Write-Host ""

# 刪除傍晚 6:00 讀經推播
Write-Host "3/4 刪除 bible-push-evening..." -ForegroundColor Yellow
try {
    gcloud scheduler jobs delete bible-push-evening --location=$LOCATION --quiet 2>$null
    Write-Host "✅ bible-push-evening 已刪除" -ForegroundColor Green
} catch {
    Write-Host "⚠️  bible-push-evening 不存在或已刪除" -ForegroundColor Yellow
}
Write-Host ""

# 刪除晚上 11:00 讀經推播
Write-Host "4/4 刪除 bible-push-night..." -ForegroundColor Yellow
try {
    gcloud scheduler jobs delete bible-push-night --location=$LOCATION --quiet 2>$null
    Write-Host "✅ bible-push-night 已刪除" -ForegroundColor Green
} catch {
    Write-Host "⚠️  bible-push-night 不存在或已刪除" -ForegroundColor Yellow
}
Write-Host ""

Write-Host "✅ 刪除完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 剩餘的 Scheduler 任務:" -ForegroundColor Cyan
gcloud scheduler jobs list --location=$LOCATION
Write-Host ""

Write-Host "💰 預期成本節省:" -ForegroundColor Green
Write-Host "   原本: 5 jobs × `$0.04 = `$0.20/月"
Write-Host "   現在: 1 job × `$0.04 = `$0.04/月"
Write-Host "   節省: `$0.16/月（Cloud Scheduler）"
Write-Host ""
Write-Host "   原本: ~1,500 推播/月 × `$0.003 = `$4.50/月"
Write-Host "   現在: ~300 推播/月 × `$0.003 = `$0.90/月"
Write-Host "   節省: `$3.60/月（LINE API）"
Write-Host ""
Write-Host "   總節省: `$3.76/月（94% 降低）"
Write-Host ""
Write-Host "💡 提醒: 請確保 Rich Menu 已部署，讓用戶可以主動取得內容" -ForegroundColor Yellow
