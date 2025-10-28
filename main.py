import os
import json
import re
from datetime import date, timedelta
from typing import Annotated

from fastapi import FastAPI, Request, HTTPException, Depends
from linebot.v3 import WebhookHandler
# --- (修正) 匯入 QuickReply 和 FlexMessage 按鈕相關模組 ---
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage, 
    FlexMessage, PushMessageRequest, QuickReply, QuickReplyItem, MessageAction,
    # --- (FlexMessage 相關模組) ---
    FlexContainer, FlexBubble, FlexBox, FlexText, FlexButton, URIAction, 
    FlexSeparator
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, FollowEvent, PostbackEvent

from database import init_db, get_db, User, BiblePlan, BibleText
from quiz_generator import generate_quiz_for_user, process_quiz_answer, get_daily_reading_text, get_random_encouraging_verse
from api_routes import router as api_router
from admin_routes import router as admin_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# --- 環境變數設定 ---
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "YOUR_CHANNEL_SECRET")

# --- LINE Bot 初始化 ---
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = FastAPI()

# 包含 API 路由
app.include_router(api_router)
app.include_router(admin_router)

# 靜態檔案服務
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"Warning: Could not mount static directory: {e}")

# 在應用啟動時執行一次資料庫初始化
@app.on_event("startup")
async def startup_event():
    print("Application startup: Checking Firestore database...")
    # 注意：首次啟動時如果需要匯入資料，可能會超時
    # 建議先使用 import_data_to_firestore.py 手動匯入資料
    init_db()

# --- 聖經書卷對照表 ---
BIBLE_BOOK_MAP = {
    # 舊約 (Old Testament)
    "創": {"full": "創世記", "code": "GEN"},
    "出": {"full": "出埃及記", "code": "EXO"},
    "利": {"full": "利未記", "code": "LEV"},
    "民": {"full": "民數記", "code": "NUM"},
    "申": {"full": "申命記", "code": "DEU"},
    "書": {"full": "約書亞記", "code": "JOS"},
    "士": {"full": "士師記", "code": "JDG"},
    "得": {"full": "路得記", "code": "RUT"},
    "撒上": {"full": "撒母耳記上", "code": "1SA"},
    "撒下": {"full": "撒母耳記下", "code": "2SA"},
    "王上": {"full": "列王紀上", "code": "1KI"},
    "王下": {"full": "列王紀下", "code": "2KI"},
    "代上": {"full": "歷代志上", "code": "1CH"},
    "代下": {"full": "歷代志下", "code": "2CH"},
    "拉": {"full": "以斯拉記", "code": "EZR"},
    "尼": {"full": "尼希米記", "code": "NEH"},
    "斯": {"full": "以斯帖記", "code": "EST"},
    "伯": {"full": "約伯記", "code": "JOB"},
    "詩": {"full": "詩篇", "code": "PSA"},
    "箴": {"full": "箴言", "code": "PRO"},
    "傳": {"full": "傳道書", "code": "ECC"},
    "歌": {"full": "雅歌", "code": "SNG"},
    "賽": {"full": "以賽亞書", "code": "ISA"},
    "耶": {"full": "耶利米書", "code": "JER"},
    "哀": {"full": "耶利米哀歌", "code": "LAM"},
    "結": {"full": "以西結書", "code": "EZK"},
    "但": {"full": "但以理書", "code": "DAN"},
    "何": {"full": "何西阿書", "code": "HOS"},
    "珥": {"full": "約珥書", "code": "JOL"},
    "摩": {"full": "阿摩司書", "code": "AMO"},
    "俄": {"full": "俄巴底亞書", "code": "OBA"},
    "拿": {"full": "約拿書", "code": "JON"},
    "彌": {"full": "彌迦書", "code": "MIC"},
    "鴻": {"full": "那鴻書", "code": "NAM"},
    "哈": {"full": "哈巴谷書", "code": "HAB"},
    "番": {"full": "西番雅書", "code": "ZEP"},
    "該": {"full": "哈該書", "code": "HAG"},
    "亞": {"full": "撒迦利亞書", "code": "ZEC"},
    "瑪": {"full": "瑪拉基書", "code": "MAL"},
    # 新約 (New Testament)
    "太": {"full": "馬太福音", "code": "MAT"},
    "可": {"full": "馬可福音", "code": "MRK"},
    "路": {"full": "路加福音", "code": "LUK"},
    "約": {"full": "約翰福音", "code": "JHN"},
    "徒": {"full": "使徒行傳", "code": "ACT"},
    "羅": {"full": "羅馬書", "code": "ROM"},
    "林前": {"full": "哥林多前書", "code": "1CO"},
    "林後": {"full": "哥林多後書", "code": "2CO"},
    "加": {"full": "加拉太書", "code": "GAL"},
    "弗": {"full": "以弗所書", "code": "EPH"},
    "腓": {"full": "腓立比書", "code": "PHP"},
    "西": {"full": "歌羅西書", "code": "COL"},
    "帖前": {"full": "帖撒羅尼迦前書", "code": "1TH"},
    "帖後": {"full": "帖撒羅尼迦後書", "code": "2TH"},
    "提前": {"full": "提摩太前書", "code": "1TI"},
    "提後": {"full": "提摩太後書", "code": "2TI"},
    "多": {"full": "提多書", "code": "TIT"},
    "門": {"full": "腓利門書", "code": "PHM"},
    "來": {"full": "希伯來書", "code": "HEB"},
    "雅": {"full": "雅各書", "code": "JAS"},
    "彼前": {"full": "彼得前書", "code": "1PE"},
    "彼後": {"full": "彼得後書", "code": "2PE"},
    "約一": {"full": "約翰壹書", "code": "1JN"},
    "約二": {"full": "約翰貳書", "code": "2JN"},
    "約三": {"full": "約翰參書", "code": "3JN"},
    "猶": {"full": "猶大書", "code": "JUD"},
    "啟": {"full": "啟示錄", "code": "REV"}
}

