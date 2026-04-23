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

export const useProductContentStore = defineStore('productContent', () => {
  const products = ref([])
  const productsTotal = ref(0)
  const generations = ref([])
  const generationsTotal = ref(0)
  const currentQuota = ref(null)
  const subscription = ref(null)
  const lastGenerated = ref(null)

  const loadingProducts = ref(false)
  const loadingGenerations = ref(false)
  const loadingQuota = ref(false)
  const loadingSubscription = ref(false)
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

  async function createProduct(payload) {
    return productContentApi.createProduct(payload)
  }

  async function updateProduct(productId, payload) {
    return productContentApi.updateProduct(productId, payload)
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
      generations.value = data.list || []
      generationsTotal.value = data.total || 0
      return data
    } finally {
      loadingGenerations.value = false
    }
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
      lastGenerated.value = data
      if (data?.quota) {
        currentQuota.value = data.quota
      }
      return data
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
    loadingProducts,
    loadingGenerations,
    loadingQuota,
    loadingSubscription,
    isGenerating,
    isGeneratingImage,
    hasQuota,
    fetchProducts,
    createProduct,
    updateProduct,
    deleteProduct,
    fetchGenerations,
    fetchQuota,
    fetchSubscription,
    generateContents,
    generateImage,
    getDefaultProductForm
  }
})
