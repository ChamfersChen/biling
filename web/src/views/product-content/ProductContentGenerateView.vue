<template>
  <div class="page">
    <section class="top-bar">
      <div class="top-bar__main">
        <span class="top-bar__kicker">Product Content</span>
        <h1>产品文案生成</h1>
        <p>填写产品信息，选择风格和渠道，一键生成文案。</p>
        <div class="top-bar__highlights">
          <span class="highlight-pill">支持多风格批量生成</span>
          <span class="highlight-pill">可复用已保存产品</span>
          <span class="highlight-pill">可直接回看历史记录</span>
        </div>
      </div>
      <div class="top-bar__side">
        <div class="top-bar__card">
          <span class="top-bar__card-label">当前工作流</span>
          <strong>产品信息 -> 提示词方案 -> 文案结果</strong>
          <p>先完善产品描述，再选择提示词和风格，生成后可继续生图或复用历史结果。</p>
          <div class="top-bar__actions">
            <a-button size="large" @click="router.push('/product-content/history')">查看记录</a-button>
          </div>
        </div>
      </div>
    </section>

    <section class="workspace">
      <div class="editor-panel">
        <div class="panel-header">
          <span>产品信息</span>
          <a-button type="link" size="small" @click="openProductsDrawer">
            <template #icon><PackageSearch :size="14" /></template>
            从已存产品中选择
          </a-button>
        </div>

        <div class="editor-form">
          <a-textarea v-model:value="productForm.name" :rows="3" size="large" placeholder="请描述产品，如：一款适合通勤和日常穿着的轻奢真丝衬衫，主打垂坠感和舒适面料，目标用户是25-35岁的都市女性。" />
          <div class="form-row form-row--three">
            <a-input v-model:value="productForm.material" size="large" placeholder="材质" />
            <a-input v-model:value="productForm.style" size="large" placeholder="风格" />
            <a-input v-model:value="productForm.color" size="large" placeholder="颜色" />
          </div>
          <div class="form-row form-row--two">
            <a-input v-model:value="productForm.scene" size="large" placeholder="使用场景，如：通勤" />
            <a-input v-model:value="productForm.target_audience" size="large" placeholder="目标人群，如：25-35岁女性" />
          </div>
          <div class="form-row form-row--two">
            <a-input v-model:value="sellingPointsInput" size="large" placeholder="卖点关键词，用分号隔开" @blur="syncSellingPointsArray" />
            <a-input v-model:value="productForm.price_range" size="large" placeholder="价格区间，如：199-399元" />
          </div>
          <div class="form-attrs">
            <div class="form-attrs__add">
              <a-input v-model:value="attributeKey" size="small" placeholder="属性名" />
              <a-input v-model:value="attributeValue" size="small" placeholder="属性值" />
              <a-button size="small" @click="handleAddAttribute">添加</a-button>
            </div>
            <div class="form-attrs__tags">
              <a-tag v-for="(value, key) in productForm.attributes" :key="key" closable @close.prevent="handleRemoveAttribute(key)">{{ key }} / {{ value }}</a-tag>
              <span v-if="!attributesCount" class="empty-hint">可选补充属性</span>
            </div>
          </div>
          <div class="form-images">
            <div class="form-images__head">
              <span>参考图片</span>
              <a-upload
                :show-upload-list="false"
                :before-upload="handleBeforeUploadImage"
                accept="image/png,image/jpeg,image/webp"
              >
                <a-button size="small" :loading="uploadingImage">上传图片</a-button>
              </a-upload>
            </div>
            <div v-if="productForm.image_paths?.length" class="form-images__list">
              <div v-for="(imgUrl, idx) in productForm.image_paths" :key="idx" class="form-images__item">
                <img :src="imgUrl" alt="" class="form-images__thumb" />
                <a-button type="text" size="small" danger @click="handleRemoveImage(idx)">删除</a-button>
              </div>
            </div>
            <span v-else class="empty-hint">暂无参考图片，上传后可辅助文案生成</span>
          </div>
        </div>

        <div class="editor-actions">
          <div class="editor-actions__left">
            <a-button @click="handleClearForm" danger>清除产品信息</a-button>
          </div>
          <div class="editor-actions__right">
            <a-button @click="handleCreateOrUpdateProduct" :loading="isSavingProduct" :disabled="!canSaveProduct">{{ selectedProductId ? '保存修改' : '保存产品资料' }}</a-button>
            <a-button type="primary" @click="handleGenerate" :loading="productContentStore.isGenerating" :disabled="!canGenerate || !productContentStore.hasQuota">
              <template #icon><Sparkles :size="16" /></template>
              生成文案
            </a-button>
          </div>
        </div>
      </div>

      <div class="config-panel">
        <div class="panel-header">
          <span>生成设置</span>
        </div>

        <a-form layout="vertical">
          <a-form-item label="提示词方案">
            <a-select
              v-model:value="selectedPromptExternalId"
              :options="promptOptions"
              size="large"
              show-search
              :filter-option="filterPromptOption"
              :loading="productContentStore.loadingPromptOptions"
              placeholder="默认使用系统内置提示词"
              allow-clear
              @change="(value) => { selectedPromptExternalId = value === '__builtin__' ? undefined : value }"
            >
              <template #option="{ label, value, disabled, meta }">
                <div class="prompt-option" :class="{ 'prompt-option--disabled': disabled }">
                  <strong>{{ getPromptFileName(meta?.path, label) }}</strong>
                  <span class="prompt-option__path">{{ meta?.path }}</span>
                  <a-tag v-if="value === '__builtin__'" color="gold">内置</a-tag>
                  <a-tag v-else-if="disabled" color="red">不可用</a-tag>
                  <a-tag v-else color="green">可用</a-tag>
                </div>
              </template>
            </a-select>
            <div v-if="promptStrategySummary" class="prompt-summary">
              <span class="prompt-summary__badge">{{ promptStrategySummary.modeLabel }}</span>
              <span class="prompt-summary__detail">{{ promptStrategySummary.description }}</span>
              <a-button type="link" size="small" @click="openSelectedPromptInManager">查看原提示词</a-button>
            </div>
          </a-form-item>
          <a-form-item label="发布渠道">
            <a-select v-model:value="channel" :options="channelOptions" size="large" />
          </a-form-item>
          <a-form-item label="文案风格（可多选）">
            <div class="style-grid">
              <button v-for="style in styleOptions" :key="style" type="button" class="style-pill" :class="{ active: selectedStyles.includes(style) }" @click="selectedStyles = selectedStyles.includes(style) ? selectedStyles.filter((s) => s !== style) : [...selectedStyles, style]">{{ style }}</button>
            </div>
          </a-form-item>
          <a-form-item label="生成条数">
            <a-slider v-model:value="count" :min="1" :max="20" />
            <div class="count-note">{{ count }} 条</div>
          </a-form-item>
        </a-form>
      </div>
    </section>

    <section class="results-panel" v-if="resultItems.length || loadingSelectedProductResult">
      <div class="panel-header">
        <span>生成结果</span>
        <span class="result-summary" v-if="resultItems.length">{{ resultCount }} 条 · {{ currentResultMeta.channel }} · {{ currentResultMeta.toneStyles?.join('/') }}</span>
      </div>

      <a-skeleton v-if="loadingSelectedProductResult" active :paragraph="{ rows: 4 }" />
      <a-empty v-else-if="!resultItems.length" description="暂无结果" />

      <div v-else class="result-grid">
        <article v-for="(item, index) in resultItems" :key="index" class="result-card">
          <div class="result-card__top">
            <span class="result-style">{{ item.style }}</span>
            <span class="result-num">#{{ index + 1 }}</span>
            <div class="result-card__actions">
              <a-button size="small" @click="handleCopy(item)">
                <template #icon><Copy :size="13" /></template>
                复制
              </a-button>
              <a-button size="small" type="primary" :loading="generatingImageIndex === index" @click="handleGenerateImage(item, index)">
                <template #icon><Image :size="13" /></template>
                {{ generatedImages[index] ? '重新生图' : '生图' }}
              </a-button>
            </div>
          </div>
          <h4>{{ item.title }}</h4>
          <p class="result-content">{{ item.content }}</p>
          <div class="result-tags">
            <a-tag v-for="tag in item.hashtags" :key="tag">{{ tag }}</a-tag>
          </div>
          <div class="result-image-prompt">
            <div class="result-image-prompt__head">
              <span>图片提示词</span>
              <div class="result-image-prompt__actions">
                <a-button size="small" type="link" @click="copyImagePrompt(item)">复制</a-button>
                <a-button size="small" type="link" @click="startEditImagePrompt(index)">编辑</a-button>
              </div>
            </div>
            <div v-if="editingImagePromptIndex === index" class="result-image-prompt__editor">
              <a-textarea v-model:value="editingImagePromptValue" :rows="3" />
              <div class="result-image-prompt__editor-actions">
                <a-button size="small" @click="cancelEditImagePrompt">取消</a-button>
                <a-button size="small" type="primary" @click="saveEditImagePrompt(index)">保存</a-button>
              </div>
            </div>
            <div v-else class="result-image-prompt__text">
              <p>{{ item.image_prompt || '无' }}</p>
            </div>
          </div>
          <img v-if="generatedImages[index]" :src="generatedImages[index]" alt="" class="result-img" />
        </article>
      </div>
    </section>

    <a-drawer v-model:open="showProductsDrawer" title="已保存产品" placement="right" :width="480">
      <div class="drawer-toolbar">
        <a-input v-model:value="productKeyword" size="large" placeholder="搜索产品名称、类目" />
        <a-space>
          <a-button @click="refreshProducts" :loading="productContentStore.loadingProducts">
            <template #icon><RefreshCw :size="14" /></template>
            刷新
          </a-button>
          <a-button type="primary" @click="handleCreateNewProduct">
            <template #icon><Plus :size="14" /></template>
            新建
          </a-button>
        </a-space>
      </div>

      <div class="drawer-list">
        <div v-if="!filteredProducts.length" class="drawer-empty">暂无产品</div>
        <div v-for="product in filteredProducts" :key="product.id" class="drawer-item" :class="{ active: activeProductPreview?.id === product.id }" @click="handleUseProduct(product)">
          <strong>{{ product.name }}</strong>
          <a-tag v-if="selectedProductId === product.id" color="blue">使用中</a-tag>
          <a-button size="small" danger type="link" :loading="deletingProductId === product.id" @click.stop="confirmDelete(product)">删除</a-button>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { Copy, Image, PackageSearch, Plus, RefreshCw, Sparkles } from 'lucide-vue-next'
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
const uploadingImage = ref(false)
const editingImagePromptIndex = ref(null)
const editingImagePromptValue = ref('')

