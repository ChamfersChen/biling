<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ArrowRight, Copy, Eye, Image, Layers3, PackageSearch, Pencil, Plus, RefreshCw, Sparkles, SwatchBook, Trash2, Wand2 } from 'lucide-vue-next'
import { useProductContentStore } from '@/stores/productContent'

const router = useRouter()
const route = useRoute()
const productContentStore = useProductContentStore()

const productForm = reactive(productContentStore.getDefaultProductForm())
const selectedProductId = ref(undefined)
const selectedStyles = ref(['种草'])
const count = ref(10)
const channel = ref('xiaohongshu')
const sellingPointsInput = ref('')
const attributeKey = ref('')
const attributeValue = ref('')
const generatedImages = ref({})
const generatingImageIndex = ref(null)
const showProductsDrawer = ref(false)
const productKeyword = ref('')
const activeProductPreviewId = ref(null)
const deletingProductId = ref(null)
const loadingSelectedProductResult = ref(false)
const isSavingProduct = ref(false)
const hasFormChanges = ref(false)
const selectedPromptExternalId = ref(undefined)

const styleOptions = ['种草', '专业', '故事', '对比', '简洁', '高级感']
const channelOptions = [
  { label: '小红书', value: 'xiaohongshu' },
  { label: '抖音', value: 'douyin' },
  { label: '公众号', value: 'wechat' },
  { label: '电商详情', value: 'ecommerce' }
]

const previewTips = [
  '适合先保存常用产品，后续一键复用',
  '混合多种风格时，文案层次会更自然',
  '图片提示词已联动生图接口，可直接继续出图'
]

const requiredPromptVariables = ['product_payload', 'channel', 'styles_payload', 'count']

const quotaInfo = computed(() => {
  const quota = productContentStore.currentQuota
  if (!quota) {
    return {
      dailyText: '加载中',
      monthlyText: '加载中',
      remainingText: '正在拉取配额信息',
      percentage: 0,
      tone: 'normal'
    }
  }

  const dailyLimit = quota.daily_limit === null ? '无限' : quota.daily_limit
  const monthlyLimit = quota.monthly_limit === null ? '无限' : quota.monthly_limit
  const remaining = quota.daily_remaining === -1 ? '无限' : quota.daily_remaining
  const percentage = quota.daily_limit ? Math.min(100, Math.round((quota.daily_used / quota.daily_limit) * 100)) : 8
  const tone = quota.daily_remaining !== -1 && quota.daily_remaining <= 1 ? 'warning' : 'normal'

  return {
    dailyText: `${quota.daily_used} / ${dailyLimit}`,
    monthlyText: `${quota.monthly_used} / ${monthlyLimit}`,
    remainingText: `今日剩余 ${remaining} 次生成机会`,
    percentage,
    tone
  }
})

