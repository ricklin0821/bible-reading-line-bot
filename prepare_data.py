import re
import json
import pandas as pd
from collections import OrderedDict

# --- 1. 聖經經文資料處理 ---

def extract_bible_text(js_path="ChineseBibleSearchJS/bibleText.js"):
    print(f"Reading {js_path}...")
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 尋找包含經文陣列的區塊
    # 陣列內容位於 return new Array( ... ); 之間
    match = re.search(r'return new Array\(([\s\S]*?)\);', content)
    if not match:
        raise ValueError("Could not find the Bible text array in the JS file.")

    # 提取陣列內容字符串
    array_content = match.group(1)
    
    # 使用正則表達式提取每一個單引號括起來的經文
    # 匹配: '經文內容',
    # 這裡使用一個更寬鬆的匹配，匹配單引號括起來的任何內容
    verses_raw = re.findall(r"'(.*?)'", array_content)
    
    bible_data = []
    # 經文縮寫對應表 (從 FHL API 的 listall.html 資訊和 CUV 慣例推測)
    book_map = {
        '創': '創世記', '出': '出埃及記', '利': '利未記', '民': '民數記', '申': '申命記',
        '書': '約書亞記', '士': '士師記', '得': '路得記', '撒上': '撒母耳記上', '撒下': '撒母耳記下',
        '王上': '列王紀上', '王下': '列王紀下', '代上': '歷代志上', '代下': '歷代志下', '拉': '以斯拉記',
        '尼': '尼希米記', '斯': '以斯帖記', '伯': '約伯記', '詩': '詩篇', '箴': '箴言',
        '傳': '傳道書', '歌': '雅歌', '賽': '以賽亞書', '耶': '耶利米書', '哀': '耶利米哀歌',
        '結': '以西結書', '但': '但以理書', '何': '何西阿書', '珥': '約珥書', '摩': '阿摩司書',
        '俄': '俄巴底亞書', '拿': '約拿書', '彌': '彌迦書', '鴻': '那鴻書', '哈': '哈巴谷書',
        '番': '西番雅書', '哈': '哈該書', '亞': '撒迦利亞書', '瑪': '瑪拉基書',
        # 新約
        '太': '馬太福音', '可': '馬可福音', '路': '路加福音', '約': '約翰福音', '徒': '使徒行傳',
        '羅': '羅馬書', '林前': '哥林多前書', '林後': '哥林多後書', '加': '加拉太書', '弗': '以弗所書',
        '腓': '腓立比書', '西': '歌羅西書', '帖前': '帖撒羅尼迦前書', '帖後': '帖撒羅尼迦後書',
        '提前': '提摩太前書', '提後': '提摩太後書', '多': '提多書', '門': '腓利門書', '來': '希伯來書',
        '雅': '雅各書', '彼前': '彼得前書', '彼後': '彼得後書', '約一': '約翰一書', '約二': '約翰二書',
        '約三': '約翰三書', '猶': '猶大書', '啟': '啟示錄'
    }

    for verse_line in verses_raw:
        # 匹配: 創1:1 經文內容
        # 經文行可能包含換行符，需要清理
        verse_line = verse_line.strip().replace('\\n', ' ')
        match = re.match(r'([^\d:]+)(\d+):(\d+)\s*(.*)', verse_line)
        if match:
            book_abbr, chapter, verse, text = match.groups()
            book_name = book_map.get(book_abbr, book_abbr)
            bible_data.append({
                'book_abbr': book_abbr,
                'book': book_name,
                'chapter': int(chapter),
                'verse': int(verse),
                'text': text.strip()
            })
        elif verse_line:
            print(f"Skipping malformed line: {verse_line}")

    return pd.DataFrame(bible_data)

# --- 2. 讀經計畫生成 (與前次相同，不再重複) ---

def get_book_abbr(df, book, chapter):
    """根據書卷名和章節號獲取書卷縮寫"""
    try:
        return df[(df['book'] == book) & (df['chapter'] == chapter)]['book_abbr'].iloc[0]
    except IndexError:
        return None

