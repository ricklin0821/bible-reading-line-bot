"""
成就分享圖片生成模組
使用 Pillow 生成精美的成就分享圖片
"""
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Dict, Optional


# 字型路徑
FONT_PATH_REGULAR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
FONT_PATH_BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"

# 圖片尺寸
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1080

# 顏色定義
COLOR_GRADIENT_START = (102, 126, 234)  # #667eea
COLOR_GRADIENT_END = (118, 75, 162)     # #764ba2
COLOR_WHITE = (255, 255, 255)
COLOR_GOLD = (255, 215, 0)
COLOR_TEXT_DARK = (45, 55, 72)
COLOR_TEXT_LIGHT = (107, 114, 128)


def create_gradient_background(width: int, height: int, color_start: tuple, color_end: tuple) -> Image.Image:
    """
    創建漸層背景
    
    Args:
        width: 圖片寬度
        height: 圖片高度
        color_start: 起始顏色 (R, G, B)
        color_end: 結束顏色 (R, G, B)
    
    Returns:
        Image: 漸層背景圖片
    """
    base = Image.new('RGB', (width, height), color_start)
    top = Image.new('RGB', (width, height), color_end)
    mask = Image.new('L', (width, height))
    mask_data = []
    
    for y in range(height):
        for x in range(width):
            mask_data.append(int(255 * (y / height)))
    
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    
    return base


def draw_text_with_shadow(draw: ImageDraw.Draw, position: tuple, text: str, font: ImageFont.FreeTypeFont, 
                          fill: tuple, shadow_offset: int = 3):
    """
    繪製帶陰影的文字
    
    Args:
        draw: ImageDraw 物件
        position: 文字位置 (x, y)
        text: 文字內容
        font: 字型
        fill: 文字顏色
        shadow_offset: 陰影偏移量
    """
    x, y = position
    # 繪製陰影
    shadow_color = (0, 0, 0, 50)
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color)
    # 繪製文字
    draw.text((x, y), text, font=font, fill=fill)


