import axios, { AxiosInstance } from 'axios'

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000'
console.log('API_BASE_URL:', API_BASE_URL)

class ApiService {
  private client: AxiosInstance
  private token: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Add request interceptor to include auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`
        }
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Add response interceptor to handle auth errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.setToken(null)
          localStorage.removeItem('token')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      }
    )
  }

  setToken(token: string | null) {
    this.token = token
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const response = await this.client.post('/auth/login', { username, password })
    return response.data
  }

  async register(username: string, email: string, password: string) {
    const response = await this.client.post('/auth/register', { username, email, password })
    return response.data
  }

  async getCurrentUser() {
    const response = await this.client.get('/auth/me')
    return response.data
  }

  // Repricer endpoints
  async uploadInventory(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post('/repricer/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  async filterInventory(filters: any) {
    const response = await this.client.post('/repricer/filter', filters)
    return response.data
  }

  async updatePrices(updateData: any) {
    const response = await this.client.post('/repricer/update-prices', updateData)
    return response.data
  }

  // EV Tools endpoints
  async simulateBoosterBox(setCode: string, boxesToOpen: number) {
    const response = await this.client.post('/ev-tools/simulate-box', {
      set_code: setCode,
      boxes_to_open: boxesToOpen
    })
    return response.data
  }

  async calculatePreconEV(preconName: string, setCode: string) {
    const response = await this.client.post('/ev-tools/precon-ev', {
      precon_name: preconName,
      set_code: setCode,
      calculate_singles: true
    })
    return response.data
  }

  // Pokemon Tracker endpoints
  async getPokemonPrices(setName?: string) {
    const params = setName ? { set_name: setName } : {}
    const response = await this.client.get('/pokemon/prices', { params })
    return response.data
  }

  // Manabox endpoints
  async convertManaboxCSV(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post('/manabox/convert', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  // Inventory endpoints
  async getInventory() {
    const response = await this.client.get('/inventory')
    return response.data
  }

  async getInventorySnapshots() {
    const response = await this.client.get('/inventory/snapshots')
    return response.data
  }

  async uploadInventoryPDF(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post('/inventory/upload-pdf', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  async uploadInventoryCSV(file: File, replaceAll: boolean = false) {
    console.log('Uploading CSV file:', file.name, 'Size:', file.size, 'Replace all:', replaceAll)
    
    const formData = new FormData()
    formData.append('file', file)
    
    const params = new URLSearchParams()
    if (replaceAll) {
      params.append('replace_all', 'true')
    }
    
    const url = `/inventory/upload-csv?${params.toString()}`
    console.log('Upload URL:', `${API_BASE_URL}${url}`)
    
    try {
      const response = await this.client.post(url, formData, {
        headers: { 
          'Content-Type': 'multipart/form-data'
        },
        timeout: 300000 // 5 minute timeout for large inventories
      })
      console.log('Upload successful:', response.data)
      return response.data
    } catch (error: any) {
      console.error('Upload failed:', error)
      console.error('Error details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data
      })
      throw error
    }
  }

  async getInventoryAnalytics(period: 'week' | 'month' | 'year') {
    const response = await this.client.get(`/inventory/analytics/${period}`)
    return response.data
  }

  // TCGPlayer endpoints
  async extractTCGPlayerOrders(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const response = await this.client.post('/tcgplayer/extract-orders', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return response.data
  }

  // Admin endpoints
  async updateTCGPlayerIDs() {
    const response = await this.client.post('/admin/update-tcgplayer-ids')
    return response.data
  }

  async getCloudControlStatus() {
    const response = await this.client.get('/admin/cloud-control')
    return response.data
  }

  // Health check
  async healthCheck() {
    const response = await this.client.get('/health')
    return response.data
  }
}

// Create singleton instance
export const apiService = new ApiService()

// Export individual service modules for better organization
export const authService = {
  login: (username: string, password: string) => apiService.login(username, password),
  register: (username: string, email: string, password: string) => apiService.register(username, email, password),
  getCurrentUser: () => apiService.getCurrentUser(),
  setToken: (token: string | null) => apiService.setToken(token),
}

export const repricerService = {
  uploadInventory: (file: File) => apiService.uploadInventory(file),
  filterInventory: (filters: any) => apiService.filterInventory(filters),
  updatePrices: (updateData: any) => apiService.updatePrices(updateData),
}

export const evToolsService = {
  simulateBoosterBox: (setCode: string, boxesToOpen: number) => 
    apiService.simulateBoosterBox(setCode, boxesToOpen),
  calculatePreconEV: (preconName: string, setCode: string) => 
    apiService.calculatePreconEV(preconName, setCode),
}

export const pokemonService = {
  getPrices: (setName?: string) => apiService.getPokemonPrices(setName),
}

export const manaboxService = {
  convertCSV: (file: File) => apiService.convertManaboxCSV(file),
}

export const inventoryService = {
  getInventory: () => apiService.getInventory(),
  getInventorySnapshots: () => apiService.getInventorySnapshots(),
  uploadInventoryPDF: (file: File) => apiService.uploadInventoryPDF(file),
  uploadInventoryCSV: (file: File, replaceAll: boolean = false) => apiService.uploadInventoryCSV(file, replaceAll),
  getAnalytics: (period: 'week' | 'month' | 'year') => apiService.getInventoryAnalytics(period),
}

export const tcgplayerService = {
  extractOrders: (file: File) => apiService.extractTCGPlayerOrders(file),
}

export const adminService = {
  updateTCGPlayerIDs: () => apiService.updateTCGPlayerIDs(),
  getCloudControlStatus: () => apiService.getCloudControlStatus(),
}

export default apiService
