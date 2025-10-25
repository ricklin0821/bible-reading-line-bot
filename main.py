import os
import json
from datetime import date, timedelta
from typing import Annotated

from fastapi import FastAPI, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage, FlexMessage, PushMessageRequest
from linebot.v3.webhooks import MessageEvent, TextMessageContent, FollowEvent, PostbackEvent

from database import init_db, get_db, User, BiblePlan, BibleText
from quiz_generator import generate_quiz_for_user, process_quiz_answer, get_daily_reading_text
from api_routes import router as api_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# --- 環境變數設定 ---
# 請使用者在部署時設定這些變數
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "YOUR_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "YOUR_CHANNEL_SECRET")

# --- LINE Bot 初始化 ---
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = FastAPI()

# 初始化資料庫

# 包含 API 路由
app.include_router(api_router)

# 靜態檔案服務
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    print(f"Warning: Could not mount static directory: {e}")
init_db()

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

def get_current_reading_plan(db: Session, user: User) -> str:
    """獲取使用者當天的讀經計畫內容"""
    plan = db.query(BiblePlan).filter(
        BiblePlan.plan_type == user.plan_type,
        BiblePlan.day_number == user.current_day
    ).first()
    
    if plan:
        return plan.readings
    return "今日無讀經計畫或計畫已完成。"

def get_reading_plan_message(user: User, readings: str) -> TextMessage:
    """生成讀經計畫的訊息"""
    plan_name = "按卷順序計畫" if user.plan_type == "Canonical" else "平衡讀經計畫"
    
    text = (
        f"【{plan_name} - 第 {user.current_day} 天】\n\n"
        f"今天的讀經範圍是：\n**{readings}**\n\n"
        "請您在讀完後，點擊下方選單的「回報讀經」來進行今日的經文測驗！"
    )
    return TextMessage(text=text)

# --- LINE Event Handlers ---

@handler.add(FollowEvent)
def handle_follow(event):
    """處理使用者加入好友事件"""
    db: Session = next(get_db())
    line_user_id = event.source.user_id
    
    user = db.query(User).filter(User.line_user_id == line_user_id).first()
    
    if not user:
        # 創建新使用者，等待選擇計畫
        new_user = User(line_user_id=line_user_id, plan_type=None)
        db.add(new_user)
        db.commit()
    
    # 發送歡迎訊息和計畫選擇 Flex Message
    welcome_message = TextMessage(text="歡迎加入一年讀經計畫！\n\n請先選擇您想進行的讀經計畫：")
    
    # Flex Message for Plan Selection (簡化為文字訊息和 Postback)
    plan_selection_message = TextMessage(
        text="請選擇您的讀經計畫：\n\n"
             "1. 按卷順序計畫 (Canonical)：從創世記到啟示錄，一年讀完一遍。\n"
             "2. 平衡讀經計畫 (Balanced)：每日搭配舊約、新約、詩篇/箴言，一年讀完一遍。\n\n"
             "請回覆「1」或「2」來選擇。",
        quick_reply={
            "items": [
                {
                    "type": "action",
                    "action": {
                        "type": "postback",
                        "label": "1. 按卷順序計畫",
                        "data": "action=select_plan&plan=Canonical"
                    }
                },
                {
                    "type": "action",
                    "action": {
                        "type": "postback",
                        "label": "2. 平衡讀經計畫",
                        "data": "action=select_plan&plan=Balanced"
                    }
                }
            ]
        }
    )
    
    messaging_api: MessagingApi = next(get_messaging_api())
    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[welcome_message, plan_selection_message]
        )
    )

@handler.add(PostbackEvent)
def handle_postback(event):
    """處理 Postback 事件 (例如：選擇讀經計畫)"""
    data = event.postback.data
    params = dict(item.split("=") for item in data.split("&"))
    
    db: Session = next(get_db())
    line_user_id = event.source.user_id
    user = db.query(User).filter(User.line_user_id == line_user_id).first()
    messaging_api: MessagingApi = next(get_messaging_api())
    
    if params.get("action") == "select_plan" and user and not user.plan_type:
        plan_type = params.get("plan")
        if plan_type in ["Canonical", "Balanced"]:
            user.plan_type = plan_type
            user.start_date = date.today()
            user.current_day = 1
            db.commit()
            
            readings = get_current_reading_plan(db, user)
            reading_message = get_reading_plan_message(user, readings)
            
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[
                        TextMessage(text=f"太棒了！您已選擇「{'按卷順序計畫' if plan_type == 'Canonical' else '平衡讀經計畫'}」。\n\n讓我們從今天開始吧！"),
                        reading_message
                    ]
                )
            )
        else:
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text="無效的計畫選擇。請重新選擇。")]
                )
            )

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    """處理文字訊息事件"""
    text = event.message.text.strip()
    line_user_id = event.source.user_id
    db: Session = next(get_db())
    user = db.query(User).filter(User.line_user_id == line_user_id).first()
    messaging_api: MessagingApi = next(get_messaging_api())
    
    if not user or not user.plan_type:
        # 尚未選擇計畫，引導選擇
        handle_follow(event) # 重新發送選擇訊息
        return

    # 處理讀經回報/測驗開始
    if text in ["回報讀經", "已讀完", "開始測驗"]:
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
            quiz_data, first_question_message = generate_quiz_for_user(db, user)
            
            user.quiz_state = "WAITING_ANSWER"
            user.quiz_data = json.dumps(quiz_data)
            db.commit()
            
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

    # 處理測驗答案
    if user.quiz_state == "WAITING_ANSWER":
        reply_messages = process_quiz_answer(db, user, text)
        
        # 檢查是否完成測驗
        if user.quiz_state == "QUIZ_COMPLETED":
            user.last_read_date = date.today()
            user.current_day += 1 # 讀經完成，進入下一天
            user.quiz_state = "IDLE"
            user.quiz_data = "{}"
            db.commit()
            
            # 附帶明天的讀經計畫
            next_day_user = db.query(User).filter(User.line_user_id == line_user_id).first()
            next_day_readings = get_current_reading_plan(db, next_day_user)
            next_day_message = get_reading_plan_message(next_day_user, next_day_readings)
            
            reply_messages.append(TextMessage(text="恭喜您！今天的讀經與測驗都完成了！\n\n這是您明天的讀經計畫："))
            reply_messages.append(next_day_message)
        else:
            db.commit() # 儲存更新後的測驗狀態
            
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=reply_messages
            )
        )
        return

    # 預設回覆
    messaging_api.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="我不太明白您的意思。您可以回覆「回報讀經」來開始今天的測驗，或是回覆「我的計畫」來查看您的讀經進度。")]
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
    """根路由，提供網頁預覽介面"""
    if os.path.exists("index.html"):
        return FileResponse("index.html", media_type="text/html")
    return {"Hello": "Bible Reading Bot is running!"}

# --- 排程任務 (用於每日推送) ---

# 實際部署時，這個函數會被一個外部的排程服務 (如 Celery Beat 或 Cron Job) 定期呼叫
@app.post("/schedule/daily_push")
def daily_push(db: Session = Depends(get_db), messaging_api: MessagingApi = Depends(get_messaging_api)):
    """每日推送讀經計畫給所有使用者"""
    today = date.today()
    
    # 找到所有已選擇計畫的使用者
    users_to_push = db.query(User).filter(User.plan_type.isnot(None)).all()
    
    for user in users_to_push:
        # 檢查使用者是否已經在今天回報讀經，如果已經回報，則不推送
        if user.last_read_date == today:
            continue
            
        readings = get_current_reading_plan(db, user)
        message = get_reading_plan_message(user, readings)
        
        send_message(user.line_user_id, [message], messaging_api)
        
    return {"status": "success", "pushed_count": len(users_to_push)}
