#!/usr/bin/env python3
"""
每日自動發送荒漠甘泉圖片
在中午 12:30 發送給所有使用者
"""
import os
from datetime import datetime
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, PushMessageRequest,
    ImageMessage, TextMessage
)
from database import init_db, User
from daily_verse import generate_devotional_share_image

# LINE Bot 設定
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

def send_daily_devotional():
    """發送每日荒漠甘泉圖片給所有使用者"""
    
    # 初始化資料庫
    init_db()
    
    # 初始化 LINE Bot API
    configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
    
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        
        # 獲取所有使用者
        users = User.get_all_users()
        
        print(f"開始發送每日荒漠甘泉圖片給 {len(users)} 位使用者...")
        
        success_count = 0
        fail_count = 0
        
        for user in users:
            try:
                # 生成圖片
                image_path = generate_devotional_share_image(user)
                
                if not image_path:
                    print(f"❌ 無法為使用者 {user.user_id} 生成圖片")
                    fail_count += 1
                    continue
                
                # 獲取圖片檔名
                image_filename = os.path.basename(image_path)
                
                # 產生公開 URL
                base_url = os.environ.get('BASE_URL', 'https://bible-bot-741437082833.asia-east1.run.app')
                image_url = f"{base_url}/devotional_images/{image_filename}"
                
                # 發送圖片
                messaging_api.push_message(
                    PushMessageRequest(
                        to=user.user_id,
                        messages=[
                            TextMessage(text="🌅 早安！今天的荒漠甘泉："),
                            ImageMessage(
                                original_content_url=image_url,
                                preview_image_url=image_url
                            )
                        ]
                    )
                )
                
                print(f"✅ 成功發送給使用者 {user.user_id}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ 發送給使用者 {user.user_id} 失敗: {e}")
                fail_count += 1
        
        print(f"\n發送完成！成功: {success_count}, 失敗: {fail_count}")

if __name__ == '__main__':
    send_daily_devotional()