const resultItems = computed(() => productContentStore.lastGenerated?.items || [])
const resultCount = computed(() => resultItems.value.length)
const selectedStyleSummary = computed(() => selectedStyles.value.join(' / '))
const attributesCount = computed(() => Object.keys(productForm.attributes || {}).length)
const sellingPointsCount = computed(() => (productForm.selling_points || []).length)
const savedProductsCount = computed(() => productContentStore.productsTotal || productContentStore.products.length)
const currentResultMeta = computed(() => ({
  channel: productContentStore.lastGenerated?.channel || channel.value,
  toneStyles: productContentStore.lastGenerated?.tone_styles || selectedStyles.value,
  createdAt: productContentStore.lastGenerated?.created_at || null,
  promptName: productContentStore.lastGenerated?.prompt_name || null,
  promptExternalId: productContentStore.lastGenerated?.prompt_external_id || null
}))
const currentResultTimestamp = computed(() => {
  const value = currentResultMeta.value.createdAt
  if (!value) {
    return ''
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})

const selectedProduct = computed(() => {
  if (!selectedProductId.value) {
    return null
  }
  return productContentStore.products.find((item) => item.id === selectedProductId.value) || null
})

const formSnapshot = computed(() => JSON.stringify({
  category: productForm.category || 'general',
  name: productForm.name || '',
  material: productForm.material || '',
  style: productForm.style || '',
  color: productForm.color || '',
  scene: productForm.scene || '',
  selling_points: productForm.selling_points || [],
  target_audience: productForm.target_audience || '',
  price_range: productForm.price_range || '',
  attributes: productForm.attributes || {}
}))

const selectedProductSnapshot = computed(() => {
  if (!selectedProduct.value) {
    return ''
  }
  return JSON.stringify({
    category: selectedProduct.value.category || 'general',
    name: selectedProduct.value.name || '',
    material: selectedProduct.value.material || '',
    style: selectedProduct.value.style || '',
    color: selectedProduct.value.color || '',
    scene: selectedProduct.value.scene || '',
    selling_points: selectedProduct.value.selling_points || [],
    target_audience: selectedProduct.value.target_audience || '',
    price_range: selectedProduct.value.price_range || '',
    attributes: selectedProduct.value.attributes || {}
  })
})

const resultContext = computed(() => {
  const hasSavedProduct = Boolean(selectedProductId.value)
  const hasResults = resultItems.value.length > 0
  const productName = selectedProduct.value?.name || productForm.name || '当前产品'
  const matchesSelectedProduct = hasSavedProduct && productContentStore.lastGenerated?.product_id === selectedProductId.value

  if (!hasSavedProduct) {
    return {
      modeLabel: '新建产品模式',
      modeHint: '当前结果来自本页填写信息，生成后可继续保存或复用。',
      resultBadge: '当前输入',
      alertType: 'success',
      alertMessage: hasResults ? `当前展示的是「${productName}」刚生成的结果` : '先填写产品信息，再生成第一组文案'
    }
  }

  if (loadingSelectedProductResult.value) {
    return {
      modeLabel: '复用已保存产品',
      modeHint: '正在同步最近一次生成结果，稍后即可继续复制或生图。',
      resultBadge: '历史结果',
      alertType: 'info',
      alertMessage: '正在加载该产品最近一次生成结果...'
    }
  }

  if (hasResults && matchesSelectedProduct) {
    return {
      modeLabel: '复用已保存产品',
      modeHint: hasFormChanges.value
        ? `当前正在编辑「${productName}」，结果仍是上一次保存版本，建议先保存或直接重新生成。`
        : `当前已锁定「${productName}」，可直接重生成或继续生图。`,
      resultBadge: '已保存产品',
      alertType: 'info',
      alertMessage: `当前展示的是「${productName}」最近一次生成结果`
    }
  }

  return {
    modeLabel: '复用已保存产品',
    modeHint: `已载入「${productName}」，还没有历史结果，可直接开始生成第一组文案。`,
    resultBadge: '等待生成',
    alertType: 'warning',
    alertMessage: `「${productName}」暂时没有历史生成结果`
  }
})

const productOptions = computed(() =>
  productContentStore.products.map((item) => ({
    label: `${item.name} (${item.category})`,
    value: item.id
  }))
)

const promptOptions = computed(() => {
  const latestPromptId = productContentStore.lastGenerated?.prompt_external_id || null

  const managedOptions = (productContentStore.promptOptions || []).map((item) => ({
    label: item.path || item.name,
    value: item.external_id,
    disabled: !item.is_compatible,
    priority: item.external_id === latestPromptId ? 0 : 1,
    meta: {
      name: item.name,
      path: item.path,
      external_id: item.external_id,
      summary: item.description || '',
      is_compatible: item.is_compatible,
      detected_variables: item.detected_variables || [],
      missing_variables: item.missing_variables || [],
      extra_variables: item.extra_variables || []
    }
  }))
    .sort((a, b) => {
      if ((a.priority || 0) !== (b.priority || 0)) {
        return (a.priority || 0) - (b.priority || 0)
      }
      return String(a.label || '').localeCompare(String(b.label || ''), 'zh-CN')
    })

  return [
    {
      label: '系统内置提示词',
      value: '__builtin__',
      meta: {
        name: '系统内置提示词',
        path: 'builtin',
        external_id: '__builtin__',
        summary: '使用系统默认生成提示词',
        is_compatible: true,
        detected_variables: requiredPromptVariables,
        missing_variables: [],
        extra_variables: []
      }
    },
    ...managedOptions
  ]
})

const incompatiblePromptOptions = computed(() =>
  promptOptions.value.filter((item) => item.value !== '__builtin__' && item.disabled)
)

const selectedPromptOption = computed(() => {
  if (!selectedPromptExternalId.value) {
    return null
  }
  return productContentStore.promptOptions.find((item) => item.external_id === selectedPromptExternalId.value) || null
})

const promptStrategySummary = computed(() => {
  if (!selectedPromptExternalId.value) {
    return {
      modeLabel: '系统内置提示词',
      description: '使用系统默认提示词，适合直接开始生成。',
      detail: '系统会自动注入产品资料、渠道、风格和生成条数。'
    }
  }

  return {
    modeLabel: selectedPromptOption.value?.path || selectedPromptOption.value?.name || '自定义提示词',
    description: `${getPromptFileName(selectedPromptOption.value?.path, selectedPromptOption.value?.name)} · ${getPromptDirectory(selectedPromptOption.value?.path)}`,
    detail: `external_id：${selectedPromptExternalId.value}`
  }
})

const filterPromptOption = (input, option) => {
  const keyword = String(input || '').trim().toLowerCase()
  if (!keyword) {
    return true
  }

  const meta = option?.meta || {}
  return [option?.label, meta.name, meta.path, meta.external_id, meta.summary]
    .filter(Boolean)
    .some((value) => String(value).toLowerCase().includes(keyword))
}

const getPromptFileName = (path, fallback = '') => {
  const normalized = String(path || fallback || '').trim()
  if (!normalized) {
    return '未命名提示词'
  }
  const parts = normalized.split('/').filter(Boolean)
  return parts[parts.length - 1] || normalized
}

const getPromptDirectory = (path) => {
  const normalized = String(path || '').trim()
  if (!normalized || !normalized.includes('/')) {
    return '根目录'
  }
  const parts = normalized.split('/').filter(Boolean)
  return parts.slice(0, -1).join('/') || '根目录'
}

const filteredProducts = computed(() => {
  const keyword = productKeyword.value.trim().toLowerCase()
  if (!keyword) {
    return productContentStore.products
  }
  return productContentStore.products.filter((item) => {
    return [item.name, item.category, item.scene, item.style, item.material, item.target_audience]
      .filter(Boolean)
      .some((field) => String(field).toLowerCase().includes(keyword))
  })
})

const activeProductPreview = computed(() => {
  if (!filteredProducts.value.length) {
    return null
  }
  return filteredProducts.value.find((item) => item.id === activeProductPreviewId.value) || filteredProducts.value[0]
})

const activeProductTimestamp = computed(() => {
  const value = activeProductPreview.value?.updated_at || activeProductPreview.value?.created_at
  if (!value) {
    return '最近保存时间未知'
  }
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
})

const canGenerate = computed(() => Boolean(productForm.name?.trim()) && selectedStyles.value.length > 0 && count.value > 0)
const canSaveProduct = computed(() => Boolean(productForm.name?.trim()) && !isSavingProduct.value)
const selectedProductLabel = computed(() => selectedProduct.value?.name || productForm.name || '未命名产品')

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
  sellingPointsInput.value = (productForm.selling_points || []).join('; ')
}

const syncSellingPointsArray = () => {
  productForm.selling_points = sellingPointsInput.value
    .split(/[;；,，\n]/)
    .map((text) => text.trim())
    .filter(Boolean)
}

const resetProductForm = () => {
  const nextForm = productContentStore.getDefaultProductForm()
  Object.assign(productForm, nextForm)
  sellingPointsInput.value = ''
  selectedProductId.value = undefined
  generatedImages.value = {}
  productContentStore.lastGenerated = null
  hasFormChanges.value = false
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
  hasFormChanges.value = false
}

const handleSelectProduct = (productId) => {
  if (!productId) {
    resetProductForm()
    return
  }
  const product = productContentStore.products.find((item) => item.id === productId)
  if (!product) {
    return
  }
  activeProductPreviewId.value = product.id
  loadProductToForm(product)
  void loadSelectedProductResult(product.id)
}

const loadSelectedProductResult = async (productId) => {
  loadingSelectedProductResult.value = true
  generatedImages.value = {}
  try {
    const result = await productContentStore.fetchLatestGenerationForProduct(productId)
    if (!result) {
      productContentStore.lastGenerated = null
    }
  } catch (error) {
    productContentStore.lastGenerated = null
    if (error?.status === 404) {
      return
    }
    message.error(parseError(error, '加载产品历史文案失败'))
  } finally {
    loadingSelectedProductResult.value = false
  }
}

const openProductsDrawer = async () => {
  showProductsDrawer.value = true
  if (!productContentStore.products.length) {
    await productContentStore.fetchProducts({ page: 1, page_size: 50 })
  }
  activeProductPreviewId.value = selectedProductId.value || activeProductPreviewId.value || productContentStore.products[0]?.id || null
}

const handlePreviewProduct = (product) => {
  activeProductPreviewId.value = product.id
}

const handleUseProduct = (product) => {
  selectedProductId.value = product.id
  activeProductPreviewId.value = product.id
  loadProductToForm(product)
  message.success(`已载入产品：${product.name}`)
  void loadSelectedProductResult(product.id)
}

const handleEditProduct = (product) => {
  handleUseProduct(product)
  showProductsDrawer.value = false
}

const handleCreateNewProduct = () => {
  resetProductForm()
  activeProductPreviewId.value = null
  message.success('已切换到新建产品模式')
}