# --- 經文解析器 ---
sorted_book_abbrevs = sorted(BIBLE_BOOK_MAP.keys(), key=len, reverse=True)
book_pattern = re.compile(f"({'|'.join(re.escape(abbrev) for abbrev in sorted_book_abbrevs)})")

def parse_readings(readings_str: str) -> list[dict]:
    """
    將 '斯1;斯2;弗1;詩1' 或 '創1-3' 這類的字串，
    解析為包含全名和網址的字典列表。
    """
    parsed_list = []
    parts = readings_str.split(';') # 用分號拆分
    
    current_book_abbrev = None
    current_book_info = None

    for part in parts:
        if not part:
            continue
            
        match = book_pattern.match(part)
        chapter_str = ""
        
        if match:
            current_book_abbrev = match.group(1)
            current_book_info = BIBLE_BOOK_MAP.get(current_book_abbrev)
            chapter_str = part[len(current_book_abbrev):].strip()
        else:
            chapter_str = part.strip()

        if not current_book_info:
            parsed_list.append({"full_name": part, "chapter_display": "", "url": None})
            continue

        if not chapter_str:
            continue
            
        chapter_for_url_match = re.match(r"(\d+)", chapter_str)
        chapter_for_url = "1" 
        if chapter_for_url_match:
            chapter_for_url = chapter_for_url_match.group(1)
            
        url = f"https://www.bible.com/bible/46/{current_book_info['code']}.{chapter_for_url}.CUNP"
        
        parsed_list.append({
            "full_name": current_book_info["full"],
            "chapter_display": chapter_str, 
            "url": url
        })

    return parsed_list

# --- 依賴項 ---
def get_messaging_api():
    with ApiClient(configuration) as api_client:
        yield MessagingApi(api_client)

# --- 輔助函數 ---

def send_message(line_user_id: str, messages: list[TextMessage | FlexMessage], messaging_api: MessagingApi):
    """發送訊息給指定使用者"""
    try:
        messaging_api.push_message(
            PushMessageRequest(
                to=line_user_id,
                messages=messages
            )
        )
    except Exception as e:
        print(f"Error sending message to {line_user_id}: {e}")


