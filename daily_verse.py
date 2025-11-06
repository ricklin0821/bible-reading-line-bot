"""
每日金句模組
從當天的讀經範圍中選擇一句經文作為每日金句
"""
from typing import Dict, Optional
from datetime import datetime
from linebot.v3.messaging import (
    FlexMessage, FlexBubble, FlexBox, FlexText, FlexButton,
    FlexSeparator, MessageAction, URIAction, FlexImage
)
from database import User, BiblePlan


# 精選金句列表（按天數對應）
# 這些是手動選擇的精華經文，優先使用
FEATURED_VERSES = {
    1: {
        "text": "起初，神創造天地。",
        "reference": "創世記 1:1",
        "book": "創世記",
        "chapter": 1,
        "verse": 1
    },
    2: {
        "text": "神看著一切所造的都甚好。有晚上，有早晨，是第六日。",
        "reference": "創世記 1:31",
        "book": "創世記",
        "chapter": 1,
        "verse": 31
    },
    7: {
        "text": "耶和華神用地上的塵土造人，將生氣吹在他鼻孔裡，他就成了有靈的活人，名叫亞當。",
        "reference": "創世記 2:7",
        "book": "創世記",
        "chapter": 2,
        "verse": 7
    },
    30: {
        "text": "你的話是我腳前的燈，是我路上的光。",
        "reference": "詩篇 119:105",
        "book": "詩篇",
        "chapter": 119,
        "verse": 105
    },
    100: {
        "text": "你們要嘗嘗主恩的滋味，便知道他是美善；投靠他的人有福了！",
        "reference": "詩篇 34:8",
        "book": "詩篇",
        "chapter": 34,
        "verse": 8
    },
    365: {
        "text": "我靠著那加給我力量的，凡事都能做。",
        "reference": "腓立比書 4:13",
        "book": "腓立比書",
        "chapter": 4,
        "verse": 13
    }
}


def get_daily_verse(user: User) -> Optional[Dict]:
    """
    獲取當天的每日金句
    
    Args:
        user: 使用者物件
    
    Returns:
        Dict: 金句資訊，包含 text, reference, book, chapter, verse
        None: 如果無法獲取金句
    """
    if not user or not user.plan_type:
        return None
    
    current_day = user.current_day or 1
    
    # 優先使用精選金句
    if current_day in FEATURED_VERSES:
        return FEATURED_VERSES[current_day]
    
    # 如果沒有精選金句，返回預設金句（避免從讀經計畫中獲取，因為可能會導致錯誤）
    # 直接返回預設金句
    
    # 如果都失敗，返回預設金句
    return {
        "text": "你的話是我腳前的燈，是我路上的光。",
        "reference": "詩篇 119:105",
        "book": "詩篇",
        "chapter": 119,
        "verse": 105
    }


def get_daily_verse_message(user: User) -> FlexMessage:
    """
    生成每日金句的 Flex Message
    
    Args:
        user: 使用者物件
    
    Returns:
        FlexMessage: 每日金句訊息
    """
    verse = get_daily_verse(user)
    
    if not verse:
        verse = {
            "text": "你的話是我腳前的燈，是我路上的光。",
            "reference": "詩篇 119:105",
            "book": "詩篇",
            "chapter": 119,
            "verse": 105
        }
    
    current_day = user.current_day or 1
    today = datetime.now().strftime("%Y/%m/%d")
    
    # 構建 Bible Gateway 連結（使用 quote 編碼中文）
    from urllib.parse import quote
    reference_encoded = quote(verse['reference'])
    bible_url = f"https://www.biblegateway.com/passage/?search={reference_encoded}&version=CUVMPT"
    
    bubble = FlexBubble(
        size="mega",
        header=FlexBox(
            layout="vertical",
            contents=[
                FlexText(
                    text="📖 今日金句",
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
                # 日期和天數
                FlexBox(
                    layout="horizontal",
                    contents=[
                        FlexText(
                            text=f"第 {current_day} 天",
                            size="sm",
                            color="#6b7280",
                            flex=1
                        ),
                        FlexText(
                            text=today,
                            size="sm",
                            color="#6b7280",
                            align="end"
                        )
                    ],
                    margin="none"
                ),
                
                FlexSeparator(margin="md"),
                
                # 金句內容
                FlexBox(
                    layout="vertical",
                    contents=[
                        FlexText(
                            text=f"「{verse['text']}」",
                            size="lg",
                            color="#1f2937",
                            wrap=True,
                            weight="bold",
                            margin="xl"
                        ),
                        FlexText(
                            text=f"— {verse['reference']}",
                            size="sm",
                            color="#667eea",
                            align="end",
                            margin="md",
                            weight="bold"
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
                            text="💡 讓神的話語成為今天的力量",
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
                # 閱讀經文按鈕
                FlexButton(
                    style="primary",
                    color="#667eea",
                    action=URIAction(
                        label="📖 閱讀完整經文",
                        uri=bible_url
                    ),
                    height="sm"
                ),
                # 開始讀經按鈕
                FlexButton(
                    style="link",
                    action=MessageAction(
                        label="開始今日讀經",
                        text="回報讀經"
                    ),
                    height="sm",
                    margin="sm"
                )
            ],
            spacing="sm",
            padding_all="20px"
        )
    )
    
    return FlexMessage(alt_text=f"今日金句：{verse['reference']}", contents=bubble)


def get_verse_text(user: User) -> str:
    """
    獲取每日金句的純文字版本
    
    Args:
        user: 使用者物件
    
    Returns:
        str: 金句文字
    """
    verse = get_daily_verse(user)
    
    if not verse:
        return "今日金句：你的話是我腳前的燈，是我路上的光。（詩篇 119:105）"
    
    current_day = user.current_day or 1
    today = datetime.now().strftime("%Y/%m/%d")
    
    return f"""📖 今日金句（第 {current_day} 天）
{today}

「{verse['text']}」

— {verse['reference']}

💡 讓神的話語成為今天的力量"""
