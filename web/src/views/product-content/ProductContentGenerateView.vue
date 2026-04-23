<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { Copy, Image, Sparkles } from 'lucide-vue-next'
import { useProductContentStore } from '@/stores/productContent'

const router = useRouter()
const productContentStore = useProductContentStore()

const productForm = reactive(productContentStore.getDefaultProductForm())
const formRef = ref()

const selectedProductId = ref(undefined)
const selectedStyles = ref(['种草'])
const count = ref(10)
const channel = ref('xiaohongshu')
const sellingPointsInput = ref('')
const attributeKey = ref('')
const attributeValue = ref('')
const generatedImages = ref({})

const styleOptions = ['种草', '专业', '故事', '对比', '简洁', '高级感']
const channelOptions = [
  { label: '小红书', value: 'xiaohongshu' },
  { label: '抖音', value: 'douyin' },
  { label: '公众号', value: 'wechat' },
  { label: '电商详情', value: 'ecommerce' }
]

const quotaText = computed(() => {
  const quota = productContentStore.currentQuota
  if (!quota) {
    return '配额加载中...'
  }
  const daily = quota.daily_limit === null ? '无限' : `${quota.daily_used}/${quota.daily_limit}`
  const monthly = quota.monthly_limit === null ? '无限' : `${quota.monthly_used}/${quota.monthly_limit}`
  return `日额度 ${daily} · 月额度 ${monthly}`
})

const resultItems = computed(() => productContentStore.lastGenerated?.items || [])

const productOptions = computed(() =>
  productContentStore.products.map((item) => ({
    label: `${item.name} (${item.category})`,
    value: item.id
  }))
)

const canGenerate = computed(() => {
  return Boolean(productForm.name?.trim()) && selectedStyles.value.length > 0 && count.value > 0
})

const parseError = (error, fallback) => {
  if (!error) {
    return fallback
  }
  if (typeof error.message === 'string' && error.message.trim()) {
    return error.message
  }
  return fallback
}

const syncSellingPointsInput = () => {
  sellingPointsInput.value = (productForm.selling_points || []).join('，')
}

const syncSellingPointsArray = () => {
  productForm.selling_points = sellingPointsInput.value
    .split(/[,，\n]/)
    .map((text) => text.trim())
    .filter(Boolean)
}

const loadProductToForm = (product) => {
  productForm.category = product.category || 'general'
  productForm.name = product.name || ''
  productForm.material = product.material || ''
  productForm.style = product.style || ''
  productForm.color = product.color || ''
  productForm.scene = product.scene || ''
  productForm.selling_points = [...(product.selling_points || [])]
  productForm.target_audience = product.target_audience || ''
  productForm.price_range = product.price_range || ''
  productForm.attributes = { ...(product.attributes || {}) }
  syncSellingPointsInput()
}

const handleSelectProduct = (productId) => {
  const product = productContentStore.products.find((item) => item.id === productId)
  if (!product) {
    return
  }
  loadProductToForm(product)
}

const handleAddAttribute = () => {
  const key = attributeKey.value.trim()
  const value = attributeValue.value.trim()
  if (!key || !value) {
    return
  }
  productForm.attributes = {
    ...(productForm.attributes || {}),
    [key]: value
  }
  attributeKey.value = ''
  attributeValue.value = ''
}

const handleRemoveAttribute = (key) => {
  const nextAttrs = { ...(productForm.attributes || {}) }
  delete nextAttrs[key]
  productForm.attributes = nextAttrs
}

const handleCreateOrUpdateProduct = async () => {
  syncSellingPointsArray()
  const payload = {
    ...productForm,
    name: productForm.name.trim()
  }
  if (!payload.name) {
    message.warning('请先输入产品名称')
    return
  }

  try {
    if (selectedProductId.value) {
      await productContentStore.updateProduct(selectedProductId.value, payload)
      message.success('产品已更新')
    } else {
      const created = await productContentStore.createProduct(payload)
      selectedProductId.value = created.id
      message.success('产品已保存')
    }
    await productContentStore.fetchProducts({ page: 1, page_size: 50 })
  } catch (error) {
    message.error(parseError(error, '保存产品失败'))
  }
}

