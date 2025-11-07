#!/usr/bin/env python3
"""
荒漠甘泉內容爬蟲
從 wd.bible 網站抓取 366 天的荒漠甘泉內容並存入 JSON 檔案
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

# 月份對應的 URL ID
MONTH_IDS = {
    1: 402,  # 1月
    2: 403,  # 2月
    3: 404,  # 3月
    4: 405,  # 4月
    5: 406,  # 5月 (需要確認)
    6: 407,  # 6月 (需要確認)
    7: 408,  # 7月 (需要確認)
    8: 409,  # 8月 (需要確認)
    9: 410,  # 9月 (需要確認)
    10: 411, # 10月 (需要確認)
    11: 406, # 11月
    12: 412, # 12月 (需要確認)
}

def get_month_url(month):
    """獲取月份的 URL"""
    return f"https://wd.bible/tw/resource/channel/4/{MONTH_IDS[month]}"

def scrape_month_list(month):
    """抓取某個月份的所有日期列表"""
    url = get_month_url(month)
    print(f"正在抓取 {month}月 的列表: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://wd.bible/tw/resource/channel/4'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 找到所有日期的連結
        day_links = []
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if f'/resource/channel/4/{MONTH_IDS[month]}/' in href and href.count('/') == 5:
                day_text = link.get_text(strip=True)
                if f'{month}月' in day_text and '日' in day_text:
                    day_links.append({
                        'url': 'https://wd.bible' + href if href.startswith('/') else href,
                        'text': day_text
                    })
        
        return day_links
    except Exception as e:
        print(f"抓取 {month}月 列表失敗: {e}")
        return []

def scrape_daily_content(url, month, day):
    """抓取某一天的完整內容"""
    print(f"正在抓取 {month}月{day}日 的內容: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://wd.bible/tw/resource/channel/4'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取經文（通常在第一個段落）
        verse = ""
        verse_ref = ""
        
        # 嘗試找到經文引用（通常包含書卷章節）
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if '（' in text and '）' in text and any(book in text for book in ['創', '出', '利', '民', '申', '書', '士', '得', '撒', '王', '代', '拉', '尼', '斯', '伯', '詩', '箴', '傳', '歌', '賽', '耶', '哀', '結', '但', '何', '珥', '摩', '俄', '拿', '彌', '鴻', '哈', '番', '該', '亞', '瑪', '太', '可', '路', '約', '徒', '羅', '林', '加', '弗', '腓', '西', '帖', '提', '多', '門', '來', '雅', '彼', '猶', '啟']):
                verse = text
                # 提取經文引用
                start = text.find('（')
                end = text.find('）')
                if start != -1 and end != -1:
                    verse_ref = text[start+1:end]
                break
        
        # 提取正文內容（所有段落）
        content_paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text and text != verse and len(text) > 10:
                content_paragraphs.append(text)
        
        content = '\n\n'.join(content_paragraphs[:5])  # 只取前5段，避免太長
        
        return {
            'month': month,
            'day': day,
            'verse': verse,
            'verse_ref': verse_ref,
            'content': content,
            'url': url
        }
    except Exception as e:
        print(f"抓取 {month}月{day}日 內容失敗: {e}")
        return None

def main():
    """主函數"""
    all_data = {}
    
    # 先測試 11月
    print("開始抓取荒漠甘泉內容...")
    
    for month in range(1, 13):
        print(f"\n{'='*50}")
        print(f"正在處理 {month}月")
        print(f"{'='*50}")
        
        # 獲取該月所有日期
        day_links = scrape_month_list(month)
        
        if not day_links:
            print(f"警告: {month}月 沒有找到任何日期")
            continue
        
        print(f"找到 {len(day_links)} 天的內容")
        
        # 抓取每一天的內容
        for link in day_links:
            # 從文字中提取日期
            day_text = link['text']
            try:
                day = int(day_text.split('月')[1].split('日')[0])
            except:
                print(f"無法解析日期: {day_text}")
                continue
            
            # 抓取內容
            daily_data = scrape_daily_content(link['url'], month, day)
            
            if daily_data:
                # 使用 "月-日" 作為 key
                key = f"{month:02d}-{day:02d}"
                all_data[key] = daily_data
                print(f"✓ {month}月{day}日 抓取成功")
            
            # 避免請求太快
            time.sleep(0.5)
    
    # 儲存為 JSON
    output_file = '/home/ubuntu/bible-reading-line-bot/streams_in_desert.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"抓取完成！共 {len(all_data)} 天的內容")
    print(f"已儲存至: {output_file}")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()
