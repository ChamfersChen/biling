"""通用产品文案生成模块路由"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from server.utils.auth_middleware import get_db, get_required_user
from src.services.product_content_service import ProductContentService
from src.storage.postgres.models_business import User
from src.utils.logging_config import logger

product_content = APIRouter(prefix="/product-content", tags=["通用产品文案"])


class ProductPayload(BaseModel):
    category: str = Field("general", description="产品类目")
    name: str = Field(..., description="产品名称")
    material: str | None = None
    style: str | None = None
    color: str | None = None
    scene: str | None = None
    selling_points: list[str] = Field(default_factory=list)
    target_audience: str | None = None
    price_range: str | None = None
    attributes: dict = Field(default_factory=dict)


class GenerateContentRequest(BaseModel):
    product_id: int | None = Field(default=None)
    prompt_external_id: str | None = Field(default=None)
    product: ProductPayload
    count: int = Field(10, ge=1, le=20)
    styles: list[str] = Field(default_factory=list)
    channel: str = Field("xiaohongshu")


@product_content.get("/prompt-options")
async def list_prompt_options(
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = ProductContentService(db)
        items = await service.list_available_prompts(user=current_user)
        return {"success": True, "data": {"list": items, "required_variables": ["product_payload", "channel", "styles_payload", "count"]}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"list prompt options failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取提示词选项失败")


class GenerateImageRequest(BaseModel):
    prompt: str
    size: str = Field("1024x1024")
    style: str = Field("natural")


@product_content.get("/products")
async def list_products(
    category: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = ProductContentService(db)
        items, total = await service.list_products(
            user=current_user,
            category=category,
            keyword=keyword,
            page=page,
            page_size=page_size,
        )
        return {"success": True, "data": {"list": items, "total": total}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"list products failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取产品列表失败")


@product_content.post("/products")
async def create_product(
    payload: ProductPayload,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = ProductContentService(db)
        item = await service.create_product(user=current_user, payload=payload.model_dump())
        return {"success": True, "data": item}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"create product failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建产品失败")


@product_content.put("/products/{product_id}")
async def update_product(
    product_id: int,
    payload: ProductPayload,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = ProductContentService(db)
        item = await service.update_product(user=current_user, product_id=product_id, payload=payload.model_dump())
        return {"success": True, "data": item}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"update product failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新产品失败")


@product_content.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = ProductContentService(db)
        await service.delete_product(user=current_user, product_id=product_id)
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"delete product failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除产品失败")


@product_content.get("/generations")
async def list_generations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = ProductContentService(db)
        items, total = await service.list_generations(user=current_user, page=page, page_size=page_size)
        return {"success": True, "data": {"list": items, "total": total}}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"list generations failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取生成记录失败")


@product_content.get("/products/{product_id}/latest-generation")
async def get_latest_generation_for_product(
    product_id: int,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = ProductContentService(db)
        item = await service.get_latest_generation_for_product(user=current_user, product_id=product_id)
        return {"success": True, "data": item}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get latest generation for product failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取产品最近生成结果失败")


@product_content.post("/generate")
async def generate_contents(
    payload: GenerateContentRequest,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = ProductContentService(db)
        result = await service.generate_contents(user=current_user, payload=payload.model_dump())
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"generate content failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="生成文案失败")


@product_content.post("/generate-image")
async def generate_image(
    payload: GenerateImageRequest,
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = ProductContentService(db)
        result = await service.generate_image(
            user=current_user,
            prompt=payload.prompt,
            size=payload.size,
            style=payload.style,
        )
        return {"success": True, "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"generate image failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="生成图片失败")


@product_content.get("/quota")
async def get_quota(
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = ProductContentService(db)
        quota = await service.get_quota(user=current_user)
        return {"success": True, "data": quota}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get quota failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取配额失败")


@product_content.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_required_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = ProductContentService(db)
        subscription = await service.get_subscription(user=current_user)
        return {"success": True, "data": subscription}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get subscription failed: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取订阅信息失败")