def generate_achievement_image(achievement_type: str, achievement_data: Dict) -> str:
    """
    生成成就分享圖片
    
    Args:
        achievement_type: 成就類型 (streak, quiz, milestone)
        achievement_data: 成就數據
            - title: 成就標題
            - subtitle: 成就副標題
            - emoji: 成就圖示
            - value: 成就數值
            - verse_text: 經文內容（可選）
            - verse_ref: 經文出處（可選）
            - date: 達成日期（可選）
    
    Returns:
        str: 圖片檔案路徑
    """
    # 創建漸層背景
    img = create_gradient_background(IMAGE_WIDTH, IMAGE_HEIGHT, COLOR_GRADIENT_START, COLOR_GRADIENT_END)
    draw = ImageDraw.Draw(img)
    
    # 載入字型
    try:
        font_title = ImageFont.truetype(FONT_PATH_BOLD, 80, index=0)
        font_emoji = ImageFont.truetype(FONT_PATH_REGULAR, 150, index=0)
        font_subtitle = ImageFont.truetype(FONT_PATH_REGULAR, 50, index=0)
        font_value = ImageFont.truetype(FONT_PATH_BOLD, 60, index=0)
        font_verse = ImageFont.truetype(FONT_PATH_REGULAR, 40, index=0)
        font_verse_ref = ImageFont.truetype(FONT_PATH_BOLD, 35, index=0)
        font_date = ImageFont.truetype(FONT_PATH_REGULAR, 30, index=0)
        font_footer = ImageFont.truetype(FONT_PATH_REGULAR, 28, index=0)
    except Exception as e:
        print(f"Error loading fonts: {e}")
        # 使用預設字型
        font_title = ImageFont.load_default()
        font_emoji = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        font_value = ImageFont.load_default()
        font_verse = ImageFont.load_default()
        font_verse_ref = ImageFont.load_default()
        font_date = ImageFont.load_default()
        font_footer = ImageFont.load_default()
    
    # 繪製白色圓角矩形背景
    rect_margin = 80
    rect_x1 = rect_margin
    rect_y1 = 250
    rect_x2 = IMAGE_WIDTH - rect_margin
    rect_y2 = IMAGE_HEIGHT - 150
    
    # 創建圓角矩形遮罩
    rounded_rectangle = Image.new('RGBA', (IMAGE_WIDTH, IMAGE_HEIGHT), (255, 255, 255, 0))
    rect_draw = ImageDraw.Draw(rounded_rectangle)
    rect_draw.rounded_rectangle(
        [(rect_x1, rect_y1), (rect_x2, rect_y2)],
        radius=30,
        fill=(255, 255, 255, 230)
    )
    img = Image.alpha_composite(img.convert('RGBA'), rounded_rectangle).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # 繪製頂部標題
    header_text = "🏆 恭喜獲得成就！"
    header_bbox = draw.textbbox((0, 0), header_text, font=font_title)
    header_width = header_bbox[2] - header_bbox[0]
    header_x = (IMAGE_WIDTH - header_width) // 2
    draw.text((header_x, 100), header_text, font=font_title, fill=COLOR_WHITE)
    
    # 繪製成就圖示（使用圓形色塊）
    circle_radius = 100
    circle_x = IMAGE_WIDTH // 2
    circle_y = 380
    
    # 繪製外圈（金色）
    draw.ellipse(
        [(circle_x - circle_radius, circle_y - circle_radius),
         (circle_x + circle_radius, circle_y + circle_radius)],
        fill=COLOR_GOLD
    )
    
    # 繪製內圈（白色）
    inner_radius = circle_radius - 10
    draw.ellipse(
        [(circle_x - inner_radius, circle_y - inner_radius),
         (circle_x + inner_radius, circle_y + inner_radius)],
        fill=COLOR_WHITE
    )
    
    # 在圓形中間繪製 emoji 文字
    emoji = achievement_data.get('emoji', '🎉')
    emoji_bbox = draw.textbbox((0, 0), emoji, font=font_emoji)
    emoji_width = emoji_bbox[2] - emoji_bbox[0]
    emoji_height = emoji_bbox[3] - emoji_bbox[1]
    emoji_x = circle_x - emoji_width // 2
    emoji_y = circle_y - emoji_height // 2 - 20
    draw.text((emoji_x, emoji_y), emoji, font=font_emoji, fill=COLOR_GRADIENT_START)
    
    # 繪製成就標題
    title = achievement_data.get('title', '成就達成')
    title_bbox = draw.textbbox((0, 0), title, font=font_subtitle)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (IMAGE_WIDTH - title_width) // 2
    draw.text((title_x, 480), title, font=font_subtitle, fill=COLOR_TEXT_DARK)
    
    # 繪製成就數值
    if 'value' in achievement_data:
        value_text = achievement_data['value']
        value_bbox = draw.textbbox((0, 0), value_text, font=font_value)
        value_width = value_bbox[2] - value_bbox[0]
        value_x = (IMAGE_WIDTH - value_width) // 2
        draw.text((value_x, 560), value_text, font=font_value, fill=COLOR_GRADIENT_START)
    
    # 繪製經文（如果有）
    current_y = 660
    if 'verse_text' in achievement_data and achievement_data['verse_text']:
        verse_text = f"「{achievement_data['verse_text']}」"
        
        # 處理換行
        max_width = IMAGE_WIDTH - 200
        words = verse_text
        lines = []
        current_line = ""
        
        for char in words:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font_verse)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        
        if current_line:
            lines.append(current_line)
        
        # 繪製經文行
        for line in lines:
            line_bbox = draw.textbbox((0, 0), line, font=font_verse)
            line_width = line_bbox[2] - line_bbox[0]
            line_x = (IMAGE_WIDTH - line_width) // 2
            draw.text((line_x, current_y), line, font=font_verse, fill=COLOR_TEXT_LIGHT)
            current_y += 55
        
        # 繪製經文出處
        if 'verse_ref' in achievement_data:
            verse_ref = f"— {achievement_data['verse_ref']}"
            ref_bbox = draw.textbbox((0, 0), verse_ref, font=font_verse_ref)
            ref_width = ref_bbox[2] - ref_bbox[0]
            ref_x = (IMAGE_WIDTH - ref_width) // 2
            draw.text((ref_x, current_y + 10), verse_ref, font=font_verse_ref, fill=COLOR_GRADIENT_START)
            current_y += 70
    
    # 繪製達成日期
    date_text = achievement_data.get('date', datetime.now().strftime("%Y/%m/%d"))
    date_display = f"達成日期：{date_text}"
    date_bbox = draw.textbbox((0, 0), date_display, font=font_date)
    date_width = date_bbox[2] - date_bbox[0]
    date_x = (IMAGE_WIDTH - date_width) // 2
    draw.text((date_x, IMAGE_HEIGHT - 250), date_display, font=font_date, fill=COLOR_TEXT_LIGHT)
    
    # 繪製底部標籤
    footer_text = "📖 一年讀經計畫"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    footer_width = footer_bbox[2] - footer_bbox[0]
    footer_x = (IMAGE_WIDTH - footer_width) // 2
    draw.text((footer_x, IMAGE_HEIGHT - 100), footer_text, font=font_footer, fill=COLOR_WHITE)
    
    # 儲存圖片
    output_dir = "/home/ubuntu/bible-reading-line-bot/achievements"
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"achievement_{achievement_type}_{timestamp}.png"
    filepath = os.path.join(output_dir, filename)
    
    img.save(filepath, quality=95)
    
    return filepath