def generate_canonical_plan(df):
    """生成按卷順序讀經計畫 (每日約 3 章)"""
    print("Generating Canonical Plan...")
    
    # 獲取所有書卷和章節，並保持順序
    all_chapters_df = df.groupby(['book', 'chapter']).first().reset_index()[['book', 'chapter', 'book_abbr']]
    all_chapters = list(all_chapters_df.itertuples(index=False, name=None))
            
    total_chapters = len(all_chapters)
    total_days = 365
    
    # 計算平均每天應讀的章節數
    avg_chapters_per_day = total_chapters / total_days
    
    plan_data = []
    current_chapter_index = 0
    
    for day in range(1, total_days + 1):
        readings = []
        
        # 計算今天應該讀多少章 (確保總數接近平均)
        target_index = round(avg_chapters_per_day * day)
        chapters_to_read = target_index - current_chapter_index
        chapters_to_read = max(1, chapters_to_read) # 確保至少讀一章 (除非已讀完)
        
        # 避免讀超過總章節數
        if current_chapter_index + chapters_to_read > total_chapters:
            chapters_to_read = total_chapters - current_chapter_index

        
        for _ in range(chapters_to_read):
            if current_chapter_index < total_chapters:
                book, chap, book_abbr = all_chapters[current_chapter_index]
                readings.append((book_abbr, chap))
                current_chapter_index += 1
            else:
                break
        
        reading_str = "休息日/補讀"
        if readings:
            # 格式化為範圍，例如: 創1, 創2, 創3 -> 創1-3
            formatted_readings = []
            
            if not readings:
                continue

            current_book_abbr, current_chap = readings[0]
            start_chap = current_chap
            
            for i in range(1, len(readings)):
                next_book_abbr, next_chap = readings[i]
                
                if next_book_abbr == current_book_abbr and next_chap == current_chap + 1:
                    current_chap = next_chap
                else:
                    if start_chap == current_chap:
                        formatted_readings.append(f"{current_book_abbr}{start_chap}")
                    else:
                        formatted_readings.append(f"{current_book_abbr}{start_chap}-{current_chap}")
                    
                    current_book_abbr = next_book_abbr
                    current_chap = next_chap
                    start_chap = current_chap
            
            # 處理最後一個範圍
            if start_chap == current_chap:
                formatted_readings.append(f"{current_book_abbr}{start_chap}")
            else:
                formatted_readings.append(f"{current_book_abbr}{start_chap}-{current_chap}")
            
            reading_str = ";".join(formatted_readings)

        plan_data.append({
            'plan_type': 'Canonical',
            'day_number': day,
            'readings': reading_str
        })
        
        if current_chapter_index >= total_chapters:
            break
            
    # 填充剩餘天數為休息日
    while len(plan_data) < total_days:
        plan_data.append({
            'plan_type': 'Canonical',
            'day_number': len(plan_data) + 1,
            'readings': "休息日/補讀"
        })
        
    return pd.DataFrame(plan_data)