const handleGenerate = async () => {
  syncSellingPointsArray()
  if (!canGenerate.value) {
    message.warning('请补全产品名称和文案风格')
    return
  }

  try {
    generatedImages.value = {}
    await productContentStore.generateContents({
      product: { ...productForm },
      styles: selectedStyles.value,
      count: count.value,
      channel: channel.value
    })
    message.success('文案生成完成')
    await productContentStore.fetchGenerations({ page: 1, page_size: 20 })
  } catch (error) {
    message.error(parseError(error, '文案生成失败'))
  }
}

const handleGenerateImage = async (item, index) => {
  if (!item.image_prompt) {
    message.warning('该文案未返回图片提示词')
    return
  }
  try {
    const result = await productContentStore.generateImage({
      prompt: item.image_prompt,
      size: '1024x1024',
      style: 'natural'
    })
    generatedImages.value = {
      ...generatedImages.value,
      [index]: result.image_url
    }
    message.success('图片生成完成')
  } catch (error) {
    message.error(parseError(error, '生成图片失败'))
  }
}

const handleCopy = async (item) => {
  const fullText = `${item.title}\n\n${item.content}\n\n${(item.hashtags || []).join(' ')}`
  await navigator.clipboard.writeText(fullText)
  message.success('已复制文案')
}

onMounted(async () => {
  await Promise.all([
    productContentStore.fetchQuota(),
    productContentStore.fetchProducts({ page: 1, page_size: 50 })
  ])
})
</script>