def generate_streak_achievement_image(days: int) -> str:
    """
    生成連續讀經成就圖片
    
    Args:
        days: 連續天數
    
    Returns:
        str: 圖片檔案路徑
    """
    # 根據天數選擇標題和圖示
    if days >= 365:
        title = "讀經勇士"
        emoji = "👑"
    elif days >= 100:
        title = "忠心僕人"
        emoji = "🌳"
    elif days >= 30:
        title = "堅持者"
        emoji = "🌿"
    elif days >= 7:
        title = "初心者"
        emoji = "🌱"
    else:
        title = "讀經新手"
        emoji = "🎉"
    
    achievement_data = {
        'title': title,
        'emoji': emoji,
        'value': f"連續讀經 {days} 天",
        'verse_text': "你的話是我腳前的燈，是我路上的光。",
        'verse_ref': "詩篇 119:105",
        'date': datetime.now().strftime("%Y/%m/%d")
    }
    
    return generate_achievement_image('streak', achievement_data)


def generate_quiz_achievement_image(perfect_count: int) -> str:
    """
    生成測驗成就圖片
    
    Args:
        perfect_count: 全對次數
    
    Returns:
        str: 圖片檔案路徑
    """
    # 根據全對次數選擇標題和圖示
    if perfect_count >= 500:
        title = "聖經學者"
        emoji = "📚"
    elif perfect_count >= 100:
        title = "真理探索者"
        emoji = "🎯"
    else:
        title = "學習者"
        emoji = "📖"
    
    achievement_data = {
        'title': title,
        'emoji': emoji,
        'value': f"測驗全對 {perfect_count} 次",
        'verse_text': "你們必曉得真理，真理必叫你們得以自由。",
        'verse_ref': "約翰福音 8:32",
        'date': datetime.now().strftime("%Y/%m/%d")
    }
    
    return generate_achievement_image('quiz', achievement_data)


def generate_milestone_achievement_image(milestone_type: str, value: int) -> str:
    """
    生成里程碑成就圖片
    
    Args:
        milestone_type: 里程碑類型 (reading_days, total_score)
        value: 數值
    
    Returns:
        str: 圖片檔案路徑
    """
    if milestone_type == 'reading_days':
        title = "讀經里程碑"
        emoji = "🎊"
        value_text = f"累計讀經 {value} 天"
        verse_text = "我今日成了何等人，是蒙神的恩才成的。"
        verse_ref = "哥林多前書 15:10"
    else:  # total_score
        title = "積分里程碑"
        emoji = "🌟"
        value_text = f"累計積分 {value} 分"
        verse_text = "忘記背後，努力面前的，向著標竿直跑。"
        verse_ref = "腓立比書 3:13-14"
    
    achievement_data = {
        'title': title,
        'emoji': emoji,
        'value': value_text,
        'verse_text': verse_text,
        'verse_ref': verse_ref,
        'date': datetime.now().strftime("%Y/%m/%d")
    }
    
    return generate_achievement_image('milestone', achievement_data)
