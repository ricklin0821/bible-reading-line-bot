"""
荒漠甘泉圖片生成模組
使用 Pillow 生成精美的每日荒漠甘泉分享圖片
"""

import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Optional

# 圖片尺寸（適合社群媒體分享）
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1080

# 字型路徑（使用系統字型）
# 嘗試多個可能的字型路徑
FONT_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
]

FONT_BOLD_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Bold.ttc",
]

# 尋找可用的字型檔案
def find_font(paths):
    for path in paths:
        if os.path.exists(path):
            return path
    return None

FONT_PATH = find_font(FONT_PATHS)
FONT_BOLD_PATH = find_font(FONT_BOLD_PATHS)

# 儲存路徑
SAVE_DIR = os.path.join(os.path.dirname(__file__), 'devotional_images')

# 確保儲存目錄存在
os.makedirs(SAVE_DIR, exist_ok=True)


def create_gradient_background(width: int, height: int, color1: tuple, color2: tuple) -> Image.Image:
    """
    創建漸層背景
    
    Args:
        width: 寬度
        height: 高度
        color1: 起始顏色 (R, G, B)
        color2: 結束顏色 (R, G, B)
    
    Returns:
        Image: 漸層背景圖片
    """
    base = Image.new('RGB', (width, height), color1)
    top = Image.new('RGB', (width, height), color2)
    
    mask = Image.new('L', (width, height))
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    
    base.paste(top, (0, 0), mask)
    return base


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    """
    將文字換行以適應指定寬度
    
    Args:
        text: 要換行的文字
        font: 字型
        max_width: 最大寬度
    
    Returns:
        list: 換行後的文字列表
    """
    lines = []
    words = text.replace('\n', ' \n ').split(' ')
    current_line = ""
    
    for word in words:
        if word == '\n':
            if current_line:
                lines.append(current_line.strip())
                current_line = ""
            lines.append("")
            continue
            
        test_line = current_line + word + " "
        bbox = font.getbbox(test_line)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.strip())
            current_line = word + " "
    
    if current_line:
        lines.append(current_line.strip())
    
    return lines


