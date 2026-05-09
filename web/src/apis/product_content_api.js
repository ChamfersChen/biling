import { apiGet, apiPost, apiPut, apiPatch, apiDelete } from './base'

const BASE_URL = '/api/product-content'

const unwrap = (res) => (res && typeof res === 'object' && 'data' in res ? res.data : res)

export const productContentApi = {
  getPromptOptions: async () => unwrap(await apiGet(`${BASE_URL}/prompt-options`)),
  getProducts: async (params = {}) => unwrap(await apiGet(`${BASE_URL}/products`, params)),
  createProduct: async (payload) => unwrap(await apiPost(`${BASE_URL}/products`, payload)),
  updateProduct: async (productId, payload) => unwrap(await apiPut(`${BASE_URL}/products/${productId}`, payload)),
  deleteProduct: async (productId) => unwrap(await apiDelete(`${BASE_URL}/products/${productId}`)),
  getGenerations: async (params = {}) => unwrap(await apiGet(`${BASE_URL}/generations`, params)),
  getLatestGenerationForProduct: async (productId) => unwrap(await apiGet(`${BASE_URL}/products/${productId}/latest-generation`)),
  generateContents: async (payload) => unwrap(await apiPost(`${BASE_URL}/generate`, payload)),
  generateImage: async (payload) => unwrap(await apiPost(`${BASE_URL}/generate-image`, payload)),
  getQuota: async () => unwrap(await apiGet(`${BASE_URL}/quota`)),
  getSubscription: async () => unwrap(await apiGet(`${BASE_URL}/subscription`)),
  getDashboard: async () => unwrap(await apiGet(`${BASE_URL}/dashboard`)),
  createCheckoutSession: async (payload) => unwrap(await apiPost(`${BASE_URL}/subscription/checkout`, payload)),
  createCustomerPortal: async (payload) => unwrap(await apiPost(`${BASE_URL}/subscription/portal`, payload)),
  redeemCode: async (payload) => unwrap(await apiPost(`${BASE_URL}/subscription/redeem`, payload)),
  getTransactions: async () => unwrap(await apiGet(`${BASE_URL}/subscription/transactions`)),
  getSubscriptionCodes: async () => unwrap(await apiGet(`${BASE_URL}/subscription/codes`)),
  createSubscriptionCode: async (payload) => unwrap(await apiPost(`${BASE_URL}/subscription/codes`, payload)),
  uploadProductImage: async (productId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return unwrap(await apiPost(`${BASE_URL}/products/${productId}/images`, formData, {}))
  },
  deleteProductImage: async (productId, imageUrl) => unwrap(await apiDelete(`${BASE_URL}/products/${productId}/images?image_url=${encodeURIComponent(imageUrl)}`)),
  updateGenerationItemImagePrompt: async (generationId, payload) => unwrap(await apiPatch(`${BASE_URL}/generations/${generationId}/items/image-prompt`, payload))
}

export default productContentApi
