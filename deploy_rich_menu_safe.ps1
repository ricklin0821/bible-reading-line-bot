# Rich Menu Deployment Script (Windows PowerShell - Encoding Safe Version)
# Usage: .\deploy_rich_menu_safe.ps1 -Token "YOUR_CHANNEL_ACCESS_TOKEN"

param(
    [Parameter(Mandatory=$true)]
    [string]$Token
)

$ErrorActionPreference = "Stop"

$RICH_MENU_IMAGE = "rich_menu.png"

# Check if image exists
if (-not (Test-Path $RICH_MENU_IMAGE)) {
    Write-Host "Error: Cannot find $RICH_MENU_IMAGE" -ForegroundColor Red
    exit 1
}

Write-Host "Starting Rich Menu deployment..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Create Rich Menu
Write-Host "Step 1: Creating Rich Menu..." -ForegroundColor Yellow

$richMenuJson = @{
    size = @{
        width = 2500
        height = 1686
    }
    selected = $true
    name = "Bible Reading Bot Menu"
    chatBarText = [char]0x1F4D6 + " Bible Reading Menu"
    areas = @(
        @{
            bounds = @{ x = 0; y = 0; width = 1250; height = 562 }
            action = @{ type = "message"; text = "Today's Reading" }
        },
        @{
            bounds = @{ x = 1250; y = 0; width = 1250; height = 562 }
            action = @{ type = "message"; text = "Devotional" }
        },
        @{
            bounds = @{ x = 0; y = 562; width = 1250; height = 562 }
            action = @{ type = "message"; text = "Report Reading" }
        },
        @{
            bounds = @{ x = 1250; y = 562; width = 1250; height = 562 }
            action = @{ type = "message"; text = "My Progress" }
        },
        @{
            bounds = @{ x = 0; y = 1124; width = 1250; height = 562 }
            action = @{ type = "message"; text = "Leaderboard" }
        },
        @{
            bounds = @{ x = 1250; y = 1124; width = 1250; height = 562 }
            action = @{ type = "message"; text = "Menu" }
        }
    )
} | ConvertTo-Json -Depth 10

try {
    $headers = @{
        "Authorization" = "Bearer $Token"
        "Content-Type" = "application/json; charset=utf-8"
    }
    
    $response = Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu" `
        -Method Post `
        -Headers $headers `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($richMenuJson))
    
    $richMenuId = $response.richMenuId
    Write-Host "Success: Rich Menu created: $richMenuId" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "Error: Failed to create Rich Menu" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Step 2: Upload image
Write-Host "Step 2: Uploading Rich Menu image..." -ForegroundColor Yellow

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
    
    Write-Host "Success: Image uploaded" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "Error: Failed to upload image" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Step 3: Set as default Rich Menu
Write-Host "Step 3: Setting as default Rich Menu..." -ForegroundColor Yellow

try {
    $headers = @{
        "Authorization" = "Bearer $Token"
    }
    
    $response = Invoke-RestMethod -Uri "https://api.line.me/v2/bot/user/all/richmenu/$richMenuId" `
        -Method Post `
        -Headers $headers
    
    Write-Host "Success: Set as default Rich Menu" -ForegroundColor Green
    Write-Host ""
    
} catch {
    Write-Host "Error: Failed to set default Rich Menu" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Complete
Write-Host "Rich Menu deployment completed!" -ForegroundColor Green
Write-Host ""
Write-Host "Deployment Info:" -ForegroundColor Cyan
Write-Host "   Rich Menu ID: $richMenuId"
Write-Host "   Image: $RICH_MENU_IMAGE"
Write-Host "   Status: Active and set as default"
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Open LINE Bot chat"
Write-Host "   2. Click keyboard icon at bottom left"
Write-Host "   3. You should see the Rich Menu"
Write-Host ""
Write-Host "IMPORTANT: Update main.py to handle these English trigger texts:" -ForegroundColor Red
Write-Host '   - "Today' + "'" + 's Reading" -> Send daily reading'
Write-Host '   - "Devotional" -> Send devotional content'
Write-Host '   - "Report Reading" -> Handle reading report'
Write-Host '   - "My Progress" -> Send user stats'
Write-Host '   - "Leaderboard" -> Send leaderboard link'
Write-Host '   - "Menu" -> Send menu options'
Write-Host ""
Write-Host "To view all Rich Menus:" -ForegroundColor Cyan
Write-Host '   $headers = @{"Authorization" = "Bearer ' + $Token + '"}'
Write-Host '   Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu/list" -Headers $headers'
Write-Host ""
Write-Host "To delete this Rich Menu:" -ForegroundColor Cyan
Write-Host '   $headers = @{"Authorization" = "Bearer ' + $Token + '"}'
Write-Host '   Invoke-RestMethod -Uri "https://api.line.me/v2/bot/richmenu/' + $richMenuId + '" -Method Delete -Headers $headers'