const handleResetToNewProduct = () => {
  handleCreateNewProduct()
  productKeyword.value = ''
}

const refreshProducts = async () => {
  await productContentStore.fetchProducts({ page: 1, page_size: 50 })
  if (!productContentStore.products.some((item) => item.id === activeProductPreviewId.value)) {
    activeProductPreviewId.value = productContentStore.products[0]?.id || null
  }
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
    isSavingProduct.value = true
    if (selectedProductId.value) {
      const updated = await productContentStore.updateProduct(selectedProductId.value, payload)
      loadProductToForm(updated)
      message.success('产品已更新')
    } else {
      const created = await productContentStore.createProduct(payload)
      selectedProductId.value = created.id
      loadProductToForm(created)
      message.success('产品已保存')
    }
    await productContentStore.fetchProducts({ page: 1, page_size: 50 })
    activeProductPreviewId.value = selectedProductId.value
    hasFormChanges.value = false
  } catch (error) {
    message.error(parseError(error, '保存产品失败'))
  } finally {
    isSavingProduct.value = false
  }
}

const handleDeleteProduct = async (product) => {
  deletingProductId.value = product.id
  try {
    await productContentStore.deleteProduct(product.id)
    if (selectedProductId.value === product.id) {
      resetProductForm()
    }
    if (activeProductPreviewId.value === product.id) {
      activeProductPreviewId.value = productContentStore.products[0]?.id || null
    }
    message.success(`已删除产品：${product.name}`)
  } catch (error) {
    message.error(parseError(error, '删除产品失败'))
  } finally {
    deletingProductId.value = null
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
      product_id: selectedProductId.value,
      prompt_external_id: selectedPromptExternalId.value,
      product: { ...productForm },
      styles: selectedStyles.value,
      count: count.value,
      channel: channel.value
    })
    if (productContentStore.lastGenerated?.product_id) {
      selectedProductId.value = productContentStore.lastGenerated.product_id
      activeProductPreviewId.value = productContentStore.lastGenerated.product_id
    }
    await productContentStore.fetchProducts({ page: 1, page_size: 50 })
    hasFormChanges.value = false
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
  generatingImageIndex.value = index
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
  } finally {
    generatingImageIndex.value = null
  }
}

const handleCopy = async (item) => {
  const fullText = `${item.title}\n\n${item.content}\n\n${(item.hashtags || []).join(' ')}`
  await navigator.clipboard.writeText(fullText)
  message.success('已复制文案')
}

const openSelectedPromptInManager = () => {
  if (!selectedPromptExternalId.value || !selectedPromptOption.value) {
    message.info('当前使用的是系统内置提示词，暂无原始提示词文件可查看')
    return
  }

  router.push({
    path: '/extensions/prompts',
    query: {
      external_id: selectedPromptExternalId.value
    }
  })
}

onMounted(async () => {
  await Promise.all([
    productContentStore.fetchQuota(),
    productContentStore.fetchProducts({ page: 1, page_size: 50 }),
    productContentStore.fetchPromptOptions()
  ])

  const queryPromptExternalId = String(route.query.prompt_external_id || '').trim()
  if (queryPromptExternalId) {
    const exists = (productContentStore.promptOptions || []).some((item) => item.external_id === queryPromptExternalId && item.is_compatible)
    if (exists) {
      selectedPromptExternalId.value = queryPromptExternalId
    }
  }

  const queryProductId = Number(route.query.product_id)
  if (Number.isInteger(queryProductId) && queryProductId > 0) {
    selectedProductId.value = queryProductId
    handleSelectProduct(queryProductId)
  }

  activeProductPreviewId.value = selectedProductId.value || productContentStore.products[0]?.id || null
})

watch(filteredProducts, (nextList) => {
  if (!nextList.length) {
    activeProductPreviewId.value = null
    return
  }
  if (!nextList.some((item) => item.id === activeProductPreviewId.value)) {
    activeProductPreviewId.value = nextList[0].id
  }
})

watch(formSnapshot, (nextSnapshot) => {
  if (!selectedProductId.value) {
    hasFormChanges.value = Boolean(productForm.name?.trim() || sellingPointsInput.value.trim() || attributesCount.value)
    return
  }
  hasFormChanges.value = nextSnapshot !== selectedProductSnapshot.value
})

watch(selectedProductSnapshot, (nextSnapshot) => {
  if (!selectedProductId.value) {
    return
  }
  hasFormChanges.value = formSnapshot.value !== nextSnapshot
})
</script>

