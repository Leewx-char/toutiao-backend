from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from config.db_config import get_db
from models.users import User
from schemas.history import HistoryAddRequest, HistoryListResponse
from utils.auth import get_current_user
from utils.response import success_response
from crud import history

router = APIRouter(prefix="/api/history", tags=["history"])

@router.post("/add")
async def add_history(
        data: HistoryAddRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await history.add_history(db, user.id, data.news_id)
    return success_response(message="添加成功", data=result)

@router.get("/list")
async def get_history_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    rows, total = await history.list_history(db, page, page_size, user.id)
    history_list = [ {
        **news.__dict__,
        "view_time": view_time
    } for news, view_time in rows]
    has_more = total > page * page_size
    data = HistoryListResponse(list=history_list, total=total, hasMore=has_more)
    return success_response(message="获取历史浏览记录成功", data=data)

@router.delete("/delete/{history_id}")
async def delete_history(
        history_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await history.delete_history(db, user.id, history_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="浏览记录不存在")
    return success_response(message="删除单条浏览记录成功")

@router.delete("/clear")
async def clear_history(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await history.delete_all_history(db, user.id)
    return success_response(message=f"清空了{result}条历史记录")