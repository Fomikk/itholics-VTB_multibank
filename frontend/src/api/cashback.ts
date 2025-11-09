/** API functions for cashback */
import apiClient from './client'
import type {
  CashbackActivateRequest,
  CashbackActivateResponse,
  CashbackBonus,
} from './types'

export async function activateCashback(
  request: CashbackActivateRequest
): Promise<CashbackActivateResponse> {
  const response = await apiClient.post<CashbackActivateResponse>(
    '/cashback/activate',
    request
  )
  return response.data
}

export async function getActiveCashback(clientId: string): Promise<CashbackBonus[]> {
  const response = await apiClient.get<CashbackBonus[]>(
    `/cashback/active?client_id=${encodeURIComponent(clientId)}`
  )
  return response.data
}

