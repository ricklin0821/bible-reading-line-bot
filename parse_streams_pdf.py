#!/usr/bin/env python3
"""
解析荒漠甘泉 PDF 文字檔，轉換成繁體並存成 JSON
"""

import re
import json
from opencc import OpenCC

# 初始化簡繁轉換器
cc = OpenCC('s2t')  # 簡體轉繁體

def parse_streams_text(text_file):
    """解析荒漠甘泉文字檔"""
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分割每一天的內容
    # 格式：《荒漠甘泉》X 月 Y 日
    pattern = r'《荒漠甘泉》(\d+)\s*月\s*(\d+)\s*日\n(.*?)(?=《荒漠甘泉》|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    print(f"找到 {len(matches)} 天的內容")
    
    all_data = {}
    
    for match in matches:
        month = int(match[0])
        day = int(match[1])
        daily_content = match[2].strip()
        
        # 分離經文和內容
        lines = daily_content.split('\n')
        
        # 第一行通常是經文
        verse = lines[0] if lines else ""
        
        # 提取經文引用（括號中的內容）
        verse_ref = ""
        verse_match = re.search(r'[（(]([^）)]+)[）)]', verse)
        if verse_match:
            verse_ref = verse_match.group(1)
        
        # 其餘是內容
        content_text = '\n'.join(lines[1:]).strip()
        
        # 移除分隔線
        content_text = re.sub(r'-{10,}', '', content_text).strip()
        
        # 轉換成繁體
        verse_tc = cc.convert(verse)
        verse_ref_tc = cc.convert(verse_ref)
        content_tc = cc.convert(content_text)
        
        # 儲存
        key = f"{month:02d}-{day:02d}"
        all_data[key] = {
            'month': month,
            'day': day,
            'verse': verse_tc,
            'verse_ref': verse_ref_tc,
            'content': content_tc
        }
        
        print(f"✓ {month}月{day}日 處理完成")
    
    return all_data

def main():
    """主函數"""
    print("開始解析荒漠甘泉...")
    
    # 解析文字檔
    data = parse_streams_text('/home/ubuntu/bible-reading-line-bot/streams_in_desert.txt')
    
    # 儲存為 JSON
    output_file = '/home/ubuntu/bible-reading-line-bot/streams_in_desert.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"解析完成！共 {len(data)} 天的內容")
    print(f"已儲存至: {output_file}")
    print(f"{'='*50}")
    
    # 顯示今天（11月6日）的內容作為測試
    if '11-06' in data:
        print("\n今天（11月6日）的內容：")
        print(f"經文：{data['11-06']['verse']}")
        print(f"內容（前200字）：{data['11-06']['content'][:200]}...")

if __name__ == '__main__':
    main()