const selectedPromptExternalId = ref(undefined)
const requiredPromptVariables = ['product_payload', 'channel', 'styles_payload', 'count']

const styleOptions = ['种草', '专业', '故事', '对比', '简洁', '高级感']
const channelOptions = [
  { label: '小红书', value: 'xiaohongshu' },
  { label: '抖音', value: 'douyin' },
  { label: '公众号', value: 'wechat' },
  { label: '电商详情', value: 'ecommerce' }
]

const resultItems = computed(() => productContentStore.lastGenerated?.items || [])
const resultCount = computed(() => resultItems.value.length)
const attributesCount = computed(() => Object.keys(productForm.attributes || {}).length)
const savedProductsCount = computed(() => productContentStore.productsTotal || productContentStore.products.length)
const currentResultMeta = computed(() => ({
  channel: productContentStore.lastGenerated?.channel || channel.value,
  toneStyles: productContentStore.lastGenerated?.tone_styles || selectedStyles.value,
  createdAt: productContentStore.lastGenerated?.created_at || null
}))

const promptOptions = computed(() => {
  const managedOptions = (productContentStore.promptOptions || []).map((item) => ({
    label: item.path || item.name,
    value: item.external_id,
    disabled: !item.is_compatible,
    meta: { name: item.name, path: item.path, external_id: item.external_id, is_compatible: item.is_compatible }
  })).sort((a, b) => String(a.label || '').localeCompare(String(b.label || ''), 'zh-CN'))

  return [{ label: '系统内置提示词', value: '__builtin__', meta: { name: '系统内置提示词', path: 'builtin', external_id: '__builtin__', is_compatible: true } }, ...managedOptions]
})

