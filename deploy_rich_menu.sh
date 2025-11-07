#!/bin/bash
# Rich Menu 部署腳本
# 使用方式: ./deploy_rich_menu.sh YOUR_CHANNEL_ACCESS_TOKEN

set -e

if [ -z "$1" ]; then
    echo "❌ 錯誤: 請提供 LINE Channel Access Token"
    echo "使用方式: ./deploy_rich_menu.sh YOUR_CHANNEL_ACCESS_TOKEN"
    exit 1
fi

CHANNEL_ACCESS_TOKEN="$1"
RICH_MENU_IMAGE="rich_menu.png"

if [ ! -f "$RICH_MENU_IMAGE" ]; then
    echo "❌ 錯誤: 找不到 $RICH_MENU_IMAGE"
    exit 1
fi

echo "🚀 開始部署 Rich Menu..."
echo ""

# 步驟 1: 創建 Rich Menu
echo "📝 步驟 1: 創建 Rich Menu..."
RESPONSE=$(curl -s -X POST https://api.line.me/v2/bot/richmenu \
-H "Authorization: Bearer $CHANNEL_ACCESS_TOKEN" \
-H "Content-Type: application/json" \
-d '{
  "size": {
    "width": 2500,
    "height": 1686
  },
  "selected": true,
  "name": "Bible Reading Bot Menu",
  "chatBarText": "📖 聖經讀經選單",
  "areas": [
    {
      "bounds": {
        "x": 0,
        "y": 0,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "今日讀經"
      }
    },
    {
      "bounds": {
        "x": 1250,
        "y": 0,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "荒漠甘泉"
      }
    },
    {
      "bounds": {
        "x": 0,
        "y": 562,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "回報讀經"
      }
    },
    {
      "bounds": {
        "x": 1250,
        "y": 562,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "我的進度"
      }
    },
    {
      "bounds": {
        "x": 0,
        "y": 1124,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "排行榜"
      }
    },
    {
      "bounds": {
        "x": 1250,
        "y": 1124,
        "width": 1250,
        "height": 562
      },
      "action": {
        "type": "message",
        "text": "選單"
      }
    }
  ]
}')

# 檢查是否有錯誤
if echo "$RESPONSE" | grep -q "error"; then
    echo "❌ 創建 Rich Menu 失敗:"
    echo "$RESPONSE" | python3 -m json.tool
    exit 1
fi

RICH_MENU_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['richMenuId'])")
echo "✅ Rich Menu 已創建: $RICH_MENU_ID"
echo ""

# 步驟 2: 上傳圖片
echo "📤 步驟 2: 上傳 Rich Menu 圖片..."
UPLOAD_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
"https://api-data.line.me/v2/bot/richmenu/$RICH_MENU_ID/content" \
-H "Authorization: Bearer $CHANNEL_ACCESS_TOKEN" \
-H "Content-Type: image/png" \
--data-binary "@$RICH_MENU_IMAGE")

HTTP_CODE=$(echo "$UPLOAD_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ 上傳圖片失敗 (HTTP $HTTP_CODE)"
    echo "$UPLOAD_RESPONSE"
    exit 1
fi

echo "✅ 圖片上傳成功"
echo ""

# 步驟 3: 設定為預設 Rich Menu
echo "🔧 步驟 3: 設定為預設 Rich Menu..."
DEFAULT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
"https://api.line.me/v2/bot/user/all/richmenu/$RICH_MENU_ID" \
-H "Authorization: Bearer $CHANNEL_ACCESS_TOKEN")

HTTP_CODE=$(echo "$DEFAULT_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" != "200" ]; then
    echo "❌ 設定預設 Rich Menu 失敗 (HTTP $HTTP_CODE)"
    echo "$DEFAULT_RESPONSE"
    exit 1
fi

echo "✅ 已設定為預設 Rich Menu"
echo ""

# 完成
echo "🎉 Rich Menu 部署完成！"
echo ""
echo "📋 部署資訊:"
echo "   Rich Menu ID: $RICH_MENU_ID"
echo "   圖片: $RICH_MENU_IMAGE"
echo "   狀態: 已啟用並設為預設"
echo ""
echo "💡 下一步:"
echo "   1. 開啟 LINE Bot 聊天室"
echo "   2. 點擊左下角鍵盤圖示"
echo "   3. 應該會看到 Rich Menu"
echo ""
echo "🔍 如需查看所有 Rich Menu:"
echo "   curl -X GET https://api.line.me/v2/bot/richmenu/list \\"
echo "     -H \"Authorization: Bearer $CHANNEL_ACCESS_TOKEN\""
echo ""
echo "🗑️  如需刪除此 Rich Menu:"
echo "   curl -X DELETE https://api.line.me/v2/bot/richmenu/$RICH_MENU_ID \\"
echo "     -H \"Authorization: Bearer $CHANNEL_ACCESS_TOKEN\""
