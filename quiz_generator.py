import re
import random
import json
from typing import Tuple, List, Dict, Any
from linebot.v3.messaging import TextMessage

from database import User, BiblePlan, BibleText

# 鼓勵用的聖經金句範圍 (詩篇、箴言、新約書信等)
ENCOURAGING_REFERENCES = [
    # 詩篇
    ("詩", 23, 1, 1), ("詩", 27, 1, 1), ("詩", 46, 1, 1), ("詩", 121, 1, 1),
    # 箴言
    ("箴", 3, 5, 5), ("箴", 16, 3, 3), ("箴", 18, 10, 10),
    # 新約
    ("太", 6, 33, 33), ("約", 14, 27, 27), ("羅", 8, 28, 28), ("林前", 10, 13, 13),
    ("林後", 12, 9, 9), ("腓", 4, 6, 7), ("腓", 4, 13, 13), ("提後", 1, 7, 7),
    ("來", 10, 24, 25), ("雅", 1, 2, 4), ("彼前", 5, 7, 7)
]

def get_random_encouraging_verse() -> dict:
    """從預設的鼓勵經文範圍中隨機抽取一節經文"""
    
    # 隨機選擇一個經文範圍
    book_abbr, chap, start_v, end_v = random.choice(ENCOURAGING_REFERENCES)
    
    # 在選定的範圍內隨機選擇一節
    verse_num = random.randint(start_v, end_v)
    
    # 從 Firestore 中查詢該節經文
    verse = BibleText.get_verse(book_abbr, chap, verse_num)
    
    if verse:
        return {
            "text": verse['text'],
            "reference": f"{verse['book_abbr']}{verse['chapter']}:{verse['verse']}"
        }
    
    # 如果找不到，則返回一個預設的鼓勵語
    return {
        "text": "你當剛強壯膽，不要懼怕，也不要驚惶,因為你無論往哪裡去，耶和華你的神必與你同在。",
        "reference": "約書亞記 1:9"
    }

# --- 輔助函數 ---

def get_verses_for_reading(reading_ref: str) -> List[Dict[str, Any]]:
    """
    根據經文範圍字串 (例如: '創1:1-3:24;太1:1-2:23') 獲取所有經文。
    返回一個包含 {book_abbr, chapter, verse, text} 的列表。
    """
    all_verses = []
    
    print(f"[DEBUG] get_verses_for_reading called with: {reading_ref}")
    
    # 處理多個閱讀範圍
    refs = reading_ref.split(';')
    print(f"[DEBUG] Split refs: {refs}")
    
    for ref in refs:
        ref = ref.strip()
        if not ref:
            continue
        
        print(f"[DEBUG] Processing ref: {ref}")
            
        # 匹配書卷縮寫和章節範圍 (例如: 創1-3, 太1:1-2:23)
        match = re.match(r'([^\d]+)(\d+)(?::(\d+))?(?:-(\d+)(?::(\d+))?)?', ref)
        print(f"[DEBUG] Match result: {match.groups() if match else None}")
        
        if not match:
            # 處理只有章節的情況 (例如: 創1)
            match_chap = re.match(r'([^\d]+)(\d+)', ref)
            if match_chap:
                book_abbr, chap = match_chap.groups()
                verses = BibleText.get_verses_by_reference(book_abbr, int(chap))
                all_verses.extend(verses)
            continue
            
        book_abbr, start_chap_str, start_verse_str, end_chap_str, end_verse_str = match.groups()
        
        start_chap = int(start_chap_str)
        end_chap = int(end_chap_str) if end_chap_str else start_chap
        start_verse = int(start_verse_str) if start_verse_str else None
        end_verse = int(end_verse_str) if end_verse_str else None
        
        # 使用 Firestore 查詢獲取經文範圍
        if start_chap == end_chap and not start_verse:
            # 單章，無節範圍
            print(f"[DEBUG] Fetching single chapter: {book_abbr} {start_chap}")
            verses = BibleText.get_verses_by_reference(book_abbr, start_chap)
        else:
            # 複雜範圍查詢
            print(f"[DEBUG] Fetching range: {book_abbr} {start_chap}-{end_chap}, verses {start_verse}-{end_verse}")
            verses = BibleText.get_verses_in_range(book_abbr, start_chap, end_chap, start_verse, end_verse)
        
        print(f"[DEBUG] Verses fetched for {ref}: {len(verses)}")
        all_verses.extend(verses)
        
    return all_verses