def generate_balanced_plan(df):
    """生成平衡讀經計畫 (近似麥琴，每日舊約+新約+詩篇/箴言)"""
    print("Generating Balanced Plan...")
    
    # 獲取所有書卷和章節，並保持順序
    all_chapters_df = df.groupby(['book', 'chapter']).first().reset_index()[['book', 'chapter', 'book_abbr']]
    
    # 劃分舊約、新約、詩篇/箴言
    ot_books = ['創', '出', '利', '民', '申', '書', '士', '得', '撒上', '撒下', '王上', '王下', '代上', '代下', '拉', '尼', '斯', '伯', '賽', '耶', '哀', '結', '但', '何', '珥', '摩', '俄', '拿', '彌', '鴻', '哈', '番', '哈', '亞', '瑪']
    nt_books = ['太', '可', '路', '約', '徒', '羅', '林前', '林後', '加', '弗', '腓', '西', '帖前', '帖後', '提前', '提後', '多', '門', '來', '雅', '彼前', '彼後', '約一', '約二', '約三', '猶', '啟']
    
    ot_chapters = all_chapters_df[all_chapters_df['book_abbr'].isin(ot_books)].itertuples(index=False, name=None)
    nt_chapters = all_chapters_df[all_chapters_df['book_abbr'].isin(nt_books)].itertuples(index=False, name=None)
    psalms_chapters = all_chapters_df[all_chapters_df['book_abbr'] == '詩'].itertuples(index=False, name=None)
    proverbs_chapters = all_chapters_df[all_chapters_df['book_abbr'] == '箴'].itertuples(index=False, name=None)
    
    ot_list = list(ot_chapters)
    nt_list = list(nt_chapters)
    psalms_list = list(psalms_chapters)
    proverbs_list = list(proverbs_chapters)
    
    ot_idx, nt_idx, ps_idx, pr_idx = 0, 0, 0, 0
    
    plan_data = []
    
    for day in range(1, 366):
        readings = []
        
        # 1. 舊約 (2 章/天)
        for _ in range(2):
            if ot_idx < len(ot_list):
                book_abbr = get_book_abbr(df, ot_list[ot_idx][0], ot_list[ot_idx][1])
                readings.append(f"{book_abbr}{ot_list[ot_idx][1]}")
                ot_idx += 1
        
        # 2. 新約 (1 章/天)
        if nt_idx < len(nt_list):
            book_abbr = get_book_abbr(df, nt_list[nt_idx][0], nt_list[nt_idx][1])
            readings.append(f"{book_abbr}{nt_list[nt_idx][1]}")
            nt_idx += 1
        
        # 3. 詩篇/箴言 (輪流)
        if day % 7 == 0: # 每週一天箴言
            if pr_idx < len(proverbs_list):
                book_abbr = get_book_abbr(df, proverbs_list[pr_idx][0], proverbs_list[pr_idx][1])
                readings.append(f"{book_abbr}{proverbs_list[pr_idx][1]}")
                pr_idx += 1
            else:
                pr_idx = 0 # 箴言讀完，從頭開始
                book_abbr = get_book_abbr(df, proverbs_list[pr_idx][0], proverbs_list[pr_idx][1])
                readings.append(f"{book_abbr}{proverbs_list[pr_idx][1]}")
                pr_idx += 1
        else: # 其他天詩篇
            if ps_idx < len(psalms_list):
                book_abbr = get_book_abbr(df, psalms_list[ps_idx][0], psalms_list[ps_idx][1])
                readings.append(f"{book_abbr}{psalms_list[ps_idx][1]}")
                ps_idx += 1
            else:
                ps_idx = 0 # 詩篇讀完，從頭開始
                book_abbr = get_book_abbr(df, psalms_list[ps_idx][0], psalms_list[ps_idx][1])
                readings.append(f"{book_abbr}{psalms_list[ps_idx][1]}")
                ps_idx += 1

        # 格式化閱讀範圍
        reading_str = ";".join(readings)

        plan_data.append({
            'plan_type': 'Balanced',
            'day_number': day,
            'readings': reading_str
        })
        
        if ot_idx >= len(ot_list) and nt_idx >= len(nt_list):
            break
            
    # 填充剩餘天數為休息日
    while len(plan_data) < 365:
        plan_data.append({
            'plan_type': 'Balanced',
            'day_number': len(plan_data) + 1,
            'readings': "休息日/補讀"
        })
        
    return pd.DataFrame(plan_data)


# --- 3. 執行主邏輯 ---

if __name__ == "__main__":
    # 1. 提取聖經經文
    try:
        # 確保 data 目錄存在
        import os
        os.makedirs('data', exist_ok=True)
        
        bible_df = extract_bible_text()
        
        # 過濾掉沒有經文內容的行
        bible_df = bible_df[bible_df['text'].str.strip() != '']
        
        bible_df['id'] = bible_df.index + 1
        bible_df = bible_df[['id', 'book_abbr', 'book', 'chapter', 'verse', 'text']]
        bible_df.to_csv('data/bible_text.csv', index=False)
        print(f"Bible text extracted and saved to data/bible_text.csv. Total verses: {len(bible_df)}")

        # 2. 生成讀經計畫
        canonical_plan_df = generate_canonical_plan(bible_df)
        balanced_plan_df = generate_balanced_plan(bible_df)
        
        plans_df = pd.concat([canonical_plan_df, balanced_plan_df], ignore_index=True)
        plans_df.to_csv('data/bible_plans.csv', index=False)
        print(f"Bible plans saved to data/bible_plans.csv. Total entries: {len(plans_df)}")

    except Exception as e:
        print(f"An error occurred: {e}")
