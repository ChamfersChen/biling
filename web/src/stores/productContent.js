import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { productContentApi } from '@/apis/product_content_api'

const defaultProductForm = {
  category: 'general',
  name: '',
  material: '',
  style: '',
  color: '',
  scene: '',
  selling_points: [],
  target_audience: '',
  price_range: '',
  attributes: {}
}

const normalizeGeneration = (data) => {
  if (!data) {
    return null
  }
  const items = data.items || data.result_items || []
  return {
    ...data,
    items,
    result_items: items,
    tone_styles: data.tone_styles || [],
    channel: data.channel || 'xiaohongshu',
    created_at: data.created_at || null,
    product_name: data.product_name || null,
    product_category: data.product_category || null,
    prompt_name: data.prompt_name || null,
    prompt_external_id: data.prompt_external_id || null
  }
}

const upsertProduct = (list, product) => {
  if (!product?.id) {
    return list
  }
  const next = [product, ...list.filter((item) => item.id !== product.id)]
  return next
}

export const useProductContentStore = defineStore('productContent', () => {
  const products = ref([])
  const productsTotal = ref(0)
  const generations = ref([])
  const generationsTotal = ref(0)
  const currentQuota = ref(null)
  const subscription = ref(null)
  const lastGenerated = ref(null)
  const promptOptions = ref([])

  const loadingProducts = ref(false)
  const loadingGenerations = ref(false)
  const loadingQuota = ref(false)
  const loadingSubscription = ref(false)
  const loadingPromptOptions = ref(false)
  const isGenerating = ref(false)
  const isGeneratingImage = ref(false)

  const hasQuota = computed(() => {
    if (!currentQuota.value) {
      return true
    }
    if (currentQuota.value.daily_remaining === -1 || currentQuota.value.monthly_remaining === -1) {
      return true
    }
    return currentQuota.value.daily_remaining > 0 && currentQuota.value.monthly_remaining > 0
  })

  async function fetchProducts(params = {}) {
    loadingProducts.value = true
    try {
      const data = await productContentApi.getProducts(params)
      products.value = data.list || []
      productsTotal.value = data.total || 0
      return data
    } finally {
      loadingProducts.value = false
    }
  }

  async function fetchPromptOptions() {
    loadingPromptOptions.value = true
    try {
      const data = await productContentApi.getPromptOptions()
      promptOptions.value = data.list || []
      return data
    } finally {
      loadingPromptOptions.value = false
    }
  }

  async function createProduct(payload) {
    const data = await productContentApi.createProduct(payload)
    products.value = upsertProduct(products.value, data)
    productsTotal.value = Math.max(productsTotal.value, products.value.length)
    return data
  }

  async function updateProduct(productId, payload) {
    const data = await productContentApi.updateProduct(productId, payload)
    products.value = products.value.map((item) => (item.id === productId ? data : item))
    return data
  }

  async function deleteProduct(productId) {
    await productContentApi.deleteProduct(productId)
    products.value = products.value.filter((item) => item.id !== productId)
    productsTotal.value = Math.max(0, productsTotal.value - 1)
  }

  async function fetchGenerations(params = {}) {
    loadingGenerations.value = true
    try {
      const data = await productContentApi.getGenerations(params)
      generations.value = (data.list || []).map(normalizeGeneration)
      generationsTotal.value = data.total || 0
      return data
    } finally {
      loadingGenerations.value = false
    }
  }

  async function fetchLatestGenerationForProduct(productId) {
    const data = await productContentApi.getLatestGenerationForProduct(productId)
    const normalized = normalizeGeneration(data)
    lastGenerated.value = normalized
    return normalized
  }

  async function fetchQuota() {
    loadingQuota.value = true
    try {
      const data = await productContentApi.getQuota()
      currentQuota.value = data
      return data
    } finally {
      loadingQuota.value = false
    }
  }

  async function fetchSubscription() {
    loadingSubscription.value = true
    try {
      const data = await productContentApi.getSubscription()
      subscription.value = data
      return data
    } finally {
      loadingSubscription.value = false
    }
  }

  async function generateContents(payload) {
    isGenerating.value = true
    try {
      const data = await productContentApi.generateContents(payload)
      const normalized = normalizeGeneration(data)
      lastGenerated.value = normalized
      if (normalized?.product_id) {
        const index = products.value.findIndex((item) => item.id === normalized.product_id)
        if (index !== -1) {
          products.value[index] = {
            ...products.value[index],
            ...(payload.product || {}),
            id: normalized.product_id,
            name: normalized.product_name || payload.product?.name || products.value[index].name,
            category: normalized.product_category || payload.product?.category || products.value[index].category,
            updated_at: normalized.created_at || products.value[index].updated_at
          }
        } else if (payload.product) {
          products.value = upsertProduct(products.value, {
            ...payload.product,
            id: normalized.product_id,
            name: normalized.product_name || payload.product.name,
            category: normalized.product_category || payload.product.category || 'general',
            updated_at: normalized.created_at,
            created_at: normalized.created_at
          })
          productsTotal.value = Math.max(productsTotal.value, products.value.length)
        }
      }
      if (normalized?.quota) {
        currentQuota.value = normalized.quota
      }
      return normalized
    } finally {
      isGenerating.value = false
    }
  }

  async function generateImage(payload) {
    isGeneratingImage.value = true
    try {
      const data = await productContentApi.generateImage(payload)
      if (data?.quota) {
        currentQuota.value = data.quota
      }
      return data
    } finally {
      isGeneratingImage.value = false
    }
  }

  function getDefaultProductForm() {
    return {
      ...defaultProductForm,
      selling_points: [],
      attributes: {}
    }
  }

  return {
    products,
    productsTotal,
    generations,
    generationsTotal,
    currentQuota,
    subscription,
    lastGenerated,
    promptOptions,
    loadingProducts,
    loadingGenerations,
    loadingQuota,
    loadingSubscription,
    loadingPromptOptions,
    isGenerating,
    isGeneratingImage,
    hasQuota,
    fetchProducts,
    fetchPromptOptions,
    createProduct,
    updateProduct,
    deleteProduct,
    fetchGenerations,
    fetchLatestGenerationForProduct,
    fetchQuota,
    fetchSubscription,
    generateContents,
    generateImage,
    getDefaultProductForm
  }
})