def create_fill_in_the_blank_quiz(verse_data: Dict[str, Any]) -> Tuple[str, str]:
    """
    根據經文數據生成一個填充題。
    選擇經文中一個關鍵詞或短語進行挖空。
    """
    text = verse_data['text']
    
    # 移除標點符號，方便分詞
    clean_text = re.sub(r'[，。！？：「」；、]', ' ', text)
    words = clean_text.split()
    
    # 過濾掉太短的詞 (例如: 的, 了, 是)
    meaningful_words = [w for w in words if len(w) > 1 and w not in ['的', '了', '是', '在', '我', '你', '他', '她', '它', '這', '那', '與', '和', '都', '就', '又', '從', '到', '為', '因', '以', '所', '將', '必', '要', '向', '說', '看', '聽', '行', '來', '去', '上', '下', '中', '裡', '外', '已', '未', '更', '最']]
    
    if not meaningful_words:
        # 如果沒有足夠的詞，選擇最長的詞
        words_with_punc = re.findall(r'[\w]+|[，。！？：「」；、]', text)
        meaningful_words = sorted([w for w in words_with_punc if re.match(r'[\w]+', w)], key=len, reverse=True)
        if not meaningful_words:
            return text, "無答案" # 實在無法生成題目
        
    # 隨機選擇一個詞作為答案
    answer = random.choice(meaningful_words)
    
    # 挖空題目
    # 使用正則表達式替換，確保只替換第一個出現的詞，避免重複挖空
    quiz_text = re.sub(re.escape(answer), "[___]", text, 1)
    
    # 確保挖空後題目和答案不完全一樣 (例如: 經文只有一個詞)
    if quiz_text == text:
        return text, "無答案" # 實在無法生成題目
        
    return quiz_text, answer

# --- 核心邏輯 ---

def generate_quiz_for_user(user: User) -> Tuple[Dict[str, Any], TextMessage]:
    """
    為使用者生成當天的 3 題填充題測驗。
    返回 quiz_data 字典和第一道題目的 TextMessage。
    """
    
    # 1. 獲取當天的讀經範圍
    print(f"[DEBUG] Generating quiz for user: plan_type={user['plan_type']}, current_day={user['current_day']}")
    plan = BiblePlan.get_by_day(user['plan_type'], user['current_day'])
    print(f"[DEBUG] Plan retrieved: {plan}")
    
    if not plan:
        raise ValueError("No reading plan found for today.")
    
    readings = plan['readings']
    print(f"[DEBUG] Readings: {readings}")
    
    if not readings:
        raise ValueError("No reading plan found for today.")
    
    # 2. 獲取範圍內的所有經文
    print(f"[DEBUG] Fetching verses for readings: {readings}")
    all_verses = get_verses_for_reading(readings)
    print(f"[DEBUG] Total verses fetched: {len(all_verses)}")
    
    if not all_verses:
        raise ValueError("No verses found for today's reading plan.")
        
    # 3. 從中隨機選取 3 節經文作為題目來源
    # 確保選取的經文是獨一無二的，且能生成有效的題目
    selected_verses = []
    attempts = 0
    while len(selected_verses) < 3 and attempts < 100:
        verse = random.choice(all_verses)
        ref = f"{verse['book_abbr']}{verse['chapter']}:{verse['verse']}"
        if ref not in [f"{v['book_abbr']}{v['chapter']}:{v['verse']}" for v in selected_verses]:
            quiz_text, answer = create_fill_in_the_blank_quiz(verse)
            if answer != "無答案":
                verse['quiz_text'] = quiz_text
                verse['answer'] = answer
                selected_verses.append(verse)
        attempts += 1
        
    if len(selected_verses) < 3:
        # 如果無法生成 3 題，則用已生成的題目填充，或簡化處理
        # 這裡假設至少能生成 1 題
        if not selected_verses:
            raise ValueError("Could not generate any valid quiz question.")
        
        # 用第一道題重複填充到 3 題
        while len(selected_verses) < 3:
            selected_verses.append(selected_verses[0])

    # 4. 構建測驗數據結構
    quiz_data = {
        "readings": readings,
        "current_question_index": 0,
        "questions": []
    }
    
    for verse in selected_verses:
        quiz_data["questions"].append({
            "ref": f"{verse['book_abbr']}{verse['chapter']}:{verse['verse']}",
            "quiz_text": verse['quiz_text'],
            "full_verse": verse['text'],
            "answer": verse['answer'],
            "attempts": 0
        })
        
    # 5. 準備第一道題目的訊息
    first_question = quiz_data["questions"][0]
    message_text = (
        f"第 1 題 (共 3 題) - 經文：{first_question['ref']}\n\n"
        f"{first_question['quiz_text']}\n\n"
        "請輸入您認為正確的答案 (詞彙)。"
    )
    first_question_message = TextMessage(text=message_text)
    
    return quiz_data, first_question_message