def get_all_users_with_plan():
    """獲取所有已選擇讀經計畫的使用者"""
    from database import db, USERS_COLLECTION
    users_ref = db.collection(USERS_COLLECTION)
    query = users_ref.where('plan_type', '!=', None)
    docs = query.stream()
    
    users = []
    for doc in docs:
        data = doc.to_dict()
        user = User(
            line_user_id=data['line_user_id'],
            plan_type=data.get('plan_type'),
            start_date=data.get('start_date'),
            current_day=data.get('current_day', 1),
            last_read_date=data.get('last_read_date'),
            quiz_state=data.get('quiz_state', 'IDLE'),
            quiz_data=data.get('quiz_data', '{}')
        )
        user._doc_id = doc.id
        users.append(user)
    
    return users

def get_current_reading_plan(db, user: User) -> str:
    """獲取使用者當天的讀經計畫內容 (原始字串)"""
    plan = BiblePlan.get_by_plan_and_day(user.plan_type, user.current_day)
    
    if plan:
        return plan
    return "今日無讀經計畫或計畫已完成。"

def get_reading_plan_message(user: User, readings: str) -> FlexMessage:
    """(已修正) 生成讀經計畫的 FlexMessage，包含大按鈕"""
    plan_name = "按卷順序計畫" if user.plan_type == "Canonical" else "平衡讀經計畫"
    
    parsed_readings = parse_readings(readings)
    body_contents = []
    
    body_contents.append(FlexText(
        text="今天的讀經範圍是：",
        size="md",
        color="#555555",
        margin="md"
    ))
    
    for i, reading in enumerate(parsed_readings):
        if i > 0:
            body_contents.append(FlexSeparator(margin="md"))
            
        if reading["url"]:
            body_contents.append(FlexBox(
                layout="horizontal",
                margin="md",
                spacing="md",
                contents=[
                    FlexText(
                        text=f"{reading['full_name']} {reading['chapter_display']}",
                        size="lg",
                        weight="bold",
                        color="#111111",
                        gravity="center",
                        flex=4
                    ),
                    FlexButton(
                        action=URIAction(
                            label="閱讀",
                            uri=reading["url"]
                        ),
                        style="link",
                        height="sm",
                        gravity="center",
                        flex=1
                    )
                ]
            ))
        else:
            body_contents.append(FlexText(
                text=reading["full_name"], 
                size="lg",
                weight="bold",
                color="#111111",
                margin="md",
                wrap=True
            ))

    body_contents.append(FlexSeparator(margin="xl"))
    body_contents.append(FlexText(
        text="請您在讀完後，點擊下方按鈕來進行今日的經文測驗！",
        wrap=True,
        size="sm",
        color="#555555",
        margin="lg"
    ))
    
    # 4. 組裝 Flex Message
    bubble = FlexBubble(
        header=FlexBox(
            layout="vertical",
            contents=[
                FlexText(
                    text=f"【{plan_name} - 第 {user.current_day} 天】",
                    weight="bold",
                    size="xl",
                    color="#FFFFFF"
                )
            ],
            backgroundColor="#0066cc", # 藍色標頭
            paddingAll="lg"
        ),
        body=FlexBox(
            layout="vertical",
            contents=body_contents
        ),
        # --- (修正) 將按鈕移至 footer，並放大上色 ---
        footer=FlexBox(
            layout="vertical",
            spacing="sm",
            contents=[
                FlexButton(
                    action=MessageAction(
                        label="✅ 回報已完成讀經", # <--- (修正文字)
                        text="回報已完成讀經" # <--- (修正文字)
                    ),
                    style="primary", # 顯眼的樣式
                    color="#0066cc", # 藍色按鈕
                    height="md" # 中等高度
                )
            ],
            paddingAll="md" # 增加底部邊距
        )
    )

    return FlexMessage(
        alt_text=f"讀經計畫第 {user.current_day} 天：{readings}", # 這是給推播通知看的
        contents=bubble
        # --- (修正) QuickReply 已被移除，移至 footer ---
    )

# --- LINE Event Handlers ---

