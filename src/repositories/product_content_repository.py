"""Repository for generic product content module."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.postgres.models_product_content import (
    Product,
    ProductContentGeneration,
    ProductSubscription,
    ProductUsageDaily,
)
from src.utils.datetime_utils import utc_now_naive


class ProductContentRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_product(self, **kwargs) -> Product:
        item = Product(**kwargs)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_product_by_id(self, product_id: int) -> Product | None:
        result = await self.db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def list_products(
        self,
        *,
        user_id: int,
        department_id: int | None,
        category: str | None,
        keyword: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        query = select(Product).where(Product.user_id == user_id)
        if department_id is None:
            query = query.where(Product.department_id.is_(None))
        else:
            query = query.where(Product.department_id == department_id)
        if category:
            query = query.where(Product.category == category)
        if keyword:
            query = query.where(Product.name.ilike(f"%{keyword}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(Product.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update_product(self, product: Product, **kwargs) -> Product:
        for key, value in kwargs.items():
            setattr(product, key, value)
        product.updated_at = utc_now_naive()
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete_product(self, product: Product) -> None:
        await self.db.delete(product)
        await self.db.commit()

    async def create_generation(self, **kwargs) -> ProductContentGeneration:
        item = ProductContentGeneration(**kwargs)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def list_generations(
        self,
        *,
        user_id: int,
        department_id: int | None,
        page: int,
        page_size: int,
    ) -> tuple[list[ProductContentGeneration], int]:
        query = select(ProductContentGeneration).where(ProductContentGeneration.user_id == user_id)
        if department_id is None:
            query = query.where(ProductContentGeneration.department_id.is_(None))
        else:
            query = query.where(ProductContentGeneration.department_id == department_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(ProductContentGeneration.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_or_create_subscription(
        self,
        *,
        user_id: int,
        department_id: int | None,
    ) -> ProductSubscription:
        result = await self.db.execute(select(ProductSubscription).where(ProductSubscription.user_id == user_id))
        item = result.scalar_one_or_none()
        if item:
            return item

        item = ProductSubscription(user_id=user_id, department_id=department_id, tier="free", status="active")
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_daily_usage(self, *, user_id: int, usage_date: dt.date) -> ProductUsageDaily | None:
        result = await self.db.execute(
            select(ProductUsageDaily).where(
                ProductUsageDaily.user_id == user_id,
                ProductUsageDaily.usage_date == usage_date,
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_daily_usage(
        self,
        *,
        user_id: int,
        department_id: int | None,
        usage_date: dt.date,
    ) -> ProductUsageDaily:
        item = await self.get_daily_usage(user_id=user_id, usage_date=usage_date)
        if item:
            return item

        item = ProductUsageDaily(
            user_id=user_id,
            department_id=department_id,
            usage_date=usage_date,
            text_generate_count=0,
            image_prompt_count=0,
            image_generate_count=0,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def increment_daily_usage(
        self,
        *,
        user_id: int,
        department_id: int | None,
        usage_date: dt.date,
        field_name: str,
        amount: int,
    ) -> ProductUsageDaily:
        item = await self.get_or_create_daily_usage(
            user_id=user_id,
            department_id=department_id,
            usage_date=usage_date,
        )
        current_value = getattr(item, field_name, 0) or 0
        setattr(item, field_name, current_value + amount)
        item.updated_at = utc_now_naive()
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_month_usage_sum(
        self,
        *,
        user_id: int,
        from_date: dt.date,
        to_date: dt.date,
        field_name: str,
    ) -> int:
        field = getattr(ProductUsageDaily, field_name)
        result = await self.db.execute(
            select(func.coalesce(func.sum(field), 0)).where(
                ProductUsageDaily.user_id == user_id,
                ProductUsageDaily.usage_date >= from_date,
                ProductUsageDaily.usage_date <= to_date,
            )
        )
        return int(result.scalar() or 0)
