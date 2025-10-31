#!/bin/bash
# 重置使用者測驗狀態的簡易腳本

echo "=========================================="
echo "聖經讀經 Bot - 使用者狀態重置工具"
echo "=========================================="
echo ""

# 檢查是否提供了 LINE User ID
if [ -z "$1" ]; then
    echo "❌ 錯誤：請提供 LINE User ID"
    echo ""
    echo "使用方式："
    echo "  ./reset_user.sh <LINE_USER_ID>"
    echo ""
    echo "範例："
    echo "  ./reset_user.sh U67da4c26e3706928c2eb77c1fc89b3a9"
    echo ""
    exit 1
fi

LINE_USER_ID=$1

# 取得 Cloud Run URL
echo "正在取得 Cloud Run 服務 URL..."
CLOUD_RUN_URL=$(gcloud run services describe bible-bot --region asia-east1 --format='value(status.url)' 2>/dev/null)

if [ -z "$CLOUD_RUN_URL" ]; then
    echo "❌ 錯誤：無法取得 Cloud Run URL"
    echo "請確認："
    echo "  1. 已安裝並設定 gcloud CLI"
    echo "  2. 已部署 bible-bot 服務到 asia-east1 區域"
    echo "  3. 已登入正確的 Google Cloud 專案"
    exit 1
fi

echo "✅ Cloud Run URL: $CLOUD_RUN_URL"
echo ""

# 詢問要執行的操作
echo "請選擇要執行的操作："
echo "  1) 重置測驗狀態（保留讀經進度）"
echo "  2) 重置讀經進度（回到第 1 天，並清除測驗狀態）"
echo ""
read -p "請輸入選項 (1 或 2): " choice

case $choice in
    1)
        echo ""
        echo "正在重置測驗狀態..."
        RESPONSE=$(curl -s -X POST "${CLOUD_RUN_URL}/admin/users/${LINE_USER_ID}/reset-quiz" \
            -u admin:bible2025 \
            -H "Content-Type: application/json")
        
        if echo "$RESPONSE" | grep -q "success"; then
            echo "✅ 測驗狀態已成功重置！"
            echo ""
            echo "回應內容："
            echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
        else
            echo "❌ 重置失敗"
            echo "回應內容："
            echo "$RESPONSE"
        fi
        ;;
    2)
        echo ""
        echo "正在重置讀經進度..."
        RESPONSE=$(curl -s -X POST "${CLOUD_RUN_URL}/admin/users/${LINE_USER_ID}/reset-progress" \
            -u admin:bible2025 \
            -H "Content-Type: application/json")
        
        if echo "$RESPONSE" | grep -q "success"; then
            echo "✅ 讀經進度已成功重置！"
            echo ""
            echo "回應內容："
            echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
        else
            echo "❌ 重置失敗"
            echo "回應內容："
            echo "$RESPONSE"
        fi
        ;;
    *)
        echo "❌ 無效的選項"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "完成！"
echo "=========================================="