<template>
  <div class="product-content-page">
    <section class="hero-panel">
      <div class="hero-copy">
        <span class="eyebrow">Product Content Studio</span>
        <h1>让产品信息直接变成可发布、可延展、可出图的内容资产</h1>
        <p>
          先整理产品画像，再组合渠道和风格，一次生成整组文案结果。整个界面围绕“输入更少、结果更清楚、继续操作更顺手”来设计。
        </p>
        <div class="hero-actions">
          <a-button type="primary" size="large" @click="handleGenerate" :loading="productContentStore.isGenerating" :disabled="!canGenerate || !productContentStore.hasQuota">
            <template #icon><Sparkles :size="16" /></template>
            立即生成
          </a-button>
          <a-button size="large" @click="router.push('/product-content/history')">
            查看记录
            <template #icon><ArrowRight :size="16" /></template>
          </a-button>
        </div>
        <div class="hero-tips">
          <span v-for="tip in previewTips" :key="tip">{{ tip }}</span>
        </div>
      </div>

      <div class="hero-stats-card" :class="quotaInfo.tone">
        <div class="stats-top">
          <div>
            <div class="stats-label">今日生成配额</div>
            <div class="stats-value">{{ quotaInfo.dailyText }}</div>
          </div>
          <div class="stats-chip">{{ productContentStore.currentQuota?.tier || 'free' }}</div>
        </div>
        <div class="stats-progress">
          <div class="stats-progress-bar" :style="{ width: `${quotaInfo.percentage}%` }"></div>
        </div>
        <div class="stats-meta">
          <div>
            <span>月度使用</span>
            <strong>{{ quotaInfo.monthlyText }}</strong>
          </div>
          <div>
            <span>当前状态</span>
            <strong>{{ quotaInfo.remainingText }}</strong>
          </div>
        </div>
        <a-alert
          v-if="!productContentStore.hasQuota"
          class="quota-inline-alert"
          type="warning"
          show-icon
          message="今日配额已用尽，可升级订阅或明日继续生成"
        />
      </div>
    </section>

    <section class="quick-metrics">
      <div class="metric-card soft-orange metric-card-clickable" @click="openProductsDrawer">
        <div class="metric-icon"><PackageSearch :size="18" /></div>
        <div>
          <span>已存产品</span>
          <strong>{{ savedProductsCount }}</strong>
        </div>
      </div>
      <div class="metric-card soft-blue">
        <div class="metric-icon"><SwatchBook :size="18" /></div>
        <div>
          <span>已选风格</span>
          <strong>{{ selectedStyles.length }}</strong>
        </div>
      </div>
      <div class="metric-card soft-green">
        <div class="metric-icon"><Layers3 :size="18" /></div>
        <div>
          <span>产品属性</span>
          <strong>{{ attributesCount }}</strong>
        </div>
      </div>
      <div class="metric-card soft-amber">
        <div class="metric-icon"><Wand2 :size="18" /></div>
        <div>
          <span>最近结果</span>
          <strong>{{ resultCount }}</strong>
        </div>
      </div>
    </section>

    <section class="studio-grid">
      <div class="editor-shell glass-panel">
          <div class="panel-heading">
            <div>
              <span class="panel-kicker">Step 1</span>
              <h3>产品信息编排</h3>
            </div>
            <a-space>
              <a-button type="link" @click="openProductsDrawer">管理已存产品</a-button>
              <a-button type="link" @click="router.push('/product-content/subscription')">查看订阅</a-button>
            </a-space>
        </div>

        <div class="editor-topline">
          <div class="picker-box">
            <span class="picker-label">复用已保存产品</span>
            <a-select
              v-model:value="selectedProductId"
              :options="productOptions"
              placeholder="选择后自动填充产品字段"
              allow-clear
              size="large"
              :disabled="productContentStore.loadingProducts"
              @change="handleSelectProduct"
            />
          </div>
          <div class="digest-box">
            <span>{{ resultContext.modeLabel }}</span>
            <span>{{ hasFormChanges ? '有未保存改动' : '已同步保存状态' }}</span>
            <span>卖点 {{ sellingPointsCount }}</span>
            <span>属性 {{ attributesCount }}</span>
            <span>渠道 {{ channel }}</span>
            <button type="button" class="digest-link" @click="handleResetToNewProduct">切换为新产品</button>
          </div>
        </div>

        <a-alert
          v-if="selectedProductId && hasFormChanges"
          class="editor-state-alert"
          type="info"
          show-icon
          :message="`你正在编辑「${selectedProductLabel}」，当前表单有未保存修改`"
          description="保存后可沉淀为新的产品资料版本；直接生成则会基于当前表单内容输出新结果。"
        />

        <a-form layout="vertical" class="editor-form">
          <div class="editor-section">
            <div class="editor-section-head">
              <span class="panel-kicker">基础档案</span>
              <p>先描述产品本身，帮助系统识别品类和视觉调性。</p>
            </div>
            <div class="editor-columns">
              <div class="field-group">
                <a-form-item label="产品名称" required>
                  <a-input v-model:value="productForm.name" size="large" placeholder="如：轻奢真丝衬衫" />
                </a-form-item>
                <a-form-item label="产品类目">
                  <a-input v-model:value="productForm.category" size="large" placeholder="如：服饰、家居、户外装备" />
                </a-form-item>
              </div>
              <div class="field-group field-group--three">
                <a-form-item label="材质">
                  <a-input v-model:value="productForm.material" size="large" placeholder="真丝 / 铝合金 / 原木" />
                </a-form-item>
                <a-form-item label="风格">
                  <a-input v-model:value="productForm.style" size="large" placeholder="极简 / 轻奢 / 户外感" />
                </a-form-item>
                <a-form-item label="颜色">
                  <a-input v-model:value="productForm.color" size="large" placeholder="奶油白 / 深海蓝 / 暖灰" />
                </a-form-item>
              </div>
            </div>
          </div>

          <div class="editor-section">
            <div class="editor-section-head">
              <span class="panel-kicker">使用场景</span>
              <p>再补充目标人群、适用场景和价格带，方便文案更贴近渠道语境。</p>
            </div>
            <div class="editor-columns two-wide">
              <a-form-item label="使用场景">
                <a-input v-model:value="productForm.scene" size="large" placeholder="如：通勤、居家、露营、礼赠" />
              </a-form-item>
              <a-form-item label="目标人群">
                <a-input v-model:value="productForm.target_audience" size="large" placeholder="如：25-35 岁都市女性" />
              </a-form-item>
            </div>

            <div class="editor-columns two-wide compact-grid">
              <a-form-item label="卖点关键词" extra="多个关键词请用分号（;）隔开">
                <a-input
                  v-model:value="sellingPointsInput"
                  size="large"
                  placeholder="例如：垂坠显瘦; 抗皱免烫; 适合通勤"
                  @blur="syncSellingPointsArray"
                />
              </a-form-item>
              <a-form-item label="价格区间">
                <a-input v-model:value="productForm.price_range" size="large" placeholder="如：199-399 元" />
              </a-form-item>
            </div>
          </div>

          <div class="attribute-box editor-section">
            <div class="attribute-head">
              <div>
                <span class="panel-kicker">补充属性</span>
                <h4>用更细颗粒度的信息增强生成结果</h4>
                <p>适合填写工艺、规格、功能、包装等结构化信息。</p>
              </div>
            </div>
            <div class="attribute-controls">
              <a-input v-model:value="attributeKey" size="large" placeholder="属性名，如：工艺" />
              <a-input v-model:value="attributeValue" size="large" placeholder="属性值，如：双层锁边" />
              <a-button type="primary" size="large" @click="handleAddAttribute">添加属性</a-button>
            </div>
            <div class="attribute-tags">
              <a-tag
                v-for="(value, key) in productForm.attributes"
                :key="key"
                class="attribute-tag"
                closable
                @close.prevent="handleRemoveAttribute(key)"
              >
                {{ key }} / {{ value }}
              </a-tag>
              <span v-if="!attributesCount" class="empty-inline">暂无补充属性</span>
            </div>
          </div>

          <div class="editor-actions">
            <a-button size="large" @click="handleCreateOrUpdateProduct" :loading="isSavingProduct" :disabled="!canSaveProduct">{{ selectedProductId ? '保存当前修改' : '保存产品资料' }}</a-button>
            <a-button type="primary" size="large" @click="handleGenerate" :loading="productContentStore.isGenerating" :disabled="!canGenerate || !productContentStore.hasQuota">
              生成整组文案
            </a-button>
          </div>
        </a-form>
      </div>

      <div class="control-shell">
        <div class="glass-panel control-panel">
          <div class="panel-heading compact">
            <div>
              <span class="panel-kicker">Step 2</span>
              <h3>生成策略</h3>
            </div>
          </div>

          <a-form layout="vertical">
            <a-form-item label="提示词方案">
              <a-select
                :value="selectedPromptExternalId || '__builtin__'"
                :options="promptOptions"
                size="large"
                show-search
                :filter-option="filterPromptOption"
                option-filter-prop="label"
                :loading="productContentStore.loadingPromptOptions"
                placeholder="搜索提示词名称、路径或 external_id"
                @change="(value) => { selectedPromptExternalId = value === '__builtin__' ? undefined : value }"
              >
                <template #option="{ label, value, disabled, meta }">
                  <a-tooltip v-if="disabled" placement="left">
                    <template #title>
                      <div class="prompt-tooltip-content">
                        <div class="prompt-tooltip-title">{{ meta?.path || label }}</div>
                        <div class="prompt-tooltip-line is-warning">缺少变量：{{ meta?.missing_variables?.join('、') || '无' }}</div>
                        <div class="prompt-tooltip-line">额外变量：{{ meta?.extra_variables?.join('、') || '无' }}</div>
                        <div class="prompt-tooltip-line">已识别变量：{{ meta?.detected_variables?.join('、') || '无' }}</div>
                      </div>
                    </template>
                    <div class="prompt-option-row" :class="{ 'is-disabled': disabled }">
                      <div class="prompt-option-top">
                        <strong>{{ getPromptFileName(meta?.path, label) }}</strong>
                        <a-tag v-if="value === '__builtin__'" color="gold">内置</a-tag>
                        <a-tag v-else-if="disabled" color="red">变量不完整</a-tag>
                      </div>
                      <div class="prompt-option-path">{{ meta?.path || label }}</div>
                      <div class="prompt-option-meta">external_id：{{ meta?.external_id || value }}</div>
                    </div>
                  </a-tooltip>
                  <div v-else class="prompt-option-row" :class="{ 'is-disabled': disabled }">
                    <div class="prompt-option-top">
                      <strong>{{ getPromptFileName(meta?.path, label) }}</strong>
                      <a-tag v-if="value === '__builtin__'" color="gold">内置</a-tag>
                    </div>
                    <div class="prompt-option-path">{{ meta?.path || label }}</div>
                    <div class="prompt-option-meta">external_id：{{ meta?.external_id || value }}</div>
                  </div>
                </template>
              </a-select>
              <div class="prompt-strategy-card">
                <div class="prompt-strategy-head">
                  <span class="prompt-strategy-badge">{{ promptStrategySummary.modeLabel }}</span>
                  <div class="prompt-strategy-actions">
                    <a-button type="link" size="small" @click="productContentStore.fetchPromptOptions()">刷新提示词</a-button>
                    <a-button type="link" size="small" @click="openSelectedPromptInManager">查看原提示词</a-button>
                  </div>
                </div>
                <p>{{ promptStrategySummary.description }}</p>
                <span>{{ promptStrategySummary.detail }}</span>
              </div>
              <div v-if="selectedPromptOption" class="prompt-variable-row">
                <span>必需变量</span>
                <a-tag v-for="item in requiredPromptVariables" :key="item" color="blue">{{ item }}</a-tag>
              </div>
              <div class="prompt-variable-row prompt-search-tip">
                <span>可按提示词名称、路径或 external_id 搜索</span>
              </div>
              <div class="prompt-variable-row prompt-search-tip">
                <span>将鼠标悬停在不可用提示词上，可查看缺失变量与额外变量说明</span>
              </div>
            </a-form-item>
            <a-form-item label="发布渠道">
              <a-select v-model:value="channel" :options="channelOptions" size="large" />
            </a-form-item>
            <a-form-item label="文案风格">
              <div class="style-grid">
                <button
                  v-for="style in styleOptions"
                  :key="style"
                  type="button"
                  class="style-pill"
                  :class="{ active: selectedStyles.includes(style) }"
                  @click="selectedStyles = selectedStyles.includes(style) ? selectedStyles.filter((item) => item !== style) : [...selectedStyles, style]"
                >
                  {{ style }}
                </button>
              </div>
            </a-form-item>
            <a-form-item label="生成条数">
              <a-slider v-model:value="count" :min="1" :max="20" />
              <div class="count-badge">输出 {{ count }} 条结果</div>
            </a-form-item>
          </a-form>

          <div class="formula-card">
            <span class="panel-kicker">本次组合</span>
            <h4>{{ selectedStyleSummary || '请选择风格' }}</h4>
            <p>{{ productForm.name || '未填写产品名称' }} · {{ channel }}</p>
            <strong class="formula-hint">{{ resultContext.modeHint }}</strong>
            <span class="formula-subhint">提示词方案：{{ promptStrategySummary.modeLabel }}</span>
          </div>
        </div>
      </div>
    </section>

    <section class="results-shell glass-panel">
      <div class="panel-heading results-head">
        <div>
          <span class="panel-kicker">Step 3</span>
          <h3>生成结果</h3>
          <p>
            {{ selectedProductId ? '已自动展示当前产品最近一次生成结果，方便继续复用或生图。' : '标题、正文、标签和图片提示词集中展示，方便继续复制或生图。' }}
          </p>
          <p v-if="hasFormChanges && selectedProductId" class="results-helper">你正在编辑已保存产品，当前结果可能与表单内容不完全一致，保存或重新生成后会同步。</p>
        </div>
        <div class="result-summary">
          <span>{{ resultCount }} 条结果</span>
          <span>{{ resultContext.resultBadge }}</span>
          <span v-if="currentResultMeta.toneStyles?.length">{{ currentResultMeta.toneStyles.join(' / ') }}</span>
          <span>{{ currentResultMeta.channel }}</span>
          <span>{{ currentResultMeta.promptName || '系统内置提示词' }}</span>
        </div>
      </div>

      <a-alert
        v-if="selectedProductId || (!loadingSelectedProductResult && resultItems.length)"
        class="results-alert"
        :type="resultContext.alertType"
        show-icon
        :message="resultContext.alertMessage"
      />

      <div v-if="!loadingSelectedProductResult && resultItems.length" class="results-meta-bar">
        <span>模式：{{ resultContext.modeLabel }}</span>
        <span v-if="selectedProductId">来源：{{ selectedProduct?.name || productForm.name || '已保存产品' }}</span>
        <span v-if="hasFormChanges && selectedProductId">状态：表单有未保存修改</span>
        <span v-if="currentResultTimestamp">生成时间：{{ currentResultTimestamp }}</span>
        <span>渠道：{{ currentResultMeta.channel }}</span>
        <span>提示词：{{ currentResultMeta.promptName || '系统内置提示词' }}</span>
      </div>

      <a-empty
        v-if="!loadingSelectedProductResult && resultItems.length === 0"
        :description="selectedProductId ? '该产品暂时没有历史生成结果，点击上方按钮开始生成第一组文案' : '先填写产品信息，再生成第一组文案'"
      />

      <a-skeleton v-else-if="loadingSelectedProductResult" active :paragraph="{ rows: 6 }" />

      <div v-else class="result-list">
        <article v-for="(item, index) in resultItems" :key="`${item.style}-${index}`" class="result-card">
          <div class="result-card-head">
            <div class="result-labels">
              <span class="style-badge">{{ item.style }}</span>
              <span class="result-index">No.{{ index + 1 }}</span>
            </div>
            <div class="result-actions">
              <a-button size="small" @click="handleCopy(item)">
                <template #icon><Copy :size="14" /></template>
                复制
              </a-button>
              <a-button size="small" type="primary" :loading="generatingImageIndex === index" @click="handleGenerateImage(item, index)">
                <template #icon><Image :size="14" /></template>
                {{ generatedImages[index] ? '重新生成' : '生图' }}
              </a-button>
            </div>
          </div>

          <h4>{{ item.title || '未返回标题' }}</h4>
          <p class="content-text">{{ item.content || '未返回正文' }}</p>

          <div class="hashtags">
            <a-tag v-for="tag in item.hashtags" :key="tag" class="hash-tag">{{ tag }}</a-tag>
          </div>

          <div class="prompt-box">
            <span>图片提示词</span>
            <p>{{ item.image_prompt || '无' }}</p>
          </div>

          <img v-if="generatedImages[index]" :src="generatedImages[index]" alt="generated image" class="generated-image" />
        </article>
      </div>
    </section>

    <a-drawer
      v-model:open="showProductsDrawer"
      title="已保存产品"
      placement="right"
      :width="980"
      class="products-drawer"
    >
      <div class="drawer-toolbar">
        <a-input
          v-model:value="productKeyword"
          size="large"
          placeholder="搜索名称、类目、场景、风格"
        />
        <a-space>
          <a-button @click="refreshProducts" :loading="productContentStore.loadingProducts">
            <template #icon><RefreshCw :size="14" /></template>
            刷新
          </a-button>
          <a-button type="primary" @click="handleCreateNewProduct">
            <template #icon><Plus :size="14" /></template>
            新建产品
          </a-button>
        </a-space>
      </div>

      <div class="drawer-layout">
        <div class="product-list-panel">
          <div v-if="filteredProducts.length === 0" class="drawer-empty">没有匹配的已保存产品</div>
          <button
            v-for="product in filteredProducts"
            :key="product.id"
            type="button"
            class="product-list-card"
            :class="{ active: activeProductPreview?.id === product.id }"
            @click="handlePreviewProduct(product)"
          >
            <div class="product-list-top">
              <div>
                <strong>{{ product.name }}</strong>
                <span>{{ product.category || 'general' }}</span>
              </div>
              <a-tag v-if="selectedProductId === product.id" color="blue">当前使用中</a-tag>
            </div>
            <p>{{ product.scene || product.target_audience || '暂无场景或目标人群描述' }}</p>
            <div class="product-list-meta">
              <span>卖点 {{ (product.selling_points || []).length }}</span>
              <span>属性 {{ Object.keys(product.attributes || {}).length }}</span>
            </div>
          </button>
        </div>

        <div class="product-preview-panel" v-if="activeProductPreview">
          <div class="product-preview-top">
            <div>
              <span class="panel-kicker">Product Profile</span>
              <h3>{{ activeProductPreview.name }}</h3>
              <p>{{ activeProductPreview.category || 'general' }} · {{ activeProductTimestamp }}</p>
            </div>
            <a-space>
              <a-button @click="handleUseProduct(activeProductPreview)">
                <template #icon><Eye :size="14" /></template>
                查看并载入
              </a-button>
              <a-button type="primary" @click="handleEditProduct(activeProductPreview)">
                <template #icon><Pencil :size="14" /></template>
                编辑
              </a-button>
              <a-popconfirm
                title="确认删除该产品吗？"
                ok-text="删除"
                cancel-text="取消"
                @confirm="handleDeleteProduct(activeProductPreview)"
              >
                <a-button danger :loading="deletingProductId === activeProductPreview.id">
                  <template #icon><Trash2 :size="14" /></template>
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </div>

          <div class="product-preview-grid">
            <div class="preview-info-card">
              <span>基础信息</span>
              <ul>
                <li><strong>材质</strong><em>{{ activeProductPreview.material || '未填写' }}</em></li>
                <li><strong>风格</strong><em>{{ activeProductPreview.style || '未填写' }}</em></li>
                <li><strong>颜色</strong><em>{{ activeProductPreview.color || '未填写' }}</em></li>
                <li><strong>场景</strong><em>{{ activeProductPreview.scene || '未填写' }}</em></li>
                <li><strong>人群</strong><em>{{ activeProductPreview.target_audience || '未填写' }}</em></li>
                <li><strong>价格</strong><em>{{ activeProductPreview.price_range || '未填写' }}</em></li>
              </ul>
            </div>

            <div class="preview-info-card">
              <span>卖点关键词</span>
              <div class="preview-tags">
                <a-tag v-for="point in activeProductPreview.selling_points || []" :key="point">{{ point }}</a-tag>
                <span v-if="!(activeProductPreview.selling_points || []).length" class="empty-inline">暂无卖点</span>
              </div>
            </div>

            <div class="preview-info-card wide">
              <span>补充属性</span>
              <div class="preview-tags">
                <a-tag v-for="(value, key) in activeProductPreview.attributes || {}" :key="key">{{ key }} / {{ value }}</a-tag>
                <span v-if="!Object.keys(activeProductPreview.attributes || {}).length" class="empty-inline">暂无补充属性</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="product-preview-panel preview-empty-panel">
          <a-empty description="选择一个已保存产品查看详情，或直接创建新的产品资料" />
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<style scoped>
.product-content-page {
  --pc-bg-1: #fff9f2;
  --pc-bg-2: #eef6ff;
  --pc-panel: rgba(255, 255, 255, 0.78);
  --pc-border: rgba(15, 23, 42, 0.08);
  --pc-shadow: 0 28px 60px rgba(27, 52, 92, 0.12);
  --pc-accent: #d97706;
  --pc-accent-soft: rgba(217, 119, 6, 0.1);
  --pc-blue: #2563eb;
  --pc-green: #0f766e;
  --pc-text: #172033;
  --pc-muted: #60708a;
  padding: 28px;
  min-height: 100%;
  background:
    radial-gradient(circle at top left, rgba(245, 158, 11, 0.18), transparent 32%),
    radial-gradient(circle at 90% 12%, rgba(37, 99, 235, 0.16), transparent 26%),
    linear-gradient(180deg, var(--pc-bg-1), var(--pc-bg-2));
}

