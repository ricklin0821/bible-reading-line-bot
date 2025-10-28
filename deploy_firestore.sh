#!/bin/bash

# ============================================
# Bible Reading LINE Bot - Firestore 版本部署腳本
# ============================================

set -e  # 遇到錯誤立即停止

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 輔助函數
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================
# 步驟 1: 檢查必要工具
# ============================================
print_info "檢查必要工具..."

if ! command -v gcloud &> /dev/null; then
    print_error "未安裝 gcloud CLI。請先安裝: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

if ! command -v git &> /dev/null; then
    print_error "未安裝 git。請先安裝 git。"
    exit 1
fi

print_success "必要工具檢查完成"

# ============================================
# 步驟 2: 取得專案資訊
# ============================================
print_info "取得 Google Cloud 專案資訊..."

# 嘗試從 gcloud 取得當前專案 ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

if [ -z "$PROJECT_ID" ]; then
    print_warning "未設定 Google Cloud 專案"
    read -p "請輸入您的 Google Cloud 專案 ID: " PROJECT_ID
    gcloud config set project "$PROJECT_ID"
fi

print_success "專案 ID: $PROJECT_ID"

# ============================================
# 步驟 3: 檢查環境變數
# ============================================
print_info "檢查 LINE Bot 環境變數..."

if [ -z "$LINE_CHANNEL_ACCESS_TOKEN" ]; then
    print_warning "未設定 LINE_CHANNEL_ACCESS_TOKEN"
    read -p "請輸入 LINE Channel Access Token: " LINE_CHANNEL_ACCESS_TOKEN
fi

if [ -z "$LINE_CHANNEL_SECRET" ]; then
    print_warning "未設定 LINE_CHANNEL_SECRET"
    read -p "請輸入 LINE Channel Secret: " LINE_CHANNEL_SECRET
fi

print_success "環境變數設定完成"

# ============================================
# 步驟 4: 檢查 Firestore 是否已啟用
# ============================================
print_info "檢查 Firestore API 狀態..."

if gcloud services list --enabled --filter="name:firestore.googleapis.com" --format="value(name)" | grep -q "firestore.googleapis.com"; then
    print_success "Firestore API 已啟用"
else
    print_warning "Firestore API 尚未啟用"
    read -p "是否要啟用 Firestore API? (y/n): " enable_firestore
    
    if [ "$enable_firestore" = "y" ] || [ "$enable_firestore" = "Y" ]; then
        gcloud services enable firestore.googleapis.com
        print_success "Firestore API 已啟用"
        print_warning "請前往 Firestore Console 建立資料庫: https://console.cloud.google.com/firestore"
        print_warning "選擇 Native mode 和適當的區域 (建議: asia-east1)"
        read -p "完成後按 Enter 繼續..."
    else
        print_error "需要啟用 Firestore API 才能繼續部署"
        exit 1
    fi
fi

# ============================================
# 步驟 5: 建置 Docker 映像
# ============================================
print_info "開始建置 Docker 映像..."

IMAGE_NAME="gcr.io/$PROJECT_ID/bible-bot"
IMAGE_TAG="v5-firestore"
FULL_IMAGE="$IMAGE_NAME:$IMAGE_TAG"

print_info "映像名稱: $FULL_IMAGE"

gcloud builds submit --tag "$FULL_IMAGE"

print_success "Docker 映像建置完成"

# ============================================
# 步驟 6: 部署到 Cloud Run
# ============================================
print_info "開始部署到 Cloud Run..."

SERVICE_NAME="bible-bot"
REGION="asia-east1"

gcloud run deploy "$SERVICE_NAME" \
    --image "$FULL_IMAGE" \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --set-env-vars "LINE_CHANNEL_ACCESS_TOKEN=$LINE_CHANNEL_ACCESS_TOKEN,LINE_CHANNEL_SECRET=$LINE_CHANNEL_SECRET" \
    --memory 512Mi \
    --cpu 1 \
    --max-instances 10 \
    --timeout 60

print_success "部署完成!"

# ============================================
# 步驟 7: 取得服務 URL
# ============================================
print_info "取得服務 URL..."

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --region "$REGION" --format="value(status.url)")

print_success "服務 URL: $SERVICE_URL"

# ============================================
# 步驟 8: 測試 Webhook
# ============================================
print_info "測試 Webhook 連線..."

WEBHOOK_URL="$SERVICE_URL/callback"
TEST_RESPONSE=$(curl -s -X POST "$WEBHOOK_URL" \
    -H "Content-Type: application/json" \
    -d '{"events":[]}')

if echo "$TEST_RESPONSE" | grep -q "ok"; then
    print_success "Webhook 測試成功!"
else
    print_warning "Webhook 測試回應: $TEST_RESPONSE"
fi

# ============================================
# 步驟 9: 顯示後續步驟
# ============================================
echo ""
echo "============================================"
print_success "🎉 部署完成!"
echo "============================================"
echo ""
print_info "後續步驟:"
echo ""
echo "1. 設定 LINE Bot Webhook URL:"
echo "   前往 LINE Developers Console: https://developers.line.biz/console/"
echo "   Webhook URL: $WEBHOOK_URL"
echo ""
echo "2. 測試 Bot 功能:"
echo "   - 在 LINE 中封鎖並重新加入您的 Bot"
echo "   - Bot 應該發送歡迎訊息"
echo "   - 選擇讀經計畫並測試功能"
echo ""
echo "3. 驗證資料持久化:"
echo "   - 與 Bot 互動並記錄狀態"
echo "   - 執行: gcloud run services update $SERVICE_NAME --region $REGION"
echo "   - 再次與 Bot 互動,確認資料仍然存在"
echo ""
echo "4. 查看日誌:"
echo "   gcloud run services logs tail $SERVICE_NAME --region $REGION"
echo ""
print_info "詳細說明請參考: FIRESTORE_DEPLOYMENT_GUIDE.md"
echo ""