@handler.add(FollowEvent)
def handle_follow(event):
    """(已修正) 處理使用者加入好友事件，使用按鈕選擇計畫"""
    db = next(get_db())
    line_user_id = event.source.user_id
    
    user = User.get_by_line_user_id(line_user_id)
    
    if not user:
        new_user = User(line_user_id=line_user_id, plan_type=None)
        new_user.save()
    
    welcome_message = TextMessage(text="歡迎加入一年讀經計畫！\n\n請先選擇您想進行的讀經計畫：")
    
    plan_selection_message = TextMessage(
        text="請選擇您的讀經計畫：\n\n"
             "1. 按卷順序計畫 (Canonical)：從創世記到啟示錄，一年讀完一遍。\n"
             "2. 平衡讀經計畫 (Balanced)：每日搭配舊約、新約、詩篇/箴言，一年讀完一遍。",
        quick_reply=QuickReply(
            items=[
                QuickReplyItem(
                    action=MessageAction(label="1. 按卷順序計畫", text="1")
                ),
                QuickReplyItem(
                    action=MessageAction(label="2. 平衡讀經計畫", text="2")
                )
            ]
        )
    )
    
    messaging_api: MessagingApi = next(get_messaging_api())
    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[welcome_message, plan_selection_message]
        )
    )


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """(已修正) 處理文字訊息事件 (邏輯與之前相同，但現在由按鈕觸發)"""
    text = event.message.text.strip()
    line_user_id = event.source.user_id
    db = next(get_db())
    user = User.get_by_line_user_id(line_user_id)
    messaging_api: MessagingApi = next(get_messaging_api())
    
    if not user:
        handle_follow(event)
        return

    # --- 處理「計畫選擇」的文字回覆 ("1" 或 "2") ---
    if not user.plan_type:
        selected_plan = None
        plan_name = ""
        
        if text == "1":
            selected_plan = "Canonical"
            plan_name = "按卷順序計畫"
        elif text == "2":
            selected_plan = "Balanced"
            plan_name = "平衡讀經計畫"
        
        if selected_plan:
            user.plan_type = selected_plan
            user.start_date = date.today()
            user.current_day = 1
            user.save()
            
            reply_text = f"太棒了！您已選擇「{plan_name}」。\n\n我們將從今天 (第 1 天) 開始！"
            
            readings = get_current_reading_plan(db, user)
            plan_message = get_reading_plan_message(user, readings) 
            
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text), plan_message] 
                )
            )
        else:
            handle_follow(event)
        
        return 

    # --- (修正) 處理「回報讀經」的文字回覆 ---
    # 增加 "✅ 回報已完成讀經" 的選項
    report_keywords = ["回報讀經", "已讀完", "開始測驗", "回報已完成讀經", "✅ 回報已完成讀經"]
    if text in report_keywords:
        # 檢查今天是否已完成測驗
        if user.last_read_date == date.today():
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="您今天已經回報並完成測驗了喔！請明天再回來繼續讀經。")]
                )
            )
            return
            
        # 檢查是否有未完成的測驗
        if user.quiz_state == "WAITING_ANSWER":
            quiz_data = json.loads(user.quiz_data)
            current_question_index = quiz_data.get("current_question_index", 0)
            current_question = quiz_data["questions"][current_question_index]
            
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"您還有未完成的測驗！\n\n{current_question['quiz_text']}\n\n請輸入您的答案。")]
                )
            )
            return
            
        # 開始生成測驗
        try:
            quiz_data, first_question_message = generate_quiz_for_user(user)
            
            user.quiz_state = "WAITING_ANSWER"
            user.quiz_data = json.dumps(quiz_data)
            user.save()
            
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="太棒了！讓我們來進行今天的經文小測驗。"), first_question_message]
                )
            )
        except Exception as e:
            print(f"Error generating quiz: {e}")
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="抱歉，生成測驗時發生錯誤。請稍後再試。")]
                )
            )
        return

    # --- 處理測驗答案 ---
    if user.quiz_state == "WAITING_ANSWER":
        reply_messages = process_quiz_answer(user, text)
        
        # 檢查是否完成測驗
        if user.quiz_state == "QUIZ_COMPLETED":
            user.last_read_date = date.today()
            user.current_day += 1 
            user.quiz_state = "IDLE"
            user.quiz_data = "{}"
            user.save()
            
            next_day_user = User.get_by_line_user_id(line_user_id)
            next_day_readings = get_current_reading_plan(db, next_day_user)
            next_day_message = get_reading_plan_message(next_day_user, next_day_readings) 
            
            reply_messages.append(TextMessage(text="恭喜您！今天的讀經與測驗都完成了！\n\n這是您明天的讀經計畫："))
            reply_messages.append(next_day_message)
        else:
            user.save() 
            
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=reply_messages
            )
        )
        return

    # --- 預設回覆 ---
    # (修正) 更新預設回覆的提示文字
    default_message_text = "我不太明白您的意思。請點擊「回報已完成讀經」按鈕來開始今天的測驗。"
    
    if user.plan_type and user.quiz_state == "IDLE" and user.last_read_date != date.today():
         readings = get_current_reading_plan(db, user)
         plan_message = get_reading_plan_message(user, readings) 
         messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=default_message_text), plan_message]
            )
        )
    else:
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=default_message_text)]
            )
        )


