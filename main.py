import os
import json
import re
from datetime import date, datetime, timedelta
from typing import Annotated
from urllib.parse import quote

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

from database import init_db, User, BiblePlan, BibleText
from quiz_generator import generate_quiz_for_user, process_quiz_answer, get_daily_reading_text, get_random_encouraging_verse
from api_routes import router as api_router
from admin_routes import router as admin_router
from admin_auth import router as admin_auth_router
from preview_routes import router as preview_router
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
app.include_router(admin_auth_router)
app.include_router(preview_router)

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
    "創": {"full": "創世記", "code": "GEN", "wd_code": "gen"},
    "出": {"full": "出埃及記", "code": "EXO", "wd_code": "exo"},
    "利": {"full": "利未記", "code": "LEV", "wd_code": "lev"},
    "民": {"full": "民數記", "code": "NUM", "wd_code": "num"},
    "申": {"full": "申命記", "code": "DEU", "wd_code": "deu"},
    "書": {"full": "約書亞記", "code": "JOS", "wd_code": "jos"},
    "士": {"full": "士師記", "code": "JDG", "wd_code": "jdg"},
    "得": {"full": "路得記", "code": "RUT", "wd_code": "rut"},
    "撒上": {"full": "撒母耳記上", "code": "1SA", "wd_code": "1sa"},
    "撒下": {"full": "撒母耳記下", "code": "2SA", "wd_code": "2sa"},
    "王上": {"full": "列王紀上", "code": "1KI", "wd_code": "1ki"},
    "王下": {"full": "列王紀下", "code": "2KI", "wd_code": "2ki"},
    "代上": {"full": "歷代志上", "code": "1CH", "wd_code": "1ch"},
    "代下": {"full": "歷代志下", "code": "2CH", "wd_code": "2ch"},
    "拉": {"full": "以斯拉記", "code": "EZR", "wd_code": "ezr"},
    "尼": {"full": "尼希米記", "code": "NEH", "wd_code": "neh"},
    "斯": {"full": "以斯帖記", "code": "EST", "wd_code": "est"},
    "伯": {"full": "約伯記", "code": "JOB", "wd_code": "job"},
    "詩": {"full": "詩篇", "code": "PSA", "wd_code": "psa"},
    "箴": {"full": "箴言", "code": "PRO", "wd_code": "pro"},
    "傳": {"full": "傳道書", "code": "ECC", "wd_code": "ecc"},
    "歌": {"full": "雅歌", "code": "SNG", "wd_code": "sng"},
    "賽": {"full": "以賽亞書", "code": "ISA", "wd_code": "isa"},
    "耶": {"full": "耶利米書", "code": "JER", "wd_code": "jer"},
    "哀": {"full": "耶利米哀歌", "code": "LAM", "wd_code": "lam"},
    "結": {"full": "以西結書", "code": "EZK", "wd_code": "ezk"},
    "但": {"full": "但以理書", "code": "DAN", "wd_code": "dan"},
    "何": {"full": "何西阿書", "code": "HOS", "wd_code": "hos"},
    "珥": {"full": "約珥書", "code": "JOL", "wd_code": "jol"},
    "摩": {"full": "阿摩司書", "code": "AMO", "wd_code": "amo"},
    "俄": {"full": "俄巴底亞書", "code": "OBA", "wd_code": "oba"},
    "拿": {"full": "約拿書", "code": "JON", "wd_code": "jon"},
    "彌": {"full": "彌迦書", "code": "MIC", "wd_code": "mic"},
    "鴻": {"full": "那鴻書", "code": "NAM", "wd_code": "nam"},
    "哈": {"full": "哈巴谷書", "code": "HAB", "wd_code": "hab"},
    "番": {"full": "西番雅書", "code": "ZEP", "wd_code": "zep"},
    "該": {"full": "哈該書", "code": "HAG", "wd_code": "hag"},
    "亞": {"full": "撒迦利亞書", "code": "ZEC", "wd_code": "zec"},
    "瑪": {"full": "瑪拉基書", "code": "MAL", "wd_code": "mal"},
    # 新約 (New Testament)
    "太": {"full": "馬太福音", "code": "MAT", "wd_code": "mat"},
    "可": {"full": "馬可福音", "code": "MRK", "wd_code": "mrk"},
    "路": {"full": "路加福音", "code": "LUK", "wd_code": "luk"},
    "約": {"full": "約翰福音", "code": "JHN", "wd_code": "jhn"},
    "徒": {"full": "使徒行傳", "code": "ACT", "wd_code": "act"},
    "羅": {"full": "羅馬書", "code": "ROM", "wd_code": "rom"},
    "林前": {"full": "哥林多前書", "code": "1CO", "wd_code": "1co"},
    "林後": {"full": "哥林多後書", "code": "2CO", "wd_code": "2co"},
    "加": {"full": "加拉太書", "code": "GAL", "wd_code": "gal"},
    "弗": {"full": "以弗所書", "code": "EPH", "wd_code": "eph"},
    "腓": {"full": "腓立比書", "code": "PHP", "wd_code": "php"},
    "西": {"full": "歌羅西書", "code": "COL", "wd_code": "col"},
    "帖前": {"full": "帖撒羅尼迦前書", "code": "1TH", "wd_code": "1th"},
    "帖後": {"full": "帖撒羅尼迦後書", "code": "2TH", "wd_code": "2th"},
    "提前": {"full": "提摩太前書", "code": "1TI", "wd_code": "1ti"},
    "提後": {"full": "提摩太後書", "code": "2TI", "wd_code": "2ti"},
    "多": {"full": "提多書", "code": "TIT", "wd_code": "tit"},
    "門": {"full": "腓利門書", "code": "PHM", "wd_code": "phm"},
    "來": {"full": "希伯來書", "code": "HEB", "wd_code": "heb"},
    "雅": {"full": "雅各書", "code": "JAS", "wd_code": "jas"},
    "彼前": {"full": "彼得前書", "code": "1PE", "wd_code": "1pe"},
    "彼後": {"full": "彼得後書", "code": "2PE", "wd_code": "2pe"},
    "約一": {"full": "約翰壹書", "code": "1JN", "wd_code": "1jn"},
    "約二": {"full": "約翰貳書", "code": "2JN", "wd_code": "2jn"},
    "約三": {"full": "約翰參書", "code": "3JN", "wd_code": "3jn"},
    "猶": {"full": "猶大書", "code": "JUD", "wd_code": "jud"},
    "啓": {"full": "啓示錄", "code": "REV", "wd_code": "rev"}
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
            
        # 使用微讀聖經 (wd.bible) 連結
        # 格式：https://wd.bible/tw/bible/{wd_code}.{chapter}.cuvmpt
        wd_code = current_book_info.get('wd_code', '')
        if wd_code:
            url = f"https://wd.bible/tw/bible/{wd_code}.{chapter_for_url}.cuvmpt"
        else:
            # 如果沒有 wd_code，使用 None
            url = None
        
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
    from database import db, USERS_COLLECTION, UserObject
    users_ref = db.collection(USERS_COLLECTION)
    query = users_ref.where('plan_type', '!=', None)
    docs = query.stream()
    
    users = []
    for doc in docs:
        data = doc.to_dict()
        data['_id'] = doc.id
        user = UserObject(data)
        users.append(user)
    
    return users

def get_current_reading_plan(user: User) -> str:
    """獲取使用者當天的讀經計畫內容 (原始字串)"""
    plan = BiblePlan.get_by_day(user.plan_type, user.current_day)
    
    if plan:
        # 確保只回傳讀經範圍字串
        return plan.get('readings', '今日無讀經計畫')
    return "今日無讀經計畫或計畫已完成。"

def get_reading_plan_message(user: User, readings: str) -> FlexMessage:
    """（已修正） 生成讀經計畫的 FlexMessage，包含大按鈕"""
    plan_name = "按卷順序計畫" if user.plan_type == "Canonical" else "平衡讀經計畫"
    
    print(f"[DEBUG] get_reading_plan_message called with readings: '{readings}'")
    
    # 定義分享文字（避免 f-string 中使用反斜線）
    share_text = f"【今日讀經】{readings}\n\n📚 一起加入一年讀經計畫！\n每天讀聖經、做測驗，讓神的話語成為生命的力量。\n\n✨ 搜尋「一年讀經計畫」或請朋友分享 LINE Bot 給你，一起每日讀經！"
    
    parsed_readings = parse_readings(readings)
    print(f"[DEBUG] Parsed readings: {parsed_readings}")
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
            
        # 確保 URL 不為空且以 http 或 https 開頭
        url_valid = reading["url"] and reading["url"].strip() and (reading["url"].startswith("http://") or reading["url"].startswith("https://"))
        print(f"[DEBUG] Reading {i}: url_valid={url_valid}, url={reading.get('url', 'None')}")
        if url_valid:
            # 將整個書卷名稱改為可點擊的按鈕，更明顯且易於點擊
            button_uri = reading["url"]
            print(f"[DEBUG] Creating FlexButton with URI: {button_uri}")
            body_contents.append(FlexButton(
                action=URIAction(
                    label=f"📖 {reading['full_name']} {reading['chapter_display']}",
                    uri=button_uri
                ),
                style="primary",
                color="#667eea",
                height="md",
                margin="md"
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
    # 準備 footer 按鈕
    footer_buttons = [
        FlexButton(
            action=MessageAction(
                label="✅ 回報已完成讀經",
                text="回報已完成讀經"
            ),
            style="primary",
            color="#0066cc",
            height="md"
        )
    ]
    
    # 只有當 readings 不為空時才添加分享按鈕
    if readings and readings.strip():
        try:
            share_uri = f"https://line.me/R/share?text={quote(share_text)}"
            # 驗證 URI 長度（LINE 限制為 1000 字元）
            if len(share_uri) < 1000:
                footer_buttons.append(
                    FlexButton(
                        action=URIAction(
                            label="📤 分享經文",
                            uri=share_uri
                        ),
                        style="link",
                        height="sm"
                    )
                )
        except Exception as e:
            print(f"[WARNING] Failed to create share button: {e}")
    
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
            contents=footer_buttons,
            paddingAll="md"
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
    """（已修正） 處理使用者加入好友事件，使用按鈕選擇計畫"""
    line_user_id = event.source.user_id
    print(f"[DEBUG] New user follow event: {line_user_id}")
    
    # 取得使用者顯示名稱
    messaging_api: MessagingApi = next(get_messaging_api())
    try:
        profile = messaging_api.get_profile(line_user_id)
        display_name = profile.display_name
        print(f"[DEBUG] User display name: {display_name}")
    except Exception as e:
        print(f"[ERROR] Failed to get user profile: {e}")
        display_name = None
    
    try:
        user = User.get_by_line_user_id(line_user_id)
        
        if not user:
            print(f"[DEBUG] Creating new user: {line_user_id}")
            new_user = User.create(line_user_id=line_user_id, plan_type=None)
            if display_name:
                new_user.display_name = display_name
                new_user.save()
            print(f"[DEBUG] New user created successfully")
        elif not user.display_name and display_name:
            # 更新現有使用者的顯示名稱
            print(f"[DEBUG] Updating existing user display name")
            user.display_name = display_name
            user.save()
    except Exception as e:
        print(f"[ERROR] Failed to create/update user: {e}")
        import traceback
        traceback.print_exc()
    
    welcome_message = TextMessage(text="🎉 歡迎加入一年讀經計畫！\n\n🙏 感謝神帶領您來到這裡，讓我們一起透過讀經與神更親近！\n\n📖 請先選擇您想進行的讀經計畫：")
    
    plan_selection_message = TextMessage(
        text="🎯 請選擇您的讀經計畫：\n\n"
             "📘 1. 按卷順序計畫\n從創世記到啟示錄，有系統地一年讀完一遍。\n\n"
             "⚖️ 2. 平衡讀經計畫\n每日搭配舊約、新約、詩篇/箴言，均衡成長！",
        quick_reply=QuickReply(
            items=[
                QuickReplyItem(
                    action=MessageAction(label="1. 按卷順序計畫", text="1")
                ),
                QuickReplyItem(
                    action=MessageAction(label="2. 平衡讀經計畫", text="2")
                ),
                QuickReplyItem(
                    action=MessageAction(label="聯繫作者", text="聯繫作者")
                )
            ]
        )
    )
    
    try:
        messaging_api: MessagingApi = next(get_messaging_api())
        print(f"[DEBUG] Sending welcome message to {line_user_id}")
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[welcome_message, plan_selection_message]
            )
        )
        print(f"[DEBUG] Welcome message sent successfully")
    except Exception as e:
        print(f"[ERROR] Failed to send welcome message: {e}")
        import traceback
        traceback.print_exc()


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """（已修正） 處理文字訊息事件 （邏輯與之前相同，但現在由按鈕觸發）"""
    # 檢查是否為文字訊息，如果不是則忽略
    if not isinstance(event.message, TextMessageContent):
        return
        
    text = event.message.text.strip()
    line_user_id = event.source.user_id
    user = User.get_by_line_user_id(line_user_id)
    messaging_api: MessagingApi = next(get_messaging_api())
    
    # 取得使用者顯示名稱（如果還沒有）
    if user and not user.display_name:
        try:
            profile = messaging_api.get_profile(line_user_id)
            user.display_name = profile.display_name
            user.save()
        except:
            pass
    
    if not user:
        handle_follow(event)
        return

    # --- 處理「聯繫作者」功能 ---
    if text == "聯繫作者":
        # 記錄使用者狀態為等待輸入 EMAIL
        User.update(line_user_id, contact_state="WAITING_EMAIL")
        
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="請輸入您的 Email 信箱：")]
            )
        )
        return
    
    # 處理 EMAIL 輸入
    if user.get('contact_state') == "WAITING_EMAIL":
        # 簡單驗證 email 格式
        if '@' not in text or '.' not in text:
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="Email 格式不正確，請重新輸入：")]
                )
            )
            return
        
        User.update(line_user_id, contact_email=text, contact_state="WAITING_MESSAGE")
        
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="請輸入您想說的話：")]
            )
        )
        return
    
    # 處理訊息內容
    if user.get('contact_state') == "WAITING_MESSAGE":
        contact_email = user.get('contact_email', '未提供')
        contact_message = text
        
        # 清除狀態
        User.update(line_user_id, contact_state="IDLE", contact_email="")
        
        # 發送通知給作者
        author_line_id = "U67da4c26e3706928c2eb77c1fc89b3a9"
        display_name = user.get('display_name', '未知')
        notification_text = f"【使用者聯繫】\n\n姓名：{display_name}\nEmail：{contact_email}\n\n內容：\n{contact_message}"
        
        try:
            send_message(author_line_id, [TextMessage(text=notification_text)], messaging_api)
        except Exception as e:
            print(f"Error sending contact notification: {e}")
        
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="感謝您的聯繫！我們已收到您的訊息，會盡快回覆您。")]
            )
        )
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
            user.start_date = datetime.now()
            user.current_day = 1
            user.save()
            
            reply_text = f"太棒了！您已選擇「{plan_name}」。\n\n我們將從今天 (第 1 天) 開始！"
            
            # 恢復 Flex Message 邏輯，並加入詳細錯誤捕捉
            readings = get_current_reading_plan(user)

            try:
                plan_message = get_reading_plan_message(user, readings) 
                messages_to_send = [TextMessage(text=reply_text), plan_message]
                
                messaging_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=messages_to_send
                    )
                )
            except Exception as e:
                # 捕捉 LINE API 錯誤，並將錯誤訊息發送給使用者
                error_message = f"抱歉，發送讀經計畫時發生錯誤：{e}"
                print(f"LINE API Error during plan selection: {error_message}")
                
                # 嘗試發送一個簡單的錯誤回覆
                try:
                    messaging_api.reply_message(
                        ReplyMessageRequest(
                            reply_token=event.reply_token,
                            messages=[TextMessage(text=error_message)]
                        )
                    )
                except:
                    # 如果連錯誤回覆都失敗，則不採取任何行動
                    pass
            
        else:
            handle_follow(event)
        
        return 

    # --- (修正) 處理「回報讀經」的文字回覆 ---
    # 增加 "✅ 回報已完成讀經" 的選項
    report_keywords = ["回報讀經", "已讀完", "開始測驗", "回報已完成讀經", "✅ 回報已完成讀經"]
    if text in report_keywords:
        # 檢查今天是否已完成測驗
        today_str = datetime.now().date().isoformat()
        # 處理 last_read_date 可能是字串或 date 物件
        last_read_str = user.last_read_date
        if isinstance(last_read_str, date):
            last_read_str = last_read_str.isoformat()
        elif isinstance(last_read_str, datetime):
            last_read_str = last_read_str.date().isoformat()
        
        if last_read_str == today_str:
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="🎉 您今天已經完成所有任務了！\n\n🙏 感謝神，您又完成了一天的屬靈功課！\n\n🌟 明天再回來繼續讀經吧！")]
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
                    messages=[TextMessage(text=f"📝 您還有未完成的測驗！\n\n{current_question['quiz_text']}\n\n💡 請輸入您的答案，繼續加油！")]
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
                    messages=[TextMessage(text="🎉 太棒了！您已經完成今天的讀經！\n\n📝 現在讓我們來進行今天的經文小測驗，加深對神話語的記憶！"), first_question_message]
                )
            )
        except ValueError as e:
            # 資料庫查詢錯誤
            print(f"ValueError generating quiz: {e}")
            import traceback
            traceback.print_exc()
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"抱歉，無法生成測驗。\n\n錯誤訊息：{str(e)}\n\n請聯繫管理員檢查資料庫設定。")]
                )
            )
        except Exception as e:
            print(f"Error generating quiz: {e}")
            import traceback
            traceback.print_exc()
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=f"抱歉，生成測驗時發生錯誤。\n\n錯誤訊息：{str(e)}")]
                )
            )
        return

    # --- 處理測驗答案 ---
    if user.quiz_state == "WAITING_ANSWER":
        reply_messages, user = process_quiz_answer(user, text)
        
        # 檢查是否完成測驗
        if user.quiz_state == "QUIZ_COMPLETED":
            print(f"[DEBUG] Quiz completed for user {line_user_id}")
            user.last_read_date = datetime.now().date().isoformat()  # 轉換為字串以支援 Firestore
            user.current_day += 1 
            print(f"[DEBUG] Updated current_day to {user.current_day}")
            user.quiz_state = "IDLE"
            user.quiz_data = "{}"
            user.save()
            print(f"[DEBUG] User data saved")
        else:
            user.save() 
            
        # 先發送 reply_message（確保使用者收到測驗結果）
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=reply_messages
            )
        )
        
        # 如果測驗完成，使用 push message 發送下一天的讀經計畫
        if user.quiz_state == "IDLE" and user.last_read_date == datetime.now().date().isoformat():
            try:
                next_day_user = User.get_by_line_user_id(line_user_id)
                print(f"[DEBUG] Retrieved next_day_user: current_day={next_day_user.current_day}")
                
                next_day_readings = get_current_reading_plan(next_day_user)
                print(f"[DEBUG] Next day readings: {next_day_readings}")
                
                next_day_message = get_reading_plan_message(next_day_user, next_day_readings)
                print(f"[DEBUG] Next day message generated successfully")
                
                # 使用 push message 發送下一天計畫
                messaging_api.push_message(
                    PushMessageRequest(
                        to=line_user_id,
                        messages=[
                            TextMessage(text="🎉 恭喜您！今天的讀經與測驗都完成了！\n\n👏 您又完成了一天的屬靈功課，感謝神的話語滿足我們的心！\n\n📖 這是您明天的讀經計畫："),
                            next_day_message
                        ]
                    )
                )
                print(f"[DEBUG] Next day plan pushed successfully")
            except Exception as e:
                print(f"[ERROR] Failed to push next day plan: {e}")
                import traceback
                traceback.print_exc()
        
        return

    # --- 預設回覆 ---
    # 根據使用者輸入提供更友善的回應
    
    # 常見問候語和回應
    greetings = ["你好", "哈囉", "hi", "hello", "早安", "晚安", "午安", "嗨嗨"]
    help_keywords = ["幫助", "help", "怎麼用", "如何使用", "功能"]
    
    if text.lower() in greetings:
        greeting_response = (
            f"👋 您好！我是聖經讀經助手\n\n"
            f"😊 很高興能陪伴您一起讀經，讓神的話語成為我們生命的力量！\n\n"
        )
        if not user.plan_type:
            greeting_response += "🎯 請選擇您的讀經計畫：\n📘 1. 按卷順序計畫\n⚖️ 2. 平衡讀經計畫"
        else:
            greeting_response += f"🎉 您正在進行「{user.plan_type}」計畫，目前是第 {user.current_day} 天！\n\n💪 繼續加油，您做得很棒！"
        
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=greeting_response)]
            )
        )
        return
    
    if any(keyword in text for keyword in help_keywords):
        help_response = (
            "📚 聖經讀經助手使用指南\n\n"
            "✨ 主要功能：\n"
            "• 📖 每日讀經計畫推送\n"
            "• 📝 經文測驗與複習\n"
            "• 📊 讀經進度追蹤\n\n"
            "🎯 可用指令：\n"
            "• 發送 '1' 或 '2' - 選擇讀經計畫\n"
            "• 發送 '幫助' - 查看使用指南\n"
            "• 發送 '你好' - 問候與查看進度\n"
            "• 發送 '聯繫作者' - 聯繫系統管理員\n\n"
            "💡 小提示：\n"
            "• 可以隨時點擊經文連結閱讀聖經\n"
            "• 測驗答錯不會影響進度\n"
            "• 可以提前完成多天的讀經\n\n"
            "🙏 願神的話語成為您腳前的燈、路上的光！"
        )
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=help_response)]
            )
        )
        return
    
    # 預設回覆
    default_message_text = "我不太明白您的意思。🤔\n\n發送 '幫助' 查看使用指南，或點擊下方按鈕開始今天的讀經。"
    
    # 修改：無論是否完成，都推送讀經進度
    if user.plan_type and user.quiz_state == "IDLE":
         readings = get_current_reading_plan(user)
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
    """根路由，顯示讀經計畫首頁"""
    return FileResponse("static/index.html", media_type="text/html")

