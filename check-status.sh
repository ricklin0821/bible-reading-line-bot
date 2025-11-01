#!/bin/bash

# Bible Bot 部署狀態快速檢查腳本
# 用途：快速檢查建置、部署和服務狀態

set -e

PROJECT_ID="bible-bot-project"
SERVICE_NAME="bible-bot"
REGION="asia-east1"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================="
echo "📊 Bible Bot 部署狀態檢查"
echo "========================================="
echo ""

# 檢查是否已登入 gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ 錯誤：尚未登入 gcloud${NC}"
    echo "請執行：gcloud auth login"
    exit 1
fi

# 設定專案
gcloud config set project $PROJECT_ID --quiet

echo -e "${BLUE}1️⃣  最近 5 次建置：${NC}"
echo "---"
gcloud builds list --limit=5 --format="table(id.scope(build_id),status,createTime.date('%Y-%m-%d %H:%M:%S'),duration)" 2>/dev/null || echo "無法取得建置資訊"
echo ""

echo -e "${BLUE}2️⃣  Cloud Run 服務狀態：${NC}"
echo "---"

# 取得服務資訊
SERVICE_INFO=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url,status.conditions[0].status,status.latestReadyRevisionName)" 2>/dev/null)

if [ -z "$SERVICE_INFO" ]; then
    echo -e "${RED}❌ 無法取得服務資訊${NC}"
else
    SERVICE_URL=$(echo "$SERVICE_INFO" | cut -d$'\t' -f1)
    SERVICE_STATUS=$(echo "$SERVICE_INFO" | cut -d$'\t' -f2)
    LATEST_REVISION=$(echo "$SERVICE_INFO" | cut -d$'\t' -f3)
    
    echo "服務 URL: $SERVICE_URL"
    
    if [ "$SERVICE_STATUS" = "True" ]; then
        echo -e "服務狀態: ${GREEN}✅ 正常${NC}"
    else
        echo -e "服務狀態: ${RED}❌ 異常${NC}"
    fi
    
    echo "最新版本: $LATEST_REVISION"
fi
echo ""

echo -e "${BLUE}3️⃣  健康檢查：${NC}"
echo "---"

if [ -n "$SERVICE_URL" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$SERVICE_URL" || echo "000")
    
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "HTTP 狀態: ${GREEN}✅ $HTTP_CODE (正常)${NC}"
    else
        echo -e "HTTP 狀態: ${RED}❌ $HTTP_CODE (異常)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  無法取得服務 URL${NC}"
fi
echo ""

echo -e "${BLUE}4️⃣  最近 5 個錯誤：${NC}"
echo "---"

ERROR_LOGS=$(gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND severity>=ERROR" --limit=5 --format="table(timestamp.date('%Y-%m-%d %H:%M:%S'),severity,textPayload.slice(0:100))" 2>/dev/null)

if [ -z "$ERROR_LOGS" ] || [ "$ERROR_LOGS" = "Listed 0 items." ]; then
    echo -e "${GREEN}✅ 沒有錯誤${NC}"
else
    echo "$ERROR_LOGS"
fi
echo ""

echo -e "${BLUE}5️⃣  Firestore 索引狀態：${NC}"
echo "---"
echo "請前往以下連結檢查索引狀態："
echo "https://console.cloud.google.com/firestore/databases/-default-/indexes/composite?project=$PROJECT_ID"
echo ""

echo -e "${BLUE}6️⃣  快速連結：${NC}"
echo "---"
echo "📊 Cloud Build: https://console.cloud.google.com/cloud-build/builds?project=$PROJECT_ID"
echo "🚀 Cloud Run: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID"
echo "📝 日誌: https://console.cloud.google.com/logs/query?project=$PROJECT_ID"
echo "🔥 Firestore: https://console.cloud.google.com/firestore/databases/-default-/data/panel?project=$PROJECT_ID"
echo "👥 管理後台: $SERVICE_URL/admin"
echo ""

echo "========================================="
echo -e "${GREEN}✅ 檢查完成${NC}"
echo "========================================="
echo ""

# 提供建議
echo -e "${YELLOW}💡 提示：${NC}"
echo "• 如果發現錯誤，請執行：gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME AND severity>=ERROR\" --limit=20"
echo "• 如果需要查看即時日誌，請執行：gcloud logging tail \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\""
echo "• 如果需要重新部署，請執行：gcloud builds triggers run bible-bot-auto-deploy --branch=master"
echo ""