const selectedPromptOption = computed(() => {
  if (!selectedPromptExternalId.value) return null
  return productContentStore.promptOptions.find((item) => item.external_id === selectedPromptExternalId.value) || null
})

const promptStrategySummary = computed(() => {
  if (!selectedPromptExternalId.value) return null
  return {
    modeLabel: selectedPromptOption.value?.path || selectedPromptOption.value?.name || '自定义提示词',
    description: `${getPromptFileName(selectedPromptOption.value?.path, selectedPromptOption.value?.name)} · external_id: ${selectedPromptExternalId.value}`
  }
})

const getPromptFileName = (path, fallback = '') => {
  const normalized = String(path || fallback || '').trim()
  if (!normalized) return '未命名提示词'
  const parts = normalized.split('/').filter(Boolean)
  return parts[parts.length - 1] || normalized
}

const filterPromptOption = (input, option) => {
  const keyword = String(input || '').trim().toLowerCase()
  if (!keyword) return true
  const meta = option?.meta || {}
  return [option?.label, meta.name, meta.path, meta.external_id].filter(Boolean).some((v) => String(v).toLowerCase().includes(keyword))
}

const openSelectedPromptInManager = () => {
  if (!selectedPromptExternalId.value) { message.info('当前使用系统内置提示词'); return }
  router.push({ path: '/extensions/prompts', query: { external_id: selectedPromptExternalId.value } })
}

