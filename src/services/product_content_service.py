"""Service for generic product content generation module."""

from __future__ import annotations

import datetime as dt
import json
from calendar import monthrange

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src import config as app_config
from src.models.chat import select_model
from src.repositories.product_content_repository import ProductContentRepository
from src.services.product_image_service import ProductImageService
from src.storage.postgres.models_business import User
from src.storage.postgres.models_product_content import Product
from src.utils.product_prompts import build_product_content_prompt

TIER_LIMITS: dict[str, dict[str, int | None]] = {
    "free": {"daily": 5, "monthly": 50},
    "pro": {"daily": 50, "monthly": 1500},
    "enterprise": {"daily": None, "monthly": None},
}

USAGE_FIELD_MAP = {
    "text_generate": "text_generate_count",
    "image_prompt": "image_prompt_count",
    "image_generate": "image_generate_count",
}


class ProductContentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ProductContentRepository(db)
        self.image_service = ProductImageService()

    async def list_products(
        self,
        *,
        user: User,
        category: str | None,
        keyword: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[dict], int]:
        items, total = await self.repo.list_products(
            user_id=user.id,
            department_id=user.department_id,
            category=category,
            keyword=keyword,
            page=page,
            page_size=page_size,
        )
        return [item.to_dict() for item in items], total

    async def create_product(self, *, user: User, payload: dict) -> dict:
        item = await self.repo.create_product(
            user_id=user.id,
            department_id=user.department_id,
            category=(payload.get("category") or "general").strip(),
            name=(payload.get("name") or "").strip(),
            material=(payload.get("material") or "").strip() or None,
            style=(payload.get("style") or "").strip() or None,
            color=(payload.get("color") or "").strip() or None,
            scene=(payload.get("scene") or "").strip() or None,
            selling_points=payload.get("selling_points") or [],
            target_audience=(payload.get("target_audience") or "").strip() or None,
            price_range=(payload.get("price_range") or "").strip() or None,
            attributes=payload.get("attributes") or {},
        )
        return item.to_dict()

    async def update_product(self, *, user: User, product_id: int, payload: dict) -> dict:
        product = await self._get_owned_product(user=user, product_id=product_id)

        update_data = {}
        for key in [
            "category",
            "name",
            "material",
            "style",
            "color",
            "scene",
            "selling_points",
            "target_audience",
            "price_range",
            "attributes",
        ]:
            if key in payload:
                update_data[key] = payload[key]

        if "category" in update_data and isinstance(update_data["category"], str):
            update_data["category"] = update_data["category"].strip() or "general"
        if "name" in update_data and isinstance(update_data["name"], str):
            update_data["name"] = update_data["name"].strip()
            if not update_data["name"]:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="产品名称不能为空")

        updated = await self.repo.update_product(product, **update_data)
        return updated.to_dict()

    async def delete_product(self, *, user: User, product_id: int) -> None:
        product = await self._get_owned_product(user=user, product_id=product_id)
        await self.repo.delete_product(product)

    async def list_generations(self, *, user: User, page: int, page_size: int) -> tuple[list[dict], int]:
        items, total = await self.repo.list_generations(
            user_id=user.id,
            department_id=user.department_id,
            page=page,
            page_size=page_size,
        )
        return [item.to_dict() for item in items], total

    async def get_subscription(self, *, user: User) -> dict:
        subscription = await self.repo.get_or_create_subscription(user_id=user.id, department_id=user.department_id)
        return subscription.to_dict()

    async def get_quota(self, *, user: User) -> dict:
        quota = await self._build_quota_snapshot(user.id, user.department_id)
        return quota

    async def generate_contents(self, *, user: User, payload: dict) -> dict:
        product_payload = payload.get("product") or {}
        styles = payload.get("styles") or []
        count = int(payload.get("count") or 10)
        channel = (payload.get("channel") or "xiaohongshu").strip()

        if not product_payload.get("name"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="product.name 不能为空")
        if not styles:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="styles 不能为空")
        if count < 1 or count > 20:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="count 必须在 1-20 之间")

        await self._ensure_quota_available(user_id=user.id, department_id=user.department_id, op_type="text_generate")

        product = await self.repo.create_product(
            user_id=user.id,
            department_id=user.department_id,
            category=(product_payload.get("category") or "general").strip(),
            name=(product_payload.get("name") or "").strip(),
            material=(product_payload.get("material") or "").strip() or None,
            style=(product_payload.get("style") or "").strip() or None,
            color=(product_payload.get("color") or "").strip() or None,
            scene=(product_payload.get("scene") or "").strip() or None,
            selling_points=product_payload.get("selling_points") or [],
            target_audience=(product_payload.get("target_audience") or "").strip() or None,
            price_range=(product_payload.get("price_range") or "").strip() or None,
            attributes=product_payload.get("attributes") or {},
        )

        prompt = build_product_content_prompt(
            product=product.to_dict(),
            channel=channel,
            styles=styles,
            count=count,
        )
        model = select_model(model_spec=getattr(app_config, "default_model", ""))
        response = await model.call([{"role": "user", "content": prompt}], stream=False)
        text = getattr(response, "content", None) or str(response)

        items = self._parse_generation_items(text=text, styles=styles, count=count)

        generation = await self.repo.create_generation(
            user_id=user.id,
            department_id=user.department_id,
            product_id=product.id,
            channel=channel,
            tone_styles=styles,
            result_items=items,
            exported=0,
            favorited=0,
        )

        await self._consume_quota(user_id=user.id, department_id=user.department_id, op_type="text_generate")
        quota = await self._build_quota_snapshot(user.id, user.department_id)

        return {
            "generation_id": generation.id,
            "product_id": product.id,
            "items": items,
            "quota": quota,
        }

    async def generate_image(self, *, user: User, prompt: str, size: str, style: str) -> dict:
        if not prompt.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="prompt 不能为空")

        await self._ensure_quota_available(user_id=user.id, department_id=user.department_id, op_type="image_generate")
        image_url = await self.image_service.generate_image_from_prompt(prompt=prompt, size=size, style=style)
        await self._consume_quota(user_id=user.id, department_id=user.department_id, op_type="image_generate")
        quota = await self._build_quota_snapshot(user.id, user.department_id)
        return {"image_url": image_url, "quota": quota}

    async def _get_owned_product(self, *, user: User, product_id: int) -> Product:
        product = await self.repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="产品不存在")
        if product.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该产品")
        if product.department_id != user.department_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该产品")
        return product

    @staticmethod
    def _parse_generation_items(*, text: str, styles: list[str], count: int) -> list[dict]:
        parsed: object | None = None

        try:
            parsed = json.loads(text)
        except Exception:
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1 and end > start:
                try:
                    parsed = json.loads(text[start : end + 1])
                except Exception:
                    parsed = None

        if not isinstance(parsed, list):
            parsed = []

        normalized = []
        for i, item in enumerate(parsed[:count]):
            if not isinstance(item, dict):
                continue
            hashtags = item.get("hashtags")
            if not isinstance(hashtags, list):
                hashtags = []
            normalized.append(
                {
                    "style": str(item.get("style") or styles[i % len(styles)]),
                    "title": str(item.get("title") or ""),
                    "content": str(item.get("content") or ""),
                    "hashtags": [str(tag) for tag in hashtags if str(tag).strip()],
                    "image_prompt": str(item.get("image_prompt") or ""),
                }
            )

        while len(normalized) < count:
            idx = len(normalized)
            normalized.append(
                {
                    "style": styles[idx % len(styles)],
                    "title": "",
                    "content": "",
                    "hashtags": [],
                    "image_prompt": "",
                }
            )

        return normalized

    async def _ensure_quota_available(self, *, user_id: int, department_id: int | None, op_type: str) -> None:
        subscription = await self.repo.get_or_create_subscription(user_id=user_id, department_id=department_id)
        tier = subscription.tier
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        if limits["daily"] is None and limits["monthly"] is None:
            return

        field_name = USAGE_FIELD_MAP[op_type]
        today = dt.date.today()
        today_usage = await self.repo.get_daily_usage(user_id=user_id, usage_date=today)
        today_value = int(getattr(today_usage, field_name, 0) or 0) if today_usage else 0

        first_day = today.replace(day=1)
        month_last_day = monthrange(today.year, today.month)[1]
        last_day = today.replace(day=month_last_day)
        month_value = await self.repo.get_month_usage_sum(
            user_id=user_id,
            from_date=first_day,
            to_date=last_day,
            field_name=field_name,
        )

        daily_limit = limits["daily"]
        monthly_limit = limits["monthly"]

        if daily_limit is not None and today_value >= daily_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "QUOTA_EXCEEDED",
                    "message": "已超过当日配额限制",
                    "tier": tier,
                    "daily_remaining": max(0, daily_limit - today_value),
                    "monthly_remaining": max(0, (monthly_limit or 0) - month_value) if monthly_limit is not None else -1,
                },
            )

        if monthly_limit is not None and month_value >= monthly_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "QUOTA_EXCEEDED",
                    "message": "已超过当月配额限制",
                    "tier": tier,
                    "daily_remaining": max(0, (daily_limit or 0) - today_value) if daily_limit is not None else -1,
                    "monthly_remaining": max(0, monthly_limit - month_value),
                },
            )

    async def _consume_quota(self, *, user_id: int, department_id: int | None, op_type: str) -> None:
        field_name = USAGE_FIELD_MAP[op_type]
        today = dt.date.today()
        await self.repo.increment_daily_usage(
            user_id=user_id,
            department_id=department_id,
            usage_date=today,
            field_name=field_name,
            amount=1,
        )

    async def _build_quota_snapshot(self, user_id: int, department_id: int | None) -> dict:
        subscription = await self.repo.get_or_create_subscription(user_id=user_id, department_id=department_id)
        tier = subscription.tier
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        today = dt.date.today()
        usage = await self.repo.get_daily_usage(user_id=user_id, usage_date=today)
        daily_used = int(usage.text_generate_count if usage else 0)

        first_day = today.replace(day=1)
        month_last_day = monthrange(today.year, today.month)[1]
        last_day = today.replace(day=month_last_day)
        monthly_used = await self.repo.get_month_usage_sum(
            user_id=user_id,
            from_date=first_day,
            to_date=last_day,
            field_name="text_generate_count",
        )

        daily_limit = limits["daily"]
        monthly_limit = limits["monthly"]

        return {
            "tier": tier,
            "daily_limit": daily_limit,
            "monthly_limit": monthly_limit,
            "daily_used": daily_used,
            "monthly_used": monthly_used,
            "daily_remaining": -1 if daily_limit is None else max(0, daily_limit - daily_used),
            "monthly_remaining": -1 if monthly_limit is None else max(0, monthly_limit - monthly_used),
        }
