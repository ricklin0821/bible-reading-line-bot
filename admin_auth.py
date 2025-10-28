"""
管理後台認證路由

提供登入頁面和儀表板的路由
"""

from fastapi import APIRouter
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter()

@router.get("/admin")
def admin_root():
    """管理後台根路徑，重定向到登入頁"""
    return RedirectResponse(url="/admin/login")

@router.get("/admin/login")
def admin_login():
    """管理後台登入頁面"""
    return FileResponse("static/admin/login.html", media_type="text/html")

@router.get("/admin/dashboard")
def admin_dashboard():
    """管理後台儀表板"""
    return FileResponse("static/admin/dashboard.html", media_type="text/html")