<template>
  <div class="product-content-page">
    <div class="page-header">
      <div>
        <h2>产品文案生成</h2>
        <p>{{ quotaText }}</p>
      </div>
      <a-space>
        <a-button @click="router.push('/product-content/history')">生成记录</a-button>
        <a-button @click="router.push('/product-content/subscription')">订阅与配额</a-button>
      </a-space>
    </div>

    <a-alert
      type="info"
      show-icon
      :message="productContentStore.hasQuota ? '配额正常，可继续生成' : '当前配额不足，请稍后重试或升级订阅'"
      class="quota-alert"
    />

    <div class="content-grid">
      <a-card title="产品信息" :bordered="false">
        <a-form ref="formRef" layout="vertical">
          <a-form-item label="复用已保存产品">
            <a-select
              v-model:value="selectedProductId"
              :options="productOptions"
              placeholder="选择后自动填充"
              allow-clear
              @change="handleSelectProduct"
            />
          </a-form-item>
          <a-row :gutter="12">
            <a-col :span="12">
              <a-form-item label="产品名称" required>
                <a-input v-model:value="productForm.name" placeholder="如：轻奢真丝衬衫" />
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="产品类目">
                <a-input v-model:value="productForm.category" placeholder="如：服饰" />
              </a-form-item>
            </a-col>
          </a-row>
          <a-row :gutter="12">
            <a-col :span="8">
              <a-form-item label="材质"><a-input v-model:value="productForm.material" /></a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="风格"><a-input v-model:value="productForm.style" /></a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="颜色"><a-input v-model:value="productForm.color" /></a-form-item>
            </a-col>
          </a-row>
          <a-form-item label="使用场景">
            <a-input v-model:value="productForm.scene" placeholder="如：通勤、约会、户外" />
          </a-form-item>
          <a-form-item label="卖点（逗号分隔）">
            <a-textarea v-model:value="sellingPointsInput" :rows="2" @blur="syncSellingPointsArray" />
          </a-form-item>
          <a-row :gutter="12">
            <a-col :span="12">
              <a-form-item label="目标人群"><a-input v-model:value="productForm.target_audience" /></a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="价格区间"><a-input v-model:value="productForm.price_range" /></a-form-item>
            </a-col>
          </a-row>

          <a-form-item label="补充属性">
            <a-space compact style="width: 100%">
              <a-input v-model:value="attributeKey" placeholder="属性名" style="width: 38%" />
              <a-input v-model:value="attributeValue" placeholder="属性值" style="width: 46%" />
              <a-button type="primary" @click="handleAddAttribute">添加</a-button>
            </a-space>
            <div class="attr-tags">
              <a-tag
                v-for="(value, key) in productForm.attributes"
                :key="key"
                closable
                @close.prevent="handleRemoveAttribute(key)"
              >
                {{ key }}: {{ value }}
              </a-tag>
            </div>
          </a-form-item>

          <a-button @click="handleCreateOrUpdateProduct">保存产品</a-button>
        </a-form>
      </a-card>

      <a-card title="生成配置" :bordered="false">
        <a-form layout="vertical">
          <a-form-item label="发布渠道">
            <a-select v-model:value="channel" :options="channelOptions" />
          </a-form-item>
          <a-form-item label="文案风格" required>
            <a-checkbox-group v-model:value="selectedStyles" :options="styleOptions" />
          </a-form-item>
          <a-form-item label="生成条数">
            <a-input-number v-model:value="count" :min="1" :max="20" style="width: 100%" />
          </a-form-item>

          <a-button
            type="primary"
            block
            :loading="productContentStore.isGenerating"
            :disabled="!canGenerate"
            @click="handleGenerate"
          >
            <template #icon><Sparkles :size="16" /></template>
            生成文案
          </a-button>
        </a-form>
      </a-card>
    </div>

    <a-card title="生成结果" :bordered="false" class="result-card">
      <a-empty v-if="resultItems.length === 0" description="还没有生成结果" />
      <div v-else class="result-list">
        <a-card v-for="(item, index) in resultItems" :key="`${item.style}-${index}`" class="result-item" size="small">
          <div class="result-title-row">
            <a-tag color="blue">{{ item.style }}</a-tag>
            <a-space>
              <a-button size="small" @click="handleCopy(item)">
                <template #icon><Copy :size="14" /></template>
                复制
              </a-button>
              <a-button
                size="small"
                type="primary"
                :loading="productContentStore.isGeneratingImage"
                @click="handleGenerateImage(item, index)"
              >
                <template #icon><Image :size="14" /></template>
                生图
              </a-button>
            </a-space>
          </div>
          <h4>{{ item.title || '未返回标题' }}</h4>
          <p class="content-text">{{ item.content || '未返回正文' }}</p>
          <div class="hashtags">
            <a-tag v-for="tag in item.hashtags" :key="tag">{{ tag }}</a-tag>
          </div>
          <p class="image-prompt">图片提示词: {{ item.image_prompt || '无' }}</p>
          <img v-if="generatedImages[index]" :src="generatedImages[index]" alt="generated image" class="generated-image" />
        </a-card>
      </div>
    </a-card>
  </div>
</template>

<style scoped>
.product-content-page {
  padding: 20px;
  max-width: 1320px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.page-header h2 {
  margin: 0;
}

.page-header p {
  margin: 4px 0 0;
  color: var(--gray-600);
}

.quota-alert {
  margin-bottom: 16px;
}

.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.attr-tags {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.result-card {
  margin-bottom: 20px;
}

.result-list {
  display: grid;
  gap: 12px;
}

.result-item h4 {
  margin: 8px 0;
}

.result-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.content-text {
  white-space: pre-wrap;
}

.hashtags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 8px 0;
}

.image-prompt {
  color: var(--gray-700);
  margin: 8px 0;
}

.generated-image {
  width: 220px;
  border-radius: 8px;
  border: 1px solid var(--gray-200);
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .page-header {
    align-items: flex-start;
    gap: 12px;
    flex-direction: column;
  }
}
</style>
