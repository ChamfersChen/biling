"""Service for generic product content generation module."""

from __future__ import annotations

import datetime as dt
import json
import re
from calendar import monthrange
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from json_repair import repair_json

from src import config as app_config
from src.models.chat import select_model
from src.repositories.product_content_repository import ProductContentRepository
from src.repositories.prompt_repository import PromptRepository
from src.services.product_image_service import ProductImageService
from src.storage.postgres.models_business import User
from src.storage.postgres.models_product_content import Product
from src.utils import format_prompt
from src.utils.product_prompts import (
    PRODUCT_CONTENT_REQUIRED_VARIABLES,
    build_product_content_prompt,
    build_product_content_prompt_slots,
)

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
        self.prompt_repo = PromptRepository(db)
        self.image_service = ProductImageService()

    async def list_available_prompts(self, *, user: User) -> list[dict]:
        items = await self.prompt_repo.list_by_user(user.username)
        available = []
        for item in items:
            if item.is_dir:
                continue
            detected_variables = self._extract_prompt_variables(item.description or "")
            missing_variables = [name for name in PRODUCT_CONTENT_REQUIRED_VARIABLES if name not in detected_variables]
            extra_variables = [name for name in detected_variables if name not in PRODUCT_CONTENT_REQUIRED_VARIABLES]
            available.append(
                {
                    "external_id": item.external_id,
                    "name": item.path or item.name,
                    "path": item.path,
                    "description": self._build_prompt_summary(item.description or ""),
                    "required_variables": PRODUCT_CONTENT_REQUIRED_VARIABLES,
                    "detected_variables": detected_variables,
                    "missing_variables": missing_variables,
                    "extra_variables": extra_variables,
                    "is_compatible": len(missing_variables) == 0,
                    "updated_at": item.updated_at.isoformat() if item.updated_at else None,
                }
            )

        available.sort(key=lambda item: (not item["is_compatible"], item["name"].lower()))
        return available

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
        normalized_payload = self._normalize_product_payload(payload)
        item = await self.repo.create_product(
            user_id=user.id,
            department_id=user.department_id,
            **normalized_payload,
        )
        return item.to_dict()

    async def update_product(self, *, user: User, product_id: int, payload: dict) -> dict:
        product = await self._get_owned_product(user=user, product_id=product_id)

        normalized_payload = self._normalize_product_payload(payload)
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
                update_data[key] = normalized_payload[key]

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
        product_map = await self._build_product_map([item.product_id for item in items])
        normalized_items = []
        for item in items:
            payload = item.to_dict()
            payload["product_name"] = product_map.get(item.product_id, {}).get("name")
            payload["product_category"] = product_map.get(item.product_id, {}).get("category")
            normalized_items.append(payload)
        return normalized_items, total

    async def get_latest_generation_for_product(self, *, user: User, product_id: int) -> dict | None:
        await self._get_owned_product(user=user, product_id=product_id)
        item = await self.repo.get_latest_generation_by_product(
            user_id=user.id,
            department_id=user.department_id,
            product_id=product_id,
        )
        if not item:
            return None

        payload = item.to_dict()
        product = await self._get_owned_product(user=user, product_id=product_id)
        payload["product_name"] = product.name
        payload["product_category"] = product.category
        return payload

    async def get_subscription(self, *, user: User) -> dict:
        subscription = await self.repo.get_or_create_subscription(user_id=user.id, department_id=user.department_id)
        return subscription.to_dict()

    async def get_quota(self, *, user: User) -> dict:
        quota = await self._build_quota_snapshot(user.id, user.department_id)
        return quota

    async def generate_contents(self, *, user: User, payload: dict) -> dict:
        product_id = payload.get("product_id")
        product_payload = payload.get("product") or {}
        styles = self._normalize_styles(payload.get("styles") or [])
        count = int(payload.get("count") or 10)
        channel = self._normalize_channel(payload.get("channel"))
        prompt_external_id = str(payload.get("prompt_external_id") or "").strip() or None

        if not product_payload.get("name"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="product.name 不能为空")
        if not styles:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="styles 不能为空")
        if count < 1 or count > 20:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="count 必须在 1-20 之间")

        await self._ensure_quota_available(user_id=user.id, department_id=user.department_id, op_type="text_generate")

        normalized_payload = self._normalize_product_payload(product_payload)

        if product_id:
            product = await self._get_owned_product(user=user, product_id=int(product_id))
            product = await self.repo.update_product(product, **normalized_payload)
        else:
            product = await self.repo.create_product(
                user_id=user.id,
                department_id=user.department_id,
                **normalized_payload,
            )

        prompt, prompt_meta = await self._build_generation_prompt(
            user=user,
            product=product.to_dict(),
            channel=channel,
            styles=styles,
            count=count,
            prompt_external_id=prompt_external_id,
        )
        model = select_model(model_spec=getattr(app_config, "default_model", ""))
        response = await model.call([{"role": "user", "content": prompt}], stream=False)
        text = getattr(response, "content", None) or str(response)

        items = self._parse_generation_items(text=text, styles=styles, count=count)

        generation = await self.repo.create_generation(
            user_id=user.id,
            department_id=user.department_id,
            product_id=product.id,
            prompt_external_id=prompt_meta["external_id"],
            prompt_name=prompt_meta["name"],
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
            "product_name": product.name,
            "product_category": product.category,
            "prompt_external_id": prompt_meta["external_id"],
            "prompt_name": prompt_meta["name"],
            "channel": generation.channel,
            "tone_styles": generation.tone_styles or [],
            "created_at": generation.created_at.isoformat() if generation.created_at else None,
            "items": items,
            "quota": quota,
        }

    async def _build_generation_prompt(
        self,
        *,
        user: User,
        product: dict,
        channel: str,
        styles: list[str],
        count: int,
        prompt_external_id: str | None,
    ) -> tuple[str, dict[str, str | None]]:
        if not prompt_external_id:
            prompt = build_product_content_prompt(product=product, channel=channel, styles=styles, count=count)
            return prompt, {"external_id": None, "name": "系统内置提示词"}

        item = await self.prompt_repo.get_by_external_id(prompt_external_id)
        if not item or item.is_dir:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="指定提示词不存在")
        if item.created_by != user.username:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权使用该提示词")

        content = (item.description or "").strip()
        if not content:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="所选提示词内容为空")

        missing_variables = self._get_missing_required_variables(content)
        if missing_variables:
            joined = "、".join(missing_variables)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"所选提示词缺少必需变量：{joined}",
            )

        slots = build_product_content_prompt_slots(product=product, channel=channel, styles=styles, count=count)
        try:
            formatted = format_prompt(content, slots)
        except AssertionError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        return formatted, {"external_id": item.external_id, "name": item.path or item.name or "自定义提示词"}

    @staticmethod
    def _build_prompt_summary(content: str) -> str:
        first_line = next((line.strip() for line in content.splitlines() if line.strip()), "")
        return first_line[:120]

    @staticmethod
    def _extract_prompt_variables(content: str) -> list[str]:
        found = {
            match.group(1).strip()
            for match in re.finditer(r"\{\{([^}]+)\}\}", content or "")
            if match.group(1).strip()
        }
        return sorted(found)

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
            try:
                repaired = repair_json(text, return_objects=True)
                parsed = repaired
            except Exception:
                parsed = parsed

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

    @staticmethod
    def _normalize_channel(channel: str | None) -> str:
        normalized = (channel or "xiaohongshu").strip().lower()
        allowed_channels = {"xiaohongshu", "douyin", "wechat", "ecommerce"}
        return normalized if normalized in allowed_channels else "xiaohongshu"

    @staticmethod
    def _normalize_styles(styles: list[Any]) -> list[str]:
        normalized: list[str] = []
        for item in styles:
            value = str(item or "").strip()
            if value and value not in normalized:
                normalized.append(value)
        return normalized

    @staticmethod
    def _normalize_product_payload(payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            payload = {}

        selling_points_raw = payload.get("selling_points") or []
        if not isinstance(selling_points_raw, list):
            selling_points_raw = [selling_points_raw]
        selling_points = []
        for item in selling_points_raw:
            value = str(item or "").strip()
            if value and value not in selling_points:
                selling_points.append(value)

        attributes_raw = payload.get("attributes") or {}
        if not isinstance(attributes_raw, dict):
            attributes_raw = {}
        attributes = {}
        for key, value in attributes_raw.items():
            normalized_key = str(key or "").strip()
            normalized_value = str(value or "").strip()
            if normalized_key and normalized_value:
                attributes[normalized_key] = normalized_value

        return {
            "category": (payload.get("category") or "general").strip() or "general",
            "name": (payload.get("name") or "").strip(),
            "material": (payload.get("material") or "").strip() or None,
            "style": (payload.get("style") or "").strip() or None,
            "color": (payload.get("color") or "").strip() or None,
            "scene": (payload.get("scene") or "").strip() or None,
            "selling_points": selling_points,
            "target_audience": (payload.get("target_audience") or "").strip() or None,
            "price_range": (payload.get("price_range") or "").strip() or None,
            "attributes": attributes,
        }

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

    async def _build_product_map(self, product_ids: list[int]) -> dict[int, dict]:
        products = await self.repo.get_products_by_ids(list({product_id for product_id in product_ids if product_id}))
        return {product.id: product.to_dict() for product in products}
