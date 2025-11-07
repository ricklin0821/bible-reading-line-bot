# Rich Menu 部署腳本 (Windows PowerShell 版本)
# 使用方式: .\deploy_rich_menu.ps1 -Token "YOUR_CHANNEL_ACCESS_TOKEN"

param(
    [Parameter(Mandatory=$true)]
    [string]$Token
)

$ErrorActionPreference = "Stop"

$RICH_MENU_IMAGE = "rich_menu.png"

# 檢查圖片是否存在
if (-not (Test-Path $RICH_MENU_IMAGE)) {
    Write-Host "❌ 錯誤: 找不到 $RICH_MENU_IMAGE" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 開始部署 Rich Menu..." -ForegroundColor Cyan
Write-Host ""

# 步驟 1: 創建 Rich Menu
Write-Host "📝 步驟 1: 創建 Rich Menu..." -ForegroundColor Yellow

$richMenuJson = @{
    size = @{
        width = 2500
        height = 1686
    }
    selected = $true
    name = "Bible Reading Bot Menu"
    chatBarText = "📖 聖經讀經選單"
    areas = @(
        @{
            bounds = @{ x = 0; y = 0; width = 1250; height = 562 }
            action = @{ type = "message"; text = "今日讀經" }
        },
        @{
            bounds = @{ x = 1250; y = 0; width = 1250; height = 562 }
            action = @{ type = "message"; text = "荒漠甘泉" }
        },
        @{
            bounds = @{ x = 0; y = 562; width = 1250; height = 562 }
            action = @{ type = "message"; text = "回報讀經" }
        },
        @{
            bounds = @{ x = 1250; y = 562; width = 1250; height = 562 }
            action = @{ type = "message"; text = "我的進度" }
        },
        @{
            bounds = @{ x = 0; y = 1124; width = 1250; height = 562 }
            action = @{ type = "message"; text = "排行榜" }
        },
        @{
            bounds = @{ x = 1250; y = 1124; width = 1250; height = 562 }
            action = @{ type = "message"; text = "選單" }
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Content-Type" = "application/json"
    }
    
    $response = Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu" `
        -Method Post `
        -Headers $headers `
        -Body $richMenuJson
    
    $richMenuId = $response.richMenuId
    Write-Host "✅ Rich Menu 已創建: $richMenuId" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "❌ 創建 Rich Menu 失敗:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# 步驟 2: 上傳圖片
Write-Host "📤 步驟 2: 上傳 Rich Menu 圖片..." -ForegroundColor Yellow

try {
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Content-Type" = "image/png"
    }
    
    $imageBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $RICH_MENU_IMAGE))
    
    $response = Invoke-RestMethod -Uri "https://api-data.line.me/v2/bot/richmenu/$richMenuId/content" `
        -Method Post `
        -Headers $headers `
        -Body $imageBytes
    
    Write-Host "✅ 圖片上傳成功" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "❌ 上傳圖片失敗:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# 步驟 3: 設定為預設 Rich Menu
Write-Host "🔧 步驟 3: 設定為預設 Rich Menu..." -ForegroundColor Yellow

try {
    $headers = @{
        "Authorization" = "Bearer $Token"
    }
    
    $response = Invoke-RestMethod -Uri "https://api.line.me/v2/bot/user/all/richmenu/$richMenuId" `
        -Method Post `
        -Headers $headers
    
    Write-Host "✅ 已設定為預設 Rich Menu" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "❌ 設定預設 Rich Menu 失敗:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# 完成
Write-Host "🎉 Rich Menu 部署完成！" -ForegroundColor Green
Write-Host ""
Write-Host "📋 部署資訊:" -ForegroundColor Cyan
Write-Host "   Rich Menu ID: $richMenuId"
Write-Host "   圖片: $RICH_MENU_IMAGE"
Write-Host "   狀態: 已啟用並設為預設"
Write-Host ""
Write-Host "💡 下一步:" -ForegroundColor Yellow
Write-Host "   1. 開啟 LINE Bot 聊天室"
Write-Host "   2. 點擊左下角鍵盤圖示"
Write-Host "   3. 應該會看到 Rich Menu"
Write-Host ""
Write-Host "🔍 如需查看所有 Rich Menu:" -ForegroundColor Cyan
Write-Host '   $headers = @{"Authorization" = "Bearer ' + $Token + '"}'
Write-Host '   Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu/list" -Headers $headers'
Write-Host ""
Write-Host "🗑️  如需刪除此 Rich Menu:" -ForegroundColor Cyan
Write-Host '   $headers = @{"Authorization" = "Bearer ' + $Token + '"}'
Write-Host '   Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu/' + $richMenuId + '" -Method Delete -Headers $headers'
