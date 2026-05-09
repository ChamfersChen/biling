"""通用产品文案模块数据模型"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

from src.storage.postgres.models_business import Base
from src.utils.datetime_utils import format_utc_datetime, utc_now_naive


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(128), nullable=False)
    material = Column(String(64), nullable=True)
    style = Column(String(64), nullable=True)
    color = Column(String(64), nullable=True)
    scene = Column(String(128), nullable=True)
    selling_points = Column(JSONB, nullable=False, default=list)
    target_audience = Column(String(128), nullable=True)
    price_range = Column(String(64), nullable=True)
    attributes = Column(JSONB, nullable=False, default=dict)
    image_paths = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime, nullable=False, default=utc_now_naive)
    updated_at = Column(DateTime, nullable=False, default=utc_now_naive, onupdate=utc_now_naive)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "department_id": self.department_id,
            "name": self.name,
            "material": self.material,
            "style": self.style,
            "color": self.color,
            "scene": self.scene,
            "selling_points": self.selling_points or [],
            "target_audience": self.target_audience,
            "price_range": self.price_range,
            "attributes": self.attributes or {},
            "image_paths": self.image_paths or [],
            "created_at": format_utc_datetime(self.created_at),
            "updated_at": format_utc_datetime(self.updated_at),
        }


class ProductContentGeneration(Base):
    __tablename__ = "product_content_generations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt_external_id = Column(String(36), nullable=True, index=True)
    prompt_name = Column(String(128), nullable=True)
    channel = Column(String(32), nullable=False, default="xiaohongshu")
    tone_styles = Column(JSONB, nullable=False)
    result_items = Column(JSONB, nullable=False)
    exported = Column(Integer, nullable=False, default=0)
    favorited = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utc_now_naive)
    updated_at = Column(DateTime, nullable=False, default=utc_now_naive, onupdate=utc_now_naive)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "department_id": self.department_id,
            "product_id": self.product_id,
            "prompt_external_id": self.prompt_external_id,
            "prompt_name": self.prompt_name,
            "channel": self.channel,
            "tone_styles": self.tone_styles or [],
            "result_items": self.result_items or [],
            "exported": self.exported,
            "favorited": self.favorited,
            "created_at": format_utc_datetime(self.created_at),
            "updated_at": format_utc_datetime(self.updated_at),
        }


class ProductUsageDaily(Base):
    __tablename__ = "product_usage_daily"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    usage_date = Column(Date, nullable=False, index=True)
    text_generate_count = Column(Integer, nullable=False, default=0)
    image_prompt_count = Column(Integer, nullable=False, default=0)
    image_generate_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utc_now_naive)
    updated_at = Column(DateTime, nullable=False, default=utc_now_naive, onupdate=utc_now_naive)

    __table_args__ = (UniqueConstraint("user_id", "usage_date", name="uq_usage_user_date"),)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "department_id": self.department_id,
            "usage_date": self.usage_date.isoformat() if self.usage_date else None,
            "text_generate_count": self.text_generate_count,
            "image_prompt_count": self.image_prompt_count,
            "image_generate_count": self.image_generate_count,
            "created_at": format_utc_datetime(self.created_at),
            "updated_at": format_utc_datetime(self.updated_at),
        }


class ProductSubscription(Base):
    __tablename__ = "product_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    tier = Column(String(32), nullable=False, default="free", index=True)
    status = Column(String(32), nullable=False, default="active", index=True)
    stripe_customer_id = Column(String(128), nullable=True, index=True)
    stripe_subscription_id = Column(String(128), nullable=True, index=True)
    next_billing_date = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=False, default=utc_now_naive)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now_naive)
    updated_at = Column(DateTime, nullable=False, default=utc_now_naive, onupdate=utc_now_naive)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "department_id": self.department_id,
            "tier": self.tier,
            "status": self.status,
            "stripe_customer_id": self.stripe_customer_id,
            "stripe_subscription_id": self.stripe_subscription_id,
            "next_billing_date": format_utc_datetime(self.next_billing_date),
            "started_at": format_utc_datetime(self.started_at),
            "expires_at": format_utc_datetime(self.expires_at),
            "created_at": format_utc_datetime(self.created_at),
            "updated_at": format_utc_datetime(self.updated_at),
        }


class SubscriptionCode(Base):
    __tablename__ = "subscription_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), nullable=False, unique=True, index=True)
    tier = Column(String(32), nullable=False, index=True)
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, nullable=False, default=0)
    expires_at = Column(DateTime, nullable=True)
    created_by = Column(String(64), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now_naive)
    updated_at = Column(DateTime, nullable=False, default=utc_now_naive, onupdate=utc_now_naive)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "tier": self.tier,
            "max_uses": self.max_uses,
            "used_count": self.used_count,
            "expires_at": format_utc_datetime(self.expires_at),
            "created_by": self.created_by,
            "created_at": format_utc_datetime(self.created_at),
            "updated_at": format_utc_datetime(self.updated_at),
        }


class SubscriptionTransaction(Base):
    __tablename__ = "subscription_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    tier = Column(String(32), nullable=False, index=True)
    source = Column(String(32), nullable=False, default="stripe", index=True)
    amount = Column(Integer, nullable=False, default=0)
    currency = Column(String(16), nullable=False, default="cny")
    stripe_session_id = Column(String(128), nullable=True, index=True)
    stripe_payment_intent_id = Column(String(128), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now_naive)
    updated_at = Column(DateTime, nullable=False, default=utc_now_naive, onupdate=utc_now_naive)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "department_id": self.department_id,
            "tier": self.tier,
            "source": self.source,
            "amount": self.amount,
            "currency": self.currency,
            "stripe_session_id": self.stripe_session_id,
            "stripe_payment_intent_id": self.stripe_payment_intent_id,
            "status": self.status,
            "paid_at": format_utc_datetime(self.paid_at),
            "created_at": format_utc_datetime(self.created_at),
            "updated_at": format_utc_datetime(self.updated_at),
        }