# --- 排程任務 (用於每日推送) ---

@app.post("/schedule/daily_push/{push_time}")
def daily_push(push_time: str, messaging_api: MessagingApi = Depends(get_messaging_api)):
    """
    定時推送讀經計畫或提醒給使用者。
    """
    
    users = get_all_users_with_plan()
    
    pushed_count = 0
    
    for user in users:
        # 修正: 確保日期比較正確（處理 datetime、date 與字串的差異）
        today = datetime.now().date()
        last_read = user.last_read_date
        
        # 處理不同的日期格式
        if isinstance(last_read, str):
            # 如果是字串格式 "2025-11-01"，轉換為 date 物件
            try:
                last_read = datetime.strptime(last_read, "%Y-%m-%d").date()
            except (ValueError, TypeError):
                last_read = date(1970, 1, 1)
        elif isinstance(last_read, datetime):
            last_read = last_read.date()
        elif last_read is None:
            last_read = date(1970, 1, 1) # 設置一個很早的日期，確保第一次使用時不會被誤判為已完成
            
        is_completed = last_read == today
        
        # ------------------------------------------------------------------
        # 1. 早上 6 點 (morning): 推送當天計畫
        # ------------------------------------------------------------------
        if push_time == 'morning':
            # 修正邏輯：如果昨天已經完成並看過今天的計畫，今天早上不推送。
            # 這樣確保：
            # 1. 如果使用者昨天完成讀經，昨天已經看過今天的計畫，今天早上不推送
            # 2. 如果使用者昨天沒完成，今天早上推送今天的計畫
            
            # 確保使用者不會超前 (current_day 最大為 365)
            if user.current_day > 365:
                user.current_day = 365
                user.save()
            
            # 修正邏輯：只有當 last_read_date 不是昨天時，才推送。
            # 如果 last_read_date == 昨天，表示昨天已經完成並看過今天的計畫，不需要再推送。
            yesterday = today - timedelta(days=1)
            if last_read != yesterday:
                readings = get_current_reading_plan(user)
                message = get_reading_plan_message(user, readings) 
                send_message(user.line_user_id, [message], messaging_api)
                pushed_count += 1
        
        # ------------------------------------------------------------------
        # 2. 中午/傍晚/晚上 (noon, evening, night): 提醒邏輯
        # ------------------------------------------------------------------
        elif push_time in ['noon', 'evening', 'night']:
            if not is_completed:
                readings = get_current_reading_plan(user)
                
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

