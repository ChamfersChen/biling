"""Image generation service for product-content module."""

from __future__ import annotations

import base64
import os
import uuid

from openai import AsyncOpenAI

from src.storage.minio import aupload_file_to_minio


class ProductImageService:
    def __init__(self):
        self._api_key = os.getenv("OPENAI_API_KEY")
        self._base_url = os.getenv("OPENAI_API_BASE")
        self._model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")

    async def generate_image_from_prompt(self, *, prompt: str, size: str = "1024x1024", style: str = "natural") -> str:
        if not self._api_key:
            raise ValueError("图片生成功能未配置，请先设置 OPENAI_API_KEY")

        client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        import ipdb; ipdb.set_trace()
        response = await client.images.generate(model=self._model, prompt=prompt, size=size)

        data = getattr(response, "data", None) or []
        if not data:
            raise ValueError("图片生成失败：返回结果为空")

        item = data[0]
        image_url = getattr(item, "url", None)
        if image_url:
            return image_url

        b64_data = getattr(item, "b64_json", None)
        if not b64_data:
            raise ValueError("图片生成失败：未返回可用图片数据")

        image_bytes = base64.b64decode(b64_data)
        file_name = f"{uuid.uuid4().hex}.png"
        _ = style
        minio_url = await aupload_file_to_minio("generated-images", file_name, image_bytes, "png")
        return minio_url
