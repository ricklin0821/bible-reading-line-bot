"""
隱私設定模組
處理使用者的隱私設定，包括排行榜顯示控制
"""
from linebot.v3.messaging import (
    FlexMessage, FlexBubble, FlexBox, FlexText, FlexButton, 
    PostbackAction, FlexSeparator, MessageAction
)
from database import User


def get_privacy_settings_message(user: User) -> FlexMessage:
    """
    生成隱私設定的 Flex Message
    
    Args:
        user: 使用者物件
    
    Returns:
        FlexMessage: 隱私設定訊息
    """
    # 獲取當前設定
    show_in_leaderboard = user.show_in_leaderboard if hasattr(user, 'show_in_leaderboard') else True
    
    # 狀態文字和圖示
    if show_in_leaderboard:
        status_text = "✅ 公開顯示"
        status_color = "#10b981"
        description = "您的名字會顯示在排行榜上，與弟兄姊妹一起見證讀經的堅持！"
        button_text = "🔒 切換為隱藏"
        button_action = "privacy_hide"
    else:
        status_text = "🔒 隱藏顯示"
        status_color = "#6b7280"
        description = "您的名字不會顯示在排行榜上，但您的讀經記錄仍會保留。"
        button_text = "✅ 切換為公開"
        button_action = "privacy_show"
    
    bubble = FlexBubble(
        size="mega",
        header=FlexBox(
            layout="vertical",
            contents=[
                FlexText(
                    text="🔒 隱私設定",
                    weight="bold",
                    size="xl",
                    color="#1f2937"
                )
            ],
            background_color="#f3f4f6",
            padding_all="20px"
        ),
        body=FlexBox(
            layout="vertical",
            contents=[
                # 當前狀態
                FlexBox(
                    layout="vertical",
                    contents=[
                        FlexText(
                            text="排行榜顯示設定",
                            size="sm",
                            color="#6b7280",
                            margin="none"
                        ),
                        FlexText(
                            text=status_text,
                            size="xxl",
                            weight="bold",
                            color=status_color,
                            margin="md"
                        )
                    ],
                    margin="none"
                ),
                
                FlexSeparator(margin="xl"),
                
                # 說明文字
                FlexBox(
                    layout="vertical",
                    contents=[
                        FlexText(
                            text=description,
                            size="sm",
                            color="#4b5563",
                            wrap=True,
                            margin="md"
                        )
                    ],
                    margin="xl"
                ),
                
                FlexSeparator(margin="xl"),
                
                # 功能說明
                FlexBox(
                    layout="vertical",
                    contents=[
                        FlexText(
                            text="💡 功能說明",
                            size="sm",
                            weight="bold",
                            color="#1f2937",
                            margin="md"
                        ),
                        FlexText(
                            text="• 公開：您的名字會出現在排行榜上",
                            size="xs",
                            color="#6b7280",
                            margin="sm"
                        ),
                        FlexText(
                            text="• 隱藏：排行榜上顯示「匿名使用者」",
                            size="xs",
                            color="#6b7280",
                            margin="xs"
                        ),
                        FlexText(
                            text="• 您的讀經記錄不受影響",
                            size="xs",
                            color="#6b7280",
                            margin="xs"
                        ),
                        FlexText(
                            text="• 可隨時切換設定",
                            size="xs",
                            color="#6b7280",
                            margin="xs"
                        )
                    ],
                    margin="xl"
                )
            ],
            spacing="sm",
            padding_all="20px"
        ),
        footer=FlexBox(
            layout="vertical",
            contents=[
                # 切換按鈕
                FlexButton(
                    style="primary",
                    color="#667eea",
                    action=PostbackAction(
                        label=button_text,
                        data=f"action={button_action}"
                    ),
                    height="sm"
                ),
                # 返回按鈕
                FlexButton(
                    style="link",
                    action=MessageAction(
                        label="返回",
                        text="選單"
                    ),
                    height="sm",
                    margin="sm"
                )
            ],
            spacing="sm",
            padding_all="20px"
        )
    )
    
    return FlexMessage(alt_text="隱私設定", contents=bubble)


def toggle_privacy_setting(user: User, show: bool) -> str:
    """
    切換使用者的隱私設定
    
    Args:
        user: 使用者物件
        show: True 為公開，False 為隱藏
    
    Returns:
        str: 確認訊息
    """
    user.show_in_leaderboard = show
    user.save()
    
    if show:
        return "✅ 設定已更新！\n\n您的名字現在會顯示在排行榜上。\n與弟兄姊妹一起見證讀經的堅持！"
    else:
        return "🔒 設定已更新！\n\n您的名字現在不會顯示在排行榜上。\n您的讀經記錄仍會正常保留。"


def get_privacy_status_text(user: User) -> str:
    """
    獲取隱私狀態的簡短文字說明
    
    Args:
        user: 使用者物件
    
    Returns:
        str: 狀態文字
    """
    show_in_leaderboard = user.show_in_leaderboard if hasattr(user, 'show_in_leaderboard') else True
    
    if show_in_leaderboard:
        return "✅ 排行榜顯示：公開"
    else:
        return "🔒 排行榜顯示：隱藏"