def generate_devotional_image(
    month: int,
    day: int,
    verse: str,
    content: str,
    verse_ref: str = ""
) -> str:
    """
    生成荒漠甘泉分享圖片
    
    Args:
        month: 月份
        day: 日期
        verse: 經文
        content: 內容（會截取前300字）
        verse_ref: 經文出處
    
    Returns:
        str: 圖片檔案路徑
    """
    # 創建漸層背景（優雅的紫藍色漸層）
    img = create_gradient_background(
        IMAGE_WIDTH, 
        IMAGE_HEIGHT,
        (102, 126, 234),  # 淡紫色 #667eea
        (118, 75, 162)    # 深紫色 #764ba2
    )
    
    draw = ImageDraw.Draw(img)
    
    # 載入字型
    try:
        if FONT_PATH and FONT_BOLD_PATH:
            font_title = ImageFont.truetype(FONT_BOLD_PATH, 56)
            font_date = ImageFont.truetype(FONT_PATH, 36)
            font_verse = ImageFont.truetype(FONT_BOLD_PATH, 40)
            font_verse_ref = ImageFont.truetype(FONT_PATH, 30)
            font_content = ImageFont.truetype(FONT_PATH, 30)
            font_footer = ImageFont.truetype(FONT_PATH, 26)
            print(f"Successfully loaded fonts: {FONT_PATH}")
        else:
            raise Exception("Font files not found")
    except Exception as e:
        print(f"Warning: Failed to load fonts: {e}")
        print("Using default font (Chinese characters may not display correctly)")
        # 如果載入失敗，使用預設字型
        font_title = ImageFont.load_default()
        font_date = ImageFont.load_default()
        font_verse = ImageFont.load_default()
        font_verse_ref = ImageFont.load_default()
        font_content = ImageFont.load_default()
        font_footer = ImageFont.load_default()
    
    # 繪製白色半透明背景卡片
    card_margin = 60
    card_rect = [card_margin, card_margin, IMAGE_WIDTH - card_margin, IMAGE_HEIGHT - card_margin]
    
    # 創建圓角矩形遮罩
    mask = Image.new('L', (IMAGE_WIDTH, IMAGE_HEIGHT), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(card_rect, radius=40, fill=255)
    
    # 創建白色半透明層
    overlay = Image.new('RGBA', (IMAGE_WIDTH, IMAGE_HEIGHT), (255, 255, 255, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(card_rect, radius=40, fill=(255, 255, 255, 240))
    
    # 合併
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # 當前 Y 位置
    y = card_margin + 50
    
    # 1. 標題「荒漠甘泉」
    title = "📖 荒漠甘泉"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = bbox[2] - bbox[0]
    title_x = (IMAGE_WIDTH - title_width) // 2
    draw.text((title_x, y), title, fill=(102, 126, 234), font=font_title)
    y += 80
    
    # 2. 日期
    date_text = f"{month}月{day}日"
    bbox = draw.textbbox((0, 0), date_text, font=font_date)
    date_width = bbox[2] - bbox[0]
    date_x = (IMAGE_WIDTH - date_width) // 2
    draw.text((date_x, y), date_text, fill=(107, 114, 128), font=font_date)
    y += 70
    
    # 3. 分隔線
    line_margin = 150
    draw.line([(line_margin, y), (IMAGE_WIDTH - line_margin, y)], fill=(209, 213, 219), width=2)
    y += 50
    
    # 4. 經文（加粗、居中）
    # 清理經文（移除引號）
    verse_clean = verse.replace('‚', '').replace('„', '').replace('"', '').replace('"', '').strip()
    
    # 換行處理
    verse_lines = wrap_text(verse_clean, font_verse, IMAGE_WIDTH - 200)
    
    for line in verse_lines:
        bbox = draw.textbbox((0, 0), line, font=font_verse)
        line_width = bbox[2] - bbox[0]
        line_x = (IMAGE_WIDTH - line_width) // 2
        draw.text((line_x, y), line, fill=(31, 41, 55), font=font_verse)
        y += 60
    
    # 5. 經文出處
    if verse_ref:
        y += 10
        ref_text = f"— {verse_ref}"
        bbox = draw.textbbox((0, 0), ref_text, font=font_verse_ref)
        ref_width = bbox[2] - bbox[0]
        ref_x = (IMAGE_WIDTH - ref_width) // 2
        draw.text((ref_x, y), ref_text, fill=(107, 114, 128), font=font_verse_ref)
        y += 60
    
    # 6. 分隔線
    draw.line([(line_margin, y), (IMAGE_WIDTH - line_margin, y)], fill=(209, 213, 219), width=2)
    y += 50
    
    # 7. 內容摘要（限制長度 - 簡潔版）
    content_clean = content.replace('\f', ' ').replace('\n', ' ').strip()
    # 只顯示前 150 字
    if len(content_clean) > 150:
        content_clean = content_clean[:150] + '...'
    
    # 換行處理（確保不溢出白底框）
    content_lines = wrap_text(content_clean, font_content, IMAGE_WIDTH - 200)  # 增加邊界
    
    # 計算可用的高度（白底框內）
    available_height = IMAGE_HEIGHT - card_margin - 150 - y  # 留給底部標語的空間
    max_content_lines = int(available_height / 48) - 1  # 每行 48px
    
    if len(content_lines) > max_content_lines:
        content_lines = content_lines[:max_content_lines]
        if content_lines[-1]:
            content_lines[-1] = content_lines[-1][:40] + '...'
    
    for line in content_lines:
        if line:  # 跳過空行
            draw.text((100, y), line, fill=(75, 85, 99), font=font_content)
        y += 48
    
    # 8. 底部標語（移除點擊提示）
    y = IMAGE_HEIGHT - card_margin - 70
    footer_text = "💡 願神的話語成為今天的力量"
    bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    footer_width = bbox[2] - bbox[0]
    footer_x = (IMAGE_WIDTH - footer_width) // 2
    draw.text((footer_x, y), footer_text, fill=(107, 114, 128), font=font_footer)
    
    # 儲存圖片
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"devotional_{month:02d}{day:02d}_{timestamp}.png"
    filepath = os.path.join(SAVE_DIR, filename)
    
    img.save(filepath, 'PNG', quality=95)
    
    return filepath


def generate_devotional_image_from_dict(devotional: Dict) -> str:
    """
    從荒漠甘泉字典生成圖片
    
    Args:
        devotional: 荒漠甘泉字典，包含 month, day, verse, content, verse_ref
    
    Returns:
        str: 圖片檔案路徑
    """
    return generate_devotional_image(
        month=devotional['month'],
        day=devotional['day'],
        verse=devotional['verse'],
        content=devotional['content'],
        verse_ref=devotional.get('verse_ref', '')
    )


if __name__ == '__main__':
    # 測試
    test_devotional = {
        'month': 11,
        'day': 6,
        'verse': '「凡我所疼愛的，我就責備管教他」（啟 3:19）。',
        'verse_ref': '啟 3:19',
        'content': '受到最劇烈的痛苦的，常是最屬靈的信徒。恩典受得最多的人，也是受苦受得最多的人。苦難臨到信徒，沒有一次是偶然的，每一次都是受著父神的指揮的。'
    }
    
    filepath = generate_devotional_image_from_dict(test_devotional)
    print(f"✓ 圖片已生成: {filepath}")
