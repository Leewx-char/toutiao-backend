from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from cache.news_cache import get_cached_categories, set_cache_categories, get_cache_news_list, set_cache_news_list, \
    set_cache_news_count, get_cache_news_count, get_cache_news_detail, set_cache_news_detail, \
    get_cache_news_related, set_cache_news_related, get_cache_news_views, set_cache_news_views
from config.cache_conf import redis_client
from models.news import Category, News
from schemas.Base import NewsItemBase
from schemas.news import NewsDetailResponse


async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    # 先尝试从缓存中获取数据
    cached_categories = await get_cached_categories()
    if cached_categories:
        return [Category(**item) for item in cached_categories]

    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories = result.scalars().all() # ORM

    # 写入缓存
    if categories:
        # ORM对象转换为Python对象
        categories_cache = jsonable_encoder(categories)
        await set_cache_categories(categories_cache)

    # 返回数据
    return categories

async def get_news_list(db: AsyncSession, category_id: int, skip: int = 0, limit: int = 10):
    # 先尝试从缓存获取新闻列表
    # 跳过的数量skip = (页码 - 1) * 每页数量 -> 页码 == skip // 每页数量 + 1
    page = skip // limit + 1
    cached_list = await get_cache_news_list(category_id, page, limit)
    if cached_list:
        for item in cached_list:
            news_id = item["id"]
            item["views"] = await get_cache_news_views(news_id)
        # return cached_list # 要的是 ORM
        return [News(**item) for item in cached_list]

    # 查询的是指定分类下的所有新闻
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    news_list =  result.scalars().all()

    # 写入缓存
    if news_list:
        # 先把 ORM 数据 转换 字典才能写入缓存
        # ORM 转成 Pydantic，再转为 字典
        # by_alias=False 不使用别名，保存Python风格，因为 Redis 数据是给后端用的
        news_data = [NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False) for item in news_list]
        await set_cache_news_list(category_id, page, limit, news_data)

    return news_list

async def get_news_count(db: AsyncSession, category_id: int):
    cache_count = await get_cache_news_count(category_id)
    if cache_count:
        return int(cache_count)

    # 要查询的是指定分类下的新闻数量
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    count = result.scalar_one() # 只能有一个结果，否则报错(单个整数值)

    if count:
        await set_cache_news_count(category_id, count)

    return count

async def get_news_detail(db: AsyncSession, news_id: int):
    cache_detail = await get_cache_news_detail(news_id)
    if cache_detail:
        cache_detail["views"] = await get_cache_news_views(news_id)
        return News(**cache_detail)

    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    detail = result.scalar_one_or_none()

    if detail:
        news_detail = NewsItemBase.model_validate(detail).model_dump(mode="json", by_alias=False)
        await set_cache_news_detail(news_id, news_detail)

    return detail

async def increase_news_views(db: AsyncSession, news_id: int):
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(stmt)
    await db.commit()

    if result.rowcount > 0:
        query = select(News.views).where(News.id == news_id)
        views = await db.execute(query)
        views = views.scalar_one_or_none()
        if views:
            await set_cache_news_views(news_id, views)
        return True
    return False

async def get_related_news(db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    cache_related_news = await get_cache_news_related(news_id, category_id, limit)
    if cache_related_news:
        return [NewsItemBase(**item) for item in cache_related_news]

    # order_by 排序 -> 浏览量和发布时间
    stmt = select(News).where(
        News.id != news_id,
        News.category_id == category_id
    ).order_by(News.views.desc(),
               News.publish_time.desc() # 默认是升序， desc 表示降序
    ).limit(limit)
    result = await db.execute(stmt)
    # return result.scalars().all()
    related_news = result.scalars().all()
    if related_news:
        related_data = [NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False) for item in related_news]
        await set_cache_news_related(news_id, category_id, limit, related_data)
    # 列表推导式 推导出新闻的核心数据，再return
    return related_news