const selectedProduct = computed(() => {
  if (!selectedProductId.value) return null
  return productContentStore.products.find((item) => item.id === selectedProductId.value) || null
})

const formSnapshot = computed(() => JSON.stringify({ name: productForm.name || '', material: productForm.material || '', style: productForm.style || '', color: productForm.color || '', scene: productForm.scene || '', selling_points: productForm.selling_points || [], target_audience: productForm.target_audience || '', price_range: productForm.price_range || '', attributes: productForm.attributes || {} }))

const selectedProductSnapshot = computed(() => {
  if (!selectedProduct.value) return ''
  return JSON.stringify({ name: selectedProduct.value.name || '', material: selectedProduct.value.material || '', style: selectedProduct.value.style || '', color: selectedProduct.value.color || '', scene: selectedProduct.value.scene || '', selling_points: selectedProduct.value.selling_points || [], target_audience: selectedProduct.value.target_audience || '', price_range: selectedProduct.value.price_range || '', attributes: selectedProduct.value.attributes || {} })
})

const canGenerate = computed(() => Boolean(productForm.name?.trim()) && selectedStyles.value.length > 0 && count.value > 0)
const canSaveProduct = computed(() => Boolean(productForm.name?.trim()) && !isSavingProduct.value)
const selectedProductLabel = computed(() => selectedProduct.value?.name || productForm.name || '未命名产品')

const productOptions = computed(() =>
  productContentStore.products.map((item) => ({ label: item.name, value: item.id }))
)

const filteredProducts = computed(() => {
  const keyword = productKeyword.value.trim().toLowerCase()
  if (!keyword) return productContentStore.products
  return productContentStore.products.filter((item) => [item.name, item.scene, item.style, item.material, item.target_audience].filter(Boolean).some((field) => String(field).toLowerCase().includes(keyword)))
})

const activeProductPreview = computed(() => {
  if (!filteredProducts.value.length) return null
  return filteredProducts.value.find((item) => item.id === activeProductPreviewId.value) || filteredProducts.value[0]
})

const parseError = (error, fallback) => {
  if (!error) return fallback
  return typeof error.message === 'string' && error.message.trim() ? error.message : fallback
}

const syncSellingPointsInput = () => { sellingPointsInput.value = (productForm.selling_points || []).join('; ') }
const syncSellingPointsArray = () => { productForm.selling_points = sellingPointsInput.value.split(/[;；,，\n]/).map((t) => t.trim()).filter(Boolean) }

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
  productForm.name = product.name || ''
  productForm.material = product.material || ''
  productForm.style = product.style || ''
  productForm.color = product.color || ''
  productForm.scene = product.scene || ''
  productForm.selling_points = [...(product.selling_points || [])]
  productForm.target_audience = product.target_audience || ''
  productForm.price_range = product.price_range || ''
  productForm.attributes = { ...(product.attributes || {}) }
  productForm.image_paths = [...(product.image_paths || [])]
  syncSellingPointsInput()
  hasFormChanges.value = false
}

const handleSelectProduct = (productId) => {
  if (!productId) { resetProductForm(); return }
  const product = productContentStore.products.find((item) => item.id === productId)
  if (!product) return
  activeProductPreviewId.value = product.id
  loadProductToForm(product)
  void loadSelectedProductResult(product.id)
}

const loadSelectedProductResult = async (productId) => {
  loadingSelectedProductResult.value = true
  generatedImages.value = {}
  try {
    const result = await productContentStore.fetchLatestGenerationForProduct(productId)
    if (!result) productContentStore.lastGenerated = null
  } catch (error) {
    productContentStore.lastGenerated = null
    if (error?.status !== 404) message.error(parseError(error, '加载历史结果失败'))
  } finally { loadingSelectedProductResult.value = false }
}

const openProductsDrawer = async () => {
  showProductsDrawer.value = true
  if (!productContentStore.products.length) await productContentStore.fetchProducts({ page: 1, page_size: 50 })
  activeProductPreviewId.value = selectedProductId.value || activeProductPreviewId.value || productContentStore.products[0]?.id || null
}

const handleUseProduct = (product) => {
  selectedProductId.value = product.id
  activeProductPreviewId.value = product.id
  loadProductToForm(product)
  void loadSelectedProductResult(product.id)
}

const handleCreateNewProduct = () => { resetProductForm(); activeProductPreviewId.value = null; showProductsDrawer.value = false }

const handleDeleteProduct = async (product) => {
  deletingProductId.value = product.id
  try {
    await productContentStore.deleteProduct(product.id)
    if (selectedProductId.value === product.id) resetProductForm()
    message.success('已删除')
  } catch (error) {
    message.error('删除失败')
  } finally {
    deletingProductId.value = null
  }
}

const handleClearForm = () => {
  resetProductForm()
  productContentStore.lastGenerated = null
  selectedProductId.value = undefined
  message.success('已清除')
}

const refreshProducts = async () => {
  await productContentStore.fetchProducts({ page: 1, page_size: 50 })
  if (!productContentStore.products.some((item) => item.id === activeProductPreviewId.value)) activeProductPreviewId.value = productContentStore.products[0]?.id || null
}

const handleAddAttribute = () => {
  const key = attributeKey.value.trim()
  const value = attributeValue.value.trim()
  if (!key || !value) return
  productForm.attributes = { ...(productForm.attributes || {}), [key]: value }
  attributeKey.value = ''
  attributeValue.value = ''
}

const handleRemoveAttribute = (key) => {
  const nextAttrs = { ...(productForm.attributes || {}) }
  delete nextAttrs[key]
  productForm.attributes = nextAttrs
}

const handleBeforeUploadImage = (file) => {
  const ext = file.name?.split('.').pop()?.toLowerCase()
  const allowed = ['png', 'jpg', 'jpeg', 'webp']
  if (!allowed.includes(ext)) {
    message.warning('仅支持 PNG / JPG / WebP 格式')
    return false
  }
  if (file.size > 10 * 1024 * 1024) {
    message.warning('图片大小不能超过 10MB')
    return false
  }
  handleUploadImage(file)
  return false
}

const handleUploadImage = async (file) => {
  if (!selectedProductId.value) {
    message.warning('请先保存产品后再上传参考图片')
    return
  }
  uploadingImage.value = true
  try {
    await productContentStore.uploadProductImage(selectedProductId.value, file)
    message.success('图片已上传')
    const product = productContentStore.products.find((item) => item.id === selectedProductId.value)
    if (product) {
      productForm.image_paths = [...(product.image_paths || [])]
    }
  } catch (err) {
    message.error(err?.message || '上传失败')
  } finally {
    uploadingImage.value = false
  }
}

const handleRemoveImage = async (idx) => {
  const imageUrl = productForm.image_paths?.[idx]
  if (!imageUrl || !selectedProductId.value) return
  try {
    await productContentStore.deleteProductImage(selectedProductId.value, imageUrl)
    productForm.image_paths = (productForm.image_paths || []).filter((_, i) => i !== idx)
    message.success('图片已删除')
  } catch (err) {
    message.error(err?.message || '删除失败')
  }
}

