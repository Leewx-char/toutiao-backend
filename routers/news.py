from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


from config.db_config import get_db
from crud import news
from crud import news_cache
from schemas.Base import NewsItemBase
from schemas.news import CategoryResponse, NewsListResponse, NewsDetailResponse
from utils.response import success_response

# 创建 APIRouter 实例
# prefix 路由前缀（API 接口规范文档）
# tags 分组 标签
router = APIRouter(prefix="/api/news", tags=["news"])

# 接口实现流程
# 1. 模块化路由 -> API 接口规范文档
# 2. 定义模型类 -> 数据库表（数据库设计文档）
# 3. 在 crud 文件夹里面创建文件，封装操作数据库的方法
# 4. 在路由处理函数里面调用 crud 封装好的方法，响应结果

@router.get("/categories")
async def get_categories(skip: int=0, limit: int=100, db: AsyncSession = Depends(get_db)):
    # 先获取数据库里面新闻分类数据 -> 先定义模型类 -> 封装查询数据的方法
    categories = await news_cache.get_categories(db, skip, limit)
    data = [CategoryResponse.model_validate(item) for item in categories]
    return success_response(message="获取分类成功", data=data)

@router.get("/list")
async def get_news_list(
        category_id: int = Query(..., alias="categoryId"),
        page: int = 1,
        page_size: int = Query(10, alias="pageSize", le=100),
        db: AsyncSession = Depends(get_db)
):
    # 思路：处理分页规则 -> 查询新闻列表 -> 计算总量 -> 计算是否还有更多
    offset = (page - 1) * page_size
    news_list = await news_cache.get_news_list(db, category_id, offset, page_size)
    total = await news_cache.get_news_count(db, category_id)
    has_more = (offset + len(news_list)) < total
    news_list = [NewsItemBase.model_validate(item) for item in news_list]
    data = NewsListResponse(list=news_list, total=total, hasMore=has_more)
    return success_response(message="获取新闻列表成功", data=data)

@router.get("/detail")
async def get_news_datail(news_id: int=Query(..., alias="id"), db: AsyncSession=Depends(get_db)):
    # 浏览量加一 + 获取新闻详情 + 相关新闻
    views_res = await news_cache.increase_news_views(db, news_id)
    if not views_res:
        raise HTTPException(status_code=404, detail="新闻不存在")
    news_detail = await news_cache.get_news_detail(db, news_id)
    if not news_detail:
        raise HTTPException(status_code=404, detail="新闻不存在")

    related_news = await news_cache.get_related_news(db, news_detail.id, news_detail.category_id)

    data = NewsDetailResponse.model_validate(news_detail)
    related_model = [NewsItemBase.model_validate(item) for item in related_news]

    data.related_news = related_model
    return success_response(message="获取新闻详情成功", data=data)