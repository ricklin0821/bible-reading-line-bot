"""
每日荒漠甘泉模組
從本地 JSON 資料庫讀取荒漠甘泉內容
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict
from linebot.v3.messaging import (
    FlexMessage, FlexBubble, FlexBox, FlexText, FlexButton, FlexSeparator,
    MessageAction, URIAction, ImageMessage
)
from database import User
from devotional_image import generate_devotional_image_from_dict

# 荒漠甘泉資料庫路徑
STREAMS_DB_PATH = os.path.join(os.path.dirname(__file__), 'streams_in_desert.json')

# 載入荒漠甘泉資料
_streams_data = None

def load_streams_data():
    """載入荒漠甘泉資料"""
    global _streams_data
    if _streams_data is None:
        try:
            with open(STREAMS_DB_PATH, 'r', encoding='utf-8') as f:
                _streams_data = json.load(f)
        except Exception as e:
            print(f"Error loading streams data: {e}")
            _streams_data = {}
    return _streams_data


def get_daily_devotional(user: User = None) -> Optional[Dict]:
    """
    獲取當天的荒漠甘泉
    
    Args:
        user: 使用者物件（可選，用於判斷當前天數）
    
    Returns:
        Dict: 荒漠甘泉資訊，包含 verse, verse_ref, content
        None: 如果無法獲取
    """
    # 獲取今天的日期
    today = datetime.now()
    month = today.month
    day = today.day
    
    # 如果有使用者，可以根據使用者的當前天數來決定（可選）
    # 這裡我們使用實際日期
    
    # 載入資料
    data = load_streams_data()
    
    # 獲取今天的內容
    key = f"{month:02d}-{day:02d}"
    
    if key in data:
        return data[key]
    
    # 如果找不到，返回預設內容
    return {
        'month': month,
        'day': day,
        'verse': '「你的話是我腳前的燈，是我路上的光。」（詩篇 119:105）',
        'verse_ref': '詩篇 119:105',
        'content': '神的話語是我們生命中的光，指引我們前行的方向。讓我們每天都親近神的話語，從中得著力量和智慧。'
    }


def get_daily_devotional_message(user: User) -> FlexMessage:
    """
    生成每日荒漠甘泉的 Flex Message
    
    Args:
        user: 使用者物件
    
    Returns:
        FlexMessage: 荒漠甘泉訊息
    """
    devotional = get_daily_devotional(user)
    
    if not devotional:
        devotional = {
            'month': datetime.now().month,
            'day': datetime.now().day,
            'verse': '「你的話是我腳前的燈，是我路上的光。」（詩篇 119:105）',
            'verse_ref': '詩篇 119:105',
            'content': '神的話語是我們生命中的光，指引我們前行的方向。'
        }
    
    today = datetime.now().strftime("%Y/%m/%d")
    month = devotional['month']
    day = devotional['day']
    
    # 清理內容（移除分頁符等特殊字符）
    content = devotional['content'].replace('\f', '\n').strip()
    
    # 限制內容長度（LINE Flex Message 有字數限制）
    if len(content) > 800:
        content = content[:800] + '...'
    
    bubble = FlexBubble(
        size="mega",
        header=FlexBox(
            layout="vertical",
            contents=[
                FlexText(
                    text="📖 荒漠甘泉",
                    weight="bold",
                    size="xl",
                    color="#ffffff"
                )
            ],
            background_color="#667eea",
            padding_all="20px"
        ),
        body=FlexBox(
            layout="vertical",
            contents=[
                # 日期
                FlexBox(
                    layout="horizontal",
                    contents=[
                        FlexText(
                            text=f"{month}月{day}日",
                            size="md",
                            color="#667eea",
                            weight="bold",
                            flex=0
                        ),
                        FlexText(
                            text=today,
                            size="sm",
                            color="#9ca3af",
                            align="end"
                        )
                    ],
                    margin="none"
                ),
                
                FlexSeparator(margin="lg"),
                
                # 經文
                FlexBox(
                    layout="vertical",
                    contents=[
                        FlexText(
                            text=devotional['verse'],
                            size="md",
                            color="#1f2937",
                            wrap=True,
                            weight="bold",
                            margin="lg"
                        )
                    ],
                    margin="lg"
                ),
                
                FlexSeparator(margin="lg"),
                
                # 內容
                FlexBox(
                    layout="vertical",
                    contents=[
                        FlexText(
                            text=content,
                            size="sm",
                            color="#4b5563",
                            wrap=True,
                            margin="md"
                        )
                    ],
                    margin="lg"
                ),
                
                FlexSeparator(margin="xl"),
                
                # 鼓勵文字
                FlexBox(
                    layout="vertical",
                    contents=[
                        FlexText(
                            text="💡 願神的話語成為今天的力量",
                            size="xs",
                            color="#6b7280",
                            align="center",
                            margin="md"
                        )
                    ],
                    margin="lg"
                )
            ],
            spacing="sm",
            padding_all="20px"
        ),
        footer=FlexBox(
            layout="vertical",
            contents=[
                # 開始讀經按鈕
                FlexButton(
                    style="primary",
                    color="#667eea",
                    action=MessageAction(
                        label="開始今日讀經",
                        text="今日讀經"
                    ),
                    height="sm"
                )
            ],
            spacing="sm",
            padding_all="20px"
        )
    )
    
    return FlexMessage(alt_text=f"荒漠甘泉 {month}月{day}日", contents=bubble)


def get_devotional_text(user: User = None) -> str:
    """
    獲取每日荒漠甘泉的純文字版本
    
    Args:
        user: 使用者物件
    
    Returns:
        str: 純文字版本的荒漠甘泉
    """
    devotional = get_daily_devotional(user)
    
    if not devotional:
        return "今天的荒漠甘泉暫時無法獲取，請稍後再試。"
    
    month = devotional['month']
    day = devotional['day']
    verse = devotional['verse']
    content = devotional['content'].replace('\f', '\n').strip()
    
    # 限制長度
    if len(content) > 500:
        content = content[:500] + '...'
    
    return f"📖 荒漠甘泉 {month}月{day}日\n\n{verse}\n\n{content}"


def generate_devotional_share_image(user: User = None) -> Optional[str]:
    """
    生成荒漠甘泉分享圖片
    
    Args:
        user: 使用者物件
    
    Returns:
        str: 圖片檔案路徑
        None: 如果無法生成
    """
    devotional = get_daily_devotional(user)
    
    if not devotional:
        return None
    
    try:
        filepath = generate_devotional_image_from_dict(devotional)
        return filepath
    except Exception as e:
        print(f"Error generating devotional image: {e}")
        return None