const confirmDelete = (product) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除「${product.name}」吗？`,
    okText: '删除',
    okType: 'danger',
    cancelText: '取消',
    onOk: () => handleDeleteProduct(product)
  })
}

const handleCreateOrUpdateProduct = async () => {
  syncSellingPointsArray()
  const payload = { ...productForm, name: productForm.name.trim() }
  if (!payload.name) { message.warning('请先输入产品名称'); return }
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
    message.error(parseError(error, '保存失败'))
  } finally { isSavingProduct.value = false }
}

const handleGenerate = async () => {
  syncSellingPointsArray()
  if (!canGenerate.value) { message.warning('请补全产品名称和风格'); return }
  try {
    generatedImages.value = {}
    await productContentStore.generateContents({ product_id: selectedProductId.value, prompt_external_id: selectedPromptExternalId.value, product: { ...productForm }, styles: selectedStyles.value, count: count.value, channel: channel.value })
    if (productContentStore.lastGenerated?.product_id) selectedProductId.value = productContentStore.lastGenerated.product_id
    await productContentStore.fetchProducts({ page: 1, page_size: 50 })
    hasFormChanges.value = false
    message.success('文案生成完成')
    await productContentStore.fetchGenerations({ page: 1, page_size: 20 })
  } catch (error) {
    const detail = error?.payload?.detail
    if (error?.status === 403 && detail?.code === 'QUOTA_EXCEEDED') {
      Modal.confirm({
        title: '配额已用尽',
        content: detail?.message || '当前订阅配额已用尽，是否前往订阅中心升级？',
        okText: '前往升级',
        cancelText: '稍后再说',
        onOk: () => router.push('/product-content/subscription')
      })
      return
    }
    message.error(parseError(error, '生成失败'))
  }
}

const handleGenerateImage = async (item, index) => {
  if (!item.image_prompt) { message.warning('该文案无图片提示词'); return }
  generatingImageIndex.value = index
  try {
    const result = await productContentStore.generateImage({
      prompt: item.image_prompt,
      size: '1024x1024',
      style: 'natural',
      reference_images: productForm.image_paths || []
    })
    generatedImages.value = { ...generatedImages.value, [index]: result.image_url }
    message.success('图片生成完成')
  } catch (error) { message.error(parseError(error, '生图失败')) }
  finally { generatingImageIndex.value = null }
}

const handleCopy = async (item) => {
  const fullText = `${item.title}\n\n${item.content}\n\n${(item.hashtags || []).join(' ')}`
  await navigator.clipboard.writeText(fullText)
  message.success('已复制')
}

const copyImagePrompt = async (item) => {
  if (!item.image_prompt) { message.warning('无图片提示词可复制'); return }
  await navigator.clipboard.writeText(item.image_prompt)
  message.success('图片提示词已复制')
}

const startEditImagePrompt = (index) => {
  const item = resultItems.value[index]
  if (!item) return
  editingImagePromptValue.value = item.image_prompt || ''
  editingImagePromptIndex.value = index
}

const cancelEditImagePrompt = () => {
  editingImagePromptIndex.value = null
  editingImagePromptValue.value = ''
}

const saveEditImagePrompt = async (index) => {
  const item = resultItems.value[index]
  if (!item) return
  const generationId = productContentStore.lastGenerated?.generation_id
  if (!generationId) {
    message.warning('无法保存：未找到生成记录')
    return
  }
  try {
    await productContentStore.updateGenerationItemImagePrompt(generationId, index, editingImagePromptValue.value)
    item.image_prompt = editingImagePromptValue.value
    editingImagePromptIndex.value = null
    editingImagePromptValue.value = ''
    message.success('图片提示词已更新')
  } catch (error) {
    message.error(error?.message || '保存失败')
  }
}

onMounted(async () => {
  await Promise.all([productContentStore.fetchQuota(), productContentStore.fetchProducts({ page: 1, page_size: 50 }), productContentStore.fetchPromptOptions()])
  const queryPromptExternalId = String(route.query.prompt_external_id || '').trim()
  if (queryPromptExternalId && (productContentStore.promptOptions || []).some((item) => item.external_id === queryPromptExternalId && item.is_compatible)) {
    selectedPromptExternalId.value = queryPromptExternalId
  }
  const queryProductId = Number(route.query.product_id)
  if (Number.isInteger(queryProductId) && queryProductId > 0) {
    selectedProductId.value = queryProductId
    handleSelectProduct(queryProductId)
  }
  activeProductPreviewId.value = selectedProductId.value || productContentStore.products[0]?.id || null
})

watch(filteredProducts, (nextList) => {
  if (!nextList.length) { activeProductPreviewId.value = null; return }
  if (!nextList.some((item) => item.id === activeProductPreviewId.value)) activeProductPreviewId.value = nextList[0].id
})

watch(formSnapshot, (nextSnapshot) => {
  if (!selectedProductId.value) { hasFormChanges.value = Boolean(productForm.name?.trim() || sellingPointsInput.value.trim() || attributesCount.value); return }
  hasFormChanges.value = nextSnapshot !== selectedProductSnapshot.value
})

watch(selectedProductSnapshot, (nextSnapshot) => {
  if (!selectedProductId.value) return
  hasFormChanges.value = formSnapshot.value !== nextSnapshot
})
</script>

<style scoped>
.page {
  --pc-accent: #d97706;
  --pc-blue: #2563eb;
  --pc-text: #172033;
  --pc-muted: #60708a;
  --pc-panel: rgba(255, 255, 255, 0.78);
  --pc-border: rgba(15, 23, 42, 0.08);
  padding: 28px;
  min-height: 100%;
  background:
    radial-gradient(circle at top left, rgba(245, 158, 11, 0.14), transparent 28%),
    radial-gradient(circle at 90% 10%, rgba(37, 99, 235, 0.12), transparent 22%),
    linear-gradient(180deg, #fff9f2, #eef6ff 42%, #f9fbff 100%);
}

.top-bar,
.workspace,
.results-panel {
  max-width: 1200px;
  margin: 0 auto;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  gap: 20px;
  margin-bottom: 20px;
}

.top-bar__main {
  flex: 1 1 auto;
  min-width: 0;
}

.top-bar__main h1 {
  margin: 10px 0 8px;
  font-size: 32px;
  font-weight: 800;
  color: var(--pc-text);
}

.top-bar__main p {
  margin: 0;
  color: var(--pc-muted);
}

.top-bar__kicker {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.5);
  color: var(--pc-accent);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.top-bar__actions {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.top-bar__highlights {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.highlight-pill {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.18);
  color: var(--pc-text);
  font-size: 13px;
  font-weight: 600;
}

.top-bar__side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: space-between;
  gap: 14px;
  width: 360px;
  flex: 0 0 360px;
}

.top-bar__card {
  width: 100%;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(148, 163, 184, 0.18);
  backdrop-filter: blur(14px);
}

.top-bar__card-label {
  display: block;
  color: var(--pc-accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.top-bar__card strong {
  display: block;
  margin-top: 8px;
  color: var(--pc-text);
  font-size: 18px;
  line-height: 1.45;
}

.top-bar__card p {
  margin: 10px 0 0;
  color: var(--pc-muted);
  font-size: 13px;
  line-height: 1.7;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  font-size: 16px;
  font-weight: 700;
  color: var(--pc-text);
}

.workspace {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 18px;
  margin-bottom: 20px;
}

.editor-panel,
.config-panel,
.results-panel {
  border-radius: 24px;
  padding: 22px;
  background: var(--pc-panel);
  border: 1px solid var(--pc-border);
  backdrop-filter: blur(14px);
}

.config-panel {
  align-self: start;
  position: sticky;
  top: 20px;
}

.editor-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.form-row--three {
  grid-template-columns: 1fr 1fr 1fr;
}

.form-attrs {
  padding: 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.form-attrs__add {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 8px;
}

.form-attrs__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.empty-hint {
  color: var(--pc-muted);
  font-size: 12px;
}

.form-images {
  padding: 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.form-images__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.form-images__head span {
  font-weight: 600;
  color: var(--pc-text);
}

.form-images__list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.form-images__item {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(148, 163, 184, 0.2);
}

.form-images__thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.form-images__item:hover button {
  opacity: 1;
}

.form-images__item button {
  position: absolute;
  bottom: 4px;
  right: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  font-size: 11px;
  padding: 0 8px;
  height: 24px;
  line-height: 24px;
}

.editor-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-top: 14px;
}

.editor-actions__left {
  display: flex;
  gap: 10px;
}

.editor-actions__right {
  display: flex;
  gap: 10px;
}

.style-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.style-pill {
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.6);
  color: var(--pc-text);
  cursor: pointer;
  transition: all 0.15s;
}

.style-pill.active {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(217, 119, 6, 0.1));
  border-color: rgba(37, 99, 235, 0.2);
  color: var(--pc-blue);
}

.prompt-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 0;
}

.prompt-option--disabled { opacity: 0.6; }

.prompt-option__path {
  color: var(--pc-muted);
  font-size: 12px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.prompt-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(37, 99, 235, 0.1);
  font-size: 13px;
}

.prompt-summary__badge {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.08);
  color: var(--pc-blue);
  font-weight: 700;
  font-size: 11px;
  white-space: nowrap;
}

.prompt-summary__detail {
  color: var(--pc-muted);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.count-note {
  text-align: right;
  color: var(--pc-muted);
  font-size: 13px;
  margin-top: 4px;
}

.results-panel {
  margin-top: 0;
}

.result-summary {
  font-size: 13px;
  color: var(--pc-muted);
  font-weight: 400;
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

.result-card {
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.result-card__top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.result-style {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(217, 119, 6, 0.08);
  color: var(--pc-accent);
  font-size: 11px;
  font-weight: 700;
}

.result-num {
  color: var(--pc-blue);
  font-size: 11px;
  font-weight: 700;
}

.result-card__actions {
  margin-left: auto;
  display: flex;
  gap: 6px;
}

.result-card h4 {
  margin: 0 0 8px;
  font-size: 17px;
  font-weight: 800;
  color: var(--pc-text);
}

.result-content {
  white-space: pre-wrap;
  color: #334155;
  line-height: 1.7;
  margin: 0;
  font-size: 14px;
}

.result-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 12px 0;
}

.result-image-prompt {
  padding: 12px;
  border-radius: 14px;
  background: rgba(241, 245, 249, 0.7);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.result-image-prompt__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.result-image-prompt__head span {
  font-size: 11px;
  color: var(--pc-muted);
}

.result-image-prompt__actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.result-image-prompt__text p {
  margin: 0;
  color: var(--pc-text);
  font-size: 13px;
  line-height: 1.6;
}

.result-image-prompt__editor {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.result-image-prompt__editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.result-img {
  width: 100%;
  margin-top: 12px;
  border-radius: 14px;
  aspect-ratio: 1;
  object-fit: cover;
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.drawer-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.drawer-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.drawer-empty {
  text-align: center;
  padding: 32px 0;
  color: var(--pc-muted);
}

.drawer-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.15s;
}

.drawer-item.active {
  border-color: rgba(37, 99, 235, 0.2);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
}

.drawer-item strong {
  flex: 1;
  font-size: 14px;
  color: var(--pc-text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #d97706, #2563eb);
  border: none;
  box-shadow: 0 12px 20px rgba(37, 99, 235, 0.16);
}

:deep(.ant-input),
:deep(.ant-input-affix-wrapper),
:deep(.ant-select-selector) {
  border-radius: 12px !important;
  border-color: rgba(15, 23, 42, 0.08) !important;
}

:deep(.ant-slider-track) {
  background: linear-gradient(90deg, #f59e0b, #2563eb);
}

@media (max-width: 1100px) {
  .workspace {
    grid-template-columns: 1fr;
  }
  .config-panel {
    position: static;
  }
  .top-bar {
    flex-direction: column;
  }
  .top-bar__side {
    width: 100%;
    flex: none;
    align-items: stretch;
  }
  .top-bar__actions {
    justify-content: flex-start;
  }
  .result-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 820px) {
  .page { padding: 16px; }
  .form-row,
  .form-row--three {
    grid-template-columns: 1fr;
  }
}
</style>
