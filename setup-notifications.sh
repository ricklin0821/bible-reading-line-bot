#!/bin/bash

# Cloud Build 部署失敗通知設定腳本
# 此腳本會設定多種通知方式，確保您能即時得知部署狀態

set -e

PROJECT_ID="bible-bot-project"
REGION="asia-east1"

echo "========================================="
echo "設定 Cloud Build 部署失敗通知"
echo "========================================="
echo ""

# 檢查是否已登入 gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ 錯誤：尚未登入 gcloud"
    echo "請執行：gcloud auth login"
    exit 1
fi

# 設定專案
echo "📌 設定專案：$PROJECT_ID"
gcloud config set project $PROJECT_ID

echo ""
echo "========================================="
echo "方法 1: Email 通知（推薦）"
echo "========================================="
echo ""

# 啟用 Cloud Build API
echo "✅ 啟用 Cloud Build API..."
gcloud services enable cloudbuild.googleapis.com

# 取得使用者 Email
USER_EMAIL=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1)
echo "📧 將發送通知到：$USER_EMAIL"

echo ""
echo "請前往以下連結設定 Email 通知："
echo "https://console.cloud.google.com/cloud-build/settings/notifications?project=$PROJECT_ID"
echo ""
echo "設定步驟："
echo "1. 點擊「建立通知器」"
echo "2. 選擇「Email」"
echo "3. 輸入您的 Email：$USER_EMAIL"
echo "4. 選擇通知條件："
echo "   - ✅ 建置失敗"
echo "   - ✅ 建置成功（可選）"
echo "5. 點擊「儲存」"
echo ""

read -p "按 Enter 繼續設定 Pub/Sub 通知..."

echo ""
echo "========================================="
echo "方法 2: Pub/Sub 通知（進階）"
echo "========================================="
echo ""

# 啟用 Pub/Sub API
echo "✅ 啟用 Pub/Sub API..."
gcloud services enable pubsub.googleapis.com

# 建立 Pub/Sub 主題
TOPIC_NAME="cloud-build-notifications"
echo "📮 建立 Pub/Sub 主題：$TOPIC_NAME"

if gcloud pubsub topics describe $TOPIC_NAME &>/dev/null; then
    echo "⚠️  主題已存在，跳過建立"
else
    gcloud pubsub topics create $TOPIC_NAME
    echo "✅ 主題建立成功"
fi

# 建立訂閱
SUBSCRIPTION_NAME="cloud-build-notifications-sub"
echo "📬 建立訂閱：$SUBSCRIPTION_NAME"

if gcloud pubsub subscriptions describe $SUBSCRIPTION_NAME &>/dev/null; then
    echo "⚠️  訂閱已存在，跳過建立"
else
    gcloud pubsub subscriptions create $SUBSCRIPTION_NAME \
        --topic=$TOPIC_NAME \
        --ack-deadline=60
    echo "✅ 訂閱建立成功"
fi

echo ""
echo "========================================="
echo "方法 3: Slack 通知（推薦）"
echo "========================================="
echo ""

echo "設定 Slack 通知步驟："
echo ""
echo "1. 前往 Slack 建立 Incoming Webhook："
echo "   https://api.slack.com/messaging/webhooks"
echo ""
echo "2. 選擇要接收通知的頻道"
echo ""
echo "3. 複製 Webhook URL"
echo ""
echo "4. 建立 Cloud Function 來接收 Pub/Sub 訊息並發送到 Slack"
echo ""

read -p "是否要建立 Slack 通知 Cloud Function？(y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "請輸入 Slack Webhook URL: " SLACK_WEBHOOK_URL
    
    if [ -z "$SLACK_WEBHOOK_URL" ]; then
        echo "❌ 未輸入 Webhook URL，跳過 Slack 通知設定"
    else
        echo "✅ 建立 Slack 通知 Cloud Function..."
        
        # 建立暫存目錄
        TEMP_DIR=$(mktemp -d)
        cd $TEMP_DIR
        
        # 建立 Cloud Function 程式碼
        cat > main.py << 'EOF'
import base64
import json
import requests
import os

def notify_slack(event, context):
    """Cloud Build 通知轉發到 Slack"""
    
    # 取得 Slack Webhook URL
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    if not webhook_url:
        print('SLACK_WEBHOOK_URL not set')
        return
    
    # 解析 Pub/Sub 訊息
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    build_data = json.loads(pubsub_message)
    
    # 取得建置資訊
    build_id = build_data.get('id', 'unknown')
    status = build_data.get('status', 'unknown')
    source = build_data.get('source', {})
    repo_name = source.get('repoSource', {}).get('repoName', 'unknown')
    branch = source.get('repoSource', {}).get('branchName', 'unknown')
    
    # 建置狀態顏色
    color_map = {
        'SUCCESS': 'good',
        'FAILURE': 'danger',
        'TIMEOUT': 'warning',
        'CANCELLED': 'warning'
    }
    color = color_map.get(status, '#808080')
    
    # 建置狀態 Emoji
    emoji_map = {
        'SUCCESS': '✅',
        'FAILURE': '❌',
        'TIMEOUT': '⏰',
        'CANCELLED': '🚫'
    }
    emoji = emoji_map.get(status, '❓')
    
    # 建立 Slack 訊息
    message = {
        'attachments': [{
            'color': color,
            'title': f'{emoji} Cloud Build {status}',
            'fields': [
                {'title': 'Repository', 'value': repo_name, 'short': True},
                {'title': 'Branch', 'value': branch, 'short': True},
                {'title': 'Build ID', 'value': build_id, 'short': False},
            ],
            'footer': 'Cloud Build',
            'ts': int(build_data.get('createTime', '0').split('.')[0])
        }]
    }
    
    # 只在失敗時發送通知（可根據需求調整）
    if status in ['FAILURE', 'TIMEOUT']:
        response = requests.post(webhook_url, json=message)
        print(f'Slack notification sent: {response.status_code}')
    else:
        print(f'Build status {status}, no notification sent')
