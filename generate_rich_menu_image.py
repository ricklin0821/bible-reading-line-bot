#!/usr/bin/env python3
"""
生成 Rich Menu 圖片
尺寸: 2500x1686
"""
from PIL import Image, ImageDraw, ImageFont
import os

# 圖片尺寸
WIDTH = 2500
HEIGHT = 1686

# 按鈕尺寸
BUTTON_WIDTH = 1250
BUTTON_HEIGHT = 562

# 顏色
BG_COLOR = (99, 102, 241)  # 紫藍色
BUTTON_COLOR = (255, 255, 255)  # 白色
TEXT_COLOR = (99, 102, 241)  # 紫藍色
BORDER_COLOR = (209, 213, 219)  # 淺灰色

# 按鈕配置
BUTTONS = [
    {"text": "📖\n今日讀經", "row": 0, "col": 0},
    {"text": "🌅\n荒漠甘泉", "row": 0, "col": 1},
    {"text": "✅\n回報讀經", "row": 1, "col": 0},
    {"text": "📊\n我的進度", "row": 1, "col": 1},
    {"text": "🏆\n排行榜", "row": 2, "col": 0},
    {"text": "⚙️\n選單", "row": 2, "col": 1},
]

def find_font(paths):
    """尋找可用的字型"""
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def generate_rich_menu_image(output_path='rich_menu.png'):
    """生成 Rich Menu 圖片"""
    
    # 創建圖片
    img = Image.new('RGB', (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # 尋找字型
    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    ]
    
    font_path = find_font(font_paths)
    
    if font_path:
        try:
            font_large = ImageFont.truetype(font_path, 100)
            font_emoji = ImageFont.truetype(font_path, 120)
        except Exception as e:
            print(f"⚠️ 無法載入字型: {e}")
            font_large = ImageFont.load_default()
            font_emoji = ImageFont.load_default()
    else:
        print("⚠️ 找不到中文字型，使用預設字型")
        font_large = ImageFont.load_default()
        font_emoji = ImageFont.load_default()
    
    # 繪製按鈕
    for button in BUTTONS:
        row = button['row']
        col = button['col']
        text = button['text']
        
        # 計算按鈕位置
        x = col * BUTTON_WIDTH
        y = row * BUTTON_HEIGHT
        
        # 繪製按鈕背景（白色圓角矩形）
        margin = 10
        button_rect = [
            x + margin,
            y + margin,
            x + BUTTON_WIDTH - margin,
            y + BUTTON_HEIGHT - margin
        ]
        
        # 繪製圓角矩形
        draw.rounded_rectangle(
            button_rect,
            radius=30,
            fill=BUTTON_COLOR,
            outline=BORDER_COLOR,
            width=3
        )
        
        # 繪製文字（分兩行：Emoji + 文字）
        lines = text.split('\n')
        
        if len(lines) == 2:
            emoji = lines[0]
            label = lines[1]
            
            # Emoji
            bbox_emoji = draw.textbbox((0, 0), emoji, font=font_emoji)
            emoji_width = bbox_emoji[2] - bbox_emoji[0]
            emoji_height = bbox_emoji[3] - bbox_emoji[1]
            emoji_x = x + (BUTTON_WIDTH - emoji_width) // 2
            emoji_y = y + (BUTTON_HEIGHT - emoji_height) // 2 - 60
            draw.text((emoji_x, emoji_y), emoji, fill=TEXT_COLOR, font=font_emoji)
            
            # 文字
            bbox_label = draw.textbbox((0, 0), label, font=font_large)
            label_width = bbox_label[2] - bbox_label[0]
            label_height = bbox_label[3] - bbox_label[1]
            label_x = x + (BUTTON_WIDTH - label_width) // 2
            label_y = emoji_y + emoji_height + 20
            draw.text((label_x, label_y), label, fill=TEXT_COLOR, font=font_large)
    
    # 儲存圖片
    img.save(output_path, 'PNG')
    print(f"✅ Rich Menu 圖片已生成: {output_path}")
    print(f"   尺寸: {WIDTH}x{HEIGHT}")
    print(f"   檔案大小: {os.path.getsize(output_path) / 1024:.2f} KB")

if __name__ == '__main__':
    generate_rich_menu_image()
