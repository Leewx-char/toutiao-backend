from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from schemas.Base import NewsItemBase


class NewsBase(BaseModel):
    created_at: datetime
    updated_at: datetime

class CategoryResponse(NewsBase):
    id: int
    name: str
    sort_order: int

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

class NewsListResponse(BaseModel):
    list: list[NewsItemBase]
    total: int
    has_more: bool = Field(..., alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

class NewsDetailResponse(NewsItemBase):
    content: Optional[str] = ""
    related_news: list[NewsItemBase] = Field(default_factory=list, alias="relatedNews")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )




