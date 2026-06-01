import axios from 'axios'
import type {
  TripConfirmRequest,
  TripFormData,
  TripPlanResponse,
  TripRevisionRequest
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 600000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export async function generateTripPlan(formData: TripFormData): Promise<TripPlanResponse> {
  try {
    const response = await apiClient.post<TripPlanResponse>('/api/trip/plan', formData)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '生成旅行方案失败')
  }
}

export async function reviseTripPlan(payload: TripRevisionRequest): Promise<TripPlanResponse> {
  try {
    const response = await apiClient.post<TripPlanResponse>('/api/trip/revise', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '修改旅行方案失败')
  }
}

export async function confirmTripPlan(payload: TripConfirmRequest): Promise<TripPlanResponse> {
  try {
    const response = await apiClient.post<TripPlanResponse>('/api/trip/confirm', payload)
    return response.data
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || error.message || '确认旅行方案失败')
  }
}

export async function healthCheck(): Promise<any> {
  try {
    const response = await apiClient.get('/health')
    return response.data
  } catch (error: any) {
    throw new Error(error.message || '健康检查失败')
  }
}

export default apiClient
