"""
讀經計畫預覽路由
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import csv
import os

router = APIRouter()

def load_bible_plans():
    """載入讀經計畫資料"""
    plans = {'Canonical': [], 'Balanced': []}
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'bible_plans.csv')
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            plan_type = row['plan_type']
            day = int(row['day_number'])
            readings = row['readings']
            
            if plan_type in plans:
                plans[plan_type].append({
                    'day': day,
                    'readings': readings
                })
    
    return plans

@router.get("/api/bible-plans/{plan_type}")
async def get_bible_plan(plan_type: str):
    """取得指定類型的讀經計畫"""
    try:
        plans = load_bible_plans()
        
        if plan_type not in plans:
            return JSONResponse(
                status_code=404,
                content={"error": "Plan type not found"}
            )
        
        return JSONResponse(content={
            "plan_type": plan_type,
            "total_days": len(plans[plan_type]),
            "plan": plans[plan_type]
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@router.get("/api/bible-plans/{plan_type}/day/{day}")
async def get_bible_plan_day(plan_type: str, day: int):
    """取得指定天數的讀經計畫"""
    try:
        plans = load_bible_plans()
        
        if plan_type not in plans:
            return JSONResponse(
                status_code=404,
                content={"error": "Plan type not found"}
            )
        
        if day < 1 or day > len(plans[plan_type]):
            return JSONResponse(
                status_code=404,
                content={"error": "Day not found"}
            )
        
        day_plan = plans[plan_type][day - 1]
        
        return JSONResponse(content=day_plan)
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