.hero-panel,
.studio-grid,
.quick-metrics,
.results-shell {
  max-width: 1340px;
  margin: 0 auto;
}

.hero-panel {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr;
  gap: 20px;
  margin-bottom: 18px;
}

.hero-copy {
  padding: 8px 0;
}

.eyebrow,
.panel-kicker {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.55);
  color: var(--pc-accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero-copy h1 {
  margin: 14px 0 14px;
  font-size: 42px;
  line-height: 1.12;
  font-weight: 800;
  color: var(--pc-text);
  max-width: 760px;
}

.hero-copy p {
  max-width: 720px;
  color: var(--pc-muted);
  font-size: 16px;
}

.hero-actions {
  display: flex;
  gap: 12px;
  margin-top: 22px;
}

.hero-tips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.hero-tips span {
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.66);
  border: 1px solid rgba(255, 255, 255, 0.75);
  color: #4f5f78;
}

.glass-panel,
.hero-stats-card,
.metric-card,
.result-card {
  backdrop-filter: blur(14px);
  background: var(--pc-panel);
  border: 1px solid var(--pc-border);
  box-shadow: var(--pc-shadow);
}

.hero-stats-card {
  border-radius: 28px;
  padding: 24px;
  align-self: start;
}

.hero-stats-card.warning {
  border-color: rgba(217, 119, 6, 0.28);
}

.stats-top,
.stats-meta {
  display: flex;
  justify-content: space-between;
  gap: 14px;
}

.stats-label {
  color: var(--pc-muted);
  font-size: 13px;
}

.stats-value {
  margin-top: 6px;
  font-size: 34px;
  font-weight: 800;
  color: var(--pc-text);
}

.stats-chip {
  align-self: start;
  padding: 8px 12px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.14), rgba(245, 158, 11, 0.12));
  color: var(--pc-blue);
  font-weight: 700;
  text-transform: capitalize;
}

.stats-progress {
  height: 10px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.18);
  margin: 22px 0 20px;
}

.stats-progress-bar {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #f59e0b, #2563eb);
}

.stats-meta div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.quota-inline-alert {
  margin-top: 16px;
}

.stats-meta span {
  color: var(--pc-muted);
  font-size: 13px;
}

.stats-meta strong {
  color: var(--pc-text);
}

.quick-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.metric-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px;
  border-radius: 22px;
}

.metric-card span {
  display: block;
  color: var(--pc-muted);
  font-size: 13px;
}

.metric-card strong {
  display: block;
  margin-top: 2px;
  color: var(--pc-text);
  font-size: 28px;
  font-weight: 800;
}

.metric-card-clickable {
  cursor: pointer;
}