def process_quiz_answer(user: dict, answer: str) -> tuple:
    """
    處理使用者提交的測驗答案。
    返回 (reply_messages, updated_user) 元組。
    """
    reply_messages = []
    
    try:
        quiz_data = json.loads(user['quiz_data'])
        current_index = quiz_data["current_question_index"]
        question = quiz_data["questions"][current_index]
    except (json.JSONDecodeError, IndexError, KeyError):
        return [TextMessage(text="測驗狀態錯誤，請重新開始測驗。")], user

    correct_answer = question["answer"]
    user_answer = answer.strip()
    
    # 除錯日誌
    print(f"[DEBUG] Answer comparison:")
    print(f"  User answer (raw): '{user_answer}' (length: {len(user_answer)})")
    print(f"  Correct answer (raw): '{correct_answer}' (length: {len(correct_answer)})")
    
    # 移除所有標點符號和空白字元，只比對文字內容
    def clean_answer(text):
        # 移除所有標點符號、空栽、特殊字元
        cleaned = re.sub(r'[\s，。！？：「」；、,\.!\?:;"\'\(\)\[\]\{\}]', '', text)
        return cleaned.lower()
    
    user_answer_clean = clean_answer(user_answer)
    correct_answer_clean = clean_answer(correct_answer)
    
    print(f"  User answer (clean): '{user_answer_clean}' (length: {len(user_answer_clean)})")
    print(f"  Correct answer (clean): '{correct_answer_clean}' (length: {len(correct_answer_clean)})")
    
    # 答案比對
    is_correct = user_answer_clean == correct_answer_clean
    print(f"[DEBUG] Is correct: {is_correct}")
    
    if is_correct:
        # 答對：給予高度肯定與情緒價值
        affirmations = [
            "太棒了！您完全答對了！🎉 您的記憶力真是驚人！",
            "哇！完全正確！💯 真是個愛慕真理、勤奮讀經的好榜樣！",
            "阿們！答案完全正確！🙏 願神的話語常在您心裡！",
            "恭喜您！這題難不倒您！🌟 繼續保持這份對聖經的熱情！"
        ]
        reply_messages.append(TextMessage(text=random.choice(affirmations)))
        
        # 進入下一題
        quiz_data["current_question_index"] += 1
        user['quiz_data'] = json.dumps(quiz_data)
        
        if quiz_data["current_question_index"] < len(quiz_data["questions"]):
            # 還有下一題
            next_index = quiz_data["current_question_index"]
            next_question = quiz_data["questions"][next_index]
            message_text = (
                f"第 {next_index + 1} 題 (共 {len(quiz_data['questions'])} 題) - 經文：{next_question['ref']}\n\n"
                f"{next_question['quiz_text']}\n\n"
                "請輸入您認為正確的答案 (詞彙)。"
            )
            reply_messages.append(TextMessage(text=message_text))
        else:
            # 測驗完成
            user['quiz_state'] = "QUIZ_COMPLETED" # 在 main.py 中會處理後續邏輯
            reply_messages.append(TextMessage(text="所有題目都答對了！您真是太棒了！"))
            
    else:
        # 答錯
        question["attempts"] += 1
        
        if question["attempts"] == 1:
            # 第一次答錯：回應填充題的經文，再次詢問答案
            message_text = (
                f"再想想看喔！😊\n\n"
                f"這節經文是：{question['full_verse']}\n\n"
                f"請問：{question['quiz_text']}\n\n"
                "請再次輸入您的答案。"
            )
            reply_messages.append(TextMessage(text=message_text))
            
        elif question["attempts"] == 2:
            # 第二次答錯：出示答案，並給予鼓勵
            message_text = (
                f"沒關係，再接再勵！💪\n\n"
                f"正確答案是：**{correct_answer}**\n\n"
                f"完整的經文是：{question['full_verse']}\n\n"
            )
            reply_messages.append(TextMessage(text=message_text))
            
            # 自動進入下一題
            quiz_data["current_question_index"] += 1
            # 立即更新 quiz_data，確保狀態同步
            user['quiz_data'] = json.dumps(quiz_data)
            
            if quiz_data["current_question_index"] < len(quiz_data["questions"]):
                # 還有下一題
                next_index = quiz_data["current_question_index"]
                next_question = quiz_data["questions"][next_index]
                message_text = (
                    f"讓我們繼續下一題吧！\n\n"
                    f"第 {next_index + 1} 題 (共 {len(quiz_data['questions'])} 題) - 經文：{next_question['ref']}\n\n"
                    f"{next_question['quiz_text']}\n\n"
                    "請輸入您認為正確的答案 (詞彙)。"
                )
                reply_messages.append(TextMessage(text=message_text))
            else:
                # 測驗完成 (雖然有錯，但題目已結束)
                user['quiz_state'] = "QUIZ_COMPLETED" # 在 main.py 中會處理後續邏輯
                reply_messages.append(TextMessage(text="今天的測驗結束了！無論結果如何，您願意花時間讀經和學習，就是最棒的！願神祝福您！"))
        else:
            # 更新測驗數據（第一次答錯的情況）
            user['quiz_data'] = json.dumps(quiz_data)
        
    return reply_messages, user
    
def get_daily_reading_text(readings: str) -> str:
    """
    根據經文範圍字串獲取經文內容，用於每日推送。
    """
    all_verses = get_verses_for_reading(readings)
    
    if not all_verses:
        return "今日經文範圍無法取得。"
        
    text_parts = []
    current_ref = ""
    
    for verse in all_verses:
        ref = f"{verse['book_abbr']}{verse['chapter']}:{verse['verse']}"
        
        # 檢查是否為新的一章或新的書卷
        new_ref = f"{verse['book_abbr']}{verse['chapter']}"
        if new_ref != current_ref:
            text_parts.append(f"\n**{new_ref}**\n")
            current_ref = new_ref
            
        text_parts.append(f"  {verse['verse']} {verse['text']}")
        
    return "".join(text_parts)

