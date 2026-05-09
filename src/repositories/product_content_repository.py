"""Repository for generic product content module."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.postgres.models_product_content import (
    Product,
    ProductContentGeneration,
    SubscriptionCode,
    SubscriptionTransaction,
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

    async def get_products_by_ids(self, product_ids: list[int]) -> list[Product]:
        if not product_ids:
            return []
        result = await self.db.execute(select(Product).where(Product.id.in_(product_ids)))
        return list(result.scalars().all())

    async def list_products(
        self,
        *,
        user_id: int,
        department_id: int | None,
        keyword: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], int]:
        query = select(Product).where(Product.user_id == user_id)
        if department_id is None:
            query = query.where(Product.department_id.is_(None))
        else:
            query = query.where(Product.department_id == department_id)
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

    async def get_latest_generation_by_product(
        self,
        *,
        user_id: int,
        department_id: int | None,
        product_id: int,
    ) -> ProductContentGeneration | None:
        query = select(ProductContentGeneration).where(
            ProductContentGeneration.user_id == user_id,
            ProductContentGeneration.product_id == product_id,
        )
        if department_id is None:
            query = query.where(ProductContentGeneration.department_id.is_(None))
        else:
            query = query.where(ProductContentGeneration.department_id == department_id)

        query = query.order_by(ProductContentGeneration.created_at.desc()).limit(1)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

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

    async def update_subscription(self, subscription: ProductSubscription, **kwargs) -> ProductSubscription:
        for key, value in kwargs.items():
            setattr(subscription, key, value)
        subscription.updated_at = utc_now_naive()
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def get_subscription_code(self, code: str) -> SubscriptionCode | None:
        result = await self.db.execute(select(SubscriptionCode).where(SubscriptionCode.code == code))
        return result.scalar_one_or_none()

    async def create_subscription_code(self, **kwargs) -> SubscriptionCode:
        item = SubscriptionCode(**kwargs)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def list_subscription_codes(self) -> list[SubscriptionCode]:
        result = await self.db.execute(select(SubscriptionCode).order_by(SubscriptionCode.created_at.desc()))
        return list(result.scalars().all())

    async def update_subscription_code(self, item: SubscriptionCode, **kwargs) -> SubscriptionCode:
        for key, value in kwargs.items():
            setattr(item, key, value)
        item.updated_at = utc_now_naive()
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def create_subscription_transaction(self, **kwargs) -> SubscriptionTransaction:
        item = SubscriptionTransaction(**kwargs)
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_transaction_by_session_id(self, session_id: str) -> SubscriptionTransaction | None:
        result = await self.db.execute(
            select(SubscriptionTransaction).where(SubscriptionTransaction.stripe_session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def update_subscription_transaction(self, item: SubscriptionTransaction, **kwargs) -> SubscriptionTransaction:
        for key, value in kwargs.items():
            setattr(item, key, value)
        item.updated_at = utc_now_naive()
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def list_transactions(
        self,
        *,
        user_id: int,
        department_id: int | None,
        limit: int = 20,
    ) -> list[SubscriptionTransaction]:
        query = select(SubscriptionTransaction).where(SubscriptionTransaction.user_id == user_id)
        if department_id is None:
            query = query.where(SubscriptionTransaction.department_id.is_(None))
        else:
            query = query.where(SubscriptionTransaction.department_id == department_id)
        query = query.order_by(SubscriptionTransaction.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

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

    async def count_products(self, *, user_id: int, department_id: int | None) -> int:
        query = select(func.count()).select_from(Product).where(Product.user_id == user_id)
        if department_id is None:
            query = query.where(Product.department_id.is_(None))
        else:
            query = query.where(Product.department_id == department_id)
        return int((await self.db.execute(query)).scalar() or 0)

    async def count_generations(self, *, user_id: int, department_id: int | None) -> int:
        query = select(func.count()).select_from(ProductContentGeneration).where(ProductContentGeneration.user_id == user_id)
        if department_id is None:
            query = query.where(ProductContentGeneration.department_id.is_(None))
        else:
            query = query.where(ProductContentGeneration.department_id == department_id)
        return int((await self.db.execute(query)).scalar() or 0)

    async def count_generations_in_range(
        self,
        *,
        user_id: int,
        department_id: int | None,
        start_at: dt.datetime,
        end_at: dt.datetime,
    ) -> int:
        query = select(func.count()).select_from(ProductContentGeneration).where(
            ProductContentGeneration.user_id == user_id,
            ProductContentGeneration.created_at >= start_at,
            ProductContentGeneration.created_at <= end_at,
        )
        if department_id is None:
            query = query.where(ProductContentGeneration.department_id.is_(None))
        else:
            query = query.where(ProductContentGeneration.department_id == department_id)
        return int((await self.db.execute(query)).scalar() or 0)

    async def count_generated_items(self, *, user_id: int, department_id: int | None) -> int:
        items, _ = await self.list_generations(user_id=user_id, department_id=department_id, page=1, page_size=100000)
        return sum(len(item.result_items or []) for item in items)

    async def count_generated_items_in_range(
        self,
        *,
        user_id: int,
        department_id: int | None,
        start_at: dt.datetime,
        end_at: dt.datetime,
    ) -> int:
        query = select(ProductContentGeneration).where(
            ProductContentGeneration.user_id == user_id,
            ProductContentGeneration.created_at >= start_at,
            ProductContentGeneration.created_at <= end_at,
        )
        if department_id is None:
            query = query.where(ProductContentGeneration.department_id.is_(None))
        else:
            query = query.where(ProductContentGeneration.department_id == department_id)
        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return sum(len(item.result_items or []) for item in items)

    async def get_recent_daily_usage(
        self,
        *,
        user_id: int,
        department_id: int | None,
        start_date: dt.date,
        end_date: dt.date,
    ) -> list[ProductUsageDaily]:
        query = select(ProductUsageDaily).where(
            ProductUsageDaily.user_id == user_id,
            ProductUsageDaily.usage_date >= start_date,
            ProductUsageDaily.usage_date <= end_date,
        )
        if department_id is None:
            query = query.where(ProductUsageDaily.department_id.is_(None))
        else:
            query = query.where(ProductUsageDaily.department_id == department_id)
        query = query.order_by(ProductUsageDaily.usage_date.asc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_channel_generation_counts(
        self,
        *,
        user_id: int,
        department_id: int | None,
    ) -> list[tuple[str, int]]:
        query = select(
            ProductContentGeneration.channel,
            func.count(ProductContentGeneration.id),
        ).where(ProductContentGeneration.user_id == user_id)
        if department_id is None:
            query = query.where(ProductContentGeneration.department_id.is_(None))
        else:
            query = query.where(ProductContentGeneration.department_id == department_id)
        query = query.group_by(ProductContentGeneration.channel).order_by(func.count(ProductContentGeneration.id).desc())
        result = await self.db.execute(query)
        return [(str(channel or "unknown"), int(total or 0)) for channel, total in result.all()]

    async def update_generation_item_image_prompt(
        self,
        *,
        generation_id: int,
        item_index: int,
        image_prompt: str,
    ) -> ProductContentGeneration | None:
        result = await self.db.execute(
            select(ProductContentGeneration).where(ProductContentGeneration.id == generation_id)
        )
        item = result.scalar_one_or_none()
        if not item:
            return None
        items = list(item.result_items or [])
        if item_index < 0 or item_index >= len(items):
            return None
        items[item_index] = {**items[item_index], "image_prompt": image_prompt}
        item.result_items = items
        item.updated_at = utc_now_naive()
        await self.db.commit()
        await self.db.refresh(item)
        return item