.metric-card-clickable:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 32px rgba(27, 52, 92, 0.16);
}

.metric-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
}

.soft-orange .metric-icon,
.soft-orange {
  background: linear-gradient(180deg, rgba(255, 244, 230, 0.95), rgba(255, 251, 245, 0.85));
}

.soft-blue .metric-icon,
.soft-blue {
  background: linear-gradient(180deg, rgba(235, 244, 255, 0.95), rgba(248, 251, 255, 0.85));
}

.soft-green .metric-icon,
.soft-green {
  background: linear-gradient(180deg, rgba(230, 249, 244, 0.95), rgba(245, 253, 249, 0.85));
}

.soft-amber .metric-icon,
.soft-amber {
  background: linear-gradient(180deg, rgba(255, 245, 221, 0.95), rgba(255, 250, 239, 0.85));
}

.studio-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(300px, 0.72fr);
  gap: 18px;
  align-items: start;
}

.editor-shell,
.control-panel,
.results-shell {
  border-radius: 28px;
  padding: 24px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: start;
  gap: 12px;
  margin-bottom: 18px;
}

.panel-heading h3 {
  margin: 10px 0 0;
  font-size: 24px;
  font-weight: 800;
  color: var(--pc-text);
}

.panel-heading p {
  margin-top: 8px;
  color: var(--pc-muted);
}

.editor-state-alert {
  margin-bottom: 16px;
}

.results-helper {
  margin-top: 8px;
  color: #925d07;
  font-size: 13px;
  line-height: 1.6;
}

.editor-topline {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  align-items: end;
  margin-bottom: 18px;
}

.picker-box,
.digest-box,
.formula-card,
.attribute-box,
.prompt-box {
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.picker-box {
  padding: 14px;
}

.picker-label {
  display: block;
  margin-bottom: 8px;
  color: var(--pc-muted);
  font-size: 13px;
}

.digest-box {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 12px 14px;
}

.digest-box span {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.08);
  color: #925d07;
  font-size: 13px;
}

.digest-link {
  padding: 8px 12px;
  border: 1px dashed rgba(37, 99, 235, 0.22);
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.06);
  color: var(--pc-blue);
  font-size: 13px;
  cursor: pointer;
}

.editor-form :deep(.ant-form-item) {
  margin-bottom: 16px;
}

.editor-section {
  padding: 18px;
  margin-bottom: 16px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(255, 255, 255, 0.82);
}

.editor-section-head {
  margin-bottom: 14px;
}

.editor-section-head p,
.attribute-head p {
  margin: 10px 0 0;
  color: var(--pc-muted);
  font-size: 13px;
  line-height: 1.6;
}

.editor-form :deep(.ant-form-item-label > label) {
  color: var(--pc-text);
  font-weight: 600;
}

.editor-columns {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}

.field-group {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field-group--three {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.two-wide {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.compact-grid {
  align-items: start;
}

.attribute-box {
  margin-top: 6px;
}

.attribute-head h4 {
  margin: 10px 0 0;
  color: var(--pc-text);
  font-size: 18px;
  font-weight: 700;
}

.attribute-controls {
  display: grid;
  grid-template-columns: 0.95fr 1.2fr auto;
  gap: 12px;
  margin-top: 14px;
}

.attribute-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.attribute-tag {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
}

.empty-inline {
  color: var(--pc-muted);
  font-size: 13px;
}

.editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}

.control-shell {
  position: sticky;
  top: 20px;
}

.style-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.style-pill {
  padding: 10px 14px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  color: var(--pc-text);
  cursor: pointer;
  transition: all 0.2s ease;
}

.style-pill.active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(217, 119, 6, 0.12));
  border-color: rgba(37, 99, 235, 0.22);
  color: var(--pc-blue);
  box-shadow: 0 10px 24px rgba(37, 99, 235, 0.12);
}

.count-badge {
  margin-top: 10px;
  color: var(--pc-muted);
  text-align: right;
}

.formula-card {
  margin-top: 18px;
  padding: 16px;
}

.formula-card h4 {
  margin: 10px 0 6px;
  font-size: 20px;
  font-weight: 800;
  color: var(--pc-text);
}

.formula-card p {
  color: var(--pc-muted);
}

.formula-subhint {
  display: block;
  margin-top: 10px;
  color: var(--pc-blue);
  font-size: 13px;
  font-weight: 600;
}

.formula-hint {
  display: block;
  margin-top: 10px;
  color: #925d07;
  font-size: 13px;
  line-height: 1.6;
}

.results-shell {
  margin-top: 18px;
}

.results-head {
  margin-bottom: 20px;
}

.result-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.result-summary span {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.65);
  color: var(--pc-muted);
}

.results-alert {
  margin-bottom: 14px;
}

.prompt-strategy-card {
  margin-top: 10px;
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.58);
  border: 1px solid rgba(37, 99, 235, 0.12);
}

