import datetime as dt
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from src.services.product_content_service import ProductContentService


class DummyProduct:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def to_dict(self):
        return dict(self.__dict__)


class DummyGeneration:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def to_dict(self):
        return dict(self.__dict__)


class DummyRepo:
    def __init__(self):
        self.created_payload = None
        self.updated_payload = None
        self.increment_calls = []
        self.product = DummyProduct(
            id=10,
            user_id=7,
            department_id=3,
            category='general',
            name='示例产品',
            material=None,
            style=None,
            color=None,
            scene=None,
            selling_points=[],
            target_audience=None,
            price_range=None,
            attributes={},
        )

    async def create_product(self, **kwargs):
        self.created_payload = kwargs
        return DummyProduct(id=11, user_id=7, department_id=3, **kwargs)

    async def update_product(self, product, **kwargs):
        self.updated_payload = kwargs
        payload = product.to_dict()
        payload.update(kwargs)
        return DummyProduct(**payload)

    async def get_product_by_id(self, product_id):
        return self.product if product_id == self.product.id else None

    async def create_generation(self, **kwargs):
        return DummyGeneration(id=99, created_at=dt.datetime(2026, 4, 26, 12, 0, 0), channel=kwargs['channel'], tone_styles=kwargs['tone_styles'])

    async def get_or_create_subscription(self, **kwargs):
        return SimpleNamespace(tier='free', status='active', to_dict=lambda: {'tier': 'free', 'status': 'active'})

    async def get_daily_usage(self, **kwargs):
        return SimpleNamespace(text_generate_count=0)

    async def get_month_usage_sum(self, **kwargs):
        return 0

    async def increment_daily_usage(self, **kwargs):
        self.increment_calls.append(kwargs)
        return SimpleNamespace(text_generate_count=1)

    async def list_generations(self, **kwargs):
        items = [
            DummyGeneration(id=1, product_id=10, channel='xiaohongshu', tone_styles=['种草'], result_items=[{'title': 'A'}], created_at='2026-04-26T10:00:00'),
            DummyGeneration(id=2, product_id=12, channel='wechat', tone_styles=['专业'], result_items=[{'title': 'B'}], created_at='2026-04-26T11:00:00'),
        ]
        return items, 2

    async def get_products_by_ids(self, product_ids):
        return [
            DummyProduct(id=10, name='示例产品', category='服饰'),
            DummyProduct(id=12, name='露营桌', category='户外'),
        ]

    async def get_latest_generation_by_product(self, **kwargs):
        return DummyGeneration(id=3, product_id=10, channel='xiaohongshu', tone_styles=['种草'], result_items=[{'title': 'latest'}], created_at='2026-04-26T12:30:00')


class DummyModel:
    def __init__(self, content):
        self.content = content

    async def call(self, *args, **kwargs):
        return SimpleNamespace(content=self.content)


@pytest.mark.asyncio
async def test_generate_contents_normalizes_payload_and_reuses_product(monkeypatch):
    service = ProductContentService(db=None)
    service.repo = DummyRepo()
    monkeypatch.setattr('src.services.product_content_service.select_model', lambda **kwargs: DummyModel('[{"style":"种草","title":"标题","content":"正文","hashtags":["#1"],"image_prompt":"提示词"}]'))

    user = SimpleNamespace(id=7, department_id=3)
    result = await service.generate_contents(
        user=user,
        payload={
            'product_id': 10,
            'product': {
                'category': ' 服饰 ',
                'name': '  真丝衬衫 ',
                'selling_points': ['垂坠', '垂坠', ''],
                'attributes': {' 工艺 ': ' 双层锁边 ', '': 'ignored'},
            },
            'styles': ['种草', '种草', '专业'],
            'count': 1,
            'channel': 'WECHAT',
        },
    )

    assert service.repo.updated_payload['category'] == '服饰'
    assert service.repo.updated_payload['name'] == '真丝衬衫'
    assert service.repo.updated_payload['selling_points'] == ['垂坠']
    assert service.repo.updated_payload['attributes'] == {'工艺': '双层锁边'}
    assert result['product_id'] == 10
    assert result['product_name'] == '真丝衬衫'
    assert result['channel'] == 'wechat'
    assert result['items'][0]['title'] == '标题'


def test_parse_generation_items_repairs_broken_json():
    broken = '[{"style":"种草","title":"标题","content":"正文","hashtags":["#a"],"image_prompt":"海报"]'
    items = ProductContentService._parse_generation_items(text=broken, styles=['种草'], count=1)

    assert len(items) == 1
    assert items[0]['title'] == '标题'
    assert items[0]['hashtags'] == ['#a']


@pytest.mark.asyncio
async def test_list_generations_includes_product_metadata():
    service = ProductContentService(db=None)
    service.repo = DummyRepo()
    user = SimpleNamespace(id=7, department_id=3)

    items, total = await service.list_generations(user=user, page=1, page_size=20)

    assert total == 2
    assert items[0]['product_name'] == '示例产品'
    assert items[1]['product_category'] == '户外'


@pytest.mark.asyncio
async def test_get_latest_generation_rejects_cross_user_access():
    service = ProductContentService(db=None)
    service.repo = DummyRepo()
    user = SimpleNamespace(id=99, department_id=3)

    with pytest.raises(HTTPException) as exc:
        await service.get_latest_generation_for_product(user=user, product_id=10)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_quota_check_raises_structured_error_when_daily_limit_hit():
    service = ProductContentService(db=None)
    service.repo = DummyRepo()

    async def full_usage(**kwargs):
        return SimpleNamespace(text_generate_count=5)

    service.repo.get_daily_usage = full_usage

    with pytest.raises(HTTPException) as exc:
        await service._ensure_quota_available(user_id=7, department_id=3, op_type='text_generate')

    assert exc.value.status_code == 403
    assert exc.value.detail['code'] == 'QUOTA_EXCEEDED'
