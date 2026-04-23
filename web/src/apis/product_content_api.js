import { apiGet, apiPost, apiPut, apiDelete } from './base'

const BASE_URL = '/api/product-content'

const unwrap = (res) => (res && typeof res === 'object' && 'data' in res ? res.data : res)

export const productContentApi = {
  getProducts: async (params = {}) => unwrap(await apiGet(`${BASE_URL}/products`, params)),
  createProduct: async (payload) => unwrap(await apiPost(`${BASE_URL}/products`, payload)),
  updateProduct: async (productId, payload) => unwrap(await apiPut(`${BASE_URL}/products/${productId}`, payload)),
  deleteProduct: async (productId) => unwrap(await apiDelete(`${BASE_URL}/products/${productId}`)),
  getGenerations: async (params = {}) => unwrap(await apiGet(`${BASE_URL}/generations`, params)),
  generateContents: async (payload) => unwrap(await apiPost(`${BASE_URL}/generate`, payload)),
  generateImage: async (payload) => unwrap(await apiPost(`${BASE_URL}/generate-image`, payload)),
  getQuota: async () => unwrap(await apiGet(`${BASE_URL}/quota`)),
  getSubscription: async () => unwrap(await apiGet(`${BASE_URL}/subscription`))
}

export default productContentApi