# --- FastAPI 路由 ---

@app.post("/webhook")
async def handle_webhook(request: Request):
    """LINE Bot Webhook 入口"""
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    
    try:
        handler.handle(body.decode(), signature)
    except HTTPException as e:
        print(f"HTTPException: {e}")
        raise e
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    return "OK"

@app.get("/")
def read_root():
    """根路由，重定向到管理後台"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/admin/index.html")

# --- 排程任務 (用於每日推送) ---

@app.post("/schedule/daily_push/{push_time}")
def daily_push(push_time: str, db = Depends(get_db), messaging_api: MessagingApi = Depends(get_messaging_api)):
    """
    定時推送讀經計畫或提醒給使用者。
    """
    
    users = get_all_users_with_plan()
    
    pushed_count = 0
    
    for user in users:
        is_completed = user.last_read_date == date.today()
        
        # ------------------------------------------------------------------
        # 1. 早上 6 點 (morning): 推送當天計畫
        # ------------------------------------------------------------------
        if push_time == 'morning':
            yesterday = date.today() - timedelta(days=1)
            if user.last_read_date is None or user.last_read_date < yesterday:
                 pass
            elif user.last_read_date == yesterday:
                 user.current_day += 1
                 user.save()
            
            readings = get_current_reading_plan(db, user)
            
            message = get_reading_plan_message(user, readings) 
            send_message(user.line_user_id, [message], messaging_api)
            pushed_count += 1
        
        # ------------------------------------------------------------------
        # 2. 中午/傍晚/晚上 (noon, evening, night): 提醒邏輯
        # ------------------------------------------------------------------
        elif push_time in ['noon', 'evening', 'night']:
            if not is_completed:
                readings = get_current_reading_plan(db, user)
                
                if push_time == 'night':
                    encouraging_verse_data = get_random_encouraging_verse()
                    encouraging_text = encouraging_verse_data['text']
                    encouraging_ref = encouraging_verse_data['reference']
                    
                    message_text = (
                        f"【最終提醒：還差一點點！】\n您今天的讀經（{readings}）還沒完成喔！\n\n"
                        f"「{encouraging_text}」({encouraging_ref})\n\n"
                        "願這句經文鼓勵您。請趕快完成，並點擊下方按鈕來回報！" # <--- (修正文字)
                    )
                else:
                    message_text = (
                        f"【讀經提醒】\n別忘了今天的讀經計畫喔！\n範圍：{readings}\n\n"
                        "請讀完後點擊下方按鈕來回報！" # <--- (修正文字)
                    )
                
                # (修正) 提醒訊息也附帶「回報已完成讀經」按鈕
                report_button = QuickReplyItem(
                    action=MessageAction(
                        label="✅ 回報已完成讀經", # <--- (修正文字)
                        text="回報已完成讀經" # <--- (修正文字)
                    )
                )
                send_message(user.line_user_id, [
                    TextMessage(
                        text=message_text, 
                        quick_reply=QuickReply(items=[report_button])
                    )
                ], messaging_api)
                pushed_count += 1

    return {"status": "success", "push_time": push_time, "pushed_count": pushed_count}