.prompt-strategy-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.prompt-strategy-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.prompt-strategy-badge {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: var(--pc-blue);
  font-size: 12px;
  font-weight: 700;
}

.prompt-strategy-card p {
  margin: 8px 0 4px;
  color: var(--pc-text);
}

.prompt-strategy-card span {
  color: var(--pc-muted);
  font-size: 13px;
}

.prompt-option-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 2px 0;
}

.prompt-option-row.is-disabled {
  opacity: 0.8;
}

.prompt-option-top {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prompt-option-top strong {
  color: var(--pc-text);
  font-size: 13px;
}

.prompt-option-path,
.prompt-option-meta {
  color: var(--pc-muted);
  font-size: 12px;
  line-height: 1.5;
}

.prompt-option-hint {
  color: var(--pc-muted);
  font-size: 12px;
  line-height: 1.5;
}

.prompt-option-hint.is-warning {
  color: #b45309;
  font-weight: 600;
}

.prompt-tooltip-content {
  max-width: 360px;
}

.prompt-tooltip-title {
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
}

.prompt-tooltip-line {
  font-size: 12px;
  line-height: 1.6;
}

.prompt-tooltip-line.is-warning {
  color: #fbbf24;
}

.prompt-variable-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  color: var(--pc-muted);
}


.results-meta-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;
}

.results-meta-bar span {
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: var(--pc-blue);
  font-size: 13px;
}

.result-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.result-card {
  border-radius: 24px;
  padding: 18px;
}

.result-card-head,
.result-labels,
.result-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.result-labels,
.result-actions {
  justify-content: flex-start;
}

.result-card-head {
  margin-bottom: 12px;
}

.style-badge,
.result-index {
  display: inline-flex;
  padding: 8px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.style-badge {
  background: rgba(217, 119, 6, 0.1);
  color: var(--pc-accent);
}

.result-index {
  background: rgba(37, 99, 235, 0.08);
  color: var(--pc-blue);
}

.result-card h4 {
  margin: 8px 0 10px;
  font-size: 20px;
  font-weight: 800;
  color: var(--pc-text);
}

.content-text {
  white-space: pre-wrap;
  color: #334155;
  line-height: 1.75;
}

.hashtags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0;
}

.hash-tag {
  border-radius: 999px;
  padding: 4px 10px;
}

.prompt-box {
  padding: 14px;
}

.prompt-box span {
  display: block;
  color: var(--pc-muted);
  font-size: 12px;
  margin-bottom: 6px;
}

.prompt-box p {
  color: var(--pc-text);
  line-height: 1.7;
}

.generated-image {
  width: 100%;
  margin-top: 14px;
  border-radius: 18px;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border: 1px solid rgba(148, 163, 184, 0.16);
}

.drawer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.drawer-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 16px;
}

.product-list-panel,
.product-preview-panel {
  background: rgba(255, 255, 255, 0.74);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 24px;
  padding: 14px;
}

.product-list-panel {
  max-height: calc(100vh - 210px);
  overflow: auto;
}

.drawer-empty {
  padding: 24px 12px;
  color: var(--pc-muted);
  text-align: center;
}

.product-list-card {
  width: 100%;
  text-align: left;
  padding: 14px;
  margin-bottom: 10px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: rgba(255, 255, 255, 0.76);
  cursor: pointer;
  transition: all 0.2s ease;
}

.product-list-card.active {
  border-color: rgba(37, 99, 235, 0.22);
  box-shadow: 0 14px 26px rgba(37, 99, 235, 0.1);
  transform: translateY(-1px);
}

.product-list-top,
.product-preview-top {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  align-items: flex-start;
}

.product-list-top strong,
.product-preview-top h3 {
  color: var(--pc-text);
}

.product-list-top span,
.product-list-card p,
.product-preview-top p {
  color: var(--pc-muted);
}

.product-list-card p {
  margin: 8px 0;
  line-height: 1.6;
}

.product-list-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.product-list-meta span {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(245, 158, 11, 0.08);
  color: #925d07;
  font-size: 12px;
}

.product-preview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 18px;
}

.preview-info-card {
  padding: 16px;
  border-radius: 20px;
  background: rgba(248, 250, 252, 0.82);
}

.preview-info-card.wide {
  grid-column: 1 / -1;
}

.preview-info-card > span {
  display: block;
  margin-bottom: 10px;
  color: var(--pc-muted);
  font-size: 13px;
}

.preview-info-card ul {
  display: grid;
  gap: 10px;
  list-style: none;
  padding: 0;
  margin: 0;
}

.preview-info-card li {
  display: flex;
  justify-content: space-between;
  gap: 14px;
}

.preview-info-card strong {
  color: var(--pc-text);
}

.preview-info-card em {
  color: var(--pc-muted);
  font-style: normal;
  text-align: right;
}

.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.product-content-page :deep(.ant-alert) {
  border-radius: 18px;
}

.preview-empty-panel {
  display: grid;
  min-height: 320px;
  place-items: center;
}

.product-content-page :deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #d97706, #2563eb);
  border: none;
  box-shadow: 0 14px 24px rgba(37, 99, 235, 0.18);
}

.product-content-page :deep(.ant-input),
.product-content-page :deep(.ant-input-affix-wrapper),
.product-content-page :deep(.ant-select-selector),
.product-content-page :deep(.ant-input-number),
.product-content-page :deep(.ant-input-number-input-wrap textarea),
.product-content-page :deep(textarea.ant-input) {
  border-radius: 16px !important;
  border-color: rgba(15, 23, 42, 0.08) !important;
  box-shadow: none !important;
}

.product-content-page :deep(.ant-slider-track) {
  background: linear-gradient(90deg, #f59e0b, #2563eb);
}

.product-content-page :deep(.ant-slider-handle::after) {
  box-shadow: 0 0 0 2px #fff, 0 0 0 6px rgba(37, 99, 235, 0.14);
}

@media (max-width: 1180px) {
  .hero-panel,
  .studio-grid,
  .result-list,
  .quick-metrics {
    grid-template-columns: 1fr;
  }

  .control-shell {
    position: static;
  }
}

@media (max-width: 900px) {
  .product-content-page {
    padding: 16px;
  }

  .hero-copy h1 {
    font-size: 30px;
  }

  .hero-actions,
  .editor-actions,
  .drawer-toolbar,
  .attribute-controls,
  .field-group,
  .field-group--three,
  .two-wide,
  .editor-topline,
  .stats-top,
  .stats-meta,
  .result-card-head,
  .product-preview-top {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: stretch;
  }

  .hero-actions :deep(.ant-btn),
  .editor-actions :deep(.ant-btn) {
    width: 100%;
  }

  .attribute-controls {
    display: grid;
  }

  .drawer-layout,
  .product-preview-grid {
    grid-template-columns: 1fr;
  }
}
</style>