EOF
        
        cat > requirements.txt << 'EOF'
requests==2.31.0
EOF
        
        # 部署 Cloud Function
        gcloud functions deploy cloud-build-slack-notifier \
            --runtime python311 \
            --trigger-topic $TOPIC_NAME \
            --entry-point notify_slack \
            --set-env-vars SLACK_WEBHOOK_URL="$SLACK_WEBHOOK_URL" \
            --region $REGION \
            --quiet
        
        echo "✅ Slack 通知 Cloud Function 部署成功"
        
        # 清理暫存目錄
        cd -
        rm -rf $TEMP_DIR
    fi
else
    echo "⏭️  跳過 Slack 通知設定"
fi

echo ""
echo "========================================="
echo "方法 4: LINE Notify 通知"
echo "========================================="
echo ""

echo "設定 LINE Notify 步驟："
echo ""
echo "1. 前往 LINE Notify 網站："
echo "   https://notify-bot.line.me/"
echo ""
echo "2. 登入並發行權杖"
echo ""
echo "3. 選擇要接收通知的聊天室"
echo ""
echo "4. 複製權杖"
echo ""

read -p "是否要建立 LINE Notify 通知 Cloud Function？(y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "請輸入 LINE Notify Token: " LINE_NOTIFY_TOKEN
    
    if [ -z "$LINE_NOTIFY_TOKEN" ]; then
        echo "❌ 未輸入 Token，跳過 LINE Notify 設定"
    else
        echo "✅ 建立 LINE Notify Cloud Function..."
        
        # 建立暫存目錄
        TEMP_DIR=$(mktemp -d)
        cd $TEMP_DIR
        
        # 建立 Cloud Function 程式碼
        cat > main.py << 'EOF'
import base64
import json
import requests
import os

def notify_line(event, context):
    """Cloud Build 通知轉發到 LINE"""
    
    # 取得 LINE Notify Token
    token = os.environ.get('LINE_NOTIFY_TOKEN')
    if not token:
        print('LINE_NOTIFY_TOKEN not set')
        return
    
    # 解析 Pub/Sub 訊息
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    build_data = json.loads(pubsub_message)
    
    # 取得建置資訊
    build_id = build_data.get('id', 'unknown')
    status = build_data.get('status', 'unknown')
    source = build_data.get('source', {})
    repo_name = source.get('repoSource', {}).get('repoName', 'unknown')
    branch = source.get('repoSource', {}).get('branchName', 'unknown')
    log_url = build_data.get('logUrl', '')
    
    # 建置狀態 Emoji
    emoji_map = {
        'SUCCESS': '✅',
        'FAILURE': '❌',
        'TIMEOUT': '⏰',
        'CANCELLED': '🚫'
    }
    emoji = emoji_map.get(status, '❓')
    
    # 建立 LINE 訊息
    message = f"""
{emoji} Cloud Build {status}

Repository: {repo_name}
Branch: {branch}
Build ID: {build_id}

查看日誌: {log_url}
"""
    
    # 只在失敗時發送通知（可根據需求調整）
    if status in ['FAILURE', 'TIMEOUT']:
        headers = {'Authorization': f'Bearer {token}'}
        data = {'message': message}
        response = requests.post('https://notify-api.line.me/api/notify', headers=headers, data=data)
        print(f'LINE notification sent: {response.status_code}')
    else:
        print(f'Build status {status}, no notification sent')
EOF
        
        cat > requirements.txt << 'EOF'
requests==2.31.0
EOF
        
        # 部署 Cloud Function
        gcloud functions deploy cloud-build-line-notifier \
            --runtime python311 \
            --trigger-topic $TOPIC_NAME \
            --entry-point notify_line \
            --set-env-vars LINE_NOTIFY_TOKEN="$LINE_NOTIFY_TOKEN" \
            --region $REGION \
            --quiet
        
        echo "✅ LINE Notify Cloud Function 部署成功"
        
        # 清理暫存目錄
        cd -
        rm -rf $TEMP_DIR
    fi
else
    echo "⏭️  跳過 LINE Notify 設定"
fi

echo ""
echo "========================================="
echo "✅ 通知設定完成！"
echo "========================================="
echo ""

echo "已設定的通知方式："
echo "1. ✅ Pub/Sub 主題：$TOPIC_NAME"
echo "2. ✅ Pub/Sub 訂閱：$SUBSCRIPTION_NAME"
echo ""

echo "下一步："
echo "1. 前往 Cloud Build 設定 Email 通知"
echo "2. 測試部署並檢查是否收到通知"
echo "3. 查看日誌：gcloud builds log --stream"
echo ""

echo "查看通知設定："
echo "gcloud pubsub topics list"
echo "gcloud pubsub subscriptions list"
echo "gcloud functions list"
echo ""

echo "測試通知："
echo "gcloud pubsub topics publish $TOPIC_NAME --message '{\"status\":\"FAILURE\",\"id\":\"test-build\"}'"
echo ""